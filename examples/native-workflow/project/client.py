"""Explicit consumer actions for a small coding workflow."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from llm_wiki_cli import api
from bridge import WorkflowBridge

NOTE = "The batch cap bounds downstream work; a full permitted batch must retain every item."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "read", "change", "check", "note", "handoff", "resume"))
    parser.add_argument("--no-session", action="store_true")
    args = parser.parse_args()
    request = json.loads(Path("request.json").read_text(encoding="utf-8"))
    bridge = WorkflowBridge(sessions=not args.no_session)
    result = {}
    try:
        if args.command == "prepare":
            api.bootstrap_wiki("src", "wiki")
            result = {"prepared": "wiki"}
        elif args.command == "change":
            path = Path("src/policy.py")
            path.write_text(path.read_text().replace("values[:limit - 1]", "values[:limit]"), encoding="utf-8")
            result = {"changed": "src/policy.py"}
        elif args.command == "check":
            code = 'import sys; sys.path.insert(0, "src"); from client import public_values; assert public_values() == [1, 2, 3]'
            completed = subprocess.run([sys.executable, "-I", "-c", code], check=False, timeout=10)
            result = {"process_exit": completed.returncode, "behavior_matches": completed.returncode == 0}
        elif args.command == "note":
            path = Path("wiki/modules/policy.md")
            text = path.read_text(encoding="utf-8")
            if NOTE not in text:
                text = text.replace("## Description\n", "## Description\n\n" + NOTE + "\n", 1)
                path.write_text(text, encoding="utf-8")
            result = {"authored_note": NOTE, "path": str(path)}
        elif args.command == "resume":
            result = bridge.resume(json.loads(Path("output/handoff.json").read_text(encoding="utf-8")))
        else:
            bridge.start(request)
            context = bridge.before_decision()
            if args.command == "handoff":
                Path("output").mkdir(exist_ok=True)
                Path("output/handoff.json").write_text(json.dumps(bridge.handoff(NOTE), indent=2) + "\n", encoding="utf-8")
                result = {"handoff": "output/handoff.json", "result_id": context.result_id}
            else:
                result = context.to_payload()
    finally:
        bridge.close()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
