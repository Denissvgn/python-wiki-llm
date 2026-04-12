from __future__ import annotations

from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path

_DEFAULT_PROMPT_FILE = ".git/llm-wiki-prompt.txt"


def _build_prompt(wiki_dir: str, src_dir: str) -> str:
    return f"""\
You are a Wiki synchronizer for this project.
The project's wiki lives at `{wiki_dir}/`.

## Step 1 — Gather context

Run these commands in the terminal to collect current state:

```bash
# Changed files only — compact inventory of what was modified in the last commit
llm-wiki extract --src-dir {src_dir} --changed --summary

# Full diff of the last commit
git diff HEAD~1..HEAD

# Wiki health check — reports broken links, orphans, undocumented classes
llm-wiki lint --wiki-dir {wiki_dir} --src-dir {src_dir}
```

If you need the full detail (methods, params, docstrings) for a specific file, run:
```bash
llm-wiki extract --src-dir {src_dir} --paths path/to/file.py
```

## Step 2 — Update the wiki

Based on the command output above:

1. Update `{wiki_dir}/entities/<ClassName>.md` for any added, changed, or removed classes.
2. Update `{wiki_dir}/modules/<filename>.md` for any added, changed, or removed modules.
3. If 3+ modules interact differently (new imports, changed call sequences, added/removed \
pipeline steps), update or create `{wiki_dir}/workflows/*.md`.
4. If Dockerfiles or compose files changed, update `{wiki_dir}/infrastructure/*.md`.
5. Append a one-line entry to `{wiki_dir}/log.md`.
6. Update `CHANGELOG.md` under `## [Unreleased]` for user-facing changes only \
(skip pure refactors, test-only, or doc-only commits). Follow Keep a Changelog format.

## Step 3 — Commit

```bash
git add {wiki_dir}/ CHANGELOG.md
git commit -m "docs(wiki): auto-update [bot]"
```
"""


def run(args) -> None:
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    src_dir: str = getattr(args, "src_dir", ".")
    validate_path(wiki_dir, "--wiki-dir")
    validate_path(src_dir, "--src-dir")
    output: str = getattr(args, "output", _DEFAULT_PROMPT_FILE)
    print_only: bool = getattr(args, "print_prompt", False)

    prompt = _build_prompt(wiki_dir, src_dir)

    if print_only:
        print(prompt)
        return

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt)

    print(f"Wiki sync prompt written to: {out_path}")
    print()
    print("Paste the contents into your IDE agent chat to trigger a wiki sync.")
    print(f"  cat {out_path}")
