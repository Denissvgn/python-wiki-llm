"""Integration tests for TS/Go/Rust inventories flowing into wiki commands."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd, migrate_cmd
from llm_wiki_cli.services.extractor_helpers import prepare_helper, resolve_helper_cache_root


PROJECT_ROOT = Path(__file__).parents[1]
TS_NODE_MODULES = (
    PROJECT_ROOT
    / "src"
    / "llm_wiki_cli"
    / "extractors"
    / "ts_scripts"
    / "node_modules"
)


def _command_available(*cmd: str) -> bool:
    if shutil.which(cmd[0]) is None:
        return False
    try:
        subprocess.run(
            list(cmd),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


TS_READY = _command_available("node", "--version") and (
    TS_NODE_MODULES.exists() or _command_available("npm", "--version")
)
GO_READY = _command_available("go", "version")
RUST_READY = _command_available("cargo", "--version")

skip_no_ts_go_rust = pytest.mark.skipif(
    not (TS_READY and GO_READY and RUST_READY),
    reason="TypeScript, Go, and Rust toolchains are not all available",
)
skip_no_go_rust = pytest.mark.skipif(
    not (GO_READY and RUST_READY),
    reason="Go and Rust toolchains are not both available",
)


def _make_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "overwrite": True,
        "depth": "full",
        "skip_workflows": True,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _make_wiki(proj: Path) -> Path:
    wiki = proj / "docs" / "llm_wiki"
    for subdir in ["entities", "modules", "workflows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    _write(wiki / "index.md", "# Old Index\n")
    _write(wiki / "log.md", "# Log\n")
    return wiki


def _short_cache_base(tmp_path: Path) -> Path:
    digest = hashlib.sha1(str(tmp_path).encode("utf-8")).hexdigest()[:8]
    return Path(tempfile.gettempdir()) / f"lww{digest}"


def _prepare_helpers_or_fail(proj: Path, languages: list[str], cache_base: Path, monkeypatch) -> None:
    (proj / ".git").mkdir(exist_ok=True)
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(cache_base))
    cache_root = resolve_helper_cache_root(proj)
    assert cache_root is not None
    for language in languages:
        result = prepare_helper(language, cache_root)
        assert result.status in {"prepared", "already_current"}, result.message


@skip_no_ts_go_rust
def test_bootstrap_multilanguage_collision_pages_lint_passes(tmp_path, monkeypatch, capsys):
    proj = tmp_path / "proj"
    proj.mkdir()
    _write(proj / "web" / "client.ts", "export class Client {}\n")
    _write(proj / "go" / "api" / "client.go", "package api\n\ntype Client struct{}\n")
    _write(proj / "rust" / "native" / "client.rs", "pub struct Client;\n")
    _prepare_helpers_or_fail(
        proj,
        ["typescript", "go", "rust"],
        _short_cache_base(tmp_path),
        monkeypatch,
    )

    monkeypatch.chdir(proj)
    bootstrap_cmd.run(_make_args())

    wiki = proj / "docs" / "llm_wiki"
    module_names = {path.stem for path in (wiki / "modules").glob("*.md")}
    entity_names = {path.stem for path in (wiki / "entities").glob("*.md")}
    assert len([name for name in module_names if name.endswith("_client")]) == 3
    assert len([name for name in entity_names if name.endswith("_Client")]) == 3

    lint_cmd.run(_make_args())
    output = capsys.readouterr().out
    assert "Lint passed" in output


@skip_no_go_rust
def test_migrate_reconciles_legacy_go_page_with_rust_name_collision(tmp_path, monkeypatch, capsys):
    proj = tmp_path / "proj"
    proj.mkdir()
    _write(proj / "go" / "api" / "client.go", "package api\n\ntype Client struct{}\n")
    _write(proj / "rust" / "native" / "client.rs", "pub struct Client;\n")
    _prepare_helpers_or_fail(
        proj,
        ["go", "rust"],
        _short_cache_base(tmp_path),
        monkeypatch,
    )
    wiki = _make_wiki(proj)
    _write(
        wiki / "entities" / "Client.md",
        """
        # Client

        **Location:** `go/api/client.go`

        Legacy Go client notes.
        """,
    )
    _write(
        wiki / "modules" / "client.md",
        """
        # client Module

        **Path:** `go/api/client.go`

        | [`Client`](../entities/Client.md) | struct |
        """,
    )

    monkeypatch.chdir(proj)
    migrate_cmd.run(_make_args())

    assert (wiki / "entities" / "api_client_Client.md").exists()
    assert (wiki / "modules" / "api_client.md").exists()
    module_content = (wiki / "modules" / "api_client.md").read_text(encoding="utf-8")
    entity_content = (wiki / "entities" / "api_client_Client.md").read_text(encoding="utf-8")
    assert "../entities/api_client_Client.md" in module_content
    assert "../entities/Client.md" not in module_content
    assert "Legacy Go client notes." in entity_content

    lint_cmd.run(_make_args())
    output = capsys.readouterr().out
    assert "Lint passed" in output
