"""Dogfood smoke coverage for this repository's documentation surface."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, site_cmd, sync_cmd
from llm_wiki_cli.services.diagrams import (
    GENERATED_DIAGRAM_CHAR_LIMIT,
    GENERATED_DIAGRAM_LINE_LIMIT,
    GENERATED_DIAGRAM_NODE_LIMIT,
)
from llm_wiki_cli.services.extractor_helpers import (
    get_prepared_binary,
    resolve_helper_cache_root,
)
from llm_wiki_cli.services.inventory_cache import ENV_CACHE_DIR
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME


_MERMAID_NODE_DECLARATION_RE = re.compile(
    r'^\s*(?:[A-Za-z][A-Za-z0-9_]*\s*\["|'
    r"participant\s+[A-Za-z][A-Za-z0-9_]*\s+as\b)"
)
_LEGACY_RAW_DOTTED_LABEL_RE = re.compile(
    r'^\s*[A-Za-z][A-Za-z0-9_]*\s+-\.\s+(?!")[^\r\n]+\s+\.->\s+'
    r"[A-Za-z][A-Za-z0-9_]*\s*$"
)


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _copy_repo(source: Path, target: Path) -> None:
    source = source.resolve()
    common_ignore = shutil.ignore_patterns(
        ".git",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
        "reports",
        "*.egg-info",
    )

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = set(common_ignore(directory, names))
        if Path(directory).resolve() == source / "docs":
            ignored.add("llm_wiki")
        return ignored

    shutil.copytree(
        source,
        target,
        ignore=ignore,
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


def test_copy_repo_excludes_generated_wiki_and_internal_report_state(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "selected.py").write_text("VALUE = 1\n", encoding="utf-8")
    public_doc = source / "docs" / "guide.md"
    public_doc.parent.mkdir()
    public_doc.write_text("# Guide\n", encoding="utf-8")
    wiki = source / "docs" / "llm_wiki" / "index.md"
    wiki.parent.mkdir()
    wiki.write_text("# Generated wiki\n", encoding="utf-8")
    report = source / "reports" / "internal" / "ledger.jsonl"
    report.parent.mkdir(parents=True)
    report.write_text("{}\n", encoding="utf-8")

    target = tmp_path / "target"
    _copy_repo(source, target)

    assert (target / "selected.py").is_file()
    assert (target / "docs" / "guide.md").is_file()
    assert not (target / "docs" / "llm_wiki").exists()
    assert not (target / "reports").exists()


def _mermaid_body_measurements(
    wiki_dir: Path,
) -> tuple[list[dict[str, int | str]], list[dict[str, int | str]]]:
    measurements: list[dict[str, int | str]] = []
    legacy_raw_dotted_labels: list[dict[str, int | str]] = []
    paths = sorted(
        wiki_dir.rglob("*.md"),
        key=lambda path: path.relative_to(wiki_dir).as_posix(),
    )
    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        index = 0
        block_index = 0
        while index < len(lines):
            if lines[index].strip() != "```mermaid":
                index += 1
                continue
            block_index += 1
            opening_line = index + 1
            index += 1
            body: list[str] = []
            while index < len(lines) and lines[index].strip() != "```":
                body.append(lines[index])
                if _LEGACY_RAW_DOTTED_LABEL_RE.match(lines[index]):
                    legacy_raw_dotted_labels.append(
                        {
                            "path": path.relative_to(wiki_dir).as_posix(),
                            "block": block_index,
                            "line": index + 1,
                            "text": lines[index].strip(),
                        }
                    )
                index += 1
            measurements.append(
                {
                    "path": path.relative_to(wiki_dir).as_posix(),
                    "block": block_index,
                    "line": opening_line,
                    "node_declarations": sum(
                        1 for line in body if _MERMAID_NODE_DECLARATION_RE.match(line)
                    ),
                    "body_lines": len(body),
                    "characters": len("\n".join(body)),
                }
            )
            if index < len(lines):
                index += 1
    return measurements, legacy_raw_dotted_labels


def test_documentation_dogfood_bootstrap_sync_and_site_export(tmp_path, monkeypatch, capsys):
    repo_root = Path(__file__).resolve().parents[1]
    helper_root = resolve_helper_cache_root(repo_root)
    if helper_root is None:
        pytest.skip("prepared Go helper cache is required for full-repo dogfood")
    helper_cache_base = helper_root.parent
    if not get_prepared_binary("go", repo_root, str(helper_cache_base)):
        pytest.skip("prepared Go helper cache is required for full-repo dogfood")
    if not get_prepared_binary("rust", repo_root, str(helper_cache_base)):
        pytest.skip("prepared Rust helper cache is required for full-repo dogfood")
    source = tmp_path / "python-wiki-llm"
    _copy_repo(repo_root, source)
    before = _file_hashes(source)
    monkeypatch.setenv(ENV_CACHE_DIR, str(helper_cache_base))
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
    assert (wiki_dir / "flows" / "cli-bootstrap.md").exists()
    assert (wiki_dir / "flows" / "cli-context.md").exists()
    assert (wiki_dir / "flows" / "cli-extract.md").exists()
    assert (wiki_dir / "flows" / "cli-lint.md").exists()
    assert (wiki_dir / "flows" / "process-llm-wiki.md").exists()

    mermaid_measurements, legacy_raw_dotted_labels = _mermaid_body_measurements(
        wiki_dir
    )
    assert mermaid_measurements
    budget_limits = {
        "node_declarations": GENERATED_DIAGRAM_NODE_LIMIT,
        "body_lines": GENERATED_DIAGRAM_LINE_LIMIT,
        "characters": GENERATED_DIAGRAM_CHAR_LIMIT,
    }
    budget_violations: list[dict[str, int | str]] = []
    for measurement in mermaid_measurements:
        for metric, limit in budget_limits.items():
            value = measurement[metric]
            assert isinstance(value, int)
            if value > limit:
                budget_violations.append(
                    {
                        "path": measurement["path"],
                        "block": measurement["block"],
                        "line": measurement["line"],
                        "measurement": metric,
                        "value": value,
                        "limit": limit,
                    }
                )
    assert budget_violations == []
    assert legacy_raw_dotted_labels == []
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
