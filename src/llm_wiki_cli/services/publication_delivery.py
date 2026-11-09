"""Pure validation and composition of a reviewed GitHub wiki delivery or rollback."""

from __future__ import annotations

from collections.abc import Mapping
import difflib
import json
from typing import Any

from .knowledge_evidence import canonical_json_bytes, hash_json, sha256_bytes
from .publication_candidate import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_TREE_BYTES,
    _PRIVATE,
    _REVISION,
    _VCS,
    _check_hash,
    _hash_map,
    _hashes,
    _validate_candidate_files,
    validate_publication_receipt,
)
from .publication_config import (
    DELIVERY_CHECKPOINT_PATH as CHECKPOINT_PATH,
    DELIVERY_CONFIG_SCHEMA_VERSION,
    publication_ref_name,
    publication_repository,
    validate_publication_config,
)
from .publication_links import check_github_wiki

CHECKPOINT_SCHEMA = "llm-wiki-publication-checkpoint/v1"
ROLLBACK_SCHEMA = "llm-wiki-publication-rollback/v1"
ROLLBACK_REVIEW_SCHEMA = "llm-wiki-rollback-review/v1"
_CONTENT_KEYS = (
    "receipt_id",
    "candidate_id",
    "basis_id",
    "baseline_id",
    "config_hash",
    "provider_fingerprint",
    "content_source_revision",
)
_CHECKPOINT_FIELDS = {
    "schema_version",
    "checkpoint_id",
    "previous_checkpoint_id",
    "rollback_id",
    "source_repository",
    "target_repository",
    "target_branch",
    "source_policy",
    "source_revision",
    "target_base_revision",
    "policy_hash",
    "owned",
    "ownership_hash",
    "tree_hash",
    *_CONTENT_KEYS,
}


def _revision(value: object) -> str:
    if type(value) is not str or _REVISION.fullmatch(value) is None:
        raise ValueError("Delivery requires an immutable Git commit identifier")
    return value


def validate_rollback_review(record: Mapping[str, Any], *, rollback_id: str) -> None:
    """Validate a host-accepted review record against the live rollback proposal."""
    _check_hash(rollback_id)
    if (
        not isinstance(record, Mapping)
        or set(record) != {"schema_version", "rollback_id", "reviewer", "reason"}
        or record["schema_version"] != ROLLBACK_REVIEW_SCHEMA
        or record["rollback_id"] != rollback_id
    ):
        raise ValueError(
            "The rollback needs an accepted review for this exact proposal"
        )
    for field in ("reviewer", "reason"):
        value = record[field]
        if (
            type(value) is not str
            or not value.strip()
            or "\x00" in value
            or len(value.encode("utf-8")) > 4096
        ):
            raise ValueError(
                "The rollback review requires a bounded reviewer and reason"
            )


def review_rollback(
    proposal: Mapping[str, Any], *, reviewer: str, reason: str
) -> dict[str, str]:
    """Prepare a private review record for the consumer's normal acceptance process."""
    if (
        not isinstance(proposal, Mapping)
        or proposal.get("schema_version") != ROLLBACK_SCHEMA
        or proposal.get("rollback_id")
        != hash_json({k: v for k, v in proposal.items() if k != "rollback_id"})
    ):
        raise ValueError("Rollback proposal commitment mismatch")
    record = {
        "schema_version": ROLLBACK_REVIEW_SCHEMA,
        "rollback_id": proposal["rollback_id"],
        "reviewer": reviewer,
        "reason": reason,
    }
    validate_rollback_review(record, rollback_id=record["rollback_id"])
    return record


def _public_hashes(files: Mapping[str, bytes]) -> dict[str, str]:
    if not isinstance(files, Mapping) or len(files) > MAX_FILES:
        raise ValueError("Invalid public delivery inventory")
    size = 0
    for path, data in files.items():
        if type(path) is not str or any(
            part.casefold() in _VCS | _PRIVATE
            or part.casefold().startswith(".llm-wiki")
            for part in path.split("/")
        ):
            raise ValueError("Reserved or invalid public delivery path")
        if type(data) is not bytes or len(data) > MAX_FILE_BYTES:
            raise ValueError("Public delivery file exceeds its byte limit")
        size += len(data)
    if size > MAX_TREE_BYTES:
        raise ValueError("Public delivery tree exceeds its byte limit")
    result = _hashes(files)
    _hash_map(result)
    return result


