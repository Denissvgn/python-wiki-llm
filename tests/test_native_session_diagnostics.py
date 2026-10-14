"""Native failure attribution must never become an acceptance fallback."""

import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

from tests.test_native_published_artifacts import probe


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("native_session_diagnostics", ROOT / "release/native_session_diagnostics.py")
assert spec and spec.loader
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def test_fixture_preparation_requires_one_exact_boundary(tmp_path):
    path = tmp_path / "fixture.py"
    prefix = "value = 1\n\n"
    suffix = "async def transport(transport_name):\n    raise RuntimeError('not preparation')\n"
    path.write_text(prefix + suffix)
    assert worker.preparation_source(path) == prefix
    for text in (prefix, prefix + suffix + suffix):
        path.write_text(text)
        with pytest.raises(ValueError, match="boundary"):
            worker.preparation_source(path)


def test_server_observer_preserves_original_return_and_captures_completion(tmp_path, monkeypatch):
    from llm_wiki_cli.services.mcp_server import McpWikiService
    result = SimpleNamespace(metadata=lambda: {"state": "full"})
    calls = []
    def original(self, *args, **kwargs):
        calls.append((args, kwargs))
        return result
    monkeypatch.setattr(McpWikiService, "read_context_session", original)
    monkeypatch.setattr(worker.faulthandler, "dump_traceback_later", lambda *args, **kwargs: None)
    namespace = {}
    exec(compile(worker.server_observer(tmp_path), "observer", "exec"), namespace)
    try:
        owner = SimpleNamespace(src_dir="src", wiki_dir="wiki", comparison_policy="auto")
        assert namespace["_observed"](owner, "handle", request={"frozen": True}) is result
        assert calls == [(("handle",), {"request": {"frozen": True}})]
        record = json.loads((tmp_path / "server-read-1.json").read_text())
        assert record["status"] == "complete" and record["release_acceptance"] is False
        assert record["metadata"] == {"state": "full"}
        assert (tmp_path / "server-read-1.pstats").is_file()
    finally:
        namespace["_stack"].close()


@pytest.mark.parametrize("destination", ["harness", "provider", "caller"])
def test_diagnostic_output_cannot_touch_protected_or_caller_roots(tmp_path, monkeypatch, destination):
    harness, work = tmp_path / "harness", tmp_path / "work"
    prefix = tmp_path / "provider"
    monkeypatch.setattr(worker.sys, "prefix", str(prefix))
    output = {"harness": harness / "out", "provider": prefix / "out", "caller": work / "out"}[destination]
    with pytest.raises(ValueError, match="separate|outside"):
        worker.require_roots(harness, work, output)
    assert not work.exists() and not output.exists()


def test_diagnostic_refuses_existing_caller_and_output(tmp_path):
    harness, work, output = [tmp_path / name for name in ("harness", "work", "output")]
    work.mkdir()
    with pytest.raises(ValueError, match="caller must be fresh"):
        worker.require_roots(harness, work, output)
    work.rmdir()
    output.mkdir()
    (output / "sentinel").write_text("keep")
    with pytest.raises(ValueError, match="output must be fresh"):
        worker.require_roots(harness, work, output)
    assert (output / "sentinel").read_text() == "keep"


@pytest.mark.parametrize("head,dirty", [("a" * 40, b""), ("b" * 40, b" M tracked.py")])
def test_harness_identity_or_mutation_cannot_execute_diagnostic(tmp_path, monkeypatch, head, dirty):
    def git(command, **options):
        assert options["timeout"] == 5
        return head.encode() if command[-1] == "HEAD" else dirty
    monkeypatch.setattr(worker.subprocess, "check_output", git)
    with pytest.raises(ValueError, match="clean pinned"):
        worker.require_harness(tmp_path, "b" * 40)


@pytest.mark.parametrize("change", ["digest", "version", "source-install", "module-escape"])
def test_diagnostic_rejects_wrong_archive_or_provider_origin(tmp_path, monkeypatch, change):
    from llm_wiki_cli import api
    prefix = tmp_path / "consumer/.venv"
    module = prefix / "llm_wiki_cli/api.py"
    module.parent.mkdir(parents=True)
    module.write_text("# independent installed module sentinel\n")
    direct = {"url": "file:///published.whl", "archive_info": {"hashes": {"sha256": "a" * 64}}}
    version = "2.5.0"
    if change == "digest":
        direct["archive_info"]["hashes"]["sha256"] = "b" * 64
    elif change == "version":
        version = "2.6.0"
    elif change == "source-install":
        direct = {"url": "file:///provider-source", "dir_info": {}}
    else:
        module = tmp_path / "outside-api.py"
        module.write_text("# outside module\n")
    monkeypatch.setattr(api, "__file__", str(module))
    monkeypatch.setattr(worker.sys, "prefix", str(prefix))
    monkeypatch.setattr(worker, "distribution", lambda *args: SimpleNamespace(
        version=version, read_text=lambda *args: json.dumps(direct)))
    with pytest.raises(ValueError, match="original pinned installed"):
        worker.installed_origin("2.5.0", "a" * 64)


