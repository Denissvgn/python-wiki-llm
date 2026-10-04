"""Stable IDs transfer only through real verified page plans and exact sections."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from pathlib import Path


from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.maintenance_evidence import (
    MaintenanceCapture,
    captured_observations_from_knowledge,
    maintenance_transfers_from_page_plan,
    reconcile_pending_maintenance,
)
from llm_wiki_cli.services.python_implementation import analysis_identity
from llm_wiki_cli.services.sync_transitions import plan_page_transitions
from tests.test_maintenance_reconciliation import (
    MARKDOWN,
    SOURCE,
    adopted,
    acknowledged,
    project as project,
)


def moved(project, *, markdown=MARKDOWN):
    knowledge, _ = project
    loaded = load_knowledge_state(Path("wiki"))
    assert loaded.manifest_basis is not None
    manifest = loaded.manifest_basis
    Path("wiki/entities/Batch.md").write_text(MARKDOWN)
    Path("src/policy.py").unlink()
    Path("src/moved.py").write_text(SOURCE)
    collected = get_inventory_result(
        "src", deep=True, capture_implementation_observations=True
    )
    assert collected.source_snapshot is not None
    plan = plan_page_transitions(
        Path("wiki"),
        manifest,
        collected.inventory,
        module_page_map={"moved.py": "moved"},
        entity_occurrence_page_map={("Batch", "moved.py", 1): "Moved"},
        moved_entities={"Batch": ("policy.py", "moved.py")},
    )
    entity = next(t for t in plan.transitions if t.owner.scope == "entity")
    assert entity.previous_owner is not None and entity.old_path == "entities/Batch.md"
    updated = replace(
        knowledge,
        concepts=(
            replace(
                knowledge.concepts[0],
                locator="llm-wiki://entities/Moved",
                document=replace(
                    knowledge.concepts[0].document,
                    page_id="Moved",
                    canonical_path="entities/Moved.md",
                ),
            ),
        ),
    )
    return updated, collected, plan, {"entities/Moved.md": markdown}


def current_capture(updated, collected, plan, pages, previous):
    return captured_observations_from_knowledge(
        updated,
        content_by_page=pages,
        raw_content_by_page={path: text.encode() for path, text in pages.items()},
        page_source_mappings={t.final_path: t.owner for t in plan.transitions},
        captures=collected.implementation_observations,
        source_content_hashes=collected.source_snapshot.captured_content_hashes,
        analysis_compatibility_hash=analysis_identity(collected.analysis_components),
        previous_state=previous,
        missing_source_paths={"policy.py"},
        known_absent_pages={"entities/Batch.md"},
    )


def test_verified_source_and_page_move_preserves_every_section_id_and_history(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    updated, collected, plan, pages = moved(project)
    capture = current_capture(updated, collected, plan, pages, state)
    transfers = maintenance_transfers_from_page_plan(
        state,
        capture,
        plan,
        previous_raw_content_by_page={"entities/Batch.md": MARKDOWN.encode()},
    )
    assert len(transfers.confirmed) == len(state["records"]) == 3
    assert transfers.ambiguous == ()
    result = reconcile_pending_maintenance(
        state, guard, capture, confirmed_transfers=transfers.confirmed
    )
    assert set(result["records"]) == set(state["records"])
    for record_id, row in result["records"].items():
        assert row["status"] == "pending" and row["current_acknowledgment_id"] is None
        assert (
            row["acknowledgment_history"]
            == state["records"][record_id]["acknowledgment_history"]
        )
        assert len(row["coordinate_history"]) == len(row["target_history"]) == 2
        assert (
            result["observations"][record_id]["coordinate"]["source_path"] == "moved.py"
        )
    assert reconcile_pending_maintenance(result, guard, capture) == result


def test_missing_prior_capture_never_guesses_section_transfer_from_names_or_hashes(
    project,
):
    _, state = adopted(project)
    updated, collected, plan, pages = moved(project)
    capture = current_capture(updated, collected, plan, pages, state)
    result = maintenance_transfers_from_page_plan(
        state, capture, plan, previous_raw_content_by_page=None
    )
    assert result.confirmed == () and result.ambiguous == ()
    assert result.issues


def test_changed_heading_ancestry_keeps_explicit_unresolved_candidates(project):
    guard, state = adopted(project)
    state = acknowledged(state)
    updated, collected, plan, pages = moved(
        project, markdown=MARKDOWN.replace("# Batch\n", "# Renamed title\n")
    )
    capture = current_capture(updated, collected, plan, pages, state)
    transfers = maintenance_transfers_from_page_plan(
        state,
        capture,
        plan,
        previous_raw_content_by_page={"entities/Batch.md": MARKDOWN.encode()},
    )
    assert transfers.confirmed == ()
    assert len(transfers.ambiguous) == 3
    result = reconcile_pending_maintenance(
        state, guard, capture, ambiguous_transfers=transfers.ambiguous
    )
    assert set(result["records"]) == set(state["records"])
    assert all(
        row["status"] == "pending"
        and row["mapping"]["state"] == "ambiguous"
        and row["mapping"]["candidates"]
        for row in result["records"].values()
    )
    assert all(
        o["presence"] == "ambiguous" and o["implementation"]["status"] == "unavailable"
        for o in result["observations"].values()
    )


def test_no_plan_is_no_implicit_move_proof():
    assert (
        maintenance_transfers_from_page_plan(
            None, MaintenanceCapture({}), None, previous_raw_content_by_page=None
        ).confirmed
        == ()
    )


def _real_adopted(tmp_path, monkeypatch, capsys):
    from llm_wiki_cli import api
    from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority
    from llm_wiki_cli.services.sync_manifest import SyncManifest

    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(SOURCE)
    api.bootstrap_wiki("src", "wiki")
    adopt_maintenance_authority("src", "wiki", recovery_dir="recovery")
    capsys.readouterr()
    state = SyncManifest.load(Path("wiki")).maintenance_state
    assert state is not None
    return state


def test_real_sync_verified_source_move_retains_class_record_id_and_history(
    tmp_path, monkeypatch, capsys
):
    from llm_wiki_cli import cli
    from llm_wiki_cli.services.sync_manifest import SyncManifest
    import sys

    state = _real_adopted(tmp_path, monkeypatch, capsys)
    ids = {
        record_id
        for record_id, value in state["observations"].items()
        if value["implementation"]["scope"] == "class"
    }
    assert ids
    Path("src/policy.py").rename("src/moved.py")
    monkeypatch.setattr(
        sys,
        "argv",
        ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"],
    )
    cli.main()
    after = SyncManifest.load(Path("wiki")).maintenance_state
    assert after is not None
    for record_id in ids:
        assert record_id in after["records"]
        assert (
            after["observations"][record_id]["coordinate"]["source_path"] == "moved.py"
        )
        assert len(after["records"][record_id]["coordinate_history"]) == 2
        assert "confirmed-move-basis-changed" in after["records"][record_id]["reasons"]
    before = deepcopy(after)
    cli.main()
    assert SyncManifest.load(Path("wiki")).maintenance_state == before


def test_real_ambiguous_source_move_cannot_guess_or_clear_durable_history(
    tmp_path, monkeypatch, capsys
):
    from llm_wiki_cli import cli
    from llm_wiki_cli.services.sync_manifest import SyncManifest
    import sys

    state = _real_adopted(tmp_path, monkeypatch, capsys)
    Path("src/policy.py").unlink()
    Path("src/one.py").write_text(SOURCE)
    Path("src/two.py").write_text(SOURCE)
    monkeypatch.setattr(
        sys,
        "argv",
        ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"],
    )
    cli.main()
    after = SyncManifest.load(Path("wiki")).maintenance_state
    assert after is not None
    class_ids = {
        record_id
        for record_id, value in state["observations"].items()
        if value["implementation"]["scope"] == "class"
    }
    for record_id in class_ids:
        assert after["records"][record_id]["status"] == "pending"
        assert after["records"][record_id]["mapping"]["state"] == "ambiguous"
        assert len(after["records"][record_id]["mapping"]["candidates"]) == 2
        assert (
            after["records"][record_id]["acknowledgment_history"]
            == state["records"][record_id]["acknowledgment_history"]
        )
        assert after["observations"][record_id]["presence"] == "ambiguous"

    before_repeat = deepcopy(after)
    cli.main()
    assert SyncManifest.load(Path("wiki")).maintenance_state == before_repeat
