"""Packed storage preserves logical evidence and bounded, explicitly scoped reads."""

from copy import deepcopy
from importlib.resources import files
import json
import os
import shutil
import subprocess
import sys
from typing import Any
import zlib

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.cli import main
from llm_wiki_cli.services import knowledge_packs as packs
from llm_wiki_cli.services.knowledge_artifacts import (
    CommitStage, build_knowledge_commit_plan, commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError, canonical_bytes, digest
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage_diagnostics import storage_report, review_storage
from llm_wiki_cli.services.knowledge_storage_io import StorageReadSession
from llm_wiki_cli.services.knowledge_storage_lifecycle import (
    migrate_knowledge_storage, recover_knowledge_storage, prune_knowledge_storage, export_knowledge_v1,
)
from llm_wiki_cli.services.task_contract import TASK_RESULT_SCHEMA_V2
from llm_wiki_cli.services.workflow_profile import canonical_json, content_id
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_loader import _committed_state


@pytest.fixture(params=["stored", "deflate"])
def compression(request):
    return request.param


def store(compression="stored"):
    logical = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    return logical, packs.build_packed_store(logical, compression=compression)


def reader(plan, objects=None, *, selected=False, **limits):
    objects = plan.objects if objects is None else objects
    def whole(name, maximum):
        assert len(objects[name]) <= maximum
        return objects[name]
    def part(name, offset, length, file_bytes):
        assert len(objects[name]) == file_bytes
        return objects[name][offset:offset + length]
    return packs.open_knowledge_store(plan.root_bytes, whole, read_range=part if selected else None, **limits)


def committed(root, compression="stored"):
    root.mkdir(exist_ok=True)
    _, previous, _ = _committed_state(root)
    mode = "packed-v3-deflate" if compression == "deflate" else "packed-v3"
    migrate_knowledge_storage(root, to=mode, recovery_dir=root.parent / (root.name + "-recovery"))
    return previous


def request():
    return {"schema_version": "llm-wiki-task-request/v2", "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
            "requirements": [{"id": "concept", "facet": "concept", "selector": "entities/AccountService.md"}]}


def test_full_roundtrip_and_selected_independent_facts(compression):
    logical, plan = store(compression)
    assert reader(plan).materialize() == logical
    assert plan == packs.build_packed_store(deepcopy(logical), compression=compression)
    assert len(plan.objects) == 3
    selected = reader(plan, selected=True).select(["source:src/accounts.py"]).to_payload()
    assert selected["archive_validation_scope"] == "selected-members"
    assert selected["whole_store_validated"] is False
    assert {c["value"]["title"] for c in selected["records"]["concepts"]} >= {"User", "AccountService"}
    assert all(len(raw) <= packs.MAX_PACK_BYTES for raw in plan.objects.values())


def test_schemas_resolve_offline_for_both_physical_encodings(compression):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    names = ["llm-wiki-knowledge-v1.schema.json", "llm-wiki-knowledge-v2.schema.json",
             "llm-wiki-knowledge-v3.schema.json", "llm-wiki-knowledge-pack-index-v1.schema.json"]
    schemas = [json.loads(files("llm_wiki_cli").joinpath("schemas").joinpath(name).read_text()) for name in names]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    _, plan = store(compression)
    Draft202012Validator(schemas[2], registry=registry).validate(json.loads(plan.root_bytes))
    for name, raw in plan.objects.items():
        if packs.INDEX_NAME.fullmatch(name):
            Draft202012Validator(schemas[3], registry=registry).validate(json.loads(raw))


def test_full_audit_hash_work_does_not_grow_with_members_per_pack(monkeypatch, compression):
    logical, plan = store(compression)
    observations = {raw: 0 for raw in plan.objects.values()}
    original = packs.digest
    def counted(raw):
        if raw in observations:
            observations[raw] += 1
        return original(raw)
    monkeypatch.setattr(packs, "digest", counted)
    assert reader(plan).materialize() == logical
    for name, raw in plan.objects.items():
        # Once before exposing members; once again in the complete ZIP audit.
        expected = 2 if packs.PACK_NAME.fullmatch(name) else 1
        assert observations[raw] == expected


def test_pack_cache_rejects_mutable_input_buffers():
    _, plan = store()
    def mutable(name, maximum) -> Any:
        return bytearray(plan.objects[name])
    with pytest.raises(KnowledgeStorageError, match="immutable bytes"):
        packs.PackedKnowledgeStoreReader(plan.root_bytes, mutable).materialize()


def test_selected_read_does_not_promote_unread_archive_metadata(compression):
    _, plan = store(compression)
    changed = dict(plan.objects)
    name = next(n for n in changed if packs.PACK_NAME.fullmatch(n))
    changed[name] = changed[name][:-1] + b"\x01"
    selected = reader(plan, changed, selected=True).select(["source:src/accounts.py"]).to_payload()
    assert not selected["whole_store_validated"] and selected["records"]["concepts"]
    with pytest.raises(KnowledgeStorageError, match="checksum"):
        reader(plan, changed).materialize()


def test_selected_member_corruption_and_lost_member_cannot_be_empty_success(compression):
    _, plan = store(compression)
    probe = reader(plan, selected=True)
    assert isinstance(probe, packs.PackedKnowledgeStoreReader)
    probe.select(["source:src/accounts.py"])
    descriptor, position = next(iter(probe._selected_locations.values()))
    path = packs.pack_path(descriptor)
    changed = dict(plan.objects)
    target = position[1] + 30 + len(position[0])
    raw = bytearray(changed[path])
    raw[target] ^= 1
    changed[path] = bytes(raw)
    with pytest.raises(KnowledgeStorageError):
        reader(plan, changed, selected=True).select(["source:src/accounts.py"])


@pytest.mark.parametrize("mutation", ["offset", "size", "name", "wrong-bucket", "missing", "extra", "wrong-prefix"])
def test_rehashed_routing_lies_are_detected(mutation):
    _, plan = store()
    physical = dict(plan.objects)
    root = json.loads(plan.root_bytes)
    name = packs.index_path(root["packing"]["catalog"]["hash"])
    node = json.loads(physical[name])
    key = next(iter(node["members"]))
    if mutation == "offset":
        node["members"][key][2] += 1
    elif mutation == "size":
        node["members"][key][4] += 1
    elif mutation == "name":
        node["members"][key][1] = "../../outside"
    elif mutation == "wrong-bucket":
        node["members"][key][0] = "101101"
    elif mutation == "missing":
        del node["members"][key]
    elif mutation == "extra":
        node["members"]["0" * 64] = node["members"][key]
    else:
        node["prefix"] = "1"
    raw = canonical_bytes(node)
    physical[packs.index_path(digest(raw))] = raw
    root["packing"]["catalog"] = {"hash": digest(raw), "bytes": len(raw), "count": len(node["members"])}
    root["packing"]["objects"] = len(node["members"])
    with pytest.raises(KnowledgeStorageError):
        packs.open_knowledge_store(canonical_bytes(root), lambda n, _: physical[n]).materialize()


@pytest.mark.parametrize("mutation", ["trailing", "timestamp", "method", "directory-count", "directory-name", "compressed-size", "nul-in-directory-name"])
def test_full_archive_structure_checked_even_with_rehashed_container(mutation, compression):
    _, plan = store(compression)
    root = json.loads(plan.root_bytes)
    node = json.loads(plan.objects[packs.index_path(root["packing"]["pack_catalog"]["hash"])])
    descriptor = deepcopy(next(iter(node["packs"].values())))
    raw = bytearray(plan.objects[packs.pack_path(descriptor)])
    if mutation == "trailing":
        raw += b"x"
    elif mutation == "timestamp":
        raw[10] ^= 1
    elif mutation == "method":
        raw[8] = 99
    elif mutation == "directory-count":
        raw[-12] ^= 1
    elif mutation == "directory-name":
        central = raw.index(b"PK\x01\x02")
        raw[central + 46] ^= 1
    elif mutation == "nul-in-directory-name":
        central = raw.index(b"PK\x01\x02")
        name_length = int.from_bytes(raw[central + 28:central + 30], "little")
        suffix = b"\0hidden"
        raw[central + 46 + name_length:central + 46 + name_length] = suffix
        raw[central + 28:central + 30] = (name_length + len(suffix)).to_bytes(2, "little")
        footer = list(packs._END.unpack(raw[-22:]))
        footer[5] += len(suffix)
        raw[-22:] = packs._END.pack(*footer)
    else:
        raw[18] ^= 1
    descriptor.update(hash=digest(bytes(raw)), bytes=len(raw))
    with pytest.raises(KnowledgeStorageError):
        packs.validate_pack(bytes(raw), descriptor, compression)


def test_pack_and_catalog_splitting_are_bounded_and_local(monkeypatch):
    logical, _ = store()
    logical.setdefault("extensions", {}).update({f"fixture/{i}": str(i) * 1000 for i in range(40)})
    monkeypatch.setattr(packs, "PACK_TARGET_BYTES", 16_384)
    monkeypatch.setattr(packs, "MAX_INDEX_BYTES", 4096)
    original = packs.build_packed_store(logical)
    assert original.statistics["packs"] > 2 and original.statistics["indexes"] > 2
    assert reader(original).materialize() == logical
    logical["extensions"]["fixture/4"] = "new content"
    edited = packs.build_packed_store(logical)
    common = set(original.objects) & set(edited.objects)
    assert common and len(common) > len(original.objects) // 2
    assert all(original.objects[n] == edited.objects[n] for n in common)
    assert reader(edited).materialize() == logical


def test_limits_stop_before_publishing_or_excessive_member_expansion(monkeypatch, compression):
    logical, plan = store(compression)
    with pytest.raises(KnowledgeStorageError, match="budget"):
        reader(plan, selected=True, max_bytes=100).select(["source:src/accounts.py"])
    monkeypatch.setattr(packs, "MAX_PACK_BYTES", 256)
    with pytest.raises(KnowledgeStorageError, match="ceiling"):
        packs.build_packed_store(logical, compression=compression)


def test_guarded_ranges_recheck_content_inode_and_ancestors(tmp_path, compression):
    wiki = tmp_path / "wiki"
    committed(wiki, compression)
    capture = capture_knowledge_slice(wiki, ["source:src/accounts.py"])
    assert capture.session.range_observations
    assert not any(packs.PACK_NAME.fullmatch(n) for n in capture.session.observations)
    key, observed = next(iter(capture.session.range_observations.items()))
    path = wiki / key[0]
    before = path.stat()
    content = bytearray(path.read_bytes())
    content[key[1]] ^= 1
    path.write_bytes(content)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(KnowledgeStorageError):
        capture.finish()
    # A new request cannot pass with the damaged selected member.
    with pytest.raises(KnowledgeStorageError):
        capture_knowledge_slice(wiki, ["source:src/accounts.py"])
    assert observed.content


@pytest.mark.skipif(os.name == "nt", reason="POSIX link setup; native Windows guard lane owns its equivalent")
@pytest.mark.parametrize("link", ["symbolic", "hard", "parent"])
def test_ranges_never_follow_untrusted_links(tmp_path, link):
    root = tmp_path / "wiki"
    root.mkdir()
    target = tmp_path / "bytes"
    target.write_bytes(b"abc")
    if link == "symbolic":
        (root / "member").symlink_to(target)
        name = "member"
    elif link == "hard":
        os.link(target, root / "member")
        name = "member"
    else:
        (root / "parent").symlink_to(tmp_path, target_is_directory=True)
        name = "parent/bytes"
    with pytest.raises(KnowledgeStorageError):
        StorageReadSession(root).read_range(name, 0, 1, 3)


def test_explicit_migration_cleanup_recovery_and_export_preserve_authority(tmp_path, compression):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _, old, _ = _committed_state(wiki)
    before = {p.name: p.read_bytes() for p in wiki.rglob("*.md")}
    mode = "packed-v3-deflate" if compression == "deflate" else "packed-v3"
    recovery = tmp_path / "recovery"
    preview = migrate_knowledge_storage(wiki, to=mode, dry_run=True, recovery_dir=recovery)
    assert preview["changed"] and not recovery.exists()
    migrate_knowledge_storage(wiki, to=mode, recovery_dir=recovery)
    assert not migrate_knowledge_storage(wiki, to=mode)["changed"]
    assert storage_report(wiki, full=True)["ok"]
    assert load_knowledge_state(wiki).knowledge is not None
    export = tmp_path / "export.json"
    export_knowledge_v1(wiki, export)
    assert export.read_bytes() == old.knowledge_index.content
    assert {p.name: p.read_bytes() for p in wiki.rglob("*.md")} == before
    recover_knowledge_storage(wiki, recovery)
    assert (wiki / ".llm-wiki-knowledge.json").read_bytes() == old.knowledge_index.content
    # Re-adoption keeps its original recovery record reusable.
    migrate_knowledge_storage(wiki, to=mode, recovery_dir=recovery)
    # Return to v2 and remove both pack and locator namespaces through owning cleanup.
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir=tmp_path / "packed-recovery")
    preview = prune_knowledge_storage(wiki)
    assert any(packs.PACK_NAME.fullmatch(n) for n in preview["unreferenced_objects"])
    assert any(packs.INDEX_NAME.fullmatch(n) for n in preview["unreferenced_objects"])
    prune_knowledge_storage(wiki, dry_run=False)
    assert storage_report(wiki, full=True)["ok"]
    recover_knowledge_storage(wiki, tmp_path / "packed-recovery")
    assert storage_report(wiki, full=True)["format"] == mode


