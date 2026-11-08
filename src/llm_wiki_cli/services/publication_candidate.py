"""Portable, review-bound GitHub wiki candidates without remote mutation."""

from __future__ import annotations

from copy import deepcopy
import json
from importlib import metadata
from pathlib import Path
import re
import stat
from typing import Any, Mapping

from .. import __version__
from .filesystem_guard import atomic_write_private_bytes, ensure_guarded_directory
from .knowledge_evidence import hash_json, sha256_bytes
from .knowledge_storage_io import StorageReadSession, _absolute_path
from .publication_config import (
    DELIVERY_CHECKPOINT_PATH,
    load_publication_config,
    publication_control_overlap,
    publication_input_controls,
    publication_path,
)
from .publication_contracts import (
    _json_tree,
    validate_publication_basis,
    validate_publication_report,
)
from .publication_impact import capture_publication_basis, compare_publication_impact
from .validation import portable_path_key, require_portable_relative_path


RECEIPT_SCHEMA = "llm-wiki-publication-candidate/v1"
REVIEW_SCHEMA = "llm-wiki-publication-candidate-review/v1"
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TREE_BYTES = 64 * 1024 * 1024
MAX_FILES = 5000
_VCS = {".git", ".hg", ".svn"}
_PRIVATE = {".venv", "__pycache__", "node_modules", ".llm-wiki"}
_HASH = re.compile(r"sha256:[0-9a-f]{64}")
_REVISION = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
_RECEIPT_FIELDS = {
    "schema_version",
    "provider",
    "context",
    "config_hash",
    "inputs",
    "target",
    "basis",
    "impact",
    "ownership",
    "operations",
    "files",
    "tree_hash",
    "checks",
    "candidate_id",
    "review",
    "ready",
    "delivery_ready",
    "receipt_id",
}


def _portable(value):
    return require_portable_relative_path(value)


def _sealed(value, key):
    return {**value, key: hash_json(value)}


def _hashes(files):
    return {path: sha256_bytes(raw) for path, raw in sorted(files.items())}


def _same(left: Path, right: Path) -> bool:
    return left == right or (left.exists() and right.exists() and left.samefile(right))


def _candidate_path(root, value):
    if not isinstance(value, (str, Path)):
        raise ValueError("Candidate directories require an explicit path")
    selected = Path(value)
    if ".." in selected.parts:
        raise ValueError("Candidate directories cannot traverse parent paths")
    if any(
        part.casefold() in _VCS | {".venv", "__pycache__", "node_modules"}
        for part in selected.parts
    ):
        raise ValueError("Candidate directories cannot be inside VCS or runtime state")
    return (
        _absolute_path(selected)
        if selected.is_absolute()
        else publication_path(root, _portable(selected.as_posix()))
    )


def _within(path: Path, root: Path) -> bool:
    return root in path.parents or any(
        _same(parent, root) for parent in (path, *path.parents)
    )


def _target_path(root, value):
    if not isinstance(value, (str, Path)):
        raise ValueError("A local target snapshot directory is required")
    selected = Path(value)
    if (
        any(
            part.casefold()
            in _VCS
            | {
                ".venv",
                "__pycache__",
                "node_modules",
                ".llm-wiki-knowledge",
                ".llm-wiki-manifest",
            }
            for part in selected.parts
        )
        or selected.name.casefold() == ".llm-wiki"
    ):
        raise ValueError("Target snapshots cannot be inside VCS or runtime state")
    target = publication_path(root, value)
    if _same(target, root) or not target.is_dir():
        raise ValueError("Target must be a separate local public wiki snapshot")
    return target


def _tree_paths(root: Path, *, target_snapshot: bool):
    paths = []
    pending = [root]
    while pending:
        directory = pending.pop()
        for item in sorted(directory.iterdir(), key=lambda value: value.name):
            relative = item.relative_to(root).as_posix()
            if item.name.casefold() in _VCS:
                if not target_snapshot:
                    raise ValueError("Candidate files cannot include VCS metadata")
                continue
            _portable(relative)
            if item.is_symlink():
                raise ValueError("Wiki trees cannot contain symlinks or reparse points")
            info = item.lstat()
            if getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("Wiki trees cannot contain reparse points")
            checkpoint = target_snapshot and relative == DELIVERY_CHECKPOINT_PATH
            if not checkpoint and (
                item.name.casefold() in _PRIVATE
                or item.name.casefold().startswith(".llm-wiki")
            ):
                raise ValueError(
                    "Wiki trees cannot contain native state or private workspace files"
                )
            if stat.S_ISDIR(info.st_mode) and not checkpoint:
                pending.append(item)
            elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                paths.append(relative)
                if len(paths) > MAX_FILES + int(target_snapshot):
                    raise ValueError("Wiki tree exceeds the public file limit")
            else:
                raise ValueError("Wiki trees require single-link regular files")
    return sorted(paths)


