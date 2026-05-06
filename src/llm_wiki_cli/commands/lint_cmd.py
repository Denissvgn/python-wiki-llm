from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from .extract_cmd import get_call_graph, get_docker_inventory, get_inventory_result, print_inventory_failures
from .bootstrap_cmd import build_module_page_map, build_entity_page_map
from ..config import validate_path
from ..services.io import read_md

# basic regex for [text](url)
LINK_RE = re.compile(r'\[.+?\]\((.+?)\)')


def _local_link_path(link: str) -> str | None:
    """Return the file portion of a local markdown link, or None if ignored."""
    if link.startswith(("http://", "https://", "mailto:", "#")):
        return None
    base, _sep, _anchor = link.partition("#")
    if not base:
        return None
    return base


def _is_legacy_page(path: Path, wiki_dir: Path) -> bool:
    """Return True for archived migration pages that lint should ignore."""
    try:
        return path.relative_to(wiki_dir).parts[:1] == ("legacy",)
    except ValueError:
        try:
            return path.resolve().relative_to(wiki_dir.resolve()).parts[:1] == ("legacy",)
        except ValueError:
            return False


def _collect_documented_entities(wiki_dir: Path) -> set[str]:
    """Return the set of entity names that have wiki pages."""
    entities_dir = wiki_dir / "entities"
    if not entities_dir.exists():
        return set()
    return {p.stem for p in entities_dir.glob("*.md")}


def _collect_code_classes(inventory_or_src_dir) -> set[str]:
    """Return the set of entity page names found by AST scanning.

    Uses collision-aware naming so that duplicate class names across
    different modules are qualified (e.g. ``parser_Parser``).
    """
    inventory = (
        inventory_or_src_dir
        if isinstance(inventory_or_src_dir, dict)
        else get_inventory_result(inventory_or_src_dir).inventory
    )
    entity_map = build_entity_page_map(inventory)
    return set(entity_map.values())


def _collect_documented_modules(wiki_dir: Path) -> set[str]:
    """Return the set of module names that have wiki pages."""
    modules_dir = wiki_dir / "modules"
    if not modules_dir.exists():
        return set()
    return {p.stem for p in modules_dir.glob("*.md")}


def _collect_code_modules(inventory_or_src_dir) -> set[str]:
    """Return the set of module page names with tracked components.

    Uses collision-aware naming so that duplicate file stems across
    different directories are qualified (e.g. ``pkg_a_cli``).
    """
    inventory = (
        inventory_or_src_dir
        if isinstance(inventory_or_src_dir, dict)
        else get_inventory_result(inventory_or_src_dir).inventory
    )
    mod_map = build_module_page_map(inventory)
    return set(mod_map.values())


def _collect_documented_workflows(wiki_dir: Path) -> set[str]:
    """Return the set of workflow names that have wiki pages."""
    workflows_dir = wiki_dir / "workflows"
    if not workflows_dir.exists():
        return set()
    return {p.stem for p in workflows_dir.glob("*.md")}


def _collect_documented_infrastructure(wiki_dir: Path) -> set[str]:
    """Return the set of infrastructure page names that have wiki pages."""
    infra_dir = wiki_dir / "infrastructure"
    if not infra_dir.exists():
        return set()
    return {p.stem for p in infra_dir.glob("*.md")}


def _collect_docker_files(docker_inventory_or_src_dir) -> set[str]:
    """Return the set of Docker/Compose file page-names found in source."""
    docker_inv = (
        docker_inventory_or_src_dir
        if isinstance(docker_inventory_or_src_dir, dict)
        else get_docker_inventory(docker_inventory_or_src_dir)
    )
    return {f.replace("\\", "/").replace("/", "_").replace(".", "_") for f in docker_inv}


