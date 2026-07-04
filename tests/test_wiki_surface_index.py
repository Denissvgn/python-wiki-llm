"""Tests for the generated wiki surface index artifact."""

from __future__ import annotations

import json
from pathlib import Path

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
