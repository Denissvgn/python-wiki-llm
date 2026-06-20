from __future__ import annotations

import json
import re
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from collections.abc import Iterator
from pathlib import Path

from .extract_cmd import get_call_graph, get_docker_inventory, get_inventory_result
from .extract_cmd import resolve_call_edges
from .bootstrap_cmd import build_module_page_map, build_entity_page_map
from ..config import validate_path
from ..services.data_flow import analyze_data_flow
from ..services.dependencies import analyze_dependencies
from ..services.entrypoints import build_flow, get_entry_points, read_console_scripts
from ..services.inventory_cache import (
    InventoryCacheOptions,
    InventoryCacheStats,
    format_cache_stats,
)
from ..services.io import read_md
from ..services.plugins import PluginError, iter_components, load_entry_point
from ..services.source_snapshot import build_source_snapshot
from ..services.team import build_team_issues

# basic regex for [text](url)
LINK_RE = re.compile(r"\[.+?\]\((.+?)\)")

_PROFILE_PHASES = [
    "inventory",
    "docker_inventory",
    "page_index",
    "links",
    "orphans",
    "entities",
    "modules",
    "workflows",
    "flows",
    "data_flow",
    "dependencies",
    "infrastructure",
    "strict",
    "plugins",
    "team",
]


class _LintProfiler:
    def __init__(self) -> None:
        self._started = time.perf_counter()
        self._durations = {name: 0.0 for name in _PROFILE_PHASES}

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self._durations[name] = self._durations.get(name, 0.0) + (
                time.perf_counter() - started
            )

    def to_dict(self) -> dict:
        return {
            "total_ms": int(round((time.perf_counter() - self._started) * 1000)),
            "phases": [
                {
                    "name": name,
                    "duration_ms": int(round(self._durations.get(name, 0.0) * 1000)),
                }
                for name in _PROFILE_PHASES
            ],
        }


@contextmanager
def _profile_phase(profiler: _LintProfiler | None, name: str) -> Iterator[None]:
    if profiler is None:
        yield
        return
    with profiler.phase(name):
        yield


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
    diagnostics: list[LintIssue] = field(default_factory=list)
    cache_stats: InventoryCacheStats | None = None

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


@dataclass(frozen=True)
class _WikiPageIndex:
    pages: list[Path]
    links_by_page: dict[Path, list[str]]


@dataclass(frozen=True)
class _LintInputs:
    deep_inventory: dict
    docker_inventory: dict
    page_index: _WikiPageIndex


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
            return path.resolve().relative_to(wiki_dir.resolve()).parts[:1] == (
                "legacy",
            )
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


def _collect_documented_flows(wiki_dir: Path) -> set[str]:
    """Return the set of user-flow page stems (entry-point ids)."""
    flows_dir = wiki_dir / "flows"
    if not flows_dir.exists():
        return set()
    return {p.stem for p in flows_dir.glob("*.md")}


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
    return {
        f.replace("\\", "/").replace("/", "_").replace(".", "_") for f in docker_inv
    }


def _add(
    report: LintReport,
    category: str,
    message: str,
    *,
    path: str | None = None,
    target: str | None = None,
) -> None:
    report.issues.append(
        LintIssue(category=category, message=message, path=path, target=target)
    )


def _diagnose(
    report: LintReport,
    category: str,
    message: str,
    *,
    path: str | None = None,
    target: str | None = None,
    severity: str = "warning",
) -> None:
    report.diagnostics.append(
        LintIssue(
            category=category,
            message=message,
            severity=severity,
            path=path,
            target=target,
        )
    )


def _coerce_plugin_issue(raw: object, component_ref: str) -> LintIssue:
    if isinstance(raw, LintIssue):
        return raw
    if isinstance(raw, dict):
        category = str(raw.get("category") or f"plugin:{component_ref}")
        message = str(raw.get("message") or "Plugin lint rule reported an issue.")
        severity = str(raw.get("severity") or "error")
        path = raw.get("path")
        target = raw.get("target")
        return LintIssue(
            category=category,
            message=message,
            severity=severity,
            path=str(path) if path is not None else None,
            target=str(target) if target is not None else None,
        )
    return LintIssue(
        category=f"plugin:{component_ref}",
        message=f"Plugin lint rule returned unsupported issue type: {type(raw).__name__}",
    )


