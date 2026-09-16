"""Generate and qualify large packed stores in a disposable directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import tracemalloc

from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan
from llm_wiki_cli.services.knowledge_index import serialize_knowledge_index
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_packs import PACK_NAME, build_packed_store, open_knowledge_store
from llm_wiki_cli.services.knowledge_storage import digest
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from tests.knowledge_storage_scale import large_logical_payload
from tests.test_knowledge_loader import _committed_state


def git_history(work: Path, generations: list[dict[str, bytes]]) -> dict:
    work.mkdir()
    command = ["git", "-C", str(work), "-c", "user.name=Pack Fixture",
               "-c", "user.email=packs@example.invalid", "-c", "commit.gpgSign=false",
               "-c", "core.hooksPath=/dev/null", "-c", "gc.auto=0"]
    def run(*args, **kwargs):
        return subprocess.run([*command, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True, **kwargs).stdout
    run("init", "--initial-branch=fixture")
    previous = set()
    sizes, diffs = [], []
    for index, files in enumerate(generations):
        for name in previous - files.keys():
            (work / name).unlink()
        for name, raw in files.items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        run("add", "--all")
        run("commit", "-q", "-m", f"generation-{index}")
        assert not run("for-each-ref", "--format=%(upstream:short)", "refs/heads/fixture").strip()
        packed = run("-c", "pack.threads=1", "pack-objects", "--stdout", "--revs", "--window=10", "--depth=50", input=b"HEAD\n")
        sizes.append(len(packed))
        if index:
            diffs.append(run("diff", "--shortstat", "HEAD^", "HEAD").decode().strip())
        previous = set(files)
    return {"history_pack_bytes": sizes, "incremental_pack_bytes": [b - a for a, b in zip(sizes, sizes[1:])],
            "diffs": diffs, "path_layout": "actual content-addressed filenames with stable bucket suffixes and bounded prefix directories"}


def qualify(work: Path, *, compression: str, blocks: int = 900) -> dict:
    wiki = work / "wiki"
    wiki.mkdir(parents=True)
    _, original, _ = _committed_state(wiki)
    logical = large_logical_payload(original.knowledge_index.content, blocks=blocks)
    legacy = serialize_knowledge_index(logical).encode()
    assert len(legacy) > 100 * 1024 * 1024
    legacy_bytes, legacy_hash = len(legacy), hashlib.sha256(legacy).hexdigest()
    marker = original.committed_manifest.artifact_hashes
    assert marker is not None
    manifest = original.committed_manifest.with_artifact_hashes(surface_index_hash=marker.surface_index_hash,
        knowledge_index_hash=digest(legacy), evaluated_envelope_hash=marker.evaluated_envelope_hash,
        governance_hash=marker.governance_hash)
    # Seed an inherited monolith, not a new oversized product generation.
    (wiki / ".llm-wiki-knowledge.json").write_bytes(legacy)
    (wiki / ".llm-wiki-manifest.json").write_text(json.dumps(manifest.to_payload(), indent=2, sort_keys=True) + "\n")
    del legacy
    mode = "packed-v3" if compression == "stored" else "packed-v3-deflate"
    started = time.perf_counter_ns()
    migrated = migrate_knowledge_storage(wiki, to=mode, recovery_dir=work / "recovery")
    migration_ns = time.perf_counter_ns() - started
    tracemalloc.start()
    started = time.perf_counter_ns()
    selected = capture_knowledge_slice(wiki, ["source:src/accounts.py"])
    result = selected.slice.to_payload()
    receipt = selected.finish()
    selected_ns = time.perf_counter_ns() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert receipt["bytes_read"] <= 8_388_608
    assert not any(PACK_NAME.fullmatch(p) for p in selected.session.observations)
    assert result["archive_validation_scope"] == "selected-members" and not result["whole_store_validated"]
    assert {c["value"]["title"] for c in result["records"]["concepts"]} >= {"User", "AccountService"}
    state = load_knowledge_state(wiki)
    assert state.knowledge is not None and state.validated_artifacts is not None
    root = (wiki / ".llm-wiki-knowledge.json").read_bytes()
    files = dict(state.validated_artifacts.storage_objects)
    reader = open_knowledge_store(root, lambda name, _: files[name])
    assert reader.materialize() == logical
    assert hashlib.sha256(serialize_knowledge_index(state.knowledge).encode()).hexdigest() == legacy_hash
    repeat = build_knowledge_commit_plan(wiki, surface_index_bytes=original.surface_index.content,
        knowledge_index=state.knowledge, manifest=manifest.without_artifact_hashes())
    assert not repeat.changed
    first = {"root.json": root, **files}
    old = logical["extensions"]["storage-scale/record-000005"]
    logical["extensions"]["storage-scale/record-000005"] = ("0" if old[0] != "0" else "1") + old[1:]
    edit = build_packed_store(logical, compression=compression)
    changed = {p: raw for p, raw in edit.objects.items() if files.get(p) != raw}
    assert sum(map(len, changed.values())) < 16 * 1024 * 1024
    # A larger edit includes insertions/removals as well as existing-record changes.
    del logical["extensions"]["storage-scale/record-000010"]
    logical["extensions"]["storage-scale/inserted"] = "new record " * 1000
    for index in range(20, 30):
        key = f"storage-scale/record-{index:06d}"
        logical["extensions"][key] = logical["extensions"][key][::-1]
    broad = build_packed_store(logical, compression=compression)
    history = git_history(work / "git-history", [first, {"root.json": edit.root_bytes, **edit.objects},
                          {"root.json": broad.root_bytes, **broad.objects}])
    return {"schema_version": "llm-wiki-pack-scale-evidence/v1", "seed": 260916, "blocks": blocks,
            "compression": compression, "legacy_bytes": legacy_bytes, "legacy_sha256": legacy_hash,
            "migration": migrated, "selected": receipt, "selected_peak_allocated_bytes": peak,
            "migration_ns": migration_ns, "selected_ns": selected_ns,
            "largest_file_bytes": max(map(len, files.values())),
            "single_edit": {"changed_files": len(changed), "changed_bytes": sum(map(len, changed.values()))},
            "git_history": history,
            "assertions": {"independent_facts": True, "logical_equality": True, "legacy_byte_parity": True,
                           "no_op_repeat": True, "bounded_selected_read": True, "no_whole_pack_selected_read": True,
                           "limited_local_edit_bytes": True},
            "limitations": ["synthetic varied extensions, not universal latency or compression evidence",
                            "Git history uses three revisions including a broad edit; no remote publication",
                            "OS filesystem cache not cleared"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compression", choices=["stored", "deflate"], required=True)
    args = parser.parse_args()
    result = qualify(args.work, compression=args.compression)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("compression", "largest_file_bytes", "single_edit", "assertions")}))


if __name__ == "__main__":
    main()
