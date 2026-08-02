"""Tests for the generated wiki surface index artifact."""

from __future__ import annotations

import json
from pathlib import Path

from llm_wiki_cli.services.knowledge_artifacts import validate_surface_index_bytes
from llm_wiki_cli.services.wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    build_surface_index,
    write_surface_index,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_surface_index_describes_pages_links_counts_and_flows(tmp_path):
    src = tmp_path / "project"
    wiki = src / "docs" / "llm_wiki"
    src.mkdir()

    _write(
        wiki / "index.md",
        "\n".join(
            [
                "# LLM Wiki Index",
                "",
                "- [core](modules/core.md)",
                "- [run](flows/cli-run.md)",
                "- [external](https://example.com)",
                "- [anchor](#surface-overview)",
                "- [missing](missing.md)",
            ]
        ),
    )
    _write(
        wiki / "modules" / "core.md",
        "\n".join(
            [
                "# core Module",
                "",
                "**Path:** `pkg/core.py`",
                "",
                "See [User](../entities/User.md).",
                "",
                "```mermaid",
                'click user "../entities/User.md"',
                "```",
            ]
        ),
    )
    _write(wiki / "entities" / "User.md", "# User\n\n**Location:** `pkg/core.py:1`\n")
    _write(wiki / "flows" / "cli-run.md", "# cli-run\n\n[core](../modules/core.md)\n")
    _write(wiki / "dependencies.md", "# Dependencies\n\n[core](modules/core.md)\n")
    _write(wiki / "load-order.md", "# Load order\n")
    _write(
        wiki / "infrastructure" / "Dockerfile.md",
        f"# Dockerfile\n\n**Path:** `{src / 'Dockerfile'}`\n",
    )

    payload = build_surface_index(
        wiki,
        {
            "pkg/core.py": {
                "language": "python",
                "classes": [{"name": "User"}],
                "functions": [{"name": "main"}],
            }
        },
        src_dir=str(src),
        entity_page_cache={("User", "pkg/core.py"): "User"},
        module_page_map={"pkg/core.py": "core"},
        entry_points=[
            {
                "id": "cli-run",
                "category": "cli",
                "symbol": "main",
                "label": "cli-run",
                "file": "pkg/core.py",
            }
        ],
    )

    assert payload["schema_version"] == WIKI_SURFACE_INDEX_SCHEMA_VERSION
    assert payload["counts"]["total"] == 7
    assert payload["counts"]["by_kind"] == {
        "index": 1,
        "log": 0,
        "entities": 1,
        "modules": 1,
        "workflows": 0,
        "guides": 0,
        "flows": 1,
        "infrastructure": 1,
        "api-contracts": 0,
        "dependencies": 1,
        "load-order": 1,
    }
    assert payload["counts"]["dependency_architecture"] == 2
    assert payload["dependency_pages"] == {
        "dependencies": True,
        "load_order": True,
        "count": 2,
    }
    assert payload["flows"] == [
        {
            "id": "cli-run",
            "category": "cli",
            "entry_point": {
                "symbol": "main",
                "source_path": "pkg/core.py",
                "label": "cli-run",
            },
        }
    ]

    by_path = {page["canonical_path"]: page for page in payload["pages"]}
    assert by_path["index.md"]["outgoing_internal_links"] == [
        "flows/cli-run.md",
        "modules/core.md",
    ]
    assert by_path["modules/core.md"]["source_path"] == "pkg/core.py"
    assert by_path["modules/core.md"]["outgoing_internal_links"] == ["entities/User.md"]
    assert by_path["entities/User.md"]["source_path"] == "pkg/core.py"
    assert by_path["flows/cli-run.md"]["source_path"] == "pkg/core.py"
    assert by_path["infrastructure/Dockerfile.md"]["source_path"] == "Dockerfile"
    assert all(
        Path(page["canonical_path"]).as_posix() == page["canonical_path"]
        for page in payload["pages"]
    )

    serialized = json.dumps(payload, sort_keys=True)
    assert str(src) not in serialized
    assert "source_hash" in payload


