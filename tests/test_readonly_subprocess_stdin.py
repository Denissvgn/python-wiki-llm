"""Read-only child tools must not inherit a host's protocol input stream."""

import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from typing import Any, cast

import pytest

from llm_wiki_cli.commands import generate_prompt_cmd, review_cmd, trigger_cmd
from llm_wiki_cli.extractors.go_extractor import GoExtractor
from llm_wiki_cli.extractors.haskell_extractor import HaskellExtractor
from llm_wiki_cli.extractors.rust_extractor import RustExtractor
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services import (
    change_selection,
    extraction_service,
    extractor_helpers,
    knowledge_envelope,
    wiki_git_policy,
)


def _exercise_probe(name, root):
    if name == "changed-files":
        extraction_service._git_changed_files(str(root))
    elif name == "filtered-diff":
        snapshot = cast(
            Any, SimpleNamespace(root=root, source_selection_policy=object())
        )
        extraction_service.filter_source_diff(
            "no patch blocks\n", None, source_snapshot=snapshot
        )
    elif name == "repository-evidence":
        knowledge_envelope._run_git_result(root, "rev-parse", "--is-inside-work-tree")
    elif name == "line-ending-config":
        knowledge_envelope._run_effective_git_config(root, "core.autocrlf")
    elif name == "change-selection":
        change_selection._git(root, "rev-parse", "HEAD")
    elif name == "wiki-policy":
        wiki_git_policy._run_git(root, "rev-parse", "--show-toplevel", timeout=15)
    elif name == "tool-version":
        extractor_helpers.command_output(["node", "--version"], cwd=root)
    elif name == "go-version":
        extractor_helpers._go_version("go")
    elif name == "ghc-version":
        extractor_helpers._ghc_version("ghc")
    elif name == "typescript":
        TypeScriptExtractor()._run_node_extractor(["node", "extract.js"], root)
    elif name in {"go", "rust", "haskell"}:
        extractor = {
            "go": GoExtractor,
            "rust": RustExtractor,
            "haskell": HaskellExtractor,
        }[name]()
        extractor._run_helper([f"{name}-helper"], root / "helper")
    elif name == "review-diff":
        review_cmd._read_patch(SimpleNamespace(), src_dir=str(root))
    elif name == "prompt-diff":
        generate_prompt_cmd._git_diff(str(root))
    elif name == "trigger-diff":
        trigger_cmd._fetch_last_commit_diff(None, root, str(root), 0)
    else:
        raise AssertionError(name)


@pytest.mark.parametrize(
    "name",
    [
        "changed-files",
        "filtered-diff",
        "repository-evidence",
        "line-ending-config",
        "change-selection",
        "wiki-policy",
        "tool-version",
        "go-version",
        "ghc-version",
        "typescript",
        "go",
        "rust",
        "haskell",
        "review-diff",
        "prompt-diff",
        "trigger-diff",
    ],
)
def test_readonly_children_receive_eof_instead_of_host_messages(
    tmp_path, monkeypatch, name
):
    original_run = subprocess.run
    host_input = tmp_path / "host-input"
    protocol = b'{"jsonrpc":"2.0","method":"tools/call","id":7}\n'
    host_input.write_bytes(protocol)
    calls = []
    with host_input.open("rb") as stream:

        def probe_child(command, **kwargs):
            calls.append(command)
            # Give inherited stdin a known host stream, without changing pytest's
            # own descriptor. A real child proves what the caller supplied.
            child_input = {}
            if "input" in kwargs:
                value = kwargs["input"]
                child_input["input"] = (
                    value.encode("utf-8") if isinstance(value, str) else value
                )
            else:
                child_input["stdin"] = kwargs.get("stdin") or stream
            observed = original_run(
                [
                    sys.executable,
                    "-I",
                    "-c",
                    "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())",
                ],
                **child_input,
                capture_output=True,
                check=True,
                timeout=5,
            )
            assert observed.stdout == b"", (
                f"{name} inherited host protocol bytes: {observed.stdout!r}"
            )
            stdout = str(tmp_path) if "rev-parse" in command else "M\0app.py\0"
            return subprocess.CompletedProcess(command, 0, stdout, "")

        monkeypatch.setattr(subprocess, "run", probe_child)
        _exercise_probe(name, tmp_path)
        assert calls
        assert stream.read() == protocol
    if name == "changed-files":
        assert len(calls) == 2


