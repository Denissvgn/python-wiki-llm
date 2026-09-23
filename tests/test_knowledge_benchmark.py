"""Exercise benchmark result variants against real disposable storage."""

import json

import pytest

from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from tests import knowledge_performance_benchmark as benchmark
from tests.test_knowledge_loader import _committed_state


@pytest.mark.parametrize("workload", [
    "slice_concept", "slice_module", "task_cold", "session_warm", "full_load",
    "storage_full", "inspect_one", "inspect_scoped", "audit_stream",
    "plan_unchanged", "plan_reuse", "incremental", "prune_preview",
])
def test_readonly_benchmark_variants_keep_serializable_measurements(tmp_path, monkeypatch, workload):
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _committed_state(wiki)
    migrate_knowledge_storage(wiki, to="packed-v3-deflate", recovery_dir=tmp_path / "recovery")
    output = tmp_path / "profiles"
    output.mkdir()
    for name, value in {
        "ROOT": tmp_path, "WIKI": wiki, "OUT": output,
        "PAGE": "entities/AccountService.md", "ALLOW_WRITES": False,
        "SELECTORS": {"concept": "page:entities/AccountService.md", "module": "source:src/accounts.py"},
    }.items():
        monkeypatch.setattr(benchmark, name, value)
    before = benchmark.artifact_tree(wiki)
    profiled = workload == "full_load"
    result = benchmark.worker(workload, profiled)
    assert json.loads(json.dumps(result)) == result
    assert result["ok"] and result["workload"] == workload
    assert result["measurement"]["wall_ns"] > 0
    assert result["details"]["artifact_changes"] == {"files": 0, "bytes_written": 0, "bytes_removed": 0}
    assert benchmark.artifact_tree(wiki) == before
    if profiled:
        assert result["profile"]["total_calls"] > 0
        assert result["profile"]["top_self"] and result["profile"]["selected_functions"]
        assert (output / "full_load.prof").is_file()
