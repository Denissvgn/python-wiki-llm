from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from ..services.documentation_query_builder import (
    validate_live_query_source_selection,
)
from ..services.metrics import record_event, resolve_agent
from ..services.extraction_service import filter_source_diff
from ..services.paths import shell_quote
from ..services.plugins import PluginError, render_prompt_template
from ..services.redaction import redact_credentials
from ..services.secure_file import write_private_text
from ..services.source_selection import resolve_source_selection
from ..services.source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    capture_source_selection_inputs,
)
from ..services.team import TeamConfigError, team_prompt_template_default
from ..services.wiki_git_policy import (
    WikiGitDisposition,
    WikiGitPolicy,
    classify_wiki_git_policy,
)

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


def _git_diff(src_dir: str = ".") -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
            cwd=src_dir,
        )
        return result.stdout
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        OSError,
    ):
        return ""


def _prompt_git_diff(src_dir: str) -> str:
    return _git_diff() if src_dir == "." else _git_diff(src_dir)


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
    added_lines = [
        line
        for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    removed_lines = [
        line
        for line in diff_text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]

    if paths and any(_is_dependency_path(path) for path in paths):
        return "dependency"

    has_tests = any(
        "/test" in path
        or Path(path).name.startswith("test_")
        or Path(path).name.endswith("_test.py")
        for path in paths
    )
    has_fix_terms = any(
        term in lowered
        for term in ("fix", "bug", "error", "exception", "failure", "regression")
    )
    if has_tests and has_fix_terms:
        return "bugfix"

    added_source = "new file mode" in diff_text and any(
        path.endswith(_SOURCE_EXTS) for path in paths
    )
    added_public_symbol = any(
        re.match(
            r"\+\s*(class|def|async def|export function|export class|func)\s+\w+", line
        )
        for line in added_lines
    )
    if added_source or added_public_symbol:
        return "feature"

    renames = "rename from " in diff_text or "rename to " in diff_text
    broad_change = len(paths) >= 5 and abs(
        len(added_lines) - len(removed_lines)
    ) <= max(10, len(paths) * 3)
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


def _rich_prompt_context(
    *,
    diff_text: str,
    ast_json: str | None,
    graph_json: str | None,
    cli_agent: bool,
) -> tuple[str, str]:
    context_parts = []
    if ast_json is not None:
        context_parts.append(f"AST structure of the codebase:\n{ast_json}")
    if graph_json is not None:
        context_parts.append(
            f"Cross-module call graph (functions touching 3+ internal modules):\n{graph_json}"
        )
    if diff_text and cli_agent:
        context_parts.append(f"Git diff:\n{diff_text}")

    rich_context = "\n\n".join(context_parts)
    rich_context_block = f"\n{rich_context}\n" if rich_context else ""
    return rich_context, rich_context_block


def _source_selection_args(source_selection: str | Path | None) -> str:
    if source_selection is None:
        return ""
    return f" --source-selection {shell_quote(str(source_selection))}"


def _external_source_args(allow_external_src: bool) -> str:
    return " --allow-external-src" if allow_external_src else ""


def _diff_recipe(
    source_selection: str | Path | None,
    *,
    src_dir: str = ".",
    allow_external_src: bool = False,
) -> str:
    git_prefix = (
        f"git -C {shell_quote(src_dir)} diff"
        if allow_external_src
        else "git diff"
    )
    if source_selection is None:
        return f"""# Diff size and paths; use targeted diffs for only the affected files
{git_prefix} --stat HEAD~1..HEAD
{git_prefix} HEAD~1..HEAD -- path/to/affected-file"""
    return f"""# The configured source-selection profile is authoritative.
# Never run an unrestricted Git diff; inspect only paths emitted above.
{git_prefix} HEAD~1..HEAD -- path/from-selected-inventory"""


def _diff_guidance(source_selection: str | Path | None) -> str:
    if source_selection is None:
        return "`git diff --stat`, targeted per-file diffs"
    return "targeted diffs for paths emitted by the selected inventory"


def _selected_prompt_diff(
    diff_text: str,
    *,
    src_dir: str,
    wiki_dir: str,
    source_selection: str | Path | None,
    source_snapshot: SourceSnapshot | None = None,
) -> str:
    snapshot = source_snapshot or build_source_snapshot(
        src_dir, source_selection=source_selection
    )
    return filter_source_diff(
        diff_text,
        snapshot.source_selection_policy,
        retained_roots=(Path(wiki_dir).as_posix(),),
        source_snapshot=snapshot,
    )


def _resolved_prompt_selection_and_diff(
    diff_text: str,
    *,
    src_dir: str,
    wiki_dir: str,
    source_selection: str | Path | None,
    source_snapshot: SourceSnapshot | None,
) -> tuple[str | Path | None, str]:
    snapshot = source_snapshot or build_source_snapshot(
        src_dir,
        source_selection=source_selection,
    )
    resolved_selection = snapshot.source_selection_path
    return resolved_selection, _selected_prompt_diff(
        diff_text,
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        source_selection=resolved_selection,
        source_snapshot=snapshot,
    )


def _validated_prompt_snapshot(
    *,
    src_dir: str,
    wiki_dir: str,
    source_selection: str | Path | None,
    source_snapshot: SourceSnapshot | None = None,
) -> SourceSnapshot:
    if source_snapshot is not None:
        snapshot = source_snapshot
    else:
        policy = resolve_source_selection(src_dir, source_selection)
        selection_inputs = capture_source_selection_inputs(
            src_dir,
            source_selection=source_selection,
            selection_policy=policy,
        )
        validate_live_query_source_selection(
            source_root=Path(src_dir).resolve(),
            wiki_root=Path(wiki_dir),
            live_identity=None if policy is None else policy.identity,
            live_selection_inputs=selection_inputs,
            operation="Prompt generation",
        )
        snapshot = build_source_snapshot(
            src_dir,
            source_selection=source_selection,
            selection_policy=policy,
            expected_selection_inputs=selection_inputs,
        )
    validate_live_query_source_selection(
        source_root=snapshot.root,
        wiki_root=Path(wiki_dir),
        live_identity=snapshot.source_selection_identity,
        live_selection_inputs=snapshot.source_selection_inputs,
        operation="Prompt generation",
    )
    return snapshot


def _validated_prompt_selection_and_diff(
    *,
    src_dir: str,
    wiki_dir: str,
    source_selection: str | Path | None,
    source_snapshot: SourceSnapshot | None,
    diff_text: str | None,
) -> tuple[str | Path | None, str]:
    snapshot = _validated_prompt_snapshot(
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        source_selection=source_selection,
        source_snapshot=source_snapshot,
    )
    selected_diff = _prompt_git_diff(src_dir) if diff_text is None else diff_text
    return _resolved_prompt_selection_and_diff(
        selected_diff,
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        source_selection=source_selection,
        source_snapshot=snapshot,
    )


def _template_values(
    *,
    wiki_dir: str,
    src_dir: str,
    change_type: str,
    rich_context: str,
    rich_context_block: str,
    diff_text: str,
    ast_json: str | None,
    graph_json: str | None,
    cli_agent: bool,
    policy: WikiGitPolicy,
    source_selection: str | Path | None,
    allow_external_src: bool,
) -> dict[str, str]:
    included = policy.disposition is WikiGitDisposition.INCLUDED
    return {
        "wiki_dir": wiki_dir,
        "src_dir": src_dir,
        "change_type": change_type,
        "context": rich_context,
        "context_block": rich_context_block,
        "diff": diff_text,
        "ast_json": ast_json or "",
        "graph_json": graph_json or "",
        "cli_agent": "true" if cli_agent else "false",
        "source_selection": str(source_selection or ""),
        "source_selection_args": _source_selection_args(source_selection),
        "external_source_args": _external_source_args(allow_external_src),
        "wiki_git_disposition": policy.disposition.value,
        "wiki_git_reason": policy.reason,
        "wiki_git_handoff_eligible": "true" if included else "false",
        "wiki_git_handoff": (
            "conditional Git handoff" if included else "local-only handoff"
        ),
    }


_DEFAULT_PROMPT_TEMPLATE = """\
You are a Wiki synchronizer{subagent_suffix} for this project.
The project's wiki lives at `{wiki_dir}/`.

## Context
{rich_context_block}

Run these commands serially to update the deterministic wiki skeleton and
understand what changed. In an interactive or capacity-unknown environment,
the supervisor owns this heavy-gate schedule. Do not launch context, full
tests, coverage, builds, browser suites, sync, lint, or CI in parallel, and do
not delegate those gates to subagents unless the supervisor explicitly assigns
one.

```bash
# Start with the compact changed-file inventory
llm-wiki extract --src-dir {quoted_src_dir}{external_source_args}{source_selection_args} --changed --summary

{diff_recipe}

# Update generated pages only after scoping the change
llm-wiki sync --jobs 1 --wiki-dir {quoted_wiki_dir} --src-dir {quoted_src_dir}{external_source_args}{source_selection_args}

# Current wiki health — shows what's already broken vs. what you need to fix
llm-wiki lint --jobs 1 --wiki-dir {quoted_wiki_dir} --src-dir {quoted_src_dir}{external_source_args}{source_selection_args}
```

For full detail (methods, params, docstrings) on a specific file:
```bash
llm-wiki extract --src-dir {quoted_src_dir}{external_source_args}{source_selection_args} --paths path/to/file.py
```

## Semantic Pass

Use the sync output plus {diff_guidance}, and
`extract --changed --summary` to identify pages that were created or updated.
Inspect those affected entity/module pages and enrich any generated skeletons
before you stop. Do not run an unconditional repository-wide context scan for
this incremental workflow.

Replace `_Auto-generated from ..._`, copied-docstring-only descriptions, and
table `—` placeholders where semantic context is knowable from the diff or
source. Semantic content should explain responsibility, role in the system, main
collaborators, important behavior, and usage or constraints.

## Change-Type Focus

Change type: `{change_type}`.
{change_type_guidance}

## Success Criteria

Your work is done when **all** of the following are true:

1. **Final owning sync/re-anchor completed after semantic edits** — the \
canonical Markdown, surface, knowledge, and manifest snapshot was persisted \
before validation.
2. **`llm-wiki lint --strict` exits 0** — no broken links, no orphan pages, no undocumented \
classes, no stale entities, no missing modules, no broken workflow links, \
no undocumented infrastructure files.
3. **Semantic pass complete** — affected entity/module pages contain \
project-specific explanations, not just generated AST/docstring skeletons, \
copied docstrings, `_Auto-generated from ..._`, or knowable `—` placeholders.
4. **Only affected pages changed** — modify wiki pages that correspond to code \
touched in the diff. Do not edit unrelated pages or reformat existing content.
5. **`{wiki_dir}/log.md` has a new entry** — one concise line describing what changed, \
appended at the bottom.
6. **`CHANGELOG.md` updated** (if applicable) — add an entry under `## [Unreleased]` \
for user-facing changes. Skip for pure refactors, test-only, or doc-only commits. \
*(Not verified by lint.)*

## Verify & Handoff

After making your changes, run:

```bash
llm-wiki sync --jobs 1 --wiki-dir {quoted_wiki_dir} --src-dir {quoted_src_dir}{external_source_args}{source_selection_args}
llm-wiki lint --strict --jobs 1 --wiki-dir {quoted_wiki_dir} --src-dir {quoted_src_dir}{external_source_args}{source_selection_args}
```

The final sync preserves supported semantic prose and re-anchors the canonical
Markdown, surface, knowledge, and manifest snapshot. If lint reports issues,
fix them; when a fix changes Markdown, restart at the owning sync before
re-running strict lint. Report expired human section reviews and stale
machine-verification receipts with their existing reasons; do not fabricate
replacements. Follow the repository-policy handoff below.
"""


def _render_default_prompt(
    *,
    wiki_dir: str,
    src_dir: str,
    change_type: str,
    rich_context_block: str,
    cli_agent: bool,
    source_selection: str | Path | None = None,
    allow_external_src: bool = False,
) -> str:
    return _DEFAULT_PROMPT_TEMPLATE.format(
        subagent_suffix=" subagent" if cli_agent else "",
        wiki_dir=wiki_dir,
        quoted_wiki_dir=shell_quote(wiki_dir),
        quoted_src_dir=shell_quote(src_dir),
        source_selection_args=_source_selection_args(source_selection),
        external_source_args=_external_source_args(allow_external_src),
        diff_recipe=_diff_recipe(
            source_selection,
            src_dir=src_dir,
            allow_external_src=allow_external_src,
        ),
        diff_guidance=_diff_guidance(source_selection),
        rich_context_block=rich_context_block,
        change_type=change_type,
        change_type_guidance=_change_type_guidance(change_type),
    )


def _render_repository_handoff(policy: WikiGitPolicy, wiki_dir: str) -> str:
    heading = "## Repository Policy & Handoff"
    disposition = policy.disposition.value
    reason = policy.reason
    shared = (
        f"{heading}\n\n"
        f"Wiki Git disposition: **{disposition}** (`{reason}`). "
        "Applicable user instructions and repository-local rules remain "
        "authoritative. Never force-add the wiki or change ignore/exclude rules "
        "to bypass this disposition."
    )
    if policy.disposition is WikiGitDisposition.INCLUDED:
        quoted_wiki_dir_slash = shell_quote(f"{wiki_dir}/")
        return (
            f"{shared}\n\nImmediately before staging, re-read all applicable "
            "instructions and recheck the wiki path against the current Git "
            "ignore rules:\n\n```bash\n"
            f"git check-ignore --no-index -- {quoted_wiki_dir_slash} "
            f"{shell_quote(f'{wiki_dir}/index.md')}\n"
            "```\n\nExit status 1 means neither probe is ignored and establishes "
            "eligibility, not authorization. Exit status 0 or any other outcome "
            "requires a local-only handoff. Only if that recheck is eligible and "
            "the current repository rules and user instructions explicitly "
            "authorize a separate wiki commit, run:\n\n"
            "```bash\n"
            f"git add -- {quoted_wiki_dir_slash}\n"
            'LLM_WIKI_AUTO_COMMIT=1 git commit -m "docs(wiki): auto-update [bot]"\n'
            "```\n\nOtherwise, finish with a local handoff that lists changed "
            "wiki paths and validation results. Handle any changelog change only "
            "in a separately authorized surrounding workflow."
        )
    detail = (
        "Git marks this wiki as ignored, so it is local-only."
        if policy.disposition is WikiGitDisposition.IGNORED
        else "Git eligibility could not be established, so fail closed with a local-only handoff."
    )
    return (
        f"{shared}\n\n{detail} Continue the owning sync/re-anchor and strict "
        "validation, but do not stage, commit, push, tag, or open a pull request "
        "for the wiki. Report the changed local wiki paths and validation "
        "results. Handle any independently tracked changelog change only in a "
        "separately authorized code-change workflow."
    )


def _render_prompt_body(
    *,
    template: str | None,
    values: dict[str, str],
    wiki_dir: str,
    src_dir: str,
    change_type: str,
    rich_context_block: str,
    cli_agent: bool,
    source_selection: str | Path | None,
    allow_external_src: bool,
) -> str:
    if template:
        return render_prompt_template(template, values)
    return _render_default_prompt(
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        change_type=change_type,
        rich_context_block=rich_context_block,
        cli_agent=cli_agent,
        source_selection=source_selection,
        allow_external_src=allow_external_src,
    )


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
    policy: WikiGitPolicy | None = None,
    source_selection: str | Path | None = None,
    source_snapshot: SourceSnapshot | None = None,
    allow_external_src: bool = False,
) -> str:
    policy = policy or classify_wiki_git_policy(wiki_dir, cwd=Path.cwd())
    resolved_source_selection, diff_text = _validated_prompt_selection_and_diff(
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        source_selection=source_selection,
        source_snapshot=source_snapshot,
        diff_text=diff_text,
    )
    effective_type = resolve_change_type(change_type, diff_text)
    rich_context, rich_context_block = _rich_prompt_context(
        diff_text=diff_text,
        ast_json=ast_json,
        graph_json=graph_json,
        cli_agent=cli_agent,
    )
    values = _template_values(
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        change_type=effective_type,
        rich_context=rich_context,
        rich_context_block=rich_context_block,
        diff_text=diff_text,
        ast_json=ast_json,
        graph_json=graph_json,
        cli_agent=cli_agent,
        policy=policy,
        source_selection=resolved_source_selection,
        allow_external_src=allow_external_src,
    )
    body = _render_prompt_body(
        template=template, values=values,
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        change_type=effective_type,
        rich_context_block=rich_context_block,
        cli_agent=cli_agent,
        source_selection=resolved_source_selection,
        allow_external_src=allow_external_src,
    )
    return body.rstrip() + "\n\n" + _render_repository_handoff(policy, wiki_dir) + "\n"


