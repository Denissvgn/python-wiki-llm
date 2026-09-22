"""Calendar-boundary controls for byte-exact installed artifact comparison."""

from datetime import date
from pathlib import Path
import shutil
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import bootstrap_runtime
from tests import artifact_fixture_clock, release_artifact_smoke as smoke


def _dated_fixture(root, monkeypatch, days, *, controlled, changed=False):
    if root.exists():
        shutil.rmtree(root)
    source, wiki = smoke._write_fixture(root)

    def run(arguments, day):
        class WallDate(date):
            @classmethod
            def today(cls):
                return cls.fromisoformat(day)

        with monkeypatch.context() as clock:
            clock.setattr(bootstrap_runtime, "date", WallDate)
            clock.setattr(sync_cmd, "date", WallDate)
            prefix = ["fixture-clock", "-m", "llm_wiki_cli.cli"] if controlled else ["llm-wiki"]
            clock.setattr(sys, "argv", [*prefix, *arguments])
            (artifact_fixture_clock.main if controlled else cli.main)()
            assert bootstrap_runtime.date is WallDate and sync_cmd.date is WallDate

    common = ["--src-dir", str(source), "--wiki-dir", str(wiki)]
    run(["bootstrap", *common, "--skip-workflows", "--skip-flows", "--skip-dependencies"], days[0])
    # Exercise sync's log clock too, including a bootstrap before midnight and
    # a source change after it, as in the native consumer's tutorial replay.
    with (source / "app/service.py").open("a", encoding="utf-8") as stream:
        stream.write('\n\ndef farewell() -> str:\n    """End a conversation."""\n    return "bye"\n')
        if changed:
            stream.write('\n\ndef additional_behavior() -> int:\n    return 1\n')
    run(["sync", *common, "--force"], days[1])
    first = smoke._tree_hash(wiki)
    run(["sync", *common, "--force"], days[1])
    assert smoke._tree_hash(wiki) == first
    packet = root / "packet.json"
    run(["context", *common, "--budget", "2000", "--focus", "all", "--format", "packet",
         "--knowledge-mode", "auto", "--read-only", "--output", str(packet)], days[1])
    log = (wiki / "log.md").read_text(encoding="utf-8")
    assert "### Wiki bootstrap" in log and "### Wiki sync" in log
    return {
        "wiki": {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob("*") if p.is_file()},
        "packet": packet.read_bytes(),
    }


@pytest.mark.parametrize("controlled", [False, True], ids=["wall-clock-control", "fixed-fixture"])
def test_artifact_bytes_across_calendar_boundaries(tmp_path, monkeypatch, controlled):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "consumer"
    before = _dated_fixture(root, monkeypatch, ("2026-09-21", "2026-09-21"), controlled=controlled)
    after = _dated_fixture(root, monkeypatch, ("2026-09-22", "2026-09-22"), controlled=controlled)
    midnight = _dated_fixture(root, monkeypatch, ("2026-09-21", "2026-09-22"), controlled=controlled)
    if controlled:
        assert before == after == midnight
        log = before["wiki"]["log.md"]
        assert b"2026-09" not in log and log.count(b"## 2000-01-01") == 2
        assert _dated_fixture(root, monkeypatch, ("2026-09-22", "2026-09-22"),
                              controlled=True, changed=True) != before
    else:
        # Prove the original failure with actual generated commitments; a date
        # change must not be silently normalized away by the comparison.
        assert before["wiki"]["log.md"] != after["wiki"]["log.md"]
        assert before["packet"] != after["packet"] != midnight["packet"]


@pytest.mark.parametrize("writer", ["cli", "api-script", "api-inline"])
def test_fixture_clock_controls_isolated_cli_and_api_writers(tmp_path, writer):
    source, wiki = smoke._write_fixture(tmp_path)
    if writer == "cli":
        command = smoke._fixture_cli_command(
            sys.executable, "bootstrap", "--src-dir", str(source), "--wiki-dir", str(wiki),
            "--skip-workflows", "--skip-flows", "--skip-dependencies",
        )
    else:
        client = tmp_path / "client.py"
        code = (
            "import sys, __main__\nfrom llm_wiki_cli import api\n"
            "assert sys.flags.isolated and sys.flags.utf8_mode\n"
            "assert sys.argv[1:] == ['prepare', 'space and unicode: café', '--option']\n"
            "assert __name__ == '__main__'\n"
            "assert globals() is vars(__main__)\n"
            "assert 'FixtureDate' not in globals()\n"
            "if sys.argv[0] == '-c':\n    assert '__file__' not in globals()\n"
            "api.bootstrap_wiki('fixture', 'wiki')\n"
        )
        client.write_text(code, encoding="utf-8")
        invocation = ["-c", code] if writer == "api-inline" else [str(client)]
        command = smoke._isolated_utf8_python_command(
            sys.executable, str(Path(artifact_fixture_clock.__file__)), *invocation,
            "prepare", "space and unicode: café", "--option",
        )
    smoke._run(command, cwd=tmp_path)
    assert "## 2000-01-01" in (wiki / "log.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("code,exit_code,message", [
    ("import sys; print('before exit'); sys.exit(7)", 7, "before exit"),
    ("raise RuntimeError('inline failure')", 1, "RuntimeError: inline failure"),
])
def test_fixture_inline_preserves_process_failures(tmp_path, code, exit_code, message):
    command = smoke._isolated_utf8_python_command(
        sys.executable, str(Path(artifact_fixture_clock.__file__)), "-c", code,
    )
    result = smoke._run(command, cwd=tmp_path, expected=exit_code)
    assert message in result.stdout + result.stderr
    if exit_code == 1:
        assert 'File "<string>"' in result.stderr


def test_fixture_inline_restores_caller_state_on_exit(monkeypatch):
    original_main = sys.modules["__main__"]
    original_dates = bootstrap_runtime.date, sync_cmd.date
    arguments = ["fixture-clock", "-c", "raise SystemExit(7)", "remaining"]
    monkeypatch.setattr(sys, "argv", arguments)
    with pytest.raises(SystemExit) as error:
        artifact_fixture_clock.main()
    assert error.value.code == 7
    assert sys.argv is arguments
    assert sys.modules["__main__"] is original_main
    assert (bootstrap_runtime.date, sync_cmd.date) == original_dates


def test_fixture_inline_requires_code(tmp_path):
    command = smoke._isolated_utf8_python_command(
        sys.executable, str(Path(artifact_fixture_clock.__file__)), "-c",
    )
    result = smoke._run(command, cwd=tmp_path, expected=2)
    assert result.stderr.strip() == "fixture clock: -c requires code"


def test_missing_frozen_fixture_clock_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "__file__", str(tmp_path / "release_artifact_smoke.py"))
    with pytest.raises(smoke.SmokeError, match="missing from the frozen harness"):
        smoke._fixture_cli_command(Path(sys.executable), "bootstrap")
