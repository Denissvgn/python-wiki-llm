from __future__ import annotations

from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path

_DEFAULT_PROMPT_FILE = ".git/llm-wiki-prompt.txt"


def _build_prompt(wiki_dir: str, src_dir: str) -> str:
    return f"""\
You are a Wiki synchronizer for this project.
The project's wiki lives at `{wiki_dir}/`.

## Context

Run these commands to understand what changed:

```bash
# Changed files — compact inventory of what was modified in the last commit
llm-wiki extract --src-dir {src_dir} --changed --summary

# Full diff of the last commit
git diff HEAD~1..HEAD

# Current wiki health — shows what's already broken vs. what you need to fix
llm-wiki lint --wiki-dir {wiki_dir} --src-dir {src_dir}
```

For full detail (methods, params, docstrings) on a specific file:
```bash
llm-wiki extract --src-dir {src_dir} --paths path/to/file.py
```

## Success Criteria

Your work is done when **all** of the following are true:

1. **`llm-wiki lint` exits 0** — no broken links, no orphan pages, no undocumented \
classes, no stale entities, no missing modules, no broken workflow links, \
no undocumented infrastructure files.
2. **Only affected pages changed** — modify wiki pages that correspond to code \
touched in the diff. Do not edit unrelated pages or reformat existing content.
3. **`{wiki_dir}/log.md` has a new entry** — one concise line describing what changed, \
appended at the bottom.
4. **`CHANGELOG.md` updated** (if applicable) — add an entry under `## [Unreleased]` \
for user-facing changes. Skip for pure refactors, test-only, or doc-only commits. \
*(Not verified by lint.)*

## Verify & Commit

After making your changes, run:

```bash
llm-wiki lint --wiki-dir {wiki_dir} --src-dir {src_dir}
```

If lint reports issues, fix them and re-run until it exits 0. Then commit:

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
    out_path.write_text(prompt, encoding="utf-8")

    print(f"Wiki sync prompt written to: {out_path}")
    print()
    print("Paste the contents into your IDE agent chat to trigger a wiki sync.")
    print(f"  cat {out_path}")
