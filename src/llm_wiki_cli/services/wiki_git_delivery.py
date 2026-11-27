"""Read-only completeness of an owned native snapshot under effective Git policy."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
import re
from typing import Any

from llm_wiki_engine.io import decode_markdown_bytes
from llm_wiki_engine.knowledge_storage import KnowledgeStorageError
from llm_wiki_engine.knowledge_storage_diagnostics import _git
from llm_wiki_engine.knowledge_storage_lifecycle import _committed_inputs
from llm_wiki_engine.knowledge_storage_io import _absolute_path
from llm_wiki_engine.knowledge_governance import GOVERNANCE_FILENAME
from llm_wiki_engine.maintenance_protocol import ADOPTION_FILENAME
from .wiki_git_policy import _git_environment, classify_wiki_git_policy

MAX_DELIVERY_FILES = 20_000
MAX_DELIVERY_BYTES = 128 * 1024 * 1024
MAX_GIT_METADATA_BYTES = 16 * 1024 * 1024
SAMPLE_LIMIT = 20
_OID = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _command(
    root: Path,
    arguments: list[str],
    *,
    data: bytes | None = None,
    maximum: int = MAX_GIT_METADATA_BYTES,
) -> tuple[int, bytes]:
    return _git(
        root,
        arguments,
        input_bytes=data,
        maximum=maximum,
        environment=_git_environment(preserve_index=True),
    )


def _ignored(root: Path, paths: list[str]) -> set[str]:
    probes = {
        (("./" + path) if path.startswith(":") else path).encode("utf-8"): path
        for path in paths
    }
    code, output = _command(
        root,
        ["check-ignore", "--no-index", "-z", "--stdin"],
        data=b"\0".join(probes) + b"\0",
    )
    if code not in {0, 1} or (output and not output.endswith(b"\0")):
        raise KnowledgeStorageError(
            "git", "ignore policy inspection failed", code="git-delivery-indeterminate"
        )
    rows = output[:-1].split(b"\0") if output else []
    if (
        any(path not in probes for path in rows)
        or len(rows) != len(set(rows))
        or bool(rows) != (code == 0)
    ):
        raise KnowledgeStorageError(
            "git",
            "ignore policy result is incomplete",
            code="git-delivery-indeterminate",
        )
    return {probes[path] for path in rows}


def _index(root: Path) -> tuple[bytes, dict[bytes, list[tuple[bytes, bytes, bytes]]]]:
    code, output = _command(root, ["ls-files", "--stage", "-z"])
    if code or (output and not output.endswith(b"\0")):
        raise KnowledgeStorageError(
            "git", "index inspection failed", code="git-delivery-indeterminate"
        )
    entries: dict[bytes, list[tuple[bytes, bytes, bytes]]] = {}
    for row in output[:-1].split(b"\0") if output else []:
        head, separator, name = row.partition(b"\t")
        fields = head.split(b" ")
        if (
            not separator
            or len(fields) != 3
            or not _OID.fullmatch(fields[1])
            or fields[2] not in {b"0", b"1", b"2", b"3"}
        ):
            raise KnowledgeStorageError(
                "git", "invalid index entry", code="git-delivery-indeterminate"
            )
        entries.setdefault(name, []).append((fields[0], fields[1], fields[2]))
    return output, entries


def _blobs(root: Path, identities: set[bytes]) -> dict[bytes, bytes]:
    if not identities:
        return {}
    ordered = sorted(identities)
    code, output = _command(
        root,
        ["cat-file", "--batch"],
        data=b"\n".join(ordered) + b"\n",
        maximum=MAX_DELIVERY_BYTES,
    )
    if code:
        raise KnowledgeStorageError(
            "git", "staged objects are unavailable", code="git-delivery-indeterminate"
        )
    result = {}
    offset = 0
    for identity in ordered:
        end = output.find(b"\n", offset)
        fields = output[offset:end].split(b" ") if end >= 0 else []
        if (
            len(fields) != 3
            or fields[:2] != [identity, b"blob"]
            or not fields[2].isdigit()
        ):
            raise KnowledgeStorageError(
                "git",
                "staged object is not an available blob",
                code="git-delivery-indeterminate",
            )
        size = int(fields[2])
        offset = end + 1
        if (
            size > MAX_DELIVERY_BYTES
            or offset + size >= len(output)
            or output[offset + size : offset + size + 1] != b"\n"
        ):
            raise KnowledgeStorageError(
                "git",
                "staged blob exceeds its bound or is incomplete",
                code="git-delivery-indeterminate",
            )
        result[identity] = output[offset : offset + size]
        offset += size + 1
    if offset != len(output):
        raise KnowledgeStorageError(
            "git", "unexpected staged object output", code="git-delivery-indeterminate"
        )
    return result


def _require_absent_authority(root: Path, paths: set[str]) -> None:
    for path in paths:
        try:
            (root / path).lstat()
        except FileNotFoundError:
            continue
        raise KnowledgeStorageError(
            "authority",
            "native authority appeared during inspection",
            code="git-delivery-mutation",
        )


def _staged(
    root: Path, expected: Mapping[str, bytes], markdown: set[str], absent: set[str]
):
    code, partial = _command(
        root,
        [
            "config",
            "--includes",
            "--name-only",
            "--get-regexp",
            r"(^extensions\.partialclone$|^remote\..*\.promisor$)",
        ],
    )
    if code not in {0, 1} or partial.strip():
        raise KnowledgeStorageError(
            "git",
            "staged proof requires a complete local object database",
            code="git-delivery-indeterminate",
        )
    before, entries = _index(root)
    unexpected = sorted(path for path in absent if path.encode("utf-8") in entries)
    selected = {}
    missing, mismatched = [], []
    for path in expected:
        rows = entries.get(path.encode("utf-8"), [])
        if not rows:
            missing.append(path)
        elif (
            len(rows) != 1
            or rows[0][0] not in {b"100644", b"100755"}
            or rows[0][2] != b"0"
        ):
            mismatched.append(path)
        else:
            selected[path] = rows[0][1]
    blobs = _blobs(root, set(selected.values()))
    for path, identity in selected.items():
        actual, current = blobs[identity], expected[path]
        if path in markdown:
            try:
                same = decode_markdown_bytes(actual) == decode_markdown_bytes(current)
            except (ValueError, UnicodeError):
                same = False
        else:
            same = hashlib.sha256(actual).digest() == hashlib.sha256(current).digest()
        if not same:
            mismatched.append(path)
    return before, {
        "status": "incomplete" if missing or mismatched or unexpected else "complete",
        "missing": len(missing),
        "mismatched": len(mismatched),
        "missing_samples": sorted(missing)[:SAMPLE_LIMIT],
        "mismatched_samples": sorted(mismatched)[:SAMPLE_LIMIT],
        "unexpected": len(unexpected),
        "unexpected_samples": unexpected[:SAMPLE_LIMIT],
    }


def inspect_wiki_git_delivery(
    wiki_dir: str | Path, *, staged: bool = False
) -> dict[str, Any]:
    """Check every required native file; an explicit staged check gates handoff.

    Ignore policy alone never proves index completeness. Markdown newline
    normalization is allowed; native commitments and binary objects must retain
    exact bytes. No source inventory, setup, Git writes or network calls occur.
    """
    if type(staged) is not bool:
        raise KnowledgeStorageError("staged", "must be a boolean")
    result: dict[str, Any] = {
        "schema_version": "llm-wiki-git-delivery/v1",
        "delivery_state": "indeterminate",
        "reason": "not-inspected",
        "scope": "required-native-snapshot-files",
        "required_files": 0,
        "eligible_files": 0,
        "ignored_files": 0,
        "ignored_samples": [],
        "staged": {"status": "not-checked"},
        "read_only": True,
        "full_inventory_performed": False,
        "network_used": False,
        "ok": False,
    }
    try:
        root = _absolute_path(Path(wiki_dir))
        policy = classify_wiki_git_policy(root)
        if policy.repository_root is None or policy.wiki_path is None:
            result["reason"] = policy.reason
            if staged:
                result["staged"] = {"status": "indeterminate"}
            return result
        repository = policy.repository_root
        state, session, _ = _committed_inputs(root)
        assert state.knowledge is not None and state.surface is not None
        markdown = {
            concept.document.canonical_path for concept in state.knowledge.concepts
        }
        for relative in state.surface["assets"]["referenced"]:
            session.read(relative, MAX_DELIVERY_BYTES)
        if (
            len(session.observations) > MAX_DELIVERY_FILES
            or sum(len(row.content) for row in session.observations.values())
            > MAX_DELIVERY_BYTES
        ):
            raise KnowledgeStorageError(
                "snapshot",
                "delivery inspection exceeds its bound",
                code="git-delivery-limit",
            )
        prefix = root.relative_to(repository)
        expected = {
            (prefix / relative).as_posix(): row.content
            for relative, row in session.observations.items()
        }
        absent = {
            (prefix / name).as_posix()
            for name in (ADOPTION_FILENAME, GOVERNANCE_FILENAME)
            if name not in session.observations
        }
        _require_absent_authority(repository, absent)
        markdown = {(prefix / relative).as_posix() for relative in markdown}
        paths = sorted(expected)
        ignored = _ignored(repository, paths)
        delivery = (
            "git-eligible"
            if not ignored
            else "local-only"
            if len(ignored) == len(paths)
            else "mixed"
        )
        result.update(
            delivery_state=delivery,
            reason="effective-git-policy",
            required_files=len(paths),
            eligible_files=len(paths) - len(ignored),
            ignored_files=len(ignored),
            ignored_samples=sorted(ignored)[:SAMPLE_LIMIT],
            ok=True,
        )
        index_before = None
        if staged:
            index_before, result["staged"] = _staged(
                repository, expected, markdown, absent
            )
            result["ok"] = (
                delivery == "git-eligible" and result["staged"]["status"] == "complete"
            )
        if ignored != _ignored(repository, paths) or (
            staged and index_before != _index(repository)[0]
        ):
            raise KnowledgeStorageError(
                "git",
                "Git policy or index changed during inspection",
                code="git-delivery-mutation",
            )
        session.recheck()
        _require_absent_authority(repository, absent)
        return result
    except (OSError, ValueError, UnicodeError, RuntimeError) as exc:
        result.update(
            delivery_state="indeterminate",
            reason=getattr(exc, "code", "git-delivery-indeterminate"),
            ok=False,
        )
        if staged:
            result["staged"] = {"status": "indeterminate"}
        return result


BRANCH_CHECK_SCHEMA = "llm-wiki-branch-wiki-check/v1"
_MAX_REF_BYTES = 1024


def current_branch(root: str | Path = ".") -> str | None:
    """Return the checked-out branch name, or ``None`` when HEAD is detached."""
    code, output = _command(
        _absolute_path(Path(root)), ["symbolic-ref", "--quiet", "--short", "HEAD"]
    )
    name = output.decode("utf-8", "replace").strip()
    return name if code == 0 and name else None


def ownership_write_refusal(root: str | Path = ".") -> str | None:
    """Explain why this checkout may not write generated wiki state.

    Returns ``None`` when the team policy lets the checked-out branch write.
    A policy that cannot be read is a refusal: it cannot show who may write.
    """
    from .team import TeamConfigError, load_team_config, team_config_path, wiki_ownership

    if not team_config_path(root).exists():
        return None
    try:
        ownership = wiki_ownership(load_team_config(root=root))
    except TeamConfigError as exc:
        return f"Team policy is invalid, so wiki ownership is unknown: {exc}"
    if not ownership.trunk_owned:
        return None
    try:
        branch = current_branch(root)
    except KnowledgeStorageError as exc:
        return f"Could not read the checked-out branch for trunk ownership: {exc}"
    if ownership.may_write(branch):
        return None
    allowed = ", ".join([ownership.trunk, *ownership.writer_branches])
    here = f"branch {branch!r}" if branch else "a detached HEAD"
    return (
        f"The generated wiki is trunk-owned and this checkout is on {here}. "
        f"Only {allowed} may write it. Preview with --dry-run and leave the "
        "wiki to the trunk refresh."
    )


def inspect_branch_wiki_changes(
    wiki_dir: str | Path,
    *,
    base: str,
    branch: str | None = None,
    root: str | Path = ".",
) -> dict[str, Any]:
    """Report generated wiki paths a branch changed since ``base``.

    Under trunk ownership a non-writer branch must leave generated paths as
    they are at its merge base. Only Git metadata is read: no snapshot is
    validated and no source is scanned.
    """
    from .team import TeamConfigError, load_team_config, wiki_ownership

    result: dict[str, Any] = {
        "schema_version": BRANCH_CHECK_SCHEMA,
        "base": base,
        "branch": branch,
        "checked": False,
        "reason": "not-inspected",
        "generated_changes": 0,
        "generated_samples": [],
        "authored_changes": 0,
        "read_only": True,
        "ok": False,
    }
    if (
        not isinstance(base, str)
        or not base
        or base.startswith("-")
        or "\0" in base
        or len(base.encode("utf-8")) > _MAX_REF_BYTES
    ):
        raise KnowledgeStorageError("base", "an explicit bounded Git reference is required")
    try:
        ownership = wiki_ownership(load_team_config(root=root))
    except TeamConfigError as exc:
        result["reason"] = "team-policy-invalid"
        result["error"] = {"code": "team-policy-invalid", "message": str(exc)}
        return result
    result["ownership"] = ownership.to_dict()
    if not ownership.trunk_owned:
        result.update(ok=True, reason="branch-ownership")
        return result
    wiki_root = _absolute_path(Path(wiki_dir))
    policy = classify_wiki_git_policy(wiki_root)
    if policy.repository_root is None or policy.wiki_path is None:
        result["reason"] = policy.reason
        return result
    repository = policy.repository_root
    evaluated = branch if branch is not None else current_branch(repository)
    result["branch"] = evaluated
    if ownership.may_write(evaluated):
        result.update(ok=True, reason="writer-branch")
        return result
    code, _ = _command(repository, ["rev-parse", "--verify", "--quiet", base + "^{commit}"])
    if code:
        result["reason"] = "base-unresolved"
        return result
    prefix = policy.wiki_path.rstrip("/")
    code, output = _command(
        repository,
        ["diff", "--name-only", "-z", "--no-renames", base + "...HEAD", "--", prefix],
    )
    if code or (output and not output.endswith(b"\0")):
        result["reason"] = "diff-unavailable"
        return result
    generated: list[str] = []
    authored = 0
    for raw in output[:-1].split(b"\0") if output else []:
        path = raw.decode("utf-8", "surrogateescape")
        relative = path[len(prefix) + 1:] if path.startswith(prefix + "/") else path
        if ownership.is_authored(relative):
            authored += 1
        else:
            generated.append(path)
    generated.sort()
    result.update(
        checked=True,
        ok=not generated,
        reason="generated-paths-unchanged" if not generated else "generated-paths-changed",
        generated_changes=len(generated),
        generated_samples=[
            path.encode("utf-8", "surrogateescape").decode("utf-8", "replace")
            for path in generated[:SAMPLE_LIMIT]
        ],
        authored_changes=authored,
    )
    return result
