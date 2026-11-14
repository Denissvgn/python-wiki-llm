"""Authenticate reviewed hosted captures and import one explicitly reviewed plan.

Fetching and planning are read-only with respect to source. Import writes only
the wiki and retains a complete recovery catalog and resumable operation journal.
Downloaded code is never imported or executed. Local reports are not authority:
every import rechecks the original transport against GitHub's producer records.
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import hosted_evidence as hosted
from release import knowledge_maintenance as maintenance
from release import manual_release as manual
from release import policy_activation
from release.measurement_canary import provider_files

WORKFLOW = ".github/workflows/reviewed-wiki-capture.yml"
WIKI = "docs/llm_wiki"
SCHEMA = "agent-wiki-capture-import/v1"
PREVIEW_SCHEMA = "agent-wiki-reviewed-capture-preview/v1"
LIMITS = {"files": 20_000, "file_bytes": 64 * 1024 * 1024,
          "content_bytes": 512 * 1024 * 1024, "archive_bytes": 600 * 1024 * 1024}
MAX_LOG = 16 * 1024 * 1024
PREVIEW_FILES = {"preview.json", "preview.stdout", "preview.stderr"}
CONVERGENCE_FILES = {"wiki-status-before.txt", "wiki-status-after.txt", "worktree-status-after.txt",
                     "wiki-diff.patch", "sync.log"}
APPLY_FILES = PREVIEW_FILES | CONVERGENCE_FILES | {
    "sync.stdout", "sync.stderr", "convergence-result.json", "wiki-review-snapshot.json", "wiki-review-snapshot.tar"}
require = hosted.require
sha = hosted.sha256


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _name(name: str) -> str:
    require(isinstance(name, str) and 0 < len(name.encode()) <= 4096, "invalid capture path")
    path = PurePosixPath(name)
    require(path.as_posix() == name and not path.is_absolute() and ".." not in path.parts
            and "\\" not in name and ":" not in name and name != "."
            and all(not part.endswith((".", " ")) and not any(ord(c) < 32 for c in part)
                    and part.partition(".")[0].casefold() not in {
                        "con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                        *(f"lpt{i}" for i in range(1, 10))} for part in path.parts), "unsafe capture path")
    require(all(part.casefold() != ".git" for part in path.parts), "capture cannot contain Git metadata")
    return name


def _records(rows: list[dict]) -> dict[str, dict]:
    require(isinstance(rows, list) and 0 < len(rows) <= LIMITS["files"], "snapshot file count exceeds bound")
    records, folded = {}, set()
    total = 0
    for row in rows:
        require(isinstance(row, dict) and set(row) == {"path", "bytes", "sha256", "mode"}, "invalid snapshot record")
        name = _name(row["path"])
        require(name.casefold() not in folded, "duplicate or case-colliding snapshot path")
        require(type(row["bytes"]) is int and 0 <= row["bytes"] <= LIMITS["file_bytes"]
                and type(row["mode"]) is int and 0 <= row["mode"] <= 0o777
                and isinstance(row["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None,
                "invalid snapshot size, mode or digest")
        records[name] = row
        folded.add(name.casefold())
        total += row["bytes"]
    require(total <= LIMITS["content_bytes"], "snapshot content exceeds bound")
    for name in records:
        require(not any(p.as_posix().casefold() in folded for p in PurePosixPath(name).parents
                        if p.as_posix() != "."), "snapshot file/directory conflict")
    return records


def snapshot_files(raw: bytes, manifest: dict, *, source: str, tree: str,
                   run_id: int, attempt: int, epoch: int) -> tuple[dict[str, bytes], dict[str, dict]]:
    require(manifest.get("schema_version") == "llm-wiki-review-snapshot/v1"
            and manifest.get("candidate_sha") == source and manifest.get("candidate_tree") == tree
            and manifest.get("workflow_run_id") == run_id and manifest.get("run_attempt") == attempt
            and manifest.get("wiki_dir") == WIKI and manifest.get("limits") == LIMITS, "snapshot identity or limits differ")
    require(manifest.get("archive") == {"filename": "wiki-review-snapshot.tar", "bytes": len(raw), "sha256": sha(raw)}
            and len(raw) <= LIMITS["archive_bytes"], "snapshot archive digest or length differs")
    records = _records(manifest["entries"])
    require(sum(r["bytes"] for r in records.values()) == manifest.get("content_bytes"), "snapshot content size differs")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for member in archive:
            require(member.name in records and member.name not in files, "unexpected or duplicate snapshot member")
            row = records[member.name]
            require(member.isfile() and not member.linkname and member.mode == row["mode"]
                    and member.size == row["bytes"] and member.mtime == epoch, "snapshot member type, mode, size or epoch differs")
            stream = archive.extractfile(member)
            require(stream is not None, "missing snapshot member")
            assert stream is not None
            with stream:
                data = stream.read(member.size + 1)
            require(len(data) == row["bytes"] and sha(data) == row["sha256"], "snapshot member content differs")
            files[member.name] = data
    require(set(files) == set(records), "snapshot is incomplete")
    return files, records


def _git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "--no-replace-objects", "-C", str(root), *args],
                            capture_output=True, check=True, timeout=60)
    require(len(result.stdout) <= hosted.MAX_EXPANDED, "original Git data exceeds bound")
    return result.stdout


def _basis(root: Path, source: str) -> dict:
    """Read original Git objects through today's verifier; never run old code."""
    archive = _git_bytes(root, "archive", source, "--", "pyproject.toml", "src/llm_wiki_cli")
    with tempfile.TemporaryDirectory(prefix="wiki-capture-basis-") as temporary:
        destination = Path(temporary).resolve()
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
            for member in stream:
                name = _name(member.name.rstrip("/"))
                require(member.isdir() or member.isfile(), "nonregular original provider input")
                require(member.size <= LIMITS["file_bytes"], "oversized original provider input")
                target = destination / name
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    content = stream.extractfile(member)
                    require(content is not None, "missing original provider input")
                    assert content is not None
                    with content, target.open("xb") as output:
                        output.write(content.read(member.size + 1))
        provider = provider_files(destination)
    def read(name):
        return _git_bytes(root, "show", source + ":" + name)
    runtime = hosted._json(read("release/runtime-policy.json"))["profiles"]["knowledge-linux"]
    require(runtime["platform"] == "linux" and runtime["arch"] == "x64", "unsupported capture runtime declaration")
    lock = hosted._json(read("release/toolchain-lock.json"))
    return {"source_sha": source, "source_tree": manual.git(root, "rev-parse", source + "^{tree}").stdout.strip(),
            "wiki_tree": manual.git(root, "rev-parse", source + ":" + WIKI).stdout.strip(),
            "epoch": int(manual.git(root, "show", "-s", "--format=%ct", source).stdout),
            "version": provider["version"], "package_files_sha256": sha(canonical(provider["files"])),
            "python": runtime["python"], "platform": ["Linux", "x86_64"],
            "tool_versions": {n: lock["toolchains"][n]["version_output"] for n in ("node", "npm")},
            "helper_copies": {n: sha(read("src/llm_wiki_cli/extractors/ts_scripts/" + n))
                              for n in ("extract.js", "package.json", "package-lock.json")}}