def _read_tree(root: Path, *, target_snapshot: bool = False):
    root = _absolute_path(root)
    paths = _tree_paths(root, target_snapshot=target_snapshot)
    files = {}
    with StorageReadSession(root, max_bytes=3 * MAX_TREE_BYTES).phase() as session:
        total = 0
        for path in paths:
            raw = session.read(path, MAX_FILE_BYTES)
            if path != DELIVERY_CHECKPOINT_PATH:
                total += len(raw)
            if total > MAX_TREE_BYTES:
                raise ValueError("Wiki tree exceeds the public byte limit")
            files[path] = raw
    session.recheck()
    if paths != _tree_paths(root, target_snapshot=target_snapshot):
        raise ValueError("Wiki tree changed during capture")
    if target_snapshot and DELIVERY_CHECKPOINT_PATH in files:
        from .publication_delivery import split_delivery_tree

        files, _ = split_delivery_tree(files)
    if len(files) > MAX_FILES:
        raise ValueError("Wiki tree exceeds the public file limit")
    return files


def _provider():
    package = Path(__file__).parents[1]
    registry = json.loads(
        (package / "services/analysis_contracts.json").read_text(encoding="utf-8")
    )
    names = set(registry["classified_python_files"]) | {
        name
        for name in registry["classified_helper_files"]
        if not Path(name).name.startswith(".")
    }
    names.update(
        path.relative_to(package).as_posix()
        for path in (package / "schemas").glob("*.json")
    )
    names.add("py.typed")
    names.add("services/analysis_contracts.json")
    files = {}
    with StorageReadSession(package).phase() as session:
        for name in sorted(names):
            files[name] = sha256_bytes(session.read(name, MAX_FILE_BYTES))
    session.recheck()
    try:
        parser_version = metadata.version("markdown-it-py")
    except metadata.PackageNotFoundError:
        parser_version = None
    return {
        "name": "agent-wiki-cli",
        "version": __version__,
        "parser_version": parser_version,
        "fingerprint": hash_json({"files": files, "parser_version": parser_version}),
    }


def _check_hash(value):
    if type(value) is not str or _HASH.fullmatch(value) is None:
        raise ValueError("Candidate commitments require canonical SHA-256 values")


def _hash_map(value):
    if type(value) is not dict or len(value) > MAX_FILES:
        raise ValueError("Candidate file inventory is invalid")
    seen = {}
    prefixes = {}
    for path, digest in value.items():
        _portable(path)
        _check_hash(digest)
        key = portable_path_key(path)
        if key in seen:
            raise ValueError("Candidate file inventory contains a portable collision")
        seen[key] = path
        parts = path.split("/")
        for index in range(1, len(parts) + 1):
            spelling = tuple(parts[:index])
            folded = tuple(portable_path_key(part) for part in spelling)
            if prefixes.setdefault(folded, spelling) != spelling:
                raise ValueError(
                    "Candidate paths contain inconsistent portable directory spelling"
                )
    for path in value:
        if any(
            parent.as_posix() in value
            for parent in Path(path).parents
            if parent.as_posix() != "."
        ):
            raise ValueError("Candidate files collide with a parent path")


def _proposal(receipt):
    return hash_json(
        {
            key: receipt[key]
            for key in (
                "schema_version",
                "provider",
                "context",
                "config_hash",
                "target",
                "ownership",
                "operations",
                "files",
                "tree_hash",
                "checks",
            )
        }
        | {
            "basis_id": receipt["basis"]["basis_id"],
            "baseline_id": receipt["inputs"]["baseline_id"],
            "previous_receipt_id": receipt["inputs"]["previous_receipt_id"],
        }
    )


def _validate_review(value):
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "candidate_id",
        "decision",
        "reviewer",
        "reason",
        "review_id",
    }:
        raise ValueError("Candidate review has missing or unknown fields")
    if value["schema_version"] != REVIEW_SCHEMA or value["decision"] != "accepted":
        raise ValueError("Candidate review schema or decision is unsupported")
    for key in ("candidate_id", "review_id"):
        _check_hash(value[key])
    for key in ("reviewer", "reason"):
        if (
            type(value[key]) is not str
            or not value[key].strip()
            or len(value[key].encode("utf-8")) > 4096
            or "\x00" in value[key]
        ):
            raise ValueError("Candidate review needs a bounded reviewer and rationale")
    if value["review_id"] != hash_json(
        {key: item for key, item in value.items() if key != "review_id"}
    ):
        raise ValueError("Candidate review commitment is invalid")