def _checkpoint_bytes(checkpoint: Mapping[str, Any]) -> bytes:
    raw = canonical_json_bytes(checkpoint) + b"\n"
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("Delivery checkpoint exceeds its byte limit")
    return raw


def _validated_checkpoint(raw: bytes, observed: Mapping[str, str]) -> dict[str, Any]:
    if type(raw) is not bytes or len(raw) > MAX_FILE_BYTES:
        raise ValueError("Invalid delivery checkpoint size")
    try:
        state = json.loads(raw.decode("utf-8"))
        if (
            type(state) is not dict
            or set(state) != _CHECKPOINT_FIELDS
            or raw != _checkpoint_bytes(state)
        ):
            raise ValueError("Invalid delivery checkpoint shape or encoding")
    except (RecursionError, UnicodeError, OverflowError) as exc:
        raise ValueError("Invalid delivery checkpoint encoding") from exc
    if state["schema_version"] != CHECKPOINT_SCHEMA or state[
        "checkpoint_id"
    ] != hash_json({k: v for k, v in state.items() if k != "checkpoint_id"}):
        raise ValueError("Delivery checkpoint identity mismatch")
    publication_repository(state["source_repository"], "source_repository")
    publication_repository(state["target_repository"], "target_repository")
    publication_ref_name(state["target_branch"], "target_branch")
    if state["source_policy"] not in ("default-branch", "release"):
        raise ValueError("Invalid checkpoint source policy")
    for key in ("source_revision", "target_base_revision"):
        _revision(state[key])
    for key in ("policy_hash", "ownership_hash", "tree_hash"):
        _check_hash(state[key])
    for key in ("previous_checkpoint_id", "rollback_id"):
        if state[key] is not None:
            _check_hash(state[key])
    _hash_map(state["owned"])
    if any(observed.get(path) != digest for path, digest in state["owned"].items()):
        raise ValueError("Owned target files differ from the delivery checkpoint")
    if state["receipt_id"] is None:
        if (
            state["rollback_id"] is None
            or state["owned"]
            or any(state[k] is not None for k in _CONTENT_KEYS)
        ):
            raise ValueError(
                "Only a rollback to an unmanaged base can clear the owned state"
            )
    else:
        _revision(state["content_source_revision"])
        for key in _CONTENT_KEYS:
            if key == "content_source_revision" or (
                key == "baseline_id" and state[key] is None
            ):
                continue
            _check_hash(state[key])
    return state


def split_delivery_tree(
    tree: Mapping[str, bytes],
) -> tuple[dict[str, bytes], dict[str, Any] | None]:
    """Separate the exact root checkpoint from public files and validate owned bytes."""
    if not isinstance(tree, Mapping) or len(tree) > MAX_FILES + 1:
        raise ValueError("Invalid wiki tree inventory")
    files = {k: v for k, v in tree.items() if k != CHECKPOINT_PATH}
    hashes = _public_hashes(files)
    state = (
        _validated_checkpoint(tree[CHECKPOINT_PATH], hashes)
        if CHECKPOINT_PATH in tree
        else None
    )
    return files, state


def _scope(policy, source_repository, target_repository, target_branch):
    config = validate_publication_config(policy, consumer_root=None)
    if (
        config["schema_version"] != DELIVERY_CONFIG_SCHEMA_VERSION
        or config["publish"] is not True
    ):
        raise ValueError(
            "Delivery requires an explicitly enabled publication/v2 policy"
        )
    source = publication_repository(source_repository, "source_repository").lower()
    target = publication_repository(target_repository, "target_repository").lower()
    declared = config["target"]["repository"]
    if target != (source if declared == "self" else declared.lower()):
        raise ValueError(
            "Delivery target repository differs from the configured repository"
        )
    branch = publication_ref_name(target_branch, "target_branch")
    if config["target"].get("branch", branch) != branch:
        raise ValueError("Delivery target branch differs from the configured branch")
    return config, {
        "source_repository": source,
        "target_repository": target,
        "target_branch": branch,
        "source_policy": config["source_policy"],
    }


