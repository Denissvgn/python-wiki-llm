"""Generate or render versioned CLI and behavior reference data."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from llm_wiki_engine.filesystem_guard import (
    atomic_write_private_bytes,
    ensure_guarded_directory,
)
from ..services.knowledge_storage_io import StorageReadSession, _absolute_path


def _reference(args):
    if args.reference_action == "behavior":
        from ..services.behavior_reference import (
            MAX_BEHAVIOR_FACTS_BYTES,
            get_behavior_facts,
            load_behavior_facts,
            render_behavior_reference,
        )

        contract = (
            get_behavior_facts()
            if args.input is None
            else load_behavior_facts(args.input)
        )
        return contract, render_behavior_reference, MAX_BEHAVIOR_FACTS_BYTES

    from ..services.cli_reference import (
        MAX_CLI_CONTRACT_BYTES,
        get_cli_contract,
        load_cli_contract,
        render_cli_reference,
    )

    contract = (
        load_cli_contract(args.input)
        if args.reference_action == "render"
        else get_cli_contract()
    )
    return contract, render_cli_reference, MAX_CLI_CONTRACT_BYTES


def run(args):
    try:
        contract, render, maximum = _reference(args)
        if args.format == "json":
            content = (
                json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False)
                + "\n"
            )
            if len(content.encode("utf-8")) > maximum:
                # A valid near-limit contract must remain readable by the
                # saved renderer and file provider after whitespace expansion.
                content = json.dumps(
                    contract, sort_keys=True, ensure_ascii=False, separators=(",", ":")
                )
                if len(content.encode("utf-8")) < maximum:
                    content += "\n"
        else:
            content = render(contract)
        if not args.output:
            print(content, end="")
            return
        destination = _absolute_path(Path(args.output))
        if getattr(args, "input", None) is not None:
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
