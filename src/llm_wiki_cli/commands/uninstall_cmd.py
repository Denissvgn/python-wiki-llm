import shutil
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR
from ..services.schema import (
    ALL_SCHEMA_FILES as AGENT_SCHEMA_FILES,
    CONSTRAINT_START,
    CONSTRAINT_END,
    strip_wiki_block as _strip_wiki_block,
)

# Hook identifier — all llm-wiki hooks contain this string
HOOK_SIGNATURE = "LLM Wiki"

# Hooks that install-hook may have written
HOOK_NAMES = ["post-commit", "pre-commit", "pre-push"]

# Temp files created at runtime
TEMP_FILES = [
    ".git/llm-wiki-prompt.txt",
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

        content = hook_path.read_text()
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

        content = schema_path.read_text()
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
                schema_path.write_text(stripped)
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


def _remove_temp_files(dry_run: bool = False) -> int:
    """Remove temporary files created at runtime."""
    removed = 0
    for filepath in TEMP_FILES:
        p = Path(filepath)
        if p.exists():
            if dry_run:
                print(f"  WOULD REMOVE: {filepath}")
            else:
                p.unlink()
                print(f"  REMOVED: {filepath}")
            removed += 1
    return removed


def run(args):
    wiki_dir = Path(getattr(args, "wiki_dir", DEFAULT_WIKI_DIR))
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
        if p.exists() and CONSTRAINT_START in p.read_text():
            stripped = _strip_wiki_block(p.read_text())
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

    # Temp files
    print("\n4. Temp Files:")
    temp_count = sum(1 for f in TEMP_FILES if Path(f).exists())
    if temp_count:
        for f in TEMP_FILES:
            if Path(f).exists():
                print(f"  {f}")
    else:
        print("  Nothing to remove.")

    wiki_targeted = remove_wiki and wiki_dir.exists()
    total = hooks_count + schema_count + (1 if wiki_targeted else 0) + temp_count
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

    r = _remove_temp_files()
    removed_total += r

    print(f"\nUninstall complete. {removed_total} item(s) removed.")
    print("To uninstall the CLI itself: pip uninstall llm_wiki_cli")
