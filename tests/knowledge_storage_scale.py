"""Generate large native data and qualify bounded sharded reads outside the repo."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
try:
    import resource
except ImportError:  # Native Windows reports allocation peaks without getrusage.
    resource = None
import time
import tracemalloc

from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts, build_knowledge_commit_plan, validated_artifact_bytes
from llm_wiki_cli.services.knowledge_index import serialize_knowledge_index
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import KnowledgeStoreReader, build_knowledge_store, digest
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from tests.test_knowledge_loader import _committed_state


def large_logical_payload(original: bytes, *, blocks: int, block_bytes: int = 131_072):
    payload = json.loads(original)
    extensions = payload.setdefault("extensions", {})
    for index in range(blocks):
        # Varied deterministic bytes prevent a repeated-padding fixture from
        # hiding read amplification behind unusually effective deduplication.
        extensions[f"storage-scale/record-{index:06d}"] = random.Random(260916 + index).randbytes(block_bytes // 2).hex()
    return payload


def qualify(work: Path, *, blocks: int = 900) -> dict:
    wiki = work / "wiki"
    wiki.mkdir(parents=True)
    fixture, original, _ = _committed_state(wiki)
    payload = large_logical_payload(original.knowledge_index.content, blocks=blocks)
    legacy = serialize_knowledge_index(payload).encode("utf-8")
    legacy_size = len(legacy)
    assert len(legacy) > 100 * 1024 * 1024
    # Represent an already existing legacy commit, not a new v1 generation that
    # should be blocked by the new 95 MiB prepublication gate.
    marker = original.committed_manifest.artifact_hashes
    assert marker is not None
    manifest = original.committed_manifest.with_artifact_hashes(surface_index_hash=marker.surface_index_hash,
        knowledge_index_hash=digest(legacy), evaluated_envelope_hash=marker.evaluated_envelope_hash,
        governance_hash=marker.governance_hash)
    (wiki / ".llm-wiki-knowledge.json").write_bytes(legacy)
    (wiki / ".llm-wiki-manifest.json").write_text(json.dumps(manifest.to_payload(), sort_keys=True, indent=2) + "\n")
    legacy_hash = hashlib.sha256(legacy).hexdigest()
    del legacy
    started = time.perf_counter_ns()
    migrated = migrate_knowledge_storage(wiki, recovery_dir=work / "recovery")
    migrate_ns = time.perf_counter_ns() - started
    assert migrated["object_bytes"] >= 32 * 1024 * 1024
    tracemalloc.start()
    started = time.perf_counter_ns()
    read = capture_knowledge_slice(wiki, ["source:src/accounts.py"])
    selected = read.slice.to_payload()
    work_receipt = read.finish()
    selected_ns = time.perf_counter_ns() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert work_receipt["bytes_read"] <= 8_388_608
    assert all("storage-scale/" not in row["id"] for row in selected["records"]["extensions"])
    assert {row["value"]["title"] for row in selected["records"]["concepts"]} >= {"User", "AccountService"}
    assert selected["whole_store_validated"] is False
    del read
    started = time.perf_counter_ns()
    loaded = load_knowledge_state(wiki)
    full_ns = time.perf_counter_ns() - started
    artifacts = loaded.validated_artifacts
    assert loaded.knowledge is not None and artifacts is not None
    _, full_root = validated_artifact_bytes(artifacts)
    reader = KnowledgeStoreReader(full_root, lambda name, _: artifacts.storage_objects[name])
    decoded = reader.materialize()
    assert decoded == payload
    # Compare exact legacy encoding as well as the independently authored facts.
    assert hashlib.sha256(serialize_knowledge_index(decoded).encode()).hexdigest() == legacy_hash
    repeat = build_knowledge_commit_plan(wiki, surface_index_bytes=original.surface_index.content,
        knowledge_index=loaded.knowledge, manifest=manifest.without_artifact_hashes())
    assert not repeat.changed
    commit_knowledge_artifacts(repeat)
    largest = max(len(raw) for raw in artifacts.storage_objects.values())
    modified = {**payload, "extensions": dict(payload["extensions"])}
    old = modified["extensions"]["storage-scale/record-000005"]
    modified["extensions"]["storage-scale/record-000005"] = ("0" if old[0] != "0" else "1") + old[1:]
    edited = build_knowledge_store(modified)
    previous_objects = artifacts.storage_objects
    changed = {p: b for p, b in edited.objects.items() if p not in previous_objects}
    assert len(changed) <= 10 and sum(map(len, changed.values())) < 1_048_576
    return {"schema_version": "llm-wiki-storage-scale-evidence/v1", "seed": 260916, "blocks": blocks,
            "block_bytes": 131_072, "legacy_sha256": legacy_hash,
            "legacy_bytes": legacy_size,
            "store": {k: migrated[k] for k in ("root_bytes", "object_bytes", "object_count")},
            "largest_object_bytes": largest, "selected_work": work_receipt,
            "selected_allocated_peak_bytes": peak, "timings_ns": {"migration": migrate_ns, "selected": selected_ns, "full": full_ns},
            "single_edit": {"changed_objects": len(changed), "changed_object_bytes": sum(map(len, changed.values()))},
            "rss_peak_platform_units": None if resource is None else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "assertions": {"logical_equality": True, "exact_v1_encoding": True, "independent_fixture_facts": True,
                           "selected_budget": True, "scoped_not_full": True, "no_op_repeat": True, "local_edit_locality": True},
            "limitations": ["owned deterministic fixture; no general latency or model-benefit claim"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--blocks", type=int, default=900)
    args = parser.parse_args(argv)
    result = qualify(args.work, blocks=args.blocks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("store", "largest_object_bytes", "selected_allocated_peak_bytes", "assertions")}))


if __name__ == "__main__":
    main()
