"""Tests for the pure static-site mirror export service."""

from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.site_export import SiteExportError, export_site_mirror


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
        assert any(
            issue["category"] == "missing_mirror_page"
            for issue in failed["issues"]
        )

    def test_cli_help_includes_site_actions(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", "site", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out
        assert "export" in output
        assert "check" in output
