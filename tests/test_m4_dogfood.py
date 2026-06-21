"""Dogfood smoke coverage for this repository's M4 documentation surface."""

from __future__ import annotations

import hashlib
import json
import shutil
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, site_cmd, sync_cmd
from llm_wiki_cli.services.extractor_helpers import get_prepared_binary
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _copy_repo(source: Path, target: Path) -> None:
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "build",
            "dist",
            "*.egg-info",
        ),
    )


def _file_hashes(root: Path) -> dict[str, str]:
    ignored_roots = {
        "docs/llm_wiki",
        "site",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    }
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(
            rel == ignored or rel.startswith(f"{ignored}/") for ignored in ignored_roots
        ):
            continue
        hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _mermaid_body_lengths(wiki_dir: Path) -> list[int]:
    lengths: list[int] = []
    for path in wiki_dir.rglob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            if lines[index].strip() != "```mermaid":
                index += 1
                continue
            index += 1
            body_lines = 0
            while index < len(lines) and lines[index].strip() != "```":
                body_lines += 1
                index += 1
            lengths.append(body_lines)
            if index < len(lines):
                index += 1
    return lengths


def test_m4_dogfood_bootstrap_sync_and_site_export(tmp_path, monkeypatch, capsys):
    repo_root = Path(__file__).resolve().parents[1]
    helper_cache_dir = repo_root / ".git"
    if not get_prepared_binary("go", repo_root, str(helper_cache_dir)):
        pytest.skip("prepared Go helper cache is required for full-repo dogfood")
    if not get_prepared_binary("rust", repo_root, str(helper_cache_dir)):
        pytest.skip("prepared Rust helper cache is required for full-repo dogfood")
    source = tmp_path / "python-wiki-llm"
    _copy_repo(repo_root, source)
    before = _file_hashes(source)
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(helper_cache_dir))
    monkeypatch.chdir(source)

    bootstrap_cmd.run(
        _ns(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
            overwrite=False,
            depth="full",
            skip_workflows=False,
            skip_flows=False,
            skip_data_flow=False,
            skip_dependencies=False,
            dependency_graph_detail="auto",
            format="json",
            source_adapter=True,
            allow_external_src=False,
        )
    )
    bootstrap_summary = json.loads(capsys.readouterr().out)
    assert bootstrap_summary["schema_version"] == "llm-wiki-bootstrap-summary/v1"
    assert bootstrap_summary["flows"] > 0
    assert bootstrap_summary["dependencies"]["pages_created"] == 2

    sync_cmd.run(
        _ns(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
            no_cache=True,
            rebuild_cache=False,
            cache_stats=False,
            cache_dir=None,
            jobs=1,
            force=False,
            no_preserve_semantic=False,
        )
    )
    capsys.readouterr()

    site_cmd.run(
        _ns(
            site_action="export",
            wiki_dir="docs/llm_wiki",
            out_dir="site",
            format="mkdocs",
            front_matter=False,
            dry_run=False,
            output_format="json",
        )
    )
    site_export = json.loads(capsys.readouterr().out)
    assert site_export["ok"] is True
    assert site_export["format"] == "mkdocs"
    assert site_export["page_count"] > 100

    site_cmd.run(
        _ns(
            site_action="check",
            wiki_dir="docs/llm_wiki",
            out_dir="site",
            output_format="json",
        )
    )
    site_check = json.loads(capsys.readouterr().out)
    assert site_check["ok"] is True
    assert site_check["issues"] == []

    wiki_dir = source / "docs" / "llm_wiki"
    surface = json.loads(
        (wiki_dir / SURFACE_INDEX_FILENAME).read_text(encoding="utf-8")
    )
    counts = surface["counts"]["by_kind"]
    assert counts["entities"] > 100
    assert counts["modules"] > 100
    assert counts["flows"] > 0
    assert surface["counts"]["dependency_architecture"] == 2
    assert (wiki_dir / "dependencies.md").exists()
    assert (wiki_dir / "load-order.md").exists()
    assert (wiki_dir / "flows" / "process-llm-wiki.md").exists()

    mermaid_lengths = _mermaid_body_lengths(wiki_dir)
    assert mermaid_lengths
    assert max(mermaid_lengths) <= 80
    assert "```mermaid" in (wiki_dir / "dependencies.md").read_text(encoding="utf-8")
    assert "```mermaid" in (wiki_dir / "flows" / "process-llm-wiki.md").read_text(
        encoding="utf-8"
    )
    assert any(
        "```mermaid" in path.read_text(encoding="utf-8")
        for path in (wiki_dir / "entities").glob("*.md")
    )
    assert any(
        "```mermaid" in path.read_text(encoding="utf-8")
        for path in (wiki_dir / "modules").glob("*.md")
    )
    assert _file_hashes(source) == before
