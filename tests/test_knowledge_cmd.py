from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import knowledge_cmd
from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_generation import (
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.knowledge_governance import (
    GOVERNANCE_FILENAME,
    GovernanceError,
    current_lifecycle,
    load_governance,
)
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import Lifecycle
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.verification_contracts import (
    VERIFICATION_RECEIPT_FILENAME,
    load_verification_receipt,
)
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_generation import _planner_inputs


def _write_pages(root: Path, content_by_page) -> None:
    for relative_path, content in content_by_page.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _committed_wiki(root: Path, *, reviewable: bool = False):
    inputs = _planner_inputs(root)
    content = dict(inputs.content_by_page)
    if reviewable:
        module_path = "modules/accounts.md"
        content[module_path] = (
            "# accounts Module\n\n"
            "## Description\n\n"
            "Human-maintained account-domain semantics.\n"
        )
        content["entities/User.md"] = (
            "# User\n\n"
            "## Description\n\n"
            "Human-maintained user semantics.\n"
        )
        inputs = replace(inputs, content_by_page=content)
    _write_pages(root, content)
    plan = build_knowledge_generation_plan(inputs)
    commit_knowledge_artifacts(plan)
    return plan


def _run(argv: list[str]) -> None:
    args = cli._build_parser().parse_args(["knowledge", *argv])
    knowledge_cmd.run(args)


def _artifact_bytes(root: Path) -> dict[str, bytes]:
    names = (
        GOVERNANCE_FILENAME,
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        MANIFEST_FILENAME,
    )
    return {
        name: (root / name).read_bytes()
        for name in names
        if (root / name).is_file()
    }


def test_parser_exposes_nested_and_shortcut_lifecycle_commands():
    parser = cli._build_parser()
    common = [
        "--uid",
        "lw:module:0123456789abcdef0123456789abcdef",
        "--actor-kind",
        "human",
        "--actor-id",
        "alice",
        "--authored-at",
        "2026-07-27T12:00:00Z",
    ]

    nested = parser.parse_args(
        ["knowledge", "lifecycle", "set", *common, "--state", "active"]
    )
    shortcut = parser.parse_args(["knowledge", "deprecate", *common])

    assert nested.knowledge_action == "lifecycle"
    assert nested.lifecycle_action == "set"
    assert nested.state == "active"
    assert shortcut.knowledge_action == "deprecate"


def test_init_dry_run_writes_nothing_and_real_init_is_idempotent(
    tmp_path,
    capsys,
):
    _committed_wiki(tmp_path)
    before = _artifact_bytes(tmp_path)

    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_command_fixture",
            "--dry-run",
        ]
    )

    preview = json.loads(capsys.readouterr().out)
    assert preview["dry_run"] is True
    assert preview["changed"] is True
    assert not (tmp_path / GOVERNANCE_FILENAME).exists()
    assert _artifact_bytes(tmp_path) == before

    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_command_fixture",
        ]
    )
    first_output = json.loads(capsys.readouterr().out)
    first = _artifact_bytes(tmp_path)
    loaded = load_governance(tmp_path)
    assert first_output["changed"] is True
    assert loaded.ledger.bundle_id == "kb_command_fixture"
    assert len(loaded.ledger.concepts) == len(
        load_knowledge_state(tmp_path).knowledge.concepts
    )

    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_command_fixture",
        ]
    )
    second_output = json.loads(capsys.readouterr().out)
    assert second_output["changed"] is False
    assert _artifact_bytes(tmp_path) == first