def test_explicit_agent_prompt_stdin_is_preserved(tmp_path, monkeypatch):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Caller-approved agent prompt.\n", encoding="utf-8")
    captured = []

    def run(command, **kwargs):
        captured.append(kwargs["stdin"].read())
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)
    trigger_cmd._execute_agent_command(
        SimpleNamespace(agent="claude"), ["claude", "-p"], prompt, 5
    )
    assert captured == [prompt.read_text(encoding="utf-8")]


# Independent budgets: interpreter/import startup is not an EOF observation.
_STARTUP_TIMEOUT = 15
_EOF_TIMEOUT = 5
_EXIT_TIMEOUT = 5
_GIT_TIMEOUT = 15
_CLEANUP_TIMEOUT = 10
_HOST_TIMEOUT = _STARTUP_TIMEOUT + 2 * (
    _STARTUP_TIMEOUT + _EOF_TIMEOUT + _EXIT_TIMEOUT + _GIT_TIMEOUT + _CLEANUP_TIMEOUT
) + _CLEANUP_TIMEOUT

_STDIO_HOST = r"""
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from llm_wiki_cli.services import extraction_service, knowledge_envelope

source = Path(sys.argv[1])
options = json.loads(sys.argv[2])
corrupt = options["inherit"]
ready = threading.Event()
def read_host_input():
    ready.set()
    sys.stdin.buffer.read()
reader = threading.Thread(target=read_host_input)
reader.start()
ready.wait()
original_run = subprocess.run
observations = []

# Files provide an out-of-band acknowledgement without sharing the stdin under
# examination or racing communicate() against a second stdout reader.
probe_script = r'''
import json
from pathlib import Path
import sys
import time
root = Path(sys.argv[1])
options = json.loads(sys.argv[2])
time.sleep(options["startup_delay"])
if options["probe_mode"] == "never-ready":
    time.sleep(60)
    raise SystemExit(0)
def acknowledge(name, value):
    temporary = root / (name + ".tmp")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    temporary.replace(root / name)
acknowledge("ready", {"phase": "ready"})
if options["probe_mode"] == "exit-before-eof":
    raise SystemExit(0)
data = sys.stdin.buffer.read()
acknowledge("eof", {"bytes_read": len(data)})
if options["probe_mode"] == "hold-after-eof":
    time.sleep(60)
'''

def check_stdin(kwargs, record):
    markers = source.parent / ("probe-" + str(len(observations)))
    markers.mkdir()
    child_input = kwargs.get("stdin")
    if kwargs.get("input") is not None:
        assert kwargs["input"] in ("", b""), "read-only Git input must be empty"
        child_input = subprocess.PIPE
    record["stdin_mode"] = ("separate-pipe" if child_input == subprocess.PIPE else
                            "devnull" if child_input == subprocess.DEVNULL else
                            "inherited" if child_input is None else "explicit")
    record["probe_status"] = "starting"
    started = time.monotonic()
    probe = subprocess.Popen(
        [sys.executable, "-I", "-c", probe_script, str(markers), json.dumps(options)],
        stdin=child_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    record["probe_pid"] = probe.pid
    record["spawn_seconds"] = time.monotonic() - started
    def wait_for(name, timeout):
        began = time.monotonic()
        try:
            while not (markers / name).is_file():
                if probe.poll() is not None:
                    # The acknowledgement can be published between the first
                    # path check and observing process exit.
                    if (markers / name).is_file():
                        break
                    record["probe_status"] = name + "-exit"
                    raise OSError("probe exited before " + name)
                if time.monotonic() - began >= timeout:
                    if (markers / name).is_file():
                        break
                    record["probe_status"] = name + "-timeout"
                    raise subprocess.TimeoutExpired(probe.args, timeout)
                time.sleep(0.01)
            return json.loads((markers / name).read_text(encoding="utf-8"))
        finally:
            record[name + "_seconds"] = time.monotonic() - began
    try:
        # This is how communicate(input="") supplies EOF: close only the
        # child's newly created pipe. An inherited host pipe stays open.
        if probe.stdin is not None:
            probe.stdin.close()
            probe.stdin = None
        assert wait_for("ready", options["startup_timeout"]) == {"phase": "ready"}
        record["probe_ready"] = True
        record["bytes_read"] = wait_for("eof", options["eof_timeout"])["bytes_read"]
        record["eof_observed"] = True
        began = time.monotonic()
        try:
            probe.wait(timeout=options["exit_timeout"])
        except subprocess.TimeoutExpired:
            record["probe_status"] = "exit-timeout"
            raise
        finally:
            record["exit_seconds"] = time.monotonic() - began
        if probe.returncode != 0 or record["bytes_read"] != 0:
            record["probe_status"] = "invalid-eof"
            raise OSError("probe did not finish with empty input")
        record["probe_status"] = "completed"
    finally:
        if probe.poll() is None:
            probe.kill()
        stdout, stderr = probe.communicate(timeout=options["cleanup_timeout"])
        record["probe_returncode"] = probe.returncode
        record["probe_stdout"] = stdout.decode("utf-8", errors="replace")
        record["probe_stderr"] = stderr.decode("utf-8", errors="replace")
        record["probe_reaped"] = probe.returncode is not None

def traced_git(command, **kwargs):
    assert command[0] == "git"
    record = {"command": command, "probe_ready": False, "eof_observed": False,
              "probe_reaped": False, "git_status": "not-run"}
    observations.append(record)
    if corrupt:
        kwargs.pop("stdin", None)
        kwargs.pop("input", None)
    check_stdin(kwargs, record)
    assert kwargs["timeout"] <= options["git_timeout"]
    began = time.monotonic()
    try:
        result = original_run(command, **kwargs)
    except subprocess.TimeoutExpired:
        record["git_status"] = "timeout"
        raise
    except subprocess.CalledProcessError as error:
        record["git_status"] = "completed"
        record["git_returncode"] = error.returncode
        raise
    else:
        record["git_status"] = "completed"
        record["git_returncode"] = result.returncode
        return result
    finally:
        record["git_seconds"] = time.monotonic() - began
subprocess.run = traced_git
try:
    knowledge_envelope.collect_git_repository_evidence(source)
    extraction_service._git_changed_files(str(source))
finally:
    print(json.dumps(observations), flush=True)
    reader.join(timeout=options["cleanup_timeout"])
"""