def _run_plugin_lint_rules(
    report: LintReport,
    wiki_dir: Path,
    src_dir: str,
    inventory: dict,
    pages: list[Path],
) -> None:
    for component in iter_components("lint_rule"):
        component_ref = component["ref"]
        try:
            rule = load_entry_point(component["entry_point"])
            issues = rule(wiki_dir, src_dir, inventory, pages)
        except (PluginError, Exception) as exc:
            _add(
                report,
                "plugin_lint_rule",
                f"Plugin lint rule {component_ref} failed: {exc}",
                target=component_ref,
            )
            continue

        if issues is None:
            continue
        if not isinstance(issues, list):
            issues = [issues]
        for issue in issues:
            report.issues.append(_coerce_plugin_issue(issue, component_ref))


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


def _check_sync_manifest(
    report: LintReport,
    wiki_dir: Path,
    src_dir: str,
    inventory: dict | None = None,
) -> None:
    from .sync_cmd import MANIFEST_FILENAME, SyncManifest, _compute_diff

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
        if inventory is None:
            inventory_result = get_inventory_result(src_dir, deep=True)
            if inventory_result.failed:
                messages = "; ".join(
                    f"{status.language}: {status.message}"
                    for status in inventory_result.failed
                )
                raise RuntimeError(messages)
            inventory = inventory_result.inventory
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
            f"{len(diff.renamed_entity_pages)} renamed entity pages",
            f"{len(diff.renamed_module_pages)} renamed module pages",
        ]
        _add(
            report,
            "sync_manifest",
            "Sync manifest is stale against current inventory: "
            + ", ".join(parts)
            + ".",
            path=MANIFEST_FILENAME,
        )


def _collect_lint_inputs(
    report: LintReport,
    wiki_path: Path,
    src_dir: str,
    profiler: _LintProfiler | None,
    cache_options: InventoryCacheOptions | None,
    parallel_jobs: int,
) -> _LintInputs | None:
    with _profile_phase(profiler, "inventory"):
        source_snapshot = build_source_snapshot(src_dir)
        inventory_result = get_inventory_result(
            src_dir,
            deep=True,
            source_snapshot=source_snapshot,
            cache_options=cache_options,
            parallel_jobs=parallel_jobs,
        )
        if cache_options is not None and cache_options.stats_enabled:
            report.cache_stats = inventory_result.cache_stats
        if inventory_result.failed:
            _add_extractor_failures(report, inventory_result)
            return None
        deep_inventory = inventory_result.inventory

    with _profile_phase(profiler, "docker_inventory"):
        docker_inventory = get_docker_inventory(
            src_dir, source_snapshot=source_snapshot
        )

    with _profile_phase(profiler, "page_index"):
        page_index = _build_page_index(wiki_path)

    return _LintInputs(deep_inventory, docker_inventory, page_index)


def _build_page_index(wiki_path: Path) -> _WikiPageIndex:
    pages = [
        page for page in wiki_path.rglob("*.md") if not _is_legacy_page(page, wiki_path)
    ]
    page_content = {page: read_md(page) for page in pages}
    links_by_page = {
        page: LINK_RE.findall(content) for page, content in page_content.items()
    }
    return _WikiPageIndex(pages, links_by_page)


def _check_broken_links(
    report: LintReport,
    wiki_path: Path,
    page_index: _WikiPageIndex,
) -> None:
    for page in page_index.pages:
        for link in page_index.links_by_page.get(page, []):
            local_path = _local_link_path(link)
            if local_path is None:
                continue
            target = (page.parent / local_path).resolve()
            if not target.exists():
                rel = str(page.relative_to(wiki_path))
                _add(
                    report,
                    "broken_links",
                    f"Broken link in {rel} -> {link}",
                    path=rel,
                    target=link,
                )


def _check_orphan_pages(
    report: LintReport,
    wiki_path: Path,
    page_index: _WikiPageIndex,
) -> None:
    index_path = wiki_path / "index.md"
    referenced_files: set[Path] = set()
    if index_path.exists():
        index_links = page_index.links_by_page.get(index_path, [])

        for link in index_links:
            local_path = _local_link_path(link)
            if local_path is not None:
                target = (index_path.parent / local_path).resolve()
                referenced_files.add(target)

        for page in page_index.pages:
            if page.name in ["index.md", "log.md"]:
                continue
            if page.resolve() not in referenced_files:
                rel = str(page.relative_to(wiki_path))
                _add(
                    report,
                    "orphan_pages",
                    f"Orphan page (not in index.md): {rel}",
                    path=rel,
                )


