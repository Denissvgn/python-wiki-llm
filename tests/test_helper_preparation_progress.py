"""Helper setup shares CLI progress contracts without changing SDK callbacks."""
from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services import helper_cache
from llm_wiki_cli.services.helper_preparation import prepare_operation_helpers
from llm_wiki_cli.services.helper_runtime import PreparedHelperHandle
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


@pytest.fixture
def preparation(tmp_path, monkeypatch):
    (tmp_path / "main.ts").write_text("export const value = 1;\n")
    snapshot = build_source_snapshot(tmp_path)
    cache = tmp_path / "cache" / "llm-wiki-extractors"
    artifact = cache / "typescript" / ("a" * 64)
    handle = PreparedHelperHandle(
        "typescript", cache, "a" * 64, artifact,
        artifact / "node_modules/ts-morph", {},
    )
    notice = "Preparing typescript helper (first use or changed profile)…"

    def ensure(*args, progress=None, **kwargs):
        assert progress is not None
        progress(notice)
        return handle

    monkeypatch.setattr(helper_cache, "ensure_helper", ensure)

    def prepare():
        return prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY)

    return prepare, notice


@pytest.mark.parametrize("mode", ["never", "always"])
def test_cli_helper_setup_respects_progress_mode_and_json_format(
    monkeypatch, capsys, preparation, mode,
):
    prepare, _ = preparation

    def run(args):
        prepare()
        print('{"result":"unchanged"}')

    monkeypatch.setattr(cli._COMMAND_MODULES["sync"], "run", run)
    monkeypatch.setattr(sys, "argv", [
        "llm-wiki", "sync", "--progress", mode, "--progress-format", "json",
    ])
    cli.main()
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"result": "unchanged"}
    if mode == "never":
        assert captured.err == ""
    else:
        events = [json.loads(line) for line in captured.err.splitlines()]
        assert all(event["schema_version"] == "llm-wiki-progress/v1" for event in events)
        assert [event["event"] for event in events
                if event["phase"] == "helper_preparation"] == ["phase_started", "phase_finished"]


def test_sdk_preparation_retains_callback_without_default_stderr(
    monkeypatch, capsys, preparation,
):
    prepare, notice = preparation
    messages = []

    def extract(*args, **kwargs):
        prepare()
        return SimpleNamespace(payload={"result": "ready"})

    monkeypatch.setattr(api.extract_cmd, "build_extract_payload", extract)
    with api.helper_preparation("auto", progress=messages.append):
        assert api.extract_source() == {"result": "ready"}
    assert messages == [notice]
    assert capsys.readouterr() == ("", "")


def test_sdk_preparation_without_progress_sink_retains_stderr_notice(
    monkeypatch, capsys, preparation,
):
    prepare, notice = preparation

    def extract(*args, **kwargs):
        prepare()
        return SimpleNamespace(payload={"result": "ready"})

    monkeypatch.setattr(api.extract_cmd, "build_extract_payload", extract)
    assert api.extract_source() == {"result": "ready"}
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "llm-wiki: " + notice + "\n"
