"""Local GitHub wiki candidates and exact-artifact review proposals."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import sys

from . import publication_cmd
from ..services.filesystem_guard import (
    atomic_write_private_bytes,
    ensure_guarded_directory,
)
from ..services.knowledge_storage import KnowledgeStorageError
from ..services.knowledge_storage_io import StorageReadSession, _absolute_path
from ..services.publication_config import load_publication_config
from ..services.publication_contracts import validate_publication_basis
from ..services.publication_impact import MAX_JSON_BYTES, read_publication_document
from ..services.source_snapshot import _is_package_marker


def _common(parser):
    parser.add_argument("--consumer-root", default=".")
    parser.add_argument("--config", default=".llm-wiki/publication.json")


def add_commands(docs_sub):
    parser = docs_sub.add_parser(
        "wiki", help="Prepare and check a local GitHub wiki candidate"
    )
    actions = parser.add_subparsers(dest="publication_action", required=True)
    export = actions.add_parser(
        "export", help="Render explicitly owned content without publishing"
    )
    check = actions.add_parser(
        "check", help="Recheck candidate bytes, inputs and review readiness"
    )
    review = actions.add_parser(
        "review", help="Prepare an exact-candidate review proposal"
    )
    for action in (export, check, review):
        _common(action)
        action.add_argument(
            "--receipt",
            required=True,
            help="Candidate receipt JSON; output for export, input otherwise",
        )
    export.add_argument(
        "--output-dir",
        required=True,
        help="New or empty consumer-relative candidate directory",
    )
    check.add_argument("--candidate-dir", required=True)
    check.add_argument("--output", help="Optional separate rechecked receipt JSON")
    review.add_argument("--reviewer", required=True)
    review.add_argument("--reason", required=True)
    review.add_argument(
        "--candidate-dir", required=True, help="Exact candidate tree being reviewed"
    )
    review.add_argument(
        "--output", required=True, help="Proposed candidate approval JSON"
    )
    for action in (export, check):
        action.add_argument(
            "--target-dir", help="Consumer-relative pinned local sibling wiki copy"
        )
        action.add_argument("--baseline", help="Accepted publication basis JSON")
        action.add_argument("--reviews", help="Accepted topic review ledger JSON")
        action.add_argument(
            "--previous-receipt", help="Previously accepted candidate ownership receipt"
        )
        action.add_argument(
            "--candidate-review", help="Accepted exact-candidate review JSON"
        )
        action.add_argument(
            "--source-revision", help="Explicit caller-declared source revision"
        )
        action.add_argument(
            "--target-revision", help="Explicit caller-declared target-copy revision"
        )
        action.add_argument(
            "--require-ready",
            action="store_true",
            help="Exit 1 until local checks and all exact reviews are ready",
        )


def _path(args, value):
    selected = Path(value)
    if ".." in selected.parts:
        raise ValueError(
            "Publication artifact paths must not traverse parent directories"
        )
    return _absolute_path(Path(args.consumer_root).expanduser() / selected)


def _read(args, value):
    return None if value is None else read_publication_document(_path(args, value))


def _basis_files(basis):
    if not isinstance(basis, Mapping):
        return
    yield from basis.get("files", {})
    for reference in basis.get("references", {}).values():
        configuration = reference["configuration"]
        if configuration["kind"] == "contract-file":
            yield configuration["path"]


def _guard_destination(args, value, *, receipt=None, baseline=None):
    destination = _path(args, value)
    if destination.suffix != ".json":
        raise ValueError("Publication metadata output must use a .json filename")
    if any(
        part.casefold() in {".git", ".hg", ".svn"} for part in destination.parts
    ) or _is_package_marker(Path(destination.name.lower())):
        raise ValueError(
            "Publication metadata cannot replace version-control or package inputs"
        )
    root = _absolute_path(Path(args.consumer_root).expanduser())
    if args.publication_action == "review":
        if receipt is None:
            raise ValueError("Candidate review needs its input receipt")
        config = receipt["basis"]["config"]
    else:
        config = load_publication_config(root, config_path=args.config)
    protected = []
    if config["architecture"]["baseline"] == "existing-wiki":
        protected.append(root / config["architecture"]["root"])
    content = config.get("content")
    if content and content["root"] != ".":
        protected.append(root / content["root"])
    for name in ("target_dir", "output_dir", "candidate_dir"):
        selected = getattr(args, name, None)
        if selected:
            protected.append(_path(args, selected))
    if any(publication_cmd._inside_input_tree(destination, path) for path in protected):
        raise ValueError(
            "Publication metadata must stay outside candidate, content, native and target trees"
        )
    controls = [args.config]
    for name in ("baseline", "reviews", "previous_receipt", "candidate_review"):
        selected = getattr(args, name, None)
        if selected:
            controls.append(selected)
    if args.publication_action != "export":
        controls.append(args.receipt)
    if any(
        publication_cmd._same_file(destination, _path(args, source))
        for source in controls
    ):
        raise ValueError(
            "Publication metadata output must differ from accepted and input artifacts"
        )
    files = set(publication_cmd._declared_files(config))
    if content:
        files.update(asset["source_document"] for asset in content.get("assets", []))
    files.update(_basis_files(baseline))
    if receipt is not None:
        files.update(_basis_files(receipt.get("basis")))
    if any(
        publication_cmd._inside_input_tree(destination, root / source)
        or destination in (root / source).parents
        for source in files
    ):
        raise ValueError(
            "Publication metadata cannot occupy source or reference input paths"
        )
    return destination


def _write(args, destination, value):
    expected = None
    if destination.exists() or destination.is_symlink():
        with StorageReadSession(destination.parent).phase() as session:
            expected = session.read(destination.name, MAX_JSON_BYTES)
        prior = read_publication_document(destination)
        if prior.get("schema_version") != value.get("schema_version"):
            raise ValueError("Metadata output would replace a different document type")
    content = publication_cmd._document_bytes(value)
    ensure_guarded_directory(destination.parent)
    atomic_write_private_bytes(destination, content, expected_existing=expected)


def run(args):
    from ..services.publication_candidate import (
        check_publication_candidate,
        export_publication_candidate,
        review_publication_candidate,
        validate_candidate_tree,
        validate_publication_receipt,
    )

    try:
        action = args.publication_action
        if action == "review":
            receipt = _read(args, args.receipt)
            if receipt is None:
                raise ValueError("Candidate review needs its input receipt")
            validate_publication_receipt(receipt)
            destination = _guard_destination(args, args.output, receipt=receipt)
            validate_candidate_tree(args.consumer_root, args.candidate_dir, receipt)
            proposal = review_publication_candidate(
                receipt, reviewer=args.reviewer, reason=args.reason
            )
            _write(args, destination, proposal)
            print(publication_cmd._document_bytes(proposal).decode("utf-8"), end="")
            return
        baseline = _read(args, args.baseline)
        if baseline is not None:
            validate_publication_basis(baseline)
        reviews = _read(args, args.reviews)
        previous_receipt = _read(args, args.previous_receipt)
        candidate_review = _read(args, args.candidate_review)
        receipt = None if action == "export" else _read(args, args.receipt)
        if receipt is not None:
            validate_publication_receipt(receipt)
        output = args.receipt if action == "export" else args.output
        destination = (
            None
            if output is None
            else _guard_destination(args, output, receipt=receipt, baseline=baseline)
        )
        options = {
            "config_path": args.config,
            "target_dir": args.target_dir,
            "baseline": baseline,
            "reviews": reviews,
            "previous_receipt": previous_receipt,
            "candidate_review": candidate_review,
            "source_revision": args.source_revision,
            "target_revision": args.target_revision,
        }
        if action == "export":
            result = export_publication_candidate(
                args.consumer_root, output_dir=args.output_dir, **options
            )
        else:
            if receipt is None:
                raise ValueError("Candidate check needs its input receipt")
            result = check_publication_candidate(
                args.consumer_root,
                candidate_dir=args.candidate_dir,
                receipt=receipt,
                **options,
            )
        if destination is not None:
            # Recheck the complete captured input set before metadata delivery.
            _guard_destination(args, output, receipt=result, baseline=baseline)
            _write(args, destination, result)
        print(publication_cmd._document_bytes(result).decode("utf-8"), end="")
        if not result["checks"]["ok"] or (args.require_ready and not result["ready"]):
            raise SystemExit(1)
    except (OSError, ValueError, KnowledgeStorageError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
