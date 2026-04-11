import argparse
import sys
from .commands import init_cmd, extract_cmd, lint_cmd, hook_cmd, trigger_cmd, bootstrap_cmd, bump_cmd, uninstall_cmd, generate_prompt_cmd, status_cmd, release_cmd
from .config import AGENT_CHOICES, DEFAULT_WIKI_DIR

def main():
    parser = argparse.ArgumentParser(description="LLM Wiki CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    init_parser = subparsers.add_parser("init", help="Scaffold LLM Wiki structure and schema")
    init_parser.add_argument("--agent", choices=AGENT_CHOICES, default="generic", help="Target agent format for rules/constraints")
    init_parser.add_argument("--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory to create (default: docs/llm_wiki)")

    # extract command
    # ... (skipping extract/lint)
    extract_parser = subparsers.add_parser("extract", help="Extract project AST and structure into wiki")
    extract_parser.add_argument("--src-dir", default=".", help="Source directory to scan")

    # lint command
    lint_parser = subparsers.add_parser("lint", help="Lint LLM Wiki for broken links, orphans, and AST drift")
    lint_parser.add_argument("--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory to lint")
    lint_parser.add_argument("--src-dir", default=".", help="Source directory to cross-reference against")

    # hook command
    hook_parser = subparsers.add_parser("install-hook", help="Install git hooks (wiki sync + optional versioning)")
    hook_parser.add_argument("--wiki-dir", default=DEFAULT_WIKI_DIR,
                             help="Wiki directory to read agent config from (default: docs/llm_wiki)")
    hook_parser.add_argument("--agent", choices=AGENT_CHOICES, default=None,
                             help="Override the agent for the post-commit hook (default: read from wiki config)")
    hook_parser.add_argument("--enable-versioning", action="store_true",
                             help="Enable auto version bumping (patch on commit, minor on push)")

    # trigger command
    trigger_parser = subparsers.add_parser("trigger-agent", help="Trigger subagent to update wiki using diff")
    trigger_parser.add_argument("--agent", choices=AGENT_CHOICES, default="claude", help="Agent executable to invoke for background sync")
    trigger_parser.add_argument("--reset-breaker", action="store_true",
                                help="Reset the circuit breaker after consecutive failures and exit")
    trigger_parser.add_argument("--timeout", type=int, default=300,
                                help="Timeout in seconds for the subagent process (default: 300)")
    trigger_parser.add_argument("--max-diff-lines", type=int, default=1000,
                                help="Skip sync if diff exceeds this many lines (default: 1000)")
    trigger_parser.add_argument("--force", action="store_true",
                                help="Bypass the diff size guard (does not bypass lock or circuit breaker)")

    # bootstrap command
    bootstrap_parser = subparsers.add_parser("bootstrap", help="Generate initial wiki for an existing codebase")
    bootstrap_parser.add_argument("--src-dir", default=".", help="Source directory to scan")
    bootstrap_parser.add_argument("--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki output directory")
    bootstrap_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing entity/module pages")
    bootstrap_parser.add_argument("--depth", choices=["shallow", "full"], default="full",
                                  help="shallow=names only, full=docstrings/attrs/methods/imports/relationships (default: full)")
    bootstrap_parser.add_argument("--skip-workflows", action="store_true",
                                  help="Skip automatic workflow page generation from call graph")

    # bump command
    bump_parser = subparsers.add_parser("bump", help="Bump project version (patch or minor)")
    bump_group = bump_parser.add_mutually_exclusive_group(required=True)
    bump_group.add_argument("--patch", dest="bump_type", action="store_const", const="patch",
                            help="Bump patch version (0.1.5 -> 0.1.6)")
    bump_group.add_argument("--minor", dest="bump_type", action="store_const", const="minor",
                            help="Bump minor version (0.1.6 -> 0.2.0)")
    bump_parser.add_argument("--stage", action="store_true",
                             help="Git-add the version file after bumping (for use in hooks)")

    # generate-prompt command
    gp_parser = subparsers.add_parser("generate-prompt", help="Build a wiki sync prompt for IDE agents (Copilot, Cursor, etc.)")
    gp_parser.add_argument("--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory (default: docs/llm_wiki)")
    gp_parser.add_argument("--src-dir", default=".", help="Source directory to scan (default: .)")
    gp_parser.add_argument("--output", default=".git/llm-wiki-prompt.txt", help="Output file path (default: .git/llm-wiki-prompt.txt)")
    gp_parser.add_argument("--print", dest="print_prompt", action="store_true", help="Print the prompt to stdout instead of writing to a file")
    gp_parser.add_argument("--no-diff", action="store_true", help="Skip git diff (useful when no commits exist yet)")

    # uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Remove all LLM Wiki artifacts from the project")
    uninstall_parser.add_argument("--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory path")
    uninstall_parser.add_argument("--remove-wiki", action="store_true",
                                  help="Also remove the wiki documentation directory")
    uninstall_parser.add_argument("--dry-run", action="store_true",
                                  help="Preview what would be removed without deleting anything")

    # status command
    status_parser = subparsers.add_parser("status", help="Show LLM Wiki status (agent, hooks, breaker, pages)")
    status_parser.add_argument("--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory path")

    # release command
    release_parser = subparsers.add_parser(
        "release",
        help="Stamp the [Unreleased] CHANGELOG section with the current version",
    )
    release_parser.add_argument(
        "--changelog", default="CHANGELOG.md",
        help="Path to the changelog file (default: CHANGELOG.md)",
    )
    release_parser.add_argument(
        "--stage", action="store_true",
        help="Git-add CHANGELOG.md after stamping (for use in hooks)",
    )

    args = parser.parse_args()

    try:
        if args.command == "init":
            init_cmd.run(args)
        elif args.command == "extract":
            extract_cmd.run(args)
        elif args.command == "lint":
            lint_cmd.run(args)
        elif args.command == "install-hook":
            hook_cmd.run(args)
        elif args.command == "trigger-agent":
            trigger_cmd.run(args)
        elif args.command == "bootstrap":
            bootstrap_cmd.run(args)
        elif args.command == "bump":
            bump_cmd.run(args)
        elif args.command == "generate-prompt":
            generate_prompt_cmd.run(args)
        elif args.command == "uninstall":
            uninstall_cmd.run(args)
        elif args.command == "status":
            status_cmd.run(args)
        elif args.command == "release":
            release_cmd.run(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