def test_lifecycle_mutation_refreshes_projection_and_dry_run_is_read_only(
    tmp_path,
    capsys,
):
    _committed_wiki(tmp_path)
    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_lifecycle_fixture",
        ]
    )
    capsys.readouterr()
    initial_ledger = load_governance(tmp_path).ledger
    uid = next(iter(initial_ledger.concepts))
    successor_uid = next(
        candidate for candidate in initial_ledger.concepts if candidate != uid
    )

    _run(
        [
            "lifecycle",
            "set",
            "--wiki-dir",
            str(tmp_path),
            "--uid",
            uid,
            "--state",
            "active",
            "--actor-kind",
            "human",
            "--actor-id",
            "alice",
            "--authored-at",
            "2026-07-27T12:00:00Z",
        ]
    )
    capsys.readouterr()
    ledger = load_governance(tmp_path).ledger
    assert current_lifecycle(ledger, uid)[0] is Lifecycle.ACTIVE
    knowledge = load_knowledge_state(tmp_path).knowledge
    projected = next(
        concept
        for concept in knowledge.concepts
        if concept.extensions["llm-wiki/governance-v1"]["uid"] == uid
    )
    assert projected.lifecycle is Lifecycle.ACTIVE

    before = _artifact_bytes(tmp_path)
    _run(
        [
            "deprecate",
            "--wiki-dir",
            str(tmp_path),
            "--uid",
            uid,
            "--actor-kind",
            "human",
            "--actor-id",
            "alice",
            "--authored-at",
            "2026-07-28T12:00:00Z",
            "--dry-run",
        ]
    )
    preview = json.loads(capsys.readouterr().out)
    assert preview["changed"] is True
    assert _artifact_bytes(tmp_path) == before
    assert current_lifecycle(load_governance(tmp_path).ledger, uid)[0] is (
        Lifecycle.ACTIVE
    )

    _run(
        [
            "supersede",
            "--wiki-dir",
            str(tmp_path),
            "--uid",
            uid,
            "--successor-uid",
            successor_uid,
            "--actor-kind",
            "human",
            "--actor-id",
            "alice",
            "--authored-at",
            "2026-07-29T12:00:00Z",
        ]
    )
    capsys.readouterr()
    assert current_lifecycle(load_governance(tmp_path).ledger, uid)[0] is (
        Lifecycle.SUPERSEDED
    )
    superseded = load_knowledge_state(tmp_path).knowledge
    graph = superseded.extensions["llm-wiki/typed-graph-v1"]
    assert any(
        edge["kind"] == "supersedes"
        and edge["from"]["uid"] == uid
        and edge["target"]["uid"] == successor_uid
        for edge in graph["edges"]
    )
    _run(
        [
            "status",
            "--wiki-dir",
            str(tmp_path),
            "--format",
            "json",
            "--event-limit",
            "1",
        ]
    )
    status = json.loads(capsys.readouterr().out)
    assert status["freshness"] == "unevaluated (snapshot-only read)"
    assert status["freshness_evaluated"] is False
    concept_status = next(
        item for item in status["concepts"] if item["uid"] == uid
    )
    assert concept_status["lifecycle_event_coverage"] == {
        "total": 2,
        "returned": 1,
        "limit": 1,
        "truncated": True,
    }
    assert concept_status["review_event_coverage"] == {
        "total": 0,
        "returned": 0,
        "limit": 1,
        "truncated": False,
    }
    _run(
        [
            "status",
            "--wiki-dir",
            str(tmp_path),
            "--event-limit",
            "1",
        ]
    )
    assert (
        "Freshness: unevaluated (snapshot-only read)"
        in capsys.readouterr().out
    )