def validate_publication_receipt(receipt: Mapping[str, Any]) -> None:
    """Validate a complete receipt without trusting its readiness assertions."""
    if not isinstance(receipt, Mapping):
        raise ValueError("Candidate receipt must be a mapping")
    receipt = dict(receipt)
    _json_tree(receipt)
    if (
        len(
            json.dumps(
                receipt, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        )
        > MAX_TREE_BYTES
    ):
        raise ValueError("Candidate receipt exceeds its document byte limit")
    if (
        not isinstance(receipt, Mapping)
        or set(receipt) != _RECEIPT_FIELDS
        or receipt["schema_version"] != RECEIPT_SCHEMA
    ):
        raise ValueError("Candidate receipt has missing, unknown or unsupported fields")
    for key in ("receipt_id", "candidate_id", "config_hash", "tree_hash"):
        _check_hash(receipt[key])
    if receipt["receipt_id"] != hash_json(
        {key: value for key, value in receipt.items() if key != "receipt_id"}
    ):
        raise ValueError("Candidate receipt commitment is invalid")
    validate_publication_basis(receipt["basis"])
    validate_publication_report(receipt["impact"])
    if (
        receipt["config_hash"] != hash_json(receipt["basis"]["config"])
        or receipt["impact"]["basis"]["candidate"] != receipt["basis"]["basis_id"]
    ):
        raise ValueError("Candidate receipt does not bind its current basis")
    _hash_map(receipt["files"])
    target = receipt["target"]
    if (
        type(target) is not dict
        or set(target) != {"mode", "files", "tree_hash", "remote_verified"}
        or type(target["mode"]) is not str
        or target["mode"] not in {"local-snapshot", "artifact-only"}
        or target["remote_verified"] is not False
    ):
        raise ValueError(
            "Candidate target must be an unverified local snapshot or artifact-only basis"
        )
    _hash_map(target["files"])
    if target["mode"] == "artifact-only" and target["files"]:
        raise ValueError("Artifact-only candidates cannot bind existing target files")
    if target["tree_hash"] != hash_json(target["files"]) or receipt[
        "tree_hash"
    ] != hash_json(receipt["files"]):
        raise ValueError("Candidate tree commitment is invalid")
    context = receipt["context"]
    if type(context) is not dict or set(context) != {
        "source_revision",
        "target_revision",
    }:
        raise ValueError("Candidate context is invalid")
    for revision in context.values():
        if revision is not None and (
            type(revision) is not str or _REVISION.fullmatch(revision) is None
        ):
            raise ValueError(
                "Candidate revisions must be immutable hexadecimal identifiers"
            )
    provider = receipt["provider"]
    if (
        type(provider) is not dict
        or set(provider) != {"name", "version", "parser_version", "fingerprint"}
        or provider["name"] != "agent-wiki-cli"
        or type(provider["version"]) is not str
    ):
        raise ValueError("Candidate provider identity is invalid")
    _check_hash(provider["fingerprint"])
    if provider["parser_version"] is not None and (
        type(provider["parser_version"]) is not str or not provider["parser_version"]
    ):
        raise ValueError("Candidate parser identity is invalid")
    inputs = receipt["inputs"]
    if type(inputs) is not dict or set(inputs) != {
        "baseline_id",
        "reviews_hash",
        "previous_receipt_id",
    }:
        raise ValueError("Candidate input commitments are invalid")
    for value in inputs.values():
        if value is not None:
            _check_hash(value)
    if (
        receipt["impact"]["config_hash"] != receipt["config_hash"]
        or receipt["impact"]["basis"]["baseline"] != inputs["baseline_id"]
    ):
        raise ValueError("Candidate impact report belongs to different inputs")
    if type(receipt["ownership"]) is not dict or not set(receipt["ownership"]) <= set(
        receipt["files"]
    ):
        raise ValueError("Candidate ownership is outside the output inventory")
    for item in receipt["ownership"].values():
        if (
            type(item) is not dict
            or set(item) != {"kind", "owner", "source_document"}
            or type(item["kind"]) is not str
            or item["kind"] not in {"page", "asset"}
            or type(item["owner"]) is not str
            or not item["owner"].strip()
        ):
            raise ValueError("Candidate ownership declaration is invalid")
        _portable(item["source_document"])
    config = receipt["basis"]["config"]
    if "content" not in config:
        raise ValueError("Candidate receipt needs an explicit content profile")
    declared = {}
    for topic in config["topics"]:
        if topic["edit_at"] == "repository":
            if topic.get("anchor") or topic["wiki_page"] in declared:
                raise ValueError("Candidate receipt requires whole-page ownership")
            declared[topic["wiki_page"]] = {
                "kind": "page",
                "owner": topic["owner"],
                "source_document": topic["source_document"],
            }
    for asset in config["content"].get("assets", []):
        if asset["wiki_path"] in declared:
            raise ValueError("Candidate receipt repeats an owned path")
        declared[asset["wiki_path"]] = {
            "kind": "asset",
            "owner": asset["owner"],
            "source_document": asset["source_document"],
        }
    if receipt["ownership"] != declared:
        raise ValueError("Candidate ownership does not match its configured sources")
    adoptions = {item["path"]: item for item in config["content"].get("adoptions", [])}
    removals = {item["path"]: item for item in config["content"].get("removals", [])}
    if set(adoptions) - set(receipt["ownership"]):
        raise ValueError("Candidate adoptions must name a current owned output")
    if (
        type(receipt["operations"]) is not list
        or len(receipt["operations"]) > MAX_FILES
    ):
        raise ValueError("Candidate operation inventory is invalid")
    seen = set()
    for item in receipt["operations"]:
        if (
            type(item) is not dict
            or set(item) != {"path", "kind", "before", "after", "reason"}
            or type(item["kind"]) is not str
            or item["kind"] not in {"add", "update", "unchanged", "adopt", "remove"}
        ):
            raise ValueError("Candidate operation is invalid")
        _portable(item["path"])
        if item["path"] in seen:
            raise ValueError("Candidate operations repeat a destination")
        seen.add(item["path"])
        for key in ("before", "after"):
            if item[key] is not None:
                _check_hash(item[key])
        if item["before"] != target["files"].get(item["path"]) or item[
            "after"
        ] != receipt["files"].get(item["path"]):
            raise ValueError("Candidate operation does not match its trees")
        if item["kind"] == "remove" and item["after"] is not None:
            raise ValueError("Candidate removal still exists in output")
        if item["kind"] == "remove":
            if (
                inputs["previous_receipt_id"] is None
                or inputs["baseline_id"] is None
                or item["path"] in receipt["ownership"]
                or item["path"] not in removals
                or item["before"] != removals[item["path"]]["expected_hash"]
                or item["reason"] != removals[item["path"]]["reason"]
            ):
                raise ValueError(
                    "Candidate removals need prior ownership, a baseline and their configured disposition"
                )
        elif item["path"] not in receipt["ownership"] or item["after"] is None:
            raise ValueError("Candidate changed an unmanaged path")
        elif item["path"] in adoptions:
            adoption = adoptions[item["path"]]
            if (
                item["kind"] != "adopt"
                or item["before"] != adoption["expected_hash"]
                or item["reason"] != adoption["reason"]
            ):
                raise ValueError(
                    "Candidate adoption does not match its configured disposition"
                )
        elif item["kind"] == "adopt" or item["reason"] is not None:
            raise ValueError("Candidate operation has an unconfigured disposition")
        if item["kind"] == "add" and item["before"] is not None:
            raise ValueError("Candidate addition already exists in its target")
        if item["kind"] == "unchanged" and item["before"] != item["after"]:
            raise ValueError("Candidate unchanged operation has different bytes")
        if item["kind"] == "update" and (
            item["before"] is None or item["before"] == item["after"]
        ):
            raise ValueError("Candidate update requires changed existing content")
        if (
            item["kind"] in {"update", "unchanged"}
            and inputs["previous_receipt_id"] is None
        ):
            raise ValueError(
                "Candidate existing outputs require prior ownership or an adoption disposition"
            )
    if set(receipt["ownership"]) - seen:
        raise ValueError("Candidate operations omit an owned output")
    removed = {
        item["path"] for item in receipt["operations"] if item["kind"] == "remove"
    }
    if removed != set(removals):
        raise ValueError(
            "Candidate removals do not match their configured dispositions"
        )
    if set(target["files"]) - set(receipt["files"]) != removed & set(target["files"]):
        raise ValueError("Candidate removed paths without an explicit disposition")
    for path, digest in receipt["files"].items():
        if path not in receipt["ownership"] and target["files"].get(path) != digest:
            raise ValueError("Candidate did not preserve unmanaged target bytes")
    checks = receipt["checks"]
    if (
        type(checks) is not dict
        or set(checks) != {"ok", "findings"}
        or type(checks["ok"]) is not bool
        or type(checks["findings"]) is not list
        or checks["ok"] != (not checks["findings"])
    ):
        raise ValueError("Candidate checks are inconsistent")
    for finding in checks["findings"]:
        if (
            type(finding) is not dict
            or set(finding) != {"path", "kind", "message"}
            or any(type(finding[key]) is not str for key in finding)
            or not finding["kind"]
            or not finding["message"]
        ):
            raise ValueError("Candidate check finding is invalid")
        if finding["path"]:
            _portable(finding["path"])
    review = receipt["review"]
    if (
        type(review) is not dict
        or set(review) != {"decision", "accepted"}
        or type(review["accepted"]) is not bool
    ):
        raise ValueError("Candidate review state is invalid")
    if review["decision"] is not None:
        _validate_review(review["decision"])
    accepted = (
        review["decision"] is not None
        and review["decision"]["candidate_id"] == receipt["candidate_id"]
    )
    if (
        review["accepted"] != accepted
        or receipt["ready"]
        is not (checks["ok"] and receipt["impact"]["ready"] and accepted)
        or receipt["delivery_ready"] is not False
    ):
        raise ValueError("Candidate readiness exceeds its checked review state")
    if receipt["candidate_id"] != _proposal(receipt):
        raise ValueError("Candidate identity does not bind its proposal")


def review_publication_candidate(
    receipt: Mapping[str, Any], *, reviewer: str, reason: str
) -> dict[str, Any]:
    """Prepare an exact-artifact acceptance record for repository review."""
    validate_publication_receipt(receipt)
    if not receipt["checks"]["ok"] or not receipt["impact"]["complete"]:
        raise ValueError(
            "Repair incomplete evidence and invalid output before candidate review"
        )
    proposal = _sealed(
        {
            "schema_version": REVIEW_SCHEMA,
            "candidate_id": receipt["candidate_id"],
            "decision": "accepted",
            "reviewer": reviewer,
            "reason": reason,
        },
        "review_id",
    )
    _validate_review(proposal)
    return proposal


def _output_path(root, name, config, target, basis, config_path):
    if str(name) == ".":
        raise ValueError(
            "Candidate output must be a separate consumer-relative directory"
        )
    path = _candidate_path(root, name)
    content_root = publication_path(root, config["content"]["root"])
    trees = [] if _same(content_root, root) else [content_root]
    if target is not None:
        trees.append(target)
    if config["architecture"]["baseline"] == "existing-wiki":
        trees.append(publication_path(root, config["architecture"]["root"]))
    for tree in trees:
        if (
            publication_control_overlap(path, tree)
            or _within(path, tree)
            or _within(tree, path)
        ):
            raise ValueError(
                "Candidate output overlaps authored, native or target inputs"
            )
    inputs = {root / source for source in basis["files"]}
    inputs.update(
        root / reference["configuration"]["path"]
        for reference in basis.get("references", {}).values()
        if reference["configuration"]["kind"] == "contract-file"
    )
    inputs.update(publication_input_controls(root, config, config_path))
    for item in inputs:
        if publication_control_overlap(path, item):
            raise ValueError("Candidate output overlaps a declared input")
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError("Candidate output must be absent or empty")
    return path


def _prepare(
    consumer_root,
    *,
    config_path,
    target_dir,
    baseline,
    reviews,
    previous_receipt,
    candidate_review,
    source_revision,
    target_revision,
):
    from .publication_links import check_github_wiki, prepare_wiki_markdown
    from .publication_impact import project_publication_targets

    root = _absolute_path(Path(consumer_root))
    config = load_publication_config(root, config_path=config_path)
    if "content" not in config:
        raise ValueError(
            "Configure an explicit publication content profile before export"
        )
    for revision in (source_revision, target_revision):
        if revision is not None and (
            type(revision) is not str or _REVISION.fullmatch(revision) is None
        ):
            raise ValueError(
                "Source and target revisions must be immutable hexadecimal identifiers"
            )
    if previous_receipt is not None:
        validate_publication_receipt(previous_receipt)
        if not previous_receipt["ready"]:
            raise ValueError(
                "An ownership receipt must have accepted topic and candidate reviews"
            )
        if previous_receipt["basis"]["config"]["target"] != config["target"]:
            raise ValueError("Ownership receipt belongs to a different target")
    if candidate_review is not None:
        _validate_review(candidate_review)
    target = None if target_dir is None else _target_path(root, target_dir)
    if target is not None:
        if any(
            publication_control_overlap(target, control)
            for control in publication_input_controls(root, config, config_path)
        ):
            raise ValueError(
                "Target snapshot includes configuration or source-selection inputs"
            )
        for protected in (config["content"]["root"], config["architecture"]["root"]):
            if protected != "." and _within(publication_path(root, protected), target):
                raise ValueError(
                    "Target snapshot includes source or architecture inputs"
                )
    provider = _provider()
    before = {} if target is None else _read_tree(target, target_snapshot=True)
    basis = capture_publication_basis(
        root, config_path=config_path, target_dir=target_dir, baseline=baseline
    )
    output = dict(before)
    content = config["content"]
    repo_topics = [
        topic for topic in config["topics"] if topic["edit_at"] == "repository"
    ]
    pages = {}
    ownership = {}
    for topic in repo_topics:
        path = topic["wiki_page"]
        if topic.get("anchor") or any(
            other["wiki_page"] == path and other["id"] != topic["id"]
            for other in config["topics"]
        ):
            raise ValueError(
                "Export requires whole-page repository ownership; keep mixed or anchored topics review-only"
            )
        if "/" in path:
            raise ValueError(
                "Generated GitHub wiki pages must have flat Markdown filenames"
            )
        if (
            topic["source_document"] in pages
            and pages[topic["source_document"]] != path
        ):
            raise ValueError("A source document needs one unambiguous wiki destination")
        pages[topic["source_document"]] = path
        ownership[path] = {
            "kind": "page",
            "owner": topic["owner"],
            "source_document": topic["source_document"],
        }
    assets = {
        item["source_document"]: item["wiki_path"] for item in content.get("assets", [])
    }
    if len(assets) != len(content.get("assets", [])):
        raise ValueError("An asset source needs one unambiguous wiki destination")
    for item in content.get("assets", []):
        if item["wiki_path"] in ownership:
            raise ValueError("Asset collides with a generated page")
        ownership[item["wiki_path"]] = {
            "kind": "asset",
            "owner": item["owner"],
            "source_document": item["source_document"],
        }
    if not ownership:
        raise ValueError(
            "Content export needs at least one explicitly owned page or asset"
        )
    with StorageReadSession(root).phase() as session:
        authored = {}
        for path, owner in sorted(ownership.items()):
            source = owner["source_document"]
            raw = session.read(source, MAX_FILE_BYTES)
            if basis["files"].get(source) != sha256_bytes(raw):
                raise ValueError("Authored content changed after evidence capture")
            if owner["kind"] == "page":
                text = raw.decode("utf-8")
                authored[path] = prepare_wiki_markdown(
                    text,
                    source_path=source,
                    source_pages=pages,
                    source_assets=assets,
                    repository_url=content.get("repository_url"),
                    source_revision=source_revision,
                ).encode("utf-8")
            else:
                authored[path] = raw
    old_owned = {} if previous_receipt is None else previous_receipt["ownership"]
    adoptions = {item["path"]: item for item in content.get("adoptions", [])}
    removals = {item["path"]: item for item in content.get("removals", [])}
    if set(old_owned) - set(ownership) - set(removals):
        raise ValueError(
            "Retired owned paths require explicit removals; mappings never imply deletion"
        )
    operations = []
    for path, raw in sorted(authored.items()):
        prior = before.get(path)
        before_hash = None if prior is None else sha256_bytes(prior)
        adoption = adoptions.get(path)
        if adoption is not None and adoption["expected_hash"] != before_hash:
            raise ValueError("Adoption does not match the observed target bytes")
        if path in old_owned:
            assert previous_receipt is not None
            if previous_receipt["files"][path] != before_hash and adoption is None:
                raise ValueError(
                    "Owned target content drifted; review an explicit adoption before replacing it"
                )
        elif prior is not None and adoption is None:
            raise ValueError(
                "Importing an existing manual page or asset requires an explicit before-hash adoption"
            )
        output[path] = raw
        after_hash = sha256_bytes(raw)
        kind = (
            "adopt"
            if adoption is not None
            else "add"
            if prior is None
            else "unchanged"
            if before_hash == after_hash
            else "update"
        )
        operations.append(
            {
                "path": path,
                "kind": kind,
                "before": before_hash,
                "after": after_hash,
                "reason": None if adoption is None else adoption["reason"],
            }
        )
    for path, removal in sorted(removals.items()):
        if path not in old_owned:
            raise ValueError("Unmanaged paths cannot be removed by an export")
        if baseline is None:
            raise ValueError(
                "Owned removals require an accepted impact baseline and explicit retirement review"
            )
        before_hash = None if path not in before else sha256_bytes(before[path])
        if removal["expected_hash"] != before_hash:
            raise ValueError("Removal does not match the observed target bytes")
        output.pop(path, None)
        operations.append(
            {
                "path": path,
                "kind": "remove",
                "before": before_hash,
                "after": None,
                "reason": removal["reason"],
            }
        )
    if set(adoptions) - set(ownership):
        raise ValueError("Adoptions must name a current owned output")
    if (
        len(output) > MAX_FILES
        or any(len(raw) > MAX_FILE_BYTES for raw in output.values())
        or sum(map(len, output.values())) > MAX_TREE_BYTES
    ):
        raise ValueError("Composed candidate exceeds the public file or byte limit")
    checks = check_github_wiki(output)
    projected = project_publication_targets(basis, output, baseline=baseline)
    impact = compare_publication_impact(projected, baseline, reviews=reviews)
    session.recheck()
    if (
        capture_publication_basis(
            root, config_path=config_path, target_dir=target_dir, baseline=baseline
        )
        != basis
    ):
        raise ValueError("Publication evidence changed during rendering")
    if (
        config != load_publication_config(root, config_path=config_path)
        or provider != _provider()
    ):
        raise ValueError(
            "Publication configuration or provider changed during rendering"
        )
    if target is not None and _read_tree(target, target_snapshot=True) != before:
        raise ValueError("Target snapshot changed during rendering")
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "provider": provider,
        "context": {
            "source_revision": source_revision,
            "target_revision": target_revision,
        },
        "config_hash": hash_json(config),
        "inputs": {
            "baseline_id": None if baseline is None else baseline["basis_id"],
            "reviews_hash": None if reviews is None else hash_json(reviews),
            "previous_receipt_id": None
            if previous_receipt is None
            else previous_receipt["receipt_id"],
        },
        "target": {
            "mode": "artifact-only" if target is None else "local-snapshot",
            "files": _hashes(before),
            "tree_hash": hash_json(_hashes(before)),
            "remote_verified": False,
        },
        "basis": projected,
        "impact": impact,
        "ownership": ownership,
        "operations": operations,
        "files": _hashes(output),
        "tree_hash": hash_json(_hashes(output)),
        "checks": checks,
    }
    receipt["candidate_id"] = _proposal(receipt)
    accepted = (
        candidate_review is not None
        and candidate_review["candidate_id"] == receipt["candidate_id"]
    )
    receipt["review"] = {
        "decision": None
        if candidate_review is None
        else deepcopy(dict(candidate_review)),
        "accepted": accepted,
    }
    receipt["ready"] = checks["ok"] and impact["ready"] and accepted
    receipt["delivery_ready"] = False
    receipt = _sealed(receipt, "receipt_id")
    validate_publication_receipt(receipt)
    return root, config, target, output, receipt


