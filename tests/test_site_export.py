"""Tests for the pure static-site mirror export service."""

from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.site_export import (
    SITE_PUBLICATION_MARKER,
    SITE_PUBLICATION_RECEIPT,
    SITE_PUBLICATION_SCHEMA_VERSION,
    SiteExportError,
    SiteExportOperation,
    SiteExportReport,
    check_site_hub,
    check_site_mirror,
    export_site_hub,
    export_site_mirror,
    render_report_text,
)


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _carry_publication_marker(out: Path, built: Path) -> None:
    _write(
        built / SITE_PUBLICATION_MARKER,
        (out / SITE_PUBLICATION_MARKER).read_text(encoding="utf-8"),
    )


def _write_wiki(root: Path) -> Path:
    wiki = root / "docs" / "llm_wiki"
    _write(
        wiki / "index.md",
        "\n".join(
            [
                "# LLM Wiki Index",
                "",
                "- [User](./entities/../entities/User.md)",
                "- [models](modules/models.md)",
                "- [external](https://example.com)",
                "- [anchor](#top)",
                "- ![Logo](assets/logo.png)",
                "- [missing](missing.md)",
                "",
            ]
        ),
    )
    _write(wiki / "log.md", "# Architectural Log\n\n")
    _write(wiki / "dependencies.md", "# Dependencies\n\n[models](modules/models.md)\n")
    _write(wiki / "load-order.md", "# Load order\n\n[models](modules/models.md)\n")
    _write(
        wiki / "entities" / "User.md",
        "\n".join(
            [
                '# "User": account',
                "",
                "See [models](../modules/./models.md#classes), "
                "[missing](../missing.md), "
                "[external](https://example.com), "
                "[section](#local), and ![image](../assets/logo.png).",
                "",
                "```text",
                "[models](../modules/./models.md)",
                "```",
                "",
                "```mermaid",
                "flowchart LR",
                "  U --> M",
                '  click M "../modules/models.md"',
                "```",
                "",
            ]
        ),
    )
    _write(
        wiki / "modules" / "models.md",
        "# models Module\n\nSee [User](../entities/User.md).\n",
    )
    _write(
        wiki / "workflows" / "signup.md",
        "# Signup\n\nUses [models](../modules/models.md).\n",
    )
    _write(
        wiki / "flows" / "checkout.md",
        "# Checkout\n\nUses [models](../modules/models.md).\n",
    )
    _write(
        wiki / "infrastructure" / "Dockerfile.md",
        "# Dockerfile\n\nCopies [models](../modules/models.md).\n",
    )
    _write(wiki / "legacy" / "Old.md", "# Old\n\n")
    _write(wiki / "random.md", "# Random\n\n")
    return wiki


def _write_hub_wiki(root: Path, source_id: str, title: str) -> Path:
    wiki = root / source_id
    _write(
        wiki / "index.md",
        f"# {title} Index\n\n- [Service](modules/service.md)\n",
    )
    _write(wiki / "log.md", f"# {title} Log\n\n")
    _write(wiki / "modules" / "service.md", f"# {title} Service\n\n")
    return wiki


def _write_usage_asset_wiki(root: Path) -> Path:
    wiki = _write_wiki(root)
    _write(
        wiki / "guides" / "tour.md",
        "# Tour\n\n"
        '![Home](../assets/guides/tour/home.png "Home")\n'
        '<video src="../assets/guides/tour/clip.webm"></video>\n',
    )
    (wiki / "assets" / "guides" / "tour").mkdir(parents=True)
    (wiki / "assets" / "guides" / "tour" / "home.png").write_bytes(b"png")
    (wiki / "assets" / "guides" / "tour" / "clip.webm").write_bytes(b"webm")
    return wiki


def _write_disambiguated_wiki(root: Path) -> Path:
    wiki = _write_wiki(root)
    _write(wiki / "entities" / "agent_ArtifactStore.md", "# ArtifactStore\n\n")
    _write(wiki / "entities" / "artifacts_ArtifactStore.md", "# ArtifactStore\n\n")
    _write(wiki / "modules" / "cmd_main.md", "# main Module\n\n")
    _write(wiki / "modules" / "server_main.md", "# main Module\n\n")
    return wiki


def _operation_paths(report) -> list[str]:
    return [
        Path(operation.path).as_posix()
        for operation in report.operations
        if operation.source != "publication-selection"
    ]


def test_export_writes_registry_pages_in_surface_order(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="plain")

    assert report.ok is True
    assert report.page_count == 9
    assert report.format == "plain"
    assert [
        operation.action
        for operation in report.operations
        if operation.source != "publication-selection"
    ] == ["write"] * 9
    assert {
        Path(operation.path).name
        for operation in report.operations
        if operation.source == "publication-selection"
    } == {SITE_PUBLICATION_MARKER, SITE_PUBLICATION_RECEIPT}
    assert _operation_paths(report) == [
        (out / "index.md").as_posix(),
        (out / "log.md").as_posix(),
        (out / "entities" / "User.md").as_posix(),
        (out / "modules" / "models.md").as_posix(),
        (out / "workflows" / "signup.md").as_posix(),
        (out / "flows" / "checkout.md").as_posix(),
        (out / "infrastructure" / "Dockerfile.md").as_posix(),
        (out / "dependencies.md").as_posix(),
        (out / "load-order.md").as_posix(),
    ]
    assert (out / "entities" / "User.md").exists()
    assert not (out / "legacy" / "Old.md").exists()
    assert not (out / "random.md").exists()

    second = export_site_mirror(wiki_dir=wiki, out_dir=out, format="plain")

    assert [
        operation.action
        for operation in second.operations
        if operation.source != "publication-selection"
    ] == ["unchanged"] * 9


def test_export_places_api_contracts_with_architecture_pages(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(wiki / "api-contracts.md", "# API contracts\n\n## Notes\n\nReviewed.\n")
    out = tmp_path / "site"

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Assistant",
    )

    assert report.page_count == 11
    assert (out / "api-contracts.md").is_file()
    mkdocs = (out / "mkdocs.yml").read_text(encoding="utf-8")
    architecture = mkdocs.split('  - "Architecture And Operations":', 1)[1]
    assert '"API contracts": "api-contracts.md"' in architecture


def test_export_includes_guides_surface_pages(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(
        wiki / "guides" / "operator-onboarding.md",
        "# Operator Onboarding\n\nUse [models](../modules/models.md).\n",
    )
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")

    assert report.page_count == 10
    assert (out / "guides" / "operator-onboarding.md").is_file()
    sidebar = json.loads((out / "sidebars.json").read_text(encoding="utf-8"))
    assert {
        "type": "category",
        "label": "Guides",
        "items": ["guides/operator-onboarding"],
    } in sidebar["llmWikiSidebar"]


def test_accepts_site_formats_and_rejects_unknown_format(tmp_path):
    wiki = _write_wiki(tmp_path)

    for site_format in ("plain", "mkdocs", "docusaurus"):
        report = export_site_mirror(
            wiki_dir=wiki,
            out_dir=tmp_path / f"site-{site_format}",
            format=site_format,
            dry_run=True,
        )
        assert report.format == site_format
        assert report.dry_run is True

    with pytest.raises(SiteExportError, match="Unsupported site export format"):
        export_site_mirror(wiki_dir=wiki, out_dir=tmp_path / "site-bad", format="html")


@pytest.mark.parametrize("site_format", ["plain", "mkdocs", "docusaurus"])
def test_export_copies_referenced_assets_for_every_format(tmp_path, site_format):
    wiki = _write_usage_asset_wiki(tmp_path)
    out = tmp_path / f"site-{site_format}"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format=site_format)

    assert report.asset_count == 2
    assert {operation.action for operation in report.asset_operations} == {"copy"}
    assert (out / "assets" / "guides" / "tour" / "home.png").read_bytes() == b"png"
    assert (out / "assets" / "guides" / "tour" / "clip.webm").read_bytes() == b"webm"
    guide = (out / "guides" / "tour.md").read_text(encoding="utf-8")
    assert '![Home](../assets/guides/tour/home.png "Home")' in guide
    assert '<video src="../assets/guides/tour/clip.webm"></video>' in guide
    assert all(
        "assets/guides/tour" in Path(operation.path).as_posix()
        for operation in report.asset_operations
    )


