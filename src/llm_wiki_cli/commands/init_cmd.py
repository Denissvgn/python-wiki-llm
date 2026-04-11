import os
from pathlib import Path

# Enhanced and consistent schema template for all agents
WIKI_INSTRUCTIONS = """
# --- LLM Wiki Maintainer Constraints ---
You are operating within an LLM Wiki architecture. The project's persistent memory is stored in `docs/llm_wiki/`.

CRITICAL RULES:
1. ALWAYS read `docs/llm_wiki/index.md` before planning a new feature or making architectural changes.
2. UPDATE `docs/llm_wiki/entities/` and `docs/llm_wiki/modules/` whenever you create, modify, or deprecate systems so the documentation perfectly matches the codebase.
3. LOG all meaningful changes in `docs/llm_wiki/log.md`.
4. Run the local `llm-wiki extract` context tool to verify that the physical Python structure perfectly maps to the documentation you write.
# --- End LLM Wiki Constraints ---
"""

SCHEMA_TEMPLATES = {
    "claude": {"filename": "CLAUDE.md", "content": WIKI_INSTRUCTIONS},
    "cursor": {"filename": ".cursorrules", "content": WIKI_INSTRUCTIONS},
    "copilot": {"filename": ".github/copilot-instructions.md", "content": WIKI_INSTRUCTIONS},
    "generic": {"filename": ".agents.md", "content": WIKI_INSTRUCTIONS}
}

def run(args):
    print(f"Initializing LLM Wiki with {args.agent} schema...")
    
    # 1. Create directory structure
    base_dir = Path("docs/llm_wiki")
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
    schema = SCHEMA_TEMPLATES.get(args.agent)
    if schema:
        schema_path = Path(schema["filename"])
        # ensure parent exists (e.g. for .github/)
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        content_to_add = schema["content"]
        
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
    
    print("LLM Wiki initialized successfully.")
