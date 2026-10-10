"""Change, ordinary review and static relationships compose through real interfaces."""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import os
import subprocess
from hashlib import sha256

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from llm_wiki_cli.services.knowledge_governance import (
    load_governance,
    evaluate_review_event,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage import canonical_bytes
from llm_wiki_cli.services.maintenance_protocol import ADOPTION_FILENAME, snapshot_wiki
from llm_wiki_cli.services.mcp_server import McpWikiService, McpWikiError
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from tests.developer_value.oracles import apply_source_mutation, apply_prose_mutation
from tests.developer_value.fixtures import (
    POLICY_SOURCE,
    materialize,
    projects,
    source_hashes,
)
from tests.test_knowledge_loader import _committed_state

CLIENT = '"""Select a bounded view through explicit construction."""\nfrom policy import Batch, OtherBatch\n\ndef assigned_values(values: list[int]) -> list[int]:\n    batch = Batch()\n    return batch.cap(values)\n'
OTHER = '\nclass OtherBatch:\n    """Select the final allowed number of items."""\n    def cap(self, values: list[int], limit: int = 3) -> list[int]:\n        return values[-limit:]\n'


def _tree(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in Path(root).rglob("*")
        if path.is_file()
    }


def _cli(monkeypatch, capsys, *args, request=None, json_output=True):
    with monkeypatch.context() as patch:
        patch.setattr(sys, "argv", ["llm-wiki", *args])
        if request is not None:
            patch.setattr(sys, "stdin", io.StringIO(json.dumps(request)))
        cli.main()
    output = capsys.readouterr()
    return json.loads(output.out) if json_output else output.out


def _sync(monkeypatch, capsys):
    _cli(
        monkeypatch,
        capsys,
        "sync",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--no-plugins",
        json_output=False,
    )


def _caller_routes(selector, monkeypatch, capsys):
    request = {
        "operation": "symbol",
        "value": selector,
        "allow_full_inventory": True,
        "limit": 100,
    }
    mcp = McpWikiService("src", "wiki")
    return [
        dict(api.callers(selector, src_dir="src", wiki_dir="wiki", limit=100)),
        dict(api.query_documentation(request, src_dir="src", wiki_dir="wiki")),
        _cli(
            monkeypatch,
            capsys,
            "query",
            "--request",
            "-",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            request=request,
        ),
        mcp.query_graph({"type": "callers", "value": selector, "limit": 100}),
        mcp.query_documentation(request),
    ]


def _pairs(result):
    return {(row["file"], row["symbol"]) for row in result["callers"]}


def _status_routes(monkeypatch, capsys, record_id=None):
    args = [
        "maintenance",
        "status",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--format",
        "json",
    ]
    if record_id is not None:
        args.extend(["--record-id", record_id])
    return [
        dict(api.get_maintenance_status("src", "wiki", record_id=record_id)),
        _cli(monkeypatch, capsys, *args),
        McpWikiService("src", "wiki").get_maintenance_status(record_id=record_id),
    ]


def _client_record(status):
    return next(
        row
        for row in status["records"]
        if row["coordinate"]["source_path"] == "client.py"
        and row["target"]["canonical_path"] == "modules/client.md"
        and row["basis_available"]
    )


def _ack(status, row):
    assert status["state_hash"] is not None and row["expected_basis"] is not None
    return api.acknowledge_maintenance(
        "src",
        "wiki",
        record_id=row["record_id"],
        expected_state_hash=status["state_hash"],
        expected_basis=row["expected_basis"],
        actor_kind="agent",
        actor_id="composition-agent",
    )


@pytest.mark.parametrize(
    "project,storage", [("library", None), ("service", "sharded-v2")]
)
def test_frozen_positive_negative_relationships_agree_across_real_read_routes(
    tmp_path, monkeypatch, capsys, project, storage
):
    materialize(project, tmp_path)
    monkeypatch.chdir(tmp_path)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    if storage is not None:
        _cli(
            monkeypatch,
            capsys,
            "knowledge",
            "migrate",
            "--wiki-dir",
            "wiki",
            "--to",
            storage,
            "--recovery-dir",
            "storage-recovery",
        )
    before = _tree("src"), _tree("wiki")
    expected = {
        ("policy.py", "public_values"),
        ("client.py", "assigned_values")
        if project == "library"
        else ("handlers.py", "list_items"),
    }
    results = _caller_routes("policy.py:Batch.cap", monkeypatch, capsys)
    assert all(_pairs(result) == expected for result in results)
    assert all(
        result["coverage"]["runtime_completeness"] is False for result in results
    )
    if project == "service":
        callees = api.callees(
            "dynamic.py:factory_values", src_dir="src", wiki_dir="wiki"
        )
        unknown = next(row for row in callees["callees"] if row["line"] == 10)
        assert unknown["kind"] == "unresolved" and unknown["file"] is None
        assert unknown["reason"] and unknown["location"]["source_path"] == "dynamic.py"
        for name in ("shadowed_values", "conflicting_values", "rebound_values"):
            negative = api.callees(f"dynamic.py:{name}", src_dir="src", wiki_dir="wiki")
            method = next(row for row in negative["callees"] if row["symbol"] == "cap")
            assert method["kind"] == "unresolved" and method["file"] is None
            assert (
                method["reason"] and method["location"]["source_path"] == "dynamic.py"
            )
        assert not {
            ("dynamic.py", name)
            for name in (
                "factory_values",
                "shadowed_values",
                "conflicting_values",
                "rebound_values",
            )
        } & _pairs(results[0])
    assert (_tree("src"), _tree("wiki")) == before

    assert source_hashes(projects()[project]) == {
        name: sha256((Path("src") / name).read_bytes()).hexdigest()
        for name in projects()[project]
    }


@pytest.mark.parametrize(
    "storage,manifest_format,governed",
    [
        (None, "v7", False),
        ("sharded-v2", "indexed-v8", True),
        ("packed-v4-deflate", "indexed-v8", False),
    ],
)
def test_body_and_caller_change_sync_review_and_storage_preserve_independent_authorities(
    tmp_path, monkeypatch, capsys, storage, manifest_format, governed
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE + OTHER)
    Path("src/client.py").write_text(CLIENT)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    adoption = _cli(
        monkeypatch,
        capsys,
        "maintenance",
        "adopt",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--recovery-dir",
        "adoption-recovery",
        "--manifest-format",
        manifest_format,
    )
    if storage is not None:
        _cli(
            monkeypatch,
            capsys,
            "knowledge",
            "migrate",
            "--wiki-dir",
            "wiki",
            "--to",
            storage,
            "--recovery-dir",
            "initial-storage-recovery",
        )
    initial = _status_routes(monkeypatch, capsys)
    assert initial[0] == initial[1] == initial[2]
    old = _client_record(initial[0])
    _ack(initial[0], old)
    if governed:
        _cli(
            monkeypatch,
            capsys,
            "knowledge",
            "init",
            "--wiki-dir",
            "wiki",
            "--bundle-id",
            "kb_composed_authorities",
        )
        knowledge = load_knowledge_state(Path("wiki")).knowledge
        assert knowledge is not None
        page = next(
            row
            for row in knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
            if row["page_locator"] == "llm-wiki://modules/client"
        )
        section = next(
            row for row in page["sections"] if row.get("semantic_hash") is not None
        )
        ledger = load_governance(Path("wiki")).ledger
        uid = next(
            uid
            for uid, concept in ledger.concepts.items()
            if concept.locator == "llm-wiki://modules/client"
        )
        _cli(
            monkeypatch,
            capsys,
            "knowledge",
            "review",
            "--wiki-dir",
            "wiki",
            "--uid",
            uid,
            "--section",
            section["locator"],
            "--reviewer-kind",
            "human",
            "--reviewer-id",
            "composition-human",
            "--method",
            "manual-review",
            "--method-version",
            "1",
            "--authored-at",
            "2026-10-04T10:00:00Z",
        )
        reviewed_ledger = load_governance(Path("wiki")).ledger
        human_event = next(iter(reviewed_ledger.review_events.values()))
        baseline_knowledge = load_knowledge_state(Path("wiki")).knowledge
        assert baseline_knowledge is not None
        assert evaluate_review_event(
            human_event, reviewed_ledger, baseline_knowledge
        ).valid
    baseline = api.get_maintenance_status("src", "wiki")
    reviewed = _client_record(baseline)
    assert ("client.py", "assigned_values") in _pairs(
        _caller_routes("policy.py:Batch.cap", monkeypatch, capsys)[0]
    )
    prose = Path("wiki/modules/client.md").read_bytes()
    Path("src/client.py").write_text(
        CLIENT.replace("batch = Batch()", "batch = OtherBatch()")
    )
    before = _tree("src"), _tree("wiki")
    live = api.inspect_concept(
        "llm-wiki://modules/client", src_dir="src", wiki_dir="wiki", live=True
    )
    concept = live["concept"]["concept"]
    assert concept is not None
    assert concept["implementation"]["state"] == "changed"
    assert concept["freshness"]["state"] == "nonsemantic-source-change"
    unaffected = api.inspect_concept(
        "llm-wiki://entities/Batch", src_dir="src", wiki_dir="wiki", live=True
    )
    peer = unaffected["concept"]["concept"]
    assert peer is not None and peer["implementation"]["state"] == "unchanged"
    switched = _caller_routes("policy.py:OtherBatch.cap", monkeypatch, capsys)
    assert all(
        _pairs(result) == {("client.py", "assigned_values")} for result in switched
    )
    remaining = _caller_routes("policy.py:Batch.cap", monkeypatch, capsys)
    assert all(
        _pairs(result) == {("policy.py", "public_values")} for result in remaining
    )
    pending = _status_routes(monkeypatch, capsys, reviewed["record_id"])
    assert pending[0] == pending[1] == pending[2]
    assert pending[0]["records"][0]["effective_status"] == "pending"
    with pytest.raises(api.WorkspaceStateError):
        _ack(baseline, reviewed)
    assert (_tree("src"), _tree("wiki")) == before
    _sync(monkeypatch, capsys)
    assert Path("wiki/modules/client.md").read_bytes() == prose
    if governed:
        ledger = load_governance(Path("wiki")).ledger
        knowledge = load_knowledge_state(Path("wiki")).knowledge
        assert knowledge is not None
        expired = evaluate_review_event(human_event, ledger, knowledge)
        assert not expired.valid and "evidence-changed" in expired.reasons
    ready = api.get_maintenance_status("src", "wiki", record_id=reviewed["record_id"])
    row = ready["records"][0]
    assert row["record_id"] == old["record_id"] and row["recorded_status"] == "pending"
    authored = b"The reviewed source now constructs OtherBatch for this operation.\n"
    document = Path("wiki/modules/client.md")
    assert document.read_bytes().count(b"## Description\n") == 1
    document.write_bytes(
        document.read_bytes().replace(
            b"## Description\n", b"## Description\n\n" + authored, 1
        )
    )
    prose = document.read_bytes()
    unanchored = _tree("src"), _tree("wiki")
    assert api.get_maintenance_status("src", "wiki", record_id=row["record_id"])[
        "requires_sync"
    ]
    with pytest.raises(api.WorkspaceStateError):
        _ack(ready, row)
    assert (_tree("src"), _tree("wiki")) == unanchored
    _sync(monkeypatch, capsys)
    assert document.read_bytes() == prose and authored in prose
    ready = api.get_maintenance_status("src", "wiki", record_id=reviewed["record_id"])
    row = ready["records"][0]
    if governed:
        ledger = load_governance(Path("wiki")).ledger
        event = next(iter(ledger.review_events.values()))
        knowledge = load_knowledge_state(Path("wiki")).knowledge
        assert (
            knowledge is not None
            and not evaluate_review_event(event, ledger, knowledge).valid
        )
        governance_bytes = Path("wiki/.llm-wiki-governance.json").read_bytes()
    success = _ack(ready, row)
    assert (
        success["changed"]
        and success["actor"]["kind"] == "agent"
        and success["governance_effect"] == "none"
    )
    current = _status_routes(monkeypatch, capsys, row["record_id"])
    assert current[0] == current[1] == current[2]
    assert current[0]["records"][0]["effective_status"] == "acknowledged"
    history = current[0]["records"][0]["acknowledgment_history"]
    assert len(history) >= 2
    assert all(event["actor"]["kind"] == "agent" for event in history)
    if governed:
        assert Path("wiki/.llm-wiki-governance.json").read_bytes() == governance_bytes
        knowledge = load_knowledge_state(Path("wiki")).knowledge
        assert (
            knowledge is not None
            and not evaluate_review_event(
                event, load_governance(Path("wiki")).ledger, knowledge
            ).valid
        )
    after_ack = snapshot_wiki(Path("wiki"))
    assert not _ack(ready, row)["changed"]
    assert snapshot_wiki(Path("wiki")) == after_ack
    _sync(monkeypatch, capsys)
    assert document.read_bytes() == prose
    state = SyncManifest.load(Path("wiki")).maintenance_state
    assert (
        state is not None
        and state["records"][row["record_id"]]["status"] == "acknowledged"
    )
    assert state["adoption_id"] == adoption["adoption_id"]
    # Physical migration/recovery preserves the current acknowledged generation.
    authority = canonical_bytes(state)
    marker = Path("wiki", ADOPTION_FILENAME).read_bytes()
    pre_migration = _tree("wiki")
    _cli(
        monkeypatch,
        capsys,
        "knowledge",
        "migrate",
        "--wiki-dir",
        "wiki",
        "--to",
        "packed-v3" if storage != "packed-v3" else "sharded-v2",
        "--recovery-dir",
        "final-storage-recovery",
    )
    assert (
        canonical_bytes(SyncManifest.load(Path("wiki")).maintenance_state) == authority
    )
    assert Path("wiki", ADOPTION_FILENAME).read_bytes() == marker
    _cli(
        monkeypatch,
        capsys,
        "knowledge",
        "recover-storage",
        "--wiki-dir",
        "wiki",
        "--recovery-dir",
        "final-storage-recovery",
    )
    recovered = _tree("wiki")
    assert all(recovered[name] == raw for name, raw in pre_migration.items())
    assert all(
        name.startswith((".llm-wiki-knowledge/", ".llm-wiki-manifest/"))
        for name in set(recovered) - set(pre_migration)
    )
    assert load_knowledge_state(Path("wiki")).knowledge is not None
    assert (
        canonical_bytes(SyncManifest.load(Path("wiki")).maintenance_state) == authority
    )
    if manifest_format == "indexed-v8":
        sliced = capture_knowledge_slice(Path("wiki"), ["source:client.py"])
        assert sliced.maintenance_validation is not None
        assert sliced.maintenance_validation["whole_state_validated"] is False
        assert (
            sliced.maintenance_validation["ledger_record_membership"] == "not-validated"
        )
        sliced.finish()


def test_legacy_committed_model_read_never_adopts_or_claims_executable_unchanged(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / "wiki"
    fixture, _, _ = _committed_state(wiki)
    for name, content in fixture.source_files.items():
        path = tmp_path / "src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    before = _tree("src"), _tree("wiki")
    locator = next(
        concept["locator"]
        for concept in fixture.knowledge_payload["concepts"]
        if concept["concept_kind"] == "source-module"
    )
    payload = api.inspect_concept(locator, src_dir="src", wiki_dir="wiki", live=True)
    concept = payload["concept"]["concept"]
    assert concept is not None
    assert concept["implementation"]["state"] == "unavailable"
    assert concept["implementation"]["live_comparison_performed"] is False
    status = _status_routes(monkeypatch, capsys)
    assert all(
        result["availability"] == "unadopted" and result["records"] == []
        for result in status
    )
    assert not Path("wiki", ADOPTION_FILENAME).exists()
    assert (_tree("src"), _tree("wiki")) == before


@pytest.mark.parametrize("storage", [None, "packed-v4-deflate"])
def test_conditional_receiver_edit_keeps_review_pending_through_restart_and_ack(
    tmp_path, monkeypatch, capsys, storage
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    guard = '\nraise RuntimeError("owned source must only be parsed")\n'
    Path("src/policy.py").write_text(POLICY_SOURCE + OTHER + guard)
    Path("src/client.py").write_text(CLIENT + guard)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    api.adopt_maintenance("src", "wiki", recovery_dir="adoption-recovery")
    if storage:
        _cli(
            monkeypatch,
            capsys,
            "knowledge",
            "migrate",
            "--wiki-dir",
            "wiki",
            "--to",
            storage,
            "--recovery-dir",
            "storage-recovery",
        )
    baseline = api.get_maintenance_status("src", "wiki")
    row = _client_record(baseline)
    _ack(baseline, row)
    baseline = api.get_maintenance_status("src", "wiki")
    row = _client_record(baseline)
    assert ("client.py", "assigned_values") in _pairs(
        _caller_routes("policy.py:Batch.cap", monkeypatch, capsys)[0]
    )
    prose = Path("wiki/modules/client.md").read_bytes()
    Path("src/client.py").write_text(
        CLIENT.replace(
            "batch = Batch()", "batch = Batch()\n    values and (batch := OtherBatch())"
        )
        + guard
    )
    before = _tree("src"), _tree("wiki")
    mcp = McpWikiService("src", "wiki")
    selector = "client.py:assigned_values"
    python = api.callees(selector, src_dir="src", wiki_dir="wiki", limit=100)
    assert python == mcp.query_graph(
        {"type": "callees", "value": selector, "limit": 100}
    )
    method = next(edge for edge in python["callees"] if edge["symbol"] == "cap")
    assert method["kind"] == "unresolved" and method["file"] is None
    assert method["reason"] and method["location"]["source_path"] == "client.py"
    for target in ("Batch.cap", "OtherBatch.cap"):
        for result in _caller_routes("policy.py:" + target, monkeypatch, capsys):
            assert ("client.py", "assigned_values") not in _pairs(result)
    live = api.inspect_concept(
        "llm-wiki://modules/client", src_dir="src", wiki_dir="wiki", live=True
    )
    assert live == mcp.inspect_concept("llm-wiki://modules/client", live=True)
    concept = live["concept"]["concept"]
    assert concept is not None
    assert concept["implementation"]["state"] == "changed"
    assert (
        "dependencies-and-runtime-behavior-not-evaluated"
        in concept["implementation"]["limitations"]
    )
    assert concept["freshness"]["state"] == "nonsemantic-source-change"
    pending = _status_routes(monkeypatch, capsys, row["record_id"])
    assert pending[0] == pending[1] == pending[2]
    assert pending[0]["records"][0]["effective_status"] == "pending"
    with pytest.raises(api.WorkspaceStateError):
        _ack(baseline, row)
    assert (_tree("src"), _tree("wiki")) == before
    _sync(monkeypatch, capsys)
    assert Path("wiki/modules/client.md").read_bytes() == prose
    durable = canonical_bytes(SyncManifest.load(Path("wiki")).maintenance_state)
    repo = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = (
        str(repo / "src") + os.pathsep + environment.get("PYTHONPATH", "")
    )

    def restart_status():
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "llm_wiki_cli.cli",
                "maintenance",
                "status",
                "--src-dir",
                "src",
                "--wiki-dir",
                "wiki",
                "--record-id",
                row["record_id"],
                "--format",
                "json",
            ],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        return json.loads(result.stdout)

    read_basis = _tree("src"), _tree("wiki")
    restarted = restart_status()
    assert restarted["records"][0]["recorded_status"] == "pending"
    assert (_tree("src"), _tree("wiki")) == read_basis
    _sync(monkeypatch, capsys)
    assert canonical_bytes(SyncManifest.load(Path("wiki")).maintenance_state) == durable
    ready = api.get_maintenance_status("src", "wiki", record_id=row["record_id"])
    success = _ack(ready, ready["records"][0])
    assert success["changed"] and success["actor"]["kind"] == "agent"
    assert success["governance_effect"] == "none"
    acknowledged = restart_status()
    assert acknowledged["records"][0]["effective_status"] == "acknowledged"
    assert (
        acknowledged["records"][0]["acknowledgment_history"][-1]["actor"]["kind"]
        == "agent"
    )
    _sync(monkeypatch, capsys)
    assert restart_status()["records"][0]["effective_status"] == "acknowledged"
    assert Path("wiki/modules/client.md").read_bytes() == prose
    assert not Path("wiki/.llm-wiki-governance.json").exists()


def test_selected_source_caller_and_indexed_header_do_not_borrow_uncaptured_class_authority(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE + OTHER)
    Path("src/client.py").write_text(CLIENT)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    api.adopt_maintenance("src", "wiki", recovery_dir="adoption-recovery")
    _cli(
        monkeypatch,
        capsys,
        "knowledge",
        "migrate",
        "--wiki-dir",
        "wiki",
        "--to",
        "sharded-v2",
        "--recovery-dir",
        "sharded-recovery",
    )
    _cli(
        monkeypatch,
        capsys,
        "knowledge",
        "migrate",
        "--wiki-dir",
        "wiki",
        "--to",
        "indexed-v8",
        "--recovery-dir",
        "indexed-recovery",
    )
    policy = Path("src/.llm-wiki/source-selection.json")
    policy.parent.mkdir()
    policy.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["client.py"],
                "exclude": [],
            }
        )
    )
    unanchored = _tree("src"), _tree("wiki")
    with pytest.raises(api.InvalidRequestError):
        api.callees("client.py:assigned_values", src_dir="src", wiki_dir="wiki")
    assert (_tree("src"), _tree("wiki")) == unanchored
    _cli(
        monkeypatch,
        capsys,
        "sync",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--no-plugins",
        "--force",
        json_output=False,
    )
    before = _tree("src"), _tree("wiki")
    mcp = McpWikiService("src", "wiki")
    values = [
        dict(api.callees("client.py:assigned_values", src_dir="src", wiki_dir="wiki")),
        mcp.query_graph(
            {"type": "callees", "value": "client.py:assigned_values", "limit": 100}
        ),
    ]
    for value in values:
        assert value["coverage"]["analysis_scope"] == "selected-source"
        assert value["coverage"]["runtime_completeness"] is False
        method = next(row for row in value["callees"] if row["symbol"] == "cap")
        assert method["file"] is None and method["kind"] == "unresolved"
        assert method["reason"] == "constructor-source-unavailable"
    assert values[0]["callees"] == values[1]["callees"]
    selected = capture_knowledge_slice(Path("wiki"), ["source:client.py"])
    assert selected.maintenance_validation is not None
    assert selected.maintenance_validation["whole_state_validated"] is False
    assert (
        selected.maintenance_validation["ledger_record_membership"] == "not-validated"
    )
    selected.finish()
    assert (_tree("src"), _tree("wiki")) == before


