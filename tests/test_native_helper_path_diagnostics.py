"""Native parser attribution, negative authority and committed-cache boundaries."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.extractors import native_diagnostics
from llm_wiki_cli.extractors.go_extractor import GoExtractionRequest, GoExtractor
from llm_wiki_cli.extractors.haskell_extractor import (
    HaskellExtractionRequest,
    HaskellExtractor,
)
from llm_wiki_cli.extractors.rust_extractor import RustExtractionRequest, RustExtractor
from llm_wiki_cli.services import mcp_server, sync_analysis_cache
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_entity_retirement import _snapshot

ROOT = Path(__file__).resolve().parents[1]
HELPERS = os.environ.get("LLM_WIKI_CACHE_DIR", str(ROOT / ".git/llm-wiki-extractors"))
PROVIDERS = {
    "go": (
        GoExtractor,
        GoExtractionRequest,
        ".go",
        "package pilot\ntype Draft struct {}\n",
        "package\n",
        "package pilot\n",
    ),
    "rust": (
        RustExtractor,
        RustExtractionRequest,
        ".rs",
        "pub struct Draft;\n",
        "pub struct {\n",
        "// empty\n",
    ),
    "haskell": (
        HaskellExtractor,
        HaskellExtractionRequest,
        ".hs",
        "module Pilot where\ndata Draft = Draft\n",
        "module Pilot where\ndata Draft =\n",
        "module Empty where\n",
    ),
}


@pytest.fixture(params=PROVIDERS)
def provider(request, require_prepared_diagnostics_helper):
    language = request.param
    require_prepared_diagnostics_helper(language)
    return language, PROVIDERS[language]


def envelope(language, paths):
    return json.dumps(
        {
            "schema_version": "llm-wiki-native-diagnostics/v1",
            "language": language,
            "inventory": {path: {"classes": [], "functions": []} for path in paths},
            "outcomes": {
                path: {
                    "extraction_state": "extracted",
                    "reason": "inventory-entry",
                    "failure_scope": "file",
                }
                for path in paths
            },
        }
    )


def test_real_selected_success_empty_and_syntax_are_distinct(tmp_path, provider):
    language, (cls, request, suffix, good, bad, empty) = provider
    names = ["good" + suffix, "bad" + suffix, "empty, named" + suffix]
    for name, body in zip(names, (good, bad, empty)):
        (tmp_path / name).write_text(body)
    (tmp_path / ("unselected" + suffix)).write_text(bad)
    extractor = cls()
    result = extractor.extract(
        request(
            str(tmp_path),
            deep=True,
            source_files=names,
            diagnostics=True,
            helper_cache_dir=HELPERS,
        )
    )
    assert set(result) == {names[0], names[2]}
    assert result[names[0]]["classes"][0]["name"] == "Draft"
    assert result[names[2]]["classes"] == result[names[2]]["functions"] == []
    assert extractor.last_path_outcomes == {
        names[0]: {
            "extraction_state": "extracted",
            "reason": "inventory-entry",
            "failure_scope": "file",
        },
        names[1]: {
            "extraction_state": "failed",
            "reason": "syntax-error",
            "failure_scope": "file",
        },
        names[2]: {
            "extraction_state": "extracted",
            "reason": "inventory-entry",
            "failure_scope": "file",
        },
    }
    assert extractor.last_error is None
    ordinary = extractor.extract(
        request(
            str(tmp_path), deep=True, source_files=[names[0]], helper_cache_dir=HELPERS
        )
    )
    assert ordinary[names[0]] == result[names[0]]
    assert extractor.last_path_outcomes == {}
    assert all(entry["language"] == language for entry in result.values())


def test_real_read_errors_are_file_scoped_not_empty_or_batch(tmp_path, provider):
    _, (cls, request, suffix, good, _, _) = provider
    names = ["good" + suffix, "missing" + suffix, "directory" + suffix]
    (tmp_path / names[0]).write_text(good)
    (tmp_path / names[2]).mkdir()
    extractor = cls()
    result = extractor.extract(
        request(
            str(tmp_path),
            source_files=names,
            diagnostics=True,
            helper_cache_dir=HELPERS,
        )
    )
    assert set(result) == {names[0]}
    for path in names[1:]:
        assert extractor.last_path_outcomes[path] == {
            "extraction_state": "failed",
            "reason": "read-error",
            "failure_scope": "file",
        }
    assert extractor.last_error is None


@pytest.mark.parametrize("language", PROVIDERS)
def test_missing_helper_reports_unavailable_owned_scope(
    tmp_path, monkeypatch, language
):
    cls, request, suffix, good, _, _ = PROVIDERS[language]
    path = "good" + suffix
    (tmp_path / path).write_text(good)
    monkeypatch.setattr(
        f"llm_wiki_cli.extractors.{language}_extractor.get_prepared_binary",
        lambda *a: None,
    )
    extractor = cls()
    assert (
        extractor.extract(request(str(tmp_path), source_files=[path], diagnostics=True))
        == {}
    )
    assert extractor.last_path_outcomes == {
        path: {
            "extraction_state": "unavailable",
            "reason": "helper-unavailable",
            "failure_scope": "extractor-batch",
        }
    }


@pytest.mark.parametrize("language", PROVIDERS)
@pytest.mark.parametrize("failure", ["exit", "timeout", "missing-executable"])
def test_process_failure_never_becomes_file_syntax_authority(
    tmp_path, monkeypatch, language, failure
):
    cls, request, suffix, _, _, _ = PROVIDERS[language]
    path = "selected" + suffix
    extractor = cls()
    monkeypatch.setattr(extractor, "_prepared_helper", lambda *a: Path("helper"))

    def fail(*args, **kwargs):
        if failure == "exit":
            raise subprocess.CalledProcessError(1, "helper", stderr="syntax-error")
        if failure == "timeout":
            raise subprocess.TimeoutExpired("helper", 1)
        raise FileNotFoundError("helper")

    monkeypatch.setattr(subprocess, "run", fail)
    assert (
        extractor.extract(request(str(tmp_path), source_files=[path], diagnostics=True))
        == {}
    )
    assert extractor.last_path_outcomes == {
        path: {
            "extraction_state": "failed",
            "reason": "extractor-batch-failed",
            "failure_scope": "extractor-batch",
        }
    }


@pytest.mark.parametrize("language", PROVIDERS)
@pytest.mark.parametrize(
    "fault",
    [
        "legacy",
        "wrong-language",
        "extra-path",
        "failed-record",
        "missing-record",
        "bad-state",
        "missing-scope",
        "duplicate",
        "malformed",
    ],
)
def test_invalid_protocol_cannot_supply_inventory(
    tmp_path, monkeypatch, language, fault
):
    cls, request, suffix, _, _, _ = PROVIDERS[language]
    path = "good" + suffix
    raw = json.loads(envelope(language, [path]))
    if fault == "legacy":
        raw = raw["inventory"]
    elif fault == "wrong-language":
        raw["language"] = "python"
    elif fault == "extra-path":
        raw["outcomes"]["unselected" + suffix] = raw["outcomes"][path]
    elif fault == "failed-record":
        raw["outcomes"][path].update(extraction_state="failed", reason="syntax-error")
    elif fault == "missing-record":
        raw["inventory"] = {}
    elif fault == "bad-state":
        raw["outcomes"][path]["reason"] = "no-documentable-content"
    elif fault == "missing-scope":
        raw["outcomes"][path].pop("failure_scope")
    output = json.dumps(raw)
    if fault == "duplicate":
        output = output[:-1] + ',"inventory":{}}'
    elif fault == "malformed":
        output = "{"
    extractor = cls()
    monkeypatch.setattr(extractor, "_prepared_helper", lambda *a: Path("helper"))
    monkeypatch.setattr(
        extractor,
        "_run_helper",
        lambda *a: subprocess.CompletedProcess(
            [], 0, output, "misleading syntax-error stderr"
        ),
    )
    assert (
        extractor.extract(request(str(tmp_path), source_files=[path], diagnostics=True))
        == {}
    )
    assert extractor.last_path_outcomes == {
        path: {
            "extraction_state": "failed",
            "reason": "invalid-helper-output",
            "failure_scope": "extractor-batch",
        }
    }


@pytest.mark.parametrize("language", PROVIDERS)
def test_omitted_outcome_stays_unavailable_without_guessed_model(language):
    raw = json.loads(envelope(language, []))
    records, outcomes = native_diagnostics.decode_diagnostics(
        json.dumps(raw), ["selected"], language
    )
    assert records == {}
    assert outcomes == {
        "selected": {
            "extraction_state": "unavailable",
            "reason": "outcome-not-reported",
        }
    }


@pytest.mark.parametrize("language", PROVIDERS)
def test_completed_failed_and_unattempted_chunks_remain_separate(
    tmp_path, monkeypatch, language
):
    cls, _, suffix, good, _, _ = PROVIDERS[language]
    names = [prefix + suffix for prefix in ("a", "b", "c")]
    for path in names:
        (tmp_path / path).write_text(good)
    monkeypatch.setattr(
        native_diagnostics,
        "chunk_source_files_for_cli",
        lambda paths: [[path] for path in paths],
    )
    monkeypatch.setattr(cls, "_prepared_helper", lambda *a: Path("helper"))
    calls = []

    def run(self, command, helper):
        calls.append(command)
        if len(calls) == 1:
            return subprocess.CompletedProcess([], 0, envelope(language, names[:1]), "")
        self.last_error = "independent batch failure"
        return None

    monkeypatch.setattr(cls, "_run_helper", run)
    result = get_inventory_result(str(tmp_path), deep=True, capture_path_outcomes=True)
    assert result.failed
    assert set(result.inventory) == {names[0]}
    assert result.path_outcomes[names[0]]["extraction_state"] == "extracted"
    assert result.path_outcomes[names[1]] == {
        "extraction_state": "failed",
        "reason": "extractor-batch-failed",
        "failure_scope": "extractor-batch",
    }
    assert result.path_outcomes[names[2]] == {
        "extraction_state": "not-attempted",
        "reason": "extractor-batch-aborted",
    }
    assert len(calls) == 2


def test_full_snapshot_selected_retry_never_reports_unrequested_paths(
    tmp_path, provider
):
    _, (_, _, suffix, good, bad, _) = provider
    selected, outside = "selected" + suffix, "outside" + suffix
    (tmp_path / selected).write_text(good)
    (tmp_path / outside).write_text(bad)
    snapshot = build_source_snapshot(tmp_path)
    result = get_inventory_result(
        str(tmp_path),
        only_files=[selected],
        source_snapshot=snapshot,
        capture_path_outcomes=True,
        helper_cache_dir=HELPERS,
    )
    assert set(result.inventory) == set(result.path_outcomes) == {selected}


def test_public_impact_api_cli_mcp_preserve_native_failure_scope(
    tmp_path, monkeypatch, provider
):
    _, (_, _, suffix, good, bad, _) = provider
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", HELPERS)
    Path("src").mkdir()
    Path("src/anchor.py").write_text("class Anchor: pass\n")
    api.bootstrap_wiki("src", "wiki", helper_cache_dir=HELPERS)
    names = ["good" + suffix, "bad" + suffix]
    for path, body in zip(names, (good, bad)):
        Path("src", path).write_text(body)
    request = {
        "operation": "impact",
        "paths": names,
        "source_policy": "discovery",
        "limit": 4,
    }
    result = api.query_documentation(request, src_dir="src", wiki_dir="wiki")
    rows = {row["path"]: row for row in result["matches"]}
    assert rows[names[0]]["present"] is True
    assert rows[names[1]]["present"] is False
    assert rows[names[1]]["reason"] == "syntax-error"
    assert rows[names[1]]["failure_scope"] == "file"
    assert (
        mcp_server.McpWikiService(src_dir="src", wiki_dir="wiki").query_documentation(
            request
        )
        == result
    )
    cli = subprocess.run(
        [
            sys.executable,
            "-m",
            "llm_wiki_cli.cli",
            "query",
            "--request",
            "-",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
        ],
        input=json.dumps(request),
        capture_output=True,
        text=True,
    )
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout) == result


def test_partial_syntax_failure_blocks_retirement_and_cache_authority(
    tmp_path, monkeypatch, provider
):
    _, (_, _, suffix, good, bad, empty) = provider
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    path = Path("src", "model" + suffix)
    path.write_text(good)
    api.bootstrap_wiki("src", "wiki", helper_cache_dir=HELPERS)
    module = Path("wiki/modules/model.md")
    prefix, description = module.read_text().split("## Description\n", 1)
    _, tail = description.split("\n## ", 1)
    module.write_text(
        prefix + "## Description\n\nAuthored module purpose.\n\n## " + tail
    )
    options = SimpleNamespace(
        src_dir="src",
        wiki_dir="wiki",
        helper_cache_dir=HELPERS,
        cache_dir="cache",
        no_plugins=True,
    )
    sync_cmd.run(options)
    cache = Path("cache", sync_analysis_cache.FILENAME)
    before, cached = _snapshot(Path("wiki")), cache.read_bytes()
    with monkeypatch.context() as context:
        context.setattr(
            sync_cmd,
            "_extract_current_inventory",
            lambda *a, **kw: pytest.fail(
                "matching committed source/provider inputs must reuse analysis"
            ),
        )
        sync_cmd.run(options)
    assert _snapshot(Path("wiki")) == before
    assert cache.read_bytes() == cached
    Path("src", "other" + suffix).write_text(empty)
    path.write_text(bad)
    with pytest.raises(SystemExit):
        sync_cmd.run(options)
    assert _snapshot(Path("wiki")) == before
    assert cache.read_bytes() == cached
    assert not SyncManifest.load(Path("wiki")).generation_inputs.get(
        "entity_retirement"
    )


def test_missing_cached_qualification_rebuilds_selected_native_paths(
    tmp_path, monkeypatch, provider
):
    _, (_, _, suffix, good, bad, _) = provider
    path = "model" + suffix
    (tmp_path / path).write_text(good)
    before = get_inventory_result(
        str(tmp_path), deep=True, capture_path_outcomes=True, helper_cache_dir=HELPERS
    )
    snapshot = before.source_snapshot
    manifest = SyncManifest.build_from_inventory(
        before.inventory, str(tmp_path), {}, {path: "model"}
    )
    # A stale sparse cached inventory carries no success authority; only a live
    # exact retry can reconstruct the physically surviving selected module.
    unqualified = replace(before, inventory={}, path_outcomes={})
    options = SimpleNamespace(
        src_dir=str(tmp_path),
        helper_cache_dir=HELPERS,
        include_tests=(),
        include_plugins=False,
        parallel_jobs=1,
    )
    rebuilt = sync_cmd._qualify_surviving_module_inventory(
        options, snapshot, manifest, unqualified
    )
    assert set(rebuilt.inventory) == {path}
    assert rebuilt.path_outcomes[path]["reason"] == "inventory-entry"
    (tmp_path / path).write_text(bad)
    from llm_wiki_cli.services.source_retirement import SourceRetirementError

    with pytest.raises(SourceRetirementError, match="syntax-error"):
        sync_cmd._qualify_surviving_module_inventory(
            options, build_source_snapshot(tmp_path), manifest, unqualified
        )