def export_publication_candidate(
    consumer_root: str | Path = ".",
    *,
    output_dir: str | Path,
    config_path: str | Path = ".llm-wiki/publication.json",
    target_dir: str | Path | None = None,
    baseline: Mapping[str, Any] | None = None,
    reviews: Mapping[str, Any] | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    candidate_review: Mapping[str, Any] | None = None,
    source_revision: str | None = None,
    target_revision: str | None = None,
) -> dict[str, Any]:
    """Render a fresh local candidate, preserving every unmanaged target file."""
    root, config, target, files, receipt = _prepare(
        consumer_root,
        config_path=config_path,
        target_dir=target_dir,
        baseline=baseline,
        reviews=reviews,
        previous_receipt=previous_receipt,
        candidate_review=candidate_review,
        source_revision=source_revision,
        target_revision=target_revision,
    )
    destination = _output_path(
        root, output_dir, config, target, receipt["basis"], config_path
    )
    if config["architecture"]["baseline"] == "bootstrap-source":
        from .publication_snapshot import assert_bootstrap_output_excluded

        assert_bootstrap_output_excluded(
            publication_path(root, config["architecture"]["root"]), destination, files
        )
    ensure_guarded_directory(destination, mode=0o700)
    for path, raw in sorted(files.items()):
        output = destination / path
        ensure_guarded_directory(output.parent, mode=0o700)
        atomic_write_private_bytes(output, raw, expected_existing=None)
    if _read_tree(destination) != files:
        raise ValueError("Candidate output changed during export")
    _recheck_basis(root, config_path, target_dir, baseline, files, receipt)
    return receipt


