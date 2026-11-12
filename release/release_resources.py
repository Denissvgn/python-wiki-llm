"""Owned release allocations, conservative cleanup previews and guarded apply.

Catalogs and receipts are evidence, never executable cleanup instructions.
Only explicitly allocated disposable directories can be removed. Shared Docker
images, builders, volumes, Git worktrees and unregistered environments are kept.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import uuid

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import hosted_evidence as hosted
from release import manual_release as manual
from release import preflight

CATALOG_SCHEMA = "agent-wiki-release-resources/v1"
PLAN_SCHEMA = "agent-wiki-release-cleanup-plan/v1"
MARKER = ".release-resource-owner.json"
MAX_RESOURCES = 1000
MAX_ENTRIES = 100_000
MAX_PLAN_BYTES = preflight.MAX_DOCUMENT
DISPOSABLE = {"venv", "scratch", "source-export"}
require = manual.require


def _identity(path: Path) -> list[int]:
    value = manual.safe(path).lstat()
    require(stat.S_ISDIR(value.st_mode), "Resource root is not a directory")
    return [value.st_dev, value.st_ino]


def _write(path: Path, value: dict) -> None:
    from llm_wiki_cli.services.filesystem_guard import atomic_write_guarded_bytes

    raw = manual.canonical(value)
    before = preflight._read(path) if path.exists() else None
    atomic_write_guarded_bytes(path, raw, expected_existing=before)


def begin_allocation(scratch: Path, *, work: Path, binding: dict, candidate_sha: str,
                     attempt_id: str, role: str, path: Path, kind: str = "venv") -> dict:
    """Record the missing destination before the maintained producer creates it."""
    scratch, work, path = manual.safe(scratch), manual.safe(work), manual.safe(path)
    require(scratch.parent == work and scratch.name == "attempt-" + attempt_id
            and path.is_relative_to(scratch) and path != scratch, "Allocation escapes its exact preflight attempt")
    require(kind in DISPOSABLE and not path.exists(), "Allocation destination is occupied or not disposable")
    catalog_path = scratch / "resources.json"
    catalog = manual.read(catalog_path) if catalog_path.exists() else {
        "schema_version": CATALOG_SCHEMA, "project": "python-wiki-llm", "work": str(work),
        "scratch": str(scratch), "attempt_id": attempt_id, "candidate_sha": candidate_sha,
        "binding_sha256": hosted.sha256(manual.canonical(binding)), "resources": [], "pins": []}
    require(catalog["schema_version"] == CATALOG_SCHEMA and catalog["candidate_sha"] == candidate_sha
            and catalog["attempt_id"] == attempt_id and catalog["work"] == str(work)
            and catalog["scratch"] == str(scratch)
            and catalog["binding_sha256"] == hosted.sha256(manual.canonical(binding))
            and len(catalog["resources"]) < MAX_RESOURCES,
            "Resource catalog belongs to another producer or exceeds bound")
    require(not any(r["path"] == str(path) for r in catalog["resources"]), "Resource was already allocated")
    record = {"resource_id": uuid.uuid4().hex, "kind": kind, "role": role, "path": str(path),
              "status": "allocation-intent", "created_at": manual.now(), "identity": None,
              "runtime_fingerprint": None, "keep": False}
    catalog["resources"].append(record)
    _write(catalog_path, catalog)
    return {"catalog": str(catalog_path), "resource_id": record["resource_id"]}


def finish_allocation(ticket: dict, *, outcome: str, runtime: dict | None = None) -> None:
    catalog_path = manual.safe(Path(ticket["catalog"]))
    catalog = manual.read(catalog_path)
    matches = [r for r in catalog["resources"] if r["resource_id"] == ticket["resource_id"]]
    require(len(matches) == 1, "Allocation ticket is missing or ambiguous")
    row = matches[0]
    path = manual.safe(Path(row["path"]))
    if not path.exists():
        row.update(status="not-created", outcome=outcome)
    else:
        identity = _identity(path)
        marker = {"schema_version": CATALOG_SCHEMA, "resource_id": row["resource_id"],
                  "project": catalog["project"], "attempt_id": catalog["attempt_id"],
                  "candidate_sha": catalog["candidate_sha"], "path": row["path"], "identity": identity}
        marker_path = path / MARKER
        require(not marker_path.exists(), "Allocation marker is already occupied")
        _write(marker_path, marker)
        row.update(status="allocated", outcome=outcome, identity=identity,
                   marker_sha256=hosted.sha256(manual.canonical(marker)),
                   runtime_fingerprint=hosted.sha256(manual.canonical(runtime)) if runtime else None)
        if row["kind"] == "venv":
            config = path / "pyvenv.cfg"
            row["pyvenv_cfg_sha256"] = hosted.sha256(preflight._read(config)) if config.exists() else None
    _write(catalog_path, catalog)


def _work_roots(state: dict) -> list[Path]:
    roots = {manual.safe(Path(a["work"])) for a in state.get("preparation", {}).get("attempts", [])}
    receipt = state.get("preflight_receipt")
    if receipt:
        value = preflight.read_document(manual.safe(Path(receipt)))
        require(value["plan"]["candidate_sha"] == state["candidate_sha"] and value["plan"]["root"] == state["root"],
                "Resource receipt source/root differs from session")
        preflight._check_seal(value, "receipt_hash")
        preflight._check_seal(value["plan"], "plan_hash")
        roots.add(manual.safe(Path(value["work"])))
    return sorted(roots)


def catalogs(state: dict) -> list[tuple[Path, dict]]:
    result = []
    for work in _work_roots(state):
        if not work.exists():
            continue
        for path in sorted(work.glob("attempt-*/resources.json")):
            value = manual.read(path)
            require(value.get("schema_version") == CATALOG_SCHEMA and value.get("candidate_sha") == state["candidate_sha"]
                    and value.get("work") == str(work) and value.get("scratch") == str(path.parent)
                    and path.parent.name == "attempt-" + value.get("attempt_id", ""), "Resource catalog is not bound to the recorded attempt")
            require(len(value["resources"]) <= MAX_RESOURCES and all(isinstance(r, dict) for r in value["resources"]),
                    "Resource inventory exceeds bound")
            result.append((path, value))
    require(len(result) <= MAX_RESOURCES, "Resource catalog count exceeds bound")
    return result


def protected_files(state: dict) -> dict[str, dict]:
    """Pin controller, recovery, qualified bytes and every retained receipt entry."""
    paths = {manual.safe(Path(state["work"]) / name) for name in ("state.json", "events.jsonl")}
    retention = Path(state["work"]) / "resource-retention.json"
    if retention.exists():
        paths.add(manual.safe(retention))
    receipt = state.get("preflight_receipt")
    if receipt:
        path = manual.safe(Path(receipt))
        value = preflight.read_document(path)
        preflight._check_seal(value, "receipt_hash")
        require(value["plan"]["candidate_sha"] == state["candidate_sha"], "Protected receipt candidate differs")
        paths.add(path)
        for name, commitment in value.get("evidence", {}).items():
            relative = Path(name)
            require(not relative.is_absolute() and ".." not in relative.parts and "\\" not in name,
                    "Unsafe receipt evidence path")
            evidence = manual.safe(Path(value["work"]) / relative)
            raw = preflight._read(evidence, preflight.LOCAL_ARCHIVE_EVIDENCE_LIMIT)
            require(commitment == {"bytes": len(raw), "sha256": hosted.sha256(raw)},
                    "Retained receipt evidence changed")
            paths.add(evidence)
    qualified = state.get("qualification", {}).get("bundle")
    if qualified:
        root = manual.safe(Path(qualified))
        require(root.is_relative_to(Path(state["work"])), "Qualified bundle escapes session")
        paths.update(p for p in root.rglob("*") if p.is_file())
    for path, value in catalogs(state):
        paths.add(path)
        paths.add(path.parent / "attempt.json")
        for pin in value.get("pins", []):
            root = manual.safe(Path(pin["path"]))
            require(root.is_relative_to(path.parent), "Resource pin escapes attempt")
            paths.update([root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()])
    # Explicit recovery and diagnostic material is never inferred disposable.
    for root in (Path(state["work"]) / "diagnostics", Path(state["work"]) / "recovery"):
        if root.exists():
            paths.update(p for p in root.rglob("*") if p.is_file())
    require(len(paths) <= 50_000, "Protection inventory exceeds bound")
    result = {}
    for path in sorted(paths):
        raw = preflight._read(manual.safe(path), preflight.LOCAL_ARCHIVE_EVIDENCE_LIMIT)
        result[str(path)] = {"bytes": len(raw), "sha256": hosted.sha256(raw)}
    return result


def retention_state(state: dict) -> dict:
    path = Path(state["work"]) / "resource-retention.json"
    value = manual.read(path) if path.exists() else {"schema_version": CATALOG_SCHEMA, "session_id": state["session_id"],
            "candidate_sha": state["candidate_sha"], "pins": {}, "events": []}
    require(value["schema_version"] == CATALOG_SCHEMA and value["session_id"] == state["session_id"]
            and value["candidate_sha"] == state["candidate_sha"], "Retention ledger belongs to another session")
    return value


def pin(store: manual.Store, resource_id: str, reason: str, *, keep: bool) -> dict:
    require(bool(reason.strip()), "Retention changes require a reason")
    with store.lock():
        state = store.load()
        rows = [r for _, catalog in catalogs(state) for r in catalog["resources"] if r["resource_id"] == resource_id]
        require(len(rows) == 1, "Retention change must identify an allocated resource")
        value = retention_state(state)
        entry = {"resource_id": resource_id, "path": rows[0]["path"], "reason": reason.strip(), "keep": keep,
                 "recorded_at": manual.now()}
        if keep:
            value["pins"][resource_id] = entry
        else:
            value["pins"].pop(resource_id, None)
        value["events"].append(entry)
        _write(store.work / "resource-retention.json", value)
        return value


def _command(argv: list[str], *, binary=False):
    try:
        return subprocess.run(argv, capture_output=True, text=not binary, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None


def scan_consumers(paths: list[Path]) -> dict:
    """Absence/inconclusive tools never becomes a claim of inactivity."""
    host = {str(p): {"status": "unknown", "pids": []} for p in paths}
    executable = shutil.which("lsof")
    if executable:
        for path in paths:
            observed = _command([executable, "-t", "+D", str(path)])
            if observed is not None and observed.returncode in {0, 1} and not observed.stderr.strip():
                pids = observed.stdout.split()
                host[str(path)] = {"status": "active" if pids else "inactive", "pids": pids}
    docker = {"status": "unknown", "containers": [], "mounts": []}
    executable = shutil.which("docker")
    if executable:
        listing = _command([executable, "ps", "-aq", "--no-trunc"])
        if listing is not None and listing.returncode == 0 and not listing.stderr.strip():
            ids = listing.stdout.split()
            require(len(ids) <= 1000 and all(re.fullmatch(r"[0-9a-f]{12,64}", i) for i in ids), "Docker inventory exceeds bound or has invalid IDs")
            if not ids:
                docker = {"status": "observed", "containers": [], "mounts": []}
            else:
                inspected = _command([executable, "inspect", *ids], binary=True)
                if inspected is not None and inspected.returncode == 0 and not inspected.stderr.strip():
                    require(len(inspected.stdout) <= 32 * 1024 * 1024, "Docker inspection exceeds bound")
                    rows = hosted._json(inspected.stdout)
                    require(isinstance(rows, list) and len(rows) == len(ids)
                            and {r["Id"] for r in rows} == set(ids), "Incomplete Docker consumer inventory")
                    docker = {"status": "observed", "containers": [r["Id"] for r in rows],
                              "mounts": [{"container_id": r["Id"], "running": r.get("State", {}).get("Running"),
                                          "source": m["Source"]} for r in rows for m in r.get("Mounts", []) if m.get("Source")]}
    return {"host": host, "docker": docker}


def _overlaps(left: Path, right: Path) -> bool:
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _inactive(path: Path, consumers: dict) -> bool:
    if consumers["host"].get(str(path), {}).get("status") != "inactive" or consumers["docker"]["status"] != "observed":
        return False
    for mount in consumers["docker"]["mounts"]:
        source = Path(mount["source"])
        if not source.is_absolute():
            return False
        # Docker Desktop may expose its VM spelling instead of the host
        # spelling. Consider both, and resolve host aliases such as /tmp and
        # /var; never discard the original mount observation.
        possible = [source]
        for prefix in (Path("/host_mnt"), Path("/run/desktop/mnt/host")):
            if source.is_relative_to(prefix):
                possible.append(Path("/") / source.relative_to(prefix))
        try:
            if any(_overlaps(path, candidate.resolve()) for candidate in possible):
                return False
        except (OSError, RuntimeError):
            return False
    return True


def _allocated(root: Path) -> int:
    return _allocated_roots([root])


def _allocated_roots(roots: list[Path]) -> int:
    seen, total = set(), 0
    for root in roots:
        if not root.exists():
            continue
        for path in (root, *root.rglob("*")):
            metadata = path.lstat()
            key = (metadata.st_dev, metadata.st_ino)
            if key not in seen:
                total += getattr(metadata, "st_blocks", 0) * 512
                seen.add(key)
    return total


def preview(store: manual.Store, *, scanner=scan_consumers, max_resources: int = 8) -> dict:
    from llm_wiki_cli.services.filesystem_guard import guarded_tree_manifest

    state = store.load()
    require(type(max_resources) is int and 1 <= max_resources <= MAX_RESOURCES, "Invalid cleanup batch limit")
    require(state["phase"] == "complete" and state.get("public_verification", {}).get("verified") is True,
            "Cleanup requires the controller's recorded public verification")
    protected = protected_files(state)
    pins = retention_state(state)["pins"]
    rows = []
    selected_count = selected_entries = 0
    for catalog_path, catalog in catalogs(state):
        attempt = manual.read(catalog_path.parent / "attempt.json")
        for record in catalog["resources"]:
            path = manual.safe(Path(record["path"]))
            require(path.is_relative_to(catalog_path.parent) and path != catalog_path.parent,
                    "Resource escaped its recorded allocation scope")
            row = {"resource_id": record["resource_id"], "path": str(path), "kind": record["kind"],
                   "role": record["role"], "catalog": str(catalog_path), "status": "retain", "reason": None}
            if record.get("status") != "allocated" or not path.exists():
                row["reason"] = "missing-or-incomplete-allocation"
            elif record["kind"] not in DISPOSABLE or record.get("keep") or record["resource_id"] in pins or attempt.get("status") != "passed":
                row["reason"] = "retention-pin-or-nonpassing-producer"
            elif (Path(catalog["work"]) / ".execution-lock").exists():
                row["reason"] = "producer-execution-lock"
            elif any(Path(p).is_relative_to(path) for p in protected):
                row["reason"] = "protected-evidence-overlap"
            elif selected_count >= max_resources or selected_entries >= MAX_ENTRIES:
                row["reason"] = "cleanup-batch-limit"
            else:
                require(_identity(path) == record["identity"], "Resource directory identity changed")
                marker = preflight._read(path / MARKER)
                require(hosted.sha256(marker) == record["marker_sha256"], "Resource ownership marker changed")
                manifest = guarded_tree_manifest(path)
                require(len(manifest) <= MAX_ENTRIES, "Resource tree exceeds cleanup bound")
                if selected_entries + len(manifest) > MAX_ENTRIES:
                    row["reason"] = "cleanup-batch-limit"
                else:
                    row.update(status="candidate", identity=record["identity"], marker_sha256=record["marker_sha256"],
                               manifest=[list(entry) for entry in manifest], allocated_bytes=_allocated(path))
                    selected_count += 1
                    selected_entries += len(manifest)
            rows.append(row)
    registered = {r["path"] for r in rows}
    # Older attempts remain visible without fabricating an ownership marker or
    # granting deletion authority to a launcher-prefix string in a receipt.
    for work in _work_roots(state):
        for path in sorted(work.glob("attempt-*/attempt.json")):
            attempt = manual.read(path)
            if attempt.get("candidate_sha") != state["candidate_sha"]:
                continue
            for command in attempt.get("commands", []):
                argv = command.get("argv", [])
                if "create-venv" not in argv or "--path" not in argv:
                    continue
                prefix = manual.safe(Path(argv[argv.index("--path") + 1]))
                require(prefix.is_relative_to(path.parent) and prefix != path.parent, "Legacy allocation escapes attempt")
                if str(prefix) not in registered:
                    rows.append({"resource_id": "legacy-" + hosted.sha256(str(prefix).encode()), "path": str(prefix),
                                 "kind": "venv", "role": command.get("name"), "catalog": None, "status": "retain",
                                 "reason": "unregistered-legacy-allocation" if prefix.exists() else "legacy-allocation-already-absent"})
                    registered.add(str(prefix))
    require(len(rows) <= MAX_RESOURCES, "Cleanup inventory exceeds bound")
    paths = [Path(r["path"]) for r in rows if r["status"] == "candidate"]
    consumers = scanner(paths)
    for row in rows:
        if row["status"] == "candidate":
            row.update(status="remove" if _inactive(Path(row["path"]), consumers) else "retain",
                       reason="owned-disposable-no-observed-consumer" if _inactive(Path(row["path"]), consumers) else "active-or-unobserved-consumer")
    current = manual.read(store.work / "state.json")
    state.pop("seal", None)
    current.pop("seal", None)
    require(state == current, "Controller changed during cleanup preview")
    value = {"schema_version": PLAN_SCHEMA, "session_id": state["session_id"], "candidate_sha": state["candidate_sha"],
             "root": str(store.root), "work": str(store.work), "state_sha256": hosted.sha256(manual.canonical(state)),
             "protected": protected, "resources": rows, "consumers": consumers,
             "batch": {"resource_limit": max_resources, "entry_limit": MAX_ENTRIES, "selected_entries": selected_entries,
                       "deferred_resources": sum(r["reason"] == "cleanup-batch-limit" for r in rows)},
             "allocated_work_bytes": _allocated(store.work), "created_at": manual.now(), "publication_authority": False,
             "docker_disposition": "No image, builder cache, volume or unrelated container removal is supported by this plan."}
    result = {**value, "plan_sha256": hosted.sha256(manual.canonical(value))}
    require(len(manual.canonical(result)) <= MAX_PLAN_BYTES, "Cleanup plan exceeds byte bound; select a smaller batch")
    return result


def apply(store: manual.Store, plan: dict, approved: str, *, scanner=scan_consumers) -> dict:
    from llm_wiki_cli.services.filesystem_guard import guarded_tree_manifest, remove_guarded_tree

    require(plan.get("schema_version") == PLAN_SCHEMA and plan.get("root") == str(store.root) and plan.get("work") == str(store.work)
            and approved == plan.get("plan_sha256") == hosted.sha256(manual.canonical({k: v for k, v in plan.items() if k != "plan_sha256"})),
            "Cleanup plan differs from the reviewed digest or session")
    with store.lock():
        state = store.load()
        require(state["session_id"] == plan["session_id"] and state["candidate_sha"] == plan["candidate_sha"]
                and state["phase"] == "complete" and state.get("public_verification", {}).get("verified") is True
                and hosted.sha256(manual.canonical(state)) == plan["state_sha256"], "Controller changed after cleanup preview")
        require(not store.lease.exists(), "An active release lease prevents cleanup")
        require(protected_files(state) == plan["protected"], "Protected evidence changed after preview")
        require(isinstance(plan["resources"], list) and len(plan["resources"]) <= MAX_RESOURCES,
                "Cleanup inventory exceeds bound")
        selected = [r for r in plan["resources"] if r["status"] == "remove"]
        require(len(selected) <= MAX_RESOURCES and len({r["resource_id"] for r in selected}) == len(selected)
                and len({r["path"] for r in selected}) == len(selected)
                and sum(len(r["manifest"]) for r in selected) <= MAX_ENTRIES,
                "Duplicate or oversized cleanup selection")
        roots = {str(path): value for path, value in catalogs(state)}
        pins = retention_state(state)["pins"]
        paths = [Path(r["path"]) for r in selected if Path(r["path"]).exists()]
        consumers = scanner(paths)
        journal_path = store.work / ("cleanup-" + approved + ".json")
        journal = manual.read(journal_path) if journal_path.exists() else {
            "schema_version": PLAN_SCHEMA, "plan_sha256": approved, "session_id": state["session_id"],
            "resources": {}, "status": "running", "before_allocated_bytes": _allocated_roots(paths),
            "before_session_work_allocated_bytes": _allocated(store.work),
            "allocation_measurement": "unique filesystem identities, st_blocks * 512; no Docker layer or filesystem-free-space claim"}
        require(journal["plan_sha256"] == approved and journal["session_id"] == state["session_id"], "Cleanup journal belongs to another operation")
        # Check the entire removal set before any write. Guarded deletion pins
        # and rechecks each tree again through its own private quarantine.
        for row in selected:
            path = manual.safe(Path(row["path"]))
            catalog = roots.get(row["catalog"])
            require(catalog is not None and path.is_relative_to(Path(catalog["scratch"]))
                    and path != Path(catalog["scratch"]), "Cleanup path is not owned by a registered attempt")
            assert catalog is not None
            matches = [record for record in catalog["resources"] if record["resource_id"] == row["resource_id"]]
            require(len(matches) == 1, "Cleanup resource is not uniquely registered")
            record = matches[0]
            require(all(record.get(key) == row.get(key) for key in ("path", "kind", "role", "identity", "marker_sha256"))
                    and record.get("status") == "allocated" and record.get("outcome") == "passed"
                    and record.get("kind") in DISPOSABLE and not record.get("keep") and record["resource_id"] not in pins,
                    "Cleanup selection differs from the disposable allocation")
            require(manual.read(Path(catalog["scratch"]) / "attempt.json").get("status") == "passed"
                    and not any(Path(p).is_relative_to(path) for p in plan["protected"]),
                    "Cleanup overlaps protected evidence or a nonpassing producer")
            require(not any(path != Path(other["path"]) and _overlaps(path, Path(other["path"])) for other in selected),
                    "Cleanup resource trees overlap")
            require(not (Path(catalog["work"]) / ".execution-lock").exists(), "Local producer is still active")
            old = journal["resources"].get(row["resource_id"], {})
            if not path.exists():
                require(old.get("status") in {"intent", "removed"}, "An unstarted cleanup destination disappeared")
                continue
            require(_inactive(path, consumers), "Active or unobserved consumer prevents cleanup")
            require(_identity(path) == row["identity"] and hosted.sha256(preflight._read(path / MARKER)) == row["marker_sha256"]
                    and [list(entry) for entry in guarded_tree_manifest(path)] == row["manifest"], "Resource changed after preview")
        _write(journal_path, journal)
        for row in selected:
            path = Path(row["path"])
            journal["resources"][row["resource_id"]] = {"path": str(path), "status": "intent"}
            _write(journal_path, journal)
            if path.exists():
                remove_guarded_tree(path, expected_identity=tuple(row["identity"]), expected_manifest=tuple(tuple(e) for e in row["manifest"]))
            journal["resources"][row["resource_id"]]["status"] = "removed"
            _write(journal_path, journal)
        require(protected_files(state) == plan["protected"], "Protected evidence changed during cleanup")
        journal.update(status="complete", after_allocated_bytes=_allocated_roots([Path(r["path"]) for r in selected]),
                       after_session_work_allocated_bytes=_allocated(store.work), completed_at=manual.now())
        journal["reclaimed_allocated_bytes"] = journal["before_allocated_bytes"] - journal["after_allocated_bytes"]
        _write(journal_path, journal)
        return journal


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("preview", "apply", "pin", "unpin"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--approved-plan-sha256")
    parser.add_argument("--resource-id")
    parser.add_argument("--reason")
    parser.add_argument("--max-resources", type=int, default=8,
                        help="Maximum disposable trees per preview; remaining resources are retained for a later batch")
    args = parser.parse_args(argv)
    try:
        root = manual.safe(args.root)
        store = manual.Store(root, root / args.work)
        output = preflight._destination(root, args.output)
        require(not output.exists(), "Cleanup result output is occupied")
        if args.operation in {"pin", "unpin"}:
            if args.resource_id is None or args.reason is None:
                raise ValueError("Resource identity and retention reason required")
            result = pin(store, args.resource_id, args.reason, keep=args.operation == "pin")
        elif args.operation == "preview":
            result = preview(store, max_resources=args.max_resources)
        else:
            if args.plan is None or args.approved_plan_sha256 is None:
                raise ValueError("Reviewed cleanup plan and digest required")
            # A real environment manifest can exceed the controller's small
            # state-document bound. Plans have their own symmetric read/write
            # bound and a shared entry budget across the entire batch.
            plan = hosted._json(preflight._read(manual.safe(root / args.plan), MAX_PLAN_BYTES))
            result = apply(store, plan, args.approved_plan_sha256)
        preflight.write_document(output, result, root=root)
        print(json.dumps({"output": str(output), "status": result.get("status", args.operation), "plan_sha256": result.get("plan_sha256")}, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print("Release resource cleanup failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