def _match_scope(checkpoint, scope):
    if checkpoint is not None and any(checkpoint[k] != v for k, v in scope.items()):
        raise ValueError(
            "Delivery checkpoint belongs to a different source, target, branch or source policy"
        )


def _compose(public, state):
    checkpoint = {**state, "checkpoint_id": hash_json(state)}
    return {**public, CHECKPOINT_PATH: _checkpoint_bytes(checkpoint)}, checkpoint


def plan_delivery(
    receipt: Mapping[str, Any],
    candidate_files: Mapping[str, bytes],
    target_tree: Mapping[str, bytes],
    *,
    policy: Mapping[str, Any],
    source_repository: str,
    target_repository: str,
    target_branch: str,
    target_revision: str,
) -> tuple[dict[str, bytes], dict[str, Any] | None]:
    """Build the exact proposed target bytes for a host-verified source/ref."""
    config, scope = _scope(policy, source_repository, target_repository, target_branch)
    validate_publication_receipt(receipt)
    if not receipt["ready"] or receipt["target"]["mode"] != "local-snapshot":
        raise ValueError(
            "Delivery requires a checked, fully reviewed local-snapshot candidate"
        )
    if receipt["basis"]["config"] != config:
        raise ValueError(
            "Reviewed publication policy differs from the eligible source policy"
        )
    source = _revision(receipt["context"]["source_revision"])
    base = _revision(receipt["context"]["target_revision"])
    tip = _revision(target_revision)
    hashes = _public_hashes(candidate_files)
    _validate_candidate_files(candidate_files, receipt)
    before, previous = split_delivery_tree(target_tree)
    _match_scope(previous, scope)
    owned = {path: hashes[path] for path in receipt["ownership"]}
    state = {
        "schema_version": CHECKPOINT_SCHEMA,
        **scope,
        "source_revision": source,
        "content_source_revision": source,
        "target_base_revision": base,
        "policy_hash": hash_json(config),
        "config_hash": receipt["config_hash"],
        "basis_id": receipt["basis"]["basis_id"],
        "baseline_id": receipt["inputs"]["baseline_id"],
        "provider_fingerprint": receipt["provider"]["fingerprint"],
        "candidate_id": receipt["candidate_id"],
        "receipt_id": receipt["receipt_id"],
        "owned": owned,
        "ownership_hash": hash_json(receipt["ownership"]),
        "tree_hash": hash_json(hashes),
        "previous_checkpoint_id": previous["checkpoint_id"] if previous else None,
        "rollback_id": None,
    }
    if (
        previous is not None
        and previous["receipt_id"] == receipt["receipt_id"]
        and not previous["rollback_id"]
    ):
        if before == candidate_files and all(
            previous[k] == state[k] for k in state if k != "previous_checkpoint_id"
        ):
            return dict(target_tree), previous
        raise ValueError(
            "Delivered candidate no longer matches the verified target tree"
        )
    if tip != base or _hashes(before) != receipt["target"]["files"]:
        raise ValueError("The target base changed since candidate review")
    expected_previous = previous["receipt_id"] if previous else None
    if receipt["inputs"]["previous_receipt_id"] != expected_previous:
        raise ValueError(
            "Previous ownership receipt differs from the verified checkpoint"
        )
    old_owned = previous["owned"] if previous else {}
    removed = {op["path"] for op in receipt["operations"] if op["kind"] == "remove"}
    if set(old_owned) - set(owned) != removed:
        raise ValueError("Owned retirements differ from the verified checkpoint")
    for operation in receipt["operations"]:
        if (
            operation["kind"] in {"update", "unchanged"}
            and operation["path"] not in old_owned
        ):
            raise ValueError("An existing manual file requires explicit adoption")
    if (
        before == candidate_files
        and owned == old_owned
        and (
            not owned
            or previous is not None
            and previous["ownership_hash"] == state["ownership_hash"]
        )
    ):
        return dict(target_tree), previous
    return _compose(candidate_files, state)


