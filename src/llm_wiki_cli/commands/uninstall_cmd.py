import shutil
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services.ci_installer import (
    MANAGED_WORKFLOW_PATH,
    is_unmodified_managed_workflow,
)
from ..services.io import first_unsafe_path_component, read_md, write_md
from ..services.schema import (
    ALL_SCHEMA_FILES as AGENT_SCHEMA_FILES,
    CONSTRAINT_END as CONSTRAINT_END,
    CONSTRAINT_START,
    strip_wiki_block as _strip_wiki_block,
)
from ..services.skills import (
    KNOWN_INSTALL_TARGETS,
    REFERENCE_SKILL_ID,
    reference_skill_state,
)

# Hook identifier — all llm-wiki hooks contain this string
HOOK_SIGNATURE = "LLM Wiki"

# Hooks that install-hook may have written
HOOK_NAMES = ["post-commit", "pre-commit", "pre-push"]

# Local runtime artifacts created by init/hooks/trigger-agent.
RUNTIME_ARTIFACTS = [
    ".git/.llm-wiki-agent",
    ".git/llm-wiki-prompt.txt",
    ".git/llm-wiki.lock",
    ".git/llm-wiki-breaker.json",
    ".git/llm-wiki-sync.log",
]


def _confirm(prompt: str) -> bool:
    """Ask for y/n confirmation."""
    try:
        answer = input(f"  {prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("y", "yes")


def _remove_hooks(dry_run: bool = False) -> int:
    """Remove llm-wiki hooks, but only if they contain our signature."""
    hooks_dir = Path(".git/hooks")
    removed = 0

    if not hooks_dir.exists():
        return 0

    for name in HOOK_NAMES:
        hook_path = hooks_dir / name
        if not hook_path.exists():
            continue

        content = hook_path.read_text(encoding="utf-8")
        if HOOK_SIGNATURE not in content:
            print(f"  SKIP hook {name} (not ours — contains custom user content)")
            continue

        if dry_run:
            print(f"  WOULD REMOVE hook: {hook_path}")
        else:
            hook_path.unlink()
            print(f"  REMOVED hook: {hook_path}")
        removed += 1

    return removed


def _clean_agent_schemas(dry_run: bool = False) -> int:
    """Remove the LLM Wiki constraint block from agent schema files.

    If the file becomes empty after block removal, delete it entirely.
    If user content remains, preserve it.
    """
    cleaned = 0

    for filename in AGENT_SCHEMA_FILES:
        schema_path = Path(filename)
        if not schema_path.exists():
            continue

        content = read_md(schema_path)
        if CONSTRAINT_START not in content:
            continue

        stripped = _strip_wiki_block(content)

        if dry_run:
            if stripped:
                print(f"  WOULD CLEAN block from: {filename} (user content preserved)")
            else:
                print(f"  WOULD DELETE: {filename} (only contained wiki constraints)")
        else:
            if stripped:
                write_md(schema_path, stripped)
                print(f"  CLEANED block from: {filename} (user content preserved)")
            else:
                schema_path.unlink()
                print(f"  DELETED: {filename} (only contained wiki constraints)")
        cleaned += 1

    return cleaned


def _remove_wiki_dir(wiki_dir: Path, dry_run: bool = False) -> bool:
    """Remove the wiki directory tree."""
    if not wiki_dir.exists():
        return False

    if dry_run:
        page_count = len(list(wiki_dir.rglob("*.md")))
        print(f"  WOULD REMOVE: {wiki_dir}/ ({page_count} markdown files)")
    else:
        shutil.rmtree(wiki_dir)
        print(f"  REMOVED: {wiki_dir}/")
    return True


def _remove_reference_skill(dry_run: bool = False) -> int:
    """Remove installed wiki-reference skill copies, but only unmodified ones.

    Sweeps every directory provisioning may have used across agents.
    """
    removed = 0
    for target in KNOWN_INSTALL_TARGETS:
        state = reference_skill_state(target=target)
        if state == "absent":
            continue

        skill_dir = Path(target) / REFERENCE_SKILL_ID
        if state == "modified":
            print(
                f"  SKIP {skill_dir}/ (locally modified — remove manually if intended)"
            )
            continue

        if dry_run:
            print(f"  WOULD REMOVE: {skill_dir}/")
        else:
            shutil.rmtree(skill_dir)
            print(f"  REMOVED: {skill_dir}/")
        removed += 1
    return removed


def _remove_runtime_artifacts(dry_run: bool = False) -> int:
    """Remove local runtime artifacts created by llm-wiki."""
    removed = 0
    for filepath in RUNTIME_ARTIFACTS:
        p = Path(filepath)
        if p.exists():
            if dry_run:
                print(f"  WOULD REMOVE: {filepath}")
            else:
                p.unlink()
                print(f"  REMOVED: {filepath}")
            removed += 1
    return removed


def _remove_ci_workflow(dry_run: bool = False) -> int:
    """Remove the dedicated CI workflow only when its checksum proves ownership."""

    path = Path(MANAGED_WORKFLOW_PATH)
    unsafe = first_unsafe_path_component(path)
    if unsafe is not None:
        print(f"  SKIP {path} (unsafe or not a regular managed workflow)")
        return 0
    if not path.exists() and not path.is_symlink():
        return 0
    if not path.is_file():
        print(f"  SKIP {path} (unsafe or not a regular managed workflow)")
        return 0
    try:
        content = path.read_bytes()
    except OSError:
        print(f"  SKIP {path} (cannot verify managed ownership)")
        return 0
    if not is_unmodified_managed_workflow(content):
        print(f"  SKIP {path} (locally modified or not managed by llm-wiki)")
        return 0

    if dry_run:
        print(f"  WOULD REMOVE: {path}")
    else:
        try:
            path.unlink()
        except OSError as exc:
            print(f"  SKIP {path} (cannot remove managed workflow: {exc})")
            return 0
        print(f"  REMOVED: {path}")
    return 1


def run(args):
    wiki_dir_arg = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(str(wiki_dir_arg), "--wiki-dir")
    wiki_dir = Path(wiki_dir_arg)
    remove_wiki = getattr(args, "remove_wiki", False)
    dry_run = getattr(args, "dry_run", False)

    if dry_run:
        print("DRY RUN — no files will be modified:\n")

    # ── 1. Preview what will be removed ──────────────────────────────
    print("LLM Wiki Uninstall")
    print("=" * 40)

    # Hooks
    print("\n1. Git Hooks:")
    hooks_count = _remove_hooks(dry_run=True)
    if hooks_count == 0:
        print("  Nothing to remove.")

    # Agent schemas
    print("\n2. Agent Constraint Blocks:")
    schema_count = 0
    for filename in AGENT_SCHEMA_FILES:
        p = Path(filename)
        if p.exists() and CONSTRAINT_START in read_md(p):
            stripped = _strip_wiki_block(read_md(p))
            if stripped:
                print(f"  {filename} — will strip wiki block (user content preserved)")
            else:
                print(f"  {filename} — will delete (only wiki constraints)")
            schema_count += 1
    if schema_count == 0:
        print("  Nothing to remove.")

    # Wiki dir
    print("\n3. Wiki Directory:")
    if remove_wiki and wiki_dir.exists():
        page_count = len(list(wiki_dir.rglob("*.md")))
        print(f"  {wiki_dir}/ — {page_count} markdown file(s)")
    elif wiki_dir.exists():
        print(f"  {wiki_dir}/ — KEPT (use --remove-wiki to delete)")
    else:
        print("  Not found.")

    # Runtime artifacts
    print("\n4. Runtime Artifacts:")
    artifact_count = sum(1 for f in RUNTIME_ARTIFACTS if Path(f).exists())
    if artifact_count:
        for f in RUNTIME_ARTIFACTS:
            if Path(f).exists():
                print(f"  {f}")
    else:
        print("  Nothing to remove.")

    # Installed wiki-reference skill copies (any agent's location)
    print("\n5. Bundled Reference Skill:")
    skill_count = 0
    skill_found = False
    for target in KNOWN_INSTALL_TARGETS:
        skill_state = reference_skill_state(target=target)
        if skill_state == "absent":
            continue
        skill_found = True
        skill_dir = Path(target) / REFERENCE_SKILL_ID
        if skill_state == "unmodified":
            print(f"  {skill_dir}/")
            skill_count += 1
        else:
            print(f"  {skill_dir}/ — KEPT (locally modified)")
    if not skill_found:
        print("  Not found.")

    # Dedicated CI workflow installed by `llm-wiki install-ci`.
    print("\n6. Managed CI Workflow:")
    ci_workflow_count = _remove_ci_workflow(dry_run=True)
    if ci_workflow_count == 0:
        print("  Nothing removable.")

    wiki_targeted = remove_wiki and wiki_dir.exists()
    total = (
        hooks_count
        + schema_count
        + (1 if wiki_targeted else 0)
        + artifact_count
        + skill_count
        + ci_workflow_count
    )
    if total == 0:
        print("\nNothing to uninstall. Project is clean.")
        return

    if dry_run:
        print(f"\nDry run complete. {total} item(s) would be affected.")
        return

    # ── 2. Confirm and execute ────────────────────────────────────────
    print(f"\n{total} item(s) will be affected.")
    if not _confirm("Proceed with uninstall?"):
        print("Aborted.")
        return

    print()
    removed_total = 0

    # Execute removals
    r = _remove_hooks()
    removed_total += r

    r = _clean_agent_schemas()
    removed_total += r

    if remove_wiki and wiki_dir.exists():
        _remove_wiki_dir(wiki_dir)
        removed_total += 1

    r = _remove_runtime_artifacts()
    removed_total += r

    r = _remove_reference_skill()
    removed_total += r

    r = _remove_ci_workflow()
    removed_total += r

    print(f"\nUninstall complete. {removed_total} item(s) removed.")
    print("To uninstall the CLI itself: pip uninstall agent-wiki-cli")
