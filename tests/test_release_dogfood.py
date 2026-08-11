"""Controlled release dogfood for native evidence and procedural fallbacks."""

from __future__ import annotations

import io
import json
import sys
import tarfile
import zipfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

try:
    import tomllib  # type: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[reportMissingImports]

from llm_wiki_cli.commands import init_cmd, status_cmd, uninstall_cmd, upgrade_cmd
from llm_wiki_cli.services.context_packet import build_qualified_context
from llm_wiki_cli.services.knowledge_artifacts import (
    KnowledgeCommitResult,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.schema import (
    ManagedSchemaBlockState,
    SchemaRenderProfile,
    classify_managed_schema_block,
)
from llm_wiki_cli.services.skills import (
    REFERENCE_SKILL_ID,
    ReferenceSkillState,
    skills_install_dir,
    verify_reference_skill,
)
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from tests import release_artifact_smoke
from tests.knowledge_fixtures import (
    fixture_hash,
    materialize_fixture_tree,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_artifacts import _plan as _knowledge_commit_plan


RECORD = Path(__file__).parent / "records" / "knowledge" / "release-dogfood.json"
WIKI_DIR = "docs/llm_wiki"


def _request() -> dict[str, object]:
    return {
        "budget_tokens": 32_000,
        "focus": ["all"],
        "format": "json",
        "filters": {},
        "knowledge_mode": "auto",
    }


def _tree_state(root: Path) -> dict[str, tuple[str, bytes | None]]:
    state: dict[str, tuple[str, bytes | None]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            state[relative] = ("symlink", path.readlink().as_posix().encode())
        elif path.is_dir():
            state[relative] = ("directory", None)
        else:
            state[relative] = ("file", path.read_bytes())
    return state


def _materialize_ready(
    root: Path,
) -> tuple[dict[str, Path], KnowledgeCommitResult]:
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, root)
    committed = commit_knowledge_artifacts(
        _knowledge_commit_plan(tree["wiki_root"], fixture)
    )
    return tree, committed


def _assert_bounded_native_selection(knowledge: object) -> None:
    assert isinstance(knowledge, dict)
    assert knowledge["status"] == "selected"
    assert knowledge["availability"] == "ready"
    assert knowledge["selected"] is True
    selection = knowledge["selection"]
    assert isinstance(selection, dict)
    assert selection["concepts"]
    for name in ("concepts", "pages", "relationships"):
        assert len(selection[name]) == knowledge["bounds"][name]["returned"]


def _artifact_paths(prefix: str) -> list[str]:
    return [
        f"{prefix}llm_wiki_cli/skills/wiki-reference/{relative}"
        for relative in release_artifact_smoke.EXPECTED_WIKI_REFERENCE_FILES
    ]


def _write_artifact(
    root: Path,
    kind: str,
    *,
    missing: str | None = None,
    extra: str | None = None,
    internal: bool = False,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if kind == "wheel":
        path = root / "agent_wiki_cli-1.6.0-py3-none-any.whl"
        names = _artifact_paths("")
        if extra is not None:
            names.append(f"llm_wiki_cli/skills/wiki-reference/{extra}")
        if internal:
            names.append("reports/agents-md-knowledge-first-implementation-backlog.md")
        with zipfile.ZipFile(path, mode="w") as archive:
            for name in names:
                if not name.endswith(f"/{missing}"):
                    archive.writestr(name, b"release fixture\n")
        return path

    path = root / "agent_wiki_cli-1.6.0.tar.gz"
    names = _artifact_paths("agent_wiki_cli-1.6.0/src/")
    if extra is not None:
        names.append(
            "agent_wiki_cli-1.6.0/src/llm_wiki_cli/skills/"
            f"wiki-reference/{extra}"
        )
    if internal:
        names.append(
            "agent_wiki_cli-1.6.0/reports/"
            "agents-md-knowledge-first-implementation-backlog.md"
        )
    with tarfile.open(path, mode="w:gz") as archive:
        for name in names:
            if name.endswith(f"/{missing}"):
                continue
            payload = b"release fixture\n"
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    return path


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_release_archive_requires_exact_topics_and_rejects_internal_reports(
    tmp_path: Path,
    kind: str,
) -> None:
    valid = _write_artifact(tmp_path, kind)
    assert release_artifact_smoke._validate_artifact_members(valid) == len(
        release_artifact_smoke.EXPECTED_WIKI_REFERENCE_FILES
    )

    missing = _write_artifact(
        tmp_path / "missing",
        kind,
        missing="references/maintenance.md",
    )
    with pytest.raises(release_artifact_smoke.SmokeError, match="maintenance.md"):
        release_artifact_smoke._validate_artifact_members(missing)

    extra = _write_artifact(
        tmp_path / "extra",
        kind,
        extra="references/unexpected.md",
    )
    with pytest.raises(release_artifact_smoke.SmokeError, match="unexpected.md"):
        release_artifact_smoke._validate_artifact_members(extra)

    internal = _write_artifact(tmp_path / "internal", kind, internal=True)
    with pytest.raises(release_artifact_smoke.SmokeError, match="internal report"):
        release_artifact_smoke._validate_artifact_members(internal)


def test_build_metadata_includes_every_current_topic_and_prunes_reports() -> None:
    root = Path(__file__).resolve().parents[1]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = set(
        metadata["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    )
    reference_root = root / "src" / "llm_wiki_cli" / "skills" / "wiki-reference"
    topics = {
        path.relative_to(root / "src" / "llm_wiki_cli").as_posix()
        for path in reference_root.rglob("*")
        if path.is_file()
    }
    expected = {
        f"skills/wiki-reference/{relative}"
        for relative in release_artifact_smoke.EXPECTED_WIKI_REFERENCE_FILES
    }

    assert topics == expected
    assert topics <= package_data
    assert "prune reports" in (root / "MANIFEST.in").read_text(
        encoding="utf-8"
    ).splitlines()


def test_installed_lifecycle_harness_covers_both_profiles_and_locations(
    tmp_path: Path,
) -> None:
    result = release_artifact_smoke._validate_profile_lifecycle(
        [sys.executable, "-I", "-m", "llm_wiki_cli.cli"],
        tmp_path,
    )

    assert result == {
        "generic": (
            "compact/current",
            "expanded/skills-disabled",
            "uninstalled",
        ),
        "claude": (
            "expanded/skills-disabled",
            "compact/current",
            "uninstalled",
        ),
    }
    assert not tuple(tmp_path.rglob(".gitignore"))


def test_installed_skill_harness_covers_transitive_reference_dependency(
    tmp_path: Path,
) -> None:
    result = release_artifact_smoke._validate_selected_skill_dependencies(
        [sys.executable, "-I", "-m", "llm_wiki_cli.cli"],
        tmp_path,
    )

    assert result == {
        "requested_skills": ["wiki-sync"],
        "dependency_skills": ["wiki-reference"],
        "skills": ["wiki-reference", "wiki-sync"],
    }
    assert not tuple(tmp_path.rglob(".gitignore"))


def test_ready_without_governance_selects_useful_native_evidence_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tree, _committed = _materialize_ready(tmp_path / "ready")
    root = tree["root"]
    wiki = tree["wiki_root"]
    (root / ".git" / "hooks").mkdir(parents=True)
    monkeypatch.chdir(root)
    init_cmd.run(
        SimpleNamespace(agent="generic", wiki_dir=WIKI_DIR, no_skills=False)
    )
    capsys.readouterr()
    schema = (root / "AGENTS.md").read_text(encoding="utf-8")
    block = classify_managed_schema_block(schema)
    assert block.state is ManagedSchemaBlockState.PROFILED
    assert block.profile is SchemaRenderProfile.COMPACT
    assert "--knowledge-mode auto --read-only" in schema
    assert verify_reference_skill(agent="generic").current
    assert not (wiki / ".llm-wiki-governance.json").exists()
    before = _tree_state(root)

    packet = build_qualified_context(".", WIKI_DIR, _request()).to_payload()

    _assert_bounded_native_selection(packet["response"]["knowledge"])
    assert _tree_state(root) == before
    assert not (wiki / ".llm-wiki-governance.json").exists()
    assert not (root / ".gitignore").exists()


def test_legacy_surface_only_and_mixed_projection_use_qualified_fallbacks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = one_module_two_entities_fixture()
    legacy = materialize_fixture_tree(fixture, tmp_path / "legacy")
    legacy["knowledge_path"].unlink()
    monkeypatch.chdir(legacy["root"])
    legacy_before = _tree_state(legacy["root"])

    legacy_packet = build_qualified_context(".", WIKI_DIR, _request()).to_payload()
    legacy_knowledge = legacy_packet["response"]["knowledge"]
    assert legacy_knowledge["status"] == "fallback"
    assert legacy_knowledge["availability"] == "absent"
    assert legacy_knowledge["reason"] == "knowledge-projection-not-present"
    assert legacy_knowledge["fallback"] == {
        "used": True,
        "evidence": [
            "independently-validated-surface",
            "markdown",
            "targeted-source-or-runtime",
        ],
        "reason": "knowledge-projection-not-present",
    }
    assert "selection" not in legacy_knowledge
    assert _tree_state(legacy["root"]) == legacy_before

    mixed, committed = _materialize_ready(tmp_path / "mixed")
    marker = committed.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        committed.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=fixture_hash("release-dogfood:mixed"),
        ),
    ).save(mixed["wiki_root"])
    monkeypatch.chdir(mixed["root"])
    mixed_before = _tree_state(mixed["root"])

    mixed_packet = build_qualified_context(".", WIKI_DIR, _request()).to_payload()
    mixed_knowledge = mixed_packet["response"]["knowledge"]
    assert mixed_knowledge["status"] == "fallback"
    assert mixed_knowledge["availability"] == "degraded"
    assert mixed_knowledge["reason"] == (
        "policy-selected-surface-only-fallback-after-mixed-snapshot"
    )
    assert mixed_knowledge["fallback"]["evidence"] == [
        "independently-validated-surface",
        "markdown",
        "targeted-source-or-runtime",
    ]
    assert "selection" not in mixed_knowledge
    assert _tree_state(mixed["root"]) == mixed_before
    assert not tuple(tmp_path.rglob(".gitignore"))
    assert not tuple(tmp_path.rglob(".llm-wiki-governance.json"))


def test_expanded_profile_retains_and_executes_the_knowledge_capable_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    tree, _committed = _materialize_ready(tmp_path / "expanded")
    root = tree["root"]
    (root / ".git" / "hooks").mkdir(parents=True)
    monkeypatch.chdir(root)

    init_cmd.run(
        SimpleNamespace(agent="generic", wiki_dir=WIKI_DIR, no_skills=True)
    )
    capsys.readouterr()
    schema = (root / "AGENTS.md").read_text(encoding="utf-8")
    block = classify_managed_schema_block(schema)
    assert block.state is ManagedSchemaBlockState.PROFILED
    assert block.profile is SchemaRenderProfile.EXPANDED_INLINE
    assert (
        "llm-wiki context --budget 8000 --src-dir . --wiki-dir "
        "docs/llm_wiki --format packet --focus changed --knowledge-mode auto "
        "--read-only"
    ) in schema
    for fallback in (
        "independently validated surface",
        "canonical Markdown",
        "targeted source/runtime evidence",
    ):
        assert fallback in schema

    before = _tree_state(root)
    packet = build_qualified_context(".", WIKI_DIR, _request()).to_payload()
    _assert_bounded_native_selection(packet["response"]["knowledge"])
    assert _tree_state(root) == before

    knowledge_bytes = tree["knowledge_path"].read_bytes()
    manifest_path = tree["wiki_root"] / MANIFEST_FILENAME
    manifest_bytes = manifest_path.read_bytes()
    tree["knowledge_path"].unlink()
    manifest_path.unlink()
    legacy_before = _tree_state(root)
    fallback_packet = build_qualified_context(".", WIKI_DIR, _request()).to_payload()
    fallback = fallback_packet["response"]["knowledge"]
    assert fallback["status"] == "fallback"
    assert fallback["availability"] == "absent"
    assert fallback["fallback"]["evidence"] == [
        "independently-validated-surface",
        "markdown",
        "targeted-source-or-runtime",
    ]
    assert _tree_state(root) == legacy_before
    tree["knowledge_path"].write_bytes(knowledge_bytes)
    manifest_path.write_bytes(manifest_bytes)

    status_cmd.run(
        SimpleNamespace(
            wiki_dir=WIKI_DIR,
            src_dir=".",
            allow_external_src=False,
            source_selection=None,
        )
    )
    status = capsys.readouterr().out
    assert "Managed lifecycle: expanded/skills-disabled" in status
    assert "Rendered profile: expanded_inline" in status
    assert not skills_install_dir("generic").joinpath(REFERENCE_SKILL_ID).exists()
    assert not (root / ".gitignore").exists()


def test_current_disabled_modified_and_agent_homes_preserve_local_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    generic = tmp_path / "generic"
    (generic / ".git" / "hooks").mkdir(parents=True)
    (generic / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.chdir(generic)
    init_cmd.run(
        SimpleNamespace(agent="generic", wiki_dir=WIKI_DIR, no_skills=False)
    )
    capsys.readouterr()
    generic_reference = generic / ".llm-wiki" / "skills" / REFERENCE_SKILL_ID
    assert verify_reference_skill(agent="generic").state is ReferenceSkillState.CURRENT
    assert generic_reference.is_dir()
    assert not (generic / ".claude").exists()

    modified = generic_reference / "references" / "maintenance.md"
    modified_bytes = modified.read_bytes() + b"\nLocal operator note.\n"
    modified.write_bytes(modified_bytes)
    status_cmd.run(
        SimpleNamespace(
            wiki_dir=WIKI_DIR,
            src_dir=".",
            allow_external_src=False,
            source_selection=None,
        )
    )
    broken_status = capsys.readouterr().out
    assert "Managed lifecycle: compact/broken" in broken_status
    assert "Reference state: locally_modified" in broken_status

    upgrade_cmd.run(
        SimpleNamespace(agent=None, wiki_dir=WIKI_DIR, skills=False)
    )
    capsys.readouterr()
    assert modified.read_bytes() == modified_bytes
    status_cmd.run(
        SimpleNamespace(
            wiki_dir=WIKI_DIR,
            src_dir=".",
            allow_external_src=False,
            source_selection=None,
        )
    )
    disabled_status = capsys.readouterr().out
    assert "Managed lifecycle: expanded/skills-disabled" in disabled_status
    assert "Reference state: locally_modified" in disabled_status

    monkeypatch.setattr(uninstall_cmd, "_confirm", lambda _prompt: True)
    uninstall_cmd.run(
        SimpleNamespace(wiki_dir=WIKI_DIR, remove_wiki=False, dry_run=False)
    )
    capsys.readouterr()
    assert modified.read_bytes() == modified_bytes
    assert not (generic / "AGENTS.md").exists()
    assert not (generic / ".git" / ".llm-wiki-agent").exists()

    claude = tmp_path / "claude"
    (claude / ".git" / "hooks").mkdir(parents=True)
    (claude / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.chdir(claude)
    init_cmd.run(
        SimpleNamespace(agent="claude", wiki_dir=WIKI_DIR, no_skills=False)
    )
    capsys.readouterr()
    claude_reference = claude / ".claude" / "skills" / REFERENCE_SKILL_ID
    assert verify_reference_skill(agent="claude").state is ReferenceSkillState.CURRENT
    assert claude_reference.is_dir()
    assert not (claude / ".llm-wiki" / "skills").exists()
    status_cmd.run(
        SimpleNamespace(
            wiki_dir=WIKI_DIR,
            src_dir=".",
            allow_external_src=False,
            source_selection=None,
        )
    )
    claude_status = capsys.readouterr().out
    assert "Managed lifecycle: compact/current" in claude_status
    assert "Reference path:  .claude/skills/wiki-reference" in claude_status
    uninstall_cmd.run(
        SimpleNamespace(wiki_dir=WIKI_DIR, remove_wiki=False, dry_run=False)
    )
    capsys.readouterr()
    assert not claude_reference.exists()
    assert not (claude / "CLAUDE.md").exists()
    assert not tuple(tmp_path.rglob(".gitignore"))


def test_release_dogfood_record_names_every_executable_case() -> None:
    record = json.loads(RECORD.read_text(encoding="utf-8"))

    assert record["schema_version"] == "llm-wiki-release-dogfood/v1"
    assert record["reproduce"] == (
        ".venv/bin/pytest -q tests/test_release_dogfood.py"
    )
    assert {scenario["id"] for scenario in record["scenarios"]} == {
        "artifact-members-wheel-sdist",
        "ready-no-governance",
        "legacy-surface-only",
        "degraded-mixed",
        "expanded-skills-disabled",
        "generic-current-modified",
        "claude-current",
        "installed-profile-lifecycle",
    }
    assert record["repository_policy"] == {
        "git_push": "not-invoked",
        "ignore_policy": "unchanged",
        "network": "not-used",
    }