def test_export_copies_parenthesized_plain_and_reference_style_media(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(
        wiki / "guides" / "tour.md",
        "# Tour\n\n"
        "![Shot](../assets/guides/tour/shot(1).png)\n"
        "[Demo](../assets/guides/tour/demo(1).webm)\n"
        "![Reference][home]\n\n"
        '[home]: ../assets/guides/tour/home.png "Home"\n',
    )
    (wiki / "assets" / "guides" / "tour").mkdir(parents=True)
    (wiki / "assets" / "guides" / "tour" / "shot(1).png").write_bytes(b"shot")
    (wiki / "assets" / "guides" / "tour" / "demo(1).webm").write_bytes(b"demo")
    (wiki / "assets" / "guides" / "tour" / "home.png").write_bytes(b"home")
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="plain")

    assert report.asset_count == 3
    assert (out / "assets" / "guides" / "tour" / "shot(1).png").read_bytes() == b"shot"
    assert (out / "assets" / "guides" / "tour" / "demo(1).webm").read_bytes() == b"demo"
    assert (out / "assets" / "guides" / "tour" / "home.png").read_bytes() == b"home"


def test_export_copies_srcset_and_outside_assets_media(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(
        wiki / "guides" / "tour.md",
        "# Tour\n\n"
        "![Local](pic.png)\n"
        '<img alt="Responsive" src="../assets/guides/tour/fallback.png" '
        'srcset="../assets/guides/tour/small.png 1x, '
        '../assets/guides/tour/large.png 2x, https://cdn.example/remote.png 3x">\n',
    )
    (wiki / "guides" / "pic.png").write_bytes(b"local")
    (wiki / "assets" / "guides" / "tour").mkdir(parents=True)
    (wiki / "assets" / "guides" / "tour" / "fallback.png").write_bytes(b"fallback")
    (wiki / "assets" / "guides" / "tour" / "small.png").write_bytes(b"small")
    (wiki / "assets" / "guides" / "tour" / "large.png").write_bytes(b"large")
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="plain")

    assert report.asset_count == 4
    assert (out / "guides" / "pic.png").read_bytes() == b"local"
    assert (
        out / "assets" / "guides" / "tour" / "fallback.png"
    ).read_bytes() == b"fallback"
    assert (out / "assets" / "guides" / "tour" / "small.png").read_bytes() == b"small"
    assert (out / "assets" / "guides" / "tour" / "large.png").read_bytes() == b"large"


def test_export_dry_run_reports_asset_copies_without_mutating(tmp_path):
    wiki = _write_usage_asset_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, dry_run=True)

    assert report.asset_count == 2
    assert {operation.action for operation in report.asset_operations} == {"would_copy"}
    assert not out.exists()


def test_dry_run_reports_planned_writes_without_mutating(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, dry_run=True)

    assert report.dry_run is True
    assert report.to_dict()["dry_run"] is True
    assert {operation.action for operation in report.operations} == {"would_write"}
    assert not out.exists()


def test_knowledge_sidecars_do_not_change_site_output(tmp_path):
    wiki = _write_wiki(tmp_path)
    before_dir = tmp_path / "site-before"
    after_dir = tmp_path / "site-after"

    before_report = export_site_mirror(wiki_dir=wiki, out_dir=before_dir)
    before = {
        path.relative_to(before_dir).as_posix(): path.read_bytes()
        for path in sorted(before_dir.rglob("*"))
        if path.is_file()
    }

    _write(wiki / ".llm-wiki-knowledge.json", '{"schema_version": "future"}\n')
    _write(wiki / ".llm-wiki-manifest.json", '{"artifact_hashes": {}}\n')
    after_report = export_site_mirror(wiki_dir=wiki, out_dir=after_dir)
    after = {
        path.relative_to(after_dir).as_posix(): path.read_bytes()
        for path in sorted(after_dir.rglob("*"))
        if path.is_file()
    }

    assert after_report.page_count == before_report.page_count
    assert after == before
    assert not any("llm-wiki-knowledge" in path for path in after)


def test_rejects_source_overlap_unless_explicitly_allowed(tmp_path):
    wiki = _write_wiki(tmp_path)

    with pytest.raises(SiteExportError, match="overlaps the source wiki"):
        export_site_mirror(wiki_dir=wiki, out_dir=wiki)

    with pytest.raises(SiteExportError, match="overlaps the source wiki"):
        export_site_mirror(wiki_dir=wiki, out_dir=wiki / "site")

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=wiki / "site",
        allow_overwrite_source=True,
    )

    assert report.ok is True
    assert (wiki / "site" / "index.md").exists()


def test_front_matter_uses_safe_yaml_metadata(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        front_matter=True,
    )

    content = (out / "entities" / "User.md").read_text(encoding="utf-8")
    assert content.startswith(
        "\n".join(
            [
                "---",
                'title: "\\"User\\": account"',
                "llm_wiki:",
                '  kind: "entities"',
                '  id: "User"',
                '  role: "semantic"',
                '  canonical_path: "entities/User.md"',
                '  mcp_uri: "llm-wiki://entities/User"',
                "---",
                "",
                '# "User": account',
            ]
        )
    )


