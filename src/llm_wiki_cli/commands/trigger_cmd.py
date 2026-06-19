from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from .generate_prompt_cmd import _build_prompt
from ..services.lockfile import WikiLock, LockAcquisitionError
from ..services import circuit_breaker
from ..services.metrics import record_event
from ..services.secure_file import write_private_text
from ..services.team import TeamConfigError, team_prompt_template_default
from ..config import DEFAULT_WIKI_DIR, IDE_AGENTS, validate_path
import json

GIT_DIR = Path(".git")
DEFAULT_MAX_PROMPT_BYTES = 2_000_000


def run(args):
    # Handle --reset-breaker early (no lock needed)
    if getattr(args, "reset_breaker", False):
        circuit_breaker.reset_breaker(GIT_DIR)
        print("Circuit breaker reset. Manual trigger-agent sync is re-enabled.")
        return

    if args.agent in IDE_AGENTS:
        print(f"Error: Agent '{args.agent}' is a UI-based assistant for IDEs.")
        print(
            "To use trigger-agent, you must specify a CLI-native agent like 'claude' or 'aider'."
        )
        print("Example: llm-wiki trigger-agent --agent claude")
        sys.exit(1)

    # --- Fuse: Concurrency Lock ---
    try:
        with WikiLock(GIT_DIR):
            _run_sync(args)
    except LockAcquisitionError:
        print("Another llm-wiki sync is already running. Skipping.")


def _run_sync(args):
    """Core sync logic, executed inside the concurrency lock."""
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    started = time.monotonic()

    if _is_breaker_open():
        return
    _record_trigger_start(args, wiki_dir)

    diff_text = _fetch_last_commit_diff(args, wiki_dir, started)
    if diff_text is None or _skip_large_diff(args, wiki_dir, started, diff_text):
        return

    prompt = _build_sync_prompt(args, wiki_dir, started, diff_text)
    if prompt is None or _skip_large_prompt(args, wiki_dir, started, prompt):
        return

    prompt_file = _write_prompt_file(prompt)
    _run_agent(args, wiki_dir, started, prompt_file)


def _record_trigger_start(args, wiki_dir) -> None:
    record_event(
        "trigger_start",
        {"agent": args.agent, "mode": "CLI", "wiki_dir": wiki_dir},
    )
    print("Triggering manual sync workflow for LLM Wiki...")


def _record_trigger_finish(
    args,
    wiki_dir,
    started: float,
    *,
    exit_code: int | None,
    breaker_result: str,
) -> None:
    record_event(
        "trigger_finish",
        {
            "agent": args.agent,
            "mode": "CLI",
            "duration_ms": int((time.monotonic() - started) * 1000),
            "exit_code": exit_code,
            "breaker_result": breaker_result,
            "wiki_dir": wiki_dir,
        },
    )


def _record_trigger_failure(args, wiki_dir, started: float, *, exit_code: int) -> None:
    circuit_breaker.record_failure(GIT_DIR)
    _record_trigger_finish(
        args,
        wiki_dir,
        started,
        exit_code=exit_code,
        breaker_result="failure",
    )


def _is_breaker_open() -> bool:
    if not circuit_breaker.check_breaker(GIT_DIR):
        return False
    print(
        "Circuit breaker is OPEN — manual trigger-agent sync is disabled after repeated failures."
    )
    print("To re-enable: llm-wiki trigger-agent --reset-breaker")
    return True


