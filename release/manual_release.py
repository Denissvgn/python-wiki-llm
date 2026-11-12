"""Durable manual release sessions around the maintained release verifiers.

Local session state is not release evidence. Remote writes require an explicit
authorization scope; an interrupted dispatch is observed, never redispatched.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import hosted_evidence as hosted
from release import qualification as q
from release import qualification_automation as automation

SCHEMA = "agent-wiki-manual-release/v1"
ACTIONS = ("qualify", "dry-run", "tag", "publish", "github-release")
NEXT = {"prepared": "qualify", "qualified": "dry-run", "dry-run-verified": "tag",
        "tagged": "publish", "published": "github-release"}
FINISHED = {"complete", "superseded"}
WORKFLOWS = {"qualify": ("release-qualification.yml", "Release qualification"),
             "dry-run": ("publish.yml", "Promote qualified artifacts to PyPI"),
             "publish": ("publish.yml", "Promote qualified artifacts to PyPI")}


class SessionError(ValueError):
    """A release transition cannot be established safely."""


def require(condition: Any, message: str) -> None:
    if not condition:
        raise SessionError(message)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    for parent in (*reversed(path.parents), path):
        if parent.exists() or parent.is_symlink():
            require(not parent.is_symlink(), "Session paths cannot traverse links")
            metadata = parent.lstat()
            require(not getattr(metadata, "st_file_attributes", 0) & 0x400,
                    "Session paths cannot traverse reparse points")
    return path


def read(path: Path) -> dict:
    path = safe(path)
    require(path.is_file() and path.stat().st_size <= 4 * 1024 * 1024,
            "Session document is missing or oversized")
    value = hosted._json(path.read_bytes())
    require(isinstance(value, dict), "Session document must be an object")
    return value


def atomic(path: Path, value: dict) -> None:
    atomic_bytes(path, canonical(value))


def atomic_bytes(path: Path, value: bytes) -> None:
    safe(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            os.chmod(temporary, 0o600)
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def sync_directory(path: Path) -> None:
    """Persist POSIX directory entries before a subsequent external write.

    Python exposes no portable directory-flush primitive on Windows. Existing
    file flushing and atomic replacement retain process-interruption safety
    there; no Windows power-loss durability is inferred from that behavior.
    """
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def ensure_directory(path: Path) -> None:
    missing = []
    current = safe(path)
    while not current.exists():
        missing.append(current)
        current = current.parent
    path.mkdir(parents=True, exist_ok=True)
    for directory in reversed(missing):
        sync_directory(directory.parent)


def sync_artifact_cache(folder: Path, inventory: dict) -> None:
    """Persist a complete POSIX cache before publishing or reusing its name.

    Windows retains the process-interruption boundary described by
    ``sync_directory``; no portable directory power-loss guarantee is claimed.
    """
    if os.name == "nt":
        return
    folder = safe(folder)
    directories = {folder}
    paths = [folder / "artifact.zip", folder / "transport.json"]
    paths.extend(folder / "files" / member for member in inventory)
    for path in paths:
        path = safe(path)
        require(path.is_relative_to(folder) and path != folder,
                "Artifact cache member escapes its directory")
        metadata = path.lstat()
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1,
                "Retained artifact cache must contain regular single-link files")
        with path.open("rb") as stream:
            os.fsync(stream.fileno())
        parent = path.parent
        while parent != folder:
            directories.add(parent)
            parent = parent.parent
    for directory in sorted(directories, key=lambda path: len(path.parts), reverse=True):
        sync_directory(directory)


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-replace-objects", "-C", str(root), *arguments], capture_output=True,
                          text=True, encoding="utf-8", check=check)


def source(root: Path) -> dict:
    from release.measurement_canary import verify_tracked_source

    require(not git(root, "status", "--porcelain", "--untracked-files=all").stdout,
            "Commit source changes before creating or advancing a release session")
    candidate = git(root, "rev-parse", "HEAD").stdout.strip()
    tree = git(root, "rev-parse", candidate + "^{tree}").stdout.strip()
    try:
        verify_tracked_source(root, candidate)
    except (OSError, ValueError) as error:
        raise SessionError("Candidate tracked source differs: " + str(error)) from error
    require(git(root, "rev-parse", "HEAD").stdout.strip() == candidate,
            "Candidate source changed during inspection")
    return {"candidate_sha": candidate, "candidate_tree": tree,
            "version": q._project_version(root)}


class Store:
    def __init__(self, root: Path, work: Path):
        self.root, self.work = safe(root), safe(work)
        require(self.work.is_relative_to(self.root) and self.work != self.root,
                "Session work must be an ignored directory within the checkout")
        require(git(self.root, "check-ignore", "--quiet", str(self.work / "state.json"),
                    check=False).returncode == 0, "Session records must be ignored")
        common = Path(git(self.root, "rev-parse", "--git-common-dir").stdout.strip())
        self.common = safe(common if common.is_absolute() else self.root / common)
        self.lease = self.common / "manual-release-active.json"

    @contextmanager
    def lock(self):
        lock = safe(self.common / "manual-release.lock")
        with lock.open("a+b") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Invalid release lock")
            if os.name == "nt":
                import msvcrt
                if stream.tell() == 0:
                    stream.write(b"\0")
                    stream.flush()
                stream.seek(0)
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise SessionError("Another release transition is active") from exc
            else:
                import fcntl
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    raise SessionError("Another release transition is active") from exc
            yield

    def load(self) -> dict:
        value = read(self.work / "state.json")
        seal = value.pop("seal", None)
        require(seal == digest(canonical(value)), "Session state changed or is incomplete")
        require(value.get("schema_version") == SCHEMA and value.get("root") == str(self.root)
                and value.get("work") == str(self.work), "Session belongs to another checkout")
        require(isinstance(value.get("phase"), str) and value["phase"] in {*NEXT, "github-released", *FINISHED},
                "Unknown session phase")
        require(isinstance(value.get("authorizations"), list)
                and all(isinstance(a, str) for a in value["authorizations"])
                and set(value["authorizations"]) <= set(ACTIONS), "Unknown authorization")
        require(all(isinstance(value.get(k), str) and re.fullmatch(r"[0-9a-f]{40}", value[k])
                    for k in ("candidate_sha", "candidate_tree"))
                and type(value.get("revision")) is int and value["revision"] > 0,
                "Invalid session source or revision")
        return value

    def save(self, state: dict, event: str) -> dict:
        state["revision"] += 1
        state["updated_at"] = now()
        record = {"revision": state["revision"], "time": state["updated_at"],
                  "event": event, "phase": state["phase"], "pending": state.get("pending")}
        events = safe(self.work / "events.jsonl")
        with events.open("ab") as stream:
            stream.write(json.dumps(record, sort_keys=True).encode() + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        atomic(self.work / "state.json", {**state, "seal": digest(canonical(state))})
        return state

    def claim(self, state: dict) -> None:
        if self.lease.exists():
            lease = read(self.lease)
            require(lease.get("session_id") == state["session_id"]
                    and lease.get("work") == str(self.work),
                    "Another release candidate owns the session lease; resume or explicitly supersede it")
        else:
            atomic(self.lease, {"session_id": state["session_id"], "work": str(self.work),
                                "candidate_sha": state["candidate_sha"]})

    def release(self, state: dict) -> None:
        if self.lease.exists() and read(self.lease).get("session_id") == state["session_id"]:
            self.lease.unlink()
            sync_directory(self.common)


class Controller:
    def __init__(self, store: Store, backend: Any = None):
        self.store, self.backend = store, backend

    def initialize(self, repository: str, candidate: str, *, receipt: Path | None = None,
                   authorize: tuple[str, ...] = ()) -> dict:
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "Invalid repository")
        require(set(authorize) <= set(ACTIONS), "Unknown authorization")
        with self.store.lock():
            if (self.store.work / "state.json").exists():
                state = self.store.load()
                require(state["repository"] == repository and state["candidate_sha"] == candidate,
                        "Existing session is bound to another candidate")
                if state["phase"] not in FINISHED:
                    self.store.claim(state)
                else:
                    self.store.release(state)
                return state
            require(not self.store.work.exists() or not any(self.store.work.iterdir()),
                    "A new session requires a fresh ignored work directory")
            identity = source(self.store.root)
            require(identity["candidate_sha"] == candidate, "Candidate differs from checkout")
            state = {"schema_version": SCHEMA, "session_id": uuid.uuid4().hex,
                     "root": str(self.store.root), "work": str(self.store.work),
                     "repository": repository, **identity, "phase": "prepared",
                     "preflight_receipt": str(safe(receipt)) if receipt else None,
                     "authorizations": sorted(set(authorize)), "pending": None,
                     "revision": 0, "created_at": now()}
            ensure_directory(self.store.work)
            self.store.save(state, "initialized")
            self.store.claim(state)
            return state

    def advance(self, authorize: tuple[str, ...] = (), receipt: Path | None = None) -> dict:
        require(set(authorize) <= set(ACTIONS), "Unknown authorization")
        with self.store.lock():
            state = self.store.load()
            if state["phase"] in FINISHED:
                self.store.release(state)
                return state
            self.store.claim(state)
            identity = source(self.store.root)
            require(identity == {k: state[k] for k in identity},
                    "Candidate source changed; explicitly supersede instead of reusing evidence")
            grants = sorted(set(state["authorizations"]) | set(authorize))
            if grants != state["authorizations"] or receipt:
                state["authorizations"] = grants
                if receipt:
                    require(state["phase"] == "prepared" and not state["pending"],
                            "Cannot replace preparation evidence after dispatch")
                    state["preflight_receipt"] = str(safe(receipt))
                self.store.save(state, "authorization-or-preparation-updated")
            if state["pending"]:
                result = self.backend.reconcile(state, state["pending"])
                if result is None:
                    return {**state, "observation": "awaiting_remote_visibility_or_completion"}
                if result.get("pending"):
                    return {**state, "observation": result.get("observation", "remote-running"), "remote": result}
                if result.get("failed"):
                    if state["pending"].get("failure") != result:
                        state["pending"]["failure"] = result
                        self.store.save(state, "remote-failed-" + state["pending"]["action"])
                    return {**state, "observation": "remote-failed", "remote": result}
                if result.get("retry_safe"):
                    action = state["pending"]["action"]
                    require(action in {"tag", "github-release"}, "Non-idempotent writes cannot be retried")
                    require(action in state["authorizations"], "Repair is not authorized")
                    self.backend.check_bundle(state)
                    return self._effect(state, action, repair=True)
                action = state["pending"]["action"]
                self._accept(state, action, result)
                state["pending"] = None
                return self.store.save(state, "reconciled-" + action)
            if state["phase"] == "github-released":
                state["public_verification"] = self.backend.verify_public(state)
                require(state["public_verification"].get("verified") is True,
                        "Public release verification is incomplete")
                state["phase"] = "complete"
                self.store.save(state, "public-release-verified")
                self.store.release(state)
                return state
            action = NEXT[state["phase"]]
            if action not in state["authorizations"]:
                observation = "awaiting_authorization" if state["phase"] == "prepared" else "authorized-scope-complete"
                return {**state, "observation": observation, "next_action": action}
            if action == "qualify":
                state["admission"] = self.backend.admit(state)
                if state["admission"].get("admitted") is not True:
                    self.store.save(state, "preparation-blocked")
                    return {**state, "observation": "preparation-blocked"}
            else:
                self.backend.check_bundle(state)
            return self._effect(state, action)

    def _effect(self, state: dict, action: str, *, repair: bool = False) -> dict:
        prepared = self.backend.prepare(state, action)
        self._same_source(state)
        previous = state.get("pending")
        state["pending"] = {"action": action, "started_at": now(), "before": prepared,
                            "operation_id": uuid.uuid4().hex, "repair": repair}
        try:
            self.store.save(state, "intent-" + action)
            validate = getattr(self.backend, "validate_submission", None)
            if validate is not None:
                validate(state, action)
            self._same_source(state)
        except BaseException:
            # No effect has been attempted in this region, including on an
            # interruption. Restore any preceding unresolved repair intent.
            state["pending"] = previous
            self.store.save(state, "validation-refused-before-submission-" + action)
            raise
        try:
            result = self.backend.perform(state, state["pending"])
        except Exception as exc:
            # The server may have accepted the write. Never infer that a lost
            # response means it is safe to submit the same POST again.
            state["pending"]["outcome_unknown"] = True
            state["pending"]["error_type"] = type(exc).__name__
            return self.store.save(state, "unknown-outcome-" + action)
        state["pending"]["response"] = result
        if previous:
            state["pending"]["previous_operation_id"] = previous["operation_id"]
        return self.store.save(state, "submitted-" + action)

    def _same_source(self, state: dict) -> None:
        identity = source(self.store.root)
        require(identity == {key: state[key] for key in identity},
                "Candidate source changed before submission")

    @staticmethod
    def _accept(state: dict, action: str, result: dict) -> None:
        require(result.get("verified") is True and result.get("candidate_sha") == state["candidate_sha"],
                "Remote result is not verified for this candidate")
        if action == "qualify":
            require(result.get("version") == state["version"], "Qualified version changed")
            state["qualification"] = result
            state["phase"] = "qualified"
        else:
            key, phase = {"dry-run": ("dry_run", "dry-run-verified"), "tag": ("tag", "tagged"),
                          "publish": ("publication", "published"),
                          "github-release": ("github_release", "github-released")}[action]
            state[key], state["phase"] = result, phase

    def supersede(self, reason: str) -> dict:
        require(bool(reason.strip()), "Supersession requires a reason")
        with self.store.lock():
            state = self.store.load()
            if state["phase"] == "superseded":
                self.store.release(state)
                return state
            previous_phase = state["phase"]
            require(previous_phase not in {"published", "github-released", "complete"},
                    "A published release must be reconciled, not superseded")
            require(not state.get("pending") or state["pending"]["action"] in {"qualify", "dry-run"},
                    "An irreversible write is unresolved")
            if previous_phase == "tagged":
                require(state.get("pending") is None and state.get("publication") is None,
                        "A publication attempt must be reconciled, not superseded")
                tag = state.get("tag", {})
                require(isinstance(tag, dict), "Tagged supersession requires a verified tag record")
                reference = "refs/tags/v" + state["version"]
                refs = tag.get("refs", {})
                require(tag.get("verified") is True and tag.get("candidate_sha") == state["candidate_sha"]
                        and isinstance(refs, dict) and set(refs) == {reference, reference + "^{}"}
                        and isinstance(refs.get(reference), str)
                        and re.fullmatch(r"[0-9a-f]{40}", refs[reference]) is not None
                        and refs[reference + "^{}"] == state["candidate_sha"],
                        "Tagged supersession requires the recorded verified tag identity")
                # This is an explicit local disposition, not a remote tag
                # deletion/move or a fresh assertion about remote state.
                state["tag_retained"] = {"ref": reference, "object_sha": refs[reference],
                                         "source_sha": state["candidate_sha"]}
            state.update(phase="superseded", supersession_from=previous_phase,
                         supersession_reason=reason.strip())
            self.store.save(state, "explicitly-superseded")
            self.store.release(state)
            return state


class GitHubBackend:
    """Actual operations; repository settings and automation enablement are untouched."""
    def __init__(self, root: Path, work: Path, repository: str, token: str):
        self.root, self.work, self.repository = root, work, repository
        require(Path(__file__).resolve() == (root / "release/manual_release.py").resolve()
                and Path(q.__file__).resolve() == (root / "release/qualification.py").resolve()
                and Path(hosted.__file__).resolve() == (root / "release/hosted_evidence.py").resolve(),
                "Execute the maintained readers from the selected candidate checkout")
        self.client = automation.GitHubClient(repository, token, write=True)
        self.token = token

    def admit(self, state: dict) -> dict:
        from release import preflight, readiness
        capabilities = readiness.inspect(self.root, check_availability=True)
        blockers = list(capabilities.get("blockers", []))
        receipt_hash = None
        try:
            require(state.get("preflight_receipt"), "A complete local preflight receipt is required")
            path = Path(state["preflight_receipt"])
            receipt = preflight.read_document(path)
            verified = preflight.verify_receipt(path)
            require(verified["ok"] and verified["status"] in {"local-ready-hosted-required", "target-runtime-unknown"}
                    and receipt["plan"]["candidate_sha"] == state["candidate_sha"]
                    and Path(receipt["plan"]["root"]).resolve() == self.root.resolve(),
                    "Preparation receipt is partial, failed or belongs to another candidate")
            receipt_hash = digest(path.read_bytes())
        except (OSError, ValueError, KeyError) as exc:
            blockers.append({"capability": "local-preflight", "reason": str(exc)})
        eligibility = q.release_eligibility(self.root, check_registry=True)
        if eligibility["status"] != "eligible":
            blockers.append({"capability": "release-version", "reason": eligibility.get("reason")})
        try:
            raw = (self.root / automation.maintenance.POLICY_PATH).read_bytes()
            policy = hosted._json(raw)
            require(isinstance(policy, dict), "Knowledge policy must be an object")
            if policy.get("mode") == "required":
                require(automation.inspect(self.root)["status"] == "current", "Required policy approval is not current")
            else:
                actual = (automation.maintenance.composite_policy_digest(lambda name: (self.root / name).read_bytes())
                          if policy.get("schema_version") == automation.maintenance.CONFIG_V2_SCHEMA
                          else digest((self.root / automation.maintenance.LEAF_PATH).read_bytes()))
                automation.maintenance.policy(raw, implementation_hash=actual)
        except (OSError, ValueError, KeyError) as exc:
            blockers.append({"capability": "knowledge-policy", "reason": str(exc)})
        try:
            require(automation.Coordinator(self.root, self.repository, self.client).ci_success(state["candidate_sha"]),
                    "Current exact-source main CI has not succeeded")
        except (OSError, ValueError, KeyError) as exc:
            blockers.append({"capability": "main-ci", "reason": str(exc)})
        return {"admitted": not blockers, "receipt_sha256": receipt_hash,
                "capabilities": capabilities, "eligibility": eligibility, "blockers": blockers}

    def _main(self, state: dict) -> None:
        ref = self.client.get("/git/ref/heads/main")
        require(ref.get("ref") == "refs/heads/main" and ref.get("object", {}).get("sha") == state["candidate_sha"],
                "Main advanced; reconcile the candidate before another write")

    def _origin(self) -> str:
        urls = git(self.root, "remote", "get-url", "--push", "--all", "origin").stdout.splitlines()
        require(len(urls) == 1, "Origin must have exactly one effective push destination")
        url = urls[0]
        require(url in {"git@github.com:" + self.repository + ".git",
                        "https://github.com/" + self.repository + ".git",
                        "ssh://git@github.com/" + self.repository + ".git"},
                "Origin push destination does not match the selected GitHub repository")
        # get-url has already expanded origin's URL aliases. Passing its result
        # as an explicit push argument must not apply a second rewrite. Reject
        # matching prefixes instead of attempting to duplicate Git's resolver.
        rules = git(self.root, "config", "--null", "--get-regexp",
                    r"^url\..*\.(insteadof|pushinsteadof)$", check=False)
        require(rules.returncode in {0, 1}, "Cannot inspect tag push URL rewriting")
        for record in rules.stdout.split("\0"):
            if record:
                _, separator, prefix = record.partition("\n")
                require(bool(separator) and not url.startswith(prefix),
                        "Captured tag push destination has a matching URL rewrite rule")
        return url

    def prepare(self, state: dict, action: str) -> dict:
        if action != "github-release":
            self._main(state)
        self._origin()
        if action == "tag":
            self._tag(state, allow_absent=True)
        elif action in {"publish", "github-release"}:
            self._tag(state)
        if action in WORKFLOWS:
            workflow = WORKFLOWS[action][0]
            runs = self.client.list(f"/actions/workflows/{workflow}/runs?event=workflow_dispatch", "workflow_runs")
            require(not any(r.get("status") != "completed" and r.get("head_sha") == state["candidate_sha"] for r in runs),
                    "An existing candidate workflow is active; reconcile it first")
            return {"run_ids": [r["id"] for r in runs]}
        return {}

    def validate_submission(self, state: dict, action: str) -> None:
        """Recheck mutable remote inputs while a refused write can still roll back."""
        if action in WORKFLOWS:
            self._main(state)
            if action == "publish":
                self._tag(state)

    def _inputs(self, state: dict, action: str) -> dict:
        if action == "qualify":
            return {**automation.qualification_inputs(state["candidate_sha"], "normal", ""),
                    "ubuntu-core-shards": "true"}
        qualified = state["qualification"]
        return {"qualification-run-id": str(qualified["run_id"]), "candidate-sha": state["candidate_sha"],
                "qualification-ref": "refs/heads/main", "wheel-sha256": qualified["artifacts"]["wheel"]["sha256"],
                "sdist-sha256": qualified["artifacts"]["sdist"]["sha256"], "publish": str(action == "publish").lower()}

    def perform(self, state: dict, pending: dict) -> dict:
        action = pending["action"]
        if action in WORKFLOWS:
            return self.client.request("POST", f"/actions/workflows/{WORKFLOWS[action][0]}/dispatches",
                                       {"ref": "main", "inputs": self._inputs(state, action)}) or {}
        if action == "tag":
            destination = self._origin()
            tag = "v" + state["version"]
            existing = git(self.root, "show-ref", "--verify", "--quiet", "refs/tags/" + tag, check=False)
            if existing.returncode == 1:
                git(self.root, "tag", "--annotate", tag, state["candidate_sha"], "--message", tag)
            else:
                require(existing.returncode == 0, "Local tag lookup failed")
            require(git(self.root, "cat-file", "-t", "refs/tags/" + tag).stdout.strip() == "tag"
                    and git(self.root, "rev-list", "-n", "1", "refs/tags/" + tag).stdout.strip() == state["candidate_sha"],
                    "Existing tag is not the exact annotated qualified tag")
            require(self._origin() == destination, "Origin push destination changed before submission")
            # An explicit refspec still inherits push.followTags, which could
            # publish unrelated reachable annotations under this authorization.
            git(self.root, "push", "--no-follow-tags", destination, f"refs/tags/{tag}:refs/tags/{tag}")
            return {}
        require(action == "github-release", "Unknown release action")
        manifest = self.check_bundle(state)
        self._tag(state)
        tag = manifest["tag"]
        notes = self._notes(state)
        files = [Path(state["qualification"]["bundle"]) / "dist" / a["filename"] for a in manifest["artifacts"]]
        files.append(Path(state["qualification"]["bundle"]) / "SHA256SUMS")
        release = self._release(tag)
        if release is None:
            command = ["gh", "release", "create", tag, "--repo", self.repository, "--verify-tag", "--latest",
                       "--target", state["candidate_sha"], "--title", tag, "--notes-file", str(notes), *map(str, files)]
        else:
            self._release_metadata(state, release)
            names = set(self._release_assets(state, release))
            missing = [str(p) for p in files if p.name not in names]
            if not missing:
                return {"release_id": release["id"]}
            command = ["gh", "release", "upload", tag, "--repo", self.repository, *missing]
        result = subprocess.run(command, capture_output=True, text=True, env={**os.environ, "GH_TOKEN": self.token})
        require(result.returncode == 0, "GitHub release write outcome requires reconciliation")
        return {}

    def _run(self, state: dict, action: str, pending: dict) -> dict | None:
        workflow, name = WORKFLOWS[action]
        started = hosted.timestamp(pending["started_at"]).replace(microsecond=0)
        returned = pending.get("response", {}).get("workflow_run_id")
        if returned is not None:
            require(type(returned) is int and returned > 0 and returned not in pending["before"]["run_ids"],
                    "Dispatch response does not identify a fresh run")
            run_id = returned
        else:
            rows = self.client.list(f"/actions/workflows/{workflow}/runs?event=workflow_dispatch", "workflow_runs")
            matches = [r for r in rows if r["id"] not in pending["before"]["run_ids"]
                       and r.get("head_sha") == state["candidate_sha"] and r.get("head_branch") == "main"
                       and hosted.timestamp(r["created_at"]) >= started]
            require(len(matches) <= 1, "Ambiguous workflow dispatch; no automatic retry")
            if not matches:
                return None
            run_id = matches[0]["id"]
        require(type(run_id) is int and run_id > 0, "Invalid workflow run identity")
        try:
            run = self.client.get(f"/actions/runs/{run_id}")
        except automation.APIError as exc:
            if exc.status == 404:
                return None
            raise
        require(run.get("id") == run_id and started <= hosted.timestamp(run["created_at"])
                and hosted.timestamp(run["created_at"]).timestamp()
                <= datetime.now(timezone.utc).timestamp() + 30, "Workflow run identity or timestamp differs")
        require(run.get("head_sha") == state["candidate_sha"] and run.get("head_branch") == "main"
                and run.get("event") == "workflow_dispatch" and run.get("path", "").partition("@")[0] == ".github/workflows/" + workflow
                and run.get("name") == name and run.get("run_attempt") == 1
                and run.get("repository", {}).get("full_name") == self.repository
                and run.get("head_repository", {}).get("full_name") == self.repository,
                "Observed dispatch identity differs")
        if run["status"] != "completed":
            return run
        atomic(self.work / f"observed-run-{run['id']}-{run['run_attempt']}.json", run)
        if run["conclusion"] != "success":
            return run
        q.validate_workflow_run(run, repository=self.repository, workflow_path=".github/workflows/" + workflow,
                                workflow_name=name, workflow_ref="refs/heads/main", workflow_revision=state["candidate_sha"],
                                event="workflow_dispatch", candidate_sha=state["candidate_sha"])
        require(run["run_attempt"] == 1, "A rerun cannot silently replace the dispatched attempt")
        return run

    def _artifact(self, state: dict, run: dict, name: str, producer_name: str) -> Path:
        rows = self.client.list(f"/actions/runs/{run['id']}/artifacts", "artifacts")
        artifacts = [a for a in rows if a["name"] == name and not a["expired"]]
        jobs = self.client.list(f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", "jobs")
        producers = [j for j in jobs if j["name"] == producer_name]
        require(len(artifacts) == len(producers) == 1, "Missing or ambiguous evidence producer")
        artifact, producer = artifacts[0], producers[0]
        limit = hosted.MAX_EXPANDED if name == "qualified-release" else hosted.MAX_ARCHIVE
        require(type(artifact.get("size_in_bytes")) is int and 0 < artifact["size_in_bytes"] <= limit,
                "Artifact transport size exceeds bound")
        require(producer["conclusion"] == "success" and producer["head_sha"] == state["candidate_sha"]
                and producer["run_id"] == run["id"] and producer["run_attempt"] == run["run_attempt"], "Evidence producer identity differs")
        require(artifact["workflow_run"]["id"] == run["id"] and artifact["workflow_run"]["head_sha"] == state["candidate_sha"]
                and artifact["workflow_run"]["repository_id"] == run["repository"]["id"]
                and artifact["workflow_run"]["head_repository_id"] == run["head_repository"]["id"], "Evidence repository identity differs")
        require(hosted.timestamp(producer["started_at"]) <= hosted.timestamp(artifact["created_at"])
                <= hosted.timestamp(artifact["updated_at"]) <= hosted.timestamp(producer["completed_at"]), "Evidence is outside the producer attempt")
        folder = safe(self.work / f"{name}-{run['id']}-{run['run_attempt']}")
        if folder.exists():
            cached = read(folder / "transport.json")
            require(cached["artifact"] == artifact, "Remote artifact identity changed")
            archive_path = safe(folder / "artifact.zip")
            metadata = archive_path.lstat()
            require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
                    and metadata.st_size == artifact["size_in_bytes"], "Retained artifact transport identity differs")
            with archive_path.open("rb") as stream:
                raw = stream.read(artifact["size_in_bytes"] + 1)
        else:
            raw = (self.client.qualified_bundle_archive(artifact, run, producer) if name == "qualified-release"
                   else self.client.archive(artifact["id"]))
        require(len(raw) == artifact["size_in_bytes"] and "sha256:" + digest(raw) == artifact["digest"], "Artifact transport differs")
        inventory = (hosted.qualified_bundle_inventory(raw, repository=self.repository, artifact=artifact, run=run, producer=producer)
                     if name == "qualified-release" else hosted.zip_inventory(raw))
        materialized = False
        if not folder.exists():
            staging = folder.with_name(folder.name + ".incomplete-" + uuid.uuid4().hex)
            staging.mkdir()
            (staging / "artifact.zip").write_bytes(raw)
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for member, expected in inventory.items():
                    data = archive.read(member)
                    require(digest(data) == expected, "Artifact member differs")
                    path = staging / "files" / member
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
            atomic(staging / "transport.json", {"artifact": artifact, "inventory": inventory})
            sync_artifact_cache(staging, inventory)
            os.rename(staging, folder)
            materialized = True
        for member, expected in inventory.items():
            require(q.sha256_file(safe(folder / "files" / member)) == expected, "Retained artifact member changed")
        if not materialized:
            sync_artifact_cache(folder, inventory)
        sync_directory(folder.parent)
        return folder / "files"

    def reconcile(self, state: dict, pending: dict) -> dict | None:
        action = pending["action"]
        if action == "tag":
            tag = "v" + state["version"]
            checked = self._tag(state, allow_absent=True)
            if checked is None:
                return {"retry_safe": True}
            refs = {"refs/tags/" + tag: checked["object_sha"],
                    "refs/tags/" + tag + "^{}": checked["source_sha"]}
            return {"verified": True, "candidate_sha": state["candidate_sha"], "refs": refs}
        if action == "github-release":
            self._tag(state)
            release = self._release("v" + state["version"])
            if release is None:
                return {"retry_safe": True}
            self._release_metadata(state, release)
            expected, assets = self._assets(state), self._release_assets(state, release)
            if set(assets) != set(expected):
                return {"retry_safe": True}
            return {"verified": True, "candidate_sha": state["candidate_sha"], "release_id": release["id"], "url": release["html_url"]}
        try:
            run = self._run(state, action, pending)
            if run is None:
                return None
            if run["status"] != "completed":
                jobs = self.client.list(f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", "jobs")
                return {"pending": True, "run_id": run["id"], "attempt": run["run_attempt"],
                        "status": run["status"], "active_jobs": [j["name"] for j in jobs if j["status"] != "completed"],
                        "failed_jobs": [j["name"] for j in jobs if j["conclusion"] == "failure"]}
        except automation.APIError as exc:
            if exc.status not in {502, 503, 504}:
                raise
            # Only the run and jobs reads are retried, at the existing watch interval.
            return {"pending": True, "observation": "remote-observation-unavailable", "http_status": exc.status}
        if run["conclusion"] != "success":
            return {"failed": True, "run_id": run["id"], "attempt": run["run_attempt"],
                    "candidate_sha": state["candidate_sha"], "conclusion": run["conclusion"]}
        if action == "qualify":
            bundle = self._artifact(state, run, "qualified-release", "Assemble immutable qualified release")
            manifest = q._validate_manifest(q.load_json(bundle / "qualification-manifest.json"))
            require(manifest["workflow_run_id"] == run["id"] and manifest["qualification_context"]["run_attempt"] == run["run_attempt"]
                    and manifest["source"]["sha"] == state["candidate_sha"] and manifest["source"]["tree"] == state["candidate_tree"], "Qualified manifest binding differs")
            artifacts = {a["kind"]: a for a in manifest["artifacts"]}
            q.verify_bundle(argparse.Namespace(bundle=bundle, repository=self.repository, workflow_run_id=run["id"],
                candidate_sha=state["candidate_sha"], repository_root=self.root, verify_repository=True, check_registry=True,
                require_tag=False, wheel_sha256=artifacts["wheel"]["sha256"], sdist_sha256=artifacts["sdist"]["sha256"],
                output=self.work / "qualified-verification.json"))
            return {"verified": True, "candidate_sha": state["candidate_sha"], "version": manifest["version"],
                    "run_id": run["id"], "attempt": run["run_attempt"], "bundle": str(bundle),
                    "manifest_sha256": q.sha256_file(bundle / "qualification-manifest.json"), "artifacts": artifacts}
        folder = self._artifact(state, run, "promotion-decision", "Verify qualified promotion input")
        jobs = self.client.list(f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", "jobs")
        upload = [j for j in jobs if j["name"] == "Publish the already-qualified distributions"]
        require(len(upload) == 1 and upload[0]["conclusion"] == ("success" if action == "publish" else "skipped"), "Actual upload result differs")
        args = argparse.Namespace(manifest=Path(state["qualification"]["bundle"]) / "qualification-manifest.json",
            verification=folder / "bundle-verification.json", repository=self.repository,
            workflow_run_id=state["qualification"]["run_id"], candidate_sha=state["candidate_sha"], require_tag=action == "publish",
            rd13_evidence=["workflow-run=" + str(folder / "workflow-run-verification.json"),
                          "build-provenance=" + str(folder / "selected-attestations/build-provenance-attestations.jsonl"),
                          "sbom-attestation=" + str(folder / "selected-attestations/sbom-attestations.jsonl")],
            output=self.work / (action + "-replayed-decision.json"))
        q.finalize_promotion(args)
        require(q.load_json(args.output) == q.load_json(folder / "promotion-decision.json"), "Technical GO replay differs")
        return {"verified": True, "candidate_sha": state["candidate_sha"], "run_id": run["id"],
                "attempt": run["run_attempt"], "technical_decision": "GO", "upload": upload[0]["conclusion"]}

    def check_bundle(self, state: dict) -> dict:
        qualified = state["qualification"]
        path = safe(Path(qualified["bundle"]))
        require(path.is_relative_to(self.work), "Bundle belongs to another session")
        manifest = q._validate_manifest(q.load_json(path / "qualification-manifest.json"))
        require(q.sha256_file(path / "qualification-manifest.json") == qualified["manifest_sha256"]
                and manifest["source"]["sha"] == state["candidate_sha"] and manifest["version"] == state["version"]
                and manifest["source"]["tree"] == state["candidate_tree"] and manifest["repository"] == self.repository
                and {a["kind"]: a for a in manifest["artifacts"]} == qualified["artifacts"]
                and manifest["workflow_run_id"] == qualified["run_id"]
                and manifest["qualification_context"]["run_attempt"] == qualified["attempt"], "Immutable qualified input changed")
        for item in manifest["artifacts"]:
            require(q.sha256_file(safe(path / "dist" / item["filename"])) == item["sha256"], "Qualified distribution changed")
        sums = "".join(a["sha256"] + "  dist/" + a["filename"] + "\n" for a in manifest["artifacts"])
        require(safe(path / "SHA256SUMS").read_text(encoding="ascii") == sums,
                "Qualified checksum file changed or is not canonical")
        current = self.client.get(f"/actions/runs/{qualified['run_id']}")
        require(current["id"] == qualified["run_id"] and current["run_attempt"] == qualified["attempt"],
                "Qualification attempt was superseded")
        q.validate_workflow_run(current, repository=self.repository,
                                workflow_path=".github/workflows/release-qualification.yml",
                                workflow_name="Release qualification", workflow_ref="refs/heads/main",
                                workflow_revision=state["candidate_sha"], event="workflow_dispatch",
                                candidate_sha=state["candidate_sha"])
        return dict(manifest)

    def _notes(self, state: dict) -> Path:
        changelog = git(self.root, "show", state["candidate_sha"] + ":CHANGELOG.md").stdout
        match = re.search(r"^## \[" + re.escape(state["version"]) + r"\][^\n]*\n(.*?)(?=^## |\Z)", changelog, re.M | re.S)
        if match is None:
            raise SessionError("Committed version changelog is absent")
        path = safe(self.work / "product-notes.md")
        expected = match.group(1).strip() + "\n"
        if path.exists():
            require(path.read_text(encoding="utf-8") == expected, "Release notes changed")
        else:
            atomic_bytes(path, expected.encode("utf-8"))
        return path

    def _release(self, tag: str) -> dict | None:
        try:
            return self.client.get("/releases/tags/" + tag)
        except automation.APIError as exc:
            if exc.status == 404:
                return None
            raise

    def _tag(self, state: dict, *, allow_absent: bool = False) -> dict | None:
        """Read the selected repository, never an ambient Git fetch alias."""
        tag = "v" + state["version"]
        reference = "refs/tags/" + tag
        try:
            ref = self.client.get("/git/ref/tags/" + tag)
        except automation.APIError as exc:
            if exc.status != 404:
                raise
            if allow_absent:
                return None
            raise SessionError("Selected repository release tag is absent") from exc
        require(isinstance(ref, dict) and ref.get("ref") == reference
                and isinstance(ref.get("object"), dict) and ref["object"].get("type") == "tag",
                "Selected repository release tag is not annotated")
        object_sha = ref["object"].get("sha")
        require(isinstance(object_sha, str) and re.fullmatch(r"[0-9a-f]{40}", object_sha),
                "Selected repository annotated tag object is invalid")
        annotation = self.client.get("/git/tags/" + object_sha)
        require(isinstance(annotation, dict) and annotation.get("sha") == object_sha
                and annotation.get("tag") == tag and isinstance(annotation.get("object"), dict)
                and annotation["object"].get("type") == "commit"
                and annotation["object"].get("sha") == state["candidate_sha"],
                "Selected repository annotated tag does not target the qualified commit")
        previous = state.get("tag", {}).get("refs", {}).get(reference)
        require(previous is None or previous == object_sha,
                "Selected repository annotated tag changed after verification")
        return {"repository": self.repository, "ref": reference,
                "object_sha": object_sha, "source_sha": annotation["object"]["sha"]}

    def _release_metadata(self, state: dict, release: dict) -> None:
        require(release["tag_name"] == "v" + state["version"] and release["draft"] is False
                and release["prerelease"] is False and release["body"] == self._notes(state).read_text(encoding="utf-8"), "Existing release metadata differs")

    def _assets(self, state: dict) -> dict:
        manifest = self.check_bundle(state)
        return {**{a["filename"]: a["sha256"] for a in manifest["artifacts"]},
                "SHA256SUMS": q.sha256_file(Path(state["qualification"]["bundle"]) / "SHA256SUMS")}

    def _release_assets(self, state: dict, release: dict) -> dict:
        expected = self._assets(state)
        assets = {a["name"]: a for a in release["assets"]}
        require(set(assets) <= set(expected) and len(assets) == len(release["assets"]),
                "Unexpected or duplicate release assets")
        for name, asset in assets.items():
            require(asset["state"] == "uploaded" and asset.get("digest") == "sha256:" + expected[name],
                    "Published asset digest differs")
        return assets

    def _public_bytes(self, group: str, name: str, url: str, size: int, expected: str,
                      *, authenticated: bool = False) -> None:
        require(type(size) is int and 0 < size <= hosted.MAX_ARCHIVE, "Public file exceeds transport bound")
        require(group in {"github", "pypi"} and Path(name).name == name and name not in {".", ".."},
                "Invalid public download destination")
        parsed = urllib.parse.urlparse(url)
        require(parsed.scheme == "https" and parsed.hostname == ("api.github.com" if authenticated else "files.pythonhosted.org"),
                "Unexpected public artifact endpoint")
        token = self.token if authenticated else None
        for _ in range(5):
            status, headers, raw = hosted._http(url, token, size, media_type="application/octet-stream")
            if status == 200:
                break
            require(status in {301, 302, 303, 307, 308}, "Public artifact download failed")
            url = next((v for k, v in headers.items() if k.lower() == "location"), "")
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname or ""
            require(parsed.scheme == "https" and (host == "files.pythonhosted.org" or host.endswith(".githubusercontent.com")),
                    "Unexpected public artifact redirect")
            token = None  # Signed redirects never receive repository credentials.
        else:
            raise SessionError("Public artifact redirect bound exceeded")
        require(len(raw) == size and digest(raw) == expected, "Public artifact bytes differ from qualification")
        path = safe(self.work / "public-downloads" / group / name)
        ensure_directory(path.parent)
        if path.exists():
            require(q.sha256_file(path) == expected, "Retained public download changed")
        else:
            temporary = path.with_name(path.name + ".incomplete-" + uuid.uuid4().hex)
            # Interrupted attempts are retained for diagnosis. Only fully
            # written, flushed and verified bytes acquire the final cache name.
            with temporary.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            require(q.sha256_file(temporary) == expected, "Public cache materialization differs")
            os.replace(temporary, path)
            sync_directory(path.parent)

    def verify_public(self, state: dict) -> dict:
        first_tag = self._tag(state)
        require(first_tag is not None, "Selected repository release tag is absent")
        release = self._release("v" + state["version"])
        if release is None:
            raise SessionError("Published GitHub release is absent")
        self._release_metadata(state, release)
        require(self.client.get("/releases/latest")["id"] == release["id"], "Published release is not latest")
        expected = self._assets(state)
        assets = {a["name"]: a for a in release["assets"]}
        require(len(assets) == len(release["assets"]) and set(assets) == set(expected) and all(a.get("digest") == "sha256:" + expected[n] and a["state"] == "uploaded"
                                                  for n, a in assets.items()), "Public GitHub assets differ")
        for name, asset in assets.items():
            self._public_bytes("github", name, f"https://api.github.com/repos/{self.repository}/releases/assets/{asset['id']}",
                               asset["size"], expected[name], authenticated=True)
        with urllib.request.urlopen("https://pypi.org/pypi/agent-wiki-cli/" + state["version"] + "/json", timeout=30) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
        require(len(raw) <= 4 * 1024 * 1024, "Registry response exceeds bound")
        registry = hosted._json(raw)
        distributions = {a["filename"]: a for a in registry["urls"]}
        require(len(distributions) == len(registry["urls"]) and set(distributions) == set(expected) - {"SHA256SUMS"}
                and registry["info"]["version"] == state["version"]
                and registry["info"]["name"].replace("_", "-").lower() == "agent-wiki-cli" and not registry["info"].get("yanked", False)
                and all(not a["yanked"] and a["digests"]["sha256"] == expected[n] for n, a in distributions.items()), "Public registry distributions differ")
        for name, asset in distributions.items():
            self._public_bytes("pypi", name, asset["url"], asset["size"], expected[name])
        final_tag = self._tag(state)
        require(first_tag == final_tag, "Selected repository release tag changed during public verification")
        atomic(self.work / "public-verification.json", {"registry": registry, "release": release,
                                                        "tag": final_tag, "verified_at": now()})
        return {"verified": True, "candidate_sha": state["candidate_sha"], "release_url": release["html_url"],
                "pypi_url": "https://pypi.org/project/agent-wiki-cli/" + state["version"] + "/"}


def main(argv: list[str] | None = None) -> int:
    def bounded_integer(minimum: int, maximum: int):
        def parse(value: str) -> int:
            try:
                number = int(value)
            except ValueError as exc:
                raise argparse.ArgumentTypeError("Expected an integer") from exc
            if not minimum <= number <= maximum:
                raise argparse.ArgumentTypeError(f"Expected {minimum}–{maximum}")
            return number
        return parse

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status", "advance", "resume", "watch", "supersede"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        command.add_argument("--work", type=Path, required=True)
        if name != "status":
            command.add_argument("--authorize", action="append", choices=ACTIONS, default=[])
        if name in {"init", "advance", "resume", "watch"}:
            command.add_argument("--preflight-receipt", type=Path)
        if name == "init":
            command.add_argument("--repository", default="Denissvgn/python-wiki-llm")
            command.add_argument("--candidate-sha", required=True)
        if name == "supersede":
            command.add_argument("--reason", required=True)
        if name == "watch":
            command.add_argument("--interval", type=bounded_integer(5, 60), default=30,
                                 help="Seconds between observations (5–60; default: 30)")
            command.add_argument("--max-polls", type=bounded_integer(1, 2880), default=720,
                                 help="Observation budget (1–2880; default: 720, six hours at 30 seconds)")
    args = parser.parse_args(argv)
    try:
        root = safe(args.root)
        work = args.work if args.work.is_absolute() else root / args.work
        store = Store(root, work)
        controller = Controller(store)
        if args.command == "init":
            value = controller.initialize(args.repository, args.candidate_sha, receipt=args.preflight_receipt,
                                          authorize=tuple(args.authorize))
        elif args.command == "status":
            value = store.load()
        elif args.command == "supersede":
            value = controller.supersede(args.reason)
        else:
            state = store.load()
            granted = set(state["authorizations"]) | set(args.authorize)
            if state["phase"] in FINISHED or (not state["pending"] and state["phase"] in NEXT
                                              and NEXT[state["phase"]] not in granted):
                value = controller.advance(tuple(args.authorize), args.preflight_receipt)
                print(json.dumps(value, sort_keys=True))
                return 0
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if not token:
                token = subprocess.check_output(["gh", "auth", "token", "--hostname", "github.com"], text=True).strip()
            require(token, "Existing Actions-read/release authorization credential is required")
            os.environ["GITHUB_TOKEN"] = token
            controller.backend = GitHubBackend(store.root, store.work, state["repository"], token)
            polls = args.max_polls if args.command == "watch" else 1
            interval = args.interval if args.command == "watch" else 0
            require(1 <= polls <= 2880 and 0 <= interval <= 60, "Observation bounds exceeded")
            require(args.command != "watch" or interval >= 5, "Watch interval must be at least five seconds")
            previous = None
            finished = False
            for index in range(polls):
                value = controller.advance(tuple(args.authorize), args.preflight_receipt if index == 0 else None)
                stamp = (value["revision"], value.get("observation"), value.get("remote"))
                if stamp != previous:
                    print(json.dumps(value, sort_keys=True), flush=True)
                    previous = stamp
                if value["phase"] in FINISHED or value.get("observation") in {"awaiting_authorization", "authorized-scope-complete", "remote-failed", "preparation-blocked"}:
                    finished = True
                    break
                if index + 1 < polls:
                    time.sleep(interval)
            if args.command == "watch" and not finished:
                print(json.dumps({**value, "observation": "observation-budget-exhausted"}, sort_keys=True))
            return 2 if value.get("observation") in {"remote-failed", "preparation-blocked"} else 0
        print(json.dumps(value, sort_keys=True))
        return 0
    except (SessionError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print("Manual release blocked: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