def test_mkdocs_export_writes_front_matter_with_surface_index_source(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(
        wiki / ".llm-wiki-surface.json",
        json.dumps(
            {
                "schema_version": "llm-wiki-surface-index/v1",
                "pages": [
                    {
                        "canonical_path": "entities/User.md",
                        "source_path": "src/models.py",
                    },
                    {
                        "canonical_path": "modules/models.md",
                        "source_path": "src/models.py",
                    },
                ],
            },
            sort_keys=True,
        )
        + "\n",
    )
    out = tmp_path / "site"

    export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")

    user_content = (out / "entities" / "User.md").read_text(encoding="utf-8")
    index_content = (out / "index.md").read_text(encoding="utf-8")
    assert user_content.startswith(
        "\n".join(
            [
                "---",
                'title: "\\"User\\": account"',
                "llm_wiki:",
                '  kind: "entities"',
                '  id: "User"',
                '  role: "semantic"',
                '  canonical_path: "entities/User.md"',
                '  mcp_uri: "llm-wiki://entities/User"',
                '  source_path: "src/models.py"',
                "---",
                "",
                '# "User": account',
            ]
        )
    )
    assert index_content.startswith("---\n")
    assert "  source_path:" not in index_content.split("---", 2)[1]
    assert 'click M "../modules/models.md"' in user_content


def test_mkdocs_export_writes_config_with_registry_ordered_nav(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")

    assert report.page_count == 9
    assert any(
        Path(operation.path) == out / "mkdocs.yml"
        for operation in report.operations
    )
    assert (out / "mkdocs.yml").read_text(encoding="utf-8") == "\n".join(
        [
            "# Generated by llm-wiki site export.",
            "# Mermaid code fences are preserved as Markdown. Configure a MkDocs",
            "# Mermaid plugin in your site environment to render diagrams.",
            'site_name: "LLM Wiki"',
            'docs_dir: "."',
            'site_dir: "../_site"',
            "nav:",
            '  - "LLM Wiki Index": "index.md"',
            '  - "Architectural Log": "log.md"',
            '  - "\\"User\\": account": "entities/User.md"',
            '  - "models Module": "modules/models.md"',
            '  - "Signup": "workflows/signup.md"',
            '  - "Checkout": "flows/checkout.md"',
            '  - "Dockerfile": "infrastructure/Dockerfile.md"',
            '  - "Dependencies": "dependencies.md"',
            '  - "Load order": "load-order.md"',
            "",
        ]
    )


def test_mkdocs_file_friendly_export_disables_directory_urls(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )

    assert report.distribution_mode == "file"
    assert report.to_dict()["distribution_mode"] == "file"
    mkdocs = (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert "use_directory_urls: false\n" in mkdocs
    assert 'custom_dir: ".llm-wiki-mkdocs-overrides"\n' in mkdocs
    assert '<a class="navbar-brand" href="{{ home.prefix }}index.html">' in (
        out / ".llm-wiki-mkdocs-overrides" / "main.html"
    ).read_text(encoding="utf-8")
    assert '<a class="navbar-brand" href="index.html">' in (
        out / ".llm-wiki-mkdocs-overrides" / "404.html"
    ).read_text(encoding="utf-8")


def test_user_profile_requires_non_default_site_name(tmp_path):
    wiki = _write_wiki(tmp_path)

    with pytest.raises(SiteExportError, match="--profile user requires --site-name"):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=tmp_path / "site-missing",
            format="mkdocs",
            profile="user",
        )

    with pytest.raises(SiteExportError, match="different from 'LLM Wiki'"):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=tmp_path / "site-default",
            format="mkdocs",
            profile="user",
            site_name="LLM Wiki",
        )


def test_user_profile_writes_human_root_and_generated_reference(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(
        wiki / "guides" / "operator-onboarding.md",
        "# Operator Onboarding\n\nStart with [Signup](../workflows/signup.md).\n",
    )
    out = tmp_path / "site"

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Assistant",
    )

    assert report.profile == "user"
    assert report.site_name == "Assistant"
    root = (out / "index.md").read_text(encoding="utf-8")
    generated = (out / "generated-reference.md").read_text(encoding="utf-8")
    assert root.startswith('---\ntitle: "Assistant"\n---\n\n# Assistant\n')
    assert "## Overview" in root
    assert "- [Operator Onboarding](guides/operator-onboarding.md)" in root
    assert "- [Generated Reference](generated-reference.md)" in root
    assert len(root.splitlines()) < 250
    assert generated.startswith("# LLM Wiki Index\n")
    assert "llm_wiki:" not in generated
    mkdocs = (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert '  - "Start Here":' in mkdocs
    assert '    - "Assistant": "index.md"' in mkdocs
    assert '    - "Operator Onboarding": "guides/operator-onboarding.md"' in mkdocs
    assert '    - "Generated Reference": "generated-reference.md"' in mkdocs


def test_user_profile_nav_groups_test_pages_and_demotes_placeholder_flows(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(wiki / "guides" / "contributor-onboarding.md", "# Contributor\n\n")
    _write(
        wiki / "flows" / "empty-flow.md",
        "# Empty Flow\n\n## Behavior\n\nReplace this placeholder.\n",
    )
    _write(
        wiki / "modules" / "test_helpers.md",
        "# test_helpers Module\n\n",
    )
    _write(
        wiki / ".llm-wiki-surface.json",
        json.dumps(
            {
                "schema_version": "llm-wiki-surface-index/v1",
                "pages": [
                    {
                        "canonical_path": "modules/test_helpers.md",
                        "source_path": "tests/test_helpers.py",
                    },
                    {
                        "canonical_path": "modules/models.md",
                        "source_path": "src/models.py",
                    },
                ],
            },
            sort_keys=True,
        )
        + "\n",
    )
    out = tmp_path / "site"

    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Assistant",
    )

    mkdocs = (out / "mkdocs.yml").read_text(encoding="utf-8")
    core = mkdocs.split('  - "Core Workflows":', 1)[1].split(
        '  - "Architecture And Operations":',
        1,
    )[0]
    reference = mkdocs.split('  - "Generated Reference":', 1)[1].split(
        '  - "Test And Fixture Reference":',
        1,
    )[0]
    tests = mkdocs.split('  - "Test And Fixture Reference":', 1)[1]
    assert '"Empty Flow": "flows/empty-flow.md"' not in core
    assert '"Empty Flow": "flows/empty-flow.md"' in reference
    assert '"test_helpers Module": "modules/test_helpers.md"' in tests


def test_file_friendly_export_requires_mkdocs_format(tmp_path):
    wiki = _write_wiki(tmp_path)

    with pytest.raises(
        SiteExportError, match="--file-friendly requires --format mkdocs"
    ):
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=tmp_path / "site",
            format="plain",
            file_friendly=True,
        )


def test_mkdocs_export_disambiguates_duplicate_navigation_labels(tmp_path):
    wiki = _write_disambiguated_wiki(tmp_path)
    out = tmp_path / "site"

    export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")

    config = (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert '  - "agent / ArtifactStore": "entities/agent_ArtifactStore.md"' in config
    assert (
        '  - "artifacts / ArtifactStore": "entities/artifacts_ArtifactStore.md"'
        in config
    )
    assert '  - "cmd / main Module": "modules/cmd_main.md"' in config
    assert '  - "server / main Module": "modules/server_main.md"' in config


def test_mkdocs_dry_run_reports_config_without_writing(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        dry_run=True,
    )

    assert report.page_count == 9
    assert report.dry_run is True
    assert {operation.action for operation in report.operations} == {"would_write"}
    assert {
        Path(operation.path).name for operation in report.operations
    }.issuperset(
        {"mkdocs.yml", SITE_PUBLICATION_MARKER, SITE_PUBLICATION_RECEIPT}
    )
    assert not out.exists()


def test_docusaurus_export_writes_front_matter_with_surface_index_source(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(
        wiki / ".llm-wiki-surface.json",
        json.dumps(
            {
                "schema_version": "llm-wiki-surface-index/v1",
                "pages": [
                    {
                        "canonical_path": "entities/User.md",
                        "source_path": "src/models.py",
                    },
                ],
            },
            sort_keys=True,
        )
        + "\n",
    )
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")

    content = (out / "entities" / "User.md").read_text(encoding="utf-8")
    assert report.front_matter is True
    assert content.startswith(
        "\n".join(
            [
                "---",
                'id: "entities/User"',
                'title: "\\"User\\": account"',
                'sidebar_label: "\\"User\\": account"',
                "sidebar_position: 3",
                "llm_wiki:",
                '  kind: "entities"',
                '  id: "User"',
                '  role: "semantic"',
                '  canonical_path: "entities/User.md"',
                '  mcp_uri: "llm-wiki://entities/User"',
                '  source_path: "src/models.py"',
                "---",
                "",
                '# "User": account',
            ]
        )
    )


def test_docusaurus_export_disambiguates_duplicate_front_matter_labels(tmp_path):
    wiki = _write_disambiguated_wiki(tmp_path)
    out = tmp_path / "site"

    export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")

    agent_content = (out / "entities" / "agent_ArtifactStore.md").read_text(
        encoding="utf-8"
    )
    artifacts_content = (out / "entities" / "artifacts_ArtifactStore.md").read_text(
        encoding="utf-8"
    )
    cmd_content = (out / "modules" / "cmd_main.md").read_text(encoding="utf-8")
    server_content = (out / "modules" / "server_main.md").read_text(encoding="utf-8")

    assert 'id: "entities/agent_ArtifactStore"' in agent_content
    assert 'title: "agent / ArtifactStore"' in agent_content
    assert 'sidebar_label: "agent / ArtifactStore"' in agent_content
    assert '  id: "agent_ArtifactStore"' in agent_content
    assert '  canonical_path: "entities/agent_ArtifactStore.md"' in agent_content

    assert 'id: "entities/artifacts_ArtifactStore"' in artifacts_content
    assert 'title: "artifacts / ArtifactStore"' in artifacts_content
    assert 'sidebar_label: "artifacts / ArtifactStore"' in artifacts_content
    assert '  id: "artifacts_ArtifactStore"' in artifacts_content
    assert (
        '  canonical_path: "entities/artifacts_ArtifactStore.md"' in artifacts_content
    )

    assert 'id: "modules/cmd_main"' in cmd_content
    assert 'title: "cmd / main Module"' in cmd_content
    assert 'sidebar_label: "cmd / main Module"' in cmd_content
    assert '  id: "cmd_main"' in cmd_content
    assert '  canonical_path: "modules/cmd_main.md"' in cmd_content

    assert 'id: "modules/server_main"' in server_content
    assert 'title: "server / main Module"' in server_content
    assert 'sidebar_label: "server / main Module"' in server_content
    assert '  id: "server_main"' in server_content
    assert '  canonical_path: "modules/server_main.md"' in server_content


def test_docusaurus_export_writes_registry_ordered_sidebar(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")

    assert report.page_count == 9
    assert any(
        Path(operation.path) == out / "sidebars.json"
        for operation in report.operations
    )
    assert json.loads((out / "sidebars.json").read_text(encoding="utf-8")) == {
        "llmWikiSidebar": [
            "index",
            "log",
            {"type": "category", "label": "Entities", "items": ["entities/User"]},
            {"type": "category", "label": "Modules", "items": ["modules/models"]},
            {
                "type": "category",
                "label": "Workflows",
                "items": ["workflows/signup"],
            },
            {"type": "category", "label": "User flows", "items": ["flows/checkout"]},
            {
                "type": "category",
                "label": "Infrastructure",
                "items": ["infrastructure/Dockerfile"],
            },
            "dependencies",
            "load-order",
        ]
    }


def test_docusaurus_dry_run_reports_sidebar_without_writing(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="docusaurus",
        dry_run=True,
    )

    assert report.front_matter is True
    assert report.dry_run is True
    assert {operation.action for operation in report.operations} == {"would_write"}
    assert {
        Path(operation.path).name for operation in report.operations
    }.issuperset(
        {"sidebars.json", SITE_PUBLICATION_MARKER, SITE_PUBLICATION_RECEIPT}
    )
    assert not out.exists()


def test_docusaurus_export_preserves_fences_and_escapes_mdx_text(tmp_path):
    wiki = _write_wiki(tmp_path)
    user_path = wiki / "entities" / "User.md"
    user_path.write_text(
        user_path.read_text(encoding="utf-8")
        + "\nLiteral {value} <Widget /> outside `inline {safe} <Safe />`.\n",
        encoding="utf-8",
    )
    out = tmp_path / "site"

    export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")

    content = (out / "entities" / "User.md").read_text(encoding="utf-8")
    assert (
        "Literal \\{value\\} \\<Widget /> outside `inline {safe} <Safe />`." in content
    )
    assert "[models](../modules/./models.md)" in content
    assert 'click M "../modules/models.md"' in content


def test_docusaurus_export_preserves_multiline_video_embed(tmp_path):
    wiki = _write_wiki(tmp_path)
    user_path = wiki / "entities" / "User.md"
    user_path.write_text(
        user_path.read_text(encoding="utf-8")
        + "\n<video controls>\n"
        + '  <source src="../assets/clip.webm" type="video/webm">\n'
        + "</video>\n",
        encoding="utf-8",
    )
    out = tmp_path / "site"

    export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")

    content = (out / "entities" / "User.md").read_text(encoding="utf-8")
    assert "<video controls>" in content
    assert '<source src="../assets/clip.webm" type="video/webm">' in content
    assert "</video>" in content
    assert "\\</video>" not in content


def test_rewrites_internal_markdown_links_and_preserves_fences(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    export_site_mirror(wiki_dir=wiki, out_dir=out)

    index_content = (out / "index.md").read_text(encoding="utf-8")
    user_content = (out / "entities" / "User.md").read_text(encoding="utf-8")

    assert "[User](entities/User.md)" in index_content
    assert "[models](../modules/models.md#classes)" in user_content
    assert "[missing](../missing.md)" in user_content
    assert "[external](https://example.com)" in user_content
    assert "[section](#local)" in user_content
    assert "![image](../assets/logo.png)" in user_content
    assert "[models](../modules/./models.md)" in user_content
    assert 'click M "../modules/models.md"' in user_content


def test_check_succeeds_after_export(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    report = importlib.import_module(
        "llm_wiki_cli.services.site_export"
    ).check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is True
    assert report.page_count == 9
    assert report.issues == []
    assert report.warnings == []


def test_check_reports_stale_exported_assets_without_failing(tmp_path):
    wiki = _write_usage_asset_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    (wiki / "guides" / "tour.md").write_text(
        "# Tour\n\nNo media now.\n", encoding="utf-8"
    )

    report = check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is True
    assert report.issues == []
    assert [
        (warning["category"], warning["target"])
        for warning in report.warnings
        if warning["category"] == "stale_asset"
    ] == [
        ("stale_asset", "assets/guides/tour/clip.webm"),
        ("stale_asset", "assets/guides/tour/home.png"),
    ]


def test_check_reports_stale_outside_assets_and_matches_export_operations(tmp_path):
    wiki = _write_wiki(tmp_path)
    _write(wiki / "guides" / "tour.md", "# Tour\n\n![Local](pic.png)\n")
    (wiki / "guides" / "pic.png").write_bytes(b"local")
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(wiki / "guides" / "tour.md", "# Tour\n\nNo media now.\n")

    export_report = export_site_mirror(wiki_dir=wiki, out_dir=out, dry_run=True)
    check_report = check_site_mirror(wiki_dir=wiki, out_dir=out)

    export_stale = [
        Path(operation.path).relative_to(out).as_posix()
        for operation in export_report.asset_operations
        if operation.action == "stale_asset"
    ]
    check_stale = [
        warning["target"]
        for warning in check_report.warnings
        if warning["category"] == "stale_asset"
    ]
    assert export_stale == ["guides/pic.png"]
    assert check_stale == export_stale


def test_check_reports_missing_output_dir_and_page(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    service = importlib.import_module("llm_wiki_cli.services.site_export")

    missing = service.check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert missing.ok is False
    assert missing.issues == [
        {
            "category": "missing_output_dir",
            "path": str(out),
            "message": f"Output directory does not exist: {out}",
        }
    ]

    export_site_mirror(wiki_dir=wiki, out_dir=out)
    (out / "entities" / "User.md").unlink()
    broken = service.check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert broken.ok is False
    assert any(
        issue["category"] == "missing_mirror_page"
        and issue["path"] == str(out / "entities" / "User.md")
        for issue in broken.issues
    )


def test_check_reports_broken_and_unsafe_local_markdown_links(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    user_page = out / "entities" / "User.md"
    user_page.write_text(
        user_page.read_text(encoding="utf-8")
        + "\n[Broken](../modules/missing.md)\n[Unsafe](../../outside.md)\n",
        encoding="utf-8",
    )

    report = importlib.import_module(
        "llm_wiki_cli.services.site_export"
    ).check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "broken_markdown_link"
        and issue["target"] == "../modules/missing.md"
        for issue in report.issues
    )
    assert any(
        issue["category"] == "unsafe_markdown_link"
        and issue["target"] == "../../outside.md"
        for issue in report.issues
    )


def test_check_reports_malformed_front_matter(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")
    _write(out / "missing.md", "# Missing\n\n")
    user_page = out / "entities" / "User.md"
    user_page.write_text("---\ntitle: Broken\n# no closing fence\n", encoding="utf-8")

    report = importlib.import_module(
        "llm_wiki_cli.services.site_export"
    ).check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "malformed_front_matter"
        and issue["path"] == str(user_page)
        for issue in report.issues
    )


def test_check_reports_missing_and_mismatched_front_matter_metadata(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")
    _write(out / "missing.md", "# Missing\n\n")
    user_page = out / "entities" / "User.md"
    content = user_page.read_text(encoding="utf-8")
    content = content.replace('  id: "User"\n', "")
    content = content.replace(
        '  canonical_path: "entities/User.md"',
        '  canonical_path: "wrong.md"',
    )
    user_page.write_text(content, encoding="utf-8")

    report = importlib.import_module(
        "llm_wiki_cli.services.site_export"
    ).check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "front_matter_missing_key"
        and issue["target"] == "llm_wiki.id"
        for issue in report.issues
    )


def test_hub_export_writes_namespaced_wikis_and_top_level_index(tmp_path):
    root = tmp_path / "sources" / "code_wikis"
    _write_hub_wiki(root, "alpha", "Alpha")
    _write_hub_wiki(root, "beta", "Beta")
    out = tmp_path / "hub"

    report = export_site_hub(wiki_root=root, out_dir=out, format="plain")

    assert report.ok is True
    assert report.page_count == 7
    assert (out / "alpha" / "index.md").is_file()
    assert (out / "beta" / "modules" / "service.md").is_file()
    assert (out / "index.md").read_text(encoding="utf-8") == "\n".join(
        [
            "# LLM Wiki Hub",
            "",
            "| Source | Pages | Index |",
            "|---|---:|---|",
            "| alpha | 3 | [index](alpha/index.md) |",
            "| beta | 3 | [index](beta/index.md) |",
            "",
        ]
    )


def test_hub_export_copies_assets_under_source_namespace(tmp_path):
    root = tmp_path / "sources" / "code_wikis"
    alpha = _write_hub_wiki(root, "alpha", "Alpha")
    _write(
        alpha / "guides" / "tour.md",
        "# Tour\n\n![Home](../assets/guides/tour/home.png)\n",
    )
    (alpha / "assets" / "guides" / "tour").mkdir(parents=True)
    (alpha / "assets" / "guides" / "tour" / "home.png").write_bytes(b"png")
    out = tmp_path / "hub"

    report = export_site_hub(wiki_root=root, out_dir=out, format="plain")

    assert report.asset_count == 1
    assert (out / "alpha" / "assets" / "guides" / "tour" / "home.png").is_file()
    assert not (out / "assets").exists()


def test_hub_export_copies_outside_assets_media_under_source_namespace(tmp_path):
    root = tmp_path / "sources" / "code_wikis"
    alpha = _write_hub_wiki(root, "alpha", "Alpha")
    _write(alpha / "guides" / "tour.md", "# Tour\n\n![Local](pic.png)\n")
    (alpha / "guides" / "pic.png").write_bytes(b"png")
    out = tmp_path / "hub"

    report = export_site_hub(wiki_root=root, out_dir=out, format="plain")

    assert report.asset_count == 1
    assert (out / "alpha" / "guides" / "pic.png").is_file()


def test_hub_export_writes_grouped_mkdocs_and_docusaurus_navigation(tmp_path):
    root = tmp_path / "sources" / "code_wikis"
    _write_hub_wiki(root, "alpha", "Alpha")
    _write_hub_wiki(root, "beta", "Beta")
    out = tmp_path / "hub"

    export_site_hub(wiki_root=root, out_dir=out, format="mkdocs")

    mkdocs = (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert '  - "alpha":' in mkdocs
    assert '    - "Alpha Index": "alpha/index.md"' in mkdocs
    assert '  - "beta":' in mkdocs
    assert '    - "Beta Service": "beta/modules/service.md"' in mkdocs

    docusaurus_out = tmp_path / "hub-docusaurus"
    export_site_hub(
        wiki_root=root,
        out_dir=docusaurus_out,
        format="docusaurus",
    )

    alpha_index = (docusaurus_out / "alpha" / "index.md").read_text(
        encoding="utf-8"
    )
    sidebars = json.loads(
        (docusaurus_out / "sidebars.json").read_text(encoding="utf-8")
    )
    assert 'id: "alpha/index"' in alpha_index
    assert sidebars == {
        "llmWikiSidebar": [
            {
                "type": "category",
                "label": "alpha",
                "items": [
                    "alpha/index",
                    "alpha/log",
                    {
                        "type": "category",
                        "label": "Modules",
                        "items": ["alpha/modules/service"],
                    },
                ],
            },
            {
                "type": "category",
                "label": "beta",
                "items": [
                    "beta/index",
                    "beta/log",
                    {
                        "type": "category",
                        "label": "Modules",
                        "items": ["beta/modules/service"],
                    },
                ],
            },
        ]
    }


def test_mkdocs_hub_file_friendly_export_disables_directory_urls(tmp_path):
    root = tmp_path / "sources" / "code_wikis"
    _write_hub_wiki(root, "alpha", "Alpha")
    out = tmp_path / "hub"

    report = export_site_hub(
        wiki_root=root,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )

    assert report.distribution_mode == "file"
    mkdocs = (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert "use_directory_urls: false\n" in mkdocs
    assert 'custom_dir: ".llm-wiki-mkdocs-overrides"\n' in mkdocs
    assert (out / ".llm-wiki-mkdocs-overrides" / "main.html").exists()
    assert (out / ".llm-wiki-mkdocs-overrides" / "404.html").exists()


def test_hub_check_validates_namespaced_wikis_and_broken_links(tmp_path):
    root = tmp_path / "sources" / "code_wikis"
    _write_hub_wiki(root, "alpha", "Alpha")
    _write_hub_wiki(root, "beta", "Beta")
    out = tmp_path / "hub"
    export_site_hub(wiki_root=root, out_dir=out, format="docusaurus")

    valid = check_site_hub(wiki_root=root, out_dir=out)

    assert valid.ok is True
    assert valid.issues == []

    alpha_service = out / "alpha" / "modules" / "service.md"
    alpha_service.write_text(
        alpha_service.read_text(encoding="utf-8") + "\n[Broken](missing.md)\n",
        encoding="utf-8",
    )

    broken = check_site_hub(wiki_root=root, out_dir=out)

    assert broken.ok is False
    assert any(
        issue["category"] == "broken_markdown_link" and issue["target"] == "missing.md"
        for issue in broken.issues
    )


def test_hub_export_rejects_duplicate_explicit_source_ids(tmp_path):
    left = tmp_path / "left" / "wiki"
    right = tmp_path / "right" / "wiki"
    _write_hub_wiki(left.parent, "wiki", "Left")
    _write_hub_wiki(right.parent, "wiki", "Right")

    with pytest.raises(SiteExportError, match="Duplicate hub source id"):
        export_site_hub(wikis=[left, right], out_dir=tmp_path / "hub")


def test_hub_export_rejects_normalized_source_id_collision_before_writes(
    tmp_path,
):
    root = tmp_path / "sources"
    _write_hub_wiki(root, "a b", "Left")
    _write_hub_wiki(root, "a  b", "Right")
    out = tmp_path / "hub"

    with pytest.raises(
        SiteExportError,
        match="Duplicate normalized hub source id",
    ):
        export_site_hub(wiki_root=root, out_dir=out)

    assert not out.exists()


def test_single_export_rejects_empty_normalized_source_id_before_writes(
    tmp_path,
):
    wiki = _write_hub_wiki(tmp_path, "   ", "Whitespace")
    out = tmp_path / "site"

    with pytest.raises(SiteExportError, match="not path-safe after normalization"):
        export_site_mirror(wiki_dir=wiki, out_dir=out)

    assert not out.exists()


def test_check_reports_duplicate_docusaurus_front_matter_ids(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")
    _write(out / "missing.md", "# Missing\n\n")
    user_page = out / "entities" / "User.md"
    models_page = out / "modules" / "models.md"
    models_page.write_text(
        models_page.read_text(encoding="utf-8").replace(
            'id: "modules/models"', 'id: "entities/User"'
        ),
        encoding="utf-8",
    )

    report = importlib.import_module(
        "llm_wiki_cli.services.site_export"
    ).check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "duplicate_front_matter_id"
        and issue["path"] == str(models_page)
        and issue["target"] == str(user_page)
        for issue in report.issues
    )


def test_check_rejects_changed_output_even_when_change_was_previously_a_warning(
    tmp_path,
):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")
    _write(out / "missing.md", "# Missing\n\n")
    user_page = out / "entities" / "User.md"
    content = user_page.read_text(encoding="utf-8")
    user_page.write_text(content.split("---\n\n", 1)[1], encoding="utf-8")

    report = importlib.import_module(
        "llm_wiki_cli.services.site_export"
    ).check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "stale_publication_commitment"
        and issue["path"] == str(user_page)
        for issue in report.issues
    )
    assert any(
        warning["category"] == "missing_front_matter"
        and warning["path"] == str(user_page)
        for warning in report.warnings
    )


def test_check_reports_output_paths_that_escape_out_dir(tmp_path, monkeypatch):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    service = importlib.import_module("llm_wiki_cli.services.site_export")
    original_safe_join = service._safe_join

    def fake_safe_join(root, relative):
        if relative == "entities/User.md":
            return root.parent / "escaped.md"
        return original_safe_join(root, relative)

    monkeypatch.setattr(service, "_safe_join", fake_safe_join)

    report = service.check_site_mirror(wiki_dir=wiki, out_dir=out)

    assert report.ok is False
    assert any(
        issue["category"] == "unsafe_output_path"
        and issue["target"] == "entities/User.md"
        for issue in report.issues
    )


def test_check_built_site_html_accepts_mkdocs_directory_urls_in_http_mode(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        '<html><body><a href="entities/User/">User</a></body></html>',
    )
    _write(built / "entities" / "User" / "index.html", "<h1>User</h1>")
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
    )

    assert report.ok is True
    assert report.built_site_dir == str(built)
    assert report.link_mode == "http"
    assert report.issues == []


def test_check_built_site_html_rejects_empty_build_directory(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    built.mkdir()
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
    )

    assert report.ok is False
    assert any(
        issue["category"] == "missing_built_html_target"
        and "contains no HTML" in issue["message"]
        for issue in report.issues
    )


def test_check_built_site_html_rejects_directory_urls_in_file_mode(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        '<html><body><a href="entities/User/">User</a></body></html>',
    )
    _write(built / "entities" / "User" / "index.html", "<h1>User</h1>")
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="file",
    )

    assert report.ok is False
    assert any(
        issue["category"] == "file_directory_url"
        and issue["target"] == "entities/User/"
        for issue in report.issues
    )


def test_check_built_site_html_rejects_dot_directory_urls_in_file_mode(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "entities" / "User.html",
        '<html><body><a href="..">Home</a></body></html>',
    )
    _write(built / "index.html", "<h1>Home</h1>")
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="file",
    )

    assert report.ok is False
    assert any(
        issue["category"] == "file_directory_url" and issue["target"] == ".."
        for issue in report.issues
    )


def test_check_built_site_html_accepts_direct_html_links_in_file_mode(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        '<html><body><a href="entities/User.html#profile">User</a></body></html>',
    )
    _write(built / "entities" / "User.html", "<h1>User</h1>")
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="file",
    )

    assert report.ok is True
    assert report.issues == []


def test_check_built_site_html_accepts_parent_relative_links_inside_site(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "dependencies" / "index.html",
        '<link href="../css/base.css"><a href="..">Home</a>',
    )
    _write(built / "css" / "base.css", "body { color: #111; }")
    _write(built / "index.html", "<h1>Home</h1>")
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
    )

    assert report.ok is True
    assert report.issues == []


def test_check_built_site_html_rejects_unsafe_traversal(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        '<html><body><a href="../outside.html">Outside</a></body></html>',
    )
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="file",
    )

    assert report.ok is False
    assert any(
        issue["category"] == "unsafe_built_html_link"
        and issue["target"] == "../outside.html"
        for issue in report.issues
    )


def test_check_built_site_html_validates_media_src_in_both_link_modes(tmp_path):
    wiki = _write_wiki(tmp_path)
    for link_mode in ("http", "file"):
        out = tmp_path / f"site-{link_mode}"
        built = tmp_path / f"_site-{link_mode}"
        export_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            format="mkdocs",
            file_friendly=link_mode == "file",
        )
        _write(out / "missing.md", "# Missing\n\n")
        _write(
            built / "index.html",
            (
                '<html><body><img src="assets/home.png">'
                '<video><source src="assets/clip.webm"></video></body></html>'
            ),
        )
        (built / "assets").mkdir(parents=True)
        (built / "assets" / "home.png").write_bytes(b"png")
        (built / "assets" / "clip.webm").write_bytes(b"webm")
        _carry_publication_marker(out, built)
        report = check_site_mirror(
            wiki_dir=wiki,
            out_dir=out,
            built_site_dir=built,
            link_mode=link_mode,
        )
        assert report.ok is True
        assert report.issues == []


def test_check_built_site_html_reports_missing_media_and_ignores_external_video(
    tmp_path,
):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        (
            '<img src="assets/missing.png">'
            '<video src="https://cdn.example/demo.mp4"></video>'
        ),
    )
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
    )

    assert report.ok is False
    assert [
        (issue["category"], issue["target"])
        for issue in report.issues
        if issue["category"] == "missing_built_media_target"
    ] == [("missing_built_media_target", "assets/missing.png")]


