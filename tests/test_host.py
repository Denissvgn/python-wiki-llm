"""The engine reaches processes, environment and the working directory via its host."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from llm_wiki_cli.services import change_selection, circuit_breaker, knowledge_storage_lifecycle, paths
from llm_wiki_cli.services.host import (
    Host,
    HostCapabilityError,
    NoProcessHost,
    current_host,
    discarding_output,
    discarding_stdout,
    emit,
    recording_errors,
    using_host,
)


class PinnedHost(Host):
    def __init__(self, *, environ: Mapping[str, str] | None = None, cwd: Path | None = None):
        self._environ = dict(environ or {})
        self._cwd = cwd

    @property
    def environ(self) -> Mapping[str, str]:
        return self._environ

    def cwd(self) -> Path:
        return self._cwd if self._cwd is not None else super().cwd()


def test_default_host_follows_live_process_state(tmp_path: Path, monkeypatch) -> None:
    host = current_host()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_WIKI_HOST_PROBE", "live")

    assert host.cwd() == Path.cwd()
    assert host.environ["LLM_WIKI_HOST_PROBE"] == "live"
    result = host.run([sys.executable, "-c", "print('ran')"], capture_output=True, text=True, check=True)
    assert result.stdout == "ran\n"
    assert host.now().tzinfo is not None


def test_using_host_is_scoped_and_restored() -> None:
    default = current_host()
    outer, inner = PinnedHost(), NoProcessHost()

    with using_host(outer):
        assert current_host() is outer
        with using_host(inner):
            assert current_host() is inner
        assert current_host() is outer
    assert current_host() is default
    with pytest.raises(TypeError):
        with using_host(object()):  # type: ignore[arg-type]
            pass


def test_engine_reads_environment_from_the_host(monkeypatch) -> None:
    monkeypatch.setenv(circuit_breaker.BREAKER_TTL_ENV, "5")

    with using_host(PinnedHost(environ={circuit_breaker.BREAKER_TTL_ENV: "42"})):
        assert circuit_breaker.breaker_ttl_seconds() == 42.0
    assert circuit_breaker.breaker_ttl_seconds() == 5.0


def test_engine_resolves_relative_paths_against_the_host_cwd(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "src").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    assert paths.portable_source_root_label(workspace / "src") == "workspace/src"
    with using_host(PinnedHost(cwd=workspace)):
        assert paths.portable_source_root_label(workspace / "src") == "src"


def test_no_process_host_refuses_and_engine_degrades_like_missing_git(tmp_path: Path, monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("no process may start under NoProcessHost")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    host = NoProcessHost()

    with pytest.raises(HostCapabilityError, match="git"):
        host.run(["git", "status"])
    assert isinstance(HostCapabilityError("x"), OSError)
    with using_host(host):
        assert knowledge_storage_lifecycle._default_recovery_directory(tmp_path, "sha256:" + "0" * 64) is None
        with pytest.raises(ValueError, match="Git changes"):
            change_selection._git(tmp_path, "rev-parse", "HEAD")
    assert os.environ is current_host().environ


def test_emit_writes_to_the_host_streams_and_defaults_follow_redirection(capsys) -> None:
    out, err = io.StringIO(), io.StringIO()

    with using_host(Host(stdout=out, stderr=err)):
        emit("progress", 3)
        emit("Error: bad", stream="stderr")
    emit("live")

    assert (out.getvalue(), err.getvalue()) == ("progress 3\n", "Error: bad\n")
    assert capsys.readouterr().out == "live\n"


def test_with_output_keeps_host_behaviour_and_discarding_drops_only_stdout() -> None:
    out, err = io.StringIO(), io.StringIO()
    host = NoProcessHost(stdout=out, stderr=err)
    pinned = PinnedHost(cwd=Path("/pinned")).with_output(stdout=out)

    assert isinstance(host.with_output(stderr=io.StringIO()), NoProcessHost)
    assert pinned.cwd() == Path("/pinned") and pinned.stdout is out
    with using_host(host):
        with discarding_stdout() as quiet:
            emit("hidden")
            emit("kept", stream="stderr")
            assert isinstance(quiet, NoProcessHost)
        emit("shown")
    assert (out.getvalue(), err.getvalue()) == ("shown\n", "kept\n")


def test_recording_errors_still_writes_stderr_and_keeps_the_error_lines() -> None:
    out, err = io.StringIO(), io.StringIO()

    with using_host(Host(stdout=out, stderr=err)):
        with recording_errors() as recorder:
            emit("working")
            emit("Warning: slow", stream="stderr")
            emit("Error: broke", stream="stderr")
        emit("after", stream="stderr")

    assert recorder.error_text() == "Error: broke"
    assert err.getvalue() == "Warning: slow\nError: broke\nafter\n"
    assert out.getvalue() == "working\n"


def test_discarding_output_drops_both_streams(capsys) -> None:
    with discarding_output():
        emit("out")
        emit("err", stream="stderr")

    assert capsys.readouterr() == ("", "")