def _rollback_diff(before, after):
    """Retain exact file commitments plus bounded readable Markdown changes."""

    parts = []
    remaining = 512 * 1024
    for path in sorted((before.keys() | after.keys()) - {CHECKPOINT_PATH}):
        old, new = before.get(path), after.get(path)
        if old == new:
            continue
        hashes = [sha256_bytes(v) if v is not None else "absent" for v in (old, new)]
        parts.append(f"\n{path}\n  before {hashes[0]}\n  after  {hashes[1]}\n")
        left, right = old or b"", new or b""
        if (
            max(len(left), len(right)) > min(64 * 1024, remaining)
            or b"\0" in left
            or b"\0" in right
        ):
            continue
        try:
            a, b = left.decode().splitlines(), right.decode().splitlines()
        except UnicodeError:
            continue
        if len(a) * len(b) > 1_000_000:
            continue
        rendered = (
            "\n".join(difflib.unified_diff(a, b, "a/" + path, "b/" + path, lineterm=""))
            + "\n"
        )
        if len(rendered.encode()) <= remaining:
            remaining -= len(rendered.encode())
            parts.append(rendered)
    return "".join(parts)


def plan_rollback(
    current_tree: Mapping[str, bytes],
    historical_tree: Mapping[str, bytes],
    *,
    policy: Mapping[str, Any],
    source_repository: str,
    target_repository: str,
    target_branch: str,
    source_revision: str,
    target_revision: str,
    restore_revision: str,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Propose a new target commit restoring earlier ownership and preserving manual changes."""
    config, scope = _scope(policy, source_repository, target_repository, target_branch)
    source = _revision(source_revision)
    tip, restore = _revision(target_revision), _revision(restore_revision)
    if tip == restore:
        raise ValueError("Choose an earlier target revision to restore")
    current, previous = split_delivery_tree(current_tree)
    if previous is None:
        raise ValueError("Rollback requires a verified current delivery checkpoint")
    historical, prior = split_delivery_tree(historical_tree)
    _match_scope(previous, scope)
    _match_scope(prior, scope)
    if prior is None and (
        previous["previous_checkpoint_id"] is not None
        or restore != previous["target_base_revision"]
    ):
        raise ValueError(
            "An unmanaged restore revision must be the verified first delivery base"
        )
    old_owned = previous["owned"]
    restored_owned = prior["owned"] if prior else {}
    desired = dict(current)
    for path in set(old_owned) | set(restored_owned):
        if path in current and path not in old_owned:
            raise ValueError(
                f"Rollback collides with a currently unmanaged file: {path}"
            )
        if path in historical:
            desired[path] = historical[path]
        else:
            desired.pop(path, None)
    hashes = _public_hashes(desired)
    if not check_github_wiki(desired)["ok"]:
        raise ValueError(
            "Rollback output fails public wiki checks; prepare a fresh reviewed candidate"
        )
    proposal = {
        "schema_version": ROLLBACK_SCHEMA,
        **scope,
        "source_revision": source,
        "target_revision": tip,
        "restore_revision": restore,
        "policy_hash": hash_json(config),
        "checkpoint_id": previous["checkpoint_id"],
        "restore_checkpoint_id": prior["checkpoint_id"] if prior else None,
        "before_tree_hash": hash_json(_hashes(current)),
        "diff": _rollback_diff(current, desired),
        "tree_hash": hash_json(hashes),
        "owned": restored_owned,
    }
    proposal["rollback_id"] = hash_json(proposal)
    restored_ownership_hash = prior["ownership_hash"] if prior else hash_json({})
    if (
        desired == current
        and previous["ownership_hash"] == restored_ownership_hash
        and old_owned == restored_owned
    ):
        return dict(current_tree), proposal
    state = {
        "schema_version": CHECKPOINT_SCHEMA,
        **scope,
        "source_revision": source,
        "target_base_revision": tip,
        "policy_hash": proposal["policy_hash"],
        **{key: prior[key] if prior else None for key in _CONTENT_KEYS},
        "owned": restored_owned,
        "ownership_hash": restored_ownership_hash,
        "tree_hash": proposal["tree_hash"],
        "previous_checkpoint_id": previous["checkpoint_id"],
        "rollback_id": proposal["rollback_id"],
    }
    return _compose(desired, state)[0], proposal