def test_check_built_site_html_validates_srcset_candidates(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        (
            '<img src="assets/fallback.png" '
            'srcset="assets/small.png 1x, assets/missing.png 2x, '
            "https://cdn.example/remote.png 3x, "
            'data:image/png;base64,AAAA 4x">'
        ),
    )
    (built / "assets").mkdir(parents=True)
    (built / "assets" / "fallback.png").write_bytes(b"fallback")
    (built / "assets" / "small.png").write_bytes(b"small")
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
    )

    assert report.ok is False
    assert [
        (issue["category"], issue["target"])
        for issue in report.issues
        if issue["category"] == "missing_built_media_target"
    ] == [("missing_built_media_target", "assets/missing.png")]


def test_check_built_site_html_rejects_media_traversal(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )
    _write(out / "missing.md", "# Missing\n\n")
    _write(built / "index.html", '<img src="../outside.png">')
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="file",
    )

    assert report.ok is False
    assert any(
        issue["category"] == "unsafe_built_html_link"
        and issue["target"] == "../outside.png"
        for issue in report.issues
    )


def test_check_built_site_html_rejects_srcset_traversal(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )
    _write(out / "missing.md", "# Missing\n\n")
    _write(built / "index.html", '<source srcset="../outside.png 1x">')
    _carry_publication_marker(out, built)

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="file",
    )

    assert report.ok is False
    assert any(
        issue["category"] == "unsafe_built_html_link"
        and issue["target"] == "../outside.png"
        for issue in report.issues
    )


