"""Tests for the canonical wiki surface registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki_cli.services import wiki_surface
from llm_wiki_cli.services.wiki_surface import PageKind, SurfaceRole


def _write(path: Path, content: str = "# Page\n\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_registry_contains_canonical_page_kinds_and_metadata():
    kinds = list(wiki_surface.iter_page_kinds())

    assert [entry.kind for entry in kinds] == [
        PageKind.INDEX,
        PageKind.LOG,
        PageKind.ENTITIES,
        PageKind.MODULES,
        PageKind.WORKFLOWS,
        PageKind.GUIDES,
        PageKind.FLOWS,
        PageKind.INFRASTRUCTURE,
        PageKind.DEPENDENCIES,
        PageKind.LOAD_ORDER,
    ]

    by_kind = {entry.kind: entry for entry in kinds}
    assert by_kind[PageKind.INDEX].label == "Index"
    assert by_kind[PageKind.INDEX].path_pattern == "index.md"
    assert by_kind[PageKind.INDEX].mcp_uri_kind == "index"
    assert by_kind[PageKind.INDEX].obsidian_mirror_dir is None
    assert by_kind[PageKind.INDEX].role is SurfaceRole.MIXED

    assert by_kind[PageKind.ENTITIES].label == "Entities"
    assert by_kind[PageKind.ENTITIES].path_pattern == "entities/{page_id}.md"
    assert by_kind[PageKind.ENTITIES].mcp_uri_kind == "entities"
    assert by_kind[PageKind.ENTITIES].obsidian_mirror_dir == "Entities"
    assert by_kind[PageKind.ENTITIES].role is SurfaceRole.SEMANTIC

    assert by_kind[PageKind.FLOWS].label == "User flows"
    assert by_kind[PageKind.FLOWS].path_pattern == "flows/{page_id}.md"
    assert by_kind[PageKind.FLOWS].obsidian_mirror_dir == "Flows"
    assert by_kind[PageKind.FLOWS].role is SurfaceRole.MIXED

    assert by_kind[PageKind.GUIDES].label == "Guides"
    assert by_kind[PageKind.GUIDES].path_pattern == "guides/{page_id}.md"
    assert by_kind[PageKind.GUIDES].mcp_uri_kind == "guides"
    assert by_kind[PageKind.GUIDES].obsidian_mirror_dir == "Guides"
    assert by_kind[PageKind.GUIDES].role is SurfaceRole.SEMANTIC

    assert by_kind[PageKind.DEPENDENCIES].label == "Dependencies"
    assert by_kind[PageKind.DEPENDENCIES].path_pattern == "dependencies.md"
    assert by_kind[PageKind.DEPENDENCIES].mcp_uri_kind == "dependencies"
    assert by_kind[PageKind.DEPENDENCIES].obsidian_mirror_dir is None
    assert by_kind[PageKind.DEPENDENCIES].role is SurfaceRole.MIXED


def test_registry_helpers_filter_roots_and_directory_kinds():
    assert [entry.kind for entry in wiki_surface.iter_root_pages()] == [
        PageKind.INDEX,
        PageKind.LOG,
        PageKind.DEPENDENCIES,
        PageKind.LOAD_ORDER,
    ]
    assert [entry.kind for entry in wiki_surface.iter_directory_kinds()] == [
        PageKind.ENTITIES,
        PageKind.MODULES,
        PageKind.WORKFLOWS,
        PageKind.GUIDES,
        PageKind.FLOWS,
        PageKind.INFRASTRUCTURE,
    ]


def test_asset_surface_is_agent_owned_and_never_generated():
    surface = wiki_surface.asset_surface()

    assert surface.label == "Assets"
    assert surface.directory == "assets"
    assert surface.path_pattern == "assets/<surface>/<page-stem>/<name>.<ext>"
    assert surface.role is SurfaceRole.SEMANTIC
    assert surface.generated is False
    assert surface.layout == "mirrored-page-path"


def test_canonical_paths_and_mcp_uris_are_posix():
    assert wiki_surface.canonical_path(PageKind.INDEX) == "index.md"
    assert wiki_surface.canonical_path(PageKind.DEPENDENCIES) == "dependencies.md"
    assert (
        wiki_surface.canonical_path(PageKind.MODULES, "pkg.module")
        == "modules/pkg.module.md"
    )
    assert wiki_surface.canonical_path(
        PageKind.INFRASTRUCTURE, "docker_Dockerfile"
    ) == ("infrastructure/docker_Dockerfile.md")
    assert (
        wiki_surface.canonical_path(PageKind.GUIDES, "operator-onboarding")
        == "guides/operator-onboarding.md"
    )

    assert wiki_surface.mcp_uri(PageKind.INDEX) == "llm-wiki://index"
    assert wiki_surface.mcp_uri(PageKind.LOAD_ORDER) == "llm-wiki://load-order"
    assert (
        wiki_surface.mcp_uri(PageKind.MODULES, "pkg.module")
        == "llm-wiki://modules/pkg.module"
    )
    assert (
        wiki_surface.mcp_uri(PageKind.GUIDES, "operator-onboarding")
        == "llm-wiki://guides/operator-onboarding"
    )


def test_page_id_validation_rejects_unsafe_ids():
    for page_id in ["User", "pkg.module", "docker_Dockerfile", "api-run", "flow_1"]:
        assert wiki_surface.is_safe_page_id(page_id)

    for page_id in [
        "",
        "../User",
        "pkg/module",
        "bad\\name",
        "two..dots",
        "space name",
        ".gitkeep",
    ]:
        assert not wiki_surface.is_safe_page_id(page_id)

    with pytest.raises(wiki_surface.WikiSurfaceError, match="page id is required"):
        wiki_surface.canonical_path(PageKind.MODULES)

    with pytest.raises(wiki_surface.WikiSurfaceError, match="Unsafe wiki page id"):
        wiki_surface.mcp_uri(PageKind.MODULES, "../models")

    with pytest.raises(
        wiki_surface.WikiSurfaceError, match="does not accept a page id"
    ):
        wiki_surface.canonical_path(PageKind.INDEX, "extra")


def test_collect_wiki_pages_handles_old_and_new_layouts_deterministically(tmp_path):
    wiki = tmp_path / "docs" / "llm_wiki"
    _write(wiki / "index.md")
    _write(wiki / "log.md")
    _write(wiki / "dependencies.md")
    _write(wiki / "load-order.md")
    _write(wiki / "entities" / "beta.md")
    _write(wiki / "entities" / "Alpha.md")
    _write(wiki / "entities" / "gamma.md")
    _write(wiki / "modules" / "models.py.md")
    _write(wiki / "workflows" / "signup.md")
    _write(wiki / "guides" / "operator-onboarding.md")
    _write(wiki / "flows" / "api-run.md")
    _write(wiki / "infrastructure" / "Dockerfile.md")

    _write(wiki / "legacy" / "Old.md")
    _write(wiki / "modules" / ".gitkeep")
    _write(wiki / "modules" / "notes.txt")
    _write(wiki / "modules" / "bad/name.md")
    _write(wiki / "modules" / "bad name.md")

    pages = wiki_surface.collect_wiki_pages(wiki)

    assert [(page.kind, page.page_id, page.relative_path) for page in pages] == [
        (PageKind.INDEX, "index", "index.md"),
        (PageKind.LOG, "log", "log.md"),
        (PageKind.ENTITIES, "Alpha", "entities/Alpha.md"),
        (PageKind.ENTITIES, "beta", "entities/beta.md"),
        (PageKind.ENTITIES, "gamma", "entities/gamma.md"),
        (PageKind.MODULES, "models.py", "modules/models.py.md"),
        (PageKind.WORKFLOWS, "signup", "workflows/signup.md"),
        (PageKind.GUIDES, "operator-onboarding", "guides/operator-onboarding.md"),
        (PageKind.FLOWS, "api-run", "flows/api-run.md"),
        (PageKind.INFRASTRUCTURE, "Dockerfile", "infrastructure/Dockerfile.md"),
        (PageKind.DEPENDENCIES, "dependencies", "dependencies.md"),
        (PageKind.LOAD_ORDER, "load-order", "load-order.md"),
    ]
    assert all("\\" not in page.relative_path for page in pages)
    assert all(page.path.is_absolute() for page in pages)
    assert pages[5].mcp_uri == "llm-wiki://modules/models.py"


def test_collect_wiki_pages_accepts_legacy_layout_without_optional_surfaces(tmp_path):
    wiki = tmp_path / "docs" / "llm_wiki"
    _write(wiki / "index.md")
    _write(wiki / "entities" / "User.md")
    _write(wiki / "modules" / "models.md")

    assert [
        (page.kind, page.relative_path)
        for page in wiki_surface.collect_wiki_pages(wiki)
    ] == [
        (PageKind.INDEX, "index.md"),
        (PageKind.ENTITIES, "entities/User.md"),
        (PageKind.MODULES, "modules/models.md"),
    ]
