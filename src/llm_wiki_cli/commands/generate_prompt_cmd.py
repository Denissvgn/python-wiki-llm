from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path
from .extract_cmd import get_inventory, get_call_graph

_DEFAULT_PROMPT_FILE = ".git/llm-wiki-prompt.txt"


def _build_prompt(diff_text: str, wiki_dir: str, src_dir: str) -> str:
    inventory = get_inventory(src_dir, deep=True)
    ast_json = json.dumps(inventory, indent=2)
    call_graph = get_call_graph(inventory)
    graph_json = json.dumps(call_graph, indent=2)

    return f"""\
You are an overarching Wiki synchronizer.
The project's wiki lives at `{wiki_dir}/`.

Here is the AST structure of the Python codebase:
{ast_json}

Here is the cross-module call graph (functions touching 3+ internal modules):
{graph_json}

Here is the Git Diff (most recent commit):
{diff_text}

TASK:
1. Identify all `{wiki_dir}/*` markdown pages that need to be updated.
2. Read them using your file reading capabilities.
3. Update entity and module pages to reflect the changes (e.g. new schemas, new logic, deleted code).
4. If the diff modifies the interaction pattern between 3+ modules (new imports, changed call \
sequences, added/removed pipeline steps), create or update the relevant `{wiki_dir}/workflows/*.md` page.
5. Read existing workflow pages in `{wiki_dir}/workflows/` to check if any existing flows are \
affected by this commit. Update or delete stale workflows.
6. Append an entry to `{wiki_dir}/log.md`.
7. Use `git add {wiki_dir}/` and `git commit -m "docs(wiki): auto-update [bot]"` to save your \
changes if any.
"""


def run(args) -> None:
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    src_dir: str = getattr(args, "src_dir", ".")
    validate_path(wiki_dir, "--wiki-dir")
    validate_path(src_dir, "--src-dir")
    output: str = getattr(args, "output", _DEFAULT_PROMPT_FILE)
    print_only: bool = getattr(args, "print_prompt", False)
    no_diff: bool = getattr(args, "no_diff", False)

    # --- get diff ---
    diff_text = ""
    if not no_diff:
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD~1..HEAD"],
                capture_output=True, text=True, check=True, timeout=30,
            )
            diff_text = result.stdout
        except subprocess.CalledProcessError:
            print("Warning: Could not get git diff (no commits yet?). Continuing without diff.")
        except subprocess.TimeoutExpired:
            print("Warning: git diff timed out. Continuing without diff.")

    prompt = _build_prompt(diff_text, wiki_dir, src_dir)

    if print_only:
        print(prompt)
        return

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt)

    print(f"Wiki sync prompt written to: {out_path}")
    print()
    print("To sync your wiki, paste the contents of that file into your IDE agent chat.")
    print(f"  cat {out_path}")
