"""Owned evaluation runtime with explicit provider-import and workspace boundaries."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any

from tests.developer_value.fixtures import POLICY_SOURCE, baseline_guides, materialize

HARNESS_ROOT = Path(__file__).resolve().parents[2]
_PROVIDER_ROOT: Path | None = None
_API: ModuleType | None = None


def temporary_parent() -> Path:
    """Use a real writable temporary path instead of the macOS /var alias."""
    import tempfile
    return Path("/private/tmp") if sys.platform == "darwin" else Path(tempfile.gettempdir()).resolve()


def _snapshot(root: Path) -> dict[str, Any] | None:
    path = root / ".developer-value-provider.json"
    if not path.exists():
        return None
    if path.is_symlink():
        raise ValueError("retained provider manifest redirects reads")
    metadata = json.loads(path.read_text())
    if metadata.get("schema_version") != "developer-value-provider-snapshot/v1":
        raise ValueError("unsupported retained provider manifest")
    expected = metadata.get("files")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("retained provider lacks source commitments")
    actual = {}
    for name in expected:
        source = root / name
        if not name.startswith("src/llm_wiki_cli/") or source.is_symlink() or not source.resolve().is_relative_to(root):
            raise ValueError("provider source commitment escaped its root")
        actual[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    names = {p.relative_to(root).as_posix() for p in (root / "src/llm_wiki_cli").rglob("*")
             if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    if actual != expected or names != set(expected):
        raise ValueError("retained provider bytes changed")
    return metadata


def load_provider(provider_root: Path) -> ModuleType:
    """Import the declared provider; reject an already loaded different tree."""
    global _PROVIDER_ROOT, _API
    root = Path(provider_root).resolve()
    source = root / "src"
    if not (source / "llm_wiki_cli/api.py").is_file():
        raise ValueError("provider root lacks the complete source package")
    _snapshot(root)
    for name, module in tuple(sys.modules.items()):
        if name == "llm_wiki_cli" or name.startswith("llm_wiki_cli."):
            location = getattr(module, "__file__", None)
            if location is not None and not Path(location).resolve().is_relative_to(source):
                raise ValueError("a different provider is already imported; use a fresh isolated process")
    sys.path.insert(0, str(source))
    api = importlib.import_module("llm_wiki_cli.api")
    if not Path(str(api.__file__)).resolve().is_relative_to(source):
        raise ValueError("provider import did not originate from its retained source")
    _PROVIDER_ROOT, _API = root, api
    return api


def provider_identity() -> dict[str, Any]:
    """Return exact imported origin and source commitments, without field claims."""
    if _PROVIDER_ROOT is None or _API is None:
        raise ValueError("load the provider before recording its identity")
    metadata = _snapshot(_PROVIDER_ROOT)
    if metadata is not None:
        if metadata.get("schema_version") != "developer-value-provider-snapshot/v1":
            raise ValueError("unsupported retained provider manifest")
        names = sorted(metadata["files"])
    else:
        tracked = subprocess.run(["git", "ls-files", "--", "src/llm_wiki_cli"],
                                 cwd=_PROVIDER_ROOT, capture_output=True, text=True)
        names = tracked.stdout.splitlines() if tracked.returncode == 0 else []
        if not names:
            names = [p.relative_to(_PROVIDER_ROOT).as_posix()
                     for p in sorted((_PROVIDER_ROOT / "src/llm_wiki_cli").rglob("*"))
                     if p.is_file() and not {"__pycache__", "target", "node_modules"}.intersection(p.parts)
                     and p.suffix != ".pyc"]
    files = {}
    for name in names:
        path = _PROVIDER_ROOT / name
        if not name.startswith("src/llm_wiki_cli/") or not path.resolve().is_relative_to(_PROVIDER_ROOT):
            raise ValueError("provider source commitment escaped its root")
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if metadata is not None and files != metadata["files"]:
        raise ValueError("retained provider bytes changed")
    commitment = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"root": str(_PROVIDER_ROOT), "module": str(_API.__file__),
            "source_files": files, "source_tree_sha256": commitment,
            "snapshot": metadata, "python_executable": sys.executable,
            "model_execution_established": False}


def run_cli(argv: list[str]) -> dict[str, Any]:
    """Dispatch a trusted harness CLI recipe through the verified provider."""
    if _PROVIDER_ROOT is None:
        raise ValueError("load the provider before CLI dispatch")
    cli = importlib.import_module("llm_wiki_cli.cli")
    if not Path(str(cli.__file__)).resolve().is_relative_to(_PROVIDER_ROOT / "src"):
        raise ValueError("CLI provider differs from the retained source")
    previous = sys.argv
    stdout, stderr = io.StringIO(), io.StringIO()
    exit_code = 0
    try:
        sys.argv = ["llm-wiki", *argv]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                cli.main()
            except SystemExit as error:
                exit_code = error.code if type(error.code) is int else (0 if error.code is None else 1)
    finally:
        sys.argv = previous
    return {"exit_code": exit_code, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}


def tree_hashes(path: Path) -> dict[str, str]:
    """Count content in an owned tree; redirected artifacts are rejected."""
    root = Path(path)
    if root.is_symlink():
        raise ValueError("owned artifact root must not redirect reads")
    if not root.exists():
        return {}
    files = list(root.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("owned artifacts must not redirect reads")
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files) if p.is_file() and "__pycache__" not in p.parts}


def prepare_workspace(project: str, root: Path, *, tiny: bool = False) -> None:
    """Materialize source and identical baseline guides, then refresh commitments."""
    if _API is None:
        raise ValueError("load the provider before workspace preparation")
    root = Path(root).absolute()
    if tiny:
        if root.is_symlink() or any(p.is_symlink() for p in root.parents):
            raise ValueError("owned workspace must not redirect writes")
        if root.exists() and (not root.is_dir() or any(root.iterdir())):
            raise ValueError("owned workspace must be new or empty")
        (root / "src").mkdir(parents=True)
        (root / "src/policy.py").write_bytes(POLICY_SOURCE.encode("utf-8"))
    else:
        materialize(project, root)
    previous = Path.cwd()
    try:
        os.chdir(root)
        _API.bootstrap_wiki("src", "wiki")
        if not tiny:
            for relative, text in baseline_guides(project).items():
                path = root / "wiki/guides" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(text.encode("utf-8"))
            result = run_cli(["sync", "--src-dir", "src", "--wiki-dir", "wiki",
                              "--jobs", "1", "--no-plugins", "--progress", "never"])
            if result["exit_code"] != 0:
                raise ValueError("baseline guide commitment refresh failed: " + result["stderr"])
    finally:
        os.chdir(previous)


def provider_command(script: str, *args: str, preload: bool = True) -> list[str]:
    """Build a fresh-process command for a trusted harness observation recipe."""
    if _PROVIDER_ROOT is None:
        raise ValueError("load the provider before constructing a child read")
    bootstrap = (
        "import sys\nfrom pathlib import Path\n"
        f"sys.path.insert(0, {str(HARNESS_ROOT)!r})\n"
    )
    if preload:
        bootstrap += ("from tests.developer_value.runtime import load_provider\n"
                      f"api = load_provider(Path({str(_PROVIDER_ROOT)!r}))\n")
    return [sys.executable, "-I", "-c", bootstrap + script, *args]
