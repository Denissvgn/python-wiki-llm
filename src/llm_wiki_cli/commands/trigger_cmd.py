import subprocess
import os
from pathlib import Path
from . import extract_cmd
from ..services.lockfile import WikiLock, LockAcquisitionError
from ..services import circuit_breaker
import json

GIT_DIR = Path(".git")


def run(args):
    # Handle --reset-breaker early (no lock needed)
    if getattr(args, "reset_breaker", False):
        circuit_breaker.reset_breaker(GIT_DIR)
        print("Circuit breaker reset. Wiki auto-sync is re-enabled.")
        return

    # Agents that are UI-based and don't support headless CLI execution
    UI_ONLY_AGENTS = ["cursor", "copilot", "generic"]

    if args.agent in UI_ONLY_AGENTS:
        print(f"Error: Agent '{args.agent}' is a UI-based assistant for IDEs.")
        print(f"To use background auto-sync, you must specify a CLI-native agent like 'claude' or 'aider'.")
        print(f"Example: llm-wiki trigger-agent --agent claude")
        return

    # --- Fuse: Concurrency Lock ---
    try:
        with WikiLock(GIT_DIR):
            _run_sync(args)
    except LockAcquisitionError:
        print("Another llm-wiki sync is already running. Skipping.")


def _run_sync(args):
    """Core sync logic, executed inside the concurrency lock."""

    # --- Fuse: Circuit Breaker ---
    if circuit_breaker.check_breaker(GIT_DIR):
        print("Circuit breaker is OPEN — wiki auto-sync is disabled after repeated failures.")
        print("To re-enable: llm-wiki trigger-agent --reset-breaker")
        return

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
        return
    except subprocess.CalledProcessError as e:
        print(f"Git diff failed. Are there commits? {e}")
        return

    if not diff_text.strip():
        print("No changes in the last commit. Aborting.")
        return

    # --- Fuse: Diff Size Guard ---
    max_diff = getattr(args, "max_diff_lines", 1000)
    force = getattr(args, "force", False)
    diff_lines = len(diff_text.splitlines())
    if diff_lines > max_diff and not force:
        print(f"Diff too large ({diff_lines} lines > {max_diff} limit). Skipping auto-sync.")
        print("Use --force to override, or increase --max-diff-lines.")
        return

    # 2. Extract context via current AST
    print("Extracting current structure context...")
    from .extract_cmd import get_inventory, get_call_graph
    inventory = get_inventory(".", deep=True)
    ast_json = json.dumps(inventory, indent=2)

    # 2b. Build call graph for workflow awareness
    call_graph = get_call_graph(inventory)
    graph_json = json.dumps(call_graph, indent=2)

    # 3. Create context prompt for the subagent
    prompt = f"""
You are an overarching Wiki synchronizer subagent.
A new commit was just made. 

Here is the AST structure of the python codebase:
{ast_json}

Here is the cross-module call graph (functions touching 3+ internal modules):
{graph_json}

Here is the Git Diff:
{diff_text}

TASK:
1. Identify all `docs/llm_wiki/*` markdown pages that need to be updated.
2. Read them using your file reading capabilities.
3. Update entity and module pages to reflect the changes (e.g. new schemas, new logic, deleted code).
4. If the diff modifies the interaction pattern between 3+ modules (new imports, changed call sequences, added/removed pipeline steps), create or update the relevant `docs/llm_wiki/workflows/*.md` page.
5. Read existing workflow pages in `docs/llm_wiki/workflows/` to check if any existing flows are affected by this commit. Update or delete stale workflows.
6. Append an entry to `docs/llm_wiki/log.md`.
7. Use `git add docs/llm_wiki/` and `git commit -m "docs(wiki): auto-update [bot]"` to save your changes if any.
"""

    # 4. Save the prompt to a temp file
    prompt_file = Path(".git/llm-wiki-prompt.txt")
    with open(prompt_file, "w") as f:
        f.write(prompt)

    # 5. Delegate to Subagent via CLI
    print(f"Delegating to {args.agent} subagent...")
    if args.agent == "claude":
        cmd = ["claude", "-p", "--dangerously-skip-permissions"]
    elif args.agent == "aider":
        cmd = ["aider", "--message-file", str(prompt_file), "--no-auto-commits"]
    elif args.agent == "opencode":
        cmd = ["opencode", "task", "-f", str(prompt_file)]
    else:
        print(f"Unsupported agent {args.agent}")
        return

    timeout = getattr(args, "timeout", 300)

    try:
        print(f"Running command: {' '.join(cmd)}")

        with open(prompt_file, 'r') as f:
            prompt_content = f.read()

        if args.agent == "claude":
            result = subprocess.run(
                cmd, input=prompt_content, capture_output=True, text=True,
                timeout=timeout,
            )
        else:
            with open(os.devnull, 'r') as devnull:
                result = subprocess.run(
                    cmd, stdin=devnull, capture_output=True, text=True,
                    timeout=timeout,
                )

        print("Subagent Result:")
        print(result.stdout)
        if result.stderr:
            print("stderr:", result.stderr)

        # --- Fuse: record success ---
        circuit_breaker.record_success(GIT_DIR)

    except subprocess.TimeoutExpired:
        print(f"Subagent timed out after {timeout}s. Process killed.")
        circuit_breaker.record_failure(GIT_DIR)
    except Exception as e:
        print(f"Error executing agent {args.agent}: {e}")
        circuit_breaker.record_failure(GIT_DIR)
