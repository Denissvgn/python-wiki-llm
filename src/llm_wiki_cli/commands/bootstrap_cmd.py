from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

from .extract_cmd import get_inventory, get_call_graph
from ..config import validate_path


def _module_name_from_path(filepath: str) -> str:
    """Derive a short module name from a file path."""
    return Path(filepath).stem


def _build_relationships(inventory: dict) -> dict:
    """Cross-reference imports against known entity names to build a usage graph.
    
    Returns a dict mapping entity name -> list of {module, function, relationship} dicts.
    """
    # Collect all known entity (class) names
    entity_to_file = {}
    for filepath, data in inventory.items():
        for cls in data.get("classes", []):
            entity_to_file[cls["name"]] = filepath

    # relationship map: entity_name -> [{"module": ..., "function": ..., "rel": ...}]
    relationships = defaultdict(list)

    for filepath, data in inventory.items():
        mod_name = _module_name_from_path(filepath)
        imports = data.get("imports", [])
        imported_names = {imp["name"] for imp in imports}

        # Check which known entities are imported into this file
        for entity_name, entity_file in entity_to_file.items():
            # Skip self-references (class defined in same file)
            if entity_file == filepath:
                continue
            if entity_name in imported_names:
                # Find which functions reference this entity via type annotations / decorators
                for fn in data.get("functions", []):
                    # Check params and return type for entity references
                    mentions_entity = False
                    for p in fn.get("params", []):
                        if entity_name in p.get("type", ""):
                            mentions_entity = True
                    if entity_name in fn.get("return_type", ""):
                        mentions_entity = True
                    # Check decorators for response_model etc.
                    for dec in fn.get("decorators", []):
                        if entity_name in dec:
                            mentions_entity = True

                    if mentions_entity:
                        relationships[entity_name].append({
                            "module": mod_name,
                            "module_path": filepath,
                            "function": fn["name"],
                            "rel": "used_by",
                        })

                # If imported but not found in any specific function, still note the import
                if not any(r["module"] == mod_name for r in relationships[entity_name]):
                    relationships[entity_name].append({
                        "module": mod_name,
                        "module_path": filepath,
                        "function": None,
                        "rel": "imported_by",
                    })

    return dict(relationships)


def _format_signature(fn: dict) -> str:
    """Build a readable function signature string."""
    params = []
    for p in fn.get("params", []):
        part = p["name"]
        if p.get("type"):
            part += f": {p['type']}"
        if p.get("default"):
            part += f" = {p['default']}"
        params.append(part)

    ret = fn.get("return_type", "")
    sig = f"({', '.join(params)})"
    if ret:
        sig += f" -> {ret}"
    return sig


def _generate_entity_md(class_info: dict, filepath: str, relationships: dict) -> str:
    """Generate comprehensive markdown for a class entity."""
    name = class_info["name"]
    bases = class_info.get("bases", [])
    line = class_info.get("line", "?")
    docstring = class_info.get("docstring", "")
    decorators = class_info.get("decorators", [])
    attributes = class_info.get("attributes", [])
    methods = class_info.get("methods", [])
    mod_name = _module_name_from_path(filepath)

    bases_str = ", ".join(f"`{b}`" for b in bases) if bases else "—"

    lines = [
        f"# {name}",
        "",
        f"**Location:** `{filepath}:{line}`",
        f"**Bases:** {bases_str}",
        f"**Module:** [{mod_name}](../modules/{mod_name}.md)",
        "",
    ]

    if decorators:
        lines.append(f"**Decorators:** {', '.join(f'`@{d}`' for d in decorators)}")
        lines.append("")

    # Description
    lines.append("## Description")
    lines.append("")
    if docstring:
        lines.append(docstring)
    else:
        lines.append(f"_Auto-generated from `{name}` in `{filepath}`._")
    lines.append("")

    # Attributes
    lines.append("## Attributes")
    lines.append("")
    if attributes:
        lines.append("| Name | Type | Default | Description |")
        lines.append("|------|------|---------|-------------|")
        for attr in attributes:
            default = f"`{attr['default']}`" if attr.get("default") else "*required*"
            lines.append(f"| `{attr['name']}` | `{attr.get('type', '—')}` | {default} | — |")
    else:
        lines.append("*No annotated attributes found.*")
    lines.append("")

    # Methods
    lines.append("## Methods")
    lines.append("")
    if methods:
        lines.append("| Method | Signature | Decorators | Description |")
        lines.append("|--------|-----------|------------|-------------|")
        for m in methods:
            sig = _format_signature(m)
            decs = ", ".join(f"`@{d}`" for d in m.get("decorators", [])) or "—"
            doc = m.get("docstring", "").split("\n")[0] if m.get("docstring") else "—"
            async_tag = "*(async)* " if m.get("is_async") else ""
            lines.append(f"| `{m['name']}` | `{async_tag}{sig}` | {decs} | {doc} |")
    else:
        lines.append("*No public methods. Inherits from base classes.*")
    lines.append("")

    # Relationships
    rels = relationships.get(name, [])
    lines.append("## Relationships")
    lines.append("")
    if rels:
        for r in rels:
            mod_link = f"[{r['module']}](../modules/{r['module']}.md)"
            if r.get("function"):
                lines.append(f"- **{r['rel']}**: `{r['function']}()` in {mod_link}")
            else:
                lines.append(f"- **{r['rel']}**: {mod_link}")
    else:
        lines.append("*No cross-module references detected.*")
    lines.append("")

    return "\n".join(lines)


