"""Retire source members without discarding authored context or inventing evidence."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.knowledge_storage_diagnostics import storage_report
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from llm_wiki_cli.services.sync_manifest import (
    EVIDENCE_NOT_RECORDED,
    MANIFEST_STATE_UNAVAILABLE,
    TOMBSTONE_UNKNOWN_PROVENANCE,
    ManifestEvidenceBaseline,
    ManifestPageSource,
    ManifestTombstone,
    SyncManifest,
)
from tests.test_sync_page_transitions import (
    _assert_consistent,
    _assert_entity_page,
    _author_description,
    _bootstrap_project,
    _draft_source,
    _sync,
)


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


def _authored_page(wiki: Path, relative: str, generated: str, authored: str) -> str:
    page = wiki / relative
    _author_description(page, generated, authored)
    text = page.read_text(encoding="utf-8")
    if "## Notes\n" in text:
        text = text.replace(
            "## Notes\n", "## Notes\n\nHistorical operational context must remain.\n", 1
        )
    else:
        text += "\n## Notes\n\nHistorical operational context must remain.\n"
    page.write_text(text, encoding="utf-8")
    return text


def _retirement_pages(manifest: SyncManifest) -> dict:
    state = manifest.generation_inputs.get("entity_retirement")
    if state is None:
        return {}
    assert isinstance(state, dict)
    pages = state.get("pages")
    assert isinstance(pages, dict)
    return pages


def _assert_retired(
    wiki: Path, relative: str, owner: ManifestPageSource
) -> SyncManifest:
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER

    manifest = SyncManifest.load(wiki)
    assert manifest.page_source_mappings[relative] == owner
    assert relative in manifest.tombstones
    assert relative not in manifest.evidence_baselines
    state = manifest.generation_inputs["entity_retirement"]
    assert isinstance(state, dict)
    assert state["schema_version"] == "llm-wiki-entity-retirement/v1"
    assert _retirement_pages(manifest)[relative] == owner.to_payload()
    assert (
        (wiki / relative)
        .read_text(encoding="utf-8")
        .startswith(SOURCE_MEMBER_REMOVED_HEADER)
    )
    assert relative in (wiki / "index.md").read_text(encoding="utf-8")
    return manifest


def _assert_converged(wiki: Path, **options) -> None:
    _assert_consistent(wiki)
    state = load_knowledge_state(wiki)
    assert state.status is KnowledgeLoadState.VALID, state.issues
    report = storage_report(wiki, full=True)
    assert report["ok"], report
    stable = _snapshot(wiki)
    _sync(wiki, **options)
    assert _snapshot(wiki) == stable


@pytest.mark.parametrize("authored", [False, True])
def test_removed_member_in_surviving_file_retains_page_and_historical_basis(
    tmp_path,
    monkeypatch,
    authored,
):
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER

    project, wiki = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "model.py": _draft_source("Retired draft.")
            + "\n"
            + _draft_source("Live keeper.", name="Keeper"),
        },
    )
    relative = "entities/Draft.md"
    if authored:
        _authored_page(wiki, relative, "Retired draft.", "AUTHORED retired draft.")
    _sync(wiki)
    before = SyncManifest.load(wiki)
    preimage = (wiki / relative).read_text(encoding="utf-8")
    owner = before.page_source_mappings[relative]
    basis = before.evidence_baselines[relative].basis
    assert basis is not None and basis.is_known
    (project / "pkg/model.py").write_text(
        _draft_source("Live keeper.", name="Keeper"), encoding="utf-8"
    )

    _sync(wiki)

    manifest = _assert_retired(wiki, relative, owner)
    assert manifest.sources["pkg/model.py"]["entities"] == ["Keeper"]
    assert manifest.tombstones[relative].last_valid_basis == basis
    assert (wiki / relative).read_text(
        encoding="utf-8"
    ) == SOURCE_MEMBER_REMOVED_HEADER + preimage
    _assert_entity_page(
        wiki, "Keeper", "pkg/model.py", "Live keeper.", entity_name="Keeper"
    )
    _assert_converged(wiki)


@pytest.mark.parametrize("unknown", [False, True])
def test_unchanged_sync_recovers_prior_unqualified_member_removal(
    tmp_path, monkeypatch, unknown
):
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER

    project, wiki = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "model.py": _draft_source("Original draft."),
        },
    )
    relative = "entities/Draft.md"
    _authored_page(wiki, relative, "Original draft.", "AUTHORED recovery context.")
    _sync(wiki)
    before = SyncManifest.load(wiki)
    owner = before.page_source_mappings[relative]
    preimage = (wiki / relative).read_text(encoding="utf-8")
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    # Replay the former missing retirement operation through the owning sync.
    # The fixture constructs any unknown historical provenance in typed state;
    # native projections are still written and committed by ordinary finalization.
    with monkeypatch.context() as old_provider:
        old_provider.setattr(
            sync_cmd, "discover_retired_entities", lambda *_args, **_kwargs: {}
        )
        if unknown:
            real_from_inventory = SyncManifest.build_from_inventory.__func__

            def unknown_previous(cls, *args, **kwargs):
                previous = kwargs.get("previous_manifest")
                if previous is not None and relative in previous.evidence_baselines:
                    kwargs["previous_manifest"] = replace(
                        previous,
                        evidence_baselines={
                            **previous.evidence_baselines,
                            relative: ManifestEvidenceBaseline.unknown(
                                EVIDENCE_NOT_RECORDED
                            ),
                        },
                    )
                return real_from_inventory(cls, *args, **kwargs)

            old_provider.setattr(
                SyncManifest, "build_from_inventory", classmethod(unknown_previous)
            )
        _sync(wiki)
    incomplete = SyncManifest.load(wiki)
    assert incomplete.sources["pkg/model.py"]["entities"] == []
    assert incomplete.page_source_mappings[relative] == owner
    assert (
        not (wiki / relative)
        .read_text(encoding="utf-8")
        .startswith(SOURCE_MEMBER_REMOVED_HEADER)
    )
    assert (wiki / relative).read_text(encoding="utf-8") == preimage
    if unknown:
        assert incomplete.tombstones[relative].last_valid_basis is None
        assert incomplete.tombstones[relative].unknown_reason == EVIDENCE_NOT_RECORDED
    else:
        assert incomplete.tombstones[relative].last_valid_basis is not None
    sources = {path: path.read_bytes() for path in (project / "pkg").glob("*.py")}

    _sync(wiki)

    recovered = _assert_retired(wiki, relative, owner)
    assert recovered.tombstones[relative] == incomplete.tombstones[relative]
    assert {path: path.read_bytes() for path in sources} == sources
    assert (wiki / relative).read_text(
        encoding="utf-8"
    ) == SOURCE_MEMBER_REMOVED_HEADER + preimage
    _assert_converged(wiki)


def test_second_duplicate_occurrence_retires_without_touching_first(
    tmp_path, monkeypatch
):
    project, wiki = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "model.py": _draft_source("First occurrence.")
            + "\n"
            + _draft_source("Second occurrence."),
        },
    )
    manifest = SyncManifest.load(wiki)
    owners = {
        owner.occurrence: (relative, owner)
        for relative, owner in manifest.page_source_mappings.items()
        if owner.scope == "entity"
    }
    first, _first_owner = owners[1]
    second, second_owner = owners[2]
    _authored_page(wiki, first, "First occurrence.", "AUTHORED first occurrence.")
    _authored_page(wiki, second, "Second occurrence.", "AUTHORED second occurrence.")
    _sync(wiki)
    first_preimage = (wiki / first).read_bytes()
    (project / "pkg/model.py").write_text(
        _draft_source("First occurrence."), encoding="utf-8"
    )

    _sync(wiki)

    _assert_retired(wiki, second, second_owner)
    after = SyncManifest.load(wiki)
    first_live = next(
        relative
        for relative, owner in after.page_source_mappings.items()
        if owner == ManifestPageSource("entity", "pkg/model.py", "Draft", 1)
        and relative in after.evidence_baselines
    )
    assert b"AUTHORED first occurrence." in (wiki / first_live).read_bytes()
    assert b"AUTHORED second occurrence." not in (wiki / first_live).read_bytes()
    assert b"AUTHORED second occurrence." in (wiki / second).read_bytes()
    assert b"AUTHORED first occurrence." in first_preimage
    _assert_converged(wiki)


def test_collision_rename_keeps_surviving_owner_separate_from_retired_page(
    tmp_path, monkeypatch
):
    project, wiki = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "alpha.py": _draft_source("Alpha draft."),
            "beta.py": _draft_source("Beta draft."),
        },
    )
    before = SyncManifest.load(wiki)
    alpha = next(
        relative
        for relative, owner in before.page_source_mappings.items()
        if owner == ManifestPageSource("entity", "pkg/alpha.py", "Draft", 1)
    )
    beta = next(
        relative
        for relative, owner in before.page_source_mappings.items()
        if owner == ManifestPageSource("entity", "pkg/beta.py", "Draft", 1)
    )
    _authored_page(wiki, alpha, "Alpha draft.", "AUTHORED alpha remains historical.")
    _authored_page(wiki, beta, "Beta draft.", "AUTHORED beta stays live.")
    _sync(wiki)
    (project / "pkg/alpha.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )

    _sync(wiki)

    _assert_retired(wiki, alpha, before.page_source_mappings[alpha])
    _assert_entity_page(wiki, "Draft", "pkg/beta.py", "AUTHORED beta stays live.")
    assert "AUTHORED alpha remains historical." in (wiki / alpha).read_text(
        encoding="utf-8"
    )
    assert "AUTHORED alpha remains historical." not in (
        wiki / "entities/Draft.md"
    ).read_text(encoding="utf-8")
    _assert_converged(wiki)


def test_move_between_surviving_sources_is_not_retirement(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "alpha.py": _draft_source("Original draft."),
            "beta.py": "def surviving_function():\n    return None\n",
        },
    )
    _authored_page(
        wiki, "entities/Draft.md", "Original draft.", "AUTHORED moved draft."
    )
    _sync(wiki)
    (project / "pkg/alpha.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    (project / "pkg/beta.py").write_text(
        _draft_source("Destination draft."), encoding="utf-8"
    )

    _sync(wiki)

    _assert_entity_page(wiki, "Draft", "pkg/beta.py", "AUTHORED moved draft.")
    manifest = SyncManifest.load(wiki)
    assert "entities/Draft.md" not in manifest.tombstones
    assert "entities/Draft.md" not in _retirement_pages(manifest)
    _assert_converged(wiki)


def test_exact_member_reappearance_revives_authored_page_and_current_evidence(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER

    source = _draft_source("Original draft.")
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": source})
    _authored_page(
        wiki, "entities/Draft.md", "Original draft.", "AUTHORED revived draft."
    )
    _sync(wiki)
    owner = SyncManifest.load(wiki).page_source_mappings["entities/Draft.md"]
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    _sync(wiki)
    _assert_retired(wiki, "entities/Draft.md", owner)
    (project / "pkg/model.py").write_text(source, encoding="utf-8")

    _sync(wiki)

    _assert_entity_page(wiki, "Draft", "pkg/model.py", "AUTHORED revived draft.")
    text = (wiki / "entities/Draft.md").read_text(encoding="utf-8")
    assert "Historical operational context must remain." in text
    assert SOURCE_MEMBER_REMOVED_HEADER not in text
    manifest = SyncManifest.load(wiki)
    assert "entities/Draft.md" not in manifest.tombstones
    assert "entities/Draft.md" not in _retirement_pages(manifest)
    _assert_converged(wiki)


@pytest.mark.parametrize("authored", [False, True])
def test_revival_updates_generated_defaults_and_preserves_authored_fields(
    tmp_path,
    monkeypatch,
    authored,
):
    from llm_wiki_cli.services.markdown_sections import table_description_cells

    source = (
        'class Draft:\n    """Old generated description."""\n'
        '    subject: str = "old"\n\n'
        "    def deliver(self, target: str) -> None:\n"
        '        """Old generated delivery."""\n        pass\n'
    )
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": source})
    page = wiki / "entities/Draft.md"
    if authored:
        _authored_page(
            wiki,
            "entities/Draft.md",
            "Old generated description.",
            "AUTHORED permanent description.",
        )
        text = page.read_text(encoding="utf-8")
        edited = []
        for line in text.splitlines():
            if line.startswith("| `subject` |"):
                cells = sync_cmd._split_table_row(line)
                cells[-1] = "AUTHORED attribute explanation."
                line = "| " + " | ".join(cells) + " |"
            edited.append(line)
        text = "\n".join(edited) + "\n"
        assert "Old generated delivery." in text
        text = text.replace("Old generated delivery.", "AUTHORED delivery explanation.")
        text += "\n### Nested reminder\n\nKeep the nested reminder.\n\n```markdown\n## Description\nA literal heading inside authored notes.\n```\n"
        page.write_text(text, encoding="utf-8")
    _sync(wiki)
    owner = SyncManifest.load(wiki).page_source_mappings["entities/Draft.md"]
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    _sync(wiki)
    _assert_retired(wiki, "entities/Draft.md", owner)
    changed = (
        source.replace("Old generated", "New generated")
        .replace('subject: str = "old"', "subject: int = 0")
        .replace("target: str", "target: int")
    )
    (project / "pkg/model.py").write_text(changed, encoding="utf-8")

    _sync(wiki)

    expected = (
        "AUTHORED permanent description." if authored else "New generated description."
    )
    _assert_entity_page(wiki, "Draft", "pkg/model.py", expected)
    revived = page.read_text(encoding="utf-8")
    assert "Old generated description." not in revived
    assert "Old generated delivery." not in revived
    if authored:
        assert (
            table_description_cells(revived, "Attributes")["subject"]
            == "AUTHORED attribute explanation."
        )
        assert (
            table_description_cells(revived, "Methods")["deliver"]
            == "AUTHORED delivery explanation."
        )
        assert "Historical operational context must remain." in revived
        assert "Keep the nested reminder." in revived
        assert (
            "```markdown\n## Description\nA literal heading inside authored notes.\n```"
            in revived
        )
    else:
        assert (
            table_description_cells(revived, "Methods")["deliver"]
            == "New generated delivery."
        )
    assert "| `subject` | `int` |" in revived
    assert "target: int" in revived
    _assert_converged(wiki)


def test_failed_source_parse_cannot_authorize_member_retirement(tmp_path, monkeypatch):
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER

    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    before = _snapshot(wiki)
    (project / "pkg/model.py").write_text("class Draft(:\n    pass\n", encoding="utf-8")

    with pytest.raises(SystemExit) as caught:
        _sync(wiki)

    assert caught.value.code != 0
    assert _snapshot(wiki) == before
    assert SOURCE_MEMBER_REMOVED_HEADER not in (wiki / "entities/Draft.md").read_text(
        encoding="utf-8"
    )
    assert not _retirement_pages(SyncManifest.load(wiki))


def test_unmapped_historical_page_is_not_given_guessed_source_identity(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.commands import lint_cmd
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER

    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    _authored_page(
        wiki, "entities/Draft.md", "Original draft.", "AUTHORED unbound history."
    )
    _sync(wiki)
    preimage = (wiki / "entities/Draft.md").read_bytes()
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    real_build = SyncManifest.build_from_inventory.__func__

    def lost_binding(cls, *args, **kwargs):
        built = real_build(cls, *args, **kwargs)
        if "entities/Draft.md" not in built.tombstones:
            return built
        return replace(
            built,
            page_source_mappings={
                path: owner
                for path, owner in built.page_source_mappings.items()
                if path != "entities/Draft.md"
            },
            tombstones={
                **built.tombstones,
                "entities/Draft.md": ManifestTombstone(
                    reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                    unknown_reason=MANIFEST_STATE_UNAVAILABLE,
                ),
            },
        )

    with monkeypatch.context() as old_provider:
        old_provider.setattr(
            sync_cmd, "discover_retired_entities", lambda *_args, **_kwargs: {}
        )
        old_provider.setattr(
            SyncManifest, "build_from_inventory", classmethod(lost_binding)
        )
        _sync(wiki)
    assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID

    _sync(wiki)

    after = SyncManifest.load(wiki)
    assert "entities/Draft.md" not in after.page_source_mappings
    assert not _retirement_pages(after)
    assert after.tombstones["entities/Draft.md"].last_valid_basis is None
    assert (
        after.tombstones["entities/Draft.md"].unknown_reason
        == MANIFEST_STATE_UNAVAILABLE
    )
    assert (wiki / "entities/Draft.md").read_bytes() == preimage
    assert SOURCE_MEMBER_REMOVED_HEADER.encode() not in preimage
    report = lint_cmd.build_report(
        wiki, ".", strict=True, parallel_jobs=1, include_plugins=False
    )
    assert not report.passed
    assert "knowledge_evidence" in report.by_category()


def test_first_duplicate_removal_cannot_transfer_authored_identity_to_second(
    tmp_path, monkeypatch
):
    first = _draft_source("First declaration.")
    second = _draft_source("Second declaration.")
    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": first + "\n" + second}
    )
    _authored_page(
        wiki, "entities/Draft.md", "First declaration.", "AUTHORED first declaration."
    )
    _authored_page(
        wiki,
        "entities/Draft_2.md",
        "Second declaration.",
        "AUTHORED second declaration.",
    )
    _sync(wiki)
    before = _snapshot(wiki)
    (project / "pkg/model.py").write_text(second, encoding="utf-8")

    with pytest.raises(SystemExit) as caught:
        _sync(wiki)

    assert caught.value.code != 0
    assert _snapshot(wiki) == before


def test_foreign_source_cannot_claim_retired_same_named_page(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"alpha.py": _draft_source("Original draft.")}
    )
    (project / "pkg/alpha.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    _sync(wiki)
    before = _snapshot(wiki)
    (project / "pkg/beta.py").write_text(
        _draft_source("Foreign draft."), encoding="utf-8"
    )

    with pytest.raises(SystemExit) as caught:
        _sync(wiki)

    assert caught.value.code != 0
    assert _snapshot(wiki) == before


def test_deselection_prunes_retired_members_without_reclassifying_them_live(
    tmp_path, monkeypatch
):
    project, wiki = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "alpha.py": _draft_source("Historical draft."),
            "keeper.py": _draft_source("Live keeper.", name="Keeper"),
        },
    )
    (project / "pkg/alpha.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    _sync(wiki)
    profile = project / ".llm-wiki/source-selection.json"
    profile.parent.mkdir(exist_ok=True)
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["pkg/keeper.py"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )

    _sync(wiki, source_selection=profile.relative_to(project))

    assert not (wiki / "entities/Draft.md").exists()
    assert not (wiki / "modules/alpha.md").exists()
    manifest = SyncManifest.load(wiki)
    assert set(manifest.sources) == {"pkg/keeper.py"}
    assert "entities/Draft.md" not in manifest.page_source_mappings
    assert "entities/Draft.md" not in _retirement_pages(manifest)
    _assert_converged(wiki, source_selection=profile.relative_to(project))


def test_retirement_dry_run_leaves_all_wiki_bytes_and_mtimes_unchanged(
    tmp_path, monkeypatch
):
    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    before = _snapshot(wiki)

    _sync(wiki, dry_run=True)

    assert _snapshot(wiki) == before
    assert "entities/Draft.md" in SyncManifest.load(wiki).evidence_baselines
    _sync(wiki)
    _assert_converged(wiki)


def test_retirement_preserves_durable_governance_identity_without_lifecycle_event(
    tmp_path, monkeypatch
):
    from llm_wiki_cli import cli
    from llm_wiki_cli.commands import knowledge_cmd
    from llm_wiki_cli.services.knowledge_governance import load_governance

    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    knowledge_cmd.run(
        cli._build_parser().parse_args(
            [
                "knowledge",
                "init",
                "--wiki-dir",
                str(wiki),
                "--bundle-id",
                "kb_retired_members",
            ]
        )
    )
    before = load_governance(wiki).ledger
    uid, allocation = next(
        (uid, allocation)
        for uid, allocation in before.concepts.items()
        if allocation.locator.endswith("/Draft")
    )
    owner = SyncManifest.load(wiki).page_source_mappings["entities/Draft.md"]
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )

    _sync(wiki)

    _assert_retired(wiki, "entities/Draft.md", owner)
    after = load_governance(wiki).ledger
    assert after.concepts[uid] == allocation
    assert after.lifecycle_events == before.lifecycle_events
    _assert_converged(wiki)


def test_symlinked_retirement_candidate_blocks_before_any_owned_page_write(
    tmp_path, monkeypatch
):
    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    page = wiki / "entities/Draft.md"
    external = project / "external-notes.md"
    external.write_bytes(page.read_bytes())
    page.unlink()
    page.symlink_to(external)
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    before = _snapshot(wiki)
    outside = external.read_bytes()

    with pytest.raises(SystemExit) as caught:
        _sync(wiki)

    assert caught.value.code != 0
    assert page.is_symlink()
    assert external.read_bytes() == outside
    assert _snapshot(wiki) == before


def test_concurrent_authored_edit_during_retirement_is_preserved(tmp_path, monkeypatch):
    from llm_wiki_cli.services import sync_transition_execution
    from llm_wiki_cli.services.maintenance_protocol import MaintenanceProtocolError
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER
    from llm_wiki_cli.services.sync_transitions import PageTransitionError

    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )
    before = _snapshot(wiki)
    original_write = sync_transition_execution.PageTransitionExecution.write
    concurrent = "# Concurrent authored replacement\n\nDo not overwrite this edit.\n"
    injected = []

    def edit_before_write(self, relative, text):
        if relative == "entities/Draft.md" and text.startswith(
            SOURCE_MEMBER_REMOVED_HEADER
        ):
            (wiki / relative).write_text(concurrent, encoding="utf-8")
            injected.append(relative)
        return original_write(self, relative, text)

    monkeypatch.setattr(
        sync_transition_execution.PageTransitionExecution, "write", edit_before_write
    )

    with pytest.raises((SystemExit, PageTransitionError, MaintenanceProtocolError)):
        _sync(wiki)

    assert injected == ["entities/Draft.md"]
    assert (wiki / "entities/Draft.md").read_text(encoding="utf-8") == concurrent
    for relative in (
        ".llm-wiki-manifest.json",
        ".llm-wiki-knowledge.json",
        ".llm-wiki-surface.json",
    ):
        assert (wiki / relative).read_bytes() == before[relative][0]


def test_interrupted_retirement_retains_durable_preimage_and_blocks_blind_retry(
    tmp_path, monkeypatch
):
    from llm_wiki_cli.services import sync_transition_execution

    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    _authored_page(
        wiki, "entities/Draft.md", "Original draft.", "AUTHORED interruption context."
    )
    _sync(wiki)
    before = _snapshot(wiki)
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )

    def interrupted(*_args, **_kwargs):
        raise OSError("Injected interruption after retired page staging")

    with monkeypatch.context() as interruption:
        interruption.setattr(sync_cmd, "_apply_refreshed_file_pages", interrupted)
        with pytest.raises(OSError, match="Injected interruption"):
            _sync(wiki)

    directories = list(wiki.glob(f"{sync_transition_execution.RECOVERY_PREFIX}*"))
    assert len(directories) == 1
    recovery = json.loads(
        (directories[0] / "recovery.json").read_text(encoding="utf-8")
    )
    retained = next(
        record
        for record in recovery["retained_pages"]
        if record["source"] == "entities/Draft.md"
    )
    assert (directories[0] / retained["backup"]).read_bytes() == before[
        "entities/Draft.md"
    ][0]
    for relative in (
        ".llm-wiki-manifest.json",
        ".llm-wiki-knowledge.json",
        ".llm-wiki-surface.json",
    ):
        assert (wiki / relative).read_bytes() == before[relative][0]
    partial = _snapshot(wiki)

    with pytest.raises(SystemExit) as caught:
        _sync(wiki)

    assert caught.value.code != 0
    assert _snapshot(wiki) == partial


def test_valid_comment_only_source_requires_explicit_empty_module_classification(
    tmp_path,
    monkeypatch,
    capsys,
):
    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    before = _snapshot(wiki)
    (project / "pkg/model.py").write_text(
        "# The selected file is valid Python and still exists.\n", encoding="utf-8"
    )
    capsys.readouterr()

    with pytest.raises(SystemExit) as caught:
        _sync(wiki)

    assert caught.value.code != 0
    captured = capsys.readouterr()
    assert "Selected source is still captured" in captured.err
    assert "pkg/model.py" in captured.err
    assert "parser/coverage or empty-module classification" in captured.err
    assert "Sync complete:" not in captured.out
    assert "Wiki is up to date." not in captured.out
    assert _snapshot(wiki) == before
    assert not _retirement_pages(SyncManifest.load(wiki))


def test_cp1252_authored_markdown_survives_retirement_as_text(tmp_path, monkeypatch):
    from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER

    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original draft.")}
    )
    page = wiki / "entities/Draft.md"
    _authored_page(
        wiki, "entities/Draft.md", "Original draft.", "AUTHORED café, déjà vu."
    )
    _sync(wiki)
    owner = SyncManifest.load(wiki).page_source_mappings["entities/Draft.md"]
    preimage = page.read_text(encoding="utf-8")
    encoded = preimage.encode("cp1252")
    assert encoded != preimage.encode("utf-8")
    page.write_bytes(encoded)
    (project / "pkg/model.py").write_text(
        "def surviving_function():\n    return None\n", encoding="utf-8"
    )

    _sync(wiki)

    _assert_retired(wiki, "entities/Draft.md", owner)
    assert page.read_text(encoding="utf-8") == SOURCE_MEMBER_REMOVED_HEADER + preimage
    assert "AUTHORED café, déjà vu." in page.read_text(encoding="utf-8")
    _assert_converged(wiki)