def check_publication_candidate(
    consumer_root: str | Path = ".",
    *,
    candidate_dir: str | Path,
    receipt: Mapping[str, Any],
    config_path: str | Path = ".llm-wiki/publication.json",
    target_dir: str | Path | None = None,
    baseline: Mapping[str, Any] | None = None,
    reviews: Mapping[str, Any] | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    candidate_review: Mapping[str, Any] | None = None,
    source_revision: str | None = None,
    target_revision: str | None = None,
) -> dict[str, Any]:
    """Re-render current inputs and verify exact candidate bytes without writing."""
    validate_publication_receipt(receipt)
    source_revision = (
        receipt["context"]["source_revision"]
        if source_revision is None
        else source_revision
    )
    target_revision = (
        receipt["context"]["target_revision"]
        if target_revision is None
        else target_revision
    )
    root, _config, _target, expected, current = _prepare(
        consumer_root,
        config_path=config_path,
        target_dir=target_dir,
        baseline=baseline,
        reviews=reviews,
        previous_receipt=previous_receipt,
        candidate_review=candidate_review,
        source_revision=source_revision,
        target_revision=target_revision,
    )
    if current["candidate_id"] != receipt["candidate_id"]:
        raise ValueError(
            "Candidate inputs, ownership or target base changed; export a fresh candidate"
        )
    path = _candidate_path(root, candidate_dir)
    if _read_tree(path) != expected:
        raise ValueError("Candidate files differ from the checked proposal")
    _recheck_basis(root, config_path, target_dir, baseline, expected, current)
    return current


