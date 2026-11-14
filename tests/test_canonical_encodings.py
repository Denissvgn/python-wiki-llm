"""Exact bytes and digests of every canonical JSON helper.

Stored artifacts and receipts persist these digests, so consolidating the
helpers must keep each encoding byte-for-byte. Four encodings exist today:
compact, compact with a trailing LF, compact ASCII-escaped, and indented.
"""

from __future__ import annotations

import hashlib

import pytest

from llm_wiki_cli.eval_lite import planner
from llm_wiki_cli.services import (
    analysis_compatibility,
    canonical_json,
    context_packet,
    documentation_queries,
    health_policy,
    knowledge_evidence,
    knowledge_graph,
    knowledge_storage,
    maintenance_shapes,
    maintenance_state,
    protected_artifacts,
    python_implementation,
    site_export,
    workflow_profile,
)
from llm_wiki_cli.services.calibration import broker, controller
from llm_wiki_cli.services.documentation_run import contracts as run_contracts

SAMPLE = {
    "zeta": [3, -0.5, 1e21, True, None],
    "alpha": {
        "ключ": "雪 ü \U0001F600",
        "q": "\"\\\n\u0007",
    },
    "Mid": 12345678901234567890,
    "empty": {},
}
DOMAIN = "llm-wiki-test/v1"

COMPACT = (
    '{"Mid":12345678901234567890,"alpha":{"q":"\\"\\\\\\n\\u0007",'
    '"ключ":"雪 ü \U0001F600"},'
    '"empty":{},"zeta":[3,-0.5,1e+21,true,null]}'
).encode("utf-8")
COMPACT_LF = COMPACT + b"\n"
COMPACT_ASCII = (
    b'{"Mid":12345678901234567890,"alpha":{"q":"\\"\\\\\\n\\u0007",'
    b'"\\u043a\\u043b\\u044e\\u0447":"\\u96ea \\u00fc \\ud83d\\ude00"},'
    b'"empty":{},"zeta":[3,-0.5,1e+21,true,null]}'
)

COMPACT_DIGEST = "sha256:87739989ef10af269ea3bd1f31456a598685b3694782e143e737be904ff4aaae"
COMPACT_LF_DIGEST = "sha256:46ea699e9615589b0d74d24d63c34991aef3351efa93ab0fca50b3408899a475"
COMPACT_ASCII_DIGEST = "sha256:f6ac9903d6b5ae21f22dfbb223889571765a15111cc0e8684f7083164f1a5a20"
INDENTED_LF_DIGEST = "sha256:5fd50dc92a6d0ceb9c15cf6e8484b8a4ba230f2c8d315fbd827803fc182446d5"
CONTENT_ID = "sha256:d7f9ee952a6314e1692c8886ca29b6c6681ab6f7a8dc712a4cc95d9a4e55145d"
DOMAIN_HASH = "sha256:9181a5ea88c083dc13d51a31f4b429904e1ddf626258283d509aae34eab76325"


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_golden_bytes_match_golden_digests() -> None:
    assert _sha256(COMPACT) == COMPACT_DIGEST
    assert _sha256(COMPACT_LF) == COMPACT_LF_DIGEST
    assert _sha256(COMPACT_ASCII) == COMPACT_ASCII_DIGEST


@pytest.mark.parametrize(
    "encode",
    [
        knowledge_evidence.canonical_json_bytes,
        lambda value: knowledge_evidence.canonical_json_text(value).encode("utf-8"),
        site_export._canonical_json_bytes,
        planner._canonical_json_bytes,
        lambda value: documentation_queries._canonical_json(value).encode("utf-8"),
        lambda value: knowledge_graph._canonical_json(value).encode("utf-8"),
    ],
    ids=[
        "knowledge_evidence.canonical_json_bytes",
        "knowledge_evidence.canonical_json_text",
        "site_export._canonical_json_bytes",
        "eval_lite.planner._canonical_json_bytes",
        "documentation_queries._canonical_json",
        "knowledge_graph._canonical_json",
    ],
)
def test_compact_encoders(encode) -> None:
    assert encode(SAMPLE) == COMPACT


@pytest.mark.parametrize(
    "encode",
    [
        knowledge_storage.canonical_bytes,
        python_implementation.canonical_bytes,
        workflow_profile.canonical_json,
        # Same name as knowledge_evidence.canonical_json_bytes, different bytes.
        protected_artifacts.canonical_json_bytes,
        broker.canonical_result_json_bytes,
        lambda value: b"".join(canonical_json.canonical_chunks(value)),
        lambda value: b"".join(canonical_json.canonical_chunks(value, chunk_bytes=64)),
    ],
    ids=[
        "knowledge_storage.canonical_bytes",
        "python_implementation.canonical_bytes",
        "workflow_profile.canonical_json",
        "protected_artifacts.canonical_json_bytes",
        "calibration.broker.canonical_result_json_bytes",
        "canonical_json.canonical_chunks",
        "canonical_json.canonical_chunks-streamed",
    ],
)
def test_compact_lf_encoders(encode) -> None:
    assert encode(SAMPLE) == COMPACT_LF


