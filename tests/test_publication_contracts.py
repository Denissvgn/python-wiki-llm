"""Imported publication documents retain exact, bounded, qualified contracts."""

from copy import deepcopy
import argparse
import json
from typing import Any

import pytest

from llm_wiki_cli.services.knowledge_evidence import hash_json, sha256_bytes
from llm_wiki_cli import api
from llm_wiki_cli.services.markdown_sections import parse_markdown_document
from llm_wiki_cli.services.publication_config import (
    PUBLICATION_CONFIG_SCHEMA_VERSION,
    validate_publication_config,
)
from llm_wiki_cli.services.publication_contracts import (
    PublicationProtocolError,
    validate_publication_basis,
    validate_publication_report,
    validate_publication_reviews,
)
from llm_wiki_cli.services.publication_impact import compare_publication_impact
from llm_wiki_cli.services.publication_snapshot import build_publication_snapshot
from llm_wiki_cli.services import publication_contracts, publication_impact
from llm_wiki_cli.services.cli_reference import (
    build_cli_contract,
    validate_cli_contract,
)
from tests.test_snapshot_query_validation import _committed_snapshot


H = sha256_bytes(b"fixture")


def seal(value, key):
    value[key] = hash_json({name: item for name, item in value.items() if name != key})
    return value


def basis():
    markdown = "# CLI\n\n## Description\n\nFixture.\n"
    document = parse_markdown_document(markdown, "llm-wiki://modules/cli")
    page = {
        "canonical_path": "modules/cli.md",
        "kind": "modules",
        "id": "cli",
        "locator": document.page_locator,
        "mcp_uri": document.page_locator,
        "uid": None,
        "role": "semantic",
        "raw_hash": sha256_bytes(markdown.encode()),
        "normalized_hash": document.exact_hash,
        "source_basis": None,
        "source_mapping": None,
        "section_ordering_hash": document.ordering_hash,
        "sections": [
            {**section.to_payload(), "ownership": "unknown"}
            for section in document.sections
        ],
    }
    native = seal(
        {
            "schema_version": "llm-wiki-publication-snapshot/v1",
            "complete": True,
            "coverage": {
                "scope": "canonical-native-pages",
                "page_count": 1,
                "section_model": "native-atx/v1",
                "source_mapping": "non-exhaustive",
            },
            "freshness": {"scope": "snapshot-only", "state": "not-evaluated"},
            "commitments": {
                **{
                    key: H
                    for key in (
                        "source_snapshot_hash",
                        "markdown_snapshot_hash",
                        "generation_options_hash",
                        "producer_hash",
                        "surface_index_hash",
                        "knowledge_index_hash",
                        "manifest_hash",
                    )
                },
                "evaluated_envelope_hash": None,
                "governance_hash": None,
                "manifest_storage_version": 8,
            },
            "pages": [page],
        },
        "snapshot_id",
    )
    config = validate_publication_config(
        {
            "schema_version": PUBLICATION_CONFIG_SCHEMA_VERSION,
            "architecture": {"baseline": "existing-wiki", "root": "wiki"},
            "target": {"kind": "github-wiki", "repository": "self"},
            "enforcement": "required",
            "publish": False,
            "topics": [
                {
                    "id": "cli",
                    "owner": "maintainers",
                    "wiki_page": "CLI.md",
                    "edit_at": "wiki",
                    "depends_on": [{"architecture_page": "modules/cli.md"}],
                }
            ],
        },
        consumer_root=None,
    )
    return seal(
        {
            "schema_version": "llm-wiki-publication-basis/v1",
            "config": config,
            "architecture": native,
            "files": {},
            "targets": {"cli": {"state": "available", "hash": H}},
        },
        "basis_id",
    )


def reseal_basis(value):
    seal(value["architecture"], "snapshot_id")
    return seal(value, "basis_id")


def review_record() -> dict[str, Any]:
    return {
        "topic": "cli",
        "owner": "maintainers",
        "reviewer": "reviewer",
        "reason": "Still correct",
        "decision": "still-current",
        "review_basis": H,
    }