def _generate_module_md(filepath: str, file_data: dict) -> str:
    """Generate comprehensive markdown for a module page."""
    mod_name = _module_name_from_path(filepath)
    classes = file_data.get("classes", [])
    functions = file_data.get("functions", [])
    imports = file_data.get("imports", [])
    module_docstring = file_data.get("module_docstring", "")

    lines = [
        f"# {mod_name} Module",
        "",
        f"**Path:** `{filepath}`",
        "",
    ]

    # Description
    lines.append("## Description")
    lines.append("")
    if module_docstring:
        lines.append(module_docstring)
    else:
        lines.append(f"_Auto-generated from `{filepath}`._")
    lines.append("")

    # Imports
    if imports:
        # Group imports by source module
        grouped: dict[str, list[str]] = defaultdict(list)
        for imp in imports:
            grouped[imp["module"]].append(imp["name"])

        lines.append("## Imports")
        lines.append("")
        lines.append("| Source | Symbols |")
        lines.append("|--------|---------|")
        for module, names in sorted(grouped.items()):
            lines.append(f"| `{module}` | {', '.join(f'`{n}`' for n in names)} |")
        lines.append("")

    # Classes
    if classes:
        lines.append("## Classes")
        lines.append("")
        lines.append("| Class | Line | Bases | Description |")
        lines.append("|-------|------|-------|-------------|")
        for c in classes:
            entity_link = f"[{c['name']}](../entities/{c['name']}.md)"
            bases = ", ".join(f"`{b}`" for b in c.get("bases", [])) or "—"
            doc = c.get("docstring", "").split("\n")[0] if c.get("docstring") else "—"
            lines.append(f"| {entity_link} | {c.get('line', '?')} | {bases} | {doc} |")
        lines.append("")

    # Functions
    if functions:
        lines.append("## Functions")
        lines.append("")
        lines.append("| Function | Signature | Decorators | Description |")
        lines.append("|----------|-----------|------------|-------------|")
        for fn in functions:
            sig = _format_signature(fn)
            decs = ", ".join(f"`@{d}`" for d in fn.get("decorators", [])) or "—"
            doc = fn.get("docstring", "").split("\n")[0] if fn.get("docstring") else "—"
            async_tag = "*(async)* " if fn.get("is_async") else ""
            lines.append(f"| `{fn['name']}` | `{async_tag}{sig}` | {decs} | {doc} |")
        lines.append("")

    return "\n".join(lines)