def _fetch_last_commit_diff(args, wiki_dir, started: float) -> str | None:
    print("Fetching git diff...")
    try:
        git_diff_result = subprocess.run(
            ["git", "diff", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("Git diff timed out (30s). Aborting.")
        _record_trigger_failure(args, wiki_dir, started, exit_code=1)
        return None
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Git diff failed. Are there commits? {e}")
        _record_trigger_failure(args, wiki_dir, started, exit_code=1)
        return None

    diff_text = git_diff_result.stdout
    if diff_text.strip():
        return diff_text
    print("No changes in the last commit. Aborting.")
    _record_trigger_finish(
        args, wiki_dir, started, exit_code=0, breaker_result="skipped"
    )
    return None


def _skip_large_diff(args, wiki_dir, started: float, diff_text: str) -> bool:
    max_diff = getattr(args, "max_diff_lines", 1000)
    diff_lines = len(diff_text.splitlines())
    if diff_lines <= max_diff or getattr(args, "force", False):
        return False
    print(
        f"Diff too large ({diff_lines} lines > {max_diff} limit). Skipping trigger-agent sync."
    )
    print("Use --force to override, or increase --max-diff-lines.")
    _record_trigger_finish(
        args, wiki_dir, started, exit_code=0, breaker_result="skipped"
    )
    return True


def _build_sync_prompt(args, wiki_dir, started: float, diff_text: str) -> str | None:
    print("Extracting current structure context...")
    from .extract_cmd import (
        get_call_graph,
        get_inventory_result,
        print_inventory_failures,
    )

    inventory_result = get_inventory_result(".", deep=True)
    if inventory_result.failed:
        print_inventory_failures(inventory_result)
        _record_trigger_failure(args, wiki_dir, started, exit_code=1)
        return None
    inventory = inventory_result.inventory
    ast_json = json.dumps(inventory, indent=2)

    call_graph = get_call_graph(inventory)
    graph_json = json.dumps(call_graph, indent=2)

    try:
        template = team_prompt_template_default()
    except TeamConfigError as exc:
        print(f"Invalid team config: {exc}")
        _record_trigger_failure(args, wiki_dir, started, exit_code=1)
        return None
    return _build_prompt(
        wiki_dir,
        ".",
        template=template,
        diff_text=diff_text,
        ast_json=ast_json,
        graph_json=graph_json,
        cli_agent=True,
    )


def _skip_large_prompt(args, wiki_dir, started: float, prompt: str) -> bool:
    max_prompt_bytes = _max_prompt_bytes(args)
    prompt_bytes = len(prompt.encode("utf-8"))
    if prompt_bytes <= max_prompt_bytes or getattr(args, "force", False):
        return False
    print(
        f"Prompt too large ({prompt_bytes} bytes > {max_prompt_bytes} limit). "
        "Skipping trigger-agent sync."
    )
    print("Use --force to override, or increase --max-prompt-bytes.")
    _record_trigger_finish(
        args, wiki_dir, started, exit_code=0, breaker_result="skipped"
    )
    return True


def _write_prompt_file(prompt: str) -> Path:
    prompt_file = Path(".git/llm-wiki-prompt.txt")
    write_private_text(prompt_file, prompt)
    return prompt_file


def _run_agent(args, wiki_dir, started: float, prompt_file: Path) -> None:
    print(f"Delegating to {args.agent} subagent...")
    cmd = _agent_command(args.agent, prompt_file)
    if cmd is None:
        print(f"Unsupported agent {args.agent}")
        _record_trigger_failure(args, wiki_dir, started, exit_code=1)
        return

    timeout = getattr(args, "timeout", 300)
    try:
        print(f"Running command: {' '.join(cmd)}")
        result = _execute_agent_command(args, cmd, prompt_file, timeout)
    except subprocess.TimeoutExpired:
        print(f"Subagent timed out after {timeout}s. Process killed.")
        _record_trigger_failure(args, wiki_dir, started, exit_code=124)
        return
    except Exception as e:
        print(f"Error executing agent {args.agent}: {e}")
        _record_trigger_failure(args, wiki_dir, started, exit_code=1)
        return

    if result.returncode != 0:
        print(f"Subagent exited with code {result.returncode}.")
        _record_trigger_failure(args, wiki_dir, started, exit_code=result.returncode)
        return
    circuit_breaker.record_success(GIT_DIR)
    _record_trigger_finish(
        args, wiki_dir, started, exit_code=0, breaker_result="success"
    )


def _agent_command(agent: str, prompt_file: Path) -> list[str] | None:
    if agent == "claude":
        return ["claude", "-p"]
    if agent == "aider":
        return ["aider", "--message-file", str(prompt_file), "--no-auto-commits"]
    if agent == "opencode":
        return ["opencode", "task", "-f", str(prompt_file)]
    return None


def _execute_agent_command(args, cmd: list[str], prompt_file: Path, timeout: int):
    if args.agent == "claude":
        with open(prompt_file, "r", encoding="utf-8") as prompt_in:
            return subprocess.run(
                cmd,
                stdin=prompt_in,
                timeout=timeout,
            )
    with open(os.devnull, "r") as devnull:
        return subprocess.run(
            cmd,
            stdin=devnull,
            timeout=timeout,
        )


def _max_prompt_bytes(args) -> int:
    value = getattr(args, "max_prompt_bytes", None)
    if value is not None:
        return int(value)
    env_value = os.environ.get("LLM_WIKI_MAX_PROMPT_BYTES")
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            pass
    return DEFAULT_MAX_PROMPT_BYTES