def _check_entity_coverage(
    report: LintReport, wiki_path: Path, deep_inventory: dict
) -> None:
    documented_entities = _collect_documented_entities(wiki_path)
    code_classes = _inventory_code_classes(deep_inventory)

    undocumented = code_classes - documented_entities
    stale = documented_entities - code_classes

    if undocumented:
        for name in sorted(undocumented):
            _add(
                report,
                "undocumented_classes",
                f"Undocumented class (in code, not in wiki): {name}",
                target=name,
            )

    if stale:
        for name in sorted(stale):
            _add(
                report,
                "stale_entities",
                f"Stale entity (in wiki, not in code): {name}",
                target=name,
            )


def _check_module_coverage(
    report: LintReport, wiki_path: Path, deep_inventory: dict
) -> None:
    documented_modules = _collect_documented_modules(wiki_path)
    code_modules = _inventory_code_modules(deep_inventory)

    undoc_mods = code_modules - documented_modules
    stale_mods = documented_modules - code_modules

    if undoc_mods:
        for name in sorted(undoc_mods):
            _add(
                report,
                "undocumented_modules",
                f"Undocumented module (in code, not in wiki): {name}",
                target=name,
            )

    if stale_mods:
        for name in sorted(stale_mods):
            _add(
                report,
                "stale_modules",
                f"Stale module (in wiki, not in code): {name}",
                target=name,
            )


def _check_workflow_coverage(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    page_index: _WikiPageIndex,
) -> None:
    documented_workflows = _collect_documented_workflows(wiki_path)

    workflows_dir = wiki_path / "workflows"
    if workflows_dir.exists():
        for wf_page in workflows_dir.glob("*.md"):
            for link in page_index.links_by_page.get(wf_page, []):
                local_path = _local_link_path(link)
                if local_path is None:
                    continue
                target = (wf_page.parent / local_path).resolve()
                if not target.exists():
                    _diagnose(
                        report,
                        "broken_workflow_links",
                        f"Broken link in workflow {wf_page.stem} -> {link}",
                        path=str(wf_page.relative_to(wiki_path)),
                        target=link,
                    )

    detected_workflows = set(get_call_graph(deep_inventory).keys())
    missing_wf = detected_workflows - documented_workflows
    if missing_wf:
        for name in sorted(missing_wf):
            _add(
                report,
                "missing_workflows",
                f"Missing workflow (detected in code, no wiki page): {name}",
                target=name,
            )


def _check_flow_coverage(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    src_dir: str,
) -> None:
    """Flag user-flow pages whose entry point no longer exists in the code.

    Only stale pages are reported (missing flows are not, since flow generation
    is opt-out via ``--skip-flows``). Broken links and orphan pages in ``flows/``
    are already covered by the global link and orphan checks.
    """
    documented_flows = _collect_documented_flows(wiki_path)
    if not documented_flows:
        return
    detected_flows = {
        ep["id"]
        for ep in get_entry_points(
            deep_inventory, console_scripts=read_console_scripts(src_dir)
        )
    }
    for name in sorted(documented_flows - detected_flows):
        _add(
            report,
            "stale_flows",
            f"Stale user-flow page (entry point removed): {name}",
            target=name,
        )


def _check_data_flow_diagnostics(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    src_dir: str,
) -> None:
    documented_flows = _collect_documented_flows(wiki_path)
    if not documented_flows:
        return

    edges = resolve_call_edges(deep_inventory)
    for entry_point in get_entry_points(
        deep_inventory, console_scripts=read_console_scripts(src_dir)
    ):
        if entry_point["id"] not in documented_flows:
            continue
        data_flow = analyze_data_flow(
            deep_inventory, build_flow(entry_point, edges), edges
        )
        for gap in data_flow["gaps"]:
            line = gap.get("line")
            location = f" line {line}" if line else ""
            _diagnose(
                report,
                "data_flow_gaps",
                (
                    f"Data-flow gap in {entry_point['id']}: {gap['kind']} "
                    f"{gap['step']} -> {gap['target']}{location}"
                ),
                target=entry_point["id"],
            )


