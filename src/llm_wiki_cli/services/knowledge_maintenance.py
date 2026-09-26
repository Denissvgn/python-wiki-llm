"""Read-only candidate/producer preflight and bound health-policy commands."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
from typing import Any

import llm_wiki_cli
from ..config import EXTRACTOR_REGISTRY, validate_path, validate_source_root
from ..extractors.common import inventory_language_for_path
from . import extractor_helpers
from .contracts import KNOWLEDGE_SCHEMA_VERSION
from .health_policy import (
    PREFLIGHT_SCHEMA,
    MaintenanceError,
    derive_policy,
    digest,
    strict_json,
    verify_policy,
    _binding,
)
from .knowledge_envelope import (
    ProducerComponentInput,
    build_producer_record,
    hash_source_snapshot,
)
from .knowledge_evidence import hash_json
from .knowledge_freshness import comparable_producer_components
from .knowledge_model import _parse_bundle, parse_knowledge_index
from .knowledge_orchestration import (
    _producer_evidence,
    _infrastructure_extractor_component,
    runtime_generation_options,
    runtime_generation_options_hash,
)
from .knowledge_packs import parse_packed_root
from .knowledge_storage import parse_store_root
from .knowledge_storage_io import StorageReadSession, read_guarded
from .source_selection import validate_persisted_source_selection_identity
from .source_snapshot import build_source_snapshot
from .sync_manifest import SyncManifest
from .wiki_surface_index import WIKI_SURFACE_INDEX_SCHEMA_VERSION

MAX_EVIDENCE_BYTES = 64 * 1024 * 1024


def project_version(root: Path) -> str:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib  # type: ignore[reportMissingImports]
    version = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    if not isinstance(version, str) or not version or version == "unknown":
        raise MaintenanceError("candidate version is unavailable")
    return version


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _installed(candidate: Path, version: str, allow_editable: bool) -> dict[str, Any]:
    distribution = importlib.metadata.distribution("agent-wiki-cli")
    actual = Path(llm_wiki_cli.__file__).resolve().parent
    installed = Path(str(distribution.locate_file("llm_wiki_cli"))).resolve()
    source = (candidate / "src/llm_wiki_cli").resolve()
    if distribution.version != version or llm_wiki_cli.__version__ != version:
        raise MaintenanceError(
            "installed distribution/imported version differs from candidate"
        )
    if actual != installed and not (allow_editable and actual == source):
        raise MaintenanceError(
            "imported package is outside the declared installed/candidate root"
        )
    if actual == source and not allow_editable:
        raise MaintenanceError("release preflight requires a noneditable installation")
    expected_files = {
        p.relative_to(source).as_posix(): digest(p.read_bytes())
        for p in source.rglob("*.py")
    }
    actual_files = {
        p.relative_to(actual).as_posix(): digest(p.read_bytes())
        for p in actual.rglob("*.py")
    }
    for name in set(actual_files) - set(expected_files):
        # The distribution intentionally bundles source-contained plugin examples.
        asset = candidate / name
        if name.startswith("examples/") and asset.is_file():
            expected_files[name] = digest(asset.read_bytes())
    if not expected_files or actual_files != expected_files:
        raise MaintenanceError(
            "installed implementation differs from the intended candidate"
        )
    return {
        "version": distribution.version,
        "import_root": str(actual),
        "implementation_hash": hash_json(expected_files),
        "editable": actual == source,
    }


def _archive_binding(
    archive: Path, identity: dict, candidate: Path, snapshot, wiki: Path
) -> None:
    expected = identity["source"]["archive_sha256"]
    checksum_state = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum_state.update(chunk)
    checksum = checksum_state.hexdigest()
    if checksum != expected:
        raise MaintenanceError("candidate source archive digest mismatch")
    paths = {snapshot.root / name for name in snapshot.captured_content_hashes}
    paths.update(candidate.joinpath("src/llm_wiki_cli").rglob("*.py"))
    paths.update(candidate.joinpath("examples").rglob("*.py"))
    paths.update(
        wiki / name
        for name in (
            ".llm-wiki-knowledge.json",
            ".llm-wiki-manifest.json",
            ".llm-wiki-surface.json",
        )
    )
    with tarfile.open(archive, "r:") as tar:
        entries = {}
        for entry in tar:
            path = PurePosixPath(entry.name)
            if path.is_absolute() or ".." in path.parts or entry.name in entries:
                raise MaintenanceError("unsafe or duplicate candidate archive entry")
            entries[entry.name] = entry
        for path in paths:
            relative = path.absolute().relative_to(candidate.resolve()).as_posix()
            entry = entries.get(relative)
            if entry is None or not entry.isfile() or entry.size > MAX_EVIDENCE_BYTES:
                raise MaintenanceError(
                    "evaluated input is absent from the frozen candidate"
                )
            member = tar.extractfile(entry)
            assert member is not None
            with member:
                expected_bytes = member.read(entry.size + 1)
            if expected_bytes != read_guarded(path, MAX_EVIDENCE_BYTES).content:
                raise MaintenanceError(
                    "evaluated input differs from the frozen candidate"
                )


def preflight(
    *,
    candidate_root: str,
    candidate_sha: str,
    src_dir: str,
    wiki_dir: str,
    helper_cache_dir: str | None = None,
    source_selection: str | None = None,
    identity_path: str | None = None,
    source_archive: str | None = None,
    allow_editable: bool = False,
) -> dict[str, Any]:
    candidate = Path(candidate_root).resolve()
    validate_path(wiki_dir, "--wiki-dir")
    source = validate_source_root(src_dir, "--src-dir")
    wiki = Path(wiki_dir)
    if not source.resolve().is_relative_to(
        candidate
    ) or not wiki.resolve().is_relative_to(candidate):
        raise MaintenanceError(
            "maintenance source and wiki must belong to the intended candidate"
        )
    version = project_version(candidate)
    if identity_path is None:
        if (
            source_archive is not None
            or _git(candidate, "rev-parse", "HEAD") != candidate_sha
        ):
            raise MaintenanceError("candidate identity does not match checkout")
        if _git(candidate, "status", "--porcelain=v1", "--untracked-files=all"):
            raise MaintenanceError("candidate checkout is dirty")
        identity = {
            "source": {
                "sha": candidate_sha,
                "tree": _git(candidate, "rev-parse", "HEAD^{tree}"),
                "archive_sha256": None,
            },
            "version": version,
        }
    else:
        identity = strict_json(
            read_guarded(Path(identity_path), MAX_EVIDENCE_BYTES).content
        )
        if (
            identity.get("schema_version") != "agent-wiki-release-identity/v1"
            or not source_archive
        ):
            raise MaintenanceError("frozen identity requires its source archive")
        if identity["source"]["sha"] != candidate_sha or identity["version"] != version:
            raise MaintenanceError("frozen candidate identity mismatch")
    snapshot = build_source_snapshot(source, source_selection=source_selection)
    if source_archive:
        _archive_binding(Path(source_archive), identity, candidate, snapshot, wiki)
    issues = []
    installed = None
    try:
        installed = _installed(candidate, version, allow_editable)
    except (OSError, ValueError, importlib.metadata.PackageNotFoundError) as exc:
        issues.append(str(exc))
    session = StorageReadSession(wiki)
    raw = session.read(".llm-wiki-knowledge.json", MAX_EVIDENCE_BYTES)
    data = strict_json(raw)
    schema = data.get("schema_version")
    if schema in {"llm-wiki-knowledge/v3", "llm-wiki-knowledge/v4"}:
        store = parse_packed_root(raw)["store"]
        bundle = _parse_bundle(store["bundle"], "bundle")
        total = store["collections"]["concepts"]["count"]
    elif schema == "llm-wiki-knowledge/v2":
        store = parse_store_root(raw)
        bundle = _parse_bundle(store["bundle"], "bundle")
        total = store["collections"]["concepts"]["count"]
    else:
        model = parse_knowledge_index(data)
        bundle, total = model.bundle, len(model.concepts)
    manifest = SyncManifest.load(wiki)
    commitments = manifest.artifact_hashes
    if commitments is None or commitments.knowledge_index_hash != digest(raw):
        raise MaintenanceError("knowledge root does not match the committed manifest")
    surface = session.read(".llm-wiki-surface.json", MAX_EVIDENCE_BYTES)
    if commitments.surface_index_hash != digest(surface):
        raise MaintenanceError("surface does not match the committed manifest")
    try:
        validate_persisted_source_selection_identity(
            manifest.generation_inputs,
            snapshot.source_selection_identity,
            operation="maintenance preflight",
            live_selection_inputs=snapshot.source_selection_inputs,
        )
    except ValueError as exc:
        issues.append(str(exc))
    inventory = {
        item.rel_path: {
            "language": inventory_language_for_path(language, item.rel_path)
        }
        for language, files in snapshot.files_by_language.items()
        for item in files
    }
    _, _, components, plugins = _producer_evidence(
        inventory, inventory_complete=True, extractor_registry=EXTRACTOR_REGISTRY
    )
    infrastructure = _infrastructure_extractor_component()
    if any(
        c.component_id == infrastructure.component_id
        for c in bundle.producer.extractors
    ):
        components = (*components, infrastructure)
    live = build_producer_record(
        tool=ProducerComponentInput(
            component_id="agent-wiki-cli",
            version=llm_wiki_cli.__version__,
            configuration={
                "knowledge_schema": KNOWLEDGE_SCHEMA_VERSION,
                "surface_schema": WIKI_SURFACE_INDEX_SCHEMA_VERSION,
            },
        ),
        extractors=components,
        plugins=plugins,
    )
    if not comparable_producer_components(
        bundle.producer.tool, live.tool, configuration_required=False
    ):
        issues.append("recorded producer differs from the installed candidate")
    current = {c.component_id: c for c in live.extractors}
    for recorded in bundle.producer.extractors:
        actual = current.get(recorded.component_id)
        if actual is None or not comparable_producer_components(recorded, actual):
            issues.append("recorded extractor basis differs: " + recorded.component_id)
    if bundle.producer.plugins:
        issues.append(
            "recorded plugin contributions cannot be supplied by the release no-plugin policy"
        )
    options = runtime_generation_options(
        surfaces=manifest.surfaces,
        generation_inputs=manifest.generation_inputs,
        include_tests=None,
        preserve_semantic=True,
    )
    if (
        runtime_generation_options_hash(options, inventory_complete=True)
        != bundle.snapshot.generation_options_hash
    ):
        issues.append(
            "recorded generation options differ from the effective maintenance policy"
        )
    for language, files in snapshot.files_by_language.items():
        if not files or language == "python":
            continue
        prepared = (
            extractor_helpers.get_prepared_typescript_root(source, helper_cache_dir)
            if language == "typescript"
            else extractor_helpers.get_prepared_binary(
                language, source, helper_cache_dir
            )
        )
        if prepared is None:
            issues.append(
                "selected helper is missing, mismatched or outdated: " + language
            )
    session.recheck()
    archive_hash = identity["source"]["archive_sha256"]
    binding = {
        "candidate_sha": candidate_sha,
        "candidate_tree": identity["source"]["tree"],
        "candidate_version": version,
        "source_archive_sha256": None
        if archive_hash is None
        else "sha256:" + archive_hash,
        "src_dir": src_dir,
        "wiki_dir": str(wiki),
        "concepts_total": total,
        "selection_fingerprint": snapshot.source_selection_fingerprint,
        "selection_inputs_hash": None
        if snapshot.source_selection_policy is None
        else hash_json(snapshot.source_selection_inputs),
        "live_source_hash": hash_source_snapshot(snapshot.to_consumed_inputs()),
        "knowledge_index_hash": digest(raw),
        "surface_index_hash": digest(surface),
        "evaluated_envelope_hash": commitments.evaluated_envelope_hash,
    }
    _binding(binding)
    return {
        "schema_version": PREFLIGHT_SCHEMA,
        "status": "blocked" if issues else "ready",
        "binding": binding,
        "installed": installed,
        "issues": sorted(set(issues)),
        "limitations": [
            "Producer alignment is not source freshness or semantic verification.",
            "Recorded package implementation bytes have no cross-version compatibility contract.",
        ],
        "remedy": "Install the intended candidate, prepare selected helpers, then review llm-wiki sync with the same selection and generation options.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    before = commands.add_parser("preflight")
    for name in ("candidate-root", "candidate-sha", "src-dir", "wiki-dir"):
        before.add_argument("--" + name, required=True)
    for name in (
        "helper-cache-dir",
        "source-selection",
        "identity-path",
        "source-archive",
    ):
        before.add_argument("--" + name)
    before.add_argument("--allow-editable", action="store_true")
    for name in ("derive", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--report", required=True)
        command.add_argument("--preflight", required=True)
        command.add_argument("--candidate-sha", required=True)
        command.add_argument("--candidate-tree", required=True)
        command.add_argument("--src-dir", required=True)
        command.add_argument("--wiki-dir", required=True)
        if name == "verify":
            command.add_argument("--receipt", required=True)
    for command in (before, *[commands.choices[name] for name in ("derive", "verify")]):
        command.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    values = vars(args).copy()
    output = Path(values.pop("output"))
    command = values.pop("command")
    try:
        if command == "preflight":
            result = preflight(**values)
            passed = result["status"] == "ready"
        else:
            report = read_guarded(Path(args.report), MAX_EVIDENCE_BYTES).content
            pre = read_guarded(Path(args.preflight), MAX_EVIDENCE_BYTES).content
            binding = strict_json(pre)["binding"]
            for key in ("candidate_sha", "candidate_tree", "src_dir", "wiki_dir"):
                expected = (
                    str(Path(args.wiki_dir))
                    if key == "wiki_dir"
                    else getattr(args, key)
                )
                if binding[key] != expected:
                    raise MaintenanceError(
                        "preflight does not match the requested candidate/scope"
                    )
            result = derive_policy(report, pre, binding=binding)
            if command == "verify":
                verify_policy(
                    strict_json(
                        read_guarded(Path(args.receipt), MAX_EVIDENCE_BYTES).content
                    ),
                    report,
                    pre,
                    binding=binding,
                )
            passed = result["status"] == "pass"
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
        return 0 if passed else 1
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        tarfile.TarError,
        subprocess.SubprocessError,
    ) as exc:
        parser.exit(2, f"maintenance evidence failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
