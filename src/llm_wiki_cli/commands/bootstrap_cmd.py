from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

from .extract_cmd import get_inventory, get_call_graph, get_docker_inventory
from ..config import validate_path
from ..services.io import read_md, write_md


def _module_name_from_path(filepath: str) -> str:
    """Derive a short module name from a file path."""
    return Path(filepath).stem


# Directory names too generic to use as service-level qualifiers.
_GENERIC_DIRS = {"src", "lib", "app", "pkg", "core", "main", "tests", "test"}


def _qualifier_for(filepath: str, src_dir: str) -> str:
    """Build a filesystem-safe path-derived qualifier, unique per source file.

    Skips generic directory names and joins remaining path components with '__',
    always including the file stem so the qualifier is uniquely tied to the file.
    """
    p = Path(filepath)
    try:
        rel = p.relative_to(Path(src_dir))
    except ValueError:
        rel = p
    dirs = [
        pt for pt in rel.parts[:-1]
        if pt.lower() not in _GENERIC_DIRS and not pt.startswith(".")
    ]
    # Include the file stem so two different files in the same directory
    # can never share a qualifier (OS guarantees unique filenames per dir).
    dirs.append(p.stem)
    joined = "__".join(dirs) if dirs else p.stem
    return re.sub(r"[^a-zA-Z0-9]+", "_", joined)


def _page_name_for_module(filepath: str, src_dir: str, colliding_stems: set[str]) -> str:
    """Return the wiki page stem for a module, qualifying on collision."""
    stem = Path(filepath).stem
    if stem in colliding_stems:
        return f"{_qualifier_for(filepath, src_dir)}__{stem}"
    return stem


def _page_name_for_entity(cls_name: str, filepath: str, src_dir: str, colliding_cls: set[str]) -> str:
    """Return the wiki page stem for an entity, qualifying on collision."""
    if cls_name in colliding_cls:
        return f"{_qualifier_for(filepath, src_dir)}__{cls_name}"
    return cls_name


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


def _generate_entity_md(class_info: dict, filepath: str, relationships: dict, mod_page_name: str | None = None) -> str:
    """Generate comprehensive markdown for a class entity."""
    name = class_info["name"]
    bases = class_info.get("bases", [])
    line = class_info.get("line", "?")
    docstring = class_info.get("docstring", "")
    decorators = class_info.get("decorators", [])
    attributes = class_info.get("attributes", [])
    methods = class_info.get("methods", [])
    mod_name = mod_page_name if mod_page_name is not None else _module_name_from_path(filepath)

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


def _generate_module_md(filepath: str, file_data: dict, entity_page_map: dict | None = None) -> str:
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
            page_name = (entity_page_map or {}).get(c["name"], c["name"])
            entity_link = f"[{c['name']}](../entities/{page_name}.md)"
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


def _generate_index_md(entity_names: list[str], module_entries: list[dict], workflow_entries: list[dict] | None = None, infra_entries: list[dict] | None = None) -> str:
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

    lines.append("## Infrastructure")
    lines.append("")

    if infra_entries:
        for entry in sorted(infra_entries, key=lambda e: e["name"]):
            desc = entry.get("type", "")
            suffix = f" - {desc}" if desc else ""
            lines.append(f"- [{entry['name']}](infrastructure/{entry['name']}.md){suffix}")
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


def _generate_docker_md(filename: str, info: dict, module_stems: set[str] | None = None) -> str:
    """Generate a wiki page for a Dockerfile or docker-compose file."""
    if info["type"] == "dockerfile":
        return _generate_dockerfile_md(filename, info, module_stems)
    return _generate_compose_md(filename, info, module_stems)


