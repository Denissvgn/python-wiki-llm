"""Regression tests for navigation across legacy and current wiki layouts."""

from __future__ import annotations

import types
from pathlib import Path

from llm_wiki_cli.commands import lint_cmd, status_cmd, sync_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services import mcp_server, obsidian


def _args(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _status_counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in output.splitlines():
        label, sep, rest = line.strip().partition(":")
        if not sep:
            continue
        value = rest.strip().split(maxsplit=1)[0] if rest.strip() else ""
        if value.isdigit():
            counts[label] = int(value)
    return counts


def _human_status_key(kind: str) -> str:
    return {
        "index": "Index",
        "log": "Log",
        "entities": "Entities",
        "modules": "Modules",
        "workflows": "Workflows",
        "guides": "Guides",
        "flows": "Flows",
        "infrastructure": "Infrastructure",
        "dependencies": "Dependencies",
        "load-order": "Load order",
        "architecture_pages": "Architecture pages",
    }[kind]


def _stub_lint_inputs(monkeypatch, layout) -> None:
    status = ExtractorStatus("python", "ok", len(layout.inventory))
    monkeypatch.setattr(
        lint_cmd,
        "get_inventory_result",
        lambda *args, **kwargs: InventoryResult(layout.inventory, {"python": status}),
    )
    monkeypatch.setattr(
        lint_cmd,
        "get_docker_inventory",
        lambda *args, **kwargs: layout.docker_inventory,
    )
    monkeypatch.setattr(
        lint_cmd,
        "analyze_dependencies",
        lambda *args, **kwargs: {
            "graph": {"nodes": ["models"], "edges": []},
            "cycles": [],
            "reconciliation": {"languages": {}},
        },
    )
    monkeypatch.setattr(
        lint_cmd,
        "analyze_data_flow",
        lambda *args, **kwargs: {"gaps": []},
    )


def test_mcp_navigation_resources_match_layout(navigation_wiki):
    service = mcp_server.McpWikiService(
        src_dir=str(navigation_wiki.src_dir),
        wiki_dir=str(navigation_wiki.wiki_dir),
    )

    resources = service.list_resources()
    uris = {resource["uri"] for resource in resources}
    status = service.get_status()

    assert navigation_wiki.expected_uris <= uris
    assert not (navigation_wiki.absent_uris & uris)
    assert status["pages"] == navigation_wiki.expected_counts

    index = service.read_resource("llm-wiki://index")
    assert index["metadata"]["path"] == "index.md"

    search = service.search_wiki("navigation entity", kinds=["entities"], limit=5)
    assert search["count"] == 1
    assert search["results"][0]["uri"] == "llm-wiki://entities/User"


def test_obsidian_navigation_export_matches_layout(navigation_wiki, monkeypatch):
    monkeypatch.setattr(
        obsidian,
        "get_inventory",
        lambda *args, **kwargs: navigation_wiki.inventory,
    )
    vault = navigation_wiki.src_dir / "vault"

    pages = obsidian.collect_wiki_pages(navigation_wiki.wiki_dir)
    canonical_paths = {page.canonical_rel for page in pages}

    report = obsidian.export_obsidian_vault(
        src_dir=str(navigation_wiki.src_dir),
        wiki_dir=navigation_wiki.wiki_dir,
        vault_dir=vault,
    )

    mirror_paths = {
        path.relative_to(vault).as_posix()
        for path in (vault / "LLM Wiki").rglob("*.md")
    }
    assert len(canonical_paths) == len(navigation_wiki.expected_uris)
    assert report.page_count == len(navigation_wiki.expected_uris)
    assert navigation_wiki.expected_mirror_paths <= mirror_paths
    assert not (navigation_wiki.absent_mirror_paths & mirror_paths)


def test_status_navigation_counts_match_layout(navigation_wiki, capsys):
    status_cmd.run(_args(wiki_dir=str(navigation_wiki.wiki_dir)))

    counts = _status_counts(capsys.readouterr().out)

    for kind, expected in navigation_wiki.expected_counts.items():
        assert counts[_human_status_key(kind)] == expected


def test_lint_navigation_smoke_accepts_layout(navigation_wiki, monkeypatch):
    _stub_lint_inputs(monkeypatch, navigation_wiki)

    report = lint_cmd.build_report(
        navigation_wiki.wiki_dir,
        str(navigation_wiki.src_dir),
        strict=False,
    )

    assert [
        (issue.category, issue.path, issue.target)
        for issue in report.issues
        if issue.category in {"broken_links", "orphan_pages"}
    ] == []


def test_sync_rebuild_index_preserves_layout_navigation(navigation_wiki):
    sync_cmd._rebuild_index(
        navigation_wiki.wiki_dir,
        navigation_wiki.inventory,
        str(navigation_wiki.src_dir),
    )

    index = (navigation_wiki.wiki_dir / "index.md").read_text(encoding="utf-8")

    assert "[User](entities/User.md)" in index
    assert "[models](modules/models.md)" in index
    if navigation_wiki.name == "legacy":
        assert "## User Flows" not in index
        assert "## Dependency Architecture" not in index
        assert "flows/api-run.md" not in index
        assert "dependencies.md" not in index
        assert "load-order.md" not in index
    else:
        assert "## User Flows" in index
        assert "[api-run](flows/api-run.md)" in index
        assert "## Dependency Architecture" in index
        assert "[Dependencies](dependencies.md)" in index
        assert "[Load order](load-order.md)" in index


def test_direct_layout_fixtures_document_old_and_current_shapes(
    legacy_navigation_wiki, current_navigation_wiki
):
    assert not (legacy_navigation_wiki.wiki_dir / "flows").exists()
    assert not (legacy_navigation_wiki.wiki_dir / "dependencies.md").exists()
    assert not (legacy_navigation_wiki.wiki_dir / "load-order.md").exists()

    for path in [
        current_navigation_wiki.wiki_dir / "flows" / "api-run.md",
        current_navigation_wiki.wiki_dir / "dependencies.md",
        current_navigation_wiki.wiki_dir / "load-order.md",
    ]:
        assert path.exists(), Path(path)