def test_same_file_bytes_compares_size_and_chunks(tmp_path):
    service = importlib.import_module("llm_wiki_cli.services.site_export")
    left = tmp_path / "left.bin"
    right = tmp_path / "right.bin"
    left.write_bytes(b"abc")
    right.write_bytes(b"abcd")
    assert service._same_file_bytes(left, right) is False

    right.write_bytes(b"abd")
    assert service._same_file_bytes(left, right) is False

    right.write_bytes(b"abc")
    assert service._same_file_bytes(left, right) is True


def test_export_reports_unchanged_for_identical_existing_asset(tmp_path):
    wiki = _write_usage_asset_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out)

    report = export_site_mirror(wiki_dir=wiki, out_dir=out)

    assert {operation.action for operation in report.asset_operations} == {"unchanged"}


def test_user_profile_check_reports_required_quality_categories(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Assistant",
    )
    index = out / "index.md"
    index.write_text(
        "# Assistant\n\n"
        + "\n".join(
            f"- [Link {number}](generated-reference.md)" for number in range(81)
        )
        + "\n",
        encoding="utf-8",
    )
    generated = out / "generated-reference.md"
    generated.write_text(
        generated.read_text(encoding="utf-8")
        + "\n_Describe what this flow does. Replace this placeholder._\n",
        encoding="utf-8",
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Assistant",
    )

    assert report.ok is False
    assert {issue["category"] for issue in report.issues} >= {
        "human_index_too_many_links",
        "missing_user_guides",
    }
    assert any(
        warning["category"] == "generated_reference_placeholder"
        and warning["path"] == str(generated)
        for warning in report.warnings
    )


