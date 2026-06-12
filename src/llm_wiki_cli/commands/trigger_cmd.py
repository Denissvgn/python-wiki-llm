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
        print("Circuit breaker reset. Wiki auto-sync is re-enabled.")
        return

    if args.agent in IDE_AGENTS:
        print(f"Error: Agent '{args.agent}' is a UI-based assistant for IDEs.")
        print(f"To use background auto-sync, you must specify a CLI-native agent like 'claude' or 'aider'.")
        print(f"Example: llm-wiki trigger-agent --agent claude")
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

    def finish(*, exit_code: int | None, breaker_result: str, duration_start: float = started) -> None:
        record_event(
            "trigger_finish",
            {
                "agent": args.agent,
                "mode": "CLI",
                "duration_ms": int((time.monotonic() - duration_start) * 1000),
                "exit_code": exit_code,
                "breaker_result": breaker_result,
                "wiki_dir": wiki_dir,
            },
        )

    # --- Fuse: Circuit Breaker ---
    if circuit_breaker.check_breaker(GIT_DIR):
        print("Circuit breaker is OPEN — wiki auto-sync is disabled after repeated failures.")
        print("To re-enable: llm-wiki trigger-agent --reset-breaker")
        return

    record_event(
        "trigger_start",
        {"agent": args.agent, "mode": "CLI", "wiki_dir": wiki_dir},
    )
    print("Triggering auto-sync workflow for LLM Wiki...")

    # 1. Get the git diff
    print("Fetching git diff...")
    try:
        git_diff_result = subprocess.run(
            ["git", "diff", "HEAD~1..HEAD"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        diff_text = git_diff_result.stdout
    except subprocess.TimeoutExpired:
        print("Git diff timed out (30s). Aborting.")
        circuit_breaker.record_failure(GIT_DIR)
        finish(exit_code=1, breaker_result="failure")
        return
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Git diff failed. Are there commits? {e}")
        circuit_breaker.record_failure(GIT_DIR)
        finish(exit_code=1, breaker_result="failure")
        return

    if not diff_text.strip():
        print("No changes in the last commit. Aborting.")
        finish(exit_code=0, breaker_result="skipped")
        return

    # --- Fuse: Diff Size Guard ---
    max_diff = getattr(args, "max_diff_lines", 1000)
    force = getattr(args, "force", False)
    diff_lines = len(diff_text.splitlines())
    if diff_lines > max_diff and not force:
        print(f"Diff too large ({diff_lines} lines > {max_diff} limit). Skipping auto-sync.")
        print("Use --force to override, or increase --max-diff-lines.")
        finish(exit_code=0, breaker_result="skipped")
        return

    # 2. Extract context via current AST
    print("Extracting current structure context...")
    from .extract_cmd import get_call_graph, get_inventory_result, print_inventory_failures
    inventory_result = get_inventory_result(".", deep=True)
    if inventory_result.failed:
        print_inventory_failures(inventory_result)
        circuit_breaker.record_failure(GIT_DIR)
        finish(exit_code=1, breaker_result="failure")
        return
    inventory = inventory_result.inventory
    ast_json = json.dumps(inventory, indent=2)

    # 2b. Build call graph for workflow awareness
    call_graph = get_call_graph(inventory)
    graph_json = json.dumps(call_graph, indent=2)

    # 3. Create context prompt for the subagent
    try:
        template = team_prompt_template_default()
    except TeamConfigError as exc:
        print(f"Invalid team config: {exc}")
        circuit_breaker.record_failure(GIT_DIR)
        finish(exit_code=1, breaker_result="failure")
        return
    prompt = _build_prompt(
        wiki_dir,
        ".",
        template=template,
        diff_text=diff_text,
        ast_json=ast_json,
        graph_json=graph_json,
        cli_agent=True,
    )

    max_prompt_bytes = _max_prompt_bytes(args)
    prompt_bytes = len(prompt.encode("utf-8"))
    if prompt_bytes > max_prompt_bytes and not force:
        print(
            f"Prompt too large ({prompt_bytes} bytes > {max_prompt_bytes} limit). "
            "Skipping auto-sync."
        )
        print("Use --force to override, or increase --max-prompt-bytes.")
        finish(exit_code=0, breaker_result="skipped")
        return

    # 4. Save the prompt to a temp file
    prompt_file = Path(".git/llm-wiki-prompt.txt")
    write_private_text(prompt_file, prompt)

    # 5. Delegate to Subagent via CLI
    print(f"Delegating to {args.agent} subagent...")
    if args.agent == "claude":
        cmd = ["claude", "-p"]
    elif args.agent == "aider":
        cmd = ["aider", "--message-file", str(prompt_file), "--no-auto-commits"]
    elif args.agent == "opencode":
        cmd = ["opencode", "task", "-f", str(prompt_file)]
    else:
        print(f"Unsupported agent {args.agent}")
        circuit_breaker.record_failure(GIT_DIR)
        finish(exit_code=1, breaker_result="failure")
        return

    timeout = getattr(args, "timeout", 300)

    try:
        print(f"Running command: {' '.join(cmd)}")

        if args.agent == "claude":
            with open(prompt_file, "r", encoding="utf-8") as prompt_in:
                result = subprocess.run(
                    cmd, stdin=prompt_in,
                    timeout=timeout,
                )
        else:
            with open(os.devnull, "r") as devnull:
                result = subprocess.run(
                    cmd, stdin=devnull,
                    timeout=timeout,
                )

        # --- Fuse: record success / failure based on exit code ---
        if result.returncode != 0:
            print(f"Subagent exited with code {result.returncode}.")
            circuit_breaker.record_failure(GIT_DIR)
            finish(exit_code=result.returncode, breaker_result="failure")
        else:
            circuit_breaker.record_success(GIT_DIR)
            finish(exit_code=0, breaker_result="success")

    except subprocess.TimeoutExpired:
        print(f"Subagent timed out after {timeout}s. Process killed.")
        circuit_breaker.record_failure(GIT_DIR)
        finish(exit_code=124, breaker_result="failure")
    except Exception as e:
        print(f"Error executing agent {args.agent}: {e}")
        circuit_breaker.record_failure(GIT_DIR)
        finish(exit_code=1, breaker_result="failure")


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