def cli_contract(*, application=False):
    program = "application" if application else "llm-wiki"
    return seal(
        {
            "schema_version": "llm-wiki-cli-contract/v1",
            "package": {
                "name": "application-cli" if application else "agent-wiki-cli",
                "version": "1.0.0",
                "requires_python": ">=3.11",
            },
            "program": program,
            "root": {
                "name": program,
                "path": [],
                "aliases": [],
                "help": None,
                "description": None,
                "epilog": None,
                "deprecated": False,
                "notes": [],
                "arguments": [],
                "groups": [],
                "exclusive_groups": [],
                "commands": [],
                "subcommands_required": False,
                "defaults": {},
                "settings": {
                    "prefix_chars": "-",
                    "allow_abbrev": True,
                    "fromfile_prefix_chars": None,
                },
            },
        },
        "contract_id",
    )


def reference_basis(
    *, provider: dict[str, Any] | None = None, contract: Any = "builtin"
):
    payload = basis()
    provider = {"kind": "llm-wiki-cli"} if provider is None else provider
    payload["config"]["reference_providers"] = {"cli.v1": provider}
    payload["config"]["topics"][0]["depends_on"] = [{"reference": "cli.v1"}]
    payload["config"] = validate_publication_config(
        payload["config"], consumer_root=None
    )
    descriptor = {"provider": "cli.v1", "configuration": provider}
    payload["references"] = {
        hash_json(descriptor): {
            **descriptor,
            "contract": cli_contract() if contract == "builtin" else contract,
        }
    }
    return reseal_basis(payload)


def test_real_native_snapshot_validates_without_consulting_its_former_paths(tmp_path):
    _committed_snapshot(tmp_path, "packed-v4-deflate", governed=True)
    payload = basis()
    payload["architecture"] = build_publication_snapshot(tmp_path)
    reseal_basis(payload)
    validate_publication_basis(payload)


