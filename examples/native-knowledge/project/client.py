"""A small downstream consumer using only the supported library API."""

import argparse
import json
from pathlib import Path

from llm_wiki_cli import api


TARGET = "llm-wiki://entities/Item"
NOTE = "Currency is explicit; price_cents remains an integer count of minor units."


def inspect_item(*, snapshot: bool) -> dict:
    result = api.inspect_concept(
        TARGET, src_dir="src", wiki_dir="wiki", live=not snapshot
    )
    concept = result["concept"]["concept"]
    freshness = None if concept is None else concept["freshness"]
    if not result["concept"]["found"] or not result["coverage"]["freshness_evaluated"]:
        decision = "Read src/catalog.py or request a live inspection before relying on the wiki."
    elif freshness is not None and freshness["state"] == "current":
        decision = "Use the recorded structure for navigation; read source and prose for the actual decision."
    else:
        decision = "Inspect src/catalog.py and review the Item description before synchronizing."
    return {
        "target": TARGET,
        "read_scope": result["read_scope"],
        "freshness": freshness,
        "coverage": result["coverage"],
        "graph_bounds": result["graph"]["bounds"],
        "section_bounds": result["sections"]["bounds"],
        "decision": decision,
    }


def check_packet(path: Path) -> dict:
    raw = path.read_bytes()
    validation = api.validate_context_packet(raw)
    expected = json.loads(Path("expected-request.json").read_text(encoding="utf-8"))
    if validation.packet.to_payload()["request"] != expected:
        raise SystemExit(
            "Packet request does not match the consumer's expected-request.json."
        )
    reconciliation = api.reconcile_context_packet(raw, src_dir="src", wiki_dir="wiki")
    return {
        "intent_matches": True,
        "offline_validation": validation.to_payload(),
        "live_reconciliation": reconciliation.to_payload(),
        "decision": (
            "Bindings match this read; preserve the packet's concept freshness and bounds."
            if reconciliation.current
            else "Rebuild the handoff before relying on its currentness."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--snapshot", action="store_true")
    commands.add_parser("change")
    commands.add_parser("follow-up")
    packet = commands.add_parser("check-packet")
    packet.add_argument("path", type=Path)
    commands.add_parser("unavailable")
    args = parser.parse_args()
    if args.command == "prepare":
        api.bootstrap_wiki("src", "wiki")
        Path("output").mkdir(exist_ok=True)
        result = {"next": "Inspect Item; no agent configuration is needed."}
    elif args.command == "inspect":
        result = inspect_item(snapshot=args.snapshot)
    elif args.command == "change":
        source = Path("src/catalog.py")
        text = source.read_text(encoding="utf-8")
        if "    currency:" not in text:
            source.write_text(text + '    currency: str = "EUR"\n', encoding="utf-8")
        result = {
            "changed": "src/catalog.py",
            "next": "Inspect drift before synchronizing.",
        }
    elif args.command == "follow-up":
        page = Path("wiki/entities/Item.md")
        text = page.read_text(encoding="utf-8")
        if NOTE not in text:
            text = text.replace(
                "A catalog item priced in whole cents.",
                "A catalog item priced in whole cents.\n\n" + NOTE,
            )
            page.write_text(text, encoding="utf-8")
        result = {"review_target": "src/catalog.py", "authored_note": NOTE}
    elif args.command == "check-packet":
        result = check_packet(args.path)
    else:
        request = json.loads(Path("expected-request.json").read_text(encoding="utf-8"))
        fallback = api.build_qualified_context(
            "src", wiki_dir="missing-wiki", request=request
        )
        result = {
            "knowledge": fallback.to_payload()["response"]["knowledge"],
            "decision": "Use source evidence; native documentation is unavailable in this read.",
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