def _generate_index_md(entity_names: list[str], module_entries: list[dict], workflow_entries: list[dict] | None = None) -> str:
    """Generate the full index.md content."""
    lines = [
        "# LLM Wiki Index",
        "",
        "Catalog of project modules and entities.",
        "",
        "## Entities",
        "",
    ]

    for name in sorted(entity_names):
        lines.append(f"- [{name}](entities/{name}.md)")

    lines.append("")
    lines.append("## Modules")
    lines.append("")

    for entry in sorted(module_entries, key=lambda e: e["name"]):
        desc = entry.get("docstring", "")
        suffix = f" - {desc}" if desc else f" - `{entry['path']}`"
        lines.append(f"- [{entry['name']}](modules/{entry['name']}.md){suffix}")

    lines.append("")
    lines.append("## Workflows")
    lines.append("")

    if workflow_entries:
        for wf in sorted(workflow_entries, key=lambda w: w["name"]):
            entry_point = wf.get("entry", "")
            lines.append(f"- [{wf['name']}](workflows/{wf['name']}.md) - entry: `{entry_point}`")
        lines.append("")

    return "\n".join(lines)


def _generate_workflow_md(name: str, wf: dict) -> str:
    """Generate a skeleton workflow page from call-graph data."""
    entry = wf["entry"]
    modules = wf["modules_touched"]
    chain = wf.get("chain", [])
    docstring = wf.get("docstring", "")

    lines = [
        f"# {name}",
        "",
        f"**Entry point:** `{entry}`",
        f"**Modules involved:** {', '.join(f'[{m}](../modules/{m}.md)' for m in modules)}",
        "",
    ]

    if docstring:
        lines.append(f"> {docstring}")
        lines.append("")

    lines.append("## Sequence")
    lines.append("")
    lines.append("<!-- Auto-detected call chain. Refine order and conditions after review. -->")
    if chain:
        for i, step in enumerate(chain, 1):
            lines.append(f"{i}. `{step}`")
    else:
        lines.append("*No detailed chain extracted — refine manually.*")
    lines.append("")

    lines.append("## Touches")
    lines.append("")
    for m in modules:
        lines.append(f"- [{m}](../modules/{m}.md)")
    lines.append("")

    return "\n".join(lines)


def run(args):
    src_dir = args.src_dir
    wiki_dir = Path(args.wiki_dir)
    validate_path(str(wiki_dir), "--wiki-dir")
    validate_path(src_dir, "--src-dir")
    depth = getattr(args, "depth", "full")
    deep = depth == "full"
    skip_workflows = getattr(args, "skip_workflows", False)

    print(f"Bootstrapping wiki from source: {src_dir} (depth={depth})")
    print(f"Wiki output directory: {wiki_dir}")

    # Ensure wiki structure exists
    for subdir in ["entities", "modules", "workflows"]:
        (wiki_dir / subdir).mkdir(parents=True, exist_ok=True)

    # 1. Extract full AST inventory
    inventory = get_inventory(src_dir, deep=deep)

    if not inventory:
        print("No Python files with classes or functions found. Nothing to bootstrap.")
        return

    # 2. Build cross-reference relationships (only meaningful in deep mode)
    relationships = _build_relationships(inventory) if deep else {}

    all_entity_names = []
    module_entries = []
    entities_created = 0
    modules_created = 0

    for filepath, file_data in inventory.items():
        mod_name = _module_name_from_path(filepath)

        # Generate entity pages for each class
        for cls in file_data.get("classes", []):
            entity_path = wiki_dir / "entities" / f"{cls['name']}.md"
            if entity_path.exists() and not args.overwrite:
                print(f"  SKIP entity (exists): {cls['name']}")
            else:
                entity_path.write_text(_generate_entity_md(cls, filepath, relationships))
                entities_created += 1
                print(f"  CREATE entity: {cls['name']}")
            all_entity_names.append(cls["name"])

        # Generate module page
        module_path = wiki_dir / "modules" / f"{mod_name}.md"
        if module_path.exists() and not args.overwrite:
            print(f"  SKIP module (exists): {mod_name}")
        else:
            module_path.write_text(_generate_module_md(filepath, file_data))
            modules_created += 1
            print(f"  CREATE module: {mod_name}")

        module_entries.append({
            "name": mod_name,
            "path": filepath,
            "docstring": file_data.get("module_docstring", ""),
        })

    # 3. Generate workflow pages from call graph (deep mode only)
    workflow_entries = []
    workflows_created = 0
    if deep and not skip_workflows:
        call_graph = get_call_graph(inventory)
        for wf_name, wf_data in call_graph.items():
            wf_path = wiki_dir / "workflows" / f"{wf_name}.md"
            if wf_path.exists() and not args.overwrite:
                print(f"  SKIP workflow (exists): {wf_name}")
            else:
                wf_path.write_text(_generate_workflow_md(wf_name, wf_data))
                workflows_created += 1
                print(f"  CREATE workflow: {wf_name}")
            workflow_entries.append({"name": wf_name, "entry": wf_data["entry"]})

    # 4. Rebuild index.md
    index_path = wiki_dir / "index.md"
    index_path.write_text(_generate_index_md(all_entity_names, module_entries, workflow_entries or None))
    print(f"  WRITE index.md")

    # 5. Append log entry
    log_path = wiki_dir / "log.md"
    today = date.today().isoformat()
    log_entry = (
        f"\n## {today}\n\n"
        f"### feat: bootstrap wiki from existing codebase\n"
        f"- Source: `{src_dir}`\n"
        f"- Depth: `{depth}`\n"
        f"- Entities created: {entities_created}\n"
        f"- Modules created: {modules_created}\n"
        f"- Workflows created: {workflows_created}\n"
        f"- Total classes tracked: {len(all_entity_names)}\n"
        f"- Total files scanned: {len(inventory)}\n"
        f"- Cross-references resolved: {sum(len(v) for v in relationships.values())}\n"
    )
    if log_path.exists():
        with open(log_path, "a") as f:
            f.write(log_entry)
    else:
        with open(log_path, "w") as f:
            f.write("# Architectural Log\n\nAppend-only chronological log.\n")
            f.write(log_entry)

    print(
        f"\nBootstrap complete: {entities_created} entities, "
        f"{modules_created} modules, {workflows_created} workflows "
        f"created from {len(inventory)} source files "
        f"({sum(len(v) for v in relationships.values())} cross-references)."
    )

    # 6. Update agent constraint files if wiki-dir differs from default
    _update_agent_constraints(str(wiki_dir))