def test_user_profile_check_reports_long_index_default_name_and_placeholders(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Assistant",
    )
    guide = out / "guides" / "operator-onboarding.md"
    _write(guide, "# Operator\n\nReplace this placeholder.\n")
    (out / "index.md").write_text(
        "# Assistant\n\n" + "\n".join("line" for _ in range(251)) + "\n",
        encoding="utf-8",
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="LLM Wiki",
    )

    assert report.ok is False
    assert {issue["category"] for issue in report.issues} >= {
        "human_index_too_long",
        "default_user_site_name",
        "published_placeholder",
    }
    assert any(issue["path"] == str(guide) for issue in report.issues)


def test_user_profile_check_warns_once_when_primary_docs_have_no_usage_media(tmp_path):
    wiki = tmp_path / "docs" / "llm_wiki"
    _write(wiki / "index.md", "# Index\n\n- [Guide](guides/tour.md)\n")
    _write(wiki / "log.md", "# Log\n")
    _write(wiki / "guides" / "tour.md", "# Tour\n\nFollow the CLI flow.\n")
    out = tmp_path / "site"

    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Project Docs",
    )
    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Project Docs",
    )

    assert report.ok is True
    assert [
        warning["category"]
        for warning in report.warnings
        if warning["category"] == "user_docs_missing_examples"
    ] == ["user_docs_missing_examples"]

    _write(
        wiki / "guides" / "tour.md",
        "# Tour\n\n![CLI](../assets/guides/tour/cli.svg)\n",
    )
    (wiki / "assets" / "guides" / "tour").mkdir(parents=True)
    (wiki / "assets" / "guides" / "tour" / "cli.svg").write_bytes(b"svg")
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Project Docs",
    )
    with_media = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Project Docs",
    )

    assert all(
        warning["category"] != "user_docs_missing_examples"
        for warning in with_media.warnings
    )

