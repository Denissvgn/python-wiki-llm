"""An explicit missing-source archive preserves authored pages and authentic historical evidence."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import bootstrap_runtime, knowledge_orchestration
from llm_wiki_cli.services.documentation_native import evaluate_documentation_native_freshness
from llm_wiki_engine.knowledge_evidence import hash_json
from llm_wiki_engine.knowledge_loader import load_knowledge_state
from llm_wiki_engine.knowledge_model import ComputedFreshness, EvidenceState, knowledge_index_to_payload
from llm_wiki_engine.sync_manifest import MANIFEST_FILENAME, SyncManifest


SOURCE = (
    '"""Collect retained samples."""\n\n'
    'class ReadingWindow:\n'
    '    """A retained sample window."""\n\n'
    '    def cap(self, values: list[int]) -> list[int]:\n'
    '        return values[:3]\n\n'
    'def readings() -> list[int]:\n'
    '    return ReadingWindow().cap([2, 4, 8])\n'
)
SOURCE_PATH = "former.py"
MODULE = "modules/former.md"
ENTITY = "entities/ReadingWindow.md"
PAGES = {MODULE: "llm-wiki://modules/former", ENTITY: "llm-wiki://entities/ReadingWindow"}
PROSE = {
    MODULE: ("Collect retained samples.", "A field editor kept this module explanation."),
    ENTITY: ("A retained sample window.", "An editor documented the original window semantics."),
}
REGISTRY = "historical_source_files"
EXTENSION = "llm-wiki/historical-source-file"
RELEASES = "historical_source_releases"
RELEASE_EXTENSION = "llm-wiki/historical-source-releases"
HEADING = "### Historical source files"
HEADER = "> ⚠️ **Stale:** Source no longer found in codebase. Run `llm-wiki lint` to audit.\n\n"


def _hash(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def _snapshot(root: Path) -> dict:
    return {
        file.relative_to(root).as_posix(): (file.read_bytes(), file.stat().st_mtime_ns)
        for file in root.rglob("*") if file.is_file()
    }


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / SOURCE_PATH).write_bytes(SOURCE.encode())
    (src / "current.py").write_text('"""Current data."""\n\nclass CurrentReading:\n    value: int = 1\n', encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1", skip_flows=True, skip_workflows=True)
    wiki = tmp_path / "wiki"
    for path, (old, edited) in PROSE.items():
        page = wiki / path
        before = page.read_text(encoding="utf-8")
        section = "\n## Description\n\n" + old + "\n"
        assert before.count(section) == 1
        page.write_text(
            before.replace(section, "\n## Description\n\n" + edited + "\n")
            + f"\n## Notes\n\nPreserve these author-owned bytes — {path}.\n",
            encoding="utf-8",
        )
    api.sync_wiki("src", "wiki")
    return src, wiki


def _acknowledge(wiki):
    result = api.adopt_maintenance("src", "wiki", recovery_dir="maintenance-recovery")
    assert result["changed"]
    rows = api.get_maintenance_status("src", "wiki")["records"]
    selected = {
        row["target"]["canonical_path"]: row["record_id"] for row in rows
        if row["coordinate"]["source_path"] == SOURCE_PATH and row["target"]["section_locator"].endswith("/Description~1")
    }
    assert set(selected) == set(PAGES)
    for record_id in selected.values():
        active = api.get_maintenance_status("src", "wiki", record_id=record_id)
        record, = active["records"]
        ack = api.acknowledge_maintenance(
            "src", "wiki", record_id=record_id, expected_state_hash=active["state_hash"],
            expected_basis=record["expected_basis"], actor_kind="human", actor_id="fixture-editor",
        )
        assert ack["changed"] and ack["record_id"] == record_id
    owner = SyncManifest.load(wiki).maintenance_state
    assert owner is not None
    return {rid: deepcopy(owner["records"][rid]["acknowledgment_history"]) for rid in selected.values()}


def _call(capsys, *args, success=True, json_output=False):
    capsys.readouterr()
    common = ["--src-dir", "src", "--wiki-dir", "wiki"]
    if args[0] not in {"bootstrap", "migrate", "upgrade"}:
        common.extend(("--jobs", "1"))
    with patch("sys.argv", ["llm-wiki", *args, *common]):
        try:
            cli.main()
        except SystemExit as exc:
            code = exc.code
        else:
            code = 0
    log = capsys.readouterr()
    if success:
        assert code == 0, log.err + log.out
    else:
        assert code != 0, log.err + log.out
        assert "unrecognized arguments" not in log.err
    if json_output:
        return json.loads(log.out)
    return log.out + log.err


def _retire(capsys, *, success=True):
    return _call(capsys, "sync", "--retire-missing-source", SOURCE_PATH, success=success)


def _release_args(pages):
    return [f"--release-historical-page={path}" for path in pages]


def _preview_release(capsys, wiki, pages):
    before = _snapshot(wiki)
    output = _call(capsys, "sync", "--dry-run", *_release_args(pages))
    matches = re.findall(r"^\s*Historical release digest: (sha256:[0-9a-f]{64})\s*$", output, re.MULTILINE)
    assert len(matches) == 1, output
    assert _snapshot(wiki) == before
    return matches[0]


def _release(capsys, pages, digest):
    return _call(capsys, "sync", *_release_args(pages), f"--expected-historical-release={digest}")


def _release_events(wiki):
    native = load_knowledge_state(wiki)
    assert native.validated_artifacts is not None and native.knowledge is not None
    ledger = SyncManifest.load(wiki).generation_inputs[RELEASES]
    assert native.knowledge.extensions[RELEASE_EXTENSION] == ledger
    events = {event["digest"]: event["basis"] for event in ledger["events"]}
    assert len(events) == len(ledger["events"])
    return events


def _new_producer(monkeypatch):
    # Simulate a later release at the same producer-version inputs used by real sync.
    for owner in (bootstrap_cmd, sync_cmd, bootstrap_runtime, knowledge_orchestration):
        monkeypatch.setattr(owner, "__version__", "9.8.7")


def _assert_ack_history(wiki, acknowledgments, *, archived=False):
    owner = SyncManifest.load(wiki).maintenance_state
    if acknowledgments is None:
        assert owner is None
        return
    assert owner is not None
    for record_id, history in acknowledgments.items():
        record = owner["records"][record_id]
        assert history and record["acknowledgment_history"] == history
        if archived:
            observation = owner["observations"][record_id]
            assert record["status"] == "pending" and record["current_acknowledgment_id"] is None
            assert (observation["presence"], observation["target_presence"]) == ("deleted", "present")


@pytest.mark.parametrize("producer_transition", ["unchanged", "at-deletion", "after-enrollment"])
def test_whole_source_preserves_canonical_pages_and_truthful_historical_evidence(
    project, monkeypatch, capsys, producer_transition
):
    src, wiki = project
    acknowledgments = None if producer_transition == "unchanged" else _acknowledge(wiki)
    native = load_knowledge_state(wiki)
    assert native.validated_artifacts is not None and native.knowledge is not None
    previous = SyncManifest.load(wiki)
    pages = {path: (wiki / path).read_bytes() for path in PAGES}
    assert all(PROSE[path][1].encode() in raw and f"author-owned bytes — {path}".encode() in raw for path, raw in pages.items())
    owners = {path: previous.page_source_mappings[path].to_payload() for path in PAGES}
    bases = {path: previous.evidence_baselines[path].basis.to_evidence_payload() for path in PAGES}
    assert all(basis["source_content_hash"] == _hash(SOURCE.encode()) for basis in bases.values())
    producer_hash = hash_json(knowledge_index_to_payload(native.knowledge)["bundle"]["producer"])
    knowledge_hash = native.validated_artifacts.knowledge_index_hash

    (src / SOURCE_PATH).unlink()
    if producer_transition == "at-deletion":
        _new_producer(monkeypatch)
    _retire(capsys)
    if producer_transition == "after-enrollment":
        enrolled = deepcopy(SyncManifest.load(wiki).generation_inputs[REGISTRY])
        _new_producer(monkeypatch)
        _call(capsys, "sync")
        assert SyncManifest.load(wiki).generation_inputs[REGISTRY] == enrolled

    state = load_knowledge_state(wiki)
    assert state.knowledge is not None and state.validated_artifacts is not None
    manifest = SyncManifest.load(wiki)
    assert SOURCE_PATH not in manifest.sources
    registry = manifest.generation_inputs[REGISTRY]
    assert registry["schema_version"] == "llm-wiki-historical-source-files/v1"
    assert set(registry["pages"]) == set(PAGES)
    index = (wiki / "index.md").read_text(encoding="utf-8")
    assert index.splitlines().count(HEADING) == 1
    section = index.split(HEADING, 1)[1].split("\n## ", 1)[0]
    live = evaluate_documentation_native_freshness(knowledge=state.knowledge, manifest=manifest, source_root=src)
    assert live.report is not None
    concepts = {entry.locator: entry for entry in state.knowledge.concepts}
    for path, locator in PAGES.items():
        assert (wiki / path).read_bytes().removeprefix(HEADER.encode()) == pages[path]
        assert f"({path})" in section
        expected = {"owner": owners[path], "basis": bases[path], "page_hash": _hash(pages[path]),
                    "marked_page_hash": _hash(HEADER.encode() + pages[path]),
                    "producer_hash": producer_hash, "knowledge_hash": knowledge_hash}
        assert registry["pages"][path] == expected
        assert concepts[locator].extensions[EXTENSION] == expected
        assert manifest.page_source_mappings[path].to_payload() == owners[path] and path not in manifest.evidence_baselines
        assert locator in state.validated_artifacts.retired_locators
        answer = api.query_documentation({"operation": "concept", "value": locator}, src_dir="src", wiki_dir="wiki")
        assert answer["found"] and not answer["ambiguous"] and answer["concept"]["canonical_path"] == path
        structural = concepts[locator].facets.structure
        tombstone = manifest.tombstones[path]
        if producer_transition == "unchanged":
            assert structural.evidence == EvidenceState.PRESENT and tombstone.last_valid_basis is not None
            assert tombstone.last_valid_basis.to_evidence_payload() == bases[path]
        else:
            assert structural.evidence == EvidenceState.UNKNOWN and structural.basis is None
            assert tombstone.last_valid_basis is None and tombstone.unknown_reason == "producer-basis-incompatible"
        freshness = live.report.by_locator[locator]
        assert freshness.state == ComputedFreshness.UNKNOWN and not freshness.live_comparison_performed

    _assert_ack_history(wiki, acknowledgments, archived=True)
    stable = _snapshot(wiki)
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]
    _call(capsys, "ci-check", "--no-report", "--knowledge-drift-report")
    _retire(capsys)
    _call(capsys, "sync")
    assert _snapshot(wiki) == stable

    (src / SOURCE_PATH).write_text(SOURCE.replace("values[:3]", "values[:2]"), encoding="utf-8")
    _call(capsys, "sync", success=False)
    assert _snapshot(wiki) == stable
    (src / SOURCE_PATH).write_bytes(SOURCE.encode())
    _call(capsys, "sync")
    revived = load_knowledge_state(wiki)
    assert revived.validated_artifacts is not None and revived.manifest_basis is not None
    assert not set(PAGES.values()).intersection(revived.validated_artifacts.retired_locators)
    assert REGISTRY not in revived.manifest_basis.generation_inputs
    assert HEADING not in (wiki / "index.md").read_text(encoding="utf-8").splitlines()
    for path in PAGES:
        assert revived.manifest_basis.evidence_baselines[path].is_known and path not in revived.manifest_basis.tombstones
        text = (wiki / path).read_text(encoding="utf-8")
        assert not text.startswith(HEADER) and PROSE[path][1] in text and f"author-owned bytes — {path}" in text
    _assert_ack_history(wiki, acknowledgments)
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]


@pytest.mark.parametrize("gap", ["active-source", "mixed-active-and-missing", "missing-markdown", "edited-page", "prior-deletion"])
def test_retirement_refuses_without_a_complete_exact_predecessor(project, capsys, gap):
    src, wiki = project
    if gap != "active-source":
        (src / SOURCE_PATH).unlink()
    if gap == "prior-deletion":
        _call(capsys, "sync")
        ordinary = api.lint_wiki("src", "wiki", strict=True)
        assert not ordinary["ok"] and any(Path(p).stem in json.dumps(ordinary["issues"]) for p in PAGES)
    elif gap == "missing-markdown":
        (wiki / ENTITY).unlink()
    elif gap == "edited-page":
        page = wiki / MODULE
        page.write_bytes(page.read_bytes() + b"\nUncommitted author revision.\n")
    beforehand = _snapshot(wiki), _snapshot(src)
    if gap == "mixed-active-and-missing":
        _call(capsys, "sync", "--retire-missing-source", SOURCE_PATH, "--retire-missing-source", "current.py", success=False)
    else:
        _retire(capsys, success=False)
    assert (_snapshot(wiki), _snapshot(src)) == beforehand


def test_unowned_stale_page_is_not_an_enrolled_source(project, capsys):
    src, wiki = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    unrelated = wiki / "entities/Unowned.md"
    unrelated.write_text(HEADER + "# Unowned\n\n**Location:** `former.py:3`\n\n## Description\n\nUnauthenticated note.\n", encoding="utf-8")
    saved = _snapshot(wiki)
    lint = api.lint_wiki("src", "wiki", strict=True)
    assert not lint["ok"] and "Unowned" in json.dumps(lint["issues"])
    _call(capsys, "ci-check", "--no-report", success=False)
    assert _snapshot(wiki) == saved
    assert "entities/Unowned.md" not in SyncManifest.load(wiki).generation_inputs[REGISTRY]["pages"]



def _assert_invalid_history_reports(capsys, *, entity_present, undocumented=None):
    lint = api.lint_wiki("src", "wiki", strict=True)
    ci = _call(capsys, "ci-check", "--no-report", "--format", "json", success=False, json_output=True)
    for report in (lint, ci):
        assert not report["ok"] and report["issue_count"] == len(report["issues"])
        issues = report["issues"]
        assert any(issue.get("reason_code") == "historical-source-invalid" for issue in issues)
        assert any(issue["category"] == "stale_modules" and issue.get("target") == "former" for issue in issues)
        if entity_present:
            assert any(issue["category"] == "stale_entities" and issue.get("target") == "ReadingWindow" for issue in issues)
        else:
            assert any(ENTITY in issue["message"] for issue in issues)
        if undocumented:
            assert any(issue["category"] == "undocumented_classes" and issue.get("target") == undocumented for issue in issues)


@pytest.mark.parametrize("target_enrolled", [False, True], ids=["missing-projection", "different-projection"])
def test_manifest_only_history_cannot_exempt_stale_pages(project, capsys, target_enrolled):
    src, wiki = project
    comparison = shutil.copytree(wiki, src.parent / "comparison")
    # A legitimate independently committed generation differs only in an unrelated
    # page. Its historical rows have the same owners and page bytes, but point
    # to a genuinely different predecessor knowledge digest.
    unrelated = comparison / "entities/CurrentReading.md"
    unrelated.write_bytes(unrelated.read_bytes() + b"\n## Notes\n\nA different editorial revision.\n")
    api.sync_wiki("src", "comparison")
    (src / SOURCE_PATH).unlink()
    api.sync_wiki("src", "comparison", retire_missing_sources=[SOURCE_PATH])
    genuine = SyncManifest.load(comparison).generation_inputs[REGISTRY]
    if target_enrolled:
        _retire(capsys)
    else:
        _call(capsys, "sync")
    before = _snapshot(wiki)
    manifest = SyncManifest.load(wiki)
    if target_enrolled:
        previous = manifest.generation_inputs[REGISTRY]["pages"]
        for path, row in genuine["pages"].items():
            assert {field for field in row if row[field] != previous[path][field]} == {"knowledge_hash"}
    else:
        assert REGISTRY not in manifest.generation_inputs
    manifest.generation_inputs[REGISTRY] = deepcopy(genuine)
    manifest.save(wiki)
    after = _snapshot(wiki)
    assert {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)} == {MANIFEST_FILENAME}
    (src / "pending.py").write_text("class PendingReading:\n    count: int = 1\n", encoding="utf-8")
    _assert_invalid_history_reports(capsys, entity_present=True, undocumented="PendingReading")
    assert _snapshot(wiki) == after


@pytest.mark.parametrize("damage", ["edited", "deleted"])
def test_invalid_enrolled_markdown_revokes_coverage_without_crashing(project, capsys, damage):
    src, wiki = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    page = wiki / ENTITY
    if damage == "edited":
        page.write_bytes(page.read_bytes() + b"\nContent outside the archived commitment.\n")
    else:
        page.unlink()
    before = _snapshot(wiki)
    _assert_invalid_history_reports(capsys, entity_present=page.exists())
    _retire(capsys, success=False)
    assert _snapshot(wiki) == before


def test_source_directory_mutation_reports_an_invalid_history_without_suppressing_ordinary_lint(project, capsys, monkeypatch):
    from llm_wiki_cli.services import historical_sources, source_snapshot
    from llm_wiki_engine import filesystem_guard

    src, wiki = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    before = _snapshot(wiki)
    checked = []
    original = historical_sources.confirm_absence

    def racing_confirmation(snapshot, selected):
        assert selected == {SOURCE_PATH}
        changed = False
        target = filesystem_guard if os.name == "nt" else os
        name = "fresh_no_follow_stat" if os.name == "nt" else "stat"
        original_stat = getattr(target, name)

        def stat_during_edit(path, *args, **kwargs):
            nonlocal changed
            is_selected = (Path(path) == src / SOURCE_PATH if os.name == "nt" else
                           path == SOURCE_PATH and kwargs.get("dir_fd") is not None)
            if not changed and is_selected:
                changed = True
                previous = src.stat()
                (src / f".membership-change-{len(checked)}").write_bytes(b"concurrent source editor\n")
                os.utime(src, ns=(previous.st_atime_ns, previous.st_mtime_ns + 2_000_000_000))
            return original_stat(path, *args, **kwargs)

        with patch.object(target, name, stat_during_edit):
            try:
                return original(snapshot, selected)
            except source_snapshot.SourceSnapshotMutationError as exc:
                assert changed and "directory changed" in str(exc)
                checked.append(exc.field)
                raise

    monkeypatch.setattr(historical_sources, "confirm_absence", racing_confirmation)
    _assert_invalid_history_reports(capsys, entity_present=True)
    assert checked == ["source", "source"] and _snapshot(wiki) == before


def test_chunked_legacy_migration_preserves_the_entire_enrolled_workspace(project, capsys):
    src, wiki = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    root = src.parent
    (root / ".gitignore").write_bytes(b"# Maintainer-owned rules\n*.scratch\n")
    before = _snapshot(root)
    refusal = _call(capsys, "migrate", "--chunk-size", "1", "--chunk", "1", success=False)
    assert "--release-historical-page" in refusal
    assert _snapshot(root) == before
    digest = _preview_release(capsys, wiki, list(PAGES))
    _release(capsys, list(PAGES), digest)
    stable = _snapshot(wiki)
    _call(capsys, "migrate", "--chunk-size", "1", "--chunk", "1", "--dry-run")
    assert _snapshot(wiki) == stable


@pytest.mark.parametrize(
    "command", [("upgrade", "--agent", "generic", "--no-skills"),
                ("sync", "--initialize-surfaces", "flows")], ids=["upgrade", "surface-only-index"],
)
def test_public_index_writers_defer_to_explicit_release_without_changing_the_workspace(project, capsys, command):
    src, wiki = project
    subprocess.run(["git", "init", "-q", str(src.parent)], check=True)
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    (src.parent / ".gitignore").write_bytes(b"# Maintainer-owned rules\n*.scratch\n")
    before = _snapshot(src.parent)
    refusal = _call(capsys, *command, success=False)
    assert "--release-historical-page" in refusal
    assert _snapshot(src.parent) == before
    manifest = SyncManifest.load(wiki)
    assert set(manifest.generation_inputs[REGISTRY]["pages"]) == set(PAGES)
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]
    digest = _preview_release(capsys, wiki, list(PAGES))
    _release(capsys, list(PAGES), digest)
    events = _release_events(wiki)
    _call(capsys, *command)
    assert _release_events(wiki) == events


@pytest.mark.parametrize("operation", ["rebuild", "sharded-format", "scoped-known-source", "existing-bootstrap"])
def test_supported_writer_options_respect_enrolled_pages_and_native_proof(project, capsys, operation):
    from llm_wiki_engine.knowledge_artifacts import current_knowledge_format

    src, wiki = project
    acknowledgments = _acknowledge(wiki) if operation == "scoped-known-source" else None
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    records = deepcopy(SyncManifest.load(wiki).generation_inputs[REGISTRY]["pages"])
    before = _snapshot(wiki)
    if operation == "existing-bootstrap":
        response = _call(capsys, "bootstrap", "--knowledge-format", "v1", success=False)
        assert "first-use only" in response and _snapshot(wiki) == before
    else:
        options = {"rebuild": ["--rebuild-knowledge"], "sharded-format": ["--knowledge-format", "sharded-v2"],
                   "scoped-known-source": ["--no-plugins", "--repair-evidence", "current.py"]}[operation]
        _call(capsys, "sync", *options, "--dry-run")
        assert _snapshot(wiki) == before
        response = _call(capsys, "sync", *options)
        if operation == "sharded-format":
            assert current_knowledge_format(wiki) == "sharded-v2"
        if operation == "scoped-known-source":
            assert "no scoped publication" in response.lower() and _snapshot(wiki) == before
    now = load_knowledge_state(wiki)
    assert now.validated_artifacts is not None and now.knowledge is not None
    assert SyncManifest.load(wiki).generation_inputs[REGISTRY]["pages"] == records
    concepts = {entry.document.canonical_path: entry for entry in now.knowledge.concepts}
    for path, row in records.items():
        assert (wiki / path).read_bytes() == before[path][0] and concepts[path].extensions[EXTENSION] == row
    _assert_ack_history(wiki, acknowledgments, archived=True)
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]
    _call(capsys, "ci-check", "--no-report")


def test_no_preserve_semantic_refuses_to_discard_archived_authorship_on_exact_revival(project, capsys):
    src, wiki = project
    originals = {path: (wiki / path).read_bytes() for path in PAGES}
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    (src / SOURCE_PATH).write_bytes(SOURCE.encode())
    before = _snapshot(src.parent)
    refusal = _call(capsys, "sync", "--no-preserve-semantic", success=False)
    assert "--release-historical-page" in refusal
    assert _snapshot(src.parent) == before
    _call(capsys, "sync")
    assert REGISTRY not in SyncManifest.load(wiki).generation_inputs
    assert {path: (wiki / path).read_bytes() for path in PAGES} == originals
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]


def test_release_requires_preview_bound_to_the_selected_pages_and_current_snapshot(project, capsys):
    src, wiki = project
    acknowledgments = _acknowledge(wiki)
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    before = _snapshot(wiki)
    custody = deepcopy(SyncManifest.load(wiki).generation_inputs[REGISTRY]["pages"])
    original_pages = {path: (wiki / path).read_bytes() for path in PAGES}
    approved = _preview_release(capsys, wiki, [ENTITY])
    other = _preview_release(capsys, wiki, [MODULE])
    assert approved != other
    for args in ((), (f"--expected-historical-release={other}",)):
        _call(capsys, "sync", *_release_args([ENTITY]), *args, success=False)
        assert _snapshot(wiki) == before
    result = api.sync_wiki("src", "wiki", release_historical_pages=[ENTITY], expected_historical_release=approved)
    assert result.historical_release == {"digest": approved, "pages": [ENTITY], "applied": True, "replayed": False}
    stable = _snapshot(wiki)
    repeated = api.sync_wiki("src", "wiki", release_historical_pages=[ENTITY], expected_historical_release=approved)
    assert repeated.historical_release == {**result.historical_release, "replayed": True}
    replay_preview = api.sync_wiki("src", "wiki", dry_run=True, release_historical_pages=[ENTITY], expected_historical_release=approved)
    assert replay_preview.historical_release == {**result.historical_release, "applied": False, "replayed": True}
    assert _snapshot(wiki) == stable
    manifest = SyncManifest.load(wiki)
    assert manifest.generation_inputs[REGISTRY]["pages"] == {MODULE: custody[MODULE]}
    assert {path: (wiki / path).read_bytes() for path in PAGES} == original_pages
    native = load_knowledge_state(wiki)
    concepts = {entry.document.canonical_path: entry for entry in native.knowledge.concepts}
    assert EXTENSION not in concepts[ENTITY].extensions and concepts[MODULE].extensions[EXTENSION] == custody[MODULE]
    section = (wiki / "index.md").read_text(encoding="utf-8").split(HEADING, 1)[1].split("\n## ", 1)[0]
    assert f"({MODULE})" in section and f"({ENTITY})" not in section
    first_events = _release_events(wiki)
    assert set(first_events) == {approved}
    assert first_events[approved]["pages"] == {ENTITY: {
        "record": custody[ENTITY], "retained_page_hash": _hash(original_pages[ENTITY]),
    }}
    _assert_ack_history(wiki, acknowledgments, archived=True)
    lint = api.lint_wiki("src", "wiki", strict=True)
    assert any(issue["category"] == "stale_entities" and issue.get("target") == "ReadingWindow" for issue in lint["issues"])
    assert not any(issue["category"] == "stale_modules" and issue.get("target") == "former" for issue in lint["issues"])
    ci = _call(capsys, "ci-check", "--no-report", "--format", "json", success=False, json_output=True)
    assert any(issue["category"] == "stale_entities" and issue.get("target") == "ReadingWindow" for issue in ci["issues"])
    current = _snapshot(wiki)
    _call(capsys, "sync", *_release_args([MODULE]), f"--expected-historical-release={other}", success=False)
    assert _snapshot(wiki) == current
    last = _preview_release(capsys, wiki, [MODULE])
    assert last != other
    _release(capsys, [MODULE], last)
    last_events = _release_events(wiki)
    assert set(last_events) == {approved, last}
    assert last_events[approved] == first_events[approved]
    assert last_events[approved]["parent"] is None and last_events[last]["parent"] == approved
    assert last_events[last]["pages"] == {MODULE: {
        "record": custody[MODULE], "retained_page_hash": _hash(original_pages[MODULE]),
    }}
    assert REGISTRY not in SyncManifest.load(wiki).generation_inputs
    assert HEADING not in (wiki / "index.md").read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize("damage", ["changed", "deleted", "line-endings", "index"])
def test_release_is_recoverable_only_after_restoring_the_exact_approved_bytes(project, capsys, damage):
    src, wiki = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    digest = _preview_release(capsys, wiki, [ENTITY])
    path = wiki / ("index.md" if damage == "index" else ENTITY)
    original = path.read_bytes()
    if damage == "deleted":
        path.unlink()
    elif damage == "line-endings":
        assert b"\r\n" not in original
        path.write_bytes(original.replace(b"\n", b"\r\n"))
    elif damage == "index":
        path.write_bytes(original.replace(HEADING.encode(), b"### Different index heading"))
    else:
        path.write_bytes(original + b"\nA new editorial revision.\n")
    damaged = _snapshot(wiki)
    _call(capsys, "sync", "--dry-run", *_release_args([ENTITY]), success=False)
    _call(capsys, "sync", *_release_args([ENTITY]), f"--expected-historical-release={digest}", success=False)
    assert _snapshot(wiki) == damaged
    path.write_bytes(original)
    confirmed = _preview_release(capsys, wiki, [ENTITY])
    _release(capsys, [ENTITY], confirmed)
    if damage != "index":
        assert path.read_bytes() == original
    assert confirmed in _release_events(wiki)


@pytest.mark.parametrize("phase", ["preview", "apply"])
def test_concurrent_author_edit_is_kept_and_no_release_is_committed(project, capsys, monkeypatch, phase):
    from llm_wiki_cli.services import historical_release

    src, wiki = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    digest = _preview_release(capsys, wiki, [ENTITY])
    initial = {path: raw for path, (raw, _) in _snapshot(wiki).items()}
    edited = initial[MODULE] + b"\nConcurrent field editor update.\n"
    if phase == "preview":
        original = historical_release.commit_knowledge_artifacts

        def editing_preview(plan, *, dry_run):
            assert dry_run
            result = original(plan, dry_run=dry_run)
            (wiki / MODULE).write_bytes(edited)
            return result

        monkeypatch.setattr(historical_release, "commit_knowledge_artifacts", editing_preview)
        options = ["--dry-run"]
    else:
        original = historical_release.write_bytes_atomic

        def editing_apply(path, content):
            original(path, content)
            if path.name == "index.md" and content != initial["index.md"]:
                (wiki / MODULE).write_bytes(edited)

        monkeypatch.setattr(historical_release, "write_bytes_atomic", editing_apply)
        options = [f"--expected-historical-release={digest}"]
    result = _call(capsys, "sync", *_release_args([ENTITY]), *options, success=False)
    assert "Historical release digest:" not in result
    assert {path: raw for path, (raw, _) in _snapshot(wiki).items()} == {**initial, MODULE: edited}
    assert RELEASES not in SyncManifest.load(wiki).generation_inputs


@pytest.mark.parametrize("profile", ["v1", "sharded-v2", "adopted-v1"])
def test_concurrent_editor_during_knowledge_publication_preserves_the_predecessor_and_allows_retry(
    project, capsys, monkeypatch, profile
):
    from llm_wiki_cli.services import historical_release
    from llm_wiki_engine.knowledge_artifacts import CommitStage
    from llm_wiki_engine.maintenance_protocol import ADOPTION_FILENAME

    src, wiki = project
    if profile == "sharded-v2":
        api.sync_wiki("src", "wiki", knowledge_format=profile)
    acknowledgments = _acknowledge(wiki) if profile == "adopted-v1" else None
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    digest = _preview_release(capsys, wiki, [ENTITY])
    roots = ["index.md", ".llm-wiki-surface.json", ".llm-wiki-knowledge.json", MANIFEST_FILENAME]
    previous = {name: (wiki / name).read_bytes() for name in roots}
    marker = before_marker = None
    if profile == "adopted-v1":
        marker = wiki / ADOPTION_FILENAME
        before_marker = (marker.read_bytes(), marker.stat().st_ino, marker.stat().st_mtime_ns)
    selected = wiki / ENTITY
    original = selected.read_bytes()
    edited = original + b"\nField editor: a correction to the original page.\n"
    captured = []
    original_commit = historical_release.commit_knowledge_artifacts

    def concurrent_commit(plan, **kwargs):
        if marker is not None:
            assert plan.maintenance_adoption is not None and not plan.maintenance_adoption.needs_write
        existing_hook = kwargs.pop("fault_injector", None)

        def editor(stage):
            if stage == CommitStage.KNOWLEDGE_INDEX_WRITTEN:
                assert (wiki / "index.md").read_bytes() != previous["index.md"]
                assert (wiki / ".llm-wiki-knowledge.json").read_bytes() != previous[".llm-wiki-knowledge.json"]
                assert (wiki / MANIFEST_FILENAME).read_bytes() == previous[MANIFEST_FILENAME]
                assert selected.read_bytes() == original
                selected.write_bytes(edited)
                captured.append(stage)
            if existing_hook:
                existing_hook(stage)

        return original_commit(plan, fault_injector=editor, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(historical_release, "commit_knowledge_artifacts", concurrent_commit)
        result = _call(capsys, "sync", *_release_args([ENTITY]), f"--expected-historical-release={digest}", success=False)
    assert captured == [CommitStage.KNOWLEDGE_INDEX_WRITTEN] and "Historical release digest:" not in result
    assert selected.read_bytes() == edited
    assert all((wiki / name).read_bytes() == raw for name, raw in previous.items())
    manifest = SyncManifest.load(wiki)
    assert RELEASES not in manifest.generation_inputs and set(manifest.generation_inputs[REGISTRY]["pages"]) == set(PAGES)
    _assert_ack_history(wiki, acknowledgments, archived=True)
    _assert_invalid_history_reports(capsys, entity_present=True)

    # The editor saves their own newer text before the verified original is
    # restored for a new preview. The release itself never rewrites either.
    editor_copy = src.parent / "editor-revision.md"
    selected.rename(editor_copy)
    selected.write_bytes(original)
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]
    fresh = _preview_release(capsys, wiki, [ENTITY])
    _release(capsys, [ENTITY], fresh)
    assert list(_release_events(wiki)) == [fresh]
    stable = _snapshot(wiki)
    again = api.sync_wiki("src", "wiki", release_historical_pages=[ENTITY], expected_historical_release=fresh)
    assert again.historical_release["replayed"] and _snapshot(wiki) == stable
    assert selected.read_bytes() == original and editor_copy.read_bytes() == edited
    if marker is not None:
        assert (marker.read_bytes(), marker.stat().st_ino, marker.stat().st_mtime_ns) == before_marker
    _assert_ack_history(wiki, acknowledgments, archived=True)


@pytest.mark.parametrize("replacement", ["same-class", "same-module", "edited-original"])
def test_release_and_separate_tracked_archive_allow_a_genuinely_fresh_current_owner(project, capsys, replacement):
    src, wiki = project
    subprocess.run(["git", "init", "-q", str(src.parent)], check=True)
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    if replacement == "same-class":
        new_source, pages = "later.py", [ENTITY]
        new_code = '"""A later collection."""\nclass ReadingWindow:\n    """A new station interval."""\n    zone: str = "north"\n'
    elif replacement == "same-module":
        new_source, pages = "nested/former.py", [MODULE]
        new_code = '"""Collect station intervals."""\nclass StationInterval:\n    """A fresh station reading."""\n    zone: str = "south"\n'
    else:
        new_source, pages = SOURCE_PATH, list(PAGES)
        new_code = SOURCE.replace("retained sample", "fresh station").replace("values[:3]", "values[:2]")
    source_file = src / new_source
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text(new_code, encoding="utf-8")
    before = _snapshot(wiki)
    refusal = _call(capsys, "sync", success=False)
    assert "--release-historical-page" in refusal
    assert _snapshot(wiki) == before
    custody = {path: (wiki / path).read_bytes() for path in pages}
    digest = _preview_release(capsys, wiki, pages)
    _release(capsys, pages, digest)
    event = _release_events(wiki)[digest]
    measured = _snapshot(wiki)
    held = _call(capsys, "sync", success=False)
    assert "released" in held.lower() and _snapshot(wiki) == measured
    archive = src.parent / "history"
    for path, raw in custody.items():
        assert (wiki / path).read_bytes() == raw
        assert event["pages"][path]["retained_page_hash"] == _hash(raw)
        saved = archive / path
        saved.parent.mkdir(parents=True, exist_ok=True)
        (wiki / path).rename(saved)
        relative = saved.relative_to(src.parent).as_posix()
        subprocess.run(["git", "add", "--", relative], check=True)
        assert subprocess.run(["git", "show", f":{relative}"], check=True, capture_output=True).stdout == raw
    _call(capsys, "sync")
    manifest = SyncManifest.load(wiki)
    for path, raw in custody.items():
        current = (wiki / path).read_bytes()
        assert not current.startswith(HEADER.encode()) and PROSE[path][1].encode() not in current
        assert f"author-owned bytes — {path}".encode() not in current
        assert manifest.page_source_mappings[path].source_path == new_source
        assert manifest.evidence_baselines[path].basis.source_content_hash == _hash(new_code.encode())
        assert (archive / path).read_bytes() == raw
    assert _release_events(wiki)[digest] == event
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]

    stable = _snapshot(wiki)
    _call(capsys, "sync")
    assert _snapshot(wiki) == stable

    # The new author's editorial record is independent from the older entry
    # in the permanent release audit, even when both occupy the same URL.
    for path in pages:
        page = wiki / path
        page.write_bytes(page.read_bytes() + ("\n## Notes\n\nCurrent field notes — "+path+".\n").encode())
    _call(capsys, "sync")
    newer_pages = {path: (wiki / path).read_bytes() for path in pages}
    source_file.unlink()
    _call(capsys, "sync")
    deleted = SyncManifest.load(wiki)
    assert all(path in deleted.tombstones and deleted.page_source_mappings[path].source_path == new_source for path in pages)
    source_file.write_text(new_code, encoding="utf-8")
    if replacement != "edited-original":
        companion, = (path for path, owner in deleted.page_source_mappings.items()
                      if owner.source_path == new_source and path in deleted.tombstones and path not in pages)
        sibling = wiki / companion
        original_companion = sibling.read_bytes()
        sibling.write_bytes(original_companion + b"\nA separate editor changed only the sibling.\n")
        uncommitted = _snapshot(wiki)
        _call(capsys, "sync", success=False)
        assert _snapshot(wiki) == uncommitted
        sibling.write_bytes(original_companion)
    _call(capsys, "sync")
    revived = SyncManifest.load(wiki)
    for path in pages:
        assert path not in revived.tombstones and revived.evidence_baselines[path].basis.source_content_hash == _hash(new_code.encode())
        assert (wiki / path).read_bytes() == newer_pages[path]
        assert (archive / path).read_bytes() == custody[path]
    assert _release_events(wiki)[digest] == event
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]


def test_exact_original_source_can_reclaim_its_measured_released_markdown_in_place(project, capsys):
    src, wiki = project
    original = {path: (wiki / path).read_bytes() for path in PAGES}
    previous = SyncManifest.load(wiki)
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    digest = _preview_release(capsys, wiki, list(PAGES))
    _release(capsys, list(PAGES), digest)
    event = _release_events(wiki)[digest]
    assert all(event["pages"][path]["retained_page_hash"] == _hash((wiki / path).read_bytes()) for path in PAGES)
    (src / SOURCE_PATH).write_bytes(SOURCE.encode())
    before = _snapshot(wiki)
    _call(capsys, "sync", "--dry-run")
    assert _snapshot(wiki) == before
    _call(capsys, "sync")
    manifest = SyncManifest.load(wiki)
    for path in PAGES:
        assert manifest.page_source_mappings[path].to_payload() == previous.page_source_mappings[path].to_payload()
        assert manifest.evidence_baselines[path].basis.source_content_hash == _hash(SOURCE.encode()) and path not in manifest.tombstones
        assert (wiki / path).read_bytes() == original[path]
    assert REGISTRY not in manifest.generation_inputs and _release_events(wiki)[digest] == event
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]
    _call(capsys, "ci-check", "--no-report")


def test_release_frees_a_real_generated_link_repair_without_altering_its_original_audit(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    src, wiki = tmp_path / "src", tmp_path / "wiki"
    src.mkdir()
    (src / SOURCE_PATH).write_text(
        '"""Prior readings."""\nfrom current import CurrentReading\n\nclass ReadingWindow(CurrentReading):\n'
        '    """Prior measurement."""\n    def measurement(self):\n        return CurrentReading()\n', encoding="utf-8",
    )
    (src / "current.py").write_text('class CurrentReading:\n    """A live measurement."""\n    count: int = 1\n', encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1", skip_flows=True, skip_workflows=True)
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    before = {path: (wiki / path).read_bytes() for path in PAGES}
    assert all(b'../modules/current.md' in data for data in before.values())
    (src / "nested").mkdir()
    (src / "nested/current.py").write_text('class AnotherReading:\n    separate: str = "north"\n', encoding="utf-8")
    original = _snapshot(wiki)
    refusal = _call(capsys, "sync", success=False)
    assert "--release-historical-page" in refusal
    assert _snapshot(wiki) == original
    digest = _preview_release(capsys, wiki, list(PAGES))
    _release(capsys, list(PAGES), digest)
    assert {path: (wiki / path).read_bytes() for path in PAGES} == before
    _call(capsys, "sync")
    manifest = SyncManifest.load(wiki)
    link_target, = (path for path, owner in manifest.page_source_mappings.items()
                    if owner.scope == "module" and owner.source_path == "current.py" and path not in manifest.tombstones)
    assert link_target != "modules/current.md"
    for path, raw in before.items():
        repaired = (wiki / path).read_bytes()
        assert f"../{link_target}".encode() in repaired and b'../modules/current.md' not in repaired
        assert _release_events(wiki)[digest]["pages"][path]["retained_page_hash"] == _hash(raw)


def test_fresh_enrollment_refuses_a_different_source_claiming_the_canonical_module(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    src, wiki = tmp_path / "src", tmp_path / "wiki"
    old = src / "old/path/report.py"
    old.parent.mkdir(parents=True)
    old.write_text('"""Describe the former report."""\nclass FormerReport:\n    count: int = 3\n', encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    page = "modules/report.md"
    assert SyncManifest.load(wiki).page_source_mappings[page].source_path == "old/path/report.py"
    original = (wiki / page).read_text(encoding="utf-8")
    assert "Describe the former report." in original
    (wiki / page).write_text(original.replace("Describe the former report.", "Authors documented this earlier report."), encoding="utf-8")
    api.sync_wiki("src", "wiki")
    old.unlink()
    replaced = src / "new/path/report.py"
    replaced.parent.mkdir(parents=True)
    replaced.write_text('"""Format a fresh report."""\nclass ReplacementReport:\n    account: str = ""\n', encoding="utf-8")
    # Establish that the new source genuinely owns this canonical path when
    # bootstrapped independently; a same-named file alone is not a transfer.
    api.bootstrap_wiki("src", "new-surface", knowledge_format="v1")
    assert SyncManifest.load(tmp_path / "new-surface").page_source_mappings[page].source_path == "new/path/report.py"
    (tmp_path / ".gitignore").write_text("# Preserve existing workspace rules\n", encoding="utf-8")
    before = _snapshot(tmp_path)
    refusal = _call(capsys, "sync", "--retire-missing-source", "old/path/report.py", success=False)
    assert "historical" in refusal.lower()
    assert _snapshot(tmp_path) == before


@pytest.fixture
def mixed_transfer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src, wiki = tmp_path / "src", tmp_path / "wiki"
    src.mkdir()
    moving = 'class TransferCounter:\n    """An active counter carried forward."""\n    value: int = 2\n'
    former = (
        '"""Earlier counters."""\n\nclass ObsoleteCounter:\n    """An earlier counter."""\n    size: int = 4\n\n'
        + moving
    )
    (src / SOURCE_PATH).write_text(former, encoding="utf-8")
    (src / "other.py").write_text('class OtherCounter:\n    value: int = 1\n', encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1", skip_flows=True, skip_workflows=True)
    paths = ["modules/former.md", "entities/ObsoleteCounter.md", "entities/TransferCounter.md"]
    for path in paths:
        page = wiki / path
        text = page.read_text(encoding="utf-8")
        assert "\n## Description\n\n" in text
        page.write_text(text.replace("\n## Description\n\n", "\n## Description\n\nOriginal editorial context. ", 1), encoding="utf-8")
    api.sync_wiki("src", "wiki")
    before = SyncManifest.load(wiki)
    assert all(before.page_source_mappings[p].source_path == SOURCE_PATH for p in paths)
    original = {p: (wiki / p).read_bytes() for p in paths}
    (src / SOURCE_PATH).unlink()
    (src / "relocated.py").write_text('"""Current counters."""\n\n' + moving, encoding="utf-8")
    (tmp_path / ".gitignore").write_text("# Human-maintained rules\n*.scratch\n", encoding="utf-8")
    return src, wiki, original


def test_exact_page_selection_leaves_the_surviving_entity_with_its_live_source(mixed_transfer, capsys):
    src, wiki, original = mixed_transfer
    archived = ["modules/former.md", "entities/ObsoleteCounter.md"]
    survivor = "entities/TransferCounter.md"
    _call(capsys, "sync", "--retire-missing-source", SOURCE_PATH, "--retire-missing-page", archived[0],
          "--retire-missing-page", archived[1])
    manifest = SyncManifest.load(wiki)
    registered = manifest.generation_inputs[REGISTRY]["pages"]
    assert set(registered) == set(archived)
    before_hash = _hash((src / "relocated.py").read_bytes())
    assert manifest.page_source_mappings[survivor].source_path == "relocated.py"
    assert manifest.evidence_baselines[survivor].basis.source_content_hash == before_hash
    assert survivor not in manifest.tombstones
    native = load_knowledge_state(wiki)
    assert native.knowledge is not None and native.validated_artifacts is not None
    concepts = {c.document.canonical_path: c for c in native.knowledge.concepts}
    assert EXTENSION not in concepts[survivor].extensions
    assert concepts[survivor].locator not in native.validated_artifacts.retired_locators
    assert "Original editorial context." in (wiki / survivor).read_text(encoding="utf-8")
    for path in archived:
        assert (wiki / path).read_bytes().removeprefix(HEADER.encode()) == original[path]
        assert registered[path]["page_hash"] == _hash(original[path])
        assert concepts[path].extensions[EXTENSION] == registered[path]
    assert api.lint_wiki("src", "wiki", strict=True)["ok"]
    _call(capsys, "ci-check", "--no-report", "--knowledge-drift-report")


@pytest.mark.parametrize("gap", ["live-sibling", "unbound-page", "uncovered-source", "page-without-source"])
def test_invalid_explicit_page_selection_does_not_partially_enroll_a_source(mixed_transfer, capsys, gap):
    src, _, _ = mixed_transfer
    args = ["sync", "--retire-missing-page", "modules/former.md"]
    if gap != "page-without-source":
        args.extend(("--retire-missing-source", SOURCE_PATH))
    if gap == "live-sibling":
        args.extend(("--retire-missing-page", "entities/TransferCounter.md"))
    elif gap == "unbound-page":
        args.extend(("--retire-missing-page", "entities/NeverObserved.md"))
    elif gap == "uncovered-source":
        (src / "other.py").unlink()
        args.extend(("--retire-missing-source", "other.py"))
    before = _snapshot(src.parent)
    refusal = _call(capsys, *args, success=False)
    assert "historical" in refusal.lower() or "retire-missing-source" in refusal
    assert _snapshot(src.parent) == before