_CONSTRAINT_START = "# --- LLM Wiki Maintainer Constraints ---"
_CONSTRAINT_END = "# --- End LLM Wiki Constraints ---"

from ..config import DEFAULT_WIKI_DIR as _DEFAULT_WIKI_DIR

# All agent schema files that may contain wiki path references
_AGENT_SCHEMA_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    ".agents.md",
    ".aider.conf.yml",
    ".opencode/instructions.md",
]


def _update_agent_constraints(wiki_dir: str) -> None:
    """Replace docs/llm_wiki path references inside the constraint block
    in any existing agent schema files to match the actual wiki_dir."""
    # Normalize: treat both as Path to allow absolute/relative comparison
    wiki_path = Path(wiki_dir)
    default_path = Path(_DEFAULT_WIKI_DIR)
    # Nothing to do if the resolved paths are the same or wiki_dir already
    # contains the default string (handles the relative == relative case)
    if wiki_path == default_path or wiki_dir == _DEFAULT_WIKI_DIR:
        return
    # Also skip if the resolved absolute paths are equivalent
    try:
        if wiki_path.resolve() == default_path.resolve():
            return
    except OSError:
        pass

    updated = []
    for filename in _AGENT_SCHEMA_FILES:
        p = Path(filename)
        if not p.exists():
            continue
        text = p.read_text()
        if _CONSTRAINT_START not in text or _CONSTRAINT_END not in text:
            continue

        # Replace only within the constraint block to avoid touching user content
        start_idx = text.index(_CONSTRAINT_START)
        end_idx = text.index(_CONSTRAINT_END, start_idx) + len(_CONSTRAINT_END)
        block = text[start_idx:end_idx]
        new_block = block.replace(_DEFAULT_WIKI_DIR, wiki_dir)
        if new_block != block:
            p.write_text(text[:start_idx] + new_block + text[end_idx:])
            updated.append(filename)

    if updated:
        print(f"\nUpdated wiki path to `{wiki_dir}` in: {', '.join(updated)}")
