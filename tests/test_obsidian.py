"""Tests for Obsidian mirror export and companion plugin packaging."""

from __future__ import annotations

import json
import shutil
import subprocess
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import obsidian_cmd
from llm_wiki_cli.services import obsidian


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _write_wiki(root: Path) -> Path:
    wiki = root / "docs" / "llm_wiki"
    for subdir in [
        "entities",
        "modules",
        "workflows",
        "flows",
        "infrastructure",
        "legacy",
    ]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text(
        "# LLM Wiki Index\n\n- [User](entities/User.md)\n- [models](modules/models.md)\n",
        encoding="utf-8",
    )
    (wiki / "log.md").write_text("# Architectural Log\n\n", encoding="utf-8")
    (wiki / "dependencies.md").write_text(
        "# Dependencies\n\nProject dependency graph.\n",
        encoding="utf-8",
    )
    (wiki / "load-order.md").write_text(
        "# Load Order\n\nProject initialization order.\n",
        encoding="utf-8",
    )
    (wiki / "entities" / "User.md").write_text(
        "# User\n\n"
        "**Location:** `models.py:3`\n"
        "**Module:** [models](../modules/models.md)\n\n"
        "## Description\n\nA user entity.\n",
        encoding="utf-8",
    )
    (wiki / "modules" / "models.md").write_text(
        "# models Module\n\n"
        "**Path:** `models.py`\n\n"
        "## Classes\n\n| Class | Description |\n|---|---|\n| [User](../entities/User.md) | A user |\n",
        encoding="utf-8",
    )
    (wiki / "workflows" / "signup.md").write_text(
        "# Signup\n\nTouches [models](../modules/models.md).\n",
        encoding="utf-8",
    )
    (wiki / "flows" / "checkout.md").write_text(
        "# Checkout\n\nUses [models](../modules/models.md).\n",
        encoding="utf-8",
    )
    (wiki / "infrastructure" / "Dockerfile.md").write_text(
        "# Dockerfile\n\nCopies [models.py](../modules/models.md).\n",
        encoding="utf-8",
    )
    (wiki / "legacy" / "Old.md").write_text("# Old\n\n", encoding="utf-8")
    return wiki


