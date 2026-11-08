"""The public behavior reference tracks provider policy independently of consumer state."""

from copy import deepcopy
from importlib import metadata, resources
import json
from pathlib import Path
from types import MappingProxyType

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli import config
from llm_wiki_cli.services import behavior_reference as reference
from llm_wiki_cli.services import current_contracts, skills, task_contract
from llm_wiki_cli.services.knowledge_evidence import hash_json


def seal(contract):
    contract["contract_id"] = hash_json(
        {k: v for k, v in contract.items() if k != "contract_id"}
    )
    return contract


def test_packaged_metadata_must_belong_to_loaded_provider(tmp_path, monkeypatch):
    location = tmp_path / "site-packages"
    installed = location / "agent_wiki_cli-2.0.dist-info"
    installed.mkdir(parents=True)
    monkeypatch.setattr(
        reference,
        "__file__",
        str(location / "llm_wiki_cli/services/behavior_reference.py"),
    )
    (installed / "METADATA").write_text(
        "Name: agent-wiki-cli\nVersion: 2.0\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="metadata|Python requirement"):
        reference.get_behavior_facts()
    (installed / "METADATA").write_text(
        "Name: agent-wiki-cli\nVersion: 2.0\nRequires-Python: >=3.12\n",
        encoding="utf-8",
    )
    assert reference.get_behavior_facts()["facts"]["package"] == {
        "name": "agent-wiki-cli",
        "version": "2.0",
        "requires_python": ">=3.12",
    }


def test_provider_checkout_prefers_owned_project_metadata_over_old_egg_info(
    tmp_path, monkeypatch
):
    source = tmp_path / "src"
    old = source / "agent_wiki_cli.egg-info"
    old.mkdir(parents=True)
    (old / "PKG-INFO").write_text(
        "Name: agent-wiki-cli\nVersion: 1\nRequires-Python: >=3.10\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        reference,
        "__file__",
        str(source / "llm_wiki_cli/services/behavior_reference.py"),
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="agent-wiki-cli"\nversion="2"\nrequires-python=">=3.11"\n',
        encoding="utf-8",
    )
    assert reference.get_behavior_facts()["facts"]["package"] == {
        "name": "agent-wiki-cli",
        "version": "2",
        "requires_python": ">=3.11",
    }


def test_wheel_installed_under_foreign_src_reads_its_own_metadata(
    tmp_path, monkeypatch
):
    site = tmp_path / "src"
    dist_info = site / "agent_wiki_cli-2.0.dist-info"
    dist_info.mkdir(parents=True)
    (dist_info / "METADATA").write_text(
        "Name: agent-wiki-cli\nVersion: 2.0\nRequires-Python: >=3.12\n",
        encoding="utf-8",
    )
    (dist_info / "WHEEL").write_text("Wheel-Version: 1.0\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "consumer"\nversion = "0.1"\n', encoding="utf-8"
    )
    monkeypatch.setattr(
        reference, "__file__", str(site / "llm_wiki_cli/services/behavior_reference.py")
    )
    assert reference.get_behavior_facts()["facts"]["package"] == {
        "name": "agent-wiki-cli",
        "version": "2.0",
        "requires_python": ">=3.12",
    }


@pytest.fixture
def declared():
    return reference.get_behavior_facts()


def test_declared_facts_match_distribution_setup_storage_tasks_and_skills(declared):
    installed = metadata.distribution("agent-wiki-cli").metadata
    facts = declared["facts"]
    assert set(facts) == set(reference.BEHAVIOR_FACT_GROUPS)
    assert facts["package"] == {
        "name": installed["Name"],
        "version": installed["Version"],
        "requires_python": installed["Requires-Python"],
    }
    assert facts["setup"]["wiki_directory"] == config.DEFAULT_WIKI_DIR
    assert facts["setup"]["new_project"] == config._DEFAULT_CONFIG
    current = current_contracts.current_contract_defaults()
    assert facts["task"]["setup_and_upgrade"] == {
        key: current[key]
        for key in (
            "task_request",
            "compact_view",
            "storage_selection",
            "storage_receipt",
        )
    }
    assert facts["setup"]["policy"] == current["policy"]
    assert facts["storage"]["setup_and_upgrade"] == {
        key: current[key] for key in ("knowledge_format", "manifest_format")
    }
    assert facts["storage"]["observed_wiki_formats"] is None
    assert (
        facts["storage"]["setup_and_upgrade"]["knowledge_format"]
        in facts["storage"]["explicit_knowledge_formats"]
    )
    assert (
        facts["storage"]["setup_and_upgrade"]["manifest_format"]
        in facts["storage"]["migration_targets"]
    )
    assert facts["skills"] == [item.to_dict() for item in skills.list_bundled_skills()]
    task = facts["task"]
    normalized, profile = task_contract.normalize_task_request({})
    assert task["default_request"] == {
        "schema_version": current["task_request"],
        "storage_options": normalized["storage_options"],
        "kind": normalized["kind"],
        "profile": profile.to_payload(),
    }
    assert task["explicit_v1"] == {
        "schema_version": task_contract.TASK_REQUEST_SCHEMA,
        "storage_options": None,
    }
    explicit = task_contract.TASK_REQUEST_SCHEMA_V2
    assert task["explicit_v2"] == {
        "schema_version": explicit,
        "storage_options": None,
        "empty_storage_options": task_contract.normalize_task_request(
            {"schema_version": explicit, "storage_options": {}}
        )[0]["storage_options"],
    }
    assert task["compact_view"]["default_schema"] == current["compact_view"]
    assert task["cli_view"] == "canonical"


def test_unrelated_cwd_and_shadow_distribution_cannot_supply_behavior(
    tmp_path, declared, monkeypatch
):
    metadata_dir = tmp_path / "agent_wiki_cli-99.dist-info"
    metadata_dir.mkdir()
    (metadata_dir / "METADATA").write_text(
        "Name: agent-wiki-cli\nVersion: 99\nRequires-Python: <3\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "consumer"\nversion = "1"\nrequires-python = "<3"'
    )
    (tmp_path / "docs/llm_wiki").mkdir(parents=True)
    (tmp_path / "docs/llm_wiki/.llm-wiki-manifest.json").write_text(
        "invalid live state"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    assert reference.get_behavior_facts() == declared


def test_owner_changes_flow_to_new_detached_snapshots(monkeypatch, declared):
    monkeypatch.setitem(
        config._DEFAULT_CONFIG,
        "quality_hints",
        not config._DEFAULT_CONFIG["quality_hints"],
    )
    monkeypatch.setattr(current_contracts, "CURRENT_KNOWLEDGE_FORMAT", "new-format")
    skills_seen = skills.list_bundled_skills()
    monkeypatch.setattr(skills, "list_bundled_skills", lambda: skills_seen[:-1])
    changed = reference.get_behavior_facts()
    assert (
        changed["facts"]["storage"]["setup_and_upgrade"]["knowledge_format"]
        == "new-format"
    )
    assert changed["facts"]["setup"]["new_project"] == config._DEFAULT_CONFIG
    assert len(changed["facts"]["skills"]) == len(skills_seen) - 1
    assert changed["contract_id"] != declared["contract_id"]
    changed["facts"]["setup"]["new_project"]["quality_hints"] = "changed downstream"
    assert type(config._DEFAULT_CONFIG["quality_hints"]) is bool


def test_stored_task_policy_is_observable_separately_from_runtime_defaults(
    declared, monkeypatch
):
    changed = {
        **current_contracts.current_contract_defaults(),
        "storage_receipt": "next-format",
    }
    monkeypatch.setattr(current_contracts, "current_contract_defaults", lambda: changed)
    updated = reference.get_behavior_facts()
    assert (
        updated["facts"]["task"]["setup_and_upgrade"]["storage_receipt"]
        == "next-format"
    )
    assert (
        updated["facts"]["task"]["default_request"]
        == declared["facts"]["task"]["default_request"]
    )
    assert updated["contract_id"] != declared["contract_id"]


def test_saved_historical_facts_roundtrip_and_render_without_recapture(
    tmp_path, declared, monkeypatch
):
    stored = deepcopy(declared)
    stored["facts"]["package"].update(version="1.0", requires_python=">=3.9")
    stored["facts"]["storage"]["setup_and_upgrade"]["knowledge_format"] = "v1"
    stored["facts"]["skills"][0]["description"] = "Literal <button> and [Click](target)"
    seal(stored)
    schema = json.loads(
        resources.files("llm_wiki_cli.schemas")
        .joinpath("llm-wiki-behavior-facts-v1.schema.json")
        .read_bytes()
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(stored)
    path = tmp_path / "historical facts.json"
    path.write_bytes(json.dumps(stored, ensure_ascii=False).encode("utf-8"))
    monkeypatch.setattr(
        reference,
        "get_behavior_facts",
        lambda: pytest.fail("Saved input must stay inert"),
    )
    assert reference.load_behavior_facts(path) == stored
    raw = reference.render_behavior_reference(MappingProxyType(stored))
    assert raw == reference.render_behavior_reference(
        reference.parse_behavior_facts(path.read_bytes())
    )
    assert (
        ">=3.9" in raw and "1.0" in raw and "Setup and upgrade knowledge format" in raw
    )
    assert "<button>" not in raw and "[Click](target)" not in raw
    assert "wiki_dir" not in raw and str(tmp_path) not in raw


@pytest.mark.parametrize(
    "change",
    [
        "unknown",
        "type",
        "skill-path",
        "duplicate-skill",
        "claimed-observation",
        "commitment",
    ],
)
def test_rejects_invalid_contracts_before_rendering(declared, change):
    facts = declared["facts"]
    if change == "unknown":
        facts["runtime"] = {}
    elif change == "type":
        facts["setup"]["new_project"]["quality_hints"] = 1
    elif change == "skill-path":
        facts["skills"][0]["files"].append("../consumer/README.md")
    elif change == "duplicate-skill":
        facts["skills"].append(facts["skills"][0])
    elif change == "claimed-observation":
        facts["storage"]["observed_wiki_formats"] = {"knowledge": "v1"}
    else:
        declared["contract_id"] = "sha256:" + "0" * 64
    if change != "commitment":
        seal(declared)
    with pytest.raises(ValueError):
        reference.render_behavior_reference(declared)


def test_saved_reader_rejects_oversize_duplicates_and_invalid_unicode(
    tmp_path: Path, declared
):
    content = json.dumps(declared)
    for raw in (
        content.replace('"facts":', '"facts": {}, "facts":', 1),
        b"\xff",
        " " * (reference.MAX_BEHAVIOR_FACTS_BYTES + 1),
    ):
        with pytest.raises(ValueError):
            reference.parse_behavior_facts(raw)
    oversized = tmp_path / "oversize.json"
    oversized.write_bytes(b" " * (reference.MAX_BEHAVIOR_FACTS_BYTES + 1))
    with pytest.raises(ValueError):
        reference.load_behavior_facts(oversized)