@pytest.mark.parametrize("stage", [CommitStage.KNOWLEDGE_OBJECTS_WRITTEN, CommitStage.KNOWLEDGE_INDEX_WRITTEN])
def test_interrupted_pack_migration_recovers_exact_snapshot(tmp_path, monkeypatch, stage):
    from llm_wiki_cli.services import knowledge_storage_lifecycle as lifecycle
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _, old, _ = _committed_state(wiki)
    def interrupted(plan):
        def inject(observed):
            if observed == stage:
                raise RuntimeError("interrupt")
        return commit_knowledge_artifacts(plan, fault_injector=inject)
    monkeypatch.setattr(lifecycle, "commit_knowledge_artifacts", interrupted)
    with pytest.raises(RuntimeError, match="interrupt"):
        migrate_knowledge_storage(wiki, to="packed-v3", recovery_dir=tmp_path / "recovery")
    recover_knowledge_storage(wiki, tmp_path / "recovery")
    assert (wiki / ".llm-wiki-knowledge.json").read_bytes() == old.knowledge_index.content


def test_task_sessions_disclose_ranges_and_reject_replaced_packs(tmp_path, monkeypatch, compression):
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / "wiki"
    committed(wiki, compression)
    req = request()
    with api.open_context_session(wiki_dir="wiki") as session:
        first = session.read(req)
        assert first.context is not None
        data = api.validate_task_context(first.context.rendered, req)
        assert data["state"] == "covered" and data["packet"] is None
        assert data["storage"]["schema_version"] == "llm-wiki-task-storage/v2"
        assert data["storage"]["ranges"] and data["storage"]["archive_validation_scope"] == "selected-members"
        assert first.metadata()["work"]["validation_observed"]["wiki_bytes"] == data["storage"]["read_bytes"]
        assert session.read(req, if_result_id=first.result_id).state == "unchanged"
        cold = session.read(req, reuse=False)
        assert cold.context is not None and cold.context.rendered == first.context.rendered
        selected = data["storage"]["ranges"][0]
        path = wiki / selected["path"]
        replacement = path.with_suffix(".replacement")
        replacement.write_bytes(path.read_bytes())
        os.replace(replacement, path)
        # A cache hit must re-capture after identity replacement, even when bytes agree.
        reply = session.read(req, if_result_id=first.result_id)
        assert not reply.metadata()["reuse"]["rendering"]