def _check_dependency_coverage(
    report: LintReport,
    wiki_path: Path,
    deep_inventory: dict,
    src_dir: str,
) -> None:
    """Re-run dependency analysis for the architecture pages and warn on drift.

    Only runs when ``dependencies.md`` / ``load-order.md`` exist (projects that
    opted out via ``bootstrap --skip-dependencies`` are left untouched). Import
    cycles and undeclared / unused external dependencies surface as non-failing
    **diagnostics** so they never break ``ci-check`` on their own; a page that
    exists but whose analysis found no modules is flagged **stale** as a hard
    issue. Reuses the already-built deep inventory, so no extra extraction pass
    runs (DL-010).
    """
    pages = [
        p
        for p in (wiki_path / "dependencies.md", wiki_path / "load-order.md")
        if p.exists()
    ]
    if not pages:
        return

    analysis = analyze_dependencies(deep_inventory, src_dir)
    if not analysis["graph"]["nodes"]:
        for page in pages:
            _add(
                report,
                "stale_dependencies",
                f"Stale architecture page (no modules detected in source): {page.stem}",
                path=page.name,
                target=page.stem,
            )
        return

    for cycle in analysis["cycles"]:
        _diagnose(
            report,
            "dependency_cycles",
            "Import cycle: " + " ⇄ ".join(cycle),
        )
    for language, data in sorted(analysis["reconciliation"]["languages"].items()):
        for package in data["undeclared"]:
            _diagnose(
                report,
                "undeclared_dependencies",
                f"Undeclared {language} dependency (imported, not declared): {package}",
                target=package,
            )
        for package in data["unused"]:
            _diagnose(
                report,
                "unused_dependencies",
                f"Unused {language} dependency (declared, not imported): {package}",
                target=package,
            )


def _check_infrastructure_coverage(
    report: LintReport,
    wiki_path: Path,
    docker_inventory: dict,
) -> None:
    documented_infra = _collect_documented_infrastructure(wiki_path)
    code_docker = _collect_docker_files(docker_inventory)

    undoc_infra = code_docker - documented_infra
    stale_infra = documented_infra - code_docker

    if undoc_infra:
        for name in sorted(undoc_infra):
            _add(
                report,
                "undocumented_infrastructure",
                f"Undocumented Docker file (in source, not in wiki): {name}",
                target=name,
            )

    if stale_infra:
        for name in sorted(stale_infra):
            _add(
                report,
                "stale_infrastructure",
                f"Stale infrastructure page (in wiki, source file removed): {name}",
                target=name,
            )


def _check_team_issues(
    report: LintReport,
    wiki_path: Path,
    src_dir: str,
    inputs: _LintInputs,
) -> None:
    for issue in build_team_issues(
        wiki_path,
        src_dir,
        inputs.deep_inventory,
        inputs.page_index.pages,
        docker_inventory=inputs.docker_inventory,
    ):
        report.issues.append(_coerce_plugin_issue(issue, "team"))


def _run_report_checks(
    report: LintReport,
    wiki_path: Path,
    src_dir: str,
    strict: bool,
    profiler: _LintProfiler | None,
    inputs: _LintInputs,
) -> None:
    with _profile_phase(profiler, "links"):
        _check_broken_links(report, wiki_path, inputs.page_index)
    with _profile_phase(profiler, "orphans"):
        _check_orphan_pages(report, wiki_path, inputs.page_index)
    with _profile_phase(profiler, "entities"):
        _check_entity_coverage(report, wiki_path, inputs.deep_inventory)
    with _profile_phase(profiler, "modules"):
        _check_module_coverage(report, wiki_path, inputs.deep_inventory)
    with _profile_phase(profiler, "workflows"):
        _check_workflow_coverage(
            report, wiki_path, inputs.deep_inventory, inputs.page_index
        )
    with _profile_phase(profiler, "flows"):
        _check_flow_coverage(report, wiki_path, inputs.deep_inventory, src_dir)
    with _profile_phase(profiler, "data_flow"):
        _check_data_flow_diagnostics(report, wiki_path, inputs.deep_inventory, src_dir)
    with _profile_phase(profiler, "dependencies"):
        _check_dependency_coverage(report, wiki_path, inputs.deep_inventory, src_dir)
    with _profile_phase(profiler, "infrastructure"):
        _check_infrastructure_coverage(report, wiki_path, inputs.docker_inventory)
    with _profile_phase(profiler, "strict"):
        if strict:
            _check_required_structure(report, wiki_path)
            _check_sync_manifest(report, wiki_path, src_dir, inputs.deep_inventory)
    with _profile_phase(profiler, "plugins"):
        _run_plugin_lint_rules(
            report,
            wiki_path,
            src_dir,
            inputs.deep_inventory,
            inputs.page_index.pages,
        )
    with _profile_phase(profiler, "team"):
        _check_team_issues(report, wiki_path, src_dir, inputs)