class TestObsidianMirror:
    def test_collects_pages_and_maps_to_vault_paths(self, tmp_project):
        wiki = _write_wiki(tmp_project)

        pages = obsidian.collect_wiki_pages(wiki)
        by_rel = {page.canonical_rel: page for page in pages}

        assert by_rel["entities/User.md"].mirror_rel == "LLM Wiki/Entities/User.md"
        assert by_rel["flows/checkout.md"].mirror_rel == "LLM Wiki/Flows/checkout.md"
        assert by_rel["dependencies.md"].mirror_rel == "LLM Wiki/Dependencies.md"
        assert by_rel["load-order.md"].mirror_rel == "LLM Wiki/Load order.md"
        assert by_rel["modules/models.md"].source_path == "models.py"
        assert by_rel["entities/User.md"].source_line == 3
        assert "legacy/Old.md" not in by_rel

    def test_frontmatter_aliases_tags_and_metadata(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        page = next(
            page
            for page in obsidian.collect_wiki_pages(wiki)
            if page.canonical_rel == "entities/User.md"
        )

        frontmatter = obsidian.build_frontmatter(page)

        assert '  - "llm-wiki/entity"' in frontmatter
        assert '  canonical_path: "entities/User.md"' in frontmatter
        assert '  source_path: "models.py"' in frontmatter
        assert "  source_line: 3" in frontmatter
        assert '  - "entity/User"' in frontmatter

    def test_converts_internal_markdown_links_to_wikilinks(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        pages = obsidian.collect_wiki_pages(wiki)
        canonical = {page.canonical_rel: page for page in pages}
        page = canonical["entities/User.md"]

        content = obsidian.convert_markdown_links(
            "See [models](../modules/models.md) and [external](https://example.com).",
            page,
            canonical,
            wiki,
        )

        assert "[[LLM Wiki/Modules/models|models]]" in content
        assert "[external](https://example.com)" in content

    def test_export_creates_mirror_and_preserves_sidecar_note(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        note = vault / ".llm-wiki" / "obsidian-notes" / "entity" / "User.md"
        note.parent.mkdir(parents=True)
        note.write_text("# Existing Notes\n\nKeep this.\n", encoding="utf-8")

        report = obsidian.export_obsidian_vault(
            src_dir=".",
            wiki_dir=wiki,
            vault_dir=vault,
        )

        mirror = vault / "LLM Wiki" / "Entities" / "User.md"
        assert report.page_count == 9
        assert mirror.exists()
        assert (vault / "LLM Wiki" / "Flows" / "checkout.md").exists()
        assert (vault / "LLM Wiki" / "Dependencies.md").exists()
        assert (vault / "LLM Wiki" / "Load order.md").exists()
        content = mirror.read_text(encoding="utf-8")
        assert "aliases:" in content
        assert "[[LLM Wiki/Modules/models|models]]" in content
        assert "![[.llm-wiki/obsidian-notes/entity/User]]" in content
        assert note.read_text(encoding="utf-8") == "# Existing Notes\n\nKeep this.\n"

    def test_export_reads_each_wiki_page_once(self, tmp_project, monkeypatch):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        canonical_paths = {
            page.canonical_path.resolve() for page in obsidian.collect_wiki_pages(wiki)
        }
        reads: dict[Path, int] = {}
        original_read_md = obsidian.read_md

        def counting_read_md(path: Path) -> str:
            resolved = path.resolve()
            if resolved in canonical_paths:
                reads[resolved] = reads.get(resolved, 0) + 1
            return original_read_md(path)

        monkeypatch.setattr(obsidian, "read_md", counting_read_md)

        report = obsidian.export_obsidian_vault(
            src_dir=".",
            wiki_dir=wiki,
            vault_dir=vault,
        )

        assert report.page_count == len(canonical_paths)
        assert set(reads) == canonical_paths
        assert sum(reads.values()) == len(canonical_paths)

    def test_export_dry_run_does_not_write(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"

        report = obsidian.export_obsidian_vault(
            src_dir=".",
            wiki_dir=wiki,
            vault_dir=vault,
            dry_run=True,
        )

        assert report.dry_run is True
        assert any(op.action == "would_write" for op in report.operations)
        assert not (vault / "LLM Wiki").exists()

    def test_check_detects_missing_mirror_and_broken_wikilinks(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        vault = tmp_project / "vault"
        report = obsidian.check_obsidian_vault(wiki_dir=wiki, vault_dir=vault)

        assert report.ok is False
        assert any(
            issue["category"] == "missing_mirror_page" for issue in report.issues
        )

        obsidian.export_obsidian_vault(src_dir=".", wiki_dir=wiki, vault_dir=vault)
        user_page = vault / "LLM Wiki" / "Entities" / "User.md"
        user_page.write_text(
            user_page.read_text(encoding="utf-8") + "\n[[LLM Wiki/Missing/Page]]\n",
            encoding="utf-8",
        )
        broken = obsidian.check_obsidian_vault(wiki_dir=wiki, vault_dir=vault)

        assert any(issue["category"] == "broken_wikilink" for issue in broken.issues)

    def test_path_escape_is_rejected(self, tmp_project):
        vault = tmp_project / "vault"

        with pytest.raises(obsidian.ObsidianError):
            obsidian._safe_join(vault, "../outside.md")


class TestObsidianCli:
    def test_cli_export_and_check_json(self, tmp_project, capsys):
        _write_wiki(tmp_project)
        vault = tmp_project / "vault"

        obsidian_cmd.run(
            _ns(
                obsidian_action="export",
                src_dir=".",
                wiki_dir="docs/llm_wiki",
                vault_dir=str(vault),
                notes_dir=".llm-wiki/obsidian-notes",
                dry_run=False,
                format="json",
            )
        )
        data = json.loads(capsys.readouterr().out)
        assert data["page_count"] == 9

        obsidian_cmd.run(
            _ns(
                obsidian_action="check",
                wiki_dir="docs/llm_wiki",
                vault_dir=str(vault),
                format="json",
            )
        )
        check = json.loads(capsys.readouterr().out)
        assert check["ok"] is True

    def test_cli_install_plugin(self, tmp_project):
        vault = tmp_project / "vault"

        obsidian_cmd.run(
            _ns(
                obsidian_action="install-plugin",
                vault_dir=str(vault),
                plugin_dir="integrations/obsidian/llm-wiki",
                format="text",
            )
        )

        assert (vault / ".obsidian" / "plugins" / "llm-wiki" / "manifest.json").exists()
        assert (vault / ".obsidian" / "plugins" / "llm-wiki" / "main.js").exists()

    def test_cli_help_includes_obsidian(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["llm-wiki", "obsidian", "--help"])

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 0
        assert "export" in capsys.readouterr().out


class TestObsidianPluginPackage:
    def test_manifest_and_package_metadata(self):
        root = Path("integrations/obsidian/llm-wiki")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))

        assert manifest["id"] == "llm-wiki"
        assert manifest["isDesktopOnly"] is True
        assert package["scripts"]["build"]

    def test_main_js_syntax(self):
        node = shutil.which("node")
        if not node:
            pytest.skip("node is not installed")

        subprocess.run(
            [node, "--check", "integrations/obsidian/llm-wiki/main.js"],
            check=True,
            capture_output=True,
            text=True,
        )