def authenticate(root: Path, request: dict, *, client, retained_archive: bytes | None = None) -> dict:
    require(set(request) == {"repository", "source_sha", "run_id", "attempt", "operation", "approved_preview_sha256"},
            "invalid capture request fields")
    repository, source, run_id, attempt, operation, approved = (
        request[n] for n in ("repository", "source_sha", "run_id", "attempt", "operation", "approved_preview_sha256"))
    require(repository == "Denissvgn/python-wiki-llm" and isinstance(source, str)
            and re.fullmatch(r"[0-9a-f]{40}", source) is not None and type(run_id) is int and run_id > 0
            and type(attempt) is int and attempt > 0 and operation in {"preview", "apply"}, "invalid capture request identity")
    require((operation == "preview" and approved is None) or
            (operation == "apply" and isinstance(approved, str) and re.fullmatch(r"[0-9a-f]{64}", approved) is not None),
            "apply requires the reviewed preview digest; preview accepts no approval")
    run = client.get(f"/actions/runs/{run_id}")
    workflow = client.get(f"/actions/workflows/{run['workflow_id']}")
    require(workflow.get("path") == WORKFLOW and run.get("path", "").partition("@")[0] == WORKFLOW
            and run.get("id") == run_id and run.get("run_attempt") == attempt
            and run.get("head_sha") == source and run.get("head_branch") == "main"
            and run.get("event") == "workflow_dispatch" and run.get("status") == "completed"
            and run.get("repository", {}).get("full_name") == repository
            and run.get("head_repository", {}).get("full_name") == repository
            and type(run.get("repository", {}).get("id")) is int
            and run["repository"]["id"] == run.get("head_repository", {}).get("id"), "capture run identity differs")
    jobs = client.list(f"/actions/runs/{run_id}/attempts/{attempt}/jobs", "jobs")
    producers = [j for j in jobs if j.get("name") == "capture"]
    require(len(producers) == 1, "missing or ambiguous capture producer")
    job = producers[0]
    require(job.get("status") == "completed" and job.get("run_attempt") == attempt
            and job.get("run_id") == run_id and job.get("head_sha") == source, "capture producer identity differs")
    successful = [s for s in job.get("steps", []) if s.get("name") == "Capture complete successful writer output"
                  and s.get("conclusion") == "success"]
    require((operation == "preview" and run.get("conclusion") == job.get("conclusion") == "success")
            or (operation == "apply" and len(successful) == 1 and run.get("conclusion") in {"success", "failure"}
                and job.get("conclusion") in {"success", "failure"}), "capture producer did not emit successful output")
    artifacts = client.list(f"/actions/runs/{run_id}/artifacts", "artifacts")
    expected = f"reviewed-wiki-capture-{operation}-{run_id}-{attempt}"
    matches = [a for a in artifacts if a.get("name") == expected]
    require(len(matches) == 1, "missing or ambiguous capture artifact")
    artifact = matches[0]
    require(type(artifact.get("size_in_bytes")) is int and 0 < artifact["size_in_bytes"] <= hosted.MAX_ARCHIVE
            and artifact.get("workflow_run", {}).get("head_branch") == "main", "capture transport bound or branch differs")
    raw = client.archive(artifact["id"]) if retained_archive is None else retained_archive
    require(isinstance(raw, bytes) and len(raw) == artifact["size_in_bytes"], "capture transport length differs")
    files, transport = policy_activation._artifact(client, artifact, job, run, retained_archive=raw)
    require(set(files) == (PREVIEW_FILES if operation == "preview" else APPLY_FILES), "unexpected or incomplete capture artifact")
    preview = hosted._json(files["preview.json"])
    require(preview.get("schema_version") == PREVIEW_SCHEMA and preview.get("candidate_sha") == source
            and preview.get("workflow_run_id") == run_id and preview.get("run_attempt") == attempt
            and preview.get("operation") == operation and (preview.get("approved_preview_sha256") or None) == approved,
            "preview identity differs")
    basis = _basis(root, source)
    context = preview["context"]
    require(all(context.get(n) == basis[n] for n in ("source_sha", "source_tree", "wiki_tree", "version",
                                                    "package_files_sha256", "platform", "tool_versions"))
            and context.get("python", "").partition(" ")[0] in basis["python"]
            and context.get("helper", {}).get("status") == "ready"
            and context["helper"].get("copies") == basis["helper_copies"], "capture source, runtime, provider or helper differs")
    stdout = files["preview.stdout"]
    digest = sha(canonical(context) + b"\n" + stdout)
    require(max(len(stdout), len(files["preview.stderr"])) <= MAX_LOG
            and b"Sync dry-run plan:" in stdout and b"DRY-RUN: no files modified." in stdout
            and preview.get("preview_stdout_sha256") == sha(stdout) and preview.get("preview_sha256") == digest,
            "preview bytes or digest differ")
    captured, records = {}, {}
    if operation == "apply":
        require(approved == digest, "apply did not recompute the approved preview")
        result = hosted._json(files["convergence-result.json"])
        checks = ("pre_sync_status_available", "pre_sync_wiki_clean", "pre_sync_worktree_clean",
                  "post_sync_status_available", "post_sync_diff_available", "worktree_changes_scoped_to_wiki")
        require(result.get("schema_version") == "llm-wiki-convergence/v1" and result.get("candidate_sha") == source
                and result.get("wiki_dir") == WIKI and result.get("sync") == {"exit_code": 0, "plugins_enabled": False, "started": True}
                and all(result.get("checks", {}).get(k) is True for k in checks)
                and set(result.get("evidence", {})) == CONVERGENCE_FILES, "successful scoped convergence is missing")
        for name, row in result["evidence"].items():
            require(row.get("bytes") == len(files[name]) and row.get("sha256") == sha(files[name]), "convergence bytes differ")
        require(not files["wiki-status-before.txt"] and files["wiki-status-after.txt"] == files["worktree-status-after.txt"]
                and files["sync.log"] == files["sync.stdout"] + files["sync.stderr"], "convergence scope or sync log differs")
        captured, records = snapshot_files(files["wiki-review-snapshot.tar"], hosted._json(files["wiki-review-snapshot.json"]),
                                            source=source, tree=basis["source_tree"], run_id=run_id, attempt=attempt, epoch=basis["epoch"])
    report = {"request": request, "source_tree": basis["source_tree"], **transport, "preview_sha256": digest,
              "snapshot_archive_sha256": sha(files["wiki-review-snapshot.tar"]) if captured else None,
              "snapshot_files": len(captured), "publication_authority": False,
              "writer_status": "succeeded" if operation == "apply" else "preview",
              "authenticated_snapshot_available": bool(captured),
              "drift": (bool(files["wiki-status-after.txt"]) if operation == "apply" else None),
              "next_action": "review-import-plan" if operation == "apply" else "review-preview"}
    return {"report": report, "archive": raw, "files": files, "snapshot": captured, "records": records}