def _frozen_service_case(case_id):
    corpus = json.loads(
        (Path(__file__).parent / "developer_value/corpus.json").read_text()
    )
    return next(case for case in corpus["cases"] if case["id"] == case_id)


def _prepare_frozen_service(case, tmp_path, monkeypatch, capsys):
    materialize(case["project"], tmp_path)
    monkeypatch.chdir(tmp_path)
    api.bootstrap_wiki(
        case["preparation"]["source_root"], case["preparation"]["wiki_root"]
    )
    capsys.readouterr()
    for edit in case["preparation"]["semantic_edits"]:
        assert sha256(edit["text"].encode()).hexdigest() == edit["text_sha256"]
        page = Path("wiki") / edit["wiki_path"]
        content = page.read_bytes()
        heading = ("## " + edit["heading"] + "\n").encode()
        assert content.count(heading) == 1
        page.write_bytes(
            content.replace(heading, heading + b"\n" + edit["text"].encode(), 1)
        )
    if case["preparation"]["refresh_before_first_read"]:
        _sync(monkeypatch, capsys)
    if case["preparation"].get("adopt_storage"):
        _cli(
            monkeypatch,
            capsys,
            "knowledge",
            "migrate",
            "--wiki-dir",
            "wiki",
            "--to",
            case["preparation"]["adopt_storage"],
            "--recovery-dir",
            "storage-recovery",
        )


