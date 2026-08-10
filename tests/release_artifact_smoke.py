#!/usr/bin/env python3
"""Artifact-only functional smoke harness.

This file is uploaded independently from the source archive.  Wheel and sdist
jobs run it from an otherwise empty workspace, so a passing result cannot
silently import the checked-out source tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import unquote


SCHEMA_VERSION = "agent-wiki-artifact-smoke/v1"
EXPECTED_SUBCOMMANDS = (
    "bootstrap",
    "bump",
    "ci-check",
    "context",
    "docs",
    "doctor",
    "extract",
    "generate-prompt",
    "init",
    "install",
    "install-ci",
    "install-hook",
    "knowledge",
    "lint",
    "mcp",
    "metrics",
    "migrate",
    "obsidian",
    "plugins",
    "prepare-extractors",
    "release",
    "review",
    "site",
    "skills",
    "status",
    "sync",
    "team",
    "trigger-agent",
    "uninstall",
    "upgrade",
)
EXPECTED_WIKI_REFERENCE_FILES = (
    "SKILL.md",
    "reference.md",
    "references/context-query.md",
    "references/extractors-dependencies.md",
    "references/governance.md",
    "references/knowledge-consumption.md",
    "references/maintenance.md",
    "references/publishing.md",
    "references/repository-handoff.md",
    "references/resources-context.md",
    "references/surfaces-naming.md",
)
_MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class SmokeError(RuntimeError):
    """Installed artifact behavior failed a release smoke assertion."""


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    expected: int = 0,
) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PIP_NO_INPUT": "1",
    }
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != expected:
        raise SmokeError(
            f"command returned {completed.returncode}, expected {expected}: "
            f"{' '.join(command)}\nstdout:\n{completed.stdout}\nstderr:\n"
            f"{completed.stderr}"
        )
    return completed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_wiki_reference_tree(root: Path) -> int:
    """Require the exact managed tree and resolve every local Markdown link."""

    if root.is_symlink() or not root.is_dir():
        raise SmokeError(f"wiki-reference is not a regular directory: {root}")
    entries = tuple(sorted(root.rglob("*")))
    if any(path.is_symlink() for path in entries):
        raise SmokeError("wiki-reference export contains a symbolic link")
    if any(not path.is_file() and not path.is_dir() for path in entries):
        raise SmokeError("wiki-reference export contains a non-regular entry")
    actual_files = {
        path.relative_to(root).as_posix() for path in entries if path.is_file()
    }
    actual_directories = {
        path.relative_to(root).as_posix() for path in entries if path.is_dir()
    }
    expected_files = set(EXPECTED_WIKI_REFERENCE_FILES)
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        extra = sorted(actual_files - expected_files)
        raise SmokeError(
            "wiki-reference exported file set mismatch: "
            f"missing={missing}, extra={extra}"
        )
    if actual_directories != {"references"}:
        raise SmokeError(
            "wiki-reference exported directory set mismatch: "
            f"actual={sorted(actual_directories)}"
        )

    resolved_root = root.resolve()
    for markdown in sorted(path for path in entries if path.is_file()):
        content = markdown.read_text(encoding="utf-8")
        for match in _MARKDOWN_LINK.finditer(content):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and raw_target.endswith(">"):
                raw_target = raw_target[1:-1]
            target = raw_target.split(maxsplit=1)[0]
            if (
                not target
                or target.startswith("#")
                or _URI_SCHEME.match(target) is not None
            ):
                continue
            path_text = unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            target_path = markdown.parent / path_text
            resolved = target_path.resolve()
            if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
                relative = markdown.relative_to(root).as_posix()
                raise SmokeError(
                    f"unresolved local wiki-reference link in {relative}: {target}"
                )
    return len(actual_files)


def _absolute_without_symlink_resolution(path: Path) -> Path:
    """Return an absolute command path without dereferencing venv symlinks."""
    return Path(os.path.abspath(path))


def _write_fixture(root: Path) -> tuple[Path, Path]:
    source = root / "fixture"
    wiki = root / "wiki"
    source.mkdir(parents=True)
    (source / "pyproject.toml").write_text(
        '[project]\nname = "smoke-fixture"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    package = source / "app"
    package.mkdir()
    (package / "__init__.py").write_text(
        '"""Synthetic release smoke package."""\n',
        encoding="utf-8",
    )
    (package / "service.py").write_text(
        '"""Stable synthetic service."""\n\n'
        "def greeting(name: str) -> str:\n"
        '    """Return a deterministic greeting."""\n'
        '    return f"hello {name}"\n',
        encoding="utf-8",
    )
    return source, wiki


def _json_output(completed: subprocess.CompletedProcess[str], name: str) -> Mapping:
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SmokeError(f"{name} did not emit JSON: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise SmokeError(f"{name} JSON must be an object")
    return payload


def _validate_installation(python: Path, work: Path) -> str:
    completed = _run(
        [
            str(python),
            "-I",
            "-c",
            (
                "import pathlib, llm_wiki_cli; "
                "print(pathlib.Path(llm_wiki_cli.__file__).resolve())"
            ),
        ],
        cwd=work,
    )
    module_path = Path(completed.stdout.strip()).resolve()
    if work == module_path or work in module_path.parents:
        raise SmokeError(f"package imported from smoke workspace: {module_path}")
    if "site-packages" not in module_path.parts:
        raise SmokeError(f"package did not import from site-packages: {module_path}")
    return "/".join(module_path.parts[-2:])


def _validate_mcp(mcp_python: Path, work: Path) -> str:
    _run(
        [
            str(mcp_python),
            "-I",
            "-c",
            (
                "import mcp; "
                "from llm_wiki_cli.services import mcp_server; "
                "assert mcp is not None and mcp_server is not None"
            ),
        ],
        cwd=work,
    )
    command = [
        str(mcp_python),
        "-I",
        "-m",
        "llm_wiki_cli.cli",
        "mcp",
        "--src-dir",
        str(work / "fixture"),
        "--wiki-dir",
        str(work / "wiki"),
        "--transport",
        "stdio",
    ]
    environment = {
        **os.environ,
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "NO_PROXY": "*",
        "no_proxy": "*",
    }
    process = subprocess.Popen(
        command,
        cwd=work,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(2)
    if process.poll() is not None:
        stdout, stderr = process.communicate(timeout=5)
        if process.returncode:
            raise SmokeError(
                "MCP stdio server failed during startup\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            )
        return "stdio-clean-eof"
    process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate(timeout=5)
    return "stdio-started"


def run_smoke(args: argparse.Namespace) -> int:
    artifact = args.artifact.resolve()
    # Preserve virtual-environment interpreter paths.  Path.resolve() follows
    # the ``bin/python`` symlink to the base interpreter and silently drops the
    # environment's site-packages isolation.
    python = _absolute_without_symlink_resolution(args.python)
    mcp_python = _absolute_without_symlink_resolution(args.mcp_python)
    output = args.output.resolve()
    work = args.work.resolve()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    module_suffix = _validate_installation(python, work)
    version_text = _run(
        [str(python), "-I", "-m", "llm_wiki_cli.cli", "--version"],
        cwd=work,
    ).stdout.strip()
    if version_text != f"llm-wiki {args.expected_version}":
        raise SmokeError(
            f"installed version mismatch: {version_text!r}, "
            f"expected {args.expected_version!r}"
        )
    for command in EXPECTED_SUBCOMMANDS:
        _run(
            [str(python), "-I", "-m", "llm_wiki_cli.cli", command, "--help"],
            cwd=work,
        )

    # The default artifact environment must prove MCP remains an optional extra.
    default_mcp = _run(
        [
            str(python),
            "-I",
            "-c",
            (
                "import importlib.util; "
                "raise SystemExit(0 if importlib.util.find_spec('mcp') is None else 1)"
            ),
        ],
        cwd=work,
    )
    if default_mcp.returncode:
        raise SmokeError("default installation unexpectedly includes the MCP SDK")

    source, wiki = _write_fixture(work)
    cli = [str(python), "-I", "-m", "llm_wiki_cli.cli"]
    _run(
        [
            *cli,
            "bootstrap",
            "--src-dir",
            str(source),
            "--wiki-dir",
            str(wiki),
            "--depth",
            "full",
            "--skip-workflows",
            "--skip-flows",
            "--skip-dependencies",
        ],
        cwd=work,
    )
    _run(
        [
            *cli,
            "lint",
            "--src-dir",
            str(source),
            "--wiki-dir",
            str(wiki),
            "--strict",
        ],
        cwd=work,
    )
    sync_command = [
        *cli,
        "sync",
        "--src-dir",
        str(source),
        "--wiki-dir",
        str(wiki),
        "--force",
    ]
    _run(sync_command, cwd=work)
    first_sync_hash = _tree_hash(wiki)
    _run(sync_command, cwd=work)
    second_sync_hash = _tree_hash(wiki)
    if first_sync_hash != second_sync_hash:
        raise SmokeError("two consecutive syncs did not produce identical wiki bytes")

    doctor = _json_output(
        _run(
            [
                *cli,
                "doctor",
                "--src-dir",
                str(source),
                "--wiki-dir",
                str(wiki),
                "--strict",
                "--format",
                "json",
            ],
            cwd=work,
        ),
        "doctor",
    )
    if doctor.get("status") != "healthy" or doctor.get("exit_code") != 0:
        raise SmokeError("strict doctor did not report healthy exit 0")

    packet_path = work / "context-packet.json"
    _run(
        [
            *cli,
            "context",
            "--budget",
            "2000",
            "--src-dir",
            str(source),
            "--wiki-dir",
            str(wiki),
            "--format",
            "packet",
            "--focus",
            "all",
            "--read-only",
            "--output",
            str(packet_path),
        ],
        cwd=work,
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if not isinstance(packet, Mapping):
        raise SmokeError("qualified context packet must be an object")
    packet_schema = packet.get("schema_version")
    if packet_schema != "llm-wiki-qualified-context-packet/v1":
        raise SmokeError(f"unexpected context packet schema: {packet_schema!r}")

    site = work / "site"
    _run(
        [
            *cli,
            "site",
            "export",
            "--wiki-dir",
            str(wiki),
            "--out-dir",
            str(site),
            "--format",
            "plain",
        ],
        cwd=work,
    )
    _run(
        [
            *cli,
            "site",
            "check",
            "--wiki-dir",
            str(wiki),
            "--out-dir",
            str(site),
            "--format",
            "plain",
        ],
        cwd=work,
    )
    vault = work / "vault"
    _run(
        [
            *cli,
            "obsidian",
            "export",
            "--src-dir",
            str(source),
            "--wiki-dir",
            str(wiki),
            "--vault-dir",
            str(vault),
        ],
        cwd=work,
    )
    _run(
        [
            *cli,
            "obsidian",
            "check",
            "--wiki-dir",
            str(wiki),
            "--vault-dir",
            str(vault),
        ],
        cwd=work,
    )

    skills = work / "skills"
    _run([*cli, "skills", "export", "--dest", str(skills)], cwd=work)
    skill_count = len(list(skills.glob("*/SKILL.md")))
    if skill_count != 16:
        raise SmokeError(f"expected 16 bundled skills, found {skill_count}")
    reference_file_count = _validate_wiki_reference_tree(skills / "wiki-reference")
    plugin = work / "plugin"
    _run(
        [
            *cli,
            "plugins",
            "samples",
            "export",
            "documentation-hooks",
            "--dest",
            str(plugin),
        ],
        cwd=work,
    )
    _run([*cli, "plugins", "validate", str(plugin)], cwd=work)

    mcp_status = _validate_mcp(mcp_python, work)
    kind = "wheel" if artifact.suffix == ".whl" else "sdist"
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact": {
            "filename": artifact.name,
            "sha256": _sha256(artifact),
            "kind": kind,
        },
        "version": args.expected_version,
        "result": {
            "installed_module": module_suffix,
            "cli_version": version_text,
            "subcommands": list(EXPECTED_SUBCOMMANDS),
            "sync_sha256": first_sync_hash,
            "doctor_status": doctor["status"],
            "context_packet_schema": packet_schema,
            "context_packet_sha256": _sha256(packet_path),
            "site_sha256": _tree_hash(site),
            "obsidian_sha256": _tree_hash(vault),
            "skills": skill_count,
            "wiki_reference_files": reference_file_count,
            "plugin_sample": "documentation-hooks",
            "default_mcp_sdk": "absent",
            "mcp": mcp_status,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def _arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--mcp-python", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run_smoke(_arguments(argv))
    except (OSError, ValueError, SmokeError, subprocess.TimeoutExpired) as exc:
        print(f"artifact smoke failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
