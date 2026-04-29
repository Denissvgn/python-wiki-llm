from __future__ import annotations

import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .extract_cmd import get_inventory, get_call_graph, get_docker_inventory
from .bootstrap_cmd import build_module_page_map, build_entity_page_map
from ..config import validate_path
from ..services.io import read_md

# basic regex for [text](url)
LINK_RE = re.compile(r'\[.+?\]\((.+?)\)')


@dataclass
class LintIssue:
    category: str
    message: str
    severity: str = "error"
    path: str | None = None
    target: str | None = None


@dataclass
class LintReport:
    wiki_dir: str
    src_dir: str
    strict: bool = False
    issues: list[LintIssue] = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def passed(self) -> bool:
        return self.issue_count == 0

    def by_category(self) -> dict[str, list[LintIssue]]:
        grouped: dict[str, list[LintIssue]] = {}
        for issue in self.issues:
            grouped.setdefault(issue.category, []).append(issue)
        return grouped

    def count(self, category: str) -> int:
        return len(self.by_category().get(category, []))


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


def _collect_code_classes(src_dir: str) -> set[str]:
    """Return the set of entity page names found by AST scanning.

    Uses collision-aware naming so that duplicate class names across
    different modules are qualified (e.g. ``parser_Parser``).
    """
    inventory = get_inventory(src_dir)
    entity_map = build_entity_page_map(inventory)
    return set(entity_map.values())


def _collect_documented_modules(wiki_dir: Path) -> set[str]:
    """Return the set of module names that have wiki pages."""
    modules_dir = wiki_dir / "modules"
    if not modules_dir.exists():
        return set()
    return {p.stem for p in modules_dir.glob("*.md")}


def _collect_code_modules(src_dir: str) -> set[str]:
    """Return the set of module page names with tracked components.

    Uses collision-aware naming so that duplicate file stems across
    different directories are qualified (e.g. ``pkg_a_cli``).
    """
    inventory = get_inventory(src_dir)
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


def _collect_docker_files(src_dir: str) -> set[str]:
    """Return the set of Docker/Compose file page-names found in source."""
    docker_inv = get_docker_inventory(src_dir)
    return {f.replace("\\", "/").replace("/", "_").replace(".", "_") for f in docker_inv}


def _add(report: LintReport, category: str, message: str, *, path: str | None = None, target: str | None = None) -> None:
    report.issues.append(LintIssue(category=category, message=message, path=path, target=target))


def _inventory_code_classes(inventory: dict) -> set[str]:
    entity_map = build_entity_page_map(inventory)
    return set(entity_map.values())


def _inventory_code_modules(inventory: dict) -> set[str]:
    mod_map = build_module_page_map(inventory)
    return set(mod_map.values())


def _check_required_structure(report: LintReport, wiki_dir: Path) -> None:
    required_files = ["index.md", "log.md"]
    required_dirs = ["entities", "modules", "workflows", "infrastructure"]
    for filename in required_files:
        path = wiki_dir / filename
        if not path.exists():
            _add(
                report,
                "wiki_structure",
                f"Missing required wiki file: {filename}",
                path=filename,
            )
    for dirname in required_dirs:
        path = wiki_dir / dirname
        if not path.is_dir():
            _add(
                report,
                "wiki_structure",
                f"Missing required wiki directory: {dirname}/",
                path=dirname,
            )


def _check_sync_manifest(report: LintReport, wiki_dir: Path, src_dir: str) -> None:
    from .sync_cmd import MANIFEST_FILENAME, SyncManifest, _compute_diff

    manifest_path = wiki_dir / MANIFEST_FILENAME
    try:
        manifest = SyncManifest.load(wiki_dir)
    except FileNotFoundError:
        _add(
            report,
            "sync_manifest",
            f"Missing sync manifest: {MANIFEST_FILENAME}. Run `llm-wiki bootstrap` or `llm-wiki sync`.",
            path=MANIFEST_FILENAME,
        )
        return
    except Exception as exc:
        _add(
            report,
            "sync_manifest",
            f"Invalid sync manifest {MANIFEST_FILENAME}: {exc}",
            path=MANIFEST_FILENAME,
        )
        return

    try:
        inventory = get_inventory(src_dir, deep=True)
        diff = _compute_diff(manifest, inventory, src_dir)
    except Exception as exc:
        _add(
            report,
            "sync_manifest",
            f"Could not verify sync manifest freshness: {exc}",
            path=MANIFEST_FILENAME,
        )
        return

    if diff.has_changes:
        parts = [
            f"{len(diff.new_files)} new",
            f"{len(diff.changed_files)} changed",
            f"{len(diff.removed_files)} removed",
            f"{len(diff.moved_entities)} moved",
        ]
        _add(
            report,
            "sync_manifest",
            "Sync manifest is stale against current inventory: " + ", ".join(parts) + ".",
            path=MANIFEST_FILENAME,
        )


