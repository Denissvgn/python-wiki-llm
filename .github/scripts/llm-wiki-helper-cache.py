#!/usr/bin/env python3
"""Build and record the fail-closed GitHub helper-cache contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import NoReturn, Protocol

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 CI
    import tomli as tomllib


CACHE_KEY_SCHEMA = "llm-wiki-helpers-v1"
METRICS_SCHEMA = "llm-wiki-helper-cache-metrics/v1"
PLAN_SCHEMA = "llm-wiki-prepare-extractors-plan/v1"
SUPPORTED_HELPERS = ("typescript", "go", "rust", "haskell")
HELPER_FILES = {
    "typescript": (
        "src/llm_wiki_cli/extractors/ts_scripts/extract.js",
        "src/llm_wiki_cli/extractors/ts_scripts/package.json",
        "src/llm_wiki_cli/extractors/ts_scripts/package-lock.json",
    ),
    "go": (
        "src/llm_wiki_cli/extractors/go_scripts/main.go",
        "src/llm_wiki_cli/extractors/go_scripts/go.mod",
        "src/llm_wiki_cli/extractors/go_scripts/go.sum",
    ),
    "rust": (
        "src/llm_wiki_cli/extractors/rust_scripts/Cargo.toml",
        "src/llm_wiki_cli/extractors/rust_scripts/Cargo.lock",
        "src/llm_wiki_cli/extractors/rust_scripts/src/main.rs",
    ),
    "haskell": (
        "src/llm_wiki_cli/extractors/haskell_scripts/Main.hs",
        "src/llm_wiki_cli/extractors/haskell_scripts/Inventory.hs",
        "src/llm_wiki_cli/extractors/haskell_scripts/Parser.hs",
        "src/llm_wiki_cli/extractors/haskell_scripts/Paths.hs",
        "src/llm_wiki_cli/extractors/haskell_scripts/Json.hs",
    ),
}
OPTIONAL_HELPER_FILES = frozenset(
    {"src/llm_wiki_cli/extractors/go_scripts/go.sum"}
)
HELPER_CONTRACT = "src/llm_wiki_cli/services/extractor_helpers.py"
_SAFE_KEY_PART = re.compile(r"^[A-Za-z0-9_.-]{1,32}$", re.ASCII)
_IMMUTABLE_REF = re.compile(r"^[0-9a-f]{40}$", re.ASCII)


class HelperCacheContractError(ValueError):
    """Raised when cache identity or metrics inputs violate the contract."""


def _fail(message: str) -> NoReturn:
    raise HelperCacheContractError(message)


class _Digest(Protocol):
    def update(self, value: bytes) -> object: ...


def _read_regular(path: Path, *, label: str, limit: int | None = None) -> bytes:
    if path.is_symlink() or not path.is_file():
        _fail(f"{label} is not a non-symlink regular file")
    try:
        data = path.read_bytes()
    except OSError as exc:
        _fail(f"cannot read {label}: {exc}")
    if limit is not None and (not data or len(data) > limit):
        _fail(f"{label} size is outside the accepted bounds")
    return data


def load_plan(path: Path) -> tuple[str, ...]:
    """Load the exact canonical helper plan emitted by the CLI."""

    raw = _read_regular(path, label="extractor plan", limit=4096)
    try:
        pairs = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=lambda value: value,
            parse_constant=lambda value: _fail(
                f"extractor plan contains non-standard constant {value!r}"
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"extractor plan is not strict UTF-8 JSON: {exc}")
    if not isinstance(pairs, list) or not all(
        isinstance(pair, tuple) and len(pair) == 2 for pair in pairs
    ):
        _fail("extractor plan top level must be an object")
    if [key for key, _value in pairs] != ["schema", "languages"]:
        _fail("extractor plan keys or key order do not match the v1 contract")
    payload = dict(pairs)
    if payload["schema"] != PLAN_SCHEMA:
        _fail("extractor plan schema is unsupported")
    languages = payload["languages"]
    if not isinstance(languages, list) or any(
        type(item) is not str for item in languages
    ):
        _fail("extractor plan languages must be an array of strings")
    canonical = tuple(language for language in SUPPORTED_HELPERS if language in languages)
    if list(canonical) != languages:
        _fail("extractor plan languages are unknown, duplicated, or unordered")
    return canonical


def _project_version(project_root: Path) -> str:
    raw = _read_regular(project_root / "pyproject.toml", label="pyproject.toml")
    try:
        document = tomllib.loads(raw.decode("utf-8"))
        version = document["project"]["version"]
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        _fail(f"cannot resolve the CLI version: {exc}")
    if not isinstance(version, str) or not version or len(version) > 128:
        _fail("CLI version is not a bounded string")
    return version


def _add_identity_field(hasher: _Digest, label: str, value: bytes) -> None:
    hasher.update(label.encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(value)
    hasher.update(b"\0")


def _read_helper_source(project_root: Path, relative: str) -> bytes:
    path = project_root / relative
    if relative in OPTIONAL_HELPER_FILES and not path.exists() and not path.is_symlink():
        return b"<missing>"
    return _read_regular(path, label=relative)


def cache_key(
    *,
    project_root: Path,
    lock_path: Path,
    languages: tuple[str, ...],
    runner_os: str,
    runner_arch: str,
    action_ref: str = "",
) -> str:
    """Return the exact helper-cache key for the selected implementation."""

    for label, value in (("runner OS", runner_os), ("runner architecture", runner_arch)):
        if not _SAFE_KEY_PART.fullmatch(value):
            _fail(f"{label} is not a safe cache-key component")
    canonical = tuple(
        language for language in SUPPORTED_HELPERS if language in languages
    )
    if languages != canonical:
        _fail("selected languages are unknown, duplicated, or unordered")
    normalized_ref = action_ref.lower()
    if normalized_ref and not _IMMUTABLE_REF.fullmatch(normalized_ref):
        _fail("action ref must be empty or one immutable 40-character commit")

    hasher = hashlib.sha256()
    fields = (
        ("cache-key-schema", CACHE_KEY_SCHEMA.encode("ascii")),
        ("runner-os", runner_os.lower().encode("ascii")),
        ("runner-arch", runner_arch.lower().encode("ascii")),
        (
            "canonical-plan",
            json.dumps(
                {"schema": PLAN_SCHEMA, "languages": list(languages)},
                separators=(",", ":"),
            ).encode("ascii"),
        ),
        ("toolchain-lock", _read_regular(lock_path, label="toolchain lock")),
        ("cli-version", _project_version(project_root).encode("utf-8")),
        (
            "helper-cache-contract",
            _read_regular(project_root / HELPER_CONTRACT, label=HELPER_CONTRACT),
        ),
        ("action-ref", normalized_ref.encode("ascii")),
    )
    for label, value in fields:
        _add_identity_field(hasher, label, value)
    for language in languages:
        for relative in HELPER_FILES[language]:
            _add_identity_field(
                hasher,
                f"helper-source:{relative}",
                _read_helper_source(project_root, relative),
            )
    return (
        f"{CACHE_KEY_SCHEMA}-{runner_os.lower()}-{runner_arch.lower()}-"
        f"{hasher.hexdigest()}"
    )


def metrics_payload(
    *, languages: tuple[str, ...], cache_hit: str, started_ns: int, finished_ns: int
) -> dict[str, object]:
    """Build bounded cache metrics without runner-local path disclosure."""

    if cache_hit not in {"", "true", "false"}:
        _fail("cache-hit must be empty, true, or false")
    if started_ns < 0 or finished_ns < started_ns:
        _fail("preparation timestamps are invalid")
    elapsed_ms = (finished_ns - started_ns + 999_999) // 1_000_000
    if elapsed_ms > 3_600_000:
        _fail("preparation duration exceeds the bounded metrics contract")
    attempted = bool(languages)
    return {
        "schema": METRICS_SCHEMA,
        "cache_key_schema": CACHE_KEY_SCHEMA,
        "cache_attempted": attempted,
        "cache_hit": cache_hit == "true",
        "selected_languages": list(languages),
        "prepare_elapsed_ms": elapsed_ms,
    }


def _append_outputs(path: Path, *, key: str, has_helpers: bool) -> None:
    try:
        with path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(f"cache-key={key}\n")
            output.write(f"has-helpers={'true' if has_helpers else 'false'}\n")
    except OSError as exc:
        _fail(f"cannot write GitHub step outputs: {exc}")


def _write_metrics(path: Path, payload: dict[str, object]) -> None:
    raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    if len(raw) > 1024:
        _fail("helper-cache metrics exceed the size bound")
    if not path.parent.is_dir() or path.parent.is_symlink():
        _fail("helper-cache metrics parent must be a real directory")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(raw)
        temporary.replace(path)
    except OSError as exc:
        _fail(f"cannot write helper-cache metrics: {exc}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    identity = subparsers.add_parser("identity")
    identity.add_argument("--plan", type=Path, required=True)
    identity.add_argument("--project-root", type=Path, required=True)
    identity.add_argument("--lock", type=Path, required=True)
    identity.add_argument("--runner-os", required=True)
    identity.add_argument("--runner-arch", required=True)
    identity.add_argument("--action-ref", default="")
    identity.add_argument("--github-output", type=Path, required=True)
    metrics = subparsers.add_parser("metrics")
    metrics.add_argument("--plan", type=Path, required=True)
    metrics.add_argument("--cache-hit", default="")
    metrics.add_argument("--started-ns", type=int, required=True)
    metrics.add_argument("--finished-ns", type=int, required=True)
    metrics.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    languages = load_plan(args.plan)
    if args.command == "identity":
        key = cache_key(
            project_root=args.project_root,
            lock_path=args.lock,
            languages=languages,
            runner_os=args.runner_os,
            runner_arch=args.runner_arch,
            action_ref=args.action_ref,
        )
        _append_outputs(args.github_output, key=key, has_helpers=bool(languages))
        return 0
    payload = metrics_payload(
        languages=languages,
        cache_hit=args.cache_hit,
        started_ns=args.started_ns,
        finished_ns=args.finished_ns,
    )
    _write_metrics(args.output, payload)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HelperCacheContractError as exc:
        print(f"llm-wiki-helper-cache: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