def _generate_dockerfile_md(filename: str, info: dict, module_stems: set[str] | None = None) -> str:
    """Generate markdown for a Dockerfile."""
    stages = info.get("stages", [])
    ports = info.get("ports", [])
    env_vars = info.get("env_vars", [])
    volumes = info.get("volumes", [])
    copies = info.get("copies", [])
    build_args = info.get("build_args", [])
    labels = info.get("labels", {})
    entrypoint = info.get("entrypoint", "")
    cmd = info.get("cmd", "")
    workdir = info.get("workdir", "")
    healthcheck = info.get("healthcheck", "")

    base_images = [s["image"] for s in stages] if stages else ["unknown"]

    lines = [
        f"# {filename}",
        "",
        f"**Path:** `{filename}`",
        f"**Base Image(s):** {', '.join(f'`{img}`' for img in base_images)}",
        "",
    ]

    # Build stages
    if len(stages) > 1 or (stages and stages[0].get("alias")):
        lines.append("## Build Stages")
        lines.append("")
        lines.append("| Stage | Base Image |")
        lines.append("|-------|-----------|")
        for s in stages:
            alias = f"`{s['alias']}`" if s.get("alias") else "*(final)*"
            lines.append(f"| {alias} | `{s['image']}` |")
        lines.append("")

    # Exposed ports
    if ports:
        lines.append("## Exposed Ports")
        lines.append("")
        for p in ports:
            lines.append(f"- `{p}`")
        lines.append("")

    # Build args
    if build_args:
        lines.append("## Build Arguments")
        lines.append("")
        lines.append("| Argument | Default |")
        lines.append("|----------|---------|")
        for a in build_args:
            default = f"`{a['default']}`" if a["default"] else "—"
            lines.append(f"| `{a['name']}` | {default} |")
        lines.append("")

    # Environment variables
    if env_vars:
        lines.append("## Environment Variables")
        lines.append("")
        lines.append("| Variable | Default |")
        lines.append("|----------|---------|")
        for e in env_vars:
            default = f"`{e['default']}`" if e["default"] else "—"
            lines.append(f"| `{e['name']}` | {default} |")
        lines.append("")

    # Volumes
    if volumes:
        lines.append("## Volumes")
        lines.append("")
        for v in volumes:
            lines.append(f"- `{v}`")
        lines.append("")

    # Working directory
    if workdir:
        lines.append(f"**Working Directory:** `{workdir}`")
        lines.append("")

    # Entry point / CMD
    if entrypoint or cmd:
        lines.append("## Entry Point")
        lines.append("")
        if entrypoint:
            lines.append(f"**ENTRYPOINT:** `{entrypoint}`")
        if cmd:
            lines.append(f"**CMD:** `{cmd}`")
        lines.append("")

    # File copies
    if copies:
        lines.append("## File Copies")
        lines.append("")
        lines.append("| Instruction | Source | Destination | From Stage |")
        lines.append("|-------------|--------|-------------|------------|")
        for c in copies:
            stage = f"`{c['from_stage']}`" if c.get("from_stage") else "—"
            src_text = f"`{c['src']}`"
            # Cross-reference to module page if the copied file is a known source module
            _SOURCE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx")
            if module_stems:
                for stem in module_stems:
                    if any(f"{stem}{ext}" in c["src"] for ext in _SOURCE_EXTS):
                        src_text = f"[`{c['src']}`](../modules/{stem}.md)"
                        break
            lines.append(f"| `{c['instruction']}` | {src_text} | `{c['dest']}` | {stage} |")
        lines.append("")

    # Labels
    if labels:
        lines.append("## Labels")
        lines.append("")
        lines.append("| Key | Value |")
        lines.append("|-----|-------|")
        for k, v in labels.items():
            lines.append(f"| `{k}` | `{v}` |")
        lines.append("")

    # Healthcheck
    if healthcheck:
        lines.append(f"**Healthcheck:** `{healthcheck}`")
        lines.append("")

    return "\n".join(lines)