def build_report(
    wiki_dir: str | Path,
    src_dir: str = ".",
    *,
    strict: bool = False,
    profiler: _LintProfiler | None = None,
    cache_options: InventoryCacheOptions | None = None,
    parallel_jobs: int = 1,
) -> LintReport:
    """Build a structured lint report without rendering or exiting."""
    wiki_path = Path(wiki_dir)
    report = LintReport(wiki_dir=str(wiki_path), src_dir=src_dir, strict=strict)
    if not wiki_path.exists():
        _add(
            report,
            "wiki_missing",
            f"Directory {wiki_path} does not exist.",
            path=str(wiki_path),
        )
        return report
    inputs = _collect_lint_inputs(
        report,
        wiki_path,
        src_dir,
        profiler,
        cache_options,
        parallel_jobs,
    )
    if inputs is None:
        return report
    _run_report_checks(report, wiki_path, src_dir, strict, profiler, inputs)
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


def _profile_report_to_dict(
    report: LintReport, profiler: _LintProfiler, *, include_cache: bool = False
) -> dict:
    payload = report_to_dict(report)
    payload["diagnostics"] = [asdict(diagnostic) for diagnostic in report.diagnostics]
    payload["profile"] = profiler.to_dict()
    if include_cache and report.cache_stats is not None:
        payload["cache"] = report.cache_stats.to_dict()
    return payload


def _add_extractor_failures(report: LintReport, inventory_result) -> None:
    for status in inventory_result.failed:
        detail = f": {status.message}" if status.message else ""
        _add(
            report,
            "extractor_failure",
            f"{status.language} extraction failed{detail}",
            target=status.language,
        )