def test_indented_encoder() -> None:
    encoded = knowledge_evidence.formatted_json_bytes(SAMPLE)

    assert encoded.startswith(b'{\n  "Mid": 12345678901234567890,\n')
    assert _sha256(encoded) == INDENTED_LF_DIGEST


@pytest.mark.parametrize(
    ("compute", "expected"),
    [
        (knowledge_evidence.hash_json, COMPACT_DIGEST),
        (controller._sha256_json, COMPACT_LF_DIGEST),
        (lambda value: knowledge_storage.digest(knowledge_storage.canonical_bytes(value)), COMPACT_LF_DIGEST),
        (knowledge_storage.logical_digest, COMPACT_LF_DIGEST),
        (maintenance_state.canonical_hash, COMPACT_LF_DIGEST),
        (maintenance_shapes.canonical_hash, COMPACT_LF_DIGEST),
        (python_implementation._digest, COMPACT_LF_DIGEST),
        (analysis_compatibility.digest, COMPACT_ASCII_DIGEST),
        (run_contracts._sha256_json, COMPACT_ASCII_DIGEST),
        (lambda value: workflow_profile.content_id(DOMAIN, value), CONTENT_ID),
        (lambda value: context_packet._domain_hash(DOMAIN, value), DOMAIN_HASH),
    ],
    ids=[
        "knowledge_evidence.hash_json",
        "calibration.controller._sha256_json",
        "knowledge_storage.digest",
        "knowledge_storage.logical_digest",
        "maintenance_state.canonical_hash",
        "maintenance_shapes.canonical_hash",
        "python_implementation._digest",
        "analysis_compatibility.digest",
        "documentation_run.contracts._sha256_json",
        "workflow_profile.content_id",
        "context_packet._domain_hash",
    ],
)
def test_json_digests(compute, expected) -> None:
    assert compute(SAMPLE) == expected


def test_raw_byte_digests() -> None:
    assert knowledge_evidence.sha256_bytes(COMPACT) == COMPACT_DIGEST
    assert knowledge_storage.digest(COMPACT_LF) == COMPACT_LF_DIGEST
    assert health_policy.digest(COMPACT_ASCII) == COMPACT_ASCII_DIGEST


NAN_SAMPLE = {"value": float("nan")}


@pytest.mark.parametrize(
    "encode",
    [
        knowledge_evidence.canonical_json_bytes,
        knowledge_evidence.formatted_json_bytes,
        knowledge_storage.canonical_bytes,
        python_implementation.canonical_bytes,
        workflow_profile.canonical_json,
        planner._canonical_json_bytes,
        broker.canonical_result_json_bytes,
        analysis_compatibility.digest,
        lambda value: b"".join(canonical_json.canonical_chunks(value)),
    ],
    ids=[
        "knowledge_evidence.canonical_json_bytes",
        "knowledge_evidence.formatted_json_bytes",
        "knowledge_storage.canonical_bytes",
        "python_implementation.canonical_bytes",
        "workflow_profile.canonical_json",
        "eval_lite.planner._canonical_json_bytes",
        "calibration.broker.canonical_result_json_bytes",
        "analysis_compatibility.digest",
        "canonical_json.canonical_chunks",
    ],
)
def test_strict_encoders_reject_non_finite_numbers(encode) -> None:
    with pytest.raises(ValueError):
        encode(NAN_SAMPLE)


def test_protected_artifact_encoder_rejects_non_finite_numbers() -> None:
    with pytest.raises(protected_artifacts.ProtectedArtifactIntegrityError):
        protected_artifacts.canonical_json_bytes(NAN_SAMPLE)


@pytest.mark.parametrize(
    ("compute", "expected"),
    [
        (site_export._canonical_json_bytes, b'{"value":NaN}'),
        (lambda value: documentation_queries._canonical_json(value).encode("utf-8"), b'{"value":NaN}'),
        (run_contracts._sha256_json, _sha256(b'{"value":NaN}')),
    ],
    ids=[
        "site_export._canonical_json_bytes",
        "documentation_queries._canonical_json",
        "documentation_run.contracts._sha256_json",
    ],
)
def test_lenient_encoders_accept_non_finite_numbers(compute, expected) -> None:
    assert compute(NAN_SAMPLE) == expected