def _generate_compose_md(filename: str, info: dict, module_stems: set[str] | None = None) -> str:
    """Generate markdown for a docker-compose / compose file."""
    services = info.get("services", {})
    networks = info.get("networks", [])
    named_volumes = info.get("volumes", [])

    lines = [
        f"# {filename}",
        "",
        f"**Path:** `{filename}`",
        "",
    ]

    # Services summary table
    if services:
        lines.append("## Services")
        lines.append("")
        lines.append("| Service | Image / Build | Ports | Depends On |")
        lines.append("|---------|---------------|-------|------------|")
        for name, svc in services.items():
            image = svc.get("image", "")
            build = svc.get("build", "")
            if isinstance(build, dict):
                build = build.get("context", ".")
            img_str = f"build: `{build}`" if build else (f"`{image}`" if image else "—")
            ports = svc.get("ports", [])
            ports_str = ", ".join(f"`{p}`" for p in ports) if isinstance(ports, list) else (f"`{ports}`" if ports else "—")
            depends = svc.get("depends_on", [])
            deps_str = ", ".join(f"`{d}`" for d in depends) if isinstance(depends, list) else (f"`{depends}`" if depends else "—")
            lines.append(f"| `{name}` | {img_str} | {ports_str} | {deps_str} |")
        lines.append("")

        # Per-service detail
        for name, svc in services.items():
            lines.append(f"### {name}")
            lines.append("")
            image = svc.get("image", "")
            build = svc.get("build", "")
            if build:
                ctx = build if isinstance(build, str) else build.get("context", ".")
                lines.append(f"- **Build context:** `{ctx}`")
            if image:
                lines.append(f"- **Image:** `{image}`")
            ports = svc.get("ports", [])
            if ports:
                ports_list = ports if isinstance(ports, list) else [ports]
                lines.append(f"- **Ports:** {', '.join(f'`{p}`' for p in ports_list)}")
            vols = svc.get("volumes", [])
            if vols:
                vols_list = vols if isinstance(vols, list) else [vols]
                lines.append(f"- **Volumes:** {', '.join(f'`{v}`' for v in vols_list)}")
            env = svc.get("environment", [])
            if env:
                env_list = env if isinstance(env, list) else [env]
                lines.append(f"- **Environment:** {', '.join(f'`{e}`' for e in env_list)}")
            depends = svc.get("depends_on", [])
            if depends:
                deps_list = depends if isinstance(depends, list) else [depends]
                lines.append(f"- **Depends on:** {', '.join(f'`{d}`' for d in deps_list)}")
            command = svc.get("command", "")
            if command:
                lines.append(f"- **Command:** `{command}`")
            lines.append("")

    # Networks
    if networks:
        lines.append("## Networks")
        lines.append("")
        for n in networks:
            lines.append(f"- `{n}`")
        lines.append("")

    # Named volumes
    if named_volumes:
        lines.append("## Named Volumes")
        lines.append("")
        for v in named_volumes:
            lines.append(f"- `{v}`")
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
    for subdir in ["entities", "modules", "workflows", "infrastructure"]:
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
    _seen_entity_pages: set[str] = set()  # dedup index entries

    # Pre-scan: detect name collisions across files so pages can be disambiguated.
    _stem_to_fps: dict = defaultdict(list)
    _cls_to_fps: dict = defaultdict(list)
    for fp, data in inventory.items():
        _stem_to_fps[Path(fp).stem].append(fp)
        for cls in data.get("classes", []):
            _cls_to_fps[cls["name"]].append(fp)
    colliding_stems = {stem for stem, fps in _stem_to_fps.items() if len(fps) > 1}
    colliding_cls = {name for name, fps in _cls_to_fps.items() if len(fps) > 1}
    # Precompute per-file entity page names: (cls_name, filepath) -> page_stem
    _entity_page_name_cache: dict = {
        (cls["name"], fp): _page_name_for_entity(cls["name"], fp, src_dir, colliding_cls)
        for fp, data in inventory.items()
        for cls in data.get("classes", [])
    }

    for filepath, file_data in inventory.items():
        mod_page_name = _page_name_for_module(filepath, src_dir, colliding_stems)
        # Map cls_name -> page_stem for classes in this file (used by module page links)
        file_entity_page_map = {
            cls["name"]: _entity_page_name_cache[(cls["name"], filepath)]
            for cls in file_data.get("classes", [])
        }

        # Generate entity pages for each class
        for cls in file_data.get("classes", []):
            entity_page_name = file_entity_page_map[cls["name"]]
            entity_path = wiki_dir / "entities" / f"{entity_page_name}.md"
            if entity_path.exists() and not args.overwrite:
                print(f"  SKIP entity (exists): {entity_page_name}")
            else:
                write_md(entity_path, _generate_entity_md(cls, filepath, relationships, mod_page_name))
                entities_created += 1
                print(f"  CREATE entity: {entity_page_name}")
            if entity_page_name not in _seen_entity_pages:
                all_entity_names.append(entity_page_name)
                _seen_entity_pages.add(entity_page_name)

        # Generate module page
        module_path = wiki_dir / "modules" / f"{mod_page_name}.md"
        if module_path.exists() and not args.overwrite:
            print(f"  SKIP module (exists): {mod_page_name}")
        else:
            write_md(module_path, _generate_module_md(filepath, file_data, file_entity_page_map))
            modules_created += 1
            print(f"  CREATE module: {mod_page_name}")

        module_entries.append({
            "name": mod_page_name,
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
                write_md(wf_path, _generate_workflow_md(wf_name, wf_data))
                workflows_created += 1
                print(f"  CREATE workflow: {wf_name}")
            workflow_entries.append({"name": wf_name, "entry": wf_data["entry"]})

    # 4. Generate infrastructure pages (Dockerfile, docker-compose, etc.)
    infra_entries = []
    infra_created = 0
    docker_inventory = get_docker_inventory(src_dir)
    module_stems = {_module_name_from_path(fp) for fp in inventory}
    for docker_file, docker_info in docker_inventory.items():
        page_name = docker_file.replace("/", "_").replace(".", "_")
        infra_path = wiki_dir / "infrastructure" / f"{page_name}.md"
        if infra_path.exists() and not args.overwrite:
            print(f"  SKIP infrastructure (exists): {page_name}")
        else:
            write_md(infra_path, _generate_docker_md(docker_file, docker_info, module_stems))
            infra_created += 1
            print(f"  CREATE infrastructure: {page_name}")
        infra_entries.append({"name": page_name, "type": docker_info["type"]})

    # 5. Rebuild index.md
    index_path = wiki_dir / "index.md"
    write_md(index_path, _generate_index_md(all_entity_names, module_entries, workflow_entries or None, infra_entries or None))
    print(f"  WRITE index.md")

    # 6. Append log entry
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
        f"- Infrastructure created: {infra_created}\n"
        f"- Total classes tracked: {len(all_entity_names)}\n"
        f"- Total files scanned: {len(inventory)}\n"
        f"- Docker/Compose files: {len(docker_inventory)}\n"
        f"- Cross-references resolved: {sum(len(v) for v in relationships.values())}\n"
    )
    if log_path.exists():
        existing_log = read_md(log_path)
        write_md(log_path, existing_log + log_entry)
    else:
        write_md(log_path, "# Architectural Log\n\nAppend-only chronological log.\n" + log_entry)

    print(
        f"\nBootstrap complete: {entities_created} entities, "
        f"{modules_created} modules, {workflows_created} workflows, "
        f"{infra_created} infrastructure "
        f"created from {len(inventory)} source files "
        f"({sum(len(v) for v in relationships.values())} cross-references)."
    )

    # 7. Update agent constraint files if wiki-dir differs from default
    _update_agent_constraints(str(wiki_dir))


from ..config import DEFAULT_WIKI_DIR as _DEFAULT_WIKI_DIR
from ..services.schema import (
    ALL_SCHEMA_FILES as _AGENT_SCHEMA_FILES,
    CONSTRAINT_START as _CONSTRAINT_START,
    CONSTRAINT_END as _CONSTRAINT_END,
)


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
        text = read_md(p)
        if _CONSTRAINT_START not in text or _CONSTRAINT_END not in text:
            continue

        # Replace only within the constraint block to avoid touching user content
        start_idx = text.index(_CONSTRAINT_START)
        end_idx = text.index(_CONSTRAINT_END, start_idx) + len(_CONSTRAINT_END)
        block = text[start_idx:end_idx]
        new_block = block.replace(_DEFAULT_WIKI_DIR, wiki_dir)
        if new_block != block:
            write_md(p, text[:start_idx] + new_block + text[end_idx:])
            updated.append(filename)

    if updated:
        print(f"\nUpdated wiki path to `{wiki_dir}` in: {', '.join(updated)}")
