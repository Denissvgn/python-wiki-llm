"""Read-only public wiki impact and explicit review record preparation."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys

from ..services.filesystem_guard import (
    atomic_write_private_bytes,
    ensure_guarded_directory,
)
from ..services.knowledge_storage_io import StorageReadSession, _absolute_path
from ..services.knowledge_storage import KnowledgeStorageError
from ..services.publication_config import load_publication_config
from ..services.publication_impact import (
    IMPACT_SCHEMA,
    MAX_JSON_BYTES,
    capture_publication_basis,
    compare_publication_impact,
    read_publication_document,
    render_publication_impact,
    resolve_publication_finding,
)
from ..services.knowledge_evidence import hash_json


def _common(parser, *, child=False):
    parser.add_argument(
        "--config", default=argparse.SUPPRESS if child else ".llm-wiki/publication.json"
    )
    parser.add_argument("--consumer-root", default=argparse.SUPPRESS if child else ".")
    parser.add_argument(
        "--target-dir",
        default=argparse.SUPPRESS if child else None,
        help="Consumer-relative local sibling wiki checkout or pinned copy",
    )
    parser.add_argument(
        "--baseline",
        default=argparse.SUPPRESS if child else None,
        help="Explicit accepted publication basis JSON",
    )


def add_impact_command(docs_sub):
    parser = docs_sub.add_parser(
        "impact", help="Report architecture changes affecting sibling wiki topics"
    )
    _common(parser)
    parser.add_argument(
        "--reviews",
        help="Accepted review ledger supplied under repository review policy",
    )
    parser.add_argument("--output", help="Write machine-readable impact JSON")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    actions = parser.add_subparsers(dest="impact_action")
    snapshot = actions.add_parser(
        "snapshot", help="Capture a publication basis without advancing review state"
    )
    _common(snapshot, child=True)
    snapshot.add_argument("--output", required=True)
    snapshot.add_argument(
        "--replace",
        action="store_true",
        help="Explicitly replace a checkpoint after review",
    )
    resolve = actions.add_parser(
        "resolve", help="Prepare a still-current decision for repository review"
    )
    _common(resolve, child=True)
    resolve.add_argument("--report", required=True)
    resolve.add_argument("--finding", required=True)
    resolve.add_argument(
        "--decision", choices=("still-current", "retired"), required=True
    )
    resolve.add_argument("--reviewer", required=True)
    resolve.add_argument("--reason", required=True)
    resolve.add_argument("--reviews", default=argparse.SUPPRESS)
    resolve.add_argument(
        "--output", required=True, help="Proposed review ledger output"
    )


def _artifact_path(args, value):
    path = Path(value)
    if ".." in path.parts:
        raise ValueError("Evidence paths must not traverse parent directories")
    return _absolute_path(Path(args.consumer_root) / path)


def _same_file(left: Path, right: Path) -> bool:
    return left == right or (left.exists() and right.exists() and left.samefile(right))


def _inside_input_tree(destination: Path, source: Path) -> bool:
    return source in destination.parents or any(
        _same_file(parent, source) for parent in (destination, *destination.parents)
    )


def _declared_files(config):
    for asset in config.get("content", {}).get("assets", []):
        yield asset["source_document"]
    for provider in config.get("reference_providers", {}).values():
        if provider["kind"] == "contract-file":
            yield provider["path"]
    for topic in config["topics"]:
        if topic.get("source_document"):
            yield topic["source_document"]
        for dependency in topic["depends_on"]:
            if "source_file" in dependency:
                yield dependency["source_file"]


def _document_bytes(value):
    content = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    if len(content) > MAX_JSON_BYTES:
        content = (
            json.dumps(
                value,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    if len(content) > MAX_JSON_BYTES:
        raise ValueError(
            f"Publication output exceeds the {MAX_JSON_BYTES}-byte document limit"
        )
    return content


def _write(args, value, *, expected_document=None, input_basis=None):
    if not args.output:
        return
    destination = _artifact_path(args, args.output)
    if destination.suffix != ".json":
        raise ValueError(
            "Machine-readable publication output must use a .json filename"
        )
    root = _absolute_path(Path(args.consumer_root))
    config = load_publication_config(root, config_path=args.config)
    protected = []
    if config["architecture"]["baseline"] == "existing-wiki":
        protected.append(root / config["architecture"]["root"])
    if args.target_dir:
        protected.append(root / args.target_dir)
    for path in protected:
        if _inside_input_tree(destination, path):
            raise ValueError(
                "Publication output cannot overwrite native or sibling wiki inputs"
            )
    for name in ("config", "baseline", "report", "reviews"):
        source = getattr(args, name, None)
        if source and _same_file(destination, _artifact_path(args, source)):
            if (
                name == "reviews"
                and args.impact_action == "resolve"
                and expected_document is not None
            ):
                continue
            raise ValueError(
                "Publication output cannot overwrite configuration, baseline, report or accepted review inputs"
            )
    file_inputs = set(_declared_files(config))
    if input_basis is not None:
        file_inputs.update(input_basis["files"])
        file_inputs.update(
            reference["configuration"]["path"]
            for reference in input_basis.get("references", {}).values()
            if reference["configuration"]["kind"] == "contract-file"
        )
    if any(
        _inside_input_tree(destination, root / source)
        or destination in (root / source).parents
        for source in file_inputs
    ):
        raise ValueError(
            "Publication output cannot overwrite declared source or reference inputs"
        )
    expected = None
    if destination.exists() or destination.is_symlink():
        with StorageReadSession(destination.parent).phase() as session:
            expected = session.read(destination.name, MAX_JSON_BYTES)
        prior = read_publication_document(destination)
        if prior.get("schema_version") != value.get("schema_version"):
            raise ValueError(
                "Output would overwrite a different publication document type"
            )
        if args.impact_action == "snapshot" and not args.replace:
            raise ValueError(
                "Replacing a checkpoint requires snapshot --replace after review"
            )
        if expected_document is not None and prior != expected_document:
            raise ValueError(
                "Review ledger changed; reload it before preparing a decision"
            )
    content = _document_bytes(value)
    ensure_guarded_directory(destination.parent)
    atomic_write_private_bytes(
        destination,
        content,
        expected_existing=expected,
    )


def _error_report(message):
    result = {
        "schema_version": IMPACT_SCHEMA,
        "complete": False,
        "review_required": True,
        "changed": False,
        "ready": False,
        "config_hash": None,
        "enforcement": "required",
        "basis": {"baseline": None, "candidate": None},
        "coverage": {},
        "findings": [
            {
                "id": hash_json(message),
                "kind": "input",
                "subject": "publication inputs",
                "status": "incomplete",
                "reasons": [{"kind": message}],
            }
        ],
        "limitations": [message],
    }
    return {**result, "report_id": hash_json(result)}


def run(args):
    candidate = None
    try:
        baseline = (
            read_publication_document(_artifact_path(args, args.baseline))
            if args.baseline
            else None
        )
        candidate = capture_publication_basis(
            args.consumer_root,
            config_path=args.config,
            target_dir=args.target_dir,
            baseline=baseline,
        )
        action = args.impact_action
        if action == "snapshot":
            _write(args, candidate, input_basis=candidate)
            print(
                json.dumps({"basis_id": candidate["basis_id"], "output": args.output})
            )
            return
        reviews = (
            read_publication_document(_artifact_path(args, args.reviews))
            if args.reviews
            else None
        )
        if action == "resolve":
            report = read_publication_document(_artifact_path(args, args.report))
            proposal = resolve_publication_finding(
                report,
                candidate,
                finding_id=args.finding,
                reviewer=args.reviewer,
                reason=args.reason,
                reviews=reviews,
                decision=args.decision,
            )
            expected = (
                reviews
                if args.reviews
                and _same_file(
                    _artifact_path(args, args.reviews),
                    _artifact_path(args, args.output),
                )
                else None
            )
            _write(args, proposal, expected_document=expected, input_basis=candidate)
            print(
                json.dumps(
                    {
                        "output": args.output,
                        "records": len(proposal["records"]),
                        "acceptance": "submit through repository review policy",
                    }
                )
            )
            return
        report = compare_publication_impact(candidate, baseline, reviews=reviews)
        _write(args, report, input_basis=candidate)
    except (OSError, ValueError, KnowledgeStorageError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.impact_action:
            raise SystemExit(2) from exc
        report = _error_report(str(exc))
        # Even configuration failures produce stdout JSON. A usable explicit
        # report destination is handled by the same guarded writer when possible.
        try:
            _write(args, report, input_basis=candidate)
        except (OSError, ValueError, KnowledgeStorageError):
            pass
    print(
        render_publication_impact(report)
        if args.format == "markdown"
        else json.dumps(report, indent=2, sort_keys=True)
    )
    if not report["complete"]:
        raise SystemExit(2)
    if report["enforcement"] == "required" and not report["ready"]:
        raise SystemExit(1)