def test_publication_receipt_and_marker_are_versioned_path_safe_and_bound(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="  Project   Docs  ",
    )

    receipt = json.loads(
        (out / SITE_PUBLICATION_RECEIPT).read_text(encoding="utf-8")
    )
    marker = json.loads(
        (out / SITE_PUBLICATION_MARKER).read_text(encoding="utf-8")
    )
    assert receipt["schema_version"] == SITE_PUBLICATION_SCHEMA_VERSION
    assert receipt["state"] == "complete"
    assert receipt["selection"]["site_name"] == "Project Docs"
    assert receipt["selection"]["source_identity"]["kind"] == "single"
    assert receipt["selection_id"] == report.selection_id
    assert receipt["export_id"] == report.export_id
    assert marker == {
        "schema_version": SITE_PUBLICATION_SCHEMA_VERSION,
        "selection_id": report.selection_id,
        "export_id": report.export_id,
    }
    assert all(
        not Path(commitment["path"]).is_absolute()
        and ".." not in Path(commitment["path"]).parts
        for commitment in receipt["commitments"]
    )
    assert str(tmp_path) not in json.dumps(receipt, sort_keys=True)


def test_same_selection_regeneration_updates_export_id_and_stales_old_build(
    tmp_path,
):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site"
    first = export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")
    _write(built / "index.html", "<h1>Built</h1>\n")
    _carry_publication_marker(out, built)

    _write(
        wiki / "modules" / "models.md",
        "# models Module\n\nChanged source content.\n",
    )
    second = export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")
    _write(out / "missing.md", "# Missing\n\n")

    assert second.selection_id == first.selection_id
    assert second.export_id != first.export_id
    stale = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
        format="mkdocs",
    )
    assert stale.ok is False
    assert any(
        issue["category"] == "mismatched_built_publication_marker"
        for issue in stale.issues
    )
    _carry_publication_marker(out, built)
    assert check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
        format="mkdocs",
    ).ok is True


def test_changed_publication_selection_fails_before_any_output_mutation(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")
    before = {
        path.relative_to(out).as_posix(): path.read_bytes()
        for path in out.rglob("*")
        if path.is_file()
    }

    with pytest.raises(
        SiteExportError,
        match="different immutable publication selections",
    ):
        export_site_mirror(wiki_dir=wiki, out_dir=out, format="docusaurus")

    after = {
        path.relative_to(out).as_posix(): path.read_bytes()
        for path in out.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_built_check_rejects_cross_mode_marker_even_for_compatible_html(tmp_path):
    wiki = _write_wiki(tmp_path)
    hosted = tmp_path / "site-http"
    direct = tmp_path / "site-file"
    built = tmp_path / "_site-file"
    export_site_mirror(wiki_dir=wiki, out_dir=hosted, format="mkdocs")
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=direct,
        format="mkdocs",
        file_friendly=True,
    )
    _write(built / "index.html", "<h1>Compatible in either mode</h1>\n")
    _write(
        built / SITE_PUBLICATION_MARKER,
        (hosted / SITE_PUBLICATION_MARKER).read_text(encoding="utf-8"),
    )

    report = check_site_mirror(
        wiki_dir=wiki,
        out_dir=direct,
        built_site_dir=built,
        link_mode="file",
        format="mkdocs",
    )

    assert report.ok is False
    assert report.distribution_mode == "file"
    assert any(
        issue["category"] == "mismatched_built_publication_marker"
        for issue in report.issues
    )


def test_mirror_check_compares_supplied_link_mode_without_a_built_site(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site-file"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        file_friendly=True,
    )
    _write(out / "missing.md", "# Missing\n\n")

    mismatched = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        link_mode="http",
    )
    matching = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        link_mode="file",
    )

    assert mismatched.ok is False
    assert any(
        issue["category"] == "publication_selection_mismatch"
        and issue["target"] == "distribution_mode"
        for issue in mismatched.issues
    )
    assert matching.ok is True


def test_check_rejects_missing_tampered_and_mismatched_publication_metadata(
    tmp_path,
):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Project Docs",
    )

    mismatched = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="docusaurus",
        profile="user",
        site_name="Other Docs",
    )
    assert {
        issue.get("target")
        for issue in mismatched.issues
        if issue["category"] == "publication_selection_mismatch"
    } == {"format", "site_name"}

    profile_mismatch = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="reference",
        site_name="Project Docs",
    )
    assert any(
        issue["category"] == "publication_selection_mismatch"
        and issue["target"] == "profile"
        for issue in profile_mismatch.issues
    )

    marker = out / SITE_PUBLICATION_MARKER
    marker.unlink()
    missing_marker = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Project Docs",
    )
    assert any(
        issue["category"] == "missing_mirror_publication_marker"
        for issue in missing_marker.issues
    )

    (out / SITE_PUBLICATION_RECEIPT).unlink()
    missing_receipt = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Project Docs",
    )
    assert any(
        issue["category"] == "missing_publication_receipt"
        for issue in missing_receipt.issues
    )

    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="user",
        site_name="Project Docs",
    )
    receipt_path = out / SITE_PUBLICATION_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["selection_id"] = "sha256:" + "0" * 64
    _write(receipt_path, json.dumps(receipt, sort_keys=True) + "\n")
    tampered = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        profile="user",
        site_name="Project Docs",
    )
    assert any(
        issue["category"] == "invalid_publication_receipt"
        for issue in tampered.issues
    )


def test_check_rejects_mismatched_single_source_identity(tmp_path):
    wiki = _write_wiki(tmp_path / "original")
    other_wiki = _write_wiki(tmp_path / "copy")
    out = tmp_path / "site"
    export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")

    report = check_site_mirror(
        wiki_dir=other_wiki,
        out_dir=out,
        format="mkdocs",
        link_mode="http",
    )

    assert report.ok is False
    assert any(
        issue["category"] == "publication_selection_mismatch"
        and issue["target"] == "source_identity"
        for issue in report.issues
    )


def test_hub_source_order_is_an_immutable_selection(tmp_path):
    root = tmp_path / "sources"
    alpha = _write_hub_wiki(root, "alpha", "Alpha")
    beta = _write_hub_wiki(root, "beta", "Beta")
    out = tmp_path / "hub"
    export_site_hub(wikis=[alpha, beta], out_dir=out, format="plain")
    before = (out / SITE_PUBLICATION_RECEIPT).read_bytes()

    with pytest.raises(
        SiteExportError,
        match="different immutable publication selections",
    ):
        export_site_hub(wikis=[beta, alpha], out_dir=out, format="plain")

    assert (out / SITE_PUBLICATION_RECEIPT).read_bytes() == before


def test_hub_built_check_requires_the_root_publication_marker(tmp_path):
    root = tmp_path / "sources"
    _write_hub_wiki(root, "alpha", "Alpha")
    _write_hub_wiki(root, "beta", "Beta")
    out = tmp_path / "hub"
    built = tmp_path / "_hub"
    export_site_hub(wiki_root=root, out_dir=out, format="mkdocs")
    assert (out / SITE_PUBLICATION_RECEIPT).is_file()
    assert (out / SITE_PUBLICATION_MARKER).is_file()
    assert not (out / "alpha" / SITE_PUBLICATION_RECEIPT).exists()
    assert not (out / "alpha" / SITE_PUBLICATION_MARKER).exists()
    _write(built / "index.html", "<h1>Hub</h1>\n")
    _carry_publication_marker(out, built)

    assert check_site_hub(
        wiki_root=root,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
        format="mkdocs",
    ).ok is True

    marker = json.loads(
        (built / SITE_PUBLICATION_MARKER).read_text(encoding="utf-8")
    )
    marker["export_id"] = "sha256:" + "0" * 64
    _write(
        built / SITE_PUBLICATION_MARKER,
        json.dumps(marker, sort_keys=True) + "\n",
    )
    stale = check_site_hub(
        wiki_root=root,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
        format="mkdocs",
    )
    assert stale.ok is False
    assert any(
        issue["category"] == "mismatched_built_publication_marker"
        for issue in stale.issues
    )