@pytest.mark.parametrize("mutation", ["whole-archive", "offset", "size", "duplicate", "cost", "path"])
def test_rehashed_range_receipt_claims_are_rejected(tmp_path, monkeypatch, mutation):
    monkeypatch.chdir(tmp_path)
    committed(tmp_path / "wiki")
    req = request()
    payload = api.build_task_context(req, wiki_dir="wiki").to_payload()
    storage = payload["storage"]
    if mutation == "whole-archive":
        storage["archive_validation_scope"] = "full"
    elif mutation == "offset":
        storage["ranges"][0]["offset"] = -1
    elif mutation == "size":
        storage["ranges"][0]["file_bytes"] = 0
    elif mutation == "duplicate":
        storage["ranges"].append(storage["ranges"][0])
    elif mutation == "cost":
        storage["read_bytes"] -= 1
    else:
        storage["ranges"][0]["path"] = "../outside.zip"
    payload["result_id"] = content_id(TASK_RESULT_SCHEMA_V2, {k: v for k, v in payload.items() if k != "result_id"})
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(canonical_json(payload).decode(), req)


def test_logical_review_is_format_independent_and_output_bounded(tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _committed_state(wiki)
    before = tmp_path / "before"
    shutil.copytree(wiki, before)
    migrate_knowledge_storage(wiki, to="packed-v3", recovery_dir=tmp_path / "recovery")
    assert review_storage(wiki, against=before)["total"] == 0
    limited = review_storage(wiki, limit=1, max_bytes=1024)
    assert not limited["complete"] and limited["omitted"]
    assert len(canonical_bytes(limited)) <= 1024
    full = review_storage(wiki)
    assert full["records"] and full["total"] > 1


def test_cli_bootstrap_and_sync_keep_packed_adoption(tmp_path, monkeypatch, capsys, compression):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("def limit(value=3):\n    return value\n")
    mode = "packed-v3-deflate" if compression == "deflate" else "packed-v3"
    def command(*args):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", *args])
        main()
        return capsys.readouterr().out
    command("bootstrap", "--src-dir", ".", "--wiki-dir", "wiki", "--knowledge-format", mode,
            "--skip-flows", "--skip-workflows", "--skip-dependencies")
    command("knowledge", "init", "--wiki-dir", "wiki")
    command("sync", "--src-dir", ".", "--wiki-dir", "wiki", "--no-plugins", "--no-cache")
    wiki = tmp_path / "wiki"
    state = load_knowledge_state(wiki)
    assert state.knowledge is not None and state.manifest_basis is not None
    previous = state.validated_artifacts
    assert previous is not None
    root_before = (wiki / ".llm-wiki-knowledge.json").read_bytes()
    command("sync", "--src-dir", ".", "--wiki-dir", "wiki", "--no-plugins", "--no-cache")
    assert (wiki / ".llm-wiki-knowledge.json").read_bytes() == root_before
    report = json.loads(command("knowledge", "storage-check", "--wiki-dir", "wiki", "--full"))
    assert report["ok"] and report["format"] == mode and report["physical_packs"]
    result = json.loads(command("knowledge", "inspect-storage", "--wiki-dir", "wiki", "--limit", "1"))
    assert result["operation"] == "inspect" and not result["complete"]
    plan = build_knowledge_commit_plan(wiki, surface_index_bytes=(wiki / ".llm-wiki-surface.json").read_bytes(),
        knowledge_index=state.knowledge, manifest=state.manifest_basis.without_artifact_hashes())
    assert plan.storage_format == mode and not plan.changed


def test_deflate_member_stops_at_authenticated_expansion_limit():
    original = b"A" * 100_000
    encoder = zlib.compressobj(6, wbits=-15)
    compressed = encoder.compress(original) + encoder.flush()
    name = "extensions/root.json"
    declared = 512
    crc = zlib.crc32(original)
    header = packs._LOCAL_HEADER.pack(b"PK\x03\x04", 20, 0, 8, 0, 33, crc, len(compressed), declared, len(name), 0)
    raw = header + name.encode() + compressed
    with pytest.raises(KnowledgeStorageError, match="expansion"):
        packs.decode_member(raw, [name, 0, len(compressed), declared, crc], "deflate", digest(original))


def test_corrupt_or_unknown_orphans_are_retained_by_cleanup(tmp_path):
    wiki = tmp_path / "wiki"
    previous = committed(wiki)
    _, another = store("deflate")
    orphan_pack = next(n for n in another.objects if packs.PACK_NAME.fullmatch(n))
    path = wiki / orphan_pack
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not a generated ZIP")
    unknown = wiki / packs.PACK_DIRECTORY / "user-notes.txt"
    unknown.write_text("authored")
    report = prune_knowledge_storage(wiki, dry_run=False)
    assert orphan_pack in report["retained"] and unknown.relative_to(wiki).as_posix() in report["retained"]
    assert path.exists() and unknown.read_text() == "authored"
    assert previous.knowledge_index.content


def test_selected_scope_does_not_rely_on_packwide_reads(tmp_path, monkeypatch):
    wiki = tmp_path / "wiki"
    committed(wiki)
    original = StorageReadSession.read
    def forbid_pack(self, relative, maximum):
        assert not packs.PACK_NAME.fullmatch(relative), "selected query read an entire archive"
        return original(self, relative, maximum)
    monkeypatch.setattr(StorageReadSession, "read", forbid_pack)
    selected = capture_knowledge_slice(wiki, ["source:src/accounts.py"])
    assert selected.finish()["bytes_read"] < 8_388_608


def test_range_rejects_file_size_lies_and_counts_final_reads(tmp_path):
    (tmp_path / "pack").write_bytes(b"0123456789")
    session = StorageReadSession(tmp_path, max_bytes=8)
    assert session.read_range("pack", 2, 4, 10) == b"2345"
    session.recheck()
    assert session.receipt()["bytes_read"] == 8
    with pytest.raises(KnowledgeStorageError, match="budget"):
        session.recheck()
    with pytest.raises(KnowledgeStorageError, match="size"):
        StorageReadSession(tmp_path).read_range("pack", 0, 1, 9)


def test_divergent_pack_generations_merge_after_explicit_logical_regeneration(tmp_path, compression):
    logical, first = store(compression)
    left, right, joined = deepcopy(logical), deepcopy(logical), deepcopy(logical)
    left.setdefault("extensions", {})["consumer/left"] = "left fact"
    right.setdefault("extensions", {})["consumer/right"] = "right fact"
    joined.setdefault("extensions", {}).update({"consumer/left": "left fact", "consumer/right": "right fact"})
    git = ["git", "-C", str(tmp_path), "-c", "user.name=Pack Fixture", "-c", "user.email=packs@example.invalid",
           "-c", "commit.gpgSign=false", "-c", "core.hooksPath=/dev/null"]
    def run(*args, check=True):
        return subprocess.run([*git, *args], check=check, capture_output=True)
    def install(plan):
        shutil.rmtree(tmp_path / ".llm-wiki-knowledge", ignore_errors=True)
        for name, raw in {"root.json": plan.root_bytes, **plan.objects}.items():
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        run("add", "--all")
    run("init", "--initial-branch=fixture")
    install(first)
    run("commit", "-qm", "base")
    base = run("rev-parse", "HEAD").stdout.decode().strip()
    run("switch", "--no-track", "-c", "left", base)
    assert not run("for-each-ref", "--format=%(upstream:short)", "refs/heads/left").stdout.strip()
    install(packs.build_packed_store(left, compression=compression))
    run("commit", "-qm", "left")
    run("switch", "--no-track", "-c", "right", base)
    assert not run("for-each-ref", "--format=%(upstream:short)", "refs/heads/right").stdout.strip()
    install(packs.build_packed_store(right, compression=compression))
    run("commit", "-qm", "right")
    merge = run("merge", "--no-commit", "left", check=False)
    assert merge.returncode == 1 and b"root.json" in run("diff", "--name-only", "--diff-filter=U").stdout
    combined = packs.build_packed_store(joined, compression=compression)
    install(combined)
    run("commit", "-qm", "regenerate combined knowledge")
    loaded = packs.open_knowledge_store((tmp_path / "root.json").read_bytes(), lambda name, _: (tmp_path / name).read_bytes())
    assert loaded.materialize() == joined
    assert len(run("rev-list", "--parents", "-n", "1", "HEAD").stdout.split()) == 3
    assert not run("status", "--porcelain").stdout
