"""Explicit classification coverage preserves frozen receipt semantics."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from llm_wiki_cli.services import context_packet as packets, context_service
from llm_wiki_cli.services import packet_field_policy as policy


FIXTURES = Path(__file__).parent / "fixtures"


def _body(payload):
    return {key: value for key, value in payload.items() if key not in {"schema_version", "packet_id", "path_policy"}}


@pytest.mark.parametrize("version", [1, 2])
def test_policy_enumerates_core_fields_and_dynamic_key_spaces(version):
    root = policy.POLICIES[version]
    assert set(root.fields) == packets._PACKET_TOP_LEVEL_FIELDS
    request_keys = context_service._V1_REQUEST_KEYS if version == 1 else context_service._V2_REQUEST_KEYS
    assert set(root.fields["request"].fields) == request_keys
    assert set(policy.FILTERS.fields) == context_service._FILTER_KEYS
    response = root.fields["response"]
    for name in ("files", "downgraded_files", "source_priorities"):
        assert response.fields[name].key_policy == "repository-relative-path"
    entries = policy.field_policy_manifest()["versions"][f"llm-wiki-qualified-context-packet/v{version}"]
    assert len({entry["pointer"] for entry in entries}) == len(entries)
    assert all(entry["string_class"] in packets._PATH_COUNT_KEYS for entry in entries)
    assert all(entry.get("reason") for entry in entries if entry["kind"] == "open-json")
    with pytest.raises(TypeError):
        # Deliberately attempt a mutation to check runtime immutability.
        root.fields["new_field"] = policy.SCALAR  # pyright: ignore[reportIndexIssue]


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("suffix", ["", "-pre-bindings"])
def test_declared_policy_preserves_existing_packet_receipts(version, suffix):
    raw = (FIXTURES / f"context-packet-v{version}{suffix}.json").read_bytes()
    payload = json.loads(raw)
    policy.validate_field_coverage(payload)
    assert packets._path_policy_receipt(_body(payload)) == payload["path_policy"]
    assert packets.validate_context_packet(raw).packet.to_bytes() == raw


@pytest.mark.parametrize("location", [(), ("basis", "generator"), ("request", "filters"), ("response",)])
@pytest.mark.parametrize("value", ["/synthetic/private/root", False])
def test_unclassified_fixed_fields_fail_before_a_receipt_can_claim_passed(location, value):
    body = _body(json.loads((FIXTURES / "context-packet-v1.json").read_bytes()))
    target = body
    for part in location:
        target = target[part]
    target["brand_new_field"] = value
    with pytest.raises(packets.ContextPacketPathPolicyError, match="classification"):
        packets._path_policy_receipt(body)


def test_inventory_delegation_preserves_benign_text_and_enforces_structural_paths():
    body = _body(json.loads((FIXTURES / "context-packet-v1.json").read_bytes()))
    inventory = next(iter(body["response"]["files"].values()))
    inventory["additive_metadata"] = {"note": "[Route](/api/v1), 8 / 2, /synthetic/source/literal"}
    assert packets._path_policy_receipt(body)["final_scan"] == "passed"
    malicious = deepcopy(body)
    next(iter(malicious["response"]["files"].values()))["additive_metadata"]["source_path"] = "/synthetic/private/root"
    with pytest.raises(packets.ContextPacketPathPolicyError, match="repository-relative"):
        packets._path_policy_receipt(malicious)
