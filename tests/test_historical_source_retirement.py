"""An explicit missing-source archive preserves authored pages and authentic historical evidence."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import bootstrap_runtime, knowledge_orchestration
from llm_wiki_cli.services.documentation_native import evaluate_documentation_native_freshness
from llm_wiki_engine.knowledge_evidence import hash_json
from llm_wiki_engine.knowledge_loader import load_knowledge_state
from llm_wiki_engine.knowledge_model import ComputedFreshness, EvidenceState, knowledge_index_to_payload
from llm_wiki_engine.sync_manifest import SyncManifest


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


def _call(capsys, *args, success=True):
    capsys.readouterr()
    common = ["--src-dir", "src", "--wiki-dir", "wiki"]
    if args[0] != "migrate":
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
    return log.out + log.err


def _retire(capsys, *, success=True):
    return _call(capsys, "sync", "--retire-missing-source", SOURCE_PATH, success=success)


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



def test_edited_enrolled_markdown_does_not_keep_an_unearned_lint_exemption(project, capsys):
    src, wiki = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    page = wiki / ENTITY
    page.write_bytes(page.read_bytes() + b"\nContent outside the archived commitment.\n")
    before = _snapshot(wiki)
    lint = api.lint_wiki("src", "wiki", strict=True)
    assert not lint["ok"] and "ReadingWindow" in json.dumps(lint["issues"])
    _call(capsys, "ci-check", "--no-report", success=False)
    _retire(capsys, success=False)
    assert _snapshot(wiki) == before


def test_chunked_legacy_migration_preserves_the_entire_enrolled_workspace(project, capsys):
    src, _ = project
    (src / SOURCE_PATH).unlink()
    _retire(capsys)
    root = src.parent
    (root / ".gitignore").write_bytes(b"# Maintainer-owned rules\n*.scratch\n")
    before = _snapshot(root)
    refusal = _call(capsys, "migrate", "--chunk-size", "1", "--chunk", "1", success=False)
    assert "historical" in refusal.lower()
    assert _snapshot(root) == before


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