def _run_stdio_host(
    tmp_path, *, inherit, startup_delay=0, probe_mode="normal", expected_host_exit=0, **budgets
):
    source = tmp_path / "source"
    source.mkdir()
    # Prevent discovery of a caller repository even with a custom pytest base.
    (source / ".git").write_text("gitdir: absent\n", encoding="utf-8")
    options = {
        "inherit": inherit, "startup_delay": startup_delay, "probe_mode": probe_mode,
        "startup_timeout": _STARTUP_TIMEOUT, "eof_timeout": _EOF_TIMEOUT,
        "exit_timeout": _EXIT_TIMEOUT, "git_timeout": _GIT_TIMEOUT,
        "cleanup_timeout": _CLEANUP_TIMEOUT, **budgets,
    }
    started = time.monotonic()
    with tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            [sys.executable, "-I", "-c", _STDIO_HOST, str(source), json.dumps(options)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr_file,
        )
        lines = queue.Queue()
        assert process.stdout is not None
        stdout = process.stdout
        # One reader owns stdout throughout, including failure cleanup.
        reader = threading.Thread(target=lambda: lines.put(stdout.readline()), daemon=True)
        reader.start()
        raw = b""
        host_timeout = shutdown_timeout = False
        try:
            raw = lines.get(timeout=_HOST_TIMEOUT)
        except queue.Empty:
            host_timeout = True
        finally:
            assert process.stdin is not None
            process.stdin.close()
            process.stdin = None
            try:
                process.wait(timeout=_CLEANUP_TIMEOUT)
            except subprocess.TimeoutExpired:
                shutdown_timeout = True
                process.kill()
                process.wait(timeout=_CLEANUP_TIMEOUT)
            finally:
                reader.join(timeout=_CLEANUP_TIMEOUT)
            if host_timeout and not lines.empty():
                raw = lines.get_nowait()
            if not reader.is_alive():
                stdout.close()
        stderr_file.seek(0)
        stderr = stderr_file.read()
    diagnostics = json.dumps({
        "options": options, "elapsed_seconds": time.monotonic() - started,
        "host_returncode": process.returncode, "host_timeout": host_timeout,
        "shutdown_timeout": shutdown_timeout,
        "stdout": raw.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
    }, indent=2)
    assert (not host_timeout and not shutdown_timeout
            and process.returncode == expected_host_exit and not reader.is_alive()), diagnostics
    try:
        observations = json.loads(raw)
    except ValueError:
        pytest.fail(diagnostics)
    assert len(observations) == 2, diagnostics
    assert all(row["probe_reaped"] for row in observations), diagnostics
    return observations, diagnostics