def build_report(wiki_dir: str | Path, src_dir: str = ".", *, strict: bool = False) -> LintReport:
    """Build a structured lint report without rendering or exiting."""
    wiki_path = Path(wiki_dir)
    report = LintReport(wiki_dir=str(wiki_path), src_dir=src_dir, strict=strict)

    if not wiki_path.exists():
        _add(report, "wiki_missing", f"Directory {wiki_path} does not exist.", path=str(wiki_path))
        return report

    pages = [
        page for page in wiki_path.rglob("*.md")
        if not _is_legacy_page(page, wiki_path)
    ]

    # ── 1. Broken Links ──────────────────────────────────────────────
    for page in pages:
        content = read_md(page)
        links = LINK_RE.findall(content)

        for link in links:
            if link.startswith("http://") or link.startswith("https://"):
                continue
            target = (page.parent / link).resolve()
            if not target.exists():
                rel = str(page.relative_to(wiki_path))
                _add(report, "broken_links", f"Broken link in {rel} -> {link}", path=rel, target=link)

    # ── 2. Orphan Pages (not referenced in index.md) ─────────────────
    index_path = wiki_path / "index.md"
    referenced_files: list[Path] = []
    if index_path.exists():
        index_content = read_md(index_path)
        index_links = LINK_RE.findall(index_content)

        for link in index_links:
            if not link.startswith("http"):
                target = (index_path.parent / link).resolve()
                referenced_files.append(target)

        for page in pages:
            if page.name in ["index.md", "log.md"]:
                continue
            if page.resolve() not in referenced_files:
                rel = str(page.relative_to(wiki_path))
                _add(report, "orphan_pages", f"Orphan page (not in index.md): {rel}", path=rel)

    # ── 3. AST ↔ Wiki Cross-Reference (entities) ─────────────────────
    inventory = get_inventory(src_dir)
    documented_entities = _collect_documented_entities(wiki_path)
    code_classes = _inventory_code_classes(inventory)

    undocumented = code_classes - documented_entities
    stale = documented_entities - code_classes

    if undocumented:
        for name in sorted(undocumented):
            _add(report, "undocumented_classes", f"Undocumented class (in code, not in wiki): {name}", target=name)

    if stale:
        for name in sorted(stale):
            _add(report, "stale_entities", f"Stale entity (in wiki, not in code): {name}", target=name)

    # ── 4. AST ↔ Wiki Cross-Reference (modules) ──────────────────────
    documented_modules = _collect_documented_modules(wiki_path)
    code_modules = _inventory_code_modules(inventory)

    undoc_mods = code_modules - documented_modules
    stale_mods = documented_modules - code_modules

    if undoc_mods:
        for name in sorted(undoc_mods):
            _add(report, "undocumented_modules", f"Undocumented module (in code, not in wiki): {name}", target=name)

    if stale_mods:
        for name in sorted(stale_mods):
            _add(report, "stale_modules", f"Stale module (in wiki, not in code): {name}", target=name)

    # ── 5. Workflow checks ────────────────────────────────────────────
    documented_workflows = _collect_documented_workflows(wiki_path)

    # 5a. Check workflow pages reference existing modules
    workflows_dir = wiki_path / "workflows"
    if workflows_dir.exists():
        for wf_page in workflows_dir.glob("*.md"):
            content = read_md(wf_page)
            links = LINK_RE.findall(content)
            for link in links:
                if link.startswith("http"):
                    continue
                target = (wf_page.parent / link).resolve()
                if not target.exists():
                    _add(
                        report,
                        "broken_workflow_links",
                        f"Broken link in workflow {wf_page.stem} -> {link}",
                        path=str(wf_page.relative_to(wiki_path)),
                        target=link,
                    )

    # 5b. Detect missing workflows (call chains with 3+ modules but no page)
    try:
        deep_inventory = get_inventory(src_dir, deep=True)
        detected_workflows = set(get_call_graph(deep_inventory).keys())
    except Exception:
        detected_workflows = set()

    missing_wf = detected_workflows - documented_workflows
    if missing_wf:
        for name in sorted(missing_wf):
            _add(report, "missing_workflows", f"Missing workflow (detected in code, no wiki page): {name}", target=name)

    # ── 6. Infrastructure checks (Docker/Compose) ────────────────────
    documented_infra = _collect_documented_infrastructure(wiki_path)
    code_docker = _collect_docker_files(src_dir)

    undoc_infra = code_docker - documented_infra
    stale_infra = documented_infra - code_docker

    if undoc_infra:
        for name in sorted(undoc_infra):
            _add(report, "undocumented_infrastructure", f"Undocumented Docker file (in source, not in wiki): {name}", target=name)

    if stale_infra:
        for name in sorted(stale_infra):
            _add(report, "stale_infrastructure", f"Stale infrastructure page (in wiki, source file removed): {name}", target=name)

    if strict:
        _check_required_structure(report, wiki_path)
        _check_sync_manifest(report, wiki_path, src_dir)

    return report