def render_text(report: LintReport) -> str:
    grouped = report.by_category()
    diagnostic_groups: dict[str, list[LintIssue]] = {}
    for diagnostic in report.diagnostics:
        diagnostic_groups.setdefault(diagnostic.category, []).append(diagnostic)
    lines: list[str] = [f"Linting Wiki at: {report.wiki_dir}"]

    if grouped.get("wiki_missing"):
        for issue in grouped["wiki_missing"]:
            lines.append(f"Error: {issue.message}")
        lines.append(f"❌ Lint found {report.issue_count} issue(s).")
        return "\n".join(lines) + "\n"

    def emit_group(
        category: str,
        empty: str,
        found: str,
        prefix: str = "  ⚠️  ",
        *,
        only_if_present: bool = False,
    ) -> None:
        issues = grouped.get(category, []) + diagnostic_groups.get(category, [])
        if issues:
            for issue in issues:
                lines.append(f"{prefix}{issue.message}")
            lines.append(f"  {found.format(count=len(issues))}")
            lines.append("")
        elif not only_if_present:
            lines.append(f"  ✅ {empty}")
            lines.append("")

    if grouped.get("extractor_failure"):
        emit_group(
            "extractor_failure",
            "Source extraction completed.",
            "Found {count} source extraction failure(s).",
            prefix="  ❌ ",
        )
    emit_group(
        "broken_links",
        "No broken links.",
        "Found {count} broken link(s).",
        prefix="  ❌ ",
    )
    emit_group("orphan_pages", "No orphan pages.", "Found {count} orphan page(s).")
    emit_group(
        "undocumented_classes",
        "All classes documented.",
        "Found {count} undocumented class(es).",
    )
    emit_group(
        "stale_entities",
        "No stale entity pages.",
        "Found {count} stale entity page(s).",
    )
    emit_group(
        "undocumented_modules",
        "All modules documented.",
        "Found {count} undocumented module(s).",
    )
    emit_group(
        "stale_modules", "No stale module pages.", "Found {count} stale module page(s)."
    )
    emit_group(
        "broken_workflow_links",
        "No broken workflow links.",
        "Found {count} broken workflow link(s).",
    )
    emit_group(
        "missing_workflows",
        "All detected workflows documented.",
        "Found {count} missing workflow(s).",
    )
    emit_group(
        "undocumented_infrastructure",
        "All Docker/Compose files documented.",
        "Found {count} undocumented Docker file(s).",
    )
    emit_group(
        "stale_infrastructure",
        "No stale infrastructure pages.",
        "Found {count} stale infrastructure page(s).",
    )

    # Architecture-page checks are only meaningful when the pages exist, so they
    # stay quiet (no all-clear line) otherwise. Cycles / undeclared / unused are
    # warnings; stale architecture pages are hard issues.
    emit_group(
        "stale_dependencies",
        "No stale architecture pages.",
        "Found {count} stale architecture page(s).",
        prefix="  ❌ ",
        only_if_present=True,
    )
    emit_group(
        "dependency_cycles",
        "No import cycles.",
        "Found {count} import cycle(s).",
        only_if_present=True,
    )
    emit_group(
        "undeclared_dependencies",
        "No undeclared dependencies.",
        "Found {count} undeclared dependency(ies).",
        only_if_present=True,
    )
    emit_group(
        "unused_dependencies",
        "No unused dependencies.",
        "Found {count} unused dependency(ies).",
        only_if_present=True,
    )

    if report.strict:
        emit_group(
            "wiki_structure",
            "Required wiki structure present.",
            "Found {count} wiki structure issue(s).",
        )
        emit_group(
            "sync_manifest",
            "Sync manifest is fresh.",
            "Found {count} sync manifest issue(s).",
        )

    emit_group(
        "team_config",
        "Team config valid or not configured.",
        "Found {count} team config issue(s).",
    )
    emit_group(
        "team_plugin_requirement",
        "Team plugin requirements satisfied.",
        "Found {count} team plugin requirement issue(s).",
    )
    emit_group(
        "team_conventions",
        "Team conventions satisfied.",
        "Found {count} team convention issue(s).",
    )
    emit_group(
        "team_canonical_naming",
        "Team canonical naming satisfied.",
        "Found {count} team canonical naming issue(s).",
    )

    # ── Summary ───────────────────────────────────────────────────────
    if report.passed:
        lines.append("✅ Lint passed: wiki is fully consistent.")
    else:
        lines.append(f"❌ Lint found {report.issue_count} issue(s).")
    if report.cache_stats is not None:
        lines.extend(format_cache_stats(report.cache_stats))
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
        f"- Diagnostics: {len(report.diagnostics)}",
        "",
    ]
    if not report.issues and not report.diagnostics:
        lines.append("No issues found.")
        return "\n".join(lines) + "\n"

    if report.issues:
        lines.append("## Issues")
        lines.append("")
        for issue in report.issues:
            location = f" (`{issue.path}`)" if issue.path else ""
            lines.append(f"- **{issue.category}**{location}: {issue.message}")
        lines.append("")
    else:
        lines.append("No issues found.")
        lines.append("")

    if report.diagnostics:
        lines.append("## Diagnostics")
        lines.append("")
        for diagnostic in report.diagnostics:
            location = f" (`{diagnostic.path}`)" if diagnostic.path else ""
            severity = diagnostic.severity or "warning"
            lines.append(
                f"- **{diagnostic.category}**{location} [{severity}]: "
                f"{diagnostic.message}"
            )
    return "\n".join(lines) + "\n"


def run(args):
    wiki_dir = Path(args.wiki_dir)
    src_dir = getattr(args, "src_dir", ".")
    strict = bool(getattr(args, "strict", False))
    profile = bool(getattr(args, "profile", False))
    cache_stats = bool(getattr(args, "cache_stats", False))
    validate_path(str(wiki_dir), "--wiki-dir")
    validate_path(src_dir, "--src-dir")

    profiler = _LintProfiler() if profile else None
    cache_options = InventoryCacheOptions(
        enabled=not bool(getattr(args, "no_cache", False)),
        rebuild=bool(getattr(args, "rebuild_cache", False)),
        cache_dir=getattr(args, "cache_dir", None),
        stats_enabled=cache_stats,
    )
    report = build_report(
        wiki_dir,
        src_dir,
        strict=strict,
        profiler=profiler,
        cache_options=cache_options,
        parallel_jobs=getattr(args, "jobs", 1),
    )
    if report.count("extractor_failure") and not profile:
        for issue in report.by_category().get("extractor_failure", []):
            print(f"Error: {issue.message}", file=sys.stderr)
        sys.exit(1)
    if profile and profiler is not None:
        print(
            json.dumps(
                _profile_report_to_dict(report, profiler, include_cache=cache_stats),
                indent=2,
                sort_keys=True,
            )
        )
    else:
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
