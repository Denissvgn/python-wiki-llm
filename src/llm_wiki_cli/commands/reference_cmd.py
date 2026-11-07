"""Generate or render stable command reference data."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from ..services.filesystem_guard import (
    atomic_write_private_bytes,
    ensure_guarded_directory,
)
from ..services.knowledge_storage_io import StorageReadSession, _absolute_path


def add_commands(subparsers):
    parser = subparsers.add_parser(
        "reference", help="Export deterministic command reference data"
    )
    actions = parser.add_subparsers(dest="reference_action", required=True)
    export = actions.add_parser(
        "cli", help="Export the installed llm-wiki command contract"
    )
    render = actions.add_parser(
        "render", help="Validate and render a saved CLI contract without running it"
    )
    render.add_argument("--input", required=True, help="Versioned CLI contract JSON")
    for action in (export, render):
        action.add_argument("--format", choices=("json", "markdown"), default="json")
        action.add_argument("--output", help="Explicit reference artifact destination")


def run(args):
    from ..services.cli_reference import (
        MAX_CLI_CONTRACT_BYTES,
        get_cli_contract,
        load_cli_contract,
        render_cli_reference,
    )

    try:
        contract = (
            load_cli_contract(args.input)
            if args.reference_action == "render"
            else get_cli_contract()
        )
        if args.format == "json":
            content = (
                json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False)
                + "\n"
            )
            if len(content.encode("utf-8")) > MAX_CLI_CONTRACT_BYTES:
                # A valid near-limit contract must remain readable by the
                # saved renderer and file provider after whitespace expansion.
                content = (
                    json.dumps(
                        contract,
                        sort_keys=True,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
        else:
            content = render_cli_reference(contract)
        if not args.output:
            print(content, end="")
            return
        destination = _absolute_path(Path(args.output))
        if args.reference_action == "render":
            source = _absolute_path(Path(args.input))
            if destination == source or (
                destination.exists() and destination.samefile(source)
            ):
                raise ValueError(
                    "Reference output must differ from the saved input contract"
                )
        expected = None
        if destination.exists() or destination.is_symlink():
            with StorageReadSession(destination.parent).phase() as session:
                expected = session.read(destination.name, 64 * 1024 * 1024)
        ensure_guarded_directory(destination.parent)
        atomic_write_private_bytes(
            destination, content.encode("utf-8"), expected_existing=expected
        )
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
