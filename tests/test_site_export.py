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
    SiteExportError,
    check_site_hub,
    check_site_mirror,
    export_site_hub,
    export_site_mirror,
)


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def _write_disambiguated_wiki(root: Path) -> Path:
    wiki = _write_wiki(root)
    _write(wiki / "entities" / "agent_ArtifactStore.md", "# ArtifactStore\n\n")
    _write(wiki / "entities" / "artifacts_ArtifactStore.md", "# ArtifactStore\n\n")
    _write(wiki / "modules" / "cmd_main.md", "# main Module\n\n")
    _write(wiki / "modules" / "server_main.md", "# main Module\n\n")
    return wiki


def _operation_paths(report) -> list[str]:
    return [Path(operation.path).as_posix() for operation in report.operations]


def test_export_writes_registry_pages_in_surface_order(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, format="plain")

    assert report.ok is True
    assert report.page_count == 9
    assert report.format == "plain"
    assert [operation.action for operation in report.operations] == ["write"] * 9
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

    assert [operation.action for operation in second.operations] == ["unchanged"] * 9


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


def test_dry_run_reports_planned_writes_without_mutating(tmp_path):
    wiki = _write_wiki(tmp_path)
    out = tmp_path / "site"

    report = export_site_mirror(wiki_dir=wiki, out_dir=out, dry_run=True)

    assert report.dry_run is True
    assert report.to_dict()["dry_run"] is True
    assert {operation.action for operation in report.operations} == {"would_write"}
    assert not out.exists()


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
    assert Path(report.operations[-1].path) == out / "mkdocs.yml"
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
    assert report.operations[-1].action == "would_write"
    assert Path(report.operations[-1].path) == out / "mkdocs.yml"
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
    assert Path(report.operations[-1].path) == out / "sidebars.json"
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
    assert report.operations[-1].action == "would_write"
    assert Path(report.operations[-1].path) == out / "sidebars.json"
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

    export_site_hub(wiki_root=root, out_dir=out, format="docusaurus")

    alpha_index = (out / "alpha" / "index.md").read_text(encoding="utf-8")
    sidebars = json.loads((out / "sidebars.json").read_text(encoding="utf-8"))
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


def test_check_reports_missing_front_matter_warning_for_mixed_mirror(tmp_path):
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

    assert report.ok is True
    assert report.issues == []
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


def test_check_built_site_html_rejects_directory_urls_in_file_mode(tmp_path):
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
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "entities" / "User.html",
        '<html><body><a href="..">Home</a></body></html>',
    )
    _write(built / "index.html", "<h1>Home</h1>")

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
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        '<html><body><a href="entities/User.html#profile">User</a></body></html>',
    )
    _write(built / "entities" / "User.html", "<h1>User</h1>")

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
    export_site_mirror(wiki_dir=wiki, out_dir=out)
    _write(out / "missing.md", "# Missing\n\n")
    _write(
        built / "index.html",
        '<html><body><a href="../outside.html">Outside</a></body></html>',
    )

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

    def test_cli_check_json_warning_only_does_not_exit(
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

        site_cmd.run(
            _ns(
                site_action="check",
                wiki_dir="docs/llm_wiki",
                out_dir="site",
                output_format="json",
            )
        )

        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["issues"] == []
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