def _recheck_basis(root, config_path, target_dir, baseline, files, receipt):
    from .publication_impact import project_publication_targets

    current = capture_publication_basis(
        root, config_path=config_path, target_dir=target_dir, baseline=baseline
    )
    if (
        project_publication_targets(current, files, baseline=baseline)["basis_id"]
        != receipt["basis"]["basis_id"]
        or _provider() != receipt["provider"]
    ):
        raise ValueError("Publication evidence changed while checking the candidate")
    target_hashes = (
        {}
        if target_dir is None
        else _hashes(
            _read_tree(publication_path(root, target_dir), target_snapshot=True)
        )
    )
    if target_hashes != receipt["target"]["files"]:
        raise ValueError("Target snapshot changed while checking the candidate")


def validate_candidate_tree(
    consumer_root: str | Path, candidate_dir: str | Path, receipt: Mapping[str, Any]
) -> None:
    """Verify the full artifact inventory before preparing a local review."""
    validate_publication_receipt(receipt)
    root = _absolute_path(Path(consumer_root))
    files = _read_tree(_candidate_path(root, candidate_dir))
    _validate_candidate_files(files, receipt)


def _validate_candidate_files(
    files: Mapping[str, bytes], receipt: Mapping[str, Any]
) -> None:
    """Check public file bytes against a previously validated candidate receipt."""
    if _hashes(files) != receipt["files"]:
        raise ValueError("Candidate files differ from the supplied receipt")
    from .publication_links import check_github_wiki

    if check_github_wiki(files) != receipt["checks"]:
        raise ValueError("Candidate checks differ from its actual public content")
    from .publication_impact import publication_target_observation

    targets = receipt["basis"]["targets"]
    for topic in receipt["basis"]["config"]["topics"]:
        if targets.get(topic["id"]) != publication_target_observation(
            topic, files.get(topic["wiki_page"])
        ):
            raise ValueError("Candidate target observations differ from its content")
    for finding in receipt["impact"]["findings"]:
        if finding["kind"] != "topic":
            continue
        observed = publication_target_observation(
            finding, files.get(finding["wiki_page"])
        )
        if finding["target"] != observed or targets.get(finding["subject"]) != observed:
            raise ValueError("Candidate target observations differ from its content")


def validate_candidate_target(
    consumer_root: str | Path, target_dir: str | Path | None, receipt: Mapping[str, Any]
) -> None:
    """Recheck the original public target before preparing an artifact review."""
    validate_publication_receipt(receipt)
    if receipt["target"]["mode"] == "artifact-only":
        if target_dir is not None:
            raise ValueError("Artifact-only receipts do not bind a local target copy")
        return
    root = _absolute_path(Path(consumer_root))
    target = _target_path(root, target_dir)
    if _hashes(_read_tree(target, target_snapshot=True)) != receipt["target"]["files"]:
        raise ValueError("Original target differs from the supplied receipt")