def _fresh_directory(root: Path, path: Path) -> Path:
    path = manual.safe(path if path.is_absolute() else root / path)
    require(path.is_relative_to(root) and path != root
            and not path.is_relative_to(root / WIKI)
            and manual.git(root, "check-ignore", "-q", str(path / "record.json"), check=False).returncode == 0,
            "capture evidence must be ignored within the checkout and outside the wiki")
    require(not path.exists(), "occupied evidence destination; retain the previous attempt")
    manual.ensure_directory(path.parent)
    path.mkdir(mode=0o700)
    return path


def fetch(root: Path, request: dict, output: Path, *, client) -> dict:
    output = _fresh_directory(root, output)
    manual.atomic(output / "request.json", request)
    authenticated = authenticate(root, request, client=client)
    manual.atomic_bytes(output / "artifact.zip", authenticated["archive"])
    for name in PREVIEW_FILES:
        manual.atomic_bytes(output / name, authenticated["files"][name])
    manual.atomic(output / "authentication.json", authenticated["report"])
    return authenticated["report"]


def load_capture(root: Path, capture: Path, *, client) -> dict:
    capture = manual.safe(capture)
    request = manual.read(capture / "request.json")
    raw = maintenance.read(manual.safe(capture / "artifact.zip"), hosted.MAX_ARCHIVE)
    return authenticate(root, request, client=client, retained_archive=raw)


