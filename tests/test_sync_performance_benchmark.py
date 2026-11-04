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


def test_tree_hash_does_not_confuse_file_bytes_with_namespace_boundaries(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    # Both layouts previously encoded as b"a\x001b\x00qc\x00r", with
    # two files and five content bytes, despite different names and contents.
    (first / "a").write_bytes(b"1b\x00q")
    (first / "c").write_bytes(b"r")
    (second / "a").write_bytes(b"1")
    (second / "b").write_bytes(b"qc\x00r")
    a, b = benchmark.tree_summary(first), benchmark.tree_summary(second)
    assert a["files"] == b["files"] == 2
    assert a["bytes"] == b["bytes"] == 5
    assert a["hash_encoding"] == b["hash_encoding"] == "path-size-content-sha256/v1"
    assert a["sha256"] != b["sha256"]


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