def _batch_record(status):
    return next(
        row
        for row in status["records"]
        if row["coordinate"]["qualified_owner"] == "Batch"
        and row["target"]["canonical_path"] == "entities/Batch.md"
        and row["basis_available"]
    )


def _frozen_ack(status, row):
    assert status["state_hash"] is not None and row["expected_basis"] is not None
    return api.acknowledge_maintenance(
        "src",
        "wiki",
        record_id=row["record_id"],
        expected_state_hash=status["state_hash"],
        expected_basis=row["expected_basis"],
        actor_kind="agent",
        actor_id="developer-value-evaluator",
    )


def test_frozen_service_review_persists_after_edit_sync_fresh_process_and_repeat(
    tmp_path, monkeypatch, capsys
):
    case = _frozen_service_case("S05")
    _prepare_frozen_service(case, tmp_path, monkeypatch, capsys)
    api.adopt_maintenance("src", "wiki", recovery_dir="adoption-recovery")
    initial = api.get_maintenance_status("src", "wiki")
    row = _batch_record(initial)
    _frozen_ack(initial, row)
    authored = Path("wiki/entities/Batch.md").read_bytes()
    queue_before = api.build_maintenance_queue("src", "wiki", limit=100)
    assert not any(
        reason["code"] == "maintenance:executable-syntax-changed"
        for item in queue_before["items"]
        for reason in item["reasons"]
    )
    apply_source_mutation(case, Path("src"))
    after_edit = _tree("src"), _tree("wiki")
    edited = api.build_maintenance_queue("src", "wiki", limit=100)
    assert any(
        reason["code"] == "maintenance:executable-syntax-changed"
        for item in edited["items"]
        for reason in item["reasons"]
    )
    assert (_tree("src"), _tree("wiki")) == after_edit
    _sync(monkeypatch, capsys)
    synced = api.get_maintenance_status("src", "wiki", record_id=row["record_id"])
    assert synced["records"][0]["recorded_status"] == "pending"
    assert Path("wiki/entities/Batch.md").read_bytes() == authored
    owner = canonical_bytes(SyncManifest.load(Path("wiki")).maintenance_state)
    read_basis = _tree("src"), _tree("wiki")
    repo = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = (
        str(repo / "src") + os.pathsep + environment.get("PYTHONPATH", "")
    )
    restarted = subprocess.run(
        [
            sys.executable,
            "-m",
            "llm_wiki_cli.cli",
            "queue",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            "--format",
            "json",
            "--limit",
            "100",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    queue = json.loads(restarted.stdout)
    item = next(item for item in queue["items"] if item["path"] == "entities/Batch.md")
    assert item["maintenance"]["pending"] >= 1
    assert (_tree("src"), _tree("wiki")) == read_basis
    _sync(monkeypatch, capsys)
    assert canonical_bytes(SyncManifest.load(Path("wiki")).maintenance_state) == owner
    assert Path("wiki/entities/Batch.md").read_bytes() == authored


def test_frozen_service_stale_source_and_prose_review_requires_fresh_reanchored_basis(
    tmp_path, monkeypatch, capsys
):
    case = _frozen_service_case("S06")
    _prepare_frozen_service(case, tmp_path, monkeypatch, capsys)
    api.adopt_maintenance("src", "wiki", recovery_dir="adoption-recovery")
    inspected = api.inspect_concept(
        "entities/Batch.md", src_dir="src", wiki_dir="wiki", live=True
    )
    assert inspected["concept"]["found"]
    baseline = api.get_maintenance_status("src", "wiki")
    row = _batch_record(baseline)
    apply_source_mutation(case, Path("src"))
    before_stale = _tree("src"), _tree("wiki")
    with pytest.raises(api.WorkspaceStateError):
        _frozen_ack(baseline, row)
    assert (_tree("src"), _tree("wiki")) == before_stale
    _sync(monkeypatch, capsys)
    source_current = api.get_maintenance_status(
        "src", "wiki", record_id=row["record_id"]
    )
    source_row = source_current["records"][0]
    path = apply_prose_mutation(case, Path("wiki"))
    authored = path.read_bytes()
    before_old_prose = _tree("src"), _tree("wiki")
    with pytest.raises(api.WorkspaceStateError):
        _frozen_ack(source_current, source_row)
    assert (_tree("src"), _tree("wiki")) == before_old_prose
    _sync(monkeypatch, capsys)
    assert path.read_bytes() == authored
    fresh = api.get_maintenance_status("src", "wiki", record_id=row["record_id"])
    reviewed = fresh["records"][0]
    result = _frozen_ack(fresh, reviewed)
    assert (
        result["changed"]
        and result["actor"]["kind"] == "agent"
        and result["governance_effect"] == "none"
    )
    exact = _tree("src"), _tree("wiki")
    assert not _frozen_ack(fresh, reviewed)["changed"]
    assert (_tree("src"), _tree("wiki")) == exact
    assert not Path("wiki/.llm-wiki-governance.json").exists()


def test_frozen_service_corrupt_required_native_read_rejects_across_real_routes(
    tmp_path, monkeypatch, capsys
):
    case = _frozen_service_case("S07")
    _prepare_frozen_service(case, tmp_path, monkeypatch, capsys)
    request = case["observation_steps"][0]["request"]
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert result.ok and result.to_payload()["coverage"][0]["satisfied"]
    (Path("wiki") / case["mutation"]["path"]).write_bytes(
        case["mutation"]["after"].encode()
    )
    corrupt = _tree("src"), _tree("wiki")
    with pytest.raises(api.LlmWikiApiError):
        api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    with pytest.raises(McpWikiError):
        McpWikiService("src", "wiki").build_task_context(request)
    with pytest.raises(SystemExit):
        _cli(
            monkeypatch,
            capsys,
            "task-context",
            "--request",
            "-",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            request=request,
        )
    output = capsys.readouterr()
    assert output.out == ""
    error = json.loads(output.err)
    assert error["ok"] is False and error["error"]["code"]
    assert (_tree("src"), _tree("wiki")) == corrupt
