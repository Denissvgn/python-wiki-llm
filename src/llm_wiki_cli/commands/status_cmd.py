from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..config import (
    DEFAULT_WIKI_DIR,
    IDE_AGENTS,
    get_agent_config_path,
    read_config,
    validate_source_root,
)
from ..services import circuit_breaker
from ..services.knowledge_observability import (
    knowledge_status_payload,
    load_snapshot_knowledge_observability,
)
from ..services.skills import reference_skill_state, skills_install_dir
from ..services.wiki_surface import PageKind, canonical_path, iter_page_kinds


def _count_markdown_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(1 for _ in directory.glob("*.md"))


def _status_label(kind: PageKind, fallback: str) -> str:
    if kind == PageKind.FLOWS:
        return "Flows"
    return fallback


def _count_surface_pages(wiki_path: Path, entry) -> int:
    if entry.requires_page_id:
        if entry.directory is None:
            return 0
        return _count_markdown_files(wiki_path / entry.directory)
    return int((wiki_path / canonical_path(entry.kind)).is_file())


def _architecture_page_count(wiki_path: Path) -> int:
    return sum(
        1
        for kind in (
            PageKind.API_CONTRACTS,
            PageKind.DEPENDENCIES,
            PageKind.LOAD_ORDER,
        )
        if (wiki_path / canonical_path(kind)).is_file()
    )


def _format_counts(counts: object) -> str:
    if not isinstance(counts, dict):
        return "unavailable"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def _print_knowledge_status(
    wiki_path: Path,
    src_dir: str,
    *,
    source_selection: str | Path | None = None,
) -> None:
    observability = load_snapshot_knowledge_observability(
        wiki_path,
        src_dir=src_dir,
        source_selection=source_selection,
    )
    status = knowledge_status_payload(observability.view)
    summary = observability.summary.to_payload()

    print(f"Knowledge:       {status['availability']} (reason: {status['reason']})")
    print(f"  Concepts evaluated: {summary['concepts_evaluated']}")
    print(f"  Evidence issues: {_format_counts(summary['evidence_issue_counts'])}")
    print(f"  Freshness: {status['freshness']}")
    phase_durations = summary["phase_durations_ms"]
    load_ms = (
        phase_durations.get("load")
        if isinstance(phase_durations, Mapping)
        else None
    )
    if load_ms is not None:
        print(f"  Snapshot load: {load_ms} ms")


def run(args) -> None:
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    src_dir = getattr(args, "src_dir", ".")
    allow_external = bool(getattr(args, "allow_external_src", False))
    source_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=allow_external,
    )
    if allow_external:
        src_dir = str(source_root)
    wiki_path = Path(wiki_dir)
    git_dir = Path(".git")

    print("LLM Wiki Status")
    print("=" * 40)

    # Wiki directory
    if wiki_path.exists():
        print(f"Wiki directory:  {wiki_dir} (exists)")
        for entry in iter_page_kinds():
            label = _status_label(entry.kind, entry.label)
            count = _count_surface_pages(wiki_path, entry)
            print(f"  {label + ':':<15}{count}")
        print(f"  {'Architecture pages:':<15}{_architecture_page_count(wiki_path)}")
    else:
        print(f"Wiki directory:  {wiki_dir} (not found)")

    _print_knowledge_status(
        wiki_path,
        src_dir,
        source_selection=getattr(args, "source_selection", None),
    )

    # Agent config
    agent_config = get_agent_config_path(wiki_dir)
    config = read_config(wiki_dir)
    if agent_config.exists():
        agent = config.get("agent", "unknown")
        mode = "IDE" if agent in IDE_AGENTS else "CLI"
        print(f"Agent:           {agent} ({mode})")
        hints = config.get("quality_hints", True)
        print(f"Quality hints:   {'enabled' if hints else 'disabled'}")
        issue_reporting = config.get("issue_reporting", False)
        print(f"Issue reporting: {'enabled' if issue_reporting else 'disabled'}")
    else:
        print("Agent:           not configured (run `llm-wiki init --agent <agent>`)")

    # Reference skill (the constraint block points at it); its home follows
    # the configured agent
    configured_agent = config.get("agent")
    reference_target = skills_install_dir(configured_agent).as_posix()
    skill_state = reference_skill_state(agent=configured_agent)
    if skill_state == "unmodified":
        print("Reference skill: wiki-reference (current)")
    elif skill_state == "modified":
        print(
            "Reference skill: wiki-reference differs from bundled\n"
            "                 Run `llm-wiki upgrade` or `llm-wiki skills "
            f"install --dest {reference_target} --skill wiki-reference --force`; "
            "inspect preserved extra or conflicting entries"
        )
    else:
        print(
            "Reference skill: not installed "
            f"(run `llm-wiki init` or `llm-wiki skills install --dest "
            f"{reference_target} --skill wiki-reference --force`)"
        )

    # Hooks
    hooks_dir = git_dir / "hooks"
    if hooks_dir.exists():
        installed = []
        for hook_name in ["post-commit", "pre-commit", "pre-push"]:
            hook_file = hooks_dir / hook_name
            if hook_file.exists():
                content = hook_file.read_text(encoding="utf-8")
                if "LLM Wiki" in content:
                    installed.append(hook_name)
        if installed:
            print(f"Hooks:           {', '.join(installed)}")
        else:
            print("Hooks:           none installed")
    else:
        print("Hooks:           no .git/hooks directory")

    # Circuit breaker
    if git_dir.exists():
        state = circuit_breaker.load_state(git_dir)
        breaker_state = state.get("state", "closed")
        failures = state.get("consecutive_failures", 0)
        if breaker_state == "open":
            print(f"Circuit breaker: OPEN ({failures} consecutive failures)")
            ttl_seconds = circuit_breaker.breaker_ttl_seconds()
            if ttl_seconds == 0:
                print(
                    "                 Automatic recovery is disabled; run "
                    "`llm-wiki trigger-agent --reset-breaker` to re-enable"
                )
            else:
                print(
                    "                 The next trigger evaluates automatic recovery "
                    f"after {ttl_seconds:g}s; use `--reset-breaker` to recover now"
                )
        elif breaker_state == "half-open":
            print(
                "Circuit breaker: HALF-OPEN "
                f"({failures} consecutive failures; recovery probe lease persisted)"
            )
            ttl_seconds = circuit_breaker.breaker_ttl_seconds()
            if ttl_seconds == 0:
                print(
                    "                 Automatic recovery is disabled; run "
                    "`llm-wiki trigger-agent --reset-breaker` to re-enable"
                )
            else:
                print(
                    "                 The next trigger evaluates the probe lease "
                    f"after {ttl_seconds:g}s; use `--reset-breaker` to recover now"
                )
        else:
            print(f"Circuit breaker: closed ({failures} recent failures)")
    else:
        print("Circuit breaker: no .git directory")