@pytest.mark.parametrize("warm,valid", [(False, True), (True, True), (False, False), (True, False)])
def test_each_read_records_original_outcome_and_profile(tmp_path, warm, valid):
    result = SimpleNamespace(context=SimpleNamespace(rendered="canonical" if valid else "wrong"),
                             state="unchanged" if valid else "full", result_id="expected",
                             metadata=lambda: {"work": {"producer_files": 750}})
    session = SimpleNamespace(read=lambda *args, **options: result)
    record = {"phases": []}
    saved = []
    kwargs = {"if_result_id": "expected"} if warm else {}
    def validate(text, request, **options):
        assert text == "canonical" and request == {"scope": "frozen"}
    if valid:
        assert worker.profile_read("read", session, {"scope": "frozen"}, "canonical", validate,
            None, record, lambda: saved.append(json.dumps(record)), tmp_path, **kwargs) == "expected"
    else:
        with pytest.raises(ValueError, match="differs|warm read"):
            worker.profile_read("read", session, {"scope": "frozen"}, "canonical", validate,
                None, record, lambda: saved.append(json.dumps(record)), tmp_path, **kwargs)
    phase = record["phases"][0]
    assert len(saved) == 2 and phase["seconds"] >= 0 and phase["profile"]
    assert phase["status"] == ("complete" if valid else "failed")
    assert (tmp_path / "read.pstats").is_file()


@pytest.mark.parametrize("attempt", [{"status": "timeout"}, {"seconds": 1500.01}])
def test_diagnostic_cannot_extend_exhausted_acceptance_budget(tmp_path, attempt):
    record: dict[str, Any] = {"commands": [attempt]}
    def forbidden(*args, **options):
        pytest.fail("diagnostic extended exhausted owner budget")
    probe.diagnose_failed_harness(SimpleNamespace(output=tmp_path), record, forbidden, lambda: None, {})
    assert record["diagnostic"]["status"] == "unavailable"
    assert record["diagnostic"]["release_acceptance"] is False


@pytest.mark.parametrize("diagnostic_exit", [0, 2])
@pytest.mark.parametrize("malformed_receipt", [False, True])
def test_failed_acceptance_retains_failure_after_diagnostic(tmp_path, monkeypatch, diagnostic_exit, malformed_receipt):
    import hashlib
    monkeypatch.setattr(probe.sys, "prefix", str(tmp_path / "controller/.venv"))
    monkeypatch.setattr(probe, "is_native_windows", lambda: True)
    monkeypatch.setattr(probe.platform, "platform", lambda: "controlled-unit-fixture")
    monkeypatch.setattr(probe.platform, "machine", lambda: "controlled-unit-fixture")
    artifacts, work, output = [tmp_path / name for name in ("archives", "work", "evidence")]
    hashes = {kind: hashlib.sha256(kind.encode()).hexdigest() for kind in ("wheel", "sdist")}
    calls = []
    def controlled(command, **options):
        calls.append(command)
        if command[0] == "git":
            raw = b"b" * 40 if command[-1] == "HEAD" else b""
            code = 0
        elif command[:3] == ["gh", "release", "download"]:
            for kind, name in probe.artifact_names("2.5.0").items():
                (artifacts / name).write_bytes(kind.encode())
            raw, code = b"", 0
        elif command[2].endswith("run_provider_artifact_checks.py"):
            assert options["timeout"] == 1800
            python = work / "wheel-mcp/.venv/Scripts/python.exe"
            python.parent.mkdir(parents=True)
            python.write_bytes(b"unit interpreter placeholder")
            receipt = ["unexpected producer metadata"] if malformed_receipt else [{"label": "wheel-smoke", "exit_code": 2}]
            (output / "commands.json").write_text(json.dumps(receipt))
            raw, code = b"original MCP failure", 1
        else:
            assert command[2].endswith("native_session_diagnostics.py")
            assert options["timeout"] == 300
            assert options["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
            assert "GH_TOKEN" not in options["env"] and "GITHUB_TOKEN" not in options["env"]
            assert command[command.index("--harness-sha") + 1] == "b" * 40
            assert command[command.index("--archive-sha256") + 1] == hashes["wheel"]
            raw, code = b"diagnostic output", diagnostic_exit
        return subprocess.CompletedProcess(command, code, raw, b"")
    monkeypatch.setattr(probe.subprocess, "run", controlled)
    args = ["--repository", "Denissvgn/python-wiki-llm", "--version", "2.5.0",
            "--harness-dir", str(tmp_path / "harness"), "--harness-sha", "b" * 40,
            "--wheel-sha256", hashes["wheel"], "--sdist-sha256", hashes["sdist"],
            "--artifacts", str(artifacts), "--work", str(work), "--output", str(output)]
    assert probe.main(args) == 2
    record = json.loads((output / "probe.json").read_text())
    assert record["status"] == "fail" and record["reason"].startswith("installed-artifact-harness failed")
    assert record["diagnostic"]["release_acceptance"] is False
    assert record["diagnostic"]["status"] == ("complete" if diagnostic_exit == 0 and not malformed_receipt else "failed")
    assert (output / "installed-artifact-harness.stdout").read_bytes() == b"original MCP failure"
    assert next(c for c in record["commands"] if c["label"] == "installed-artifact-harness")["exit_code"] == 1
