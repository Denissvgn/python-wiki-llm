"""Historical success, unavailable costs and future work cannot become closure."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from tests.developer_value.evidence_reconciliation import (
    ADOPTIONS,
    CONTRACT_SCHEMA,
    ORIGINAL_REQUIREMENTS,
    DISPOSITIONS,
    FUTURE,
    SCHEMA,
    TASKS,
    UNMEASURED,
    validate_reconciliation,
)


@pytest.fixture
def packet():
    """Authority is assembled independently, then the candidate is copied from it."""
    source = sha256(b"current producer").hexdigest()
    historical = sha256(b"historical baseline producer").hexdigest()
    candidate = sha256(b"historical candidate producer").hexdigest()
    sources = {"src/llm_wiki_cli/extractors/python_bindings.py": source}
    caller = {"reviewed_binding_sha256": source, "required_repairs_remaining": [],
              "results": {"applicable_controls": 2, "applicable_passes": 2,
                          "receiving_consistent_readonly": 3, "valid_public_facts": 3,
                          "applicable_failures": 0, "private_binding_keys": 0}}
    score = {"actionable": 4, "denominator": 5, "covered_count": 2, "required_count": 2}
    triage = {"passed": True, "issues": [], "splits": {
        "development": score, "confirmation": deepcopy(score)}}
    original_tasks = {k: {"title": f"Reviewed {k} requirement", "status": "done",
                          "output_commit": f"{i:040x}"}
                      for i, k in enumerate(sorted(ORIGINAL_REQUIREMENTS), 1)}
    deliveries = {k: {"task": k, "status": "done", "outcome": f"Scoped {k} delivery",
                      "commit": sha256(k.encode()).hexdigest()[:40]}
                  for k in TASKS - FUTURE - {"AF20"}}
    payloads = {"caller-current": caller, "triage-prospective": triage,
                "original-state": {"tasks": original_tasks},
                "measurement-profile": {"arms": {"baseline": {"source_files": {
                    "src/producer~version.py": historical}}},
                    "runs": [{"provider": candidate}]},
                **{f"task-{k}": v for k, v in deliveries.items()}}
    raw = {f"fixtures/{k}.json": json.dumps(v).encode() for k, v in payloads.items()}
    trusted = {p: sha256(b).hexdigest() for p, b in raw.items()}
    evidence = {k: {"path": f"fixtures/{k}.json", "sha256": trusted[f"fixtures/{k}.json"],
                    "format": "json"} for k in payloads}
    findings = {k: {"status": v, "original_claim": "Retained original claim",
                    "tasks": ["AF19"], "evidence": ["caller-current", "triage-prospective"],
                    "limits": ["Scoped evidence only"]} for k, v in DISPOSITIONS.items()}
    tasks = {k: {"required": True,
                 "status": "pending" if k in FUTURE else "validating" if k == "AF20" else "done",
                 "remaining": "Actual integration and final verification",
                 "evidence": [f"task-{k}"] if k in deliveries else [],
                 "work_outcome": deliveries[k]["outcome"] if k in deliveries else None,
                 "output_commit": deliveries[k]["commit"] if k in deliveries else None}
             for k in TASKS}
    originals = {k: {"title": v["title"], "original_recorded_status": v["status"],
                     "original_output_commit": v["output_commit"],
                     "current_disposition": "Historical only; no final closure",
                     "affected_findings": ["R3"], "evidence": ["original-state"]}
                 for k, v in original_tasks.items()}
    adoptions = {k: {"decision": "retain-shipped-contract", "new_prototype_adopted": False,
                     "default": "Existing contract", "evidence": ["caller-current"]}
                 for k in ADOPTIONS}
    profiles = [{"evidence": "measurement-profile", "pointer": "/arms/baseline/source_files",
                 "prefix": "baseline"},
                {"evidence": "measurement-profile", "pointer": "/runs/0/provider",
                 "prefix": "candidate", "key": "provider"}]
    reviewed_claims = {
        "review_method": "Independent informed source review; no human/model/blinding claim",
        "input_revision": sha256(b"reviewed input revision").hexdigest()[:40],
        "input_tree": sha256(b"reviewed input tree").hexdigest()[:40],
        "claim_limits": dict(UNMEASURED), "findings": findings, "tasks": tasks,
        "original_requirements": originals, "adoptions": adoptions,
        "historical_limits": {"original_triage": "historical-unmeasured",
                              "retrospective_is_prospective": False,
                              "historical_cost_recovered": False,
                              "current_producer_triage_measurement": "not-claimed"},
        "amendments": {"A1": "pending-integration-cost", "A2": "source-companion-draft-only"},
        "generated_trace_passed": False,
        "combined_limits": {"required": 8, "surfaced": 7, "missed_unsolved": 1,
                            "unknown_rows": 143, "uninvoked": 4},
    }
    contract = {"schema_version": CONTRACT_SCHEMA, "evidence_roles": evidence,
                **deepcopy(reviewed_claims), "measurement_rules": {
                    "historical-trial": {"profiles": profiles, "scope": "Frozen comparable inputs",
                                         "restriction": "Original producer only",
                                         "evidence": ["triage-prospective", "measurement-profile"]}}}
    contract_bytes = json.dumps(contract).encode()
    expected_pin = sha256(contract_bytes).hexdigest()
    record = {"schema_version": SCHEMA, "provisional": True, "final_closure": False,
              "current_sources": deepcopy(sources), "evidence": deepcopy(evidence),
              **deepcopy(reviewed_claims), "measurements": [
                  {"id": "historical-trial", "evidence": ["triage-prospective", "measurement-profile"],
                   "producer_sources": {"baseline:src/producer~version.py": historical,
                                        "candidate:provider": candidate},
                   "producer_identity_evidence": ["measurement-profile"],
                   "applicability": "historical-pinned-treatment", "current_performance_claim": False,
                   "observations_reexecuted": False,
                   "scope": "Frozen comparable inputs", "restriction": "Original producer only"}]}
    return record, trusted, raw, sources, contract_bytes, expected_pin


def check(packet):
    record, trusted, raw, sources, contract_bytes, expected_pin = packet
    return validate_reconciliation(record, trusted_artifacts=trusted,
                                   artifact_bytes=raw, current_sources=sources,
                                   contract_bytes=contract_bytes, expected_contract_sha256=expected_pin)


def test_provisional_acceptance_keeps_future_and_missing_outcomes(packet):
    before = deepcopy(packet)
    result = check(packet)
    assert result == {"accepted": True, "provisional": True, "final_closure": False,
                      "findings": 9, "mandatory_tasks": 25,
                      "authenticated_artifacts": 24, "current_source_count": 1}
    assert packet == before


@pytest.mark.parametrize("identity", DISPOSITIONS)
def test_missing_or_promoted_finding_cannot_pass(packet, identity):
    packet[0]["findings"].pop(identity)
    with pytest.raises(ValueError, match="Every original"):
        check(packet)


@pytest.mark.parametrize("identity", ["R3", "R4", "R5", "G1", "G2", "G3", "G4"])
def test_unmet_or_scoped_requirement_cannot_be_unqualified_fixed(packet, identity):
    packet[0]["findings"][identity]["status"] = "fixed"
    with pytest.raises(ValueError, match="Unsupported finding"):
        check(packet)


@pytest.mark.parametrize("identity", TASKS)
def test_mandatory_work_cannot_be_reclassified_optional(packet, identity):
    packet[0]["tasks"][identity]["required"] = False
    with pytest.raises(ValueError, match="Mandatory"):
        check(packet)


@pytest.mark.parametrize("identity", FUTURE)
def test_future_integration_gate_cannot_close_from_reconciliation(packet, identity):
    packet[0]["tasks"][identity]["status"] = "done"
    with pytest.raises(ValueError, match="remain pending"):
        check(packet)


@pytest.mark.parametrize("field,value", [
    ("original_triage", "passed"), ("retrospective_is_prospective", True),
    ("historical_cost_recovered", True), ("current_producer_triage_measurement", "passed"),
])
def test_retrospective_or_original_producer_data_never_becomes_current(packet, field, value):
    packet[0]["historical_limits"][field] = value
    with pytest.raises(ValueError, match="Historical"):
        check(packet)


@pytest.mark.parametrize("field", UNMEASURED)
def test_agent_or_token_evidence_cannot_establish_external_claim(packet, field):
    packet[0]["claim_limits"][field] = "passed"
    with pytest.raises(ValueError, match="Unmeasured"):
        check(packet)


@pytest.mark.parametrize("change", ["bytes", "pin", "path", "source"])
def test_independent_commitments_and_live_producer_are_required(packet, change):
    record, trusted, raw, sources, _, _ = packet
    if change == "bytes":
        raw["fixtures/caller-current.json"] = raw["fixtures/caller-current.json"] + b" "
    elif change == "pin":
        record["evidence"]["caller-current"]["sha256"] = "0" * 64
    elif change == "path":
        record["evidence"]["caller-current"]["path"] = "../caller.json"
    else:
        record["current_sources"] = {next(iter(sources)): "0" * 64}
    with pytest.raises(ValueError):
        check(packet)


def replace_payload(packet, path, value):
    record, trusted, raw, _, _, _ = packet
    raw[path] = json.dumps(value).encode()
    trusted[path] = sha256(raw[path]).hexdigest()
    for item in record["evidence"].values():
        if item["path"] == path:
            item["sha256"] = trusted[path]


@pytest.mark.parametrize("split", ["development", "confirmation"])
@pytest.mark.parametrize("field,value", [("actionable", 3), ("actionable", 6),
                                         ("denominator", 0), ("covered_count", 1),
                                         ("required_count", True)])
def test_authenticated_prospective_failure_cannot_be_hidden_by_pass_flag(packet, split, field, value):
    path = "fixtures/triage-prospective.json"
    payload = json.loads(packet[2][path])
    payload["splits"][split][field] = value
    replace_payload(packet, path, payload)
    with pytest.raises(ValueError):
        check(packet)


def test_authenticated_stale_caller_or_missing_positive_cannot_close_fix(packet):
    path = "fixtures/caller-current.json"
    payload = json.loads(packet[2][path])
    payload["reviewed_binding_sha256"] = "0" * 64
    replace_payload(packet, path, payload)
    with pytest.raises(ValueError, match="different producer"):
        check(packet)


@pytest.mark.parametrize("field,value", [("missed_unsolved", 0), ("unknown_rows", 0),
                                         ("uninvoked", 0), ("surfaced", 8)])
def test_legacy_unknown_and_uninvoked_work_stays_no_credit(packet, field, value):
    packet[0]["combined_limits"][field] = value
    with pytest.raises(ValueError, match="unavailable work"):
        check(packet)


@pytest.mark.parametrize("field,value", [("applicability", "current"),
                                         ("current_performance_claim", True)])
def test_pinned_old_measurements_are_not_current_after_producer_change(packet, field, value):
    packet[0]["measurements"][0][field] = value
    with pytest.raises(ValueError, match="current performance"):
        check(packet)


@pytest.mark.parametrize("identity", ADOPTIONS)
def test_optional_trial_miss_cannot_promote_prototype_default(packet, identity):
    packet[0]["adoptions"][identity]["new_prototype_adopted"] = True
    with pytest.raises(ValueError, match="new adoption"):
        check(packet)


def test_source_companion_and_partial_cost_are_not_original_acceptance(packet):
    packet[0]["amendments"]["A1"] = "complete"
    with pytest.raises(ValueError, match="Substitution"):
        check(packet)


@pytest.mark.parametrize("identity", sorted(ORIGINAL_REQUIREMENTS))
def test_original_requirement_coverage_is_mandatory(packet, identity):
    packet[0]["original_requirements"].pop(identity)
    with pytest.raises(ValueError, match="Every original requirement"):
        check(packet)


def test_original_requirement_section_cannot_be_omitted(packet):
    packet[0].pop("original_requirements")
    with pytest.raises(ValueError, match="original_requirements"):
        check(packet)


@pytest.mark.parametrize("field,value", [
    ("title", "Invented obligation"), ("original_recorded_status", "accepted"),
    ("original_output_commit", "0" * 40),
    ("current_disposition", "All requirements passed; no material finding"),
    ("affected_findings", []), ("evidence", ["caller-current"]),
])
def test_original_requirement_metadata_and_disposition_are_frozen(packet, field, value):
    packet[0]["original_requirements"]["DV26"][field] = value
    with pytest.raises(ValueError):
        check(packet)


@pytest.mark.parametrize("section,identity,field,value", [
    ("findings", "R3", "limits", ["Current HEAD achieved 100% coverage and actionability"]),
    ("findings", "R1", "original_claim", "Runtime equivalence established"),
    ("findings", "R4", "tasks", ["AF18"]),
    ("findings", "R2", "evidence", ["caller-current"]),
    ("tasks", "AF10", "evidence", ["caller-current"]),
    ("tasks", "AF19", "work_outcome", "All work accepted"),
    ("tasks", "AF19", "output_commit", "0" * 40),
    ("adoptions", "search", "default", "Mandatory paid embedding service"),
    ("adoptions", "compact", "default", "Experimental decoder enabled by default"),
    ("adoptions", "ordinary-review", "default", "Automatic durable adoption"),
    ("adoptions", "packed-optimization", "default", "New packed speed default"),
    ("adoptions", "search", "evidence", ["triage-prospective"]),
])
def test_reviewed_prose_and_task_specific_evidence_cannot_be_substituted(
        packet, section, identity, field, value):
    packet[0][section][identity][field] = value
    with pytest.raises(ValueError, match="contract mismatch"):
        check(packet)


@pytest.mark.parametrize("field,value", [
    ("id", "invented-measurement"),
    ("producer_sources", {"unrelated.py": "0" * 64}),
    ("producer_sources", {"baseline:src/producer~version.py": "0" * 64}),
    ("producer_sources", {}),
    ("producer_identity_evidence", []),
    ("producer_identity_evidence", ["caller-current"]),
    ("scope", "Current repaired producer performance"),
    ("restriction", "Historical results transport unchanged to current HEAD"),
    ("evidence", ["caller-current"]),
])
def test_frozen_measurement_identity_and_raw_producer_lineage(packet, field, value):
    packet[0]["measurements"][0][field] = value
    with pytest.raises(ValueError):
        check(packet)


@pytest.mark.parametrize("change", ["omit", "duplicate", "mix-arms", "extra-producer"])
def test_measurement_rows_and_all_arms_are_complete_unique_and_exact(packet, change):
    measurements = packet[0]["measurements"]
    if change == "omit":
        measurements.clear()
    elif change == "duplicate":
        measurements.append(deepcopy(measurements[0]))
    elif change == "mix-arms":
        pins = measurements[0]["producer_sources"]
        pins["candidate:provider"] = pins["baseline:src/producer~version.py"]
    else:
        measurements[0]["producer_sources"]["extra:fake.py"] = "0" * 64
    with pytest.raises(ValueError):
        check(packet)


def reviewed_contract_variant(packet, contract):
    """A distinct synthetic controller review supplies new bytes AND a new pin."""
    data = json.dumps(contract).encode()
    return (*packet[:4], data, sha256(data).hexdigest())


@pytest.mark.parametrize("section", ["evidence_roles", "measurement_rules", "adoptions", "tasks"])
def test_forged_external_contract_cannot_keep_original_controller_pin(packet, section):
    contract = json.loads(packet[4])
    contract[section] = {}
    forged = (*packet[:4], json.dumps(contract).encode(), packet[5])
    with pytest.raises(ValueError, match="Independent claim contract commitment"):
        check(forged)


@pytest.mark.parametrize("change", ["selector", "prefix", "leaf-key"])
def test_selector_rewrite_needs_an_independently_changed_controller_pin(packet, change):
    contract = json.loads(packet[4])
    profile = contract["measurement_rules"]["historical-trial"]["profiles"][1]
    profile[{"selector": "pointer", "prefix": "prefix", "leaf-key": "key"}[change]] = "invented"
    forged = (*packet[:4], json.dumps(contract).encode(), packet[5])
    with pytest.raises(ValueError, match="commitment mismatch"):
        check(forged)


@pytest.mark.parametrize("role", ["caller-current", "measurement-profile", "original-state", "task-AF10"])
def test_repinning_candidate_artifacts_does_not_rewrite_frozen_roles(packet, role):
    path = f"fixtures/{role}.json"
    payload = json.loads(packet[2][path])
    payload["self_accepted"] = True
    replace_payload(packet, path, payload)
    with pytest.raises(ValueError, match="Reviewed evidence role mismatch"):
        check(packet)


@pytest.mark.parametrize("data", [
    b'{"schema_version":"a","schema_version":"b"}', b'{"x":NaN}',
    b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e9999}', b'\xff', b'[]',
])
def test_contract_strict_json_and_mapping_boundaries(packet, data):
    supplied = (*packet[:4], data, sha256(data).hexdigest())
    with pytest.raises(ValueError):
        check(supplied)


@pytest.mark.parametrize("data", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e9999}', b'\xff'])
def test_artifact_json_is_strict_even_with_matching_controller_artifact_pin(packet, data):
    path = "fixtures/measurement-profile.json"
    packet[2][path] = data
    packet[1][path] = sha256(data).hexdigest()
    packet[0]["evidence"]["measurement-profile"]["sha256"] = packet[1][path]
    with pytest.raises(ValueError):
        check(packet)


@pytest.mark.parametrize("value", [None, "", "0" * 63, "A" * 64, "0" * 64])
def test_controller_contract_digest_is_required_and_exact(packet, value):
    with pytest.raises(ValueError, match="commitment mismatch"):
        check((*packet[:5], value))


def test_contract_parameters_cannot_be_omitted(packet):
    arguments = {"trusted_artifacts": packet[1], "artifact_bytes": packet[2],
                 "current_sources": packet[3]}
    with pytest.raises(TypeError):
        validate_reconciliation(packet[0], **arguments)


@pytest.mark.parametrize("change", ["role", "commit", "status", "outcome"])
def test_even_reviewed_task_rows_must_match_authenticated_delivery(packet, change):
    row = packet[0]["tasks"]["AF10"]
    field, value = {"role": ("evidence", ["caller-current"]),
                    "commit": ("output_commit", "0" * 40),
                    "status": ("work_outcome", "wrong status"),
                    "outcome": ("work_outcome", "invented outcome")}[change]
    row[field] = value
    if change == "status":
        path = "fixtures/task-AF10.json"
        raw = json.loads(packet[2][path])
        raw["status"] = "pending"
        replace_payload(packet, path, raw)
    contract = json.loads(packet[4])
    contract["tasks"]["AF10"] = deepcopy(row)
    contract["evidence_roles"] = deepcopy(packet[0]["evidence"])
    with pytest.raises(ValueError, match="delivery"):
        check(reviewed_contract_variant(packet, contract))


@pytest.mark.parametrize("field", ["title", "original_recorded_status", "original_output_commit"])
def test_reviewed_original_metadata_still_rederives_from_authenticated_original_state(packet, field):
    packet[0]["original_requirements"]["DV26"][field] = "fabricated"
    contract = json.loads(packet[4])
    contract["original_requirements"]["DV26"][field] = "fabricated"
    with pytest.raises(ValueError, match="metadata mismatch"):
        check(reviewed_contract_variant(packet, contract))


@pytest.mark.parametrize("pointer", ["runs/0/provider", "/runs/00/provider", "/runs/-1/provider",
                                      "/runs/1/provider", "/runs/0/prov~2ider", "/runs/0/provider~"])
def test_reviewed_profile_pointer_has_strict_syntax_and_cannot_guess(packet, pointer):
    contract = json.loads(packet[4])
    contract["measurement_rules"]["historical-trial"]["profiles"][1]["pointer"] = pointer
    with pytest.raises(ValueError, match="pointer"):
        check(reviewed_contract_variant(packet, contract))


@pytest.mark.parametrize("change", ["leaf-without-key", "map-with-key", "missing-role", "empty-profiles",
                                     "duplicate-source", "wrong-key-type", "extra-field"])
def test_reviewed_profile_types_and_source_collisions_fail_closed(packet, change):
    contract = json.loads(packet[4])
    profiles = contract["measurement_rules"]["historical-trial"]["profiles"]
    if change == "leaf-without-key":
        profiles[1].pop("key")
    elif change == "map-with-key":
        profiles[0]["key"] = "guessed-map"
    elif change == "missing-role":
        profiles[0]["evidence"] = "caller-current"
    elif change == "empty-profiles":
        profiles.clear()
    elif change == "duplicate-source":
        profiles.append(deepcopy(profiles[0]))
    elif change == "wrong-key-type":
        profiles[1]["key"] = True
    else:
        profiles[0]["auto_accept"] = True
    with pytest.raises(ValueError):
        check(reviewed_contract_variant(packet, contract))


def test_reviewed_profile_pointer_supports_json_pointer_escaping(packet):
    contract = json.loads(packet[4])
    profiles = contract["measurement_rules"]["historical-trial"]["profiles"]
    profiles[0].update(pointer="/arms/baseline/source_files/src~1producer~0version.py",
                       key="src/producer~version.py")
    assert check(reviewed_contract_variant(packet, contract))["accepted"] is True


@pytest.mark.parametrize("field", ["applicable_failures", "private_binding_keys"])
def test_false_is_not_a_numeric_zero_in_caller_evidence(packet, field):
    path = "fixtures/caller-current.json"
    caller = json.loads(packet[2][path])
    caller["results"][field] = False
    replace_payload(packet, path, caller)
    with pytest.raises(ValueError, match="Caller correctness"):
        check(packet)


@pytest.mark.parametrize("field", ["required", "surfaced", "missed_unsolved", "unknown_rows", "uninvoked"])
def test_review_authentication_does_not_coerce_integer_claims_to_floats(packet, field):
    packet[0]["combined_limits"][field] = float(packet[0]["combined_limits"][field])
    with pytest.raises(ValueError, match="contract mismatch"):
        check(packet)


@pytest.mark.parametrize("strip_prefix", ["", "baseline:", True, None])
def test_reviewed_leaf_identity_prefix_is_exact_and_typed(packet, strip_prefix):
    contract = json.loads(packet[4])
    profile = contract["measurement_rules"]["historical-trial"]["profiles"][1]
    profile["strip_prefix"] = strip_prefix
    with pytest.raises(ValueError, match="prefix mismatch"):
        check(reviewed_contract_variant(packet, contract))


def test_reviewed_prefixed_raw_provider_identity_is_derived_after_exact_strip(packet):
    path = "fixtures/measurement-profile.json"
    raw = json.loads(packet[2][path])
    raw["runs"][0]["provider"] = "candidate-a:" + raw["runs"][0]["provider"]
    replace_payload(packet, path, raw)
    contract = json.loads(packet[4])
    contract["evidence_roles"] = deepcopy(packet[0]["evidence"])
    contract["measurement_rules"]["historical-trial"]["profiles"][1]["strip_prefix"] = "candidate-a:"
    assert check(reviewed_contract_variant(packet, contract))["accepted"] is True


@pytest.mark.parametrize("value", [None, [], True, "not-bytes"])
def test_contract_bytes_must_be_bytes(packet, value):
    with pytest.raises(ValueError, match="commitment mismatch"):
        check((*packet[:4], value, packet[5]))


@pytest.mark.parametrize("target,value", [
    ("id", []), ("id", True), ("producer_identity_evidence", "measurement-profile"),
    ("evidence", [["triage-prospective"]]), ("evidence", [True]),
    ("evidence", ["measurement-profile", "measurement-profile"]),
    ("producer_sources", ["not-a-map"]),
])
def test_candidate_measurement_types_fail_closed_with_value_errors(packet, target, value):
    packet[0]["measurements"][0][target] = value
    with pytest.raises(ValueError):
        check(packet)


@pytest.mark.parametrize("schema", [None, "developer-value-reconciliation-contract/v2", True])
def test_authenticated_contract_still_needs_supported_schema(packet, schema):
    contract = json.loads(packet[4])
    contract["schema_version"] = schema
    with pytest.raises(ValueError, match="contract schema"):
        check(reviewed_contract_variant(packet, contract))


def test_reviewed_policy_update_requires_new_controller_pin_then_preserves_other_gates(packet):
    packet[0]["adoptions"]["compact"]["default"] = "Reviewed compatible explicit compact view"
    contract = json.loads(packet[4])
    contract["adoptions"]["compact"]["default"] = packet[0]["adoptions"]["compact"]["default"]
    with pytest.raises(ValueError, match="commitment mismatch"):
        check((*packet[:4], json.dumps(contract).encode(), packet[5]))
    reviewed = reviewed_contract_variant(packet, contract)
    assert check(reviewed)["accepted"] is True
    packet[0]["final_closure"] = True
    with pytest.raises(ValueError, match="remain provisional"):
        check(reviewed)


@pytest.mark.parametrize("field,value", [("actionable", 3), ("covered_count", 1)])
def test_new_independently_reviewed_artifact_contract_cannot_change_fixed_numeric_gates(
        packet, field, value):
    path = "fixtures/triage-prospective.json"
    raw = json.loads(packet[2][path])
    raw["splits"]["confirmation"][field] = value
    replace_payload(packet, path, raw)
    contract = json.loads(packet[4])
    contract["evidence_roles"] = deepcopy(packet[0]["evidence"])
    with pytest.raises(ValueError, match="threshold|coverage incomplete"):
        check(reviewed_contract_variant(packet, contract))


def nested_profile_packet(packet, member="sha256"):
    path = "fixtures/measurement-profile.json"
    raw = json.loads(packet[2][path])
    raw["arms"]["baseline"]["source_files"] = {
        k: {"sha256": v, "bytes": 100} for k, v in raw["arms"]["baseline"]["source_files"].items()}
    replace_payload(packet, path, raw)
    contract = json.loads(packet[4])
    contract["evidence_roles"] = deepcopy(packet[0]["evidence"])
    contract["measurement_rules"]["historical-trial"]["profiles"][0]["hash_member"] = member
    return reviewed_contract_variant(packet, contract)


def test_reviewed_named_hash_member_authenticates_nested_manifest_entries(packet):
    assert check(nested_profile_packet(packet))["accepted"] is True


@pytest.mark.parametrize("member", ["", None, True, "missing", "bytes"])
def test_nested_manifest_hash_member_is_typed_exact_and_digest_validated(packet, member):
    with pytest.raises(ValueError, match="Measurement profile"):
        check(nested_profile_packet(packet, member))


def test_nested_manifest_without_explicit_reviewed_hash_member_cannot_be_inferred(packet):
    supplied = nested_profile_packet(packet)
    contract = json.loads(supplied[4])
    contract["measurement_rules"]["historical-trial"]["profiles"][0].pop("hash_member")
    with pytest.raises(ValueError, match="source digests"):
        check(reviewed_contract_variant(supplied, contract))


def test_leaf_profile_cannot_accept_mapping_hash_member(packet):
    contract = json.loads(packet[4])
    contract["measurement_rules"]["historical-trial"]["profiles"][1]["hash_member"] = "sha256"
    with pytest.raises(ValueError, match="Unsupported measurement profile fields"):
        check(reviewed_contract_variant(packet, contract))


@pytest.mark.parametrize("field,value", [
    ("review_method", "Human acceptance and blind review established 15% productivity gain"),
    ("review_method", False), ("review_method", None),
    ("input_revision", "0" * 40), ("input_revision", False), ("input_revision", None),
    ("input_tree", "0" * 40), ("input_tree", False), ("input_tree", None),
])
def test_review_method_and_input_git_identity_are_frozen_by_independent_contract(packet, field, value):
    packet[0][field] = value
    with pytest.raises(ValueError, match=f"contract mismatch: {field}"):
        check(packet)


@pytest.mark.parametrize("field", ["review_method", "input_revision", "input_tree"])
def test_review_metadata_cannot_be_omitted_from_candidate_or_external_contract(packet, field):
    packet[0].pop(field)
    with pytest.raises(ValueError, match=f"contract mismatch: {field}"):
        check(packet)
    contract = json.loads(packet[4])
    contract.pop(field)
    with pytest.raises(ValueError, match=f"contract mismatch: {field}"):
        check(reviewed_contract_variant(packet, contract))


@pytest.mark.parametrize("field,value", [
    ("human_acceptance", "passed"), ("model_productivity", "15% demonstrated"),
    ("physical_blinding", True), ("runtime_equivalence", "established"),
    ("final_acceptance", True), ("new_claim", {"accepted": True}),
    ("self_authored_contract", {"accepted": True}),
])
def test_unrecognized_top_level_claim_fields_are_outside_closed_record_schema(packet, field, value):
    packet[0][field] = value
    with pytest.raises(ValueError, match="Unsupported reconciliation fields"):
        check(packet)


@pytest.mark.parametrize("field", ["review_method", "input_revision", "input_tree"])
def test_rewriting_review_metadata_contract_requires_new_controller_pin(packet, field):
    contract = json.loads(packet[4])
    packet[0][field] = "invented review identity"
    contract[field] = packet[0][field]
    with pytest.raises(ValueError, match="commitment mismatch"):
        check((*packet[:4], json.dumps(contract).encode(), packet[5]))


@pytest.mark.parametrize("value", [True, 0, None, "false"])
def test_historical_observations_cannot_claim_reexecution_or_coerce_false(packet, value):
    packet[0]["measurements"][0]["observations_reexecuted"] = value
    with pytest.raises(ValueError, match="remain unreexecuted"):
        check(packet)


@pytest.mark.parametrize("field", [
    "id", "scope", "restriction", "evidence", "producer_identity_evidence", "producer_sources",
    "applicability", "current_performance_claim", "observations_reexecuted",
])
def test_measurement_schema_requires_all_declared_fields(packet, field):
    packet[0]["measurements"][0].pop(field)
    with pytest.raises(ValueError, match="closed schema"):
        check(packet)


@pytest.mark.parametrize("field,value", [
    ("human_acceptance", "passed"), ("new_current_measurement", True),
    ("physical_blinding", True), ("runtime_equivalence", "established"),
    ("model_productivity", "15% demonstrated"), ("extra_claim", {"accepted": True}),
])
def test_measurement_schema_rejects_unsupported_claim_fields(packet, field, value):
    packet[0]["measurements"][0][field] = value
    with pytest.raises(ValueError, match="closed schema"):
        check(packet)
