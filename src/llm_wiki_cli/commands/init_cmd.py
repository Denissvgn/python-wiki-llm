import os
import shutil
from pathlib import Path

_DEFAULT_WIKI_DIR = "docs/llm_wiki"


def _wiki_instructions(wiki_dir: str) -> str:
    return f"""You are operating within an LLM Wiki architecture. The project's persistent memory is stored in `{wiki_dir}/`.

## Before you start
- ALWAYS read `{wiki_dir}/index.md` before planning a new feature or making architectural changes.
- Consult relevant entity and module pages to understand existing patterns before writing new code.

## When you change code
- UPDATE `{wiki_dir}/entities/<ClassName>.md` when you add, modify, or remove a class.
- UPDATE `{wiki_dir}/modules/<filename>.md` when you add, modify, or remove a module.
- UPDATE `{wiki_dir}/workflows/<name>.md` when a cross-module flow changes.
- LOG a concise summary of your changes in `{wiki_dir}/log.md` (append-only, newest at bottom).

## Quality checks
- Run `llm-wiki lint --wiki-dir {wiki_dir} --src-dir .` to verify wiki consistency.
- Run `llm-wiki extract --src-dir .` to see the live AST inventory.
- Never leave the wiki in a state where lint reports errors.

## Formatting rules
- Entity pages must have: Location, Bases, Module link, Attributes table, Methods table, Relationships.
- Module pages must have: Path, Imports table, Classes summary, Functions table.
- Use relative markdown links between pages (e.g., `../entities/User.md`).
"""


_IDE_AGENTS = {"cursor", "copilot", "generic"}

_IDE_SYNC_INSTRUCTIONS = """\

## How to sync the wiki in this IDE session
Because you run inside the IDE (not as a background CLI process), the wiki is NOT
updated automatically on commit. You are responsible for keeping it current:

1. **After every code change in this session** that adds, removes, or modifies a
   class, function, module, or cross-module flow:
   - Update the relevant `entities/` and `modules/` pages immediately.
   - If 3+ modules are now connected differently, update or create a `workflows/` page.
   - Append a one-line summary to `log.md`.
2. **To do a full re-sync manually**, run in the terminal:
   ```
   llm-wiki generate-prompt
   ```
   This builds a diff + AST prompt in `.git/llm-wiki-prompt.txt`. Open that file
   and paste its contents into this chat to trigger a full wiki update.
3. **Never skip the update** — a stale wiki defeats the purpose of the system.
"""

# Marker boundaries used to wrap the entire generated block
_CONSTRAINT_START = "# --- LLM Wiki Maintainer Constraints ---"
_CONSTRAINT_END = "# --- End LLM Wiki Constraints ---"


def _build_schema_content(agent: str, wiki_dir: str) -> str:
    instructions = _wiki_instructions(wiki_dir)
    preambles = {
        "claude": f"# Project Wiki\n\nThis project uses an LLM Wiki for persistent architectural memory.\nRead `{wiki_dir}/index.md` first when starting any task.\n\n",
        "cursor": f"# Cursor Rules — LLM Wiki Project\n\nThis project maintains a living wiki at `{wiki_dir}/`.\nAlways consult it before making changes.\n\n",
        "copilot": f"# Copilot Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` as persistent documentation.\nConsult the wiki before suggesting changes.\n\n",
    }
    preamble = preambles.get(agent, f"# Agent Instructions — LLM Wiki Project\n\nThis project uses `{wiki_dir}/` for architectural memory.\n\n")
    extra = _IDE_SYNC_INSTRUCTIONS if agent in _IDE_AGENTS else ""
    body = preamble + instructions + extra
    return f"{_CONSTRAINT_START}\n{body.strip()}\n{_CONSTRAINT_END}\n"


# Agents that have a real CLI executable (used by trigger-agent / install-hook)
_CLI_AGENTS: dict[str, str] = {
    "claude": "claude",
    "aider": "aider",
    "opencode": "opencode",
}

SCHEMA_FILENAMES = {
    "claude": "CLAUDE.md",
    "cursor": ".cursorrules",
    "copilot": ".github/copilot-instructions.md",
    "aider": ".aider.conf.yml",
    "opencode": ".opencode/instructions.md",
    "generic": ".agents.md",
}


def run(args):
    wiki_dir = getattr(args, "wiki_dir", _DEFAULT_WIKI_DIR)
    print(f"Initializing LLM Wiki with {args.agent} schema...")

    # Warn if the agent has a CLI executable that isn't installed
    executable = _CLI_AGENTS.get(args.agent)
    if executable and not shutil.which(executable):
        print(
            f"\nWarning: '{executable}' is not installed or not on PATH.\n"
            f"The schema file will be created, but background auto-sync\n"
            f"(`llm-wiki trigger-agent --agent {args.agent}`) will not work\n"
            f"until '{executable}' is installed.\n"
        )

    
    # 1. Create directory structure
    base_dir = Path(wiki_dir)
    directories = [
        base_dir,
        base_dir / "entities",
        base_dir / "modules",
        base_dir / "workflows"
    ]
    
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        # Create empty .gitkeep so git tracks empty dirs
        (d / ".gitkeep").touch()
        
    print(f"Created wiki directories in {base_dir}/")
    
    # 2. Create core files if they don't exist
    index_path = base_dir / "index.md"
    if not index_path.exists():
        with open(index_path, "w") as f:
            f.write("# LLM Wiki Index\n\nCatalog of project modules and entities.\n\n## Entities\n\n## Modules\n\n## Workflows\n")
            
    log_path = base_dir / "log.md"
    if not log_path.exists():
        with open(log_path, "w") as f:
            f.write("# Architectural Log\n\nAppend-only chronological log.\n\n")

    # 3. Create or Append to Agent Schema
    filename = SCHEMA_FILENAMES.get(args.agent)
    if filename:
        schema_path = Path(filename)
        # ensure parent exists (e.g. for .github/)
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        content_to_add = _build_schema_content(args.agent, wiki_dir)
        
        if schema_path.exists():
            with open(schema_path, "r") as f:
                existing_content = f.read()
                
            if "# --- LLM Wiki Maintainer Constraints ---" not in existing_content:
                with open(schema_path, "a") as f:
                    # Append cleanly
                    f.write("\n\n" + content_to_add)
                print(f"Appended agent constraints to existing file: {schema_path}")
            else:
                print(f"Agent constraints already exist in {schema_path}, skipping append.")
        else:
            with open(schema_path, "w") as f:
                f.write(content_to_add)
            print(f"Created agent schema file: {schema_path}")
    
    # 4. Persist the chosen agent so install-hook can read it
    agent_config_path = base_dir / ".llm-wiki-agent"
    with open(agent_config_path, "w") as f:
        f.write(args.agent)

    print("LLM Wiki initialized successfully.")

