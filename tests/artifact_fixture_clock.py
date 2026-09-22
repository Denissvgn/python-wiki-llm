"""Run an installed CLI or consumer with a fixed date for parity fixtures.

Bootstrap and sync record their date in the architectural log, whose exact
bytes feed knowledge and packet commitments. Wheel/sdist consumers can run on
different days. Control that fixture input before generation, keeping every
output byte and digest under comparison. Runtime clocks and deadlines stay real.
"""

from datetime import date
import runpy
import sys
from unittest.mock import patch


class FixtureDate(date):
    @classmethod
    def today(cls):
        return cls(2000, 1, 1)


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
        else:
            with patch.object(sys, "argv", sys.argv[1:]):
                runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()
