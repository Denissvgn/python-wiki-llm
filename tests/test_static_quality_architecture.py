from __future__ import annotations

import ast
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised by the Python 3.10 qualification lane
    import tomli as tomllib


_DOCUMENTATION_RUN_ROOT = Path(
    "src/llm_wiki_cli/services/documentation_run"
)
_COMPATIBILITY_MODULES = {
    _DOCUMENTATION_RUN_ROOT / name
    for name in (
        "contracts.py",
        "export.py",
        "integrity.py",
        "packet.py",
        "prepare.py",
        "record.py",
        "refresh.py",
        "schema.py",
        "verify.py",
        "workspace.py",
    )
}
_BANDIT_SUPPRESSIONS = {
    (
        Path("src/llm_wiki_cli/services/calibration/broker.py"),
        (
            'f"/tmp:rw,noexec,nosuid,nodev,size={config.resources.tmpfs_bytes}"'
            "  # nosec B108"
        ),
    )
}


def test_star_import_exceptions_are_limited_to_compatibility_modules():
    star_import_modules = {
        path
        for root in (Path("src"), Path("integrations"), Path("tests"))
        for path in root.rglob("*.py")
        if any(
            isinstance(node, ast.ImportFrom)
            and any(alias.name == "*" for alias in node.names)
            for node in ast.walk(
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            )
        )
    }

    assert star_import_modules == _COMPATIBILITY_MODULES


def test_ruff_star_import_exceptions_match_compatibility_modules():
    with Path("ruff.toml").open("rb") as handle:
        config = tomllib.load(handle)

    exceptions = config["lint"]["per-file-ignores"]

    assert set(map(Path, exceptions)) == _COMPATIBILITY_MODULES
    assert all(set(rules) == {"F403", "F405"} for rules in exceptions.values())


def test_bandit_suppression_is_limited_to_container_internal_tmpfs():
    suppressions = {
        (path, line.strip())
        for root in (Path("src"), Path("integrations"))
        for path in root.rglob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if "# nosec" in line
    }

    assert suppressions == _BANDIT_SUPPRESSIONS