def test_alias_refreshes_projection_and_move_can_stage_until_sync(
    tmp_path,
    capsys,
):
    _committed_wiki(tmp_path)
    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_move_fixture",
        ]
    )
    capsys.readouterr()
    ledger = load_governance(tmp_path).ledger
    uid, allocation = next(
        (uid, allocation)
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://modules/accounts"
    )
    _run(
        [
            "alias",
            "--wiki-dir",
            str(tmp_path),
            "--uid",
            uid,
            "--type",
            "locator",
            "--value",
            "llm-wiki://modules/account-domain",
        ]
    )
    capsys.readouterr()
    projected = load_knowledge_state(tmp_path).knowledge
    concept = next(item for item in projected.concepts if item.locator == allocation.locator)
    assert {
        (alias["type"], alias["value"])
        for alias in concept.extensions["llm-wiki/governance-v1"]["aliases"]
    } == {("locator", "llm-wiki://modules/account-domain")}

    projection_before_move = (tmp_path / KNOWLEDGE_INDEX_FILENAME).read_bytes()
    _run(
        [
            "move",
            "--wiki-dir",
            str(tmp_path),
            "--uid",
            uid,
            "--to-locator",
            "llm-wiki://modules/accounts-renamed",
            "--to-natural-key",
            "source-module:modules/accounts-renamed.md",
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert result["projection"] == "pending-sync"
    moved = load_governance(tmp_path).ledger
    assert moved.concepts[uid].locator == "llm-wiki://modules/accounts-renamed"
    assert any(
        alias.uid == uid
        and alias.alias_type == "locator"
        and alias.value == "llm-wiki://modules/accounts"
        for alias in moved.aliases.values()
    )
    assert (tmp_path / KNOWLEDGE_INDEX_FILENAME).read_bytes() == (
        projection_before_move
    )
    with pytest.raises(KnowledgeStateLoadError):
        load_knowledge_state(tmp_path)


def test_review_and_explicit_verification_write_separate_artifacts(
    tmp_path,
    capsys,
):
    _committed_wiki(tmp_path, reviewable=True)
    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_review_fixture",
        ]
    )
    capsys.readouterr()
    state = load_knowledge_state(tmp_path)
    knowledge = state.knowledge
    sections = knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
    page = next(
        page
        for page in sections
        if page["page_locator"] == "llm-wiki://modules/accounts"
    )
    section = next(
        section
        for section in page["sections"]
        if section.get("semantic_hash") is not None
    )
    ledger = load_governance(tmp_path).ledger
    uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == page["page_locator"]
    )

    _run(
        [
            "review",
            "--wiki-dir",
            str(tmp_path),
            "--uid",
            uid,
            "--section",
            section["locator"],
            "--reviewer-kind",
            "human",
            "--reviewer-id",
            "alice",
            "--method",
            "manual-review",
            "--method-version",
            "1",
            "--authored-at",
            "2026-07-27T12:00:00Z",
        ]
    )
    capsys.readouterr()
    governed = load_governance(tmp_path).ledger
    assert len(governed.review_events) == 1
    assert not (tmp_path / VERIFICATION_RECEIPT_FILENAME).exists()

    governance_before_verify = (tmp_path / GOVERNANCE_FILENAME).read_bytes()
    _run(
        [
            "verify",
            "--wiki-dir",
            str(tmp_path),
            "--uid",
            uid,
            "--checker",
            "artifact-integrity",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert output["result"] == "passed"
    receipt = load_verification_receipt(tmp_path, missing_ok=False)
    assert receipt is not None
    assert receipt.result.value == "passed"
    assert (tmp_path / GOVERNANCE_FILENAME).read_bytes() == governance_before_verify


def test_review_rejects_another_concepts_section_without_writing(
    tmp_path,
    capsys,
):
    _committed_wiki(tmp_path, reviewable=True)
    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_review_scope_fixture",
        ]
    )
    capsys.readouterr()
    state = load_knowledge_state(tmp_path)
    knowledge = state.knowledge
    sections = knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
    user_page = next(
        page
        for page in sections
        if page["page_locator"] == "llm-wiki://entities/User"
    )
    user_section = next(
        section
        for section in user_page["sections"]
        if section.get("semantic_hash") is not None
    )
    ledger = load_governance(tmp_path).ledger
    module_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://modules/accounts"
    )
    before = _artifact_bytes(tmp_path)

    with pytest.raises(
        GovernanceError,
        match="must belong to the reviewed concept",
    ):
        _run(
            [
                "review",
                "--wiki-dir",
                str(tmp_path),
                "--uid",
                module_uid,
                "--section",
                user_section["locator"],
                "--reviewer-kind",
                "human",
                "--reviewer-id",
                "alice",
                "--method",
                "manual-review",
                "--method-version",
                "1",
                "--authored-at",
                "2026-07-27T12:00:00Z",
            ]
        )

    assert _artifact_bytes(tmp_path) == before


def test_missing_previously_governed_ledger_fails_closed_without_reallocation(
    tmp_path,
    capsys,
):
    _committed_wiki(tmp_path)
    _run(
        [
            "init",
            "--wiki-dir",
            str(tmp_path),
            "--bundle-id",
            "kb_missing_fixture",
        ]
    )
    capsys.readouterr()
    prior_knowledge = (tmp_path / KNOWLEDGE_INDEX_FILENAME).read_bytes()
    (tmp_path / GOVERNANCE_FILENAME).unlink()

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        _run(["status", "--wiki-dir", str(tmp_path), "--format", "json"])
    assert {issue.code for issue in exc_info.value.issues} == {
        "governance-missing"
    }

    with pytest.raises(KnowledgeStateLoadError):
        _run(
            [
                "init",
                "--wiki-dir",
                str(tmp_path),
                "--bundle-id",
                "kb_reallocated",
            ]
        )
    assert not (tmp_path / GOVERNANCE_FILENAME).exists()
    assert (tmp_path / KNOWLEDGE_INDEX_FILENAME).read_bytes() == prior_knowledge
