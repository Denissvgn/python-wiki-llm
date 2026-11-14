"""The embeddable engine applies its host and grants to everything it runs."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from datetime import date
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.engine import Engine, Host, NoProcessHost, current_host
from llm_wiki_cli.services.analysis_compatibility import selected_policy
from llm_wiki_cli.services.helper_runtime import current_helper_operation

ROOT = Path(__file__).resolve().parents[1]


def _helper_policy() -> str:
    operation = current_helper_operation()
    assert operation is not None
    return operation.policy


def test_importing_the_engine_loads_no_cli_commands_or_public_api() -> None:
    probe = (
        "import sys, llm_wiki_cli.engine; "
        "print(sorted(m for m in sys.modules if m == 'llm_wiki_cli.cli' or m == 'llm_wiki_cli.api' "
        "or m.startswith('llm_wiki_cli.commands') or m.startswith('llm_wiki_cli.extractors')))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(ROOT / 'src')!r}); {probe}"],
        capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == "[]"


def test_engine_never_prepares_helpers_unless_granted_while_api_keeps_its_default() -> None:
    boundary = api._api_boundary(_helper_policy)

    assert Engine().call(boundary) == "never"
    assert Engine(helper_preparation="auto").call(boundary) == "auto"
    assert boundary() == "auto"


def test_operation_applies_host_and_comparison_policy_then_restores() -> None:
    host = NoProcessHost()
    engine = Engine(host=host, comparison_policy="analysis-v1")
    outside = current_host()

    with engine.operation() as operation:
        assert current_host() is host is operation.host
        assert selected_policy() == "analysis-v1" == operation.comparison_policy
        assert _helper_policy() == "never" == operation.helper_preparation
    assert current_host() is outside
    assert selected_policy() == "auto"


def test_engine_rejects_grants_its_host_cannot_honor() -> None:
    with pytest.raises(ValueError, match="subprocess"):
        Engine(host=NoProcessHost(), helper_preparation="auto")
    with pytest.raises(ValueError):
        Engine(helper_preparation="sometimes")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Engine(host=object())  # type: ignore[arg-type]
    assert Engine(host=NoProcessHost()).capabilities() == {
        "granted": ["clock", "cwd", "environment"],
        "missing": ["subprocess"],
        "helper_preparation": "never",
        "comparison_policy": "auto",
        "validators": ["implementation-evidence", "maintenance-projection", "governance-projection"],
    }


def test_engines_with_different_hosts_run_side_by_side() -> None:
    engines = {"local": Engine(), "sandboxed": Engine(host=NoProcessHost())}
    barrier = threading.Barrier(len(engines))
    seen: dict[str, Host] = {}

    def observe(name: str) -> None:
        def inside() -> None:
            barrier.wait(timeout=10)
            seen[name] = current_host()
        engines[name].call(inside)

    threads = [threading.Thread(target=observe, args=(name,)) for name in engines]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert {name: host is engines[name].host for name, host in seen.items()} == {
        "local": True, "sandboxed": True,
    }


def test_sandboxed_engine_bootstraps_and_searches_without_any_process(tmp_path: Path, monkeypatch) -> None:
    started: list[object] = []

    def forbidden(args, *rest, **kwargs):
        started.append(args)
        raise AssertionError("no process may start")

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "billing.py").write_text(
        "class Invoice:\n    total: int\n\n\ndef bill(invoice: Invoice) -> int:\n    return invoice.total\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    engine = Engine(host=NoProcessHost())

    engine.call(api.bootstrap_wiki, "src", "wiki")
    hits = engine.call(api.search_wiki, "Invoice", src_dir="src", wiki_dir="wiki")

    assert started == []
    assert (tmp_path / "wiki" / "index.md").is_file()
    assert hits["query"] == "Invoice" and hits["results"]


def test_engine_bootstrap_creates_a_wiki_through_its_host(tmp_path: Path, monkeypatch) -> None:
    import io

    from llm_wiki_cli.engine import BootstrapRequest, BootstrapRequestError

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "billing.py").write_text("class Invoice:\n    total: int\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))

    class PinnedCalendar(NoProcessHost):
        def today(self) -> date:
            return date(2001, 2, 3)

    out = io.StringIO()
    engine = Engine(host=PinnedCalendar(stdout=out, stderr=io.StringIO()))

    result = engine.bootstrap(BootstrapRequest(source_root="src", wiki_root="wiki"))

    assert result.created_files and (tmp_path / "wiki" / "index.md").is_file()
    assert "## 2001-02-03" in (tmp_path / "wiki" / "log.md").read_text(encoding="utf-8")
    assert out.getvalue()
    with pytest.raises(BootstrapRequestError):
        engine.bootstrap(BootstrapRequest(source_root="src", wiki_root="other", overwrite=True))