def _redact_prompt_artifact(prompt: str) -> str:
    redacted, count = redact_credentials(prompt)
    if not count:
        return redacted
    return redacted.rstrip("\n") + f"\n\n[{count} credential-like values redacted]\n"


def run(args) -> None:
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    src_dir: str = getattr(args, "src_dir", ".")
    validate_path(wiki_dir, "--wiki-dir")
    allow_external = bool(getattr(args, "allow_external_src", False))
    source_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=allow_external,
    )
    if allow_external:
        src_dir = str(source_root)
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

    policy = classify_wiki_git_policy(wiki_dir, cwd=Path.cwd())
    source_selection = getattr(args, "source_selection", None)
    source_snapshot = _validated_prompt_snapshot(
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        source_selection=source_selection,
    )
    diff_text = _prompt_git_diff(src_dir)
    source_selection = source_snapshot.source_selection_path
    try:
        prompt = _build_prompt(
            wiki_dir,
            src_dir,
            change_type=change_type,
            template=template,
            diff_text=diff_text,
            policy=policy,
            source_selection=source_selection,
            source_snapshot=source_snapshot,
            allow_external_src=allow_external,
        )
    except PluginError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    prompt = _redact_prompt_artifact(prompt)
    selected_diff = _selected_prompt_diff(
        diff_text,
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        source_selection=source_selection,
        source_snapshot=source_snapshot,
    )
    effective_type = resolve_change_type(change_type, selected_diff)
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
                "wiki_git_disposition": policy.disposition.value,
                "wiki_git_reason": policy.reason,
            },
        )
        return

    out_path = write_private_text(output, prompt)

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
            "wiki_git_disposition": policy.disposition.value,
            "wiki_git_reason": policy.reason,
        },
    )

    print(f"Wiki sync prompt written to: {out_path}")
    print()
    print("Paste the contents into your IDE agent chat to trigger a wiki sync.")
    print(f"  cat {shell_quote(out_path)}")
