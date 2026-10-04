"""Source/structure diagnostics stay distinct from executable behavior."""

from __future__ import annotations

import json
from pathlib import Path

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.freshness_wording import SOURCE_CHANGED_STRUCTURE_UNCHANGED
from llm_wiki_cli.services.health_summary import FRESHNESS_DISCLOSURE
from llm_wiki_cli.services.mcp_server import McpWikiService

SOURCE = '''class Batch:
    """Keep permitted items."""
    def cap(self, values: list[int], limit: int = 3) -> list[int]:
        return values[:limit]
'''
LOCATOR = "llm-wiki://entities/Batch"


def _wiki_bytes(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_breaking_slice_change_has_equivalent_truthful_live_presentations(
    tmp_path, monkeypatch, capsys,
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    policy = source / "policy.py"
    policy.write_text(SOURCE)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    wiki = tmp_path / "wiki"
    before = _wiki_bytes(wiki)
    changed = SOURCE.replace("values[:limit]", "values[:limit - 1]")
    # Only the owned fixture is executed, independently of the product parser.
    values = []
    for text in (SOURCE, changed):
        namespace = {}
        exec(compile(text, "owned-batch-fixture.py", "exec"), namespace)
        values.append(namespace["Batch"]().cap([1, 2, 3]))
    assert values == [[1, 2, 3], [1, 2]]
    policy.write_text(changed)
    result = api.inspect_concept(LOCATOR, src_dir="src", wiki_dir="wiki", live=True)
    inspected = result["concept"]
    assert inspected is not None
    concept = inspected["concept"]
    assert concept is not None
    fresh = concept["freshness"]
    assert fresh["state"] == "nonsemantic-source-change"
    assert fresh["hint"] == SOURCE_CHANGED_STRUCTURE_UNCHANGED
    assert fresh["live_comparison_performed"] is True
    mcp = McpWikiService(src_dir="src", wiki_dir="wiki")
    assert mcp.inspect_concept(LOCATOR, live=True)["concept"]["concept"]["freshness"] == fresh
    queue = api.build_maintenance_queue("src", "wiki")
    item = next(row for row in queue["items"] if row["path"] == "entities/Batch.md")
    assert item["freshness"]["description"] == SOURCE_CHANGED_STRUCTURE_UNCHANGED
    monkeypatch.setattr("sys.argv", ["llm-wiki", "queue", "--src-dir", "src", "--wiki-dir", "wiki", "--format", "json"])
    cli.main()
    assert json.loads(capsys.readouterr().out) == queue
    snapshot = api.inspect_concept(LOCATOR, src_dir="src", wiki_dir="wiki")
    snapshot_concept = snapshot["concept"]
    assert snapshot_concept is not None
    snapshot_record = snapshot_concept["concept"]
    assert snapshot_record is not None
    assert snapshot_record["freshness"]["state"] is None
    assert snapshot_record["freshness"]["live_comparison_performed"] is False
    assert _wiki_bytes(wiki) == before


def test_health_disclosure_names_structural_qualification():
    assert SOURCE_CHANGED_STRUCTURE_UNCHANGED in FRESHNESS_DISCLOSURE
    assert "Unknown" in FRESHNESS_DISCLOSURE
    assert "zero confirmed drift alone does not establish currentness" in FRESHNESS_DISCLOSURE
