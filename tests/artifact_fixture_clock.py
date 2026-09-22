"""Run an installed CLI or consumer with a fixed date for parity fixtures.

Bootstrap and sync record their date in the architectural log, whose exact
bytes feed knowledge and packet commitments. Wheel/sdist consumers can run on
different days. Control that fixture input before generation, keeping every
output byte and digest under comparison. Runtime clocks and deadlines stay real.
"""

from datetime import date
import runpy
import sys
from types import ModuleType
from unittest.mock import patch


class FixtureDate(date):
    @classmethod
    def today(cls):
        return cls(2000, 1, 1)


def _run_inline(code, arguments):
    # Match Python -c's argv and separate __main__ namespace. In particular,
    # imports of __main__ must see the executed code, not this clock helper.
    module = ModuleType("__main__")
    original = sys.modules["__main__"]
    try:
        sys.modules["__main__"] = module
        with patch.object(sys, "argv", ["-c", *arguments]):
            exec(compile(code, "<string>", "exec"), vars(module))
    finally:
        sys.modules["__main__"] = original


def main():
    # Imports still resolve from the consumer interpreter's installed package.
    # This helper is invoked with -I, outside the candidate source tree.
    from llm_wiki_cli.commands import sync_cmd
    from llm_wiki_cli.services import bootstrap_runtime

    with patch.object(bootstrap_runtime, "date", FixtureDate), patch.object(
        sync_cmd, "date", FixtureDate
    ):
        if sys.argv[1:3] == ["-m", "llm_wiki_cli.cli"]:
            from llm_wiki_cli import cli

            with patch.object(sys, "argv", sys.argv[2:]):
                cli.main()
        elif sys.argv[1:2] == ["-c"]:
            if len(sys.argv) < 3:
                print("fixture clock: -c requires code", file=sys.stderr)
                raise SystemExit(2)
            _run_inline(sys.argv[2], sys.argv[3:])
        else:
            with patch.object(sys, "argv", sys.argv[1:]):
                runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()