def report_to_dict(report: LintReport) -> dict:
    return {
        "wiki_dir": report.wiki_dir,
        "src_dir": report.src_dir,
        "strict": report.strict,
        "ok": report.passed,
        "issue_count": report.issue_count,
        "issues": [asdict(issue) for issue in report.issues],
    }


def render_text(report: LintReport) -> str:
    grouped = report.by_category()
    lines: list[str] = [f"Linting Wiki at: {report.wiki_dir}"]

    if grouped.get("wiki_missing"):
        for issue in grouped["wiki_missing"]:
            lines.append(f"Error: {issue.message}")
        lines.append(f"❌ Lint found {report.issue_count} issue(s).")
        return "\n".join(lines) + "\n"

    def emit_group(category: str, empty: str, found: str, prefix: str = "  ⚠️  ") -> None:
        issues = grouped.get(category, [])
        if issues:
            for issue in issues:
                lines.append(f"{prefix}{issue.message}")
            lines.append(f"  {found.format(count=len(issues))}")
            lines.append("")
        else:
            lines.append(f"  ✅ {empty}")
            lines.append("")

    emit_group("broken_links", "No broken links.", "Found {count} broken link(s).", prefix="  ❌ ")
    emit_group("orphan_pages", "No orphan pages.", "Found {count} orphan page(s).")
    emit_group("undocumented_classes", "All classes documented.", "Found {count} undocumented class(es).")
    emit_group("stale_entities", "No stale entity pages.", "Found {count} stale entity page(s).")
    emit_group("undocumented_modules", "All modules documented.", "Found {count} undocumented module(s).")
    emit_group("stale_modules", "No stale module pages.", "Found {count} stale module page(s).")
    emit_group("broken_workflow_links", "No broken workflow links.", "Found {count} broken workflow link(s).")
    emit_group("missing_workflows", "All detected workflows documented.", "Found {count} missing workflow(s).")
    emit_group("undocumented_infrastructure", "All Docker/Compose files documented.", "Found {count} undocumented Docker file(s).")
    emit_group("stale_infrastructure", "No stale infrastructure pages.", "Found {count} stale infrastructure page(s).")

    if report.strict:
        emit_group("wiki_structure", "Required wiki structure present.", "Found {count} wiki structure issue(s).")
        emit_group("sync_manifest", "Sync manifest is fresh.", "Found {count} sync manifest issue(s).")

    # ── Summary ───────────────────────────────────────────────────────
    if report.passed:
        lines.append("✅ Lint passed: wiki is fully consistent.")
    else:
        lines.append(f"❌ Lint found {report.issue_count} issue(s).")
    return "\n".join(lines) + "\n"


def render_markdown(report: LintReport) -> str:
    status = "passed" if report.passed else "failed"
    lines = [
        "# LLM Wiki Validation Report",
        "",
        f"- Wiki: `{report.wiki_dir}`",
        f"- Source: `{report.src_dir}`",
        f"- Mode: `{'strict' if report.strict else 'normal'}`",
        f"- Result: **{status}**",
        f"- Issues: {report.issue_count}",
        "",
    ]
    if not report.issues:
        lines.append("No issues found.")
        return "\n".join(lines) + "\n"

    lines.append("## Issues")
    lines.append("")
    for issue in report.issues:
        location = f" (`{issue.path}`)" if issue.path else ""
        lines.append(f"- **{issue.category}**{location}: {issue.message}")
    return "\n".join(lines) + "\n"


def run(args):
    wiki_dir = Path(args.wiki_dir)
    src_dir = getattr(args, "src_dir", ".")
    strict = bool(getattr(args, "strict", False))
    validate_path(str(wiki_dir), "--wiki-dir")
    validate_path(src_dir, "--src-dir")

    report = build_report(wiki_dir, src_dir, strict=strict)
    print(render_text(report), end="")

    if strict:
        try:
            from ..services.metrics import record_validation_event
            record_validation_event(
                command="lint",
                passed=report.passed,
                issue_count=report.issue_count,
                strict=True,
                duration_ms=None,
                wiki_dir=str(wiki_dir),
                src_dir=src_dir,
            )
        except Exception:
            pass

    if not report.passed:
        sys.exit(1)