def test_real_default_bootstrap_snapshot_validates_all_current_page_kinds(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text(
        "class Application:\n    pass\n", encoding="utf-8"
    )
    api.bootstrap_wiki("src", "wiki")
    payload = basis()
    payload["architecture"] = build_publication_snapshot(tmp_path / "wiki")
    assert payload["architecture"]["commitments"]["manifest_storage_version"] == 8
    reseal_basis(payload)
    validate_publication_basis(payload)


def test_basis_and_reports_are_accepted_without_mutating_the_caller():
    payload = basis()
    before = deepcopy(payload)
    validate_publication_basis(payload)
    report = compare_publication_impact(payload)
    validate_publication_report(report)
    assert payload == before
    ledger = {
        "schema_version": "llm-wiki-publication-reviews/v1",
        "records": [review_record()],
    }
    result = validate_publication_reviews(ledger)
    result[0]["reason"] = "Changed by caller"
    assert ledger["records"][0]["reason"] == "Still correct"
    assert validate_publication_reviews(None) == []


def test_basis_requires_declared_asset_observations_and_preserves_content_policy():
    payload = basis()
    payload["config"]["content"] = {
        "root": "docs/public",
        "assets": [
            {
                "source_document": "docs/public/logo.png",
                "wiki_path": "assets/logo.png",
                "owner": "maintainers",
            }
        ],
    }
    payload["config"] = validate_publication_config(
        payload["config"], consumer_root=None
    )
    reseal_basis(payload)
    with pytest.raises(PublicationProtocolError, match="asset"):
        validate_publication_basis(payload)
    payload["files"]["docs/public/logo.png"] = None
    reseal_basis(payload)
    unchanged = deepcopy(payload)
    validate_publication_basis(payload)
    assert payload == unchanged


def test_reference_inputs_are_opt_in_and_legacy_bases_retain_their_shape():
    legacy = basis()
    before = deepcopy(legacy)
    validate_publication_basis(legacy)
    assert legacy == before and "references" not in legacy
    payload = reference_basis()
    before = deepcopy(payload)
    validate_publication_basis(payload)
    assert payload == before


def test_capture_enforces_the_aggregate_basis_node_bound(tmp_path, monkeypatch):
    fixture = basis()
    policy = deepcopy(fixture["config"])
    provider = {"kind": "contract-file", "path": "reference.json"}
    policy["reference_providers"] = {"first": provider}
    policy["topics"][0]["depends_on"] = [{"reference": "first", "command": []}]
    policy = validate_publication_config(policy, consumer_root=None)
    (tmp_path / "wiki").mkdir()
    parser = argparse.ArgumentParser(prog="application", add_help=False)
    parser.add_argument("--values", default=[0] * 400)
    contract = build_cli_contract(
        parser,
        program="application",
        package={"name": "application", "version": "1", "requires_python": None},
    )
    validate_cli_contract(contract)
    (tmp_path / "reference.json").write_text(json.dumps(contract), encoding="utf-8")
    monkeypatch.setattr(
        publication_impact,
        "load_publication_config",
        lambda *args, **kwargs: deepcopy(policy),
    )
    monkeypatch.setattr(
        publication_impact,
        "build_publication_snapshot",
        lambda root: deepcopy(fixture["architecture"]),
    )
    # Each contract and a complete one-provider basis fit. Combining otherwise
    # valid inputs must fail capture before returning a basis that cannot later
    # pass the same publication protocol's aggregate structural bound.
    monkeypatch.setattr(publication_contracts, "_MAX_JSON_NODES", 1000)
    single = publication_impact.capture_publication_basis(tmp_path)
    validate_publication_basis(single)
    policy["reference_providers"]["second"] = provider
    policy["topics"][0]["depends_on"].append({"reference": "second", "command": []})
    policy = validate_publication_config(policy, consumer_root=None)
    with pytest.raises(PublicationProtocolError, match="JSON structural bounds"):
        publication_impact.capture_publication_basis(tmp_path)


def test_custom_cli_and_known_missing_contract_files_are_valid_portable_inputs():
    provider = {"kind": "contract-file", "path": "contracts/application.json"}
    for contract in (cli_contract(application=True), None):
        validate_publication_basis(
            reference_basis(provider=provider, contract=contract)
        )


def test_remapped_provider_retains_both_current_and_previous_definitions():
    provider = {"kind": "contract-file", "path": "contracts/current.json"}
    payload = reference_basis(
        provider=provider, contract=cli_contract(application=True)
    )
    previous = {
        "provider": "cli.v1",
        "configuration": {"kind": "contract-file", "path": "contracts/previous.json"},
    }
    payload["references"][hash_json(previous)] = {
        **previous,
        "contract": cli_contract(application=True),
    }
    reseal_basis(payload)
    validate_publication_basis(payload)
    del payload["references"][
        hash_json({"provider": "cli.v1", "configuration": provider})
    ]
    reseal_basis(payload)
    with pytest.raises(
        PublicationProtocolError, match="every declared current provider"
    ):
        validate_publication_basis(payload)


def test_reference_union_has_a_bound_for_current_and_previous_provider_sets():
    payload = basis()
    provider = {"kind": "contract-file", "path": "contracts/application.json"}
    payload["references"] = {}
    for index in range(129):
        descriptor = {"provider": f"provider-{index}", "configuration": provider}
        payload["references"][hash_json(descriptor)] = {**descriptor, "contract": None}
    reseal_basis(payload)
    with pytest.raises(PublicationProtocolError, match="reference input bounds"):
        validate_publication_basis(payload)


@pytest.mark.parametrize(
    "change",
    [
        "missing-map",
        "empty-map",
        "null-map",
        "unknown-field",
        "identity",
        "provider-id",
        "path",
        "builtin-null",
        "foreign-builtin",
        "contract-seal",
        "contract-schema",
    ],
)
def test_reference_inputs_reject_missing_tampered_or_mislabeled_provider_data(change):
    payload = reference_basis()
    identity, reference = next(iter(payload["references"].items()))
    if change == "missing-map":
        del payload["references"]
    elif change == "empty-map":
        payload["references"] = {}
    elif change == "null-map":
        payload["references"] = None
    elif change == "unknown-field":
        reference["unknown"] = True
    elif change == "identity":
        payload["references"] = {H: reference}
    elif change == "provider-id":
        reference["provider"] = "different.v1"
    elif change == "path":
        reference["configuration"] = {"kind": "contract-file", "path": "../unsafe.json"}
        payload["references"] = {
            hash_json(
                {key: reference[key] for key in ("provider", "configuration")}
            ): reference
        }
    elif change == "builtin-null":
        reference["contract"] = None
    elif change == "foreign-builtin":
        reference["contract"] = cli_contract(application=True)
    elif change == "contract-seal":
        reference["contract"]["contract_id"] = H
    else:
        reference["contract"]["root"]["executable"] = "do-not-run"
        seal(reference["contract"], "contract_id")
    reseal_basis(payload)
    with pytest.raises(PublicationProtocolError):
        validate_publication_basis(payload)


def reference_report(evidence):
    report = compare_publication_impact(basis())
    finding = report["findings"][0]
    dependency = {"reference": "cli.v1", "command": ["docs", "impact"]}
    finding["reasons"] = [
        {
            "kind": "dependency-changed",
            "before": None,
            "after": {"dependency": dependency, "hash": evidence},
        }
    ]
    seal(finding, "id")
    return seal(report, "report_id")


@pytest.mark.parametrize(
    "evidence",
    [
        None,
        {"provider": {"kind": "llm-wiki-cli"}, "contract": H},
        {
            "provider": {"kind": "contract-file", "path": "contracts/application.json"},
            "contract": H,
        },
    ],
)
def test_report_reference_dependencies_carry_only_scoped_commitments(evidence):
    validate_publication_report(reference_report(evidence))


@pytest.mark.parametrize(
    "evidence",
    [
        {"provider": {"kind": "llm-wiki-cli"}, "contract": ""},
        {"provider": {"kind": "llm-wiki-cli"}, "contract": None},
        {"provider": {"kind": "executable"}, "contract": H},
        {
            "provider": {"kind": "contract-file", "path": "../unsafe.json"},
            "contract": H,
        },
        {"provider": {"kind": "llm-wiki-cli"}, "contract": H, "command": []},
    ],
)
def test_report_reference_dependencies_reject_unsafe_or_missing_commitments(evidence):
    with pytest.raises(PublicationProtocolError):
        validate_publication_report(reference_report(evidence))


@pytest.mark.parametrize(
    "path,value",
    [
        (("files",), {"../outside": H}),
        (("files",), {"src/a.py": "not-a-hash"}),
        (("files",), {"src/a.py": H, "SRC/a.py": H}),
        (("files",), {"src/a.py": H, "SRC/b.py": H}),
        (("targets", "cli"), {"state": "available", "hash": ""}),
        (("targets", "cli"), {"state": "missing", "hash": 0}),
        (("targets", "cli"), {"state": "not-evaluated", "hash": None}),
        (("architecture", "commitments", "generation_options_hash"), ""),
        (("architecture", "commitments", "manifest_storage_version"), True),
        (("architecture", "coverage", "page_count"), 2),
        (("architecture", "freshness"), {"scope": "live", "state": "current"}),
        (("architecture", "pages", 0, "normalized_hash"), ""),
        (("architecture", "pages", 0, "canonical_path"), "modules/../cli.md"),
        (("architecture", "pages", 0, "locator"), "llm-wiki://modules/other"),
        (("architecture", "pages", 0, "role"), "generated"),
        (
            ("architecture", "pages", 0, "source_mapping"),
            {"scope": "module", "source_path": "src/cli.py", "unknown": True},
        ),
        (("architecture", "pages", 0, "sections", 0, "child_locators"), []),
        (("architecture", "pages", 0, "sections", 1, "ordinal"), True),
        (
            ("architecture", "pages", 0, "sections", 1, "locator"),
            "llm-wiki://modules/cli#section/forged~1",
        ),
        (("architecture", "pages", 0, "sections", 1, "exact_hash"), ""),
        (("architecture", "pages", 0, "sections", 1, "structural_hash"), H),
    ],
)
def test_resealed_malformed_evidence_is_rejected_before_use(path, value):
    payload = basis()
    selected = payload
    for key in path[:-1]:
        selected = selected[key]
    selected[path[-1]] = value
    reseal_basis(payload)
    with pytest.raises(PublicationProtocolError):
        validate_publication_basis(payload)


@pytest.mark.parametrize(
    "kind", ["page", "section", "unknown-field", "nonfinite", "depth"]
)
def test_duplicate_unknown_and_adversarial_json_structures_fail_closed(kind):
    payload = basis()
    if kind == "page":
        payload["architecture"]["pages"].append(
            deepcopy(payload["architecture"]["pages"][0])
        )
        payload["architecture"]["coverage"]["page_count"] = 2
    elif kind == "section":
        sections = payload["architecture"]["pages"][0]["sections"]
        sections.append(deepcopy(sections[-1]))
    elif kind == "unknown-field":
        payload["architecture"]["pages"][0]["unknown"] = "unexpected"
    elif kind == "nonfinite":
        payload["extra"] = float("nan")
    else:
        nested = payload
        for _ in range(70):
            nested["extra"] = {}
            nested = nested["extra"]
    if kind != "nonfinite":
        reseal_basis(payload)
    with pytest.raises(PublicationProtocolError):
        validate_publication_basis(payload)


@pytest.mark.parametrize(
    "change", ["duplicate", "unknown", "decision", "hash", "missing"]
)
def test_reviews_require_unique_explicit_decisions_for_exact_hashes(change):
    record = review_record()
    records = [record]
    if change == "duplicate":
        records.append(deepcopy(record))
    elif change == "unknown":
        record["extra"] = True
    elif change == "decision":
        record["decision"] = "auto-approve"
    elif change == "hash":
        record["review_basis"] = ""
    else:
        del record["reviewer"]
    with pytest.raises(PublicationProtocolError):
        validate_publication_reviews(
            {"schema_version": "llm-wiki-publication-reviews/v1", "records": records}
        )


def test_reviewed_status_retains_stable_finding_identity():
    payload = basis()
    report = compare_publication_impact(payload)
    finding = report["findings"][0]
    ledger = {
        "schema_version": "llm-wiki-publication-reviews/v1",
        "records": [{**review_record(), "review_basis": finding["review_basis"]}],
    }
    reviewed = compare_publication_impact(payload, reviews=ledger)
    assert reviewed["findings"][0]["id"] == finding["id"]
    assert reviewed["findings"][0]["status"] == "reviewed-current"
    validate_publication_report(reviewed)


def test_retirement_ledger_records_are_explicit_and_detached():
    record = {
        **review_record(),
        "decision": "retired",
        "reason": "The former public topic was removed",
    }
    ledger = {"schema_version": "llm-wiki-publication-reviews/v1", "records": [record]}
    assert validate_publication_reviews(ledger) == [record]
    assert ledger["records"][0]["decision"] == "retired"


def retired_report(target, *, retirement=True, status="reviewed-retired"):
    report = compare_publication_impact(basis())
    finding = report["findings"][0]
    finding["reasons"] = [
        {"kind": "mapping-retired" if retirement else "mapping-changed"}
    ]
    finding["target"] = target
    finding["status"] = "needs-review"
    seal(finding, "id")
    finding["status"] = status
    report.update(complete=True, review_required=False, ready=True)
    return seal(report, "report_id")


@pytest.mark.parametrize(
    "target",
    [
        {"state": "available", "hash": H},
        {"state": "missing", "hash": None},
        {"state": "unresolved-anchor", "hash": H},
    ],
)
def test_reviewed_retirement_preserves_finding_id_and_observed_target(target):
    report = retired_report(target)
    validate_publication_report(report)
    assert report["findings"][0]["status"] == "reviewed-retired"


@pytest.mark.parametrize(
    "target,retirement,status",
    [
        ({"state": "available", "hash": H}, False, "reviewed-retired"),
        ({"state": "missing", "hash": None}, False, "reviewed-retired"),
        ({"state": "not-evaluated", "hash": None}, True, "reviewed-retired"),
        ({"state": "unresolved-anchor", "hash": None}, True, "reviewed-retired"),
        ({"state": "missing", "hash": None}, True, "reviewed-current"),
        ({"state": "available", "hash": H}, True, "reviewed-current"),
    ],
)
def test_retirement_dispositions_cannot_bless_active_or_unobserved_content(
    target, retirement, status
):
    with pytest.raises(PublicationProtocolError):
        validate_publication_report(
            retired_report(target, retirement=retirement, status=status)
        )


def test_native_preamble_is_separate_from_the_atx_order_commitment():
    payload = basis()
    page = payload["architecture"]["pages"][0]
    ordering = page["section_ordering_hash"]
    preamble: dict[str, Any] = {
        "locator": page["locator"] + "#section/@preamble",
        "page_locator": page["locator"],
        "exact_hash": H,
        "ownership": "semantic",
        "semantic_hash": H,
    }
    page["preamble"] = preamble
    reseal_basis(payload)
    validate_publication_basis(payload)
    assert page["section_ordering_hash"] == ordering
    assert all(
        section["locator"] != preamble["locator"] for section in page["sections"]
    )


@pytest.mark.parametrize(
    "change", ["null", "page", "locator", "hash", "ownership", "unknown"]
)
def test_native_preamble_rejects_foreign_coordinates_and_invented_ownership(change):
    payload = basis()
    page = payload["architecture"]["pages"][0]
    preamble: dict[str, Any] = {
        "locator": page["locator"] + "#section/@preamble",
        "page_locator": page["locator"],
        "exact_hash": H,
        "ownership": "semantic",
        "semantic_hash": H,
    }
    if change == "null":
        page["preamble"] = None
    else:
        page["preamble"] = preamble
        if change == "page":
            preamble["page_locator"] = "llm-wiki://modules/foreign"
        elif change == "locator":
            preamble["locator"] = page["locator"] + "#section/Description~1"
        elif change == "hash":
            preamble["semantic_hash"] = sha256_bytes(b"different")
        elif change == "ownership":
            preamble["ownership"] = "unknown"
        else:
            preamble["unknown"] = True
    reseal_basis(payload)
    with pytest.raises(PublicationProtocolError):
        validate_publication_basis(payload)


@pytest.mark.parametrize(
    "change", ["findings", "coverage", "ready", "flags", "seal", "target", "hash"]
)
def test_reports_reject_inconsistent_flags_findings_and_target_witnesses(change):
    report = compare_publication_impact(basis())
    if change == "findings":
        report["findings"].append(deepcopy(report["findings"][0]))
    elif change == "coverage":
        report["coverage"]["unmapped"] = 1
    elif change == "ready":
        report["ready"] = True
    elif change == "flags":
        report["complete"] = 1
    elif change == "target":
        report["findings"][0]["target"] = {"state": "available", "hash": None}
    elif change == "hash":
        report["findings"][0]["review_basis"] = ""
    if change != "seal":
        seal(report, "report_id")
    else:
        report["report_id"] = H
    with pytest.raises(PublicationProtocolError):
        validate_publication_report(report)


def test_error_only_incomplete_reports_cannot_be_resolved():
    with pytest.raises(PublicationProtocolError):
        validate_publication_report(
            {
                "schema_version": "llm-wiki-publication-impact/v1",
                "complete": False,
                "ready": False,
                "error": {"code": "input-unavailable"},
            }
        )
