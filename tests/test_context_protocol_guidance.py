"""Unsupported context requests advertise every accepted protocol version."""

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


def test_cli_unsupported_protocol_returns_complete_guidance_without_a_project(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    request = tmp_path / "request.json"
    request.write_text(json.dumps(_request("llm-wiki-context/v999")), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "context", "--request", str(request)])
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["protocol"] == CONTEXT_PROTOCOL_VERSION
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_request"
    assert payload["error"]["field"] == "protocol"
    assert _advertised(payload["error"]["message"]) == list(SUPPORTED)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["request.json"]
