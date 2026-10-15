"""Reject incomplete or mislabeled installed state receipts before release admission."""

from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from tests.release_artifact_smoke import SmokeError, _provider_state_result


def receipt(mode="mcp"):
    states = {
        "valid": "ready",
        "empty-selection": "ready",
        "absent": "workspace-state-error",
        "surface-only": "absent",
        "declared-missing": "degraded",
        "malformed": "degraded",
        "unsupported": "unsupported",
        "mixed": "degraded",
        "corrupt-surface": "artifact-integrity-error",
        **{f"legacy-manifest-v{v}": "absent" for v in (1, 2, 3, 4)},
    }
    fixtures = Path(__file__).parent / "fixtures"
    return {
        "status": "pass",
        "mode": mode,
        "version": "2.5.0",
        "archive_sha256": "a" * 64,
        "states": [
            {
                "state": name,
                "availability": availability,
                "counts": {"modeled": 2} if availability == "ready" else None,
                "found": name == "valid",
                "api_cli_parity": True,
                "read_only": True,
                "sdk": [
                    {"transport": t, "parity": True, "safe_error": True}
                    for t in ("stdio", "http")
                ]
                if mode == "mcp"
                else [],
            }
            for name, availability in states.items()
        ],
        "goldens": [
            {
                "name": name,
                "sha256": hashlib.sha256((fixtures / name).read_bytes()).hexdigest(),
                "schema": "llm-wiki-qualified-context-packet/v"
                + ("1" if "-v1" in name else "2"),
            }
            for name in (
                "context-packet-v1.json",
                "context-packet-v2.json",
                "context-packet-v1-pre-bindings.json",
                "context-packet-v2-pre-bindings.json",
            )
        ],
        "future_packet_rejected": True,
        "legacy_upgrade": {
            "before": "absent",
            "after": "ready",
            "source_unchanged": True,
            "authored_preserved": True,
        },
    }


def test_complete_base_and_real_transport_receipts_share_semantic_result():
    assert _provider_state_result(
        receipt("base"), mode="base", version="2.5.0", digest="a" * 64
    ) == _provider_state_result(receipt(), mode="mcp", version="2.5.0", digest="a" * 64)


@pytest.mark.parametrize(
    "fault",
    [
        "archive",
        "version",
        "omitted",
        "duplicate",
        "coerced",
        "fabricated-counts",
        "empty-denominator",
        "empty-found",
        "not-read-only",
        "no-cli",
        "no-http",
        "bad-sdk",
        "wrong-golden",
        "missing-golden",
        "future-accepted",
        "lost-prose",
    ],
)
def test_pass_flag_cannot_hide_missing_or_incorrect_obligations(fault):
    value = deepcopy(receipt())
    if fault == "archive":
        value["archive_sha256"] = "b" * 64
    elif fault == "version":
        value["version"] = "2.1.0"
    elif fault == "omitted":
        value["states"].pop()
    elif fault == "duplicate":
        value["states"][-1] = value["states"][0]
    elif fault == "coerced":
        value["states"][3]["availability"] = "ready"
    elif fault == "fabricated-counts":
        value["states"][3]["counts"] = {"modeled": 0}
    elif fault == "empty-denominator":
        value["states"][1]["counts"] = {"modeled": 0}
    elif fault == "empty-found":
        value["states"][1]["found"] = True
    elif fault == "not-read-only":
        value["states"][0]["read_only"] = False
    elif fault == "no-cli":
        value["states"][0]["api_cli_parity"] = False
    elif fault == "no-http":
        value["states"][0]["sdk"].pop()
    elif fault == "bad-sdk":
        value["states"][0]["sdk"][0]["parity"] = False
    elif fault == "wrong-golden":
        value["goldens"][0]["sha256"] = "f" * 64
    elif fault == "missing-golden":
        value["goldens"].pop()
    elif fault == "future-accepted":
        value["future_packet_rejected"] = False
    elif fault == "lost-prose":
        value["legacy_upgrade"]["authored_preserved"] = False
    with pytest.raises(SmokeError):
        _provider_state_result(value, mode="mcp", version="2.5.0", digest="a" * 64)