def run(args):
    wiki_dir = Path(args.wiki_dir)
    src_dir = getattr(args, "src_dir", ".")
    validate_path(str(wiki_dir), "--wiki-dir")
    validate_path(src_dir, "--src-dir")
    issues = 0

    print(f"Linting Wiki at: {wiki_dir}")

    if not wiki_dir.exists():
        print(f"Error: Directory {wiki_dir} does not exist.")
        sys.exit(1)

    inventory_result = get_inventory_result(src_dir, deep=True)
    if inventory_result.failed:
        print_inventory_failures(inventory_result)
        sys.exit(1)
    deep_inventory = inventory_result.inventory
    docker_inventory = get_docker_inventory(src_dir)

    pages = [
        page for page in wiki_dir.rglob("*.md")
        if not _is_legacy_page(page, wiki_dir)
    ]

    # ── 1. Broken Links ──────────────────────────────────────────────
    broken_links = 0
    for page in pages:
        content = read_md(page)
        links = LINK_RE.findall(content)

        for link in links:
            local_path = _local_link_path(link)
            if local_path is None:
                continue
            target = (page.parent / local_path).resolve()
            if not target.exists():
                print(f"  ❌ Broken link in {page.relative_to(wiki_dir)} -> {link}")
                broken_links += 1

    issues += broken_links
    if broken_links:
        print(f"  Found {broken_links} broken link(s).\n")
    else:
        print("  ✅ No broken links.\n")

    # ── 2. Orphan Pages (not referenced in index.md) ─────────────────
    orphan_count = 0
    index_path = wiki_dir / "index.md"
    referenced_files: list[Path] = []
    if index_path.exists():
        index_content = read_md(index_path)
        index_links = LINK_RE.findall(index_content)

        for link in index_links:
            local_path = _local_link_path(link)
            if local_path is not None:
                target = (index_path.parent / local_path).resolve()
                referenced_files.append(target)

        for page in pages:
            if page.name in ["index.md", "log.md"]:
                continue
            if page.resolve() not in referenced_files:
                print(f"  ⚠️  Orphan page (not in index.md): {page.relative_to(wiki_dir)}")
                orphan_count += 1

    issues += orphan_count
    if orphan_count:
        print(f"  Found {orphan_count} orphan page(s).\n")
    else:
        print("  ✅ No orphan pages.\n")

    # ── 3. AST ↔ Wiki Cross-Reference (entities) ─────────────────────
    documented_entities = _collect_documented_entities(wiki_dir)
    code_classes = _collect_code_classes(deep_inventory)

    undocumented = code_classes - documented_entities
    stale = documented_entities - code_classes

    if undocumented:
        for name in sorted(undocumented):
            print(f"  ⚠️  Undocumented class (in code, not in wiki): {name}")
        issues += len(undocumented)
        print(f"  Found {len(undocumented)} undocumented class(es).\n")
    else:
        print("  ✅ All classes documented.\n")

    if stale:
        for name in sorted(stale):
            print(f"  ⚠️  Stale entity (in wiki, not in code): {name}")
        issues += len(stale)
        print(f"  Found {len(stale)} stale entity page(s).\n")
    else:
        print("  ✅ No stale entity pages.\n")

    # ── 4. AST ↔ Wiki Cross-Reference (modules) ──────────────────────
    documented_modules = _collect_documented_modules(wiki_dir)
    code_modules = _collect_code_modules(deep_inventory)

    undoc_mods = code_modules - documented_modules
    stale_mods = documented_modules - code_modules

    if undoc_mods:
        for name in sorted(undoc_mods):
            print(f"  ⚠️  Undocumented module (in code, not in wiki): {name}")
        issues += len(undoc_mods)
        print(f"  Found {len(undoc_mods)} undocumented module(s).\n")
    else:
        print("  ✅ All modules documented.\n")

    if stale_mods:
        for name in sorted(stale_mods):
            print(f"  ⚠️  Stale module (in wiki, not in code): {name}")
        issues += len(stale_mods)
        print(f"  Found {len(stale_mods)} stale module page(s).\n")
    else:
        print("  ✅ No stale module pages.\n")

    # ── 5. Workflow checks ────────────────────────────────────────────
    documented_workflows = _collect_documented_workflows(wiki_dir)

    # 5a. Check workflow pages reference existing modules
    workflows_dir = wiki_dir / "workflows"
    stale_wf = 0
    if workflows_dir.exists():
        for wf_page in workflows_dir.glob("*.md"):
            content = read_md(wf_page)
            links = LINK_RE.findall(content)
            for link in links:
                local_path = _local_link_path(link)
                if local_path is None:
                    continue
                target = (wf_page.parent / local_path).resolve()
                if not target.exists():
                    print(f"  ⚠️  Broken link in workflow {wf_page.stem} -> {link}")
                    stale_wf += 1

    if stale_wf:
        print(f"  Found {stale_wf} broken workflow link(s).\n")
    else:
        print("  ✅ No broken workflow links.\n")

    # 5b. Detect missing workflows (call chains with 3+ modules but no page)
    detected_workflows = set(get_call_graph(deep_inventory).keys())

    missing_wf = detected_workflows - documented_workflows
    if missing_wf:
        for name in sorted(missing_wf):
            print(f"  ⚠️  Missing workflow (detected in code, no wiki page): {name}")
        issues += len(missing_wf)
        print(f"  Found {len(missing_wf)} missing workflow(s).\n")
    else:
        print("  ✅ All detected workflows documented.\n")

    # ── 6. Infrastructure checks (Docker/Compose) ────────────────────
    documented_infra = _collect_documented_infrastructure(wiki_dir)
    code_docker = _collect_docker_files(docker_inventory)

    undoc_infra = code_docker - documented_infra
    stale_infra = documented_infra - code_docker

    if undoc_infra:
        for name in sorted(undoc_infra):
            print(f"  ⚠️  Undocumented Docker file (in source, not in wiki): {name}")
        issues += len(undoc_infra)
        print(f"  Found {len(undoc_infra)} undocumented Docker file(s).\n")
    else:
        print("  ✅ All Docker/Compose files documented.\n")

    if stale_infra:
        for name in sorted(stale_infra):
            print(f"  ⚠️  Stale infrastructure page (in wiki, source file removed): {name}")
        issues += len(stale_infra)
        print(f"  Found {len(stale_infra)} stale infrastructure page(s).\n")
    else:
        print("  ✅ No stale infrastructure pages.\n")

    # ── Summary ───────────────────────────────────────────────────────
    if issues == 0:
        print("✅ Lint passed: wiki is fully consistent.")
    else:
        print(f"❌ Lint found {issues} issue(s).")
        sys.exit(1)
