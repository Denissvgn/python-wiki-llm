"""Unsupported context requests advertise every accepted protocol version."""

import io
import json
import re
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import context_service as context
from llm_wiki_cli.services.contracts import (
    CONTEXT_BUDGET_PROTOCOL_VERSION,
    CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
    CONTEXT_PROTOCOL_VERSION,
)


SUPPORTED = (CONTEXT_PROTOCOL_VERSION, CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
             CONTEXT_BUDGET_PROTOCOL_VERSION)


def _request(protocol, **changes):
    return {"protocol": protocol, "budget_tokens": 1000, "format": "json",
            **({"knowledge_mode": "off"} if protocol == CONTEXT_KNOWLEDGE_PROTOCOL_VERSION else {}),
            **changes}


def _advertised(message):
    return re.findall(r"'(llm-wiki-context/v[0-9]+)'", message.split("Expected", 1)[1])


@pytest.mark.parametrize("protocol", ["llm-wiki-context/v999", None, 3, True, [], {}])
def test_unsupported_protocol_guidance_lists_only_supported_request_versions(protocol):
    with pytest.raises(context.ProtocolRequestError) as stopped:
        context._validate_protocol_request(_request(protocol))
    assert stopped.value.field == "protocol"
    assert stopped.value.protocol == CONTEXT_PROTOCOL_VERSION
    choices = _advertised(str(stopped.value))
    assert choices == list(SUPPORTED)
    for choice in choices:
        assert context._validate_protocol_request(_request(choice))["protocol"] == choice


@pytest.mark.parametrize("protocol", SUPPORTED)
def test_supported_protocols_keep_validation_and_error_identity(protocol):
    assert context._validate_protocol_request(_request(protocol))["protocol"] == protocol
    with pytest.raises(context.ProtocolRequestError) as stopped:
        context._validate_protocol_request(_request(protocol, budget_tokens=0))
    assert stopped.value.field == "budget_tokens"
    assert stopped.value.protocol == protocol


@pytest.mark.parametrize("protocol", SUPPORTED)
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("budget_mode", "estimated"),
        ("counter_id", "counter/v1"),
        ("changes", {"mode": "paths", "paths": []}),
        ("format", "packet"),
    ],
)
def test_budgeted_fields_keep_their_protocol_boundaries(protocol, field, value):
    request = _request(protocol, **{field: value})
    if protocol == CONTEXT_BUDGET_PROTOCOL_VERSION:
        normalized = context._validate_protocol_request(request)
        assert normalized["protocol"] == protocol
        assert normalized[field] == value
    else:
        with pytest.raises(context.ProtocolRequestError) as stopped:
            context._validate_protocol_request(request)
        assert stopped.value.field == field
        assert stopped.value.protocol == protocol


@pytest.mark.parametrize("source", ["file", "stdin"])
@pytest.mark.parametrize("packet", [False, True])
@pytest.mark.parametrize("existing_output", [False, True])
def test_cli_unsupported_protocol_preserves_transport_and_output_without_a_project(
    tmp_path, monkeypatch, capsys, source, packet, existing_output
):
    monkeypatch.chdir(tmp_path)
    encoded = json.dumps(_request("llm-wiki-context/v999"))
    expected_files = []
    if source == "file":
        request = tmp_path / "request.json"
        request.write_text(encoded, encoding="utf-8")
        request_arg = str(request)
        expected_files.append(request.name)
    else:
        monkeypatch.setattr(sys, "stdin", io.StringIO(encoded))
        request_arg = "-"
    output = tmp_path / "context.out"
    if existing_output:
        output.write_bytes(b"Existing output must survive rejection.\n")
        expected_files.append(output.name)
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    argv = ["llm-wiki", "context", "--request", request_arg, "--output", str(output)]
    if packet:
        argv.extend(["--format", "packet"])
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.err if packet else captured.out)
    assert payload["protocol"] == CONTEXT_PROTOCOL_VERSION
    assert payload["ok"] is False
    assert payload["error"]["field"] == "protocol"
    if packet:
        assert captured.out == ""
        assert payload["error"]["code"] == "invalid-request"
        # Packet diagnostics intentionally sanitize raw request values/messages.
        assert payload["error"]["message"] == (
            "protocol: Context request is invalid. Check the indicated field."
        )
    else:
        assert captured.err == ""
        assert payload["error"]["code"] == "invalid_request"
        assert _advertised(payload["error"]["message"]) == list(SUPPORTED)
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(expected_files)
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()} == before
