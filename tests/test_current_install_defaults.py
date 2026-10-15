"""Current, versionless project setup and compatible recovery boundaries."""

import hashlib
import json
from pathlib import Path

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import init_cmd, upgrade_cmd
from llm_wiki_cli.config import AGENT_CHOICES, read_config
from llm_wiki_cli.services.current_contracts import current_contract_defaults, upgrade_current_knowledge
from llm_wiki_cli.services.knowledge_artifacts import current_knowledge_format
from llm_wiki_cli.services.manifest_storage import current_manifest_format
from llm_wiki_cli.services.schema import SCHEMA_FILENAMES
from llm_wiki_cli.services.task_contract import normalize_task_request


def files(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text(
        "raise RuntimeError('target must not execute')\n\nclass Item:\n    value: int\n", encoding="utf-8")
    return tmp_path


def source_request():
    return {"requirements": [{"id": "contract", "facet": "source-contract", "selector": "app.py:Item"}],
            "options": {"knowledge_mode": "off"}}


def test_versionless_first_use_gets_current_storage_tasks_and_readable_views(project):
    source = files(project / "src")
    result = api.bootstrap_wiki("src", "wiki")
    assert result.summary["current_contracts"]["state"] == "current"
    assert current_knowledge_format("wiki") == "packed-v4-deflate"
    assert current_manifest_format("wiki") == "indexed-v8"
    assert (project / "wiki/.llm-wiki-maintenance-adoption.json").is_file()
    request = source_request()
    canonical = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert canonical.ok and canonical.schema_version == "llm-wiki-task-context/v2"
    compact = api.build_compact_task_context(request, src_dir="src", wiki_dir="wiki")
    assert compact.ok and compact.schema_version == "llm-wiki-task-compact/v2"
    native = {"requirements": [{"id": "native", "facet": "concept", "selector": "llm-wiki://entities/Item"}]}
    result = api.build_task_context(native, src_dir="src", wiki_dir="wiki")
    assert result.ok and all(c["satisfied"] for c in result.to_payload()["coverage"])
    assert result.to_payload()["storage"]["layout"] == "compact-v1"
    assert files(project / "src") == source


def test_first_use_packet_defaults_match_cli_and_mcp(project, capsys):
    from llm_wiki_cli.services import context_service
    from llm_wiki_cli.services.mcp_server import McpWikiService

    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    before = files(project / "src"), files(project / "wiki")
    expected = api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"]})
    context_service.run(cli._build_parser().parse_args([
        "context", "--src-dir", "src", "--wiki-dir", "wiki", "--budget", "32000",
        "--focus", "all", "--format", "packet", "--read-only",
    ]))
    response = McpWikiService(src_dir="src", wiki_dir="wiki").get_context_packet(focus=["all"])
    assert expected.to_payload()["schema_version"] == "llm-wiki-qualified-context-packet/v2"
    knowledge = expected.to_payload()["response"]["knowledge"]
    assert knowledge["mode"] == "auto" and knowledge["availability"] == "ready"
    assert capsys.readouterr().out.encode("utf-8") == expected.to_bytes()
    assert response["packet"] == expected.to_payload()
    assert (files(project / "src"), files(project / "wiki")) == before


def test_explicit_legacy_requests_and_goldens_remain_compatible(project):
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    assert current_knowledge_format("wiki") == "v1"
    request = {**source_request(), "schema_version": "llm-wiki-task-request/v1"}
    assert api.build_task_context(request, src_dir="src", wiki_dir="wiki").schema_version == "llm-wiki-task-context/v1"
    fixture = Path(__file__).parent / "fixtures"
    for name in ("context-packet-v1.json", "context-packet-v2.json", "context-packet-v1-pre-bindings.json", "context-packet-v2-pre-bindings.json"):
        raw = (fixture / name).read_bytes()
        assert api.validate_context_packet(raw).packet.to_bytes() == raw


def test_upgrade_retains_complete_recovery_and_prose_and_is_idempotent(project):
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    page = project / "wiki/entities/Item.md"
    page.write_text(page.read_text().replace("## Description", "## Description\n\nConsumer-authored note."))
    # Re-anchor the user's prose through the owning sync before adoption.
    from llm_wiki_cli.commands import sync_cmd
    sync_cmd.run(cli._build_parser().parse_args(["sync", "--src-dir", "src", "--wiki-dir", "wiki", "--force", "--no-plugins"]))
    before = files(project / "wiki")
    result = upgrade_current_knowledge("src", "wiki")
    assert result["changed"] and "Consumer-authored note." in page.read_text()
    recovery = Path(result["recovery_dir"])
    assert (recovery / "adoption/before/maintenance-recovery.json").is_file()
    assert files(recovery / "adoption/before")["entities/Item.md"] == before["entities/Item.md"]
    after = files(project / "wiki")
    assert upgrade_current_knowledge("src", "wiki") == {"changed": False, "state": "current"}
    assert files(project / "wiki") == after


@pytest.mark.parametrize("agent", AGENT_CHOICES)
@pytest.mark.parametrize("no_skills", [False, True])
def test_all_agents_init_and_upgrade_install_current_defaults(project, agent, no_skills):
    arguments = ["--agent", agent, "--wiki-dir", "wiki"] + (["--no-skills"] if no_skills else [])
    init_cmd.run(cli._build_parser().parse_args(["init", *arguments]))
    assert read_config("wiki")["contract_defaults"] == current_contract_defaults()
    schema = Path(SCHEMA_FILENAMES[agent])
    text = schema.read_text()
    assert "do not choose older formats" in text or "current" in text
    schema.write_text("User rules: preserve me.\n\n" + text)
    upgrade_cmd.run(cli._build_parser().parse_args(["upgrade", "--wiki-dir", "wiki"]))
    assert "User rules: preserve me." in schema.read_text()
    assert read_config("wiki")["contract_defaults"] == current_contract_defaults()
    if no_skills:
        assert "--view compact --view-budget-tokens" in schema.read_text()
        assert '"schema_version":"llm-wiki-task-request' not in schema.read_text()


@pytest.mark.parametrize("schema", [None, "future/v99"])
def test_explicit_unknown_schemas_are_not_downgraded(schema):
    with pytest.raises(ValueError, match="unsupported task"):
        normalize_task_request({"schema_version": schema})


def test_bad_native_state_cannot_be_upgraded_or_rewritten(project):
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    path = project / "wiki/.llm-wiki-knowledge.json"
    payload = json.loads(path.read_bytes())
    payload["schema_version"] = "llm-wiki-knowledge/v999"
    path.write_text(json.dumps(payload))
    before = files(project / "wiki")
    with pytest.raises(ValueError):
        upgrade_current_knowledge("src", "wiki")
    assert files(project / "wiki") == before


def test_clean_init_scaffold_can_bootstrap_current_native_defaults(project):
    init_cmd.run(cli._build_parser().parse_args(["init", "--agent", "generic", "--wiki-dir", "wiki"]))
    result = api.bootstrap_wiki("src", "wiki")
    assert result.summary["current_contracts"]["state"] == "current"
    assert current_knowledge_format("wiki") == "packed-v4-deflate"
    assert current_manifest_format("wiki") == "indexed-v8"


@pytest.mark.parametrize("keep_surface", [True, False])
def test_legacy_surface_only_upgrade_retains_a_complete_preimage(project, keep_surface):
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    # Older surface-only projects have no native commitment or adoption marker.
    (project / "wiki/.llm-wiki-knowledge.json").unlink()
    (project / "wiki/.llm-wiki-manifest.json").unlink()
    if not keep_surface:
        (project / "wiki/.llm-wiki-surface.json").unlink()
    before = files(project / "wiki")
    source = files(project / "src")
    result = upgrade_current_knowledge("src", "wiki", _seed_legacy=upgrade_cmd._seed_legacy_for_current_defaults)
    recovery = Path(result["recovery_dir"]) / "legacy"
    for name, digest in before.items():
        if name == "llm-wiki-storage.lock":
            # Operational lock identity is excluded by the recovery protocol.
            continue
        assert hashlib.sha256((recovery / name).read_bytes()).hexdigest() == digest
    assert files(project / "src") == source
    assert current_knowledge_format("wiki") == "packed-v4-deflate"
    assert current_manifest_format("wiki") == "indexed-v8"


def test_missing_committed_native_data_is_not_treated_as_legacy(project):
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    (project / "wiki/.llm-wiki-knowledge.json").unlink()
    before = files(project / "wiki")
    with pytest.raises(ValueError, match="recovery"):
        upgrade_current_knowledge("src", "wiki")
    assert files(project / "wiki") == before


def test_current_ranked_source_discovery_needs_no_version_choice(project):
    api.bootstrap_wiki("src", "wiki")
    before = files(project / "wiki"), files(project / "src")
    default = api.search_wiki("Item", src_dir="src", wiki_dir="wiki", include_source=True)
    explicit = api.search_wiki("Item", src_dir="src", wiki_dir="wiki", include_source=True, mode="ranked-v2")
    assert default.pop("mode") == "ranked"
    assert explicit.pop("mode") == "ranked-v2"
    assert default == explicit
    assert default.get("source_indexing", {}).get("source_files") == 1
    assert (files(project / "wiki"), files(project / "src")) == before


def test_bootstrap_json_reports_the_final_physical_schema(project, capsys):
    from llm_wiki_cli.commands import bootstrap_cmd
    bootstrap_cmd.run(cli._build_parser().parse_args(["bootstrap", "--src-dir", "src", "--wiki-dir", "wiki", "--format", "json"]))
    report = json.loads(capsys.readouterr().out)
    root = json.loads(Path("wiki/.llm-wiki-knowledge.json").read_bytes())
    assert report["knowledge_schema_version"] == root["schema_version"] == "llm-wiki-knowledge/v4"
    assert report["current_contracts"]["state"] == "current"


def test_empty_versionless_storage_options_keep_current_defaults():
    empty, _ = normalize_task_request({**source_request(), "storage_options": {}})
    omitted, _ = normalize_task_request(source_request())
    assert empty["storage_options"] == omitted["storage_options"] == {
        "selection": "required-facets-v1", "receipt": "compact-v1"}


def test_budgeted_mcp_and_api_accept_the_same_versionless_request(project):
    from llm_wiki_cli.services.mcp_server import McpWikiService
    request = {"budget_tokens": 32000, "budget_mode": "estimated", "changes": {"mode": "paths", "paths": []}}
    expected = api.build_budgeted_context("src", "wiki", request).rendered
    actual = McpWikiService(src_dir="src", wiki_dir="wiki").build_budgeted_context(request)
    assert actual == expected and json.loads(actual)["protocol"] == "llm-wiki-context/v3"


def test_default_current_ownership_survives_noop_and_changed_source_sync(project):
    from llm_wiki_cli.commands import sync_cmd
    from llm_wiki_cli.services.knowledge_storage_lifecycle import _committed_inputs
    api.bootstrap_wiki("src", "wiki")
    marker_path = Path("wiki/.llm-wiki-maintenance-adoption.json")
    marker = marker_path.read_bytes()
    before = files(Path("wiki"))
    command = ["sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]
    sync_cmd.run(cli._build_parser().parse_args(command))
    assert files(Path("wiki")) == before
    Path("src/app.py").write_text("class Item:\n    value: str\n")
    sync_cmd.run(cli._build_parser().parse_args(command))
    assert marker_path.read_bytes() == marker
    assert current_knowledge_format("wiki") == "packed-v4-deflate"
    assert current_manifest_format("wiki") == "indexed-v8"
    state, _, _ = _committed_inputs("wiki")
    assert state.manifest_basis is not None
    assert state.manifest_basis.maintenance_state is not None
    result = api.build_task_context(source_request(), src_dir="src", wiki_dir="wiki")
    assert result.ok and 'str' in result.rendered


@pytest.mark.parametrize("authority", ["adopted", "governed"])
def test_missing_authority_is_not_an_empty_install_target(project, authority):
    if authority == "adopted":
        api.bootstrap_wiki("src", "wiki")
        for name in (".llm-wiki-knowledge.json", ".llm-wiki-manifest.json", ".llm-wiki-surface.json"):
            (Path("wiki") / name).unlink()
    else:
        Path("wiki").mkdir()
        Path("wiki/.llm-wiki-governance.json").write_text("{}")
    before = files(Path("wiki"))
    with pytest.raises(ValueError):
        upgrade_current_knowledge("src", "wiki")
    assert files(Path("wiki")) == before


def test_upgrade_preserves_existing_governance_bytes(project):
    from llm_wiki_cli.commands import knowledge_cmd
    from llm_wiki_cli.services.knowledge_storage_lifecycle import _committed_inputs
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    knowledge_cmd.run(cli._build_parser().parse_args(["knowledge", "init", "--wiki-dir", "wiki", "--bundle-id", "kb_current_upgrade"]))
    ledger = Path("wiki/.llm-wiki-governance.json").read_bytes()
    upgrade_current_knowledge("src", "wiki")
    assert Path("wiki/.llm-wiki-governance.json").read_bytes() == ledger
    _committed_inputs("wiki")


def test_current_team_resolution_never_decodes_native_packs(project, monkeypatch):
    from llm_wiki_cli.services import team
    api.bootstrap_wiki("src", "wiki")
    assert list(Path("wiki/.llm-wiki-knowledge/packs").rglob("*.zip"))
    before = files(Path("wiki"))
    original = team.read_md
    def text_only(path):
        assert Path(path).suffix not in {".zip", ".bin"}
        return original(path)
    monkeypatch.setattr(team, "read_md", text_only)
    result = team.resolve_conflicts("wiki", "src", write=False)
    assert result["ok"] and result["conflict_count"] == 0
    assert files(Path("wiki")) == before


@pytest.mark.parametrize("coverage", ["full", "inventory"])
def test_current_static_cache_reuses_observations_but_reconciles_prose(project, monkeypatch, coverage):
    from llm_wiki_cli.commands import sync_cmd
    from llm_wiki_cli.services import sync_analysis_cache
    from llm_wiki_cli.services.sync_manifest import SyncManifest
    api.bootstrap_wiki("src", "wiki")
    page = Path("wiki/modules/app.md")
    page.write_text(page.read_text().replace("## Description", "## Description\n\nFirst authored purpose."))
    command = ["sync", "--src-dir", "src", "--wiki-dir", "wiki", "--cache-dir", "cache", "--no-plugins"]
    sync_cmd.run(cli._build_parser().parse_args(command))
    cache = Path("cache") / sync_analysis_cache.FILENAME
    initial = cache.read_bytes()
    payload = json.loads(initial)
    assert payload["input_key"]["ordinary_owner"] == json.loads(Path("wiki/.llm-wiki-maintenance-adoption.json").read_bytes())["adoption_id"]
    if coverage == "inventory":
        monkeypatch.setattr(sync_analysis_cache, "MAX_BYTES", len(initial) - 1)
        page.write_text(page.read_text().replace("First authored purpose.", "Prime bounded inventory."))
        sync_cmd.run(cli._build_parser().parse_args(command))
        assert json.loads(cache.read_bytes())["coverage"] == "inventory"
    status = api.get_maintenance_status("src", "wiki")
    record = next(row for row in status["records"] if row["expected_basis"] is not None
                  and row["expected_basis"]["target"]["canonical_path"] == "modules/app.md")
    assert status["state_hash"] is not None
    assert record["expected_basis"] is not None
    api.acknowledge_maintenance("src", "wiki", record_id=record["record_id"],
        expected_state_hash=status["state_hash"], expected_basis=record["expected_basis"],
        actor_kind="agent", actor_id="explicit-fixture-review")
    before = SyncManifest.load(Path("wiki")).maintenance_state
    assert before is not None
    assert before["records"][record["record_id"]]["status"] == "acknowledged"
    page.write_text(page.read_text().replace("## Description", "## Description\n\nSecond authored purpose."))
    with monkeypatch.context() as hit:
        hit.setattr(sync_cmd, "_extract_current_inventory", lambda *a, **k: pytest.fail("unchanged source must reuse qualified observations"))
        sync_cmd.run(cli._build_parser().parse_args(command))
    after = SyncManifest.load(Path("wiki")).maintenance_state
    assert after is not None
    assert before != after and before["adoption_id"] == after["adoption_id"]
    assert "Second authored purpose." in page.read_text()
    assert after["records"][record["record_id"]]["status"] == "pending"
    for record_id, prior in before["records"].items():
        assert after["records"][record_id]["acknowledgment_history"] == prior["acknowledgment_history"]


def test_selected_clean_install_remains_a_bootstrap_scaffold(project):
    profile = Path("selection.json")
    profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1", "include": ["src"], "exclude": []}))
    init_cmd.run(cli._build_parser().parse_args(["init", "--agent", "generic", "--wiki-dir", "wiki", "--source-selection", str(profile)]))
    from llm_wiki_cli.commands import bootstrap_cmd
    bootstrap_cmd.run(cli._build_parser().parse_args(["bootstrap", "--src-dir", ".", "--wiki-dir", "wiki", "--source-selection", str(profile)]))
    assert current_knowledge_format("wiki") == "packed-v4-deflate"
