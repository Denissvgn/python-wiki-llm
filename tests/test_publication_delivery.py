"""Reviewed delivery, durable ownership and rollback contracts independent of Git transport."""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli.services import publication_candidate as candidate
from llm_wiki_cli.services import publication_delivery as delivery
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.publication_config import (
    DELIVERY_CONFIG_SCHEMA_VERSION,
    validate_publication_config,
)
from tests.test_publication_candidate import accept_topics, configure
from tests.test_publication_impact import consumer as consumer

SOURCE = "1" * 40
BASE = "2" * 40
ADVANCED = "3" * 40
LATER_SOURCE = "4" * 40
SCOPE = {
    "source_repository": "example/source",
    "target_repository": "example/source",
    "target_branch": "wiki/main",
}


def opt_in(root: Path):
    policy = configure(root, manual=True)
    original_home = b"# Home\n\n[Accounts](Accounts)\n"
    (root / "public/Home.md").write_bytes(original_home)
    policy["content"]["adoptions"].append(
        {
            "path": "Home.md",
            "expected_hash": sha256_bytes(original_home),
            "reason": "Adopt the original home",
        }
    )
    policy.update(schema_version=DELIVERY_CONFIG_SCHEMA_VERSION, publish=True)
    policy["target"]["branch"] = SCOPE["target_branch"]
    (root / ".llm-wiki/publication.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    return policy


def checked(root, output, source, tip, previous=None):
    options: dict[str, Any] = dict(
        target_dir="public",
        previous_receipt=previous,
        source_revision=source,
        target_revision=tip,
    )
    receipt = candidate.export_publication_candidate(root, output_dir=output, **options)
    approval = candidate.review_publication_candidate(
        receipt, reviewer="wiki-editor", reason="Reviewed the complete tree"
    )
    receipt = candidate.check_publication_candidate(
        root,
        candidate_dir=output,
        receipt=receipt,
        reviews=accept_topics(receipt),
        candidate_review=approval,
        **options,
    )
    assert receipt["ready"] and receipt["delivery_ready"] is False
    return receipt, candidate._read_tree(root / output)


@pytest.fixture
def first(consumer):
    policy = opt_in(consumer)
    receipt, files = checked(consumer, "first", SOURCE, BASE)
    before = candidate._read_tree(consumer / "public", target_snapshot=True)
    return consumer, policy, receipt, files, before


def test_v2_requires_explicit_boolean_and_an_exact_release_tag(consumer):
    policy = opt_in(consumer)
    assert validate_publication_config(policy, consumer_root=None)["publish"] is True
    policy["source_policy"] = "release"
    with pytest.raises(ValueError, match="exact release tag"):
        validate_publication_config(policy, consumer_root=None)
    policy["release_tag"] = "published/v1.0"
    assert (
        validate_publication_config(policy, consumer_root=None)["release_tag"]
        == "published/v1.0"
    )
    for invalid in (
        "refs/tags/latest",
        "bad..tag",
        "../other",
        "-n",
        "a.lock",
        "x@{1}",
        "other/*",
    ):
        with pytest.raises(ValueError):
            validate_publication_config(
                {**policy, "release_tag": invalid}, consumer_root=None
            )
        with pytest.raises(ValueError):
            validate_publication_config(
                {**policy, "target": {**policy["target"], "branch": invalid}},
                consumer_root=None,
            )
    for invalid in ("true", 1, None):
        with pytest.raises(ValueError, match="boolean"):
            validate_publication_config(
                {**policy, "publish": invalid}, consumer_root=None
            )
    with pytest.raises(ValueError, match="release source policy"):
        validate_publication_config(
            {**policy, "source_policy": "default-branch"}, consumer_root=None
        )


def test_delivery_binds_exact_artifact_and_emits_only_portable_public_state(first):
    root, policy, receipt, files, before = first
    output, state = delivery.plan_delivery(
        receipt, files, before, policy=policy, target_revision=BASE, **SCOPE
    )
    assert state and state["receipt_id"] == receipt["receipt_id"]
    assert state["basis_id"] == receipt["basis"]["basis_id"]
    assert state["provider_fingerprint"] == receipt["provider"]["fingerprint"]
    assert state["owned"] == {
        path: receipt["files"][path] for path in receipt["ownership"]
    }
    assert state["source_revision"] == SOURCE
    assert delivery.split_delivery_tree(output) == (files, state)
    assert output["Notes.md"] == before["Notes.md"]
    raw = output[delivery.CHECKPOINT_PATH]
    assert all(
        secret not in raw
        for secret in (
            b"wiki-editor",
            b"Reviewed the complete tree",
            b"docs/public",
            str(root).encode(),
        )
    )
    # Source eligibility is checked again by the host before this replay.
    assert delivery.plan_delivery(
        receipt, files, output, policy=policy, target_revision=ADVANCED, **SCOPE
    ) == (output, state)
    with pytest.raises(ValueError, match="no longer matches"):
        delivery.plan_delivery(
            receipt,
            files,
            {**output, "Notes.md": b"changed"},
            policy=policy,
            target_revision=ADVANCED,
            **SCOPE,
        )


def test_delivery_fails_closed_on_wrong_scope_stale_base_and_altered_inputs(first):
    _, policy, receipt, files, before = first

    def plan(**options):
        args: dict[str, Any] = dict(
            receipt=receipt,
            candidate_files=files,
            target_tree=before,
            policy=policy,
            target_revision=BASE,
            **SCOPE,
        )
        return delivery.plan_delivery(**{**args, **options})

    with pytest.raises(ValueError, match="enabled"):
        plan(policy={**policy, "publish": False})
    with pytest.raises(ValueError, match="eligible source policy"):
        plan(
            policy={
                **policy,
                "enforcement": "required"
                if policy["enforcement"] == "advisory"
                else "advisory",
            }
        )
    with pytest.raises(ValueError, match="branch"):
        plan(target_branch="master")
    with pytest.raises(ValueError, match="repository"):
        plan(target_repository="another/repository")
    with pytest.raises(ValueError, match="target base"):
        plan(target_revision=ADVANCED)
    with pytest.raises(ValueError, match="target base"):
        plan(target_tree={**before, "Notes.md": b"changed"})
    with pytest.raises(ValueError, match="Candidate files differ"):
        plan(candidate_files={**files, "Notes.md": b"changed"})
    with pytest.raises(ValueError, match="Reserved"):
        plan(candidate_files={**files, delivery.CHECKPOINT_PATH.upper(): b"private"})
    with pytest.raises(ValueError):
        plan(target_tree={**before, delivery.CHECKPOINT_PATH: b"{}"})


def test_checked_target_skips_only_a_valid_root_sidecar_and_noop_creates_no_checkpoint_change(
    first,
):
    root, policy, receipt, files, before = first
    output, state = delivery.plan_delivery(
        receipt, files, before, policy=policy, target_revision=BASE, **SCOPE
    )
    for name, raw in output.items():
        path = root / "public" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    assert candidate._read_tree(root / "public", target_snapshot=True) == files
    with pytest.raises(ValueError):
        candidate._read_tree(root / "public")
    del policy["content"]["adoptions"]
    (root / ".llm-wiki/publication.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    next_receipt, next_files = checked(
        root, "second", LATER_SOURCE, ADVANCED, previous=receipt
    )
    assert delivery.plan_delivery(
        next_receipt,
        next_files,
        output,
        policy=policy,
        target_revision=ADVANCED,
        **SCOPE,
    ) == (output, state)

    (root / "public/Home.md").write_bytes(b"unreviewed public edit")
    with pytest.raises(ValueError, match="Owned target files differ"):
        candidate._read_tree(root / "public", target_snapshot=True)
    with pytest.raises(ValueError):
        delivery.split_delivery_tree(
            {**output, delivery.CHECKPOINT_PATH.upper(): b"{}"}
        )


def test_first_rollback_preserves_later_manual_edits_and_restores_pre_adoption_bytes(
    first,
):
    _, policy, receipt, files, before = first
    output, _ = delivery.plan_delivery(
        receipt, files, before, policy=policy, target_revision=BASE, **SCOPE
    )
    manual = b"# Notes\n\nMaintainer's later guidance.\n"
    existing = {**output, "Notes.md": manual}
    args: dict[str, Any] = dict(
        policy=policy,
        source_revision=LATER_SOURCE,
        target_revision=ADVANCED,
        restore_revision=BASE,
        **SCOPE,
    )
    restored, proposal = delivery.plan_rollback(existing, before, **args)
    public, state = delivery.split_delivery_tree(restored)
    assert public == {**before, "Notes.md": manual}
    assert state and not state["owned"] and state["receipt_id"] is None
    assert state["source_revision"] == LATER_SOURCE
    approval = delivery.review_rollback(
        proposal, reviewer="editor", reason="Restore last accepted text"
    )
    delivery.validate_rollback_review(approval, rollback_id=proposal["rollback_id"])
    assert "Notes.md" not in proposal["diff"] and "Accounts.md" in proposal["diff"]
    with pytest.raises(ValueError, match="commitment"):
        delivery.review_rollback(
            {**proposal, "diff": "unreviewed explanation"},
            reviewer="editor",
            reason="Restore",
        )
    changed = deepcopy(proposal)
    changed["target_revision"] = "f" * 40
    with pytest.raises(ValueError, match="commitment"):
        delivery.review_rollback(changed, reviewer="editor", reason="Restore")
    with pytest.raises(ValueError, match="exact proposal"):
        delivery.validate_rollback_review(approval, rollback_id=receipt["receipt_id"])


def test_rollback_to_earlier_checkpoint_keeps_current_manual_content_and_high_water(
    first,
):
    root, policy, first_receipt, files, before = first
    first_tree, _ = delivery.plan_delivery(
        first_receipt, files, before, policy=policy, target_revision=BASE, **SCOPE
    )
    for name, raw in first_tree.items():
        dest = root / "public" / name
        dest.parent.mkdir(exist_ok=True, parents=True)
        dest.write_bytes(raw)
    del policy["content"]["adoptions"]
    (root / ".llm-wiki/publication.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    (root / "docs/public/Home.md").write_text(
        "# Home\n\nUpdated home.\n", encoding="utf-8"
    )
    changed, next_files = checked(
        root, "second", LATER_SOURCE, ADVANCED, previous=first_receipt
    )
    second_tree, _ = delivery.plan_delivery(
        changed,
        next_files,
        first_tree,
        policy=policy,
        target_revision=ADVANCED,
        **SCOPE,
    )
    second_tree["Notes.md"] = b"# Notes\n\nEdited after both deliveries.\n"
    second_tree["Other.md"] = b"# Another manual page\n"
    args: dict[str, Any] = dict(
        policy=policy,
        source_revision=LATER_SOURCE,
        target_revision="7" * 40,
        restore_revision=ADVANCED,
        **SCOPE,
    )
    restored, proposal = delivery.plan_rollback(second_tree, first_tree, **args)
    assert restored["Notes.md"] == second_tree["Notes.md"]
    assert restored["Other.md"] == second_tree["Other.md"]
    assert restored["Home.md"] == first_tree["Home.md"]
    _, checkpoint = delivery.split_delivery_tree(restored)
    assert checkpoint
    assert (
        checkpoint["source_revision"] == LATER_SOURCE
        and checkpoint["content_source_revision"] == SOURCE
    )
    assert checkpoint["receipt_id"] == first_receipt["receipt_id"]
    assert checkpoint["rollback_id"] == proposal["rollback_id"]
    again, _ = delivery.plan_rollback(
        restored, first_tree, **{**args, "target_revision": "8" * 40}
    )
    assert again == restored

    with pytest.raises(ValueError, match="Owned target files differ"):
        delivery.plan_rollback(
            {**second_tree, "Home.md": b"unreviewed edit"}, first_tree, **args
        )


def test_rollback_blocks_a_new_manual_file_at_a_previously_owned_path(first):
    _, policy, receipt, files, before = first
    historical, state = delivery.plan_delivery(
        receipt, files, before, policy=policy, target_revision=BASE, **SCOPE
    )
    assert state
    # A later delivery retired this asset and its incoming links. A manual
    # author has since created a different attachment at the retired path.
    updated = {**files, "assets/limits.txt": b"Manually maintained attachment"}
    current, _ = delivery._compose(
        updated,
        {
            **{k: v for k, v in state.items() if k != "checkpoint_id"},
            "owned": {
                k: v for k, v in state["owned"].items() if k != "assets/limits.txt"
            },
            "previous_checkpoint_id": state["checkpoint_id"],
        },
    )
    with pytest.raises(ValueError, match="currently unmanaged"):
        delivery.plan_rollback(
            current,
            historical,
            policy=policy,
            source_revision=LATER_SOURCE,
            target_revision="7" * 40,
            restore_revision=ADVANCED,
            **SCOPE,
        )