def _assert_stdin_observations(observations, diagnostics, *, inherit):
    assert all(row["probe_ready"] for row in observations), diagnostics
    assert all(row["probe_status"] == ("eof-timeout" if inherit else "completed")
               for row in observations), diagnostics
    assert all(row["eof_observed"] is not inherit for row in observations), diagnostics
    assert all(row["git_status"] == ("not-run" if inherit else "completed")
               for row in observations), diagnostics
    if not inherit:
        assert all(row["bytes_read"] == 0 and row["probe_returncode"] == 0
                   for row in observations), diagnostics


@pytest.mark.parametrize("inherit", [False, True])
@pytest.mark.parametrize("startup_delay", [0, 0.75], ids=["normal-start", "delayed-start"])
def test_git_reads_complete_while_stdio_host_keeps_reading_input(tmp_path, inherit, startup_delay):
    # The delayed case exceeds the former 500 ms completion deadline. Startup
    # must succeed independently before an EOF timeout can be a negative control.
    observations, diagnostics = _run_stdio_host(tmp_path, inherit=inherit, startup_delay=startup_delay)
    _assert_stdin_observations(observations, diagnostics, inherit=inherit)


@pytest.mark.parametrize("mode,budgets,status,ready,eof,host_exit", [
    ("never-ready", {"startup_timeout": 0.2}, "ready-timeout", False, False, 0),
    ("exit-before-eof", {}, "eof-exit", True, False, 1),
    ("hold-after-eof", {"exit_timeout": 0.2}, "exit-timeout", True, True, 0),
])
def test_probe_startup_and_exit_failures_cannot_pass_as_inherited_stdin(
    tmp_path, mode, budgets, status, ready, eof, host_exit
):
    # The early-exit fault raises OSError, which the changed-files service
    # deliberately does not catch. Preserve that host failure and its trace.
    observations, diagnostics = _run_stdio_host(
        tmp_path, inherit=False, probe_mode=mode, expected_host_exit=host_exit, **budgets
    )
    assert all(row["probe_status"] == status and row["probe_ready"] is ready
               and row["eof_observed"] is eof and row["git_status"] == "not-run"
               for row in observations), diagnostics
    with pytest.raises(AssertionError):
        _assert_stdin_observations(observations, diagnostics, inherit=True)