class TestSiteCli:
    def test_cli_export_dry_run_json(self, tmp_path, monkeypatch, capsys):
        site_cmd = importlib.import_module("llm_wiki_cli.commands.site_cmd")
        _write_wiki(tmp_path)
        monkeypatch.chdir(tmp_path)

        site_cmd.run(
            _ns(
                site_action="export",
                wiki_dir="docs/llm_wiki",
                out_dir="site",
                format="mkdocs",
                front_matter=False,
                dry_run=True,
                output_format="json",
            )
        )

        data = json.loads(capsys.readouterr().out)
        assert data["page_count"] == 9
        assert data["format"] == "mkdocs"
        assert data["dry_run"] is True
        assert {operation["action"] for operation in data["operations"]} == {
            "would_write"
        }
        assert not (tmp_path / "site").exists()

    def test_cli_export_hub_from_wiki_root_json(self, tmp_path, monkeypatch, capsys):
        site_cmd = importlib.import_module("llm_wiki_cli.commands.site_cmd")
        root = tmp_path / "sources" / "code_wikis"
        _write_hub_wiki(root, "alpha", "Alpha")
        _write_hub_wiki(root, "beta", "Beta")
        monkeypatch.chdir(tmp_path)

        site_cmd.run(
            _ns(
                site_action="export",
                wiki_dir="docs/llm_wiki",
                wiki_root="sources/code_wikis",
                wiki=[],
                out_dir="site",
                format="plain",
                front_matter=False,
                dry_run=False,
                output_format="json",
            )
        )

        data = json.loads(capsys.readouterr().out)
        assert data["source_count"] == 2
        assert data["page_count"] == 7
        assert (tmp_path / "site" / "alpha" / "index.md").is_file()

    def test_cli_check_json_success_and_failure(self, tmp_path, monkeypatch, capsys):
        site_cmd = importlib.import_module("llm_wiki_cli.commands.site_cmd")
        wiki = _write_wiki(tmp_path)
        out = tmp_path / "site"
        export_site_mirror(wiki_dir=wiki, out_dir=out)
        _write(out / "missing.md", "# Missing\n\n")
        monkeypatch.chdir(tmp_path)

        site_cmd.run(
            _ns(
                site_action="check",
                wiki_dir="docs/llm_wiki",
                out_dir="site",
                output_format="json",
            )
        )
        ok = json.loads(capsys.readouterr().out)
        assert ok["ok"] is True
        assert ok["issues"] == []
        assert ok["warnings"] == []

        (out / "modules" / "models.md").unlink()
        with pytest.raises(SystemExit) as exc_info:
            site_cmd.run(
                _ns(
                    site_action="check",
                    wiki_dir="docs/llm_wiki",
                    out_dir="site",
                    output_format="json",
                )
            )

        assert exc_info.value.code == 1
        failed = json.loads(capsys.readouterr().out)
        assert failed["ok"] is False
        assert failed["warnings"] == []
        assert any(
            issue["category"] == "missing_mirror_page" for issue in failed["issues"]
        )

    def test_cli_check_hub_from_explicit_wikis_json(
        self, tmp_path, monkeypatch, capsys
    ):
        site_cmd = importlib.import_module("llm_wiki_cli.commands.site_cmd")
        root = tmp_path / "sources" / "code_wikis"
        alpha = _write_hub_wiki(root, "alpha", "Alpha")
        beta = _write_hub_wiki(root, "beta", "Beta")
        out = tmp_path / "site"
        export_site_hub(wikis=[alpha, beta], out_dir=out, format="plain")
        monkeypatch.chdir(tmp_path)

        site_cmd.run(
            _ns(
                site_action="check",
                wiki_dir="docs/llm_wiki",
                wiki_root=None,
                wiki=[str(alpha), str(beta)],
                out_dir="site",
                output_format="json",
            )
        )

        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["source_count"] == 2

    def test_cli_check_json_rejects_output_changed_after_export(
        self, tmp_path, monkeypatch, capsys
    ):
        site_cmd = importlib.import_module("llm_wiki_cli.commands.site_cmd")
        wiki = _write_wiki(tmp_path)
        out = tmp_path / "site"
        export_site_mirror(wiki_dir=wiki, out_dir=out, format="mkdocs")
        _write(out / "missing.md", "# Missing\n\n")
        user_page = out / "entities" / "User.md"
        content = user_page.read_text(encoding="utf-8")
        user_page.write_text(content.split("---\n\n", 1)[1], encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            site_cmd.run(
                _ns(
                    site_action="check",
                    wiki_dir="docs/llm_wiki",
                    out_dir="site",
                    output_format="json",
                )
            )

        assert exc_info.value.code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        assert any(
            issue["category"] == "stale_publication_commitment"
            for issue in payload["issues"]
        )
        assert any(
            warning["category"] == "missing_front_matter"
            for warning in payload["warnings"]
        )

    def test_cli_file_friendly_plain_fails_closed(self, tmp_path, monkeypatch, capsys):
        site_cmd = importlib.import_module("llm_wiki_cli.commands.site_cmd")
        _write_wiki(tmp_path)
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            site_cmd.run(
                _ns(
                    site_action="export",
                    wiki_dir="docs/llm_wiki",
                    wiki_root=None,
                    wiki=None,
                    out_dir="site",
                    format="plain",
                    file_friendly=True,
                    front_matter=False,
                    dry_run=False,
                    output_format="text",
                )
            )

        assert exc_info.value.code == 1
        assert "--file-friendly requires --format mkdocs" in capsys.readouterr().err

    def test_cli_check_built_site_json(self, tmp_path, monkeypatch, capsys):
        site_cmd = importlib.import_module("llm_wiki_cli.commands.site_cmd")
        wiki = _write_wiki(tmp_path)
        out = tmp_path / "site"
        built = tmp_path / "_site"
        export_site_mirror(wiki_dir=wiki, out_dir=out)
        _write(out / "missing.md", "# Missing\n\n")
        _write(built / "index.html", '<a href="entities/User/">User</a>')
        _write(built / "entities" / "User" / "index.html", "<h1>User</h1>")
        _carry_publication_marker(out, built)
        monkeypatch.chdir(tmp_path)

        site_cmd.run(
            _ns(
                site_action="check",
                wiki_dir="docs/llm_wiki",
                wiki_root=None,
                wiki=None,
                out_dir="site",
                built_site_dir="_site",
                link_mode="http",
                output_format="json",
            )
        )

        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["built_site_dir"] == "_site"
        assert payload["link_mode"] == "http"

    def test_cli_help_includes_site_actions(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", "site", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        assert "export" in output
        assert "check" in output


def test_text_report_discloses_complete_export_evidence():
    report = SiteExportReport(
        dry_run=True,
        wiki_dir="docs/llm_wiki",
        out_dir="site",
        built_site_dir="_site",
        format="mkdocs",
        profile="reference",
        site_name="Knowledge",
        distribution_mode="file",
        link_mode="file",
        selection_id="selection-1",
        export_id="export-1",
        publication_state="complete",
        page_count=2,
        source_count=2,
        freshness_by_source={"beta": "stale", "alpha": "current"},
        operations=[
            SiteExportOperation("write", "wiki/index.md", "index.md", "page")
        ],
        asset_operations=[
            SiteExportOperation("copy", "wiki/logo.png", "logo.png", "asset")
        ],
        issues=[
            {
                "category": "broken_link",
                "path": "index.md",
                "target": "missing.md",
                "message": "missing",
            }
        ],
        warnings=[
            {
                "category": "missing_title",
                "path": "page.md",
                "target": "heading",
                "message": "fallback used",
            }
        ],
    )

    rendered = render_report_text(report, action="export")

    for expected in (
        "Wiki: docs/llm_wiki",
        "Site name: Knowledge",
        "Selection id: selection-1",
        "Export id: export-1",
        "Publication state: complete",
        "Freshness by source:",
        "- alpha: current",
        "Built site: _site",
        "Sources: 2",
        "Dry run: no files were changed.",
        "Operations:",
        "- write: index.md - page",
        "Asset operations:",
        "- copy: logo.png - asset",
        "Issues:",
        "index.md -> missing.md - missing",
        "Warnings:",
        "page.md -> heading - fallback used",
    ):
        assert expected in rendered

    assert (
        "No static-site mirror issues found."
        in render_report_text(SiteExportReport(), action="check")
    )