def test_write_surface_index_is_deterministic_and_skips_unchanged_payload(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")

    first_path, first_state = write_surface_index(wiki, {}, src_dir=str(tmp_path))
    first_content = (wiki / SURFACE_INDEX_FILENAME).read_text(encoding="utf-8")
    second_path, second_state = write_surface_index(wiki, {}, src_dir=str(tmp_path))
    second_content = (wiki / SURFACE_INDEX_FILENAME).read_text(encoding="utf-8")

    assert first_path == wiki / SURFACE_INDEX_FILENAME
    assert second_path == wiki / SURFACE_INDEX_FILENAME
    assert first_state == "created"
    assert second_state == "unchanged"
    assert first_content == second_content


def test_knowledge_sidecars_do_not_change_surface_index_v1(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n\n[User](entities/User.md)\n")
    _write(wiki / "entities" / "User.md", "# User\n")

    before = build_surface_index(wiki, {}, src_dir=str(tmp_path))
    _write(wiki / ".llm-wiki-knowledge.json", '{"malformed-for-loader": true}\n')
    _write(wiki / ".llm-wiki-manifest.json", '{"artifact_hashes": null}\n')
    after = build_surface_index(wiki, {}, src_dir=str(tmp_path))

    assert after == before
    assert after["schema_version"] == WIKI_SURFACE_INDEX_SCHEMA_VERSION
    assert [
        (page["canonical_path"], page["id"], page["mcp_uri"])
        for page in after["pages"]
    ] == [
        ("index.md", "index", "llm-wiki://index"),
        ("entities/User.md", "User", "llm-wiki://entities/User"),
    ]
    assert "generated_at" not in after
    assert "timestamp" not in after


def test_surface_index_preserves_bounded_flow_evidence(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "flows" / "http-create.md", "# Create\n")
    evidence = {
        "flow": {
            "step_count": 2,
            "truncated": False,
            "modules_touched": ["src/api.py"],
        },
        "data_flow": {
            "generated": True,
            "step_count": 2,
            "transfer_count": 1,
            "truncated": False,
            "boundary_effects": [{"kind": "database_write", "confidence": "high"}],
            "gaps": [],
        },
    }

    payload = build_surface_index(
        wiki,
        {},
        src_dir=str(tmp_path),
        entry_points=[
            {
                "id": "http-create",
                "category": "http",
                "entry": "create",
                "file": "src/api.py",
                "detector": "builtin",
                "language": "python",
                "routes": [{"method": "POST", "path": "/items"}],
                "evidence": evidence,
            }
        ],
    )

    assert payload["flows"][0]["detector"] == "builtin"
    assert payload["flows"][0]["language"] == "python"
    assert payload["flows"][0]["routes"] == [{"method": "POST", "path": "/items"}]
    assert payload["flows"][0]["evidence"] == evidence


def test_surface_index_records_asset_counts_and_page_reference_map(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n\n- [Guide](guides/tour.md)\n")
    _write(
        wiki / "guides" / "tour.md",
        "# Tour\n\n"
        '![Screenshot](../assets/guides/tour/home.png "Home")\n'
        '<img alt="CLI" src="../assets/guides/tour/cli.svg">\n',
    )
    _write(wiki / "assets" / "guides" / "tour" / "home.png", "png")
    _write(wiki / "assets" / "guides" / "tour" / "cli.svg", "svg")
    _write(wiki / "assets" / "guides" / "tour" / "unused.webp", "webp")

    payload = build_surface_index(wiki, {}, src_dir=str(tmp_path))

    assert payload["counts"]["assets"] == {
        "total": 3,
        "referenced": 2,
        "unreferenced": 1,
        "by_media_type": {"image": 3, "video": 0, "other": 0},
    }
    assert payload["assets"]["by_page"] == {
        "guides/tour.md": [
            "assets/guides/tour/cli.svg",
            "assets/guides/tour/home.png",
        ]
    }
    assert payload["assets"]["unreferenced"] == ["assets/guides/tour/unused.webp"]
    assert all("\\" not in path for path in payload["assets"]["by_page"])


def test_surface_index_records_reference_style_and_other_asset_counts(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n\n- [Guide](guides/tour.md)\n")
    _write(
        wiki / "guides" / "tour.md",
        "# Tour\n\n"
        "![Screenshot][home]\n\n"
        '[home]: ../assets/guides/tour/home.png "Home"\n',
    )
    _write(wiki / "assets" / "guides" / "tour" / "home.png", "png")
    _write(wiki / "assets" / "guides" / "tour" / "notes.txt", "notes")
    _write(wiki / "assets" / "guides" / "tour" / "README.md", "readme")

    payload = build_surface_index(wiki, {}, src_dir=str(tmp_path))

    assert payload["counts"]["assets"] == {
        "total": 3,
        "referenced": 1,
        "unreferenced": 2,
        "by_media_type": {"image": 1, "video": 0, "other": 2},
    }
    assert payload["assets"]["by_page"] == {
        "guides/tour.md": ["assets/guides/tour/home.png"]
    }
    assert payload["assets"]["unreferenced"] == [
        "assets/guides/tour/notes.txt",
        "assets/guides/tour/README.md",
    ]


def test_surface_index_serializes_only_canonical_asset_paths(tmp_path):
    wiki = tmp_path / "wiki"
    guide = wiki / "guides" / "tour.md"
    _write(
        guide,
        "# Tour\n\n"
        "![Canonical](../assets/guides/canonical.png)\n"
        "![Page-local](local.png)\n"
        "`![Inline pseudo-media](../assets/guides/pseudo.png)`\n",
    )
    _write(wiki / "assets" / "guides" / "canonical.png", "canonical")
    _write(wiki / "guides" / "local.png", "page-local")

    payload = build_surface_index(wiki, {}, src_dir=str(tmp_path))

    assert payload["counts"]["assets"] == {
        "total": 1,
        "referenced": 1,
        "unreferenced": 0,
        "by_media_type": {"image": 1, "video": 0, "other": 0},
    }
    assert payload["assets"] == {
        "by_page": {
            "guides/tour.md": ["assets/guides/canonical.png"],
        },
        "referenced": ["assets/guides/canonical.png"],
        "unreferenced": [],
    }
    assert all(
        asset_path.startswith("assets/")
        for asset_paths in payload["assets"]["by_page"].values()
        for asset_path in asset_paths
    )
    serialized = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    assert validate_surface_index_bytes(serialized) == payload

    _write(
        guide,
        "# Tour\n\n"
        "![Canonical](../assets/guides/canonical.png)\n"
        "![Other page-local](other.png)\n"
        "`![Other inline pseudo-media](../assets/guides/other-pseudo.png)`\n",
    )
    _write(wiki / "guides" / "other.png", "other-page-local")

    changed_noncanonical_references = build_surface_index(
        wiki,
        {},
        src_dir=str(tmp_path),
    )
    assert changed_noncanonical_references["assets"] == payload["assets"]
    assert changed_noncanonical_references["source_hash"] == payload["source_hash"]


def test_surface_index_resolves_titled_internal_links_with_parentheses(tmp_path):
    wiki = tmp_path / "wiki"
    _write(
        wiki / "index.md",
        '# Index\n\n[Setup](guides/setup(1).md "Setup guide")\n',
    )
    _write(wiki / "guides" / "setup(1).md", "# Setup\n")

    payload = build_surface_index(wiki, {}, src_dir=str(tmp_path))

    by_path = {page["canonical_path"]: page for page in payload["pages"]}
    assert by_path["index.md"]["outgoing_internal_links"] == ["guides/setup(1).md"]


def test_surface_index_preserves_legacy_outgoing_internal_link_behavior(tmp_path):
    wiki = tmp_path / "wiki"
    _write(
        wiki / "index.md",
        "\n".join(
            [
                "# Index",
                "",
                "[Core](modules/core.md)",
                "[Core duplicate](modules/core.md)",
                "[Core encoded](modules/%63ore.md)",
                "[Core backslash](modules\\core.md)",
                "[Core fragment](modules/core.md#overview)",
                "[Missing](modules/missing.md)",
                "[External](https://example.com/reference)",
                "[Mail](mailto:docs@example.com)",
                "[Anchor](#overview)",
                "![Asset](assets/diagram.svg)",
                "",
                "```mermaid",
                'click core "modules/core.md"',
                'click mermaid "modules/mermaid.md"',
                "```",
                "",
                "```text",
                "[Fenced pseudo-link](modules/fenced.md)",
                "```",
                "",
            ]
        ),
    )
    _write(wiki / "modules" / "core.md", "# Core\n")
    _write(wiki / "modules" / "fenced.md", "# Fenced\n")
    _write(wiki / "modules" / "mermaid.md", "# Mermaid\n")
    _write(wiki / "assets" / "diagram.svg", "<svg></svg>\n")

    payload = build_surface_index(wiki, {}, src_dir=str(tmp_path))

    by_path = {page["canonical_path"]: page for page in payload["pages"]}
    assert by_path["index.md"]["outgoing_internal_links"] == [
        "modules/core.md",
        "modules/fenced.md",
        "modules/mermaid.md",
    ]
