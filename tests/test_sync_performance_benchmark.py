"""Disposable-workload and reproducibility guards for sync measurements."""

import json
from pathlib import Path

import pytest

from tests import sync_performance_benchmark as benchmark


def test_measurement_refuses_unmarked_checkout_before_sync(tmp_path):
    with pytest.raises(SystemExit) as error:
        benchmark.main(["--checkout", str(tmp_path), "--provider", str(tmp_path),
                        "--output", str(tmp_path / "result.json"), "--allow-writes"])
    assert error.value.code == 2
    assert not (tmp_path / "result.json").exists()


def test_tree_summary_streams_exact_names_and_bytes(tmp_path):
    (tmp_path / "page.md").write_bytes(b"one\r\ntwo\n")
    before = benchmark.tree_summary(tmp_path)
    assert before["files"] == 1 and before["bytes"] == 9
    (tmp_path / "page.md").rename(tmp_path / "other.md")
    assert benchmark.tree_summary(tmp_path)["sha256"] != before["sha256"]
    (tmp_path / "link").symlink_to(tmp_path / "other.md")
    with pytest.raises(ValueError, match="symbolic"):
        benchmark.tree_summary(tmp_path)


def test_adopted_noop_measurement_records_real_work(tmp_path, monkeypatch):
    from llm_wiki_cli import api
    import llm_wiki_cli
    from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority

    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def run(value=1):\n    return value + 1\n")
    api.bootstrap_wiki(str(source), str(tmp_path / "wiki"), knowledge_format="packed-v4-deflate")
    adopt_maintenance_authority(source, tmp_path / "wiki", recovery_dir=tmp_path / "adoption")
    (tmp_path / ".sync-performance-disposable").write_text("owned test fixture\n")
    output = tmp_path / "result.json"
    assert benchmark.main(["--checkout", str(tmp_path), "--wiki", "wiki", "--source", "src",
                           "--provider", str(Path(llm_wiki_cli.__file__).parent),
                           "--output", str(output), "--allow-writes"]) == 0
    result = json.loads(output.read_text())
    assert result["ok"] and result["wall_seconds"] > 0
    assert result["work_counts"]["validate_knowledge_artifacts"] >= 1
    assert result["provider_tree"]["files"] > 0
    assert result["wiki_after"]["files"] >= result["wiki_before"]["files"]
