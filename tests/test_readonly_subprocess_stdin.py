"""Read-only child tools must not inherit a host's protocol input stream."""

import json
import queue
import subprocess
import sys
import threading
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


_STDIO_HOST = r"""
import json
from pathlib import Path
import subprocess
import sys
import threading
from llm_wiki_cli.services import extraction_service, knowledge_envelope

source = Path(sys.argv[1])
corrupt = sys.argv[2] == "inherit"
ready = threading.Event()
def read_host_input():
    ready.set()
    sys.stdin.buffer.read()
reader = threading.Thread(target=read_host_input)
reader.start()
ready.wait()
original_run = subprocess.run
observations = []
def traced_git(command, **kwargs):
    assert command[0] == "git"
    record = {"stdin_timeout": False, "git_timeout": False}
    observations.append(record)
    if corrupt:
        kwargs.pop("stdin", None)
        kwargs.pop("input", None)
    child_input = ({"input": kwargs["input"], "text": True}
                   if "input" in kwargs else {"stdin": kwargs.get("stdin")})
    try:
        original_run(
            [sys.executable, "-I", "-c", "import sys; assert sys.stdin.buffer.read() == b''"],
            **child_input, capture_output=True, check=True, timeout=0.5,
        )
    except subprocess.TimeoutExpired:
        record["stdin_timeout"] = True
        raise
    kwargs["timeout"] = 3
    try:
        return original_run(command, **kwargs)
    except subprocess.TimeoutExpired:
        record["git_timeout"] = True
        raise
subprocess.run = traced_git
try:
    knowledge_envelope.collect_git_repository_evidence(source)
    extraction_service._git_changed_files(str(source))
    print(json.dumps(observations), flush=True)
finally:
    reader.join(timeout=10)
"""


@pytest.mark.parametrize("inherit", [False, True])
def test_git_reads_complete_while_stdio_host_keeps_reading_input(tmp_path, inherit):
    # This also exercises real Git on Windows under an active stdin reader.
    # The deliberate inheritance control must stall without releasing that pipe.
    source = tmp_path / "source"
    source.mkdir()
    # Prevent discovery of a caller repository even with a custom pytest base.
    (source / ".git").write_text("gitdir: absent\n", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-c",
            _STDIO_HOST,
            str(source),
            "inherit" if inherit else "detached",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lines = queue.Queue()
    assert process.stdout is not None
    stdout = process.stdout
    reader = threading.Thread(target=lambda: lines.put(stdout.readline()))
    reader.start()
    try:
        raw = lines.get(timeout=10)
    finally:
        assert process.stdin is not None
        process.stdin.close()
        process.stdin = None
        try:
            _, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            _, stderr = process.communicate(timeout=5)
            raise
        finally:
            reader.join(timeout=5)
    assert process.returncode == 0, stderr.decode("utf-8", errors="replace")
    observations = json.loads(raw)
    assert len(observations) == 2
    assert all(row["stdin_timeout"] is inherit for row in observations)
    assert all(not row["git_timeout"] for row in observations)
