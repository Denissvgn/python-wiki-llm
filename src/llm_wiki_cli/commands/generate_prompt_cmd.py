from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services.metrics import record_event, resolve_agent
from ..services.plugins import PluginError, render_prompt_template
from ..services.team import TeamConfigError, team_prompt_template_default

_DEFAULT_PROMPT_FILE = ".git/llm-wiki-prompt.txt"
CHANGE_TYPES = ("auto", "refactor", "feature", "bugfix", "dependency", "generic")

_DEPENDENCY_FILES = {
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "poetry.lock",
    "pdm.lock",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "Gemfile",
    "Gemfile.lock",
}
_SOURCE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")


def _git_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return result.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _changed_paths(diff_text: str) -> list[str]:
    paths: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            path = line[6:]
        elif line.startswith("rename from ") or line.startswith("rename to "):
            path = line.split(" ", 2)[-1]
        else:
            continue
        if path != "/dev/null" and path not in paths:
            paths.append(path)
    return paths


def _is_dependency_path(path: str) -> bool:
    name = Path(path).name
    normalized = path.replace("\\", "/")
    return (
        name in _DEPENDENCY_FILES
        or name.startswith("Dockerfile")
        or "docker-compose" in name
        or name.startswith("compose.")
        or normalized.endswith(".dockerfile")
    )


def detect_change_type(diff_text: str) -> str:
    paths = _changed_paths(diff_text)
    lowered = diff_text.lower()
    added_lines = [line for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed_lines = [line for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---")]

    if paths and any(_is_dependency_path(path) for path in paths):
        return "dependency"

    has_tests = any("/test" in path or Path(path).name.startswith("test_") or Path(path).name.endswith("_test.py") for path in paths)
    has_fix_terms = any(term in lowered for term in ("fix", "bug", "error", "exception", "failure", "regression"))
    if has_tests and has_fix_terms:
        return "bugfix"

    added_source = "new file mode" in diff_text and any(path.endswith(_SOURCE_EXTS) for path in paths)
    added_public_symbol = any(
        re.match(r"\+\s*(class|def|async def|export function|export class|func)\s+\w+", line)
        for line in added_lines
    )
    if added_source or added_public_symbol:
        return "feature"

    renames = "rename from " in diff_text or "rename to " in diff_text
    broad_change = len(paths) >= 5 and abs(len(added_lines) - len(removed_lines)) <= max(10, len(paths) * 3)
    if renames or broad_change:
        return "refactor"

    return "generic"


def _change_type_guidance(change_type: str) -> str:
    guidance = {
        "refactor": (
            "Emphasize moved or renamed entities, updated relationships, and workflow pages whose sequence or module links changed."
        ),
        "feature": (
            "Emphasize new entities, modules, public APIs, routes, and workflows introduced by the change."
        ),
        "bugfix": (
            "Prefer minimal wiki edits that correct stale or inaccurate statements; prioritize accuracy over broad coverage churn."
        ),
        "dependency": (
            "Emphasize infrastructure, runtime compatibility, dependency constraints, and build/deployment notes."
        ),
        "generic": (
            "Keep edits proportional to the diff and update only pages whose documented facts changed."
        ),
    }
    return guidance.get(change_type, guidance["generic"])


def resolve_change_type(change_type: str, diff_text: str) -> str:
    if change_type != "auto":
        return change_type
    return detect_change_type(diff_text)


def _build_prompt(
    wiki_dir: str,
    src_dir: str,
    *,
    change_type: str = "auto",
    template: str | None = None,
    diff_text: str | None = None,
    ast_json: str | None = None,
    graph_json: str | None = None,
    cli_agent: bool = False,
) -> str:
    if diff_text is None:
        diff_text = _git_diff()
    effective_type = resolve_change_type(change_type, diff_text)
    context_parts = []
    if ast_json is not None:
        context_parts.append(f"AST structure of the codebase:\n{ast_json}")
    if graph_json is not None:
        context_parts.append(f"Cross-module call graph (functions touching 3+ internal modules):\n{graph_json}")
    if diff_text and cli_agent:
        context_parts.append(f"Git diff:\n{diff_text}")
    rich_context = "\n\n".join(context_parts)
    rich_context_block = f"\n{rich_context}\n" if rich_context else ""

    if template:
        return render_prompt_template(
            template,
            {
                "wiki_dir": wiki_dir,
                "src_dir": src_dir,
                "change_type": effective_type,
                "context": rich_context,
                "context_block": rich_context_block,
                "diff": diff_text,
                "ast_json": ast_json or "",
                "graph_json": graph_json or "",
                "cli_agent": "true" if cli_agent else "false",
            },
        )

    return f"""\
You are a Wiki synchronizer{' subagent' if cli_agent else ''} for this project.
The project's wiki lives at `{wiki_dir}/`.

## Context
{rich_context_block}

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

## Change-Type Focus

Change type: `{effective_type}`.
{_change_type_guidance(effective_type)}

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
    change_type: str = getattr(args, "change_type", "auto")
    template: str | None = getattr(args, "template", None)
    if template is None:
        try:
            template = team_prompt_template_default()
        except TeamConfigError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(1)

    try:
        prompt = _build_prompt(wiki_dir, src_dir, change_type=change_type, template=template)
    except PluginError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    effective_type = resolve_change_type(change_type, _git_diff())
    agent, mode = resolve_agent(None, wiki_dir)

    if print_only:
        print(prompt)
        record_event(
            "prompt_generated",
            {
                "agent": agent,
                "mode": mode,
                "change_type": effective_type,
                "template": template,
                "wiki_dir": wiki_dir,
                "src_dir": src_dir,
            },
        )
        return

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt, encoding="utf-8")

    record_event(
        "prompt_generated",
        {
            "agent": agent,
            "mode": mode,
            "change_type": effective_type,
            "template": template,
            "wiki_dir": wiki_dir,
            "src_dir": src_dir,
            "output": str(out_path),
        },
    )

    print(f"Wiki sync prompt written to: {out_path}")
    print()
    print("Paste the contents into your IDE agent chat to trigger a wiki sync.")
    print(f"  cat {out_path}")