def _file_record(path: Path, raw: bytes) -> dict:
    metadata = manual.safe(path).lstat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1, "source must contain regular single-link files")
    return {"bytes": len(raw), "sha256": sha(raw), "mode": 0o644 if os.name == "nt" else stat.S_IMODE(metadata.st_mode)}


def _materialized_records(records: dict) -> dict:
    # Windows does not expose POSIX permissions. The authenticated manifest
    # retains exact producer modes; this map describes the local postimage.
    return {n: {"bytes": r["bytes"], "sha256": r["sha256"], "mode": 0o644 if os.name == "nt" else r["mode"]}
            for n, r in records.items()}


def _wiki_state(root: Path) -> tuple[dict[str, bytes], dict[str, dict]]:
    from llm_wiki_cli.services.maintenance_protocol import snapshot_wiki

    files = snapshot_wiki(manual.safe(root / WIKI))
    require(len(files) <= LIMITS["files"] and sum(map(len, files.values())) <= LIMITS["content_bytes"], "wiki preimage exceeds bound")
    records = {_name(n): _file_record(root / WIKI / n, raw) for n, raw in files.items()}
    return files, records


def _outside_source(root: Path) -> dict:
    from llm_wiki_cli.services.knowledge_storage_io import read_guarded

    names = _git_bytes(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    require(len(names) <= 50001, "source inventory exceeds bound")
    result, total = {}, 0
    for name in sorted(set(names) - {""}):
        _name(name)
        if name.startswith(WIKI + "/"):
            continue
        path = manual.safe(root / name)
        raw = read_guarded(path, LIMITS["file_bytes"]).content
        total += len(raw)
        require(total <= 2 * 1024 * 1024 * 1024, "source bytes exceed bound")
        result[name] = _file_record(path, raw)
    return result


def _selected_changes(root: Path, source: str, head: str) -> list[str]:
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot
    from release.preparation import changes_since

    require(manual.git(root, "merge-base", "--is-ancestor", source, head, check=False).returncode == 0,
            "capture source is not in target history")
    require(manual.git(root, "rev-parse", source + ":" + WIKI).stdout.strip()
            == manual.git(root, "rev-parse", head + ":" + WIKI).stdout.strip(),
            "wiki baseline changed since capture; review a fresh preview to preserve newer prose and ownership")
    config = hosted._json(maintenance.read(root / maintenance.POLICY_PATH))
    original = hosted._json(_git_bytes(root, "show", source + ":" + maintenance.POLICY_PATH))
    require(all(config[n] == original[n] for n in ("wiki_dir", "src_dir", "selection")), "capture selection configuration changed")
    snapshot = build_source_snapshot(root, source_selection=config["selection"])
    inputs = (snapshot.source_selection_inputs or {}).get("inputs", [])
    require(isinstance(inputs, list), "source selection inputs are unavailable")
    if not isinstance(inputs, list):
        raise ValueError("source selection inputs are unavailable")
    selection_inputs = {r["path"] for r in inputs if isinstance(r, dict)}
    selection_inputs.update({config["selection"], ".gitignore"})
    return sorted({p for row in changes_since(root, source, head) for p in (row["path"], row["old"])
                   if p and (p in selection_inputs or p.endswith("/.gitignore") or snapshot.path_is_effectively_selected(p))})


def storage_audit(files: dict[str, bytes], records: dict[str, dict]) -> dict:
    with tempfile.TemporaryDirectory(prefix="wiki-capture-review-") as temporary:
        wiki = Path(temporary).resolve() / "wiki"
        wiki.mkdir()
        for name, raw in files.items():
            path = wiki / _name(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            path.chmod(records[name]["mode"])
        report = audit_wiki(wiki)
    return report


def audit_wiki(wiki: Path) -> dict:
    from llm_wiki_cli.services.knowledge_storage_diagnostics import storage_report

    report = storage_report(wiki, full=True, require_referenced=True)
    require(report.get("ok") is True, "captured wiki failed the full read-only storage audit")
    return report


def health_review(root: Path) -> dict:
    from release.preparation import source_status
    from release import preflight_targets

    config = hosted._json(maintenance.read(root / maintenance.POLICY_PATH))
    sources = source_status(root, config)
    require(sources["status"] != "capture-required", "imported writer snapshot does not cover current selected source")
    return {"sources": sources,
            "target_runtime": preflight_targets.inspect(root, WIKI, lambda name: maintenance.read(root / name)),
            "strict_native_maintenance_proof": "pending",
            "publication_authority": False}


def operations(before: dict, after: dict, eligible: set[str]) -> list[dict]:
    rows = []
    for name in sorted(eligible | set(after)):
        old, new = before.get(name), after.get(name)
        require(name in eligible or old is None, "captured creation destination is occupied by an ignored file")
        if old != new:
            rows.append({"path": name, "operation": "create" if old is None else "remove" if new is None else "update",
                         "before": old, "after": new})
    return rows


def _destinations(root: Path, current: dict, after: dict) -> None:
    for name in after:
        path = manual.safe(root / WIKI / _name(name))
        require(not path.exists() or name in current, "capture destination is occupied by a directory or case alias")
        for parent in path.parents:
            if parent == root / WIKI:
                break
            require(not parent.exists() or parent.is_dir(), "capture destination has an occupied parent")


def preview_import(root: Path, capture: Path, *, client) -> dict:
    identity = manual.source(root)
    authenticated = load_capture(root, capture, client=client)
    require(authenticated["report"]["request"]["operation"] == "apply", "import requires a complete applied capture")
    require(not _selected_changes(root, authenticated["report"]["request"]["source_sha"], identity["candidate_sha"]),
            "selected source changed since capture; finish source changes and review a fresh target-host preview")
    _, before = _wiki_state(root)
    eligible = {_name(str(PurePosixPath(n).relative_to(WIKI))) for n in
                _git_bytes(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", WIKI).decode().split("\0") if n}
    after = _materialized_records(authenticated["records"])
    rows = operations(before, after, eligible)
    _destinations(root, before, after)
    outside = _outside_source(root)
    report = storage_audit(authenticated["snapshot"], authenticated["records"])
    require(manual.source(root) == identity and _wiki_state(root)[1] == before and _outside_source(root) == outside,
            "source changed during import review")
    plan = {"schema_version": SCHEMA, "root": str(root), **identity, "wiki_dir": WIKI,
            "capture": str(manual.safe(capture)), "authentication": authenticated["report"],
            "before": before, "after": after, "eligible": sorted(eligible), "outside_source": outside,
            "operations": rows, "storage_audit": report, "publication_authority": False}
    return {**plan, "plan_sha256": sha(canonical(plan))}


def _validate_plan(root: Path, plan: dict, approved: str) -> None:
    require(plan.get("schema_version") == SCHEMA and plan.get("root") == str(root) and plan.get("wiki_dir") == WIKI,
            "import plan belongs to another checkout or schema")
    require(isinstance(approved, str) and re.fullmatch(r"[0-9a-f]{64}", approved) is not None
            and approved == plan.get("plan_sha256") == sha(canonical({k: v for k, v in plan.items() if k != "plan_sha256"})),
            "import plan differs from the reviewed digest")
    require(plan["operations"] == operations(plan["before"], plan["after"], set(plan["eligible"])), "import operation list differs")


def load_preimage(directory: Path, metadata: dict) -> dict[str, bytes]:
    """Read supported recovery bytes without claiming maintenance adoption."""
    from llm_wiki_cli.services.maintenance_recovery import CATALOG_SCHEMA, load_recovery_catalog
    from llm_wiki_cli.services.knowledge_storage_io import read_guarded

    if metadata.get("schema_version") == CATALOG_SCHEMA:
        return load_recovery_catalog(directory, metadata)
    require(metadata.get("schema_version") == "llm-wiki-maintenance-recovery/v1"
            and metadata.get("kind") == "captured-preimage", "unsupported import preimage")
    files = {}
    for name, row in metadata["files"].items():
        raw = read_guarded(manual.safe(directory / _name(name)), LIMITS["file_bytes"]).content
        require(row == {"hash": "sha256:" + sha(raw), "bytes": len(raw)}, "recovery bytes differ")
        files[name] = raw
    return files


def apply_import(root: Path, plan: dict, approved: str, recovery: Path, *, client) -> dict:
    from llm_wiki_cli.services.filesystem_guard import atomic_write_guarded_bytes, ensure_guarded_directory, unlink_guarded_bytes
    from llm_wiki_cli.services.knowledge_storage_io import read_guarded
    from llm_wiki_cli.services.maintenance_protocol import (
        governance_writer_lock, storage_writer_lock, save_recovery_snapshot, load_adoption_marker,
    )

    _validate_plan(root, plan, approved)
    recovery = manual.safe(recovery if recovery.is_absolute() else root / recovery)
    require(not recovery.is_relative_to(root / WIKI), "import recovery must stay outside the wiki")
    store = manual.Store(root, recovery)
    with store.lock():
        require(not store.lease.exists(), "reconcile the active release session before importing source")
        with governance_writer_lock(root / WIKI), storage_writer_lock(root / WIKI):
            require(manual.git(root, "rev-parse", "HEAD").stdout.strip() == plan["candidate_sha"]
                    and manual.git(root, "rev-parse", "HEAD^{tree}").stdout.strip() == plan["candidate_tree"]
                    and not _git_bytes(root, "diff", "--cached", "--name-only", "-z", "HEAD")
                    and _outside_source(root) == plan["outside_source"], "source or index changed after import review")
            authenticated = load_capture(root, Path(plan["capture"]), client=client)
            require(authenticated["report"] == plan["authentication"], "authenticated capture changed after review")
            after = _materialized_records(authenticated["records"])
            require(after == plan["after"], "snapshot file map changed after review")
            files, current = _wiki_state(root)
            _destinations(root, current, after)
            if not recovery.exists():
                require(current == plan["before"], "wiki changed after import review")
                _fresh_directory(root, recovery)
                manual.atomic(recovery / "plan.json", plan)
            require(manual.read(recovery / "plan.json") == plan, "recovery belongs to another reviewed plan")
            journal_path = recovery / "journal.json"
            if journal_path.exists():
                journal = manual.read(journal_path)
                require(journal.get("plan_sha256") == approved and journal.get("status") in {"importing", "complete"},
                        "invalid import recovery journal")
                preimage = load_preimage(recovery / "preimage", journal["preimage"])
            else:
                require(current == plan["before"], "wiki changed before recovery publication")
                marker = load_adoption_marker(root / WIKI)
                metadata = save_recovery_snapshot(recovery / "preimage", files, marker=marker,
                                                  kind="captured-preimage", owner_root=root / WIKI if marker else None)
                journal = {"schema_version": SCHEMA, "plan_sha256": approved, "status": "importing",
                           "preimage": metadata, "completed": []}
                manual.atomic(journal_path, journal)
                preimage = files
            require({n: {"sha256": sha(raw), "bytes": len(raw), "mode": plan["before"][n]["mode"]}
                     for n, raw in preimage.items()} == plan["before"], "complete recovery preimage differs")
            expected = dict(plan["before"])
            changed_names = {r["path"] for r in plan["operations"]}
            for row in plan["operations"]:
                require(current.get(row["path"]) in (row["before"], row["after"]), "wiki contains foreign edits; recovery retained")
                expected.pop(row["path"], None)
            require({n: r for n, r in current.items() if n not in changed_names} == expected,
                    "wiki inventory changed; recovery retained")
            for row in plan["operations"]:
                name = _name(row["path"])
                path = manual.safe(root / WIKI / name)
                old = preimage.get(name)
                new = authenticated["snapshot"].get(name)
                observed = read_guarded(path, LIMITS["file_bytes"]).content if path.exists() else None
                require(observed in (old, new), "wiki changed during import; recovery retained")
                if current.get(name) != row["after"]:
                    if new is None:
                        assert old is not None
                        unlink_guarded_bytes(path, expected=old)
                    else:
                        ensure_guarded_directory(path.parent)
                        atomic_write_guarded_bytes(path, new, mode=row["after"]["mode"], expected_existing=observed)
                if name not in journal["completed"]:
                    journal["completed"].append(name)
                    manual.atomic(journal_path, journal)
            final = {**plan["before"]}
            for row in plan["operations"]:
                if row["after"] is None:
                    final.pop(row["path"], None)
                else:
                    final[row["path"]] = row["after"]
            require(_wiki_state(root)[1] == final and _outside_source(root) == plan["outside_source"]
                    and manual.git(root, "rev-parse", "HEAD").stdout.strip() == plan["candidate_sha"], "import postimage or source changed")
            audit = audit_wiki(root / WIKI)
            health = health_review(root)
            require(_wiki_state(root)[1] == final and _outside_source(root) == plan["outside_source"]
                    and manual.git(root, "rev-parse", "HEAD").stdout.strip() == plan["candidate_sha"]
                    and not _git_bytes(root, "diff", "--cached", "--name-only", "-z", "HEAD"),
                    "source or wiki changed during final audit; recovery retained")
            journal.update(status="complete", storage_audit=audit, health_review=health)
            manual.atomic(journal_path, journal)
            return {"status": "imported-review-required", "plan_sha256": approved, "operations": len(plan["operations"]),
                    "recovery": str(recovery), "storage_audit": audit, "health_review": health, "publication_authority": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("fetch", "preview-import", "apply-import"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--repository", default="Denissvgn/python-wiki-llm")
    parser.add_argument("--source-sha")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--capture-operation", choices=("preview", "apply"))
    parser.add_argument("--approved-preview-sha256")
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--approved-plan-sha256")
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        from release.preflight import _destination, write_document
        root = manual.safe(args.root)
        client = hosted.GitHub(args.repository)
        if args.operation != "fetch":
            output = _destination(root, args.output)
            require(not output.exists() and not output.is_relative_to(root / WIKI),
                    "output must be fresh ignored evidence outside the wiki")
        if args.operation == "fetch":
            request = {"repository": args.repository, "source_sha": args.source_sha, "run_id": args.run_id,
                       "attempt": args.attempt, "operation": args.capture_operation,
                       "approved_preview_sha256": args.approved_preview_sha256}
            result = fetch(root, request, args.output, client=client)
        elif args.operation == "preview-import":
            if args.capture is None:
                raise ValueError("capture directory required")
            result = preview_import(root, manual.safe(root / args.capture), client=client)
            write_document(args.output, result, root=root)
        else:
            if args.plan is None or args.recovery is None:
                raise ValueError("reviewed plan and fresh recovery directory required")
            result = apply_import(root, manual.read(root / args.plan), args.approved_plan_sha256, args.recovery, client=client)
            write_document(args.output, result, root=root)
        print(json.dumps({k: result[k] for k in ("status", "plan_sha256", "preview_sha256", "snapshot_files") if k in result}, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print("Reviewed wiki capture failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
