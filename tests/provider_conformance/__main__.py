"""Explicit provider-conformance entry point; never performs implicit acquisition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .controls import self_test
from .frontends import Frontends
from .model import Incomplete, read_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchains", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--language", action="append")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        frontends = Frontends(read_json(args.toolchains), args.work)
        if args.self_test:
            result = self_test(frontends, args.language)
        elif args.manifest:
            from .campaign import run

            result = run(args.manifest, frontends, args.output.parent)
        else:
            raise Incomplete("--self-test or --manifest is required")
        code = 0 if result["status"] == "pass" else 1
    except (Incomplete, OSError, ValueError) as error:
        result = {"status": "incomplete", "reason": str(error)}
        code = 2
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(result["status"], file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
