"""Trusted, stdlib-only reconciliation of policy activation and qualification.

The controller never installs or executes a downloaded candidate. Reads use the
job's GITHUB_TOKEN; mutation requires the separate RELEASE_AUTOMATION_TOKEN.
Check-run receipts make interrupted dispatches visible rather than guessing
which of several hosted runs belongs to a request.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
import urllib.error
import urllib.parse
import urllib.request
import zipfile

# The workflow executes this trusted checkout with isolated Python; imports
# must not depend on the current working directory or environment PYTHONPATH.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release import hosted_evidence as hosted
from release import knowledge_maintenance as maintenance
from release import qualification

SCHEMA = "agent-wiki-release-automation/v1"
CONFIG_SCHEMA = "agent-wiki-release-automation-config/v1"
CHECK = "Release automation"
CI_PATH = ".github/workflows/ci.yml"
QUALIFICATION_PATH = ".github/workflows/release-qualification.yml"
REQUIRED_CHECKS = {"CI complete", "Release activation proof"}
AUDIT_PREFIX = "release/policy-activations/"
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_JSON = 4 * 1024 * 1024


class AutomationError(ValueError):
    """An authenticated state cannot be advanced safely."""


class APIError(AutomationError):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


def require(condition: object, message: str) -> None:
    if not condition:
        raise AutomationError(message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def strict(raw: bytes) -> Any:
    return hosted._json(raw)


class GitHubClient:
    """Bounded repository API client with injectable transport for offline tests."""

    def __init__(self, repository: str, token: str, *, write: bool = False):
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "invalid repository")
        require(token, "GitHub read credentials are unavailable")
        self.root = f"https://api.github.com/repos/{repository}"
        self.token = token
        self.write = write

    def request(self, method: str, path: str, payload: object = None) -> Any:
        require(path.startswith("/") and "\n" not in path, "invalid API path")
        require(method == "GET" or self.write, "read credentials cannot mutate repository")
        request = urllib.request.Request(self.root + path,
            data=None if payload is None else canonical(payload), method=method,
            headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {self.token}",
                "User-Agent": "agent-wiki-release-automation", "X-GitHub-Api-Version": "2026-03-10",
                "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(MAX_JSON + 1)
                require(len(raw) <= MAX_JSON, "GitHub JSON response is oversized")
                return strict(raw) if raw else None
        except urllib.error.HTTPError as exc:
            exc.close()
            raise APIError(exc.code, f"GitHub {method} {path} returned {exc.code}") from exc
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise AutomationError(f"GitHub {method} {path} unavailable") from exc

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def enable_auto_merge(self, pull_request_id: str, head_sha: str) -> dict:
        require(self.write, "read credentials cannot enable auto-merge")
        require(isinstance(pull_request_id, str) and 0 < len(pull_request_id) <= 256, "invalid pull request node identity")
        require(isinstance(head_sha, str) and SHA.fullmatch(head_sha), "invalid auto-merge head")
        request = urllib.request.Request("https://api.github.com/graphql", method="POST",
            data=canonical({
                "query": "mutation($id:ID!,$head:GitObjectID!){enablePullRequestAutoMerge(input:{pullRequestId:$id,expectedHeadOid:$head,mergeMethod:SQUASH}){pullRequest{id headRefOid merged mergeCommit{oid} autoMergeRequest{mergeMethod}}}}",
                "variables": {"id": pull_request_id, "head": head_sha},
            }),
            headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json", "User-Agent": "agent-wiki-release-automation"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(MAX_JSON + 1)
                require(len(raw) <= MAX_JSON, "auto-merge response is oversized")
                value = strict(raw)
            require(isinstance(value, dict) and not value.get("errors"), "GitHub did not accept protected auto-merge")
            pr = value["data"]["enablePullRequestAutoMerge"]["pullRequest"]
            require(isinstance(pr, dict) and pr.get("id") == pull_request_id and pr.get("headRefOid") == head_sha, "auto-merge response identity differs")
            if pr.get("merged") is True:
                require(isinstance(pr.get("mergeCommit"), dict) and isinstance(pr["mergeCommit"].get("oid"), str)
                        and SHA.fullmatch(pr["mergeCommit"]["oid"]), "auto-merge commit identity differs")
            else:
                require(isinstance(pr.get("autoMergeRequest"), dict) and pr["autoMergeRequest"].get("mergeMethod") == "SQUASH",
                        "auto-merge was not enabled")
            return pr
        except urllib.error.HTTPError as exc:
            exc.close()
            raise AutomationError("protected auto-merge request failed") from exc
        except (OSError, urllib.error.URLError, TimeoutError, KeyError, TypeError) as exc:
            raise AutomationError("protected auto-merge could not be verified") from exc

    def list(self, path: str, key: str | None = None) -> list[dict]:
        rows: list[dict] = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 11):
            value = self.get(f"{path}{separator}per_page=100&page={page}")
            page_rows = value if key is None else value.get(key)
            require(isinstance(page_rows, list), "invalid GitHub pagination")
            rows.extend(page_rows)
            if key and "total_count" in value:
                require(type(value["total_count"]) is int and len(rows) <= value["total_count"], "inconsistent pagination")
                if len(rows) == value["total_count"]:
                    return rows
            elif len(page_rows) < 100:
                return rows
            require(page_rows, "inconsistent empty page")
        raise AutomationError("GitHub pagination bound exceeded")

    def archive(self, artifact_id: int) -> bytes:
        client = hosted.GitHub.__new__(hosted.GitHub)
        client.root, client.token = self.root, self.token
        return client.archive(artifact_id)

    def get_user(self) -> dict:
        request = urllib.request.Request("https://api.github.com/user", headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2026-03-10", "User-Agent": "agent-wiki-release-automation"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(MAX_JSON + 1)
                require(len(raw) <= MAX_JSON, "GitHub identity is oversized")
                return strict(raw)
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code not in {403, 404}:
                raise AutomationError("cannot authenticate automation token") from exc
            # Installation tokens may not expose the REST /user endpoint.
            # GraphQL viewer still identifies the server-authenticated actor;
            # never infer it from a supplied token name or repository access.
            query = urllib.request.Request("https://api.github.com/graphql", method="POST",
                data=canonical({"query": "query { viewer { login databaseId } }"}),
                headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {self.token}",
                         "User-Agent": "agent-wiki-release-automation", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(query, timeout=30) as response:
                    raw = response.read(MAX_JSON + 1)
                    require(len(raw) <= MAX_JSON, "GitHub actor response is oversized")
                    value = strict(raw)
                    require(not value.get("errors"), "cannot authenticate installation token actor")
                    actor = value["data"]["viewer"]
                    return {"login": actor["login"], "id": actor["databaseId"]}
            except (OSError, urllib.error.URLError, TimeoutError, KeyError, TypeError) as failure:
                if isinstance(failure, urllib.error.HTTPError):
                    failure.close()
                raise AutomationError("cannot authenticate installation token actor") from failure
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise AutomationError("cannot authenticate automation token") from exc


def load_config(root: Path) -> dict:
    value = strict((root / "release/automation.json").read_bytes())
    require(isinstance(value, dict) and set(value) == {"schema_version", "enabled", "trusted_bot"}, "invalid automation configuration")
    require(value["schema_version"] == CONFIG_SCHEMA and type(value["enabled"]) is bool, "unsupported automation configuration")
    bot = value["trusted_bot"]
    require(isinstance(bot, dict) and set(bot) == {"login", "id", "check_app_id"} and isinstance(bot["login"], str), "invalid trusted bot")
    require(bot["id"] is None or (type(bot["id"]) is int and bot["id"] > 0), "invalid trusted bot ID")
    require(bot["check_app_id"] is None or (type(bot["check_app_id"]) is int and bot["check_app_id"] > 0), "invalid trusted check publisher")
    return value


def inspect(root: Path, *, read_bytes=None) -> dict:
    """Distinguish malformed bindings from valid stale bindings without execution."""
    reader = read_bytes or (lambda name: (root / name).read_bytes())
    try:
        raw = reader(maintenance.POLICY_PATH)
        config = strict(raw)
        require(isinstance(config, dict), "policy configuration must be an object")
        digest = (maintenance.composite_policy_digest(reader) if config.get("schema_version") == maintenance.CONFIG_V2_SCHEMA
                  else hashlib.sha256(reader(maintenance.LEAF_PATH)).hexdigest())
        checked = maintenance.policy(raw, implementation_hash=digest, policy_shadow=True)
        require(config["mode"] == "required", "automatic renewal requires mode=required")
        checked["mode"] = "required"
        current = config["activation"]["implementation_sha256"] == digest
        return {"schema_version": SCHEMA, "status": "current" if current else "stale", "implementation_sha256": digest, "configuration": checked}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"schema_version": SCHEMA, "status": "blocked_policy", "reason": str(exc)}


def eligibility(root: Path) -> dict:
    return qualification.release_eligibility(root, check_registry=True)


def request_id(repository: str, candidate: str, profile: str, generation: int = 0) -> str:
    require(SHA.fullmatch(candidate), "invalid candidate SHA")
    require(profile in {"normal", "policy-shadow"}, "invalid qualification profile")
    require(type(generation) is int and generation >= 0, "invalid retry generation")
    # Options are explicit and fixed by the controller, so a receipt cannot be
    # reused for a differently configured experiment.
    key = {"repository": repository, "candidate_sha": candidate, "profile": profile, "retry_generation": generation,
           "options": qualification_inputs(candidate, profile, "")}
    return hashlib.sha256(canonical(key)).hexdigest()


def qualification_inputs(candidate: str, profile: str, identifier: str) -> dict:
    return {"candidate-sha": candidate,
            "knowledge-policy-shadow": "true" if profile == "policy-shadow" else "false",
            "discovery-mode": "false", "bandit-parity-verification": "false", "ubuntu-suite-shadow": "false",
            "windows-core-shards": "true", "third-party-download-cache": "false",
            "dependency-setup-verification": "false", "automation-request-id": identifier}


class Coordinator:
    def __init__(self, root: Path, repository: str, client: Any, *, writer: Any = None, apply=False,
                 config=None, shadow_verifier=None, bundle_verifier=None, eligibility_check=None):
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "invalid repository")
        self.root, self.repository, self.client = root, repository, client
        self.writer, self.apply = writer, apply
        self.config = config if config is not None else load_config(root)
        self.shadow_verifier = shadow_verifier
        self.bundle_verifier = bundle_verifier
        self.eligibility_check = eligibility_check or eligibility

    def result(self, status: str, **values) -> dict:
        return {"schema_version": SCHEMA, "repository": self.repository, "status": status, **values}

    def content(self, path: str, ref: str) -> bytes:
        value = self.client.get(f"/contents/{urllib.parse.quote(path, safe='/')}?ref={urllib.parse.quote(ref, safe='')}")
        require(value.get("type") == "file" and value.get("encoding") == "base64" and value.get("size", MAX_JSON + 1) <= MAX_JSON,
                "missing, redirected or oversized repository input")
        raw = base64.b64decode(value["content"], validate=False)
        require(len(raw) == value["size"], "repository input length mismatch")
        return raw

    def main(self) -> str:
        ref = self.client.get("/git/ref/heads/main")
        require(ref.get("ref") == "refs/heads/main" and ref.get("object", {}).get("type") == "commit", "invalid main ref")
        sha = ref["object"]["sha"]
        require(isinstance(sha, str) and SHA.fullmatch(sha), "invalid main SHA")
        return sha

    def policy_at(self, sha: str) -> dict:
        return inspect(self.root, read_bytes=lambda path: self.content(path, sha))

    def setup(self) -> dict | None:
        if not self.config["enabled"]:
            return self.result("blocked_setup", reason="Automation is disabled; configure the bot and protection, then enable and resume.")
        bot = self.config["trusted_bot"]
        if not bot["login"] or not bot["id"] or type(bot.get("check_app_id")) is not int or bot["check_app_id"] <= 0 or (self.apply and self.writer is None):
            return self.result("blocked_setup", reason="Configure trusted_bot login, id, check_app_id and RELEASE_AUTOMATION_TOKEN; no fallback token is used.")
        try:
            repository = self.client.get("/")
            require(repository.get("full_name") == self.repository and repository.get("allow_auto_merge") is True, "enable repository auto-merge")
            if self.apply:
                identity = self.writer.get_user()
                require(identity.get("login") == bot["login"] and identity.get("id") == bot["id"], "automation token is not the configured bot")
            # Detailed bypass metadata requires Administration(read), which
            # the ordinary workflow GITHUB_TOKEN cannot be granted. The bot
            # uses that read capability only; it never edits protection.
            rules_client = self.writer if self.apply else self.client
            rules = rules_client.list("/rulesets?includes_parents=true")
            applicable = []
            for summary in rules:
                rule = rules_client.get(f"/rulesets/{summary['id']}")
                if rule.get("enforcement") != "active" or rule.get("target") != "branch":
                    continue
                names = rule.get("conditions", {}).get("ref_name", {})
                includes = names.get("include", [])
                excludes = names.get("exclude", [])
                if any(x in {"refs/heads/main", "~DEFAULT_BRANCH", "~ALL"} for x in includes) and not excludes:
                    applicable.append(rule)
            require(applicable, "an active main ruleset is required")
            require(all("bypass_actors" in x and isinstance(x["bypass_actors"], list) for x in applicable),
                    "ruleset bypass metadata is unavailable; grant the bot Administration(read)")
            require(all(not x["bypass_actors"] for x in applicable), "automation cannot use protection bypass")
            checks = set()
            strict_checks = False
            protections = set()
            for rule in applicable:
                for item in rule.get("rules", []):
                    protections.add(item.get("type"))
                    if item.get("type") == "required_status_checks":
                        params = item.get("parameters", {})
                        if params.get("strict_required_status_checks_policy") is True:
                            strict_checks = True
                            checks.update(x.get("context") for x in params.get("required_status_checks", []))
            require(strict_checks and REQUIRED_CHECKS <= checks, "require CI complete and Release activation proof with up-to-date checks")
            require("pull_request" in protections, "main must require pull requests")
            require({"non_fast_forward", "deletion"} <= protections, "main must prevent force pushes and deletion")
        except (AutomationError, KeyError, TypeError) as exc:
            return self.result("blocked_setup", reason=str(exc))
        return None

    def authenticate(self, event: dict) -> dict:
        payload = event.get("workflow_run")
        if not isinstance(payload, dict):
            raise AutomationError("completed workflow_run event is required")
        run_id, attempt = payload.get("id"), payload.get("run_attempt")
        require(type(run_id) is int and run_id > 0 and type(attempt) is int and attempt > 0, "invalid event run identity")
        run = self.client.get(f"/actions/runs/{run_id}/attempts/{attempt}")
        require(run.get("id") == run_id and run.get("run_attempt") == attempt, "run attempt mismatch")
        current_run = self.client.get(f"/actions/runs/{run_id}")
        require(current_run.get("id") == run_id and current_run.get("run_attempt") == attempt, "workflow attempt was superseded by a rerun")
        require(run.get("repository", {}).get("full_name") == self.repository and run.get("head_repository", {}).get("full_name") == self.repository,
                "workflow run repository mismatch")
        workflow = self.client.get(f"/actions/workflows/{run.get('workflow_id')}")
        path = str(run.get("path", "")).split("@", 1)[0]
        require(path == workflow.get("path"), "workflow path mismatch")
        require((path, run.get("name"), workflow.get("name")) in {(CI_PATH, "CI", "CI"), (QUALIFICATION_PATH, "Release qualification", "Release qualification")}, "unexpected workflow identity")
        require(run.get("status") == "completed", "workflow is not completed")
        sha = run.get("head_sha")
        require(isinstance(sha, str) and SHA.fullmatch(sha), "invalid run head SHA")
        require(payload.get("head_sha") == sha and payload.get("workflow_id") == run.get("workflow_id"), "event/API identity mismatch")
        if path == CI_PATH:
            require((run.get("event"), run.get("head_branch")) == ("push", "main") or run.get("event") == "pull_request", "untrusted CI event/ref")
        else:
            if run.get("conclusion") == "success":
                qualification.validate_workflow_run(run, repository=self.repository, workflow_path=QUALIFICATION_PATH,
                    workflow_name="Release qualification", workflow_ref="refs/heads/codex/qualification/" + sha,
                    workflow_revision=sha, event="workflow_dispatch", candidate_sha=sha)
            else:
                require(
                    run.get("event") == "workflow_dispatch" and run.get("head_branch") == "codex/qualification/" + sha, "untrusted qualification event/ref")
        return run

    def ci_success(self, sha: str) -> bool:
        runs = self.client.list(f"/actions/workflows/ci.yml/runs?head_sha={sha}&event=push", "workflow_runs")
        # Latest attempt of a matching run governs readiness; an old success
        # cannot mask its failed rerun.
        for summary in sorted(runs, key=lambda x: x.get("id", 0), reverse=True):
            if summary.get("status") != "completed":
                return False
            run = self.authenticate({"workflow_run": summary})
            if run.get("event") == "push" and run.get("head_branch") == "main":
                return run.get("conclusion") == "success"
        return False

    def receipts(self, sha: str) -> list[dict]:
        rows = self.client.list(f"/commits/{sha}/check-runs?check_name={urllib.parse.quote(CHECK)}", "check_runs")
        result = []
        for row in rows:
            if (row.get("name") != CHECK or row.get("head_sha") != sha
                    or row.get("app", {}).get("id") != self.config["trusted_bot"].get("check_app_id")
                    or row.get("app", {}).get("slug") == "github-actions"):
                continue
            try:
                value = strict(row.get("output", {}).get("text", "").encode())
                require(value.get("schema_version") == SCHEMA and value.get("repository") == self.repository
                        and value.get("request_id") == row.get("external_id")
                        and value["request_id"] == request_id(self.repository, sha, value["profile"], value.get("generation", 0)), "untrusted dispatch receipt")
                value["check_run_id"] = row["id"]
                result.append(value)
            except (ValueError, KeyError, TypeError):
                continue
        return result

    def save(self, receipt: dict) -> dict:
        if not self.apply:
            return receipt
        payload = {"name": CHECK, "head_sha": receipt["candidate_sha"], "external_id": receipt["request_id"],
                   "status": "completed", "conclusion": "neutral", "output": {"title": receipt["status"],
                   "summary": receipt.get("reason", receipt["status"]), "text": canonical({k: v for k, v in receipt.items() if k != "check_run_id"}).decode()}}
        if receipt.get("check_run_id"):
            payload.pop("head_sha")
            value = self.writer.request("PATCH", f"/check-runs/{receipt['check_run_id']}", payload)
        else:
            value = self.writer.request("POST", "/check-runs", payload)
        require(value.get("app", {}).get("id") == self.config["trusted_bot"]["check_app_id"]
                and value.get("app", {}).get("slug") != "github-actions"
                and value.get("head_sha") == receipt["candidate_sha"] and value.get("external_id") == receipt["request_id"], "dispatch receipt publisher differs from configured authority")
        receipt["check_run_id"] = value["id"]
        return receipt

    def dispatch(self, sha: str, profile: str, *, retry=False) -> dict:
        existing = [x for x in self.receipts(sha) if x["candidate_sha"] == sha and x["profile"] == profile]
        require(len(existing) <= 1, "ambiguous dispatch receipts")
        generation = 0
        history = []
        if existing:
            prior = existing[0]
            if not retry or prior["status"] not in {"failed", "blocked_evidence"}:
                return prior
            generation = prior.get("generation", 0) + 1
            history = [*prior.get("previous_runs", []), {"run_id": prior.get("run_id"), "request_id": prior["request_id"], "generation": prior.get("generation", 0)}][-16:]
        identifier = request_id(self.repository, sha, profile, generation)
        receipt = self.result("planned_dispatch", candidate_sha=sha, profile=profile, request_id=identifier, generation=generation, previous_runs=history)
        if existing:
            receipt["check_run_id"] = existing[0]["check_run_id"]
        if not self.apply:
            return receipt
        require(self.main() == sha, "main advanced before candidate pinning")
        ref_name = "codex/qualification/" + sha
        try:
            ref = self.client.get("/git/ref/heads/" + ref_name)
            require(ref.get("ref") == "refs/heads/" + ref_name and ref.get("object", {}).get("type") == "commit" and ref.get("object", {}).get("sha") == sha,
                    "candidate pin exists at a different revision")
        except APIError as exc:
            if exc.status != 404:
                raise
            self.writer.request("POST", "/git/refs", {"ref": "refs/heads/" + ref_name, "sha": sha})
        # Persist before dispatch. If a network interruption hides the API's
        # response, automatic retries must not launch duplicate expensive runs.
        receipt["status"] = "dispatch_pending"
        self.save(receipt)
        try:
            require(self.main() == sha, "main advanced before qualification dispatch")
            response = self.writer.request("POST", "/actions/workflows/release-qualification.yml/dispatches",
                {"ref": ref_name, "inputs": qualification_inputs(sha, profile, identifier)})
            run_id = response.get("workflow_run_id") if isinstance(response, dict) else None
            require(type(run_id) is int and run_id > 0, "dispatch response omitted exact workflow run ID")
            receipt.update(status="dispatched", run_id=run_id, attempt=1)
        except (AutomationError, TypeError) as exc:
            receipt.update(status="blocked_dispatch_unknown", reason=str(exc))
        return self.save(receipt)

    def start(self, sha: str, *, retry=False) -> dict:
        require(self.main() == sha, "candidate is no longer current main")
        checked_out = qualification._run(["git", "rev-parse", "HEAD"], cwd=self.root).stdout.strip()
        require(checked_out == sha, "trusted checkout must match current CI-approved main")
        state = self.policy_at(sha)
        if state["status"] not in {"current", "stale"}:
            return self.result("blocked_policy", candidate_sha=sha, reason=state.get("reason"))
        if state["status"] == "stale":
            digest = state["implementation_sha256"]
            branch = "codex/policy-activation/" + digest
            pulls = self.client.list(f"/pulls?state=open&head={urllib.parse.quote(self.repository.split('/')[0] + ':' + branch)}")
            matching = [x for x in pulls if x.get("head", {}).get("ref") == branch]
            require(len(matching) <= 1, "ambiguous existing activation proposal")
            if matching:
                pr = matching[0]
                require(self.is_bot(pr.get("user", {})) and pr.get("base", {}).get("ref") == "main", "activation PR is not trusted")
                activation = strict(self.content(maintenance.POLICY_PATH, pr["head"]["sha"]))["activation"]
                saved = [x for x in self.receipts(maintenance.activation_source_sha(activation)) if x["profile"] == "policy-shadow" and x.get("run_id") == activation["run_id"]]
                require(len(saved) == 1 and saved[0].get("activation_head") == pr["head"]["sha"], "existing activation proposal is not receipt-owned")
                verified = self._verify_activation(activation)
                return self.activation_proposal(verified, sha, saved[0])
            return self.dispatch(sha, "policy-shadow", retry=retry)
        # Eligibility uses a nonexecuting local checkout at the exact SHA.
        # A privileged runner may not check out or execute candidate code.
        ready = self.eligibility_check(self.root)
        if ready["status"] != "eligible":
            return self.result(ready["status"], candidate_sha=sha, version=ready.get("version"), reason=ready.get("reason"))
        return self.dispatch(sha, "normal", retry=retry)

    def find_request(self, run: dict) -> dict:
        saved = self.receipts(run["head_sha"])
        if any(previous.get("run_id") == run["id"] for value in saved for previous in value.get("previous_runs", [])):
            return self.result("superseded", candidate_sha=run["head_sha"], reason="completion belongs to an explicitly retried request")
        rows = [x for x in saved if x.get("run_id") == run["id"]]
        if not rows:
            pending = [x for x in saved if x.get("status") in {"dispatch_pending", "blocked_dispatch_unknown"}
                       and run.get("display_title") == f"Release qualification [{x['request_id']}]" ]
            require(len(pending) == 1, "unknown dispatch has no unique request correlation")
            recovered = self.recover_dispatch(pending[0])
            require(recovered.get("run_id") == run["id"], "unknown dispatch matches another run")
            rows = [recovered]
        require(len(rows) == 1, "qualification run has no unique dispatch receipt")
        receipt = rows[0]
        require(receipt["candidate_sha"] == run["head_sha"] and receipt["request_id"] == request_id(self.repository, run["head_sha"], receipt["profile"], receipt.get("generation", 0)), "dispatch options mismatch")
        require(run.get("display_title") == f"Release qualification [{receipt['request_id']}]", "qualification request correlation differs")
        return receipt

    def recover_dispatch(self, receipt: dict) -> dict:
        """Recover a lost response using a unique authenticated request title."""
        sha = receipt["candidate_sha"]
        require(receipt["request_id"] == request_id(self.repository, sha, receipt["profile"], receipt.get("generation", 0)), "unknown dispatch options differ")
        runs = self.client.list(f"/actions/workflows/release-qualification.yml/runs?head_sha={sha}&event=workflow_dispatch", "workflow_runs")
        matched = [x for x in runs if x.get("display_title") == f"Release qualification [{receipt['request_id']}]" ]
        if not matched:
            return receipt
        require(len(matched) == 1, "ambiguous runs for interrupted dispatch; no automatic retry")
        run = self.client.get(f"/actions/runs/{matched[0]['id']}")
        require(run.get("repository", {}).get("full_name") == self.repository and run.get("head_repository", {}).get("full_name") == self.repository
                and run.get("head_sha") == sha and run.get("head_branch") == "codex/qualification/" + sha
                and run.get("event") == "workflow_dispatch" and run.get("path", "").split("@", 1)[0] == QUALIFICATION_PATH
                and run.get("display_title") == f"Release qualification [{receipt['request_id']}]", "interrupted dispatch run identity differs")
        receipt.update(status="dispatched", run_id=run["id"], attempt=run["run_attempt"])
        return self.save(receipt)

    def shadow(self, run: dict, receipt: dict) -> dict:
        if self.shadow_verifier is None:
            from release.policy_activation import verify_shadow
            verifier = verify_shadow
        else:
            verifier = self.shadow_verifier
        latest = self.main()
        current = self.policy_at(latest)
        require(current["status"] in {"current", "stale"}, "current main policy is malformed")
        candidate_policy = self.policy_at(run["head_sha"])
        require(candidate_policy["status"] in {"current", "stale"}, "shadow candidate policy is malformed")
        from release.policy_activation import configuration_contract
        if (candidate_policy["implementation_sha256"] != current["implementation_sha256"]
                or configuration_contract(candidate_policy["configuration"]) != configuration_contract(current["configuration"])):
            receipt.update(status="superseded", reason="main policy implementation or configuration changed after the shadow candidate")
            self.save(receipt)
            return self.start(latest) if self.ci_success(latest) else self.result("waiting_ci", candidate_sha=latest)
        verified = verifier(self.repository, run["id"], run["run_attempt"], run["head_sha"], self.root,
                            client=self.client, request_id=receipt["request_id"])
        if verified["activation"]["implementation_sha256"] != current["implementation_sha256"]:
            receipt.update(status="superseded", reason="main policy changed after the shadow candidate")
            self.save(receipt)
            if self.ci_success(latest):
                return self.start(latest)
            return self.result("waiting_ci", candidate_sha=latest)
        return self.activation_proposal(verified, latest, receipt)

    def activation_proposal(self, verified: dict, main_sha: str, receipt: dict) -> dict:
        require(qualification._run(["git", "rev-parse", "HEAD"], cwd=self.root).stdout.strip() == main_sha,
                "trusted checkout must match main before proposing activation")
        state = self.policy_at(main_sha)
        activation, audit = verified["activation"], verified["audit"]
        require(state["status"] in {"current", "stale"} and state["implementation_sha256"] == activation["implementation_sha256"], "activation is superseded")
        require(audit.get("repository") == self.repository and audit.get("implementation_sha256") == activation["implementation_sha256"], "audit differs from authenticated activation")
        from release.policy_activation import configuration_contract
        evaluated = strict(self.content(maintenance.POLICY_PATH, maintenance.activation_source_sha(activation)))
        require(configuration_contract(state["configuration"]) == configuration_contract(evaluated)
                == audit.get("configuration"), "activation proof configuration is superseded")
        config = state["configuration"]
        if config["activation"] == activation:
            receipt.update(status="activation_merged", reason="verified activation is already on main")
            return self.save(receipt)
        config["activation"] = activation
        digest = activation["implementation_sha256"]
        branch = "codex/policy-activation/" + digest
        files = {maintenance.POLICY_PATH: canonical(config), AUDIT_PREFIX + digest + ".json": canonical(audit)}
        prs = self.client.list(f"/pulls?state=open&head={urllib.parse.quote(self.repository.split('/')[0] + ':' + branch)}")
        require(len(prs) <= 1, "ambiguous activation PR")
        for pr in prs:
            require(self.is_bot(pr.get("user", {})) and pr.get("base", {}).get("ref") == "main", "activation branch belongs to an untrusted PR")
            if (receipt.get("activation_head") == pr.get("head", {}).get("sha")
                    and receipt.get("activation_base") == main_sha
                    and all(self.content(path, pr["head"]["sha"]) == raw for path, raw in files.items())):
                return receipt
        if not self.apply:
            return self.result("planned_activation_pr", candidate_sha=main_sha, request_id=receipt["request_id"], files=list(files))
        require(self.main() == main_sha, "main advanced before activation proposal")
        old_ref = None
        try:
            old_ref = self.client.get("/git/ref/heads/" + branch)
        except APIError as exc:
            if exc.status != 404:
                raise
        if old_ref is not None:
            expected_head = receipt.get("activation_head")
            owned_heads = {x for x in (expected_head, receipt.get("activation_previous_head")) if x}
            observed_head = old_ref.get("object", {}).get("sha")
            require(observed_head in owned_heads,
                    "activation ref has unowned or concurrent changes")
            require(not prs or prs[0].get("head", {}).get("sha") == observed_head,
                    "activation PR head differs from the owned receipt")
        elif prs:
            raise AutomationError("activation PR ref disappeared")
        main_commit = self.client.get("/git/commits/" + main_sha)
        tree_entries = []
        for path, raw in files.items():
            blob = self.writer.request("POST", "/git/blobs", {"content": base64.b64encode(raw).decode(), "encoding": "base64"})
            tree_entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        tree = self.writer.request("POST", "/git/trees", {"base_tree": main_commit["tree"]["sha"], "tree": tree_entries})
        commit = self.writer.request("POST", "/git/commits", {"message": "Renew verified repository policy activation", "tree": tree["sha"], "parents": [main_sha]})
        require(self.main() == main_sha, "main advanced before activation ref update")
        # Keep the intended ref target before mutation so a partially created
        # proposal can be recovered without taking ownership of arbitrary refs.
        previous_head = old_ref.get("object", {}).get("sha") if old_ref else None
        receipt.update(status="activation_proposal_pending", activation_head=commit["sha"], activation_base=main_sha,
                       implementation_sha256=digest, activation_previous_head=previous_head)
        self.save(receipt)
        try:
            old = self.client.get("/git/ref/heads/" + branch)
            require(old.get("object", {}).get("sha") == previous_head, "activation ref changed before update")
            self.writer.request("PATCH", "/git/refs/heads/" + branch, {"sha": commit["sha"], "force": True})
        except APIError as exc:
            if exc.status != 404:
                raise
            self.writer.request("POST", "/git/refs", {"ref": "refs/heads/" + branch, "sha": commit["sha"]})
        if prs:
            pr = prs[0]
        else:
            pr = self.writer.request("POST", "/pulls", {"title": "Renew verified repository policy activation", "head": branch, "base": "main",
                "body": f"Renew the required policy binding from authenticated shadow run {activation['run_id']}, attempt {activation['attempt']}. The policy and evaluation scope are unchanged."})
        require(self.is_bot(pr.get("user", {})), "activation PR was not created by the configured bot")
        receipt.update(status="waiting_activation_checks", pull_request=pr["number"], activation_head=commit["sha"], activation_base=main_sha,
                       implementation_sha256=digest, run_id=activation["run_id"], attempt=activation["attempt"])
        return self.save(receipt)

    def is_bot(self, identity: dict) -> bool:
        return identity.get("login") == self.config["trusted_bot"]["login"] and identity.get("id") == self.config["trusted_bot"]["id"]

    def validate_pr(self, number: int, *, head_sha: str | None = None) -> dict:
        from release.policy_activation import validate_activation_pr
        return validate_activation_pr(self.repository, number, policy_root=self.root, client=self.client,
                                      trusted_bot=self.config["trusted_bot"], head_sha=head_sha)

    def merge_activation(self, run: dict) -> dict:
        pulls = run.get("pull_requests", [])
        require(isinstance(pulls, list) and len(pulls) == 1, "activation CI must identify one PR")
        number = pulls[0]["number"]
        pr = self.client.get(f"/pulls/{number}")
        if not self.is_bot(pr.get("user", {})) or not pr.get("head", {}).get("ref", "").startswith("codex/policy-activation/"):
            return self.result("ignored", reason="CI is not a trusted activation PR")
        require(pr["head"]["sha"] == run["head_sha"], "activation CI is stale")
        latest = self.main()
        head_commit = self.client.get("/git/commits/" + run["head_sha"])
        parents = head_commit.get("parents", [])
        require(isinstance(parents, list) and len(parents) == 1 and isinstance(parents[0], dict), "activation PR must have one owned commit")
        if parents[0].get("sha") != latest:
            # Rebuild against main from independently verified evidence; never
            # merge an out-of-date PR or carry unrelated branch changes.
            activation = strict(self.content(maintenance.POLICY_PATH, run["head_sha"]))["activation"]
            receipts = [x for x in self.receipts(maintenance.activation_source_sha(activation)) if x["profile"] == "policy-shadow" and x.get("run_id") == activation["run_id"]]
            require(len(receipts) == 1, "activation proposal lacks its dispatch receipt")
            if not self.ci_success(latest):
                return self.result("waiting_ci", candidate_sha=latest, pull_request=number)
            current = self.policy_at(latest)
            if current.get("implementation_sha256") != activation["implementation_sha256"]:
                receipt = receipts[0]
                receipt.update(status="superseded", reason="main policy changed before activation merge")
                self.save(receipt)
                return self.start(latest) if self.ci_success(latest) else self.result("waiting_ci", candidate_sha=latest)
            verified = self._verify_activation(activation)
            return self.activation_proposal(verified, latest, receipts[0])
        if run.get("conclusion") != "success":
            return self.result("blocked_ci", candidate_sha=run["head_sha"], pull_request=number, reason="activation PR CI did not succeed")
        validation = self.validate_pr(number, head_sha=run["head_sha"])
        require(validation.get("status") == "pass", "activation proof failed")
        checks = self.client.list(f"/commits/{run['head_sha']}/check-runs", "check_runs")
        for name in REQUIRED_CHECKS:
            matched = [x for x in checks if x.get("name") == name and x.get("head_sha") == run["head_sha"]]
            require(matched and all(x.get("status") == "completed" and x.get("conclusion") == "success" for x in matched), f"exact-head {name} has not passed")
        if not self.apply:
            return self.result("planned_activation_merge", pull_request=number, candidate_sha=run["head_sha"])
        require(self.main() == latest, "main advanced before activation merge")
        pr = self.client.get(f"/pulls/{number}")
        require(pr.get("head", {}).get("sha") == run["head_sha"], "activation head changed before protected merge")
        if pr.get("mergeable_state") != "clean":
            queued = pr.get("auto_merge")
            if queued is None:
                response = self.writer.enable_auto_merge(pr["node_id"], run["head_sha"])
                if response.get("merged") is True:
                    return self.result("activation_merged", pull_request=number, candidate_sha=response["mergeCommit"]["oid"])
            else:
                require(queued.get("merge_method", "").lower() == "squash", "existing auto-merge uses another method")
            return self.result("waiting_activation_merge", pull_request=number, candidate_sha=run["head_sha"],
                               reason="Protected auto-merge waits for remaining repository checks and approvals.")
        response = self.writer.request("PUT", f"/pulls/{number}/merge", {"merge_method": "squash", "sha": run["head_sha"]})
        require(response.get("merged") is True, "protected activation merge was not accepted")
        return self.result("activation_merged", pull_request=number, candidate_sha=response["sha"])

    def _verify_activation(self, activation: dict) -> dict:
        verifier = self.shadow_verifier
        if verifier is None:
            from release.policy_activation import verify_shadow
            verifier = verify_shadow
        if "proof_source_sha" in activation:
            audit = strict(self.content(AUDIT_PREFIX + activation["implementation_sha256"] + ".json", self.main()))
            require(isinstance(audit, dict), "invalid activation audit")
            if audit.get("request_id") is None:
                verified = verifier(self.repository, activation["run_id"], activation["attempt"],
                                    maintenance.activation_source_sha(activation), self.root,
                                    client=self.client, main_proof=True)
                require(verified["activation"] == activation and verified["audit"] == audit,
                        "manual activation differs from its authenticated proof")
                return verified
        receipts = [x for x in self.receipts(maintenance.activation_source_sha(activation)) if x["profile"] == "policy-shadow" and x.get("run_id") == activation["run_id"]]
        require(len(receipts) == 1, "activation lacks its exact dispatch receipt")
        return verifier(self.repository, activation["run_id"], activation["attempt"], maintenance.activation_source_sha(activation), self.root, client=self.client,
                        request_id=receipts[0]["request_id"])

    def normal(self, run: dict, receipt: dict) -> dict:
        artifacts = self.client.list(f"/actions/runs/{run['id']}/artifacts", "artifacts")
        candidates = [x for x in artifacts if x.get("name") == "qualified-release" and x.get("expired") is False]
        require(len(candidates) == 1, "missing or ambiguous qualified-release artifact")
        artifact = candidates[0]
        require(type(artifact.get("id")) is int and artifact["id"] > 0, "invalid qualified artifact ID")
        require(artifact.get("workflow_run", {}).get("id") == run["id"] and artifact.get("workflow_run", {}).get("head_sha") == run["head_sha"], "qualified artifact producer mismatch")
        require(type(run.get("repository", {}).get("id")) is int and type(run.get("head_repository", {}).get("id")) is int
                and artifact.get("workflow_run", {}).get("repository_id") == run["repository"]["id"]
                and artifact.get("workflow_run", {}).get("head_repository_id") == run["head_repository"]["id"], "qualified artifact repository IDs differ")
        raw = self.client.archive(artifact["id"])
        require(artifact.get("digest") == "sha256:" + hashlib.sha256(raw).hexdigest(), "qualified artifact archive digest differs")
        jobs = self.client.list(f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", "jobs")
        producers = [x for x in jobs if x.get("name") == "Assemble immutable qualified release"]
        require(len(producers) == 1 and producers[0].get("status") == "completed" and producers[0].get("conclusion") == "success", "qualified bundle producer did not succeed")
        producer = producers[0]
        require(type(producer.get("id")) is int and producer["id"] > 0 and producer.get("run_id") == run["id"]
                and producer.get("run_attempt") == run["run_attempt"] and producer.get("head_sha") == run["head_sha"], "qualified bundle job identity differs")
        require(hosted.timestamp(producer.get("started_at")) <= hosted.timestamp(artifact.get("created_at"))
                <= hosted.timestamp(artifact.get("updated_at")) <= hosted.timestamp(producer.get("completed_at")), "qualified artifact is outside its producer attempt")
        inventory = hosted.zip_inventory(raw)
        with tempfile.TemporaryDirectory(prefix="qualification-bundle-") as temporary:
            directory = Path(temporary)
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                for name in inventory:
                    path = directory / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read(name))
            manifest = qualification._validate_manifest(strict((directory / "qualification-manifest.json").read_bytes()))
            require(manifest["repository"] == self.repository and manifest["workflow_run_id"] == run["id"] and manifest["source"]["sha"] == run["head_sha"]
                    and manifest["qualification_context"]["run_attempt"] == run["run_attempt"], "qualified manifest identity differs")
            if self.bundle_verifier:
                self.bundle_verifier(directory, manifest, run)
            else:
                kinds = {x["kind"]: x for x in manifest["artifacts"]}
                qualification.verify_bundle(argparse.Namespace(bundle=directory, repository=self.repository, workflow_run_id=run["id"], candidate_sha=run["head_sha"],
                    verify_repository=False, require_tag=False, check_registry=False, wheel_sha256=kinds["wheel"]["sha256"], sdist_sha256=kinds["sdist"]["sha256"], output=directory / "verification-result.json"))
        receipt.update(status="qualified", attempt=run["run_attempt"], version=manifest["version"], artifact_id=artifact["id"], artifact_digest=artifact["digest"],
                       artifact_url=f"https://github.com/{self.repository}/actions/runs/{run['id']}/artifacts/{artifact['id']}")
        return self.save(receipt)

    def reconcile(self, event: dict, *, retry=False, manual=False) -> dict:
        blocked = self.setup()
        if blocked:
            return blocked
        try:
            if manual:
                sha = self.main()
                if not self.ci_success(sha):
                    return self.result("waiting_ci", candidate_sha=sha)
                saved = self.receipts(sha)
                interrupted = [x for x in saved if x.get("status") in {"dispatch_pending", "blocked_dispatch_unknown"}]
                require(len(interrupted) <= 1, "ambiguous interrupted dispatch")
                if interrupted:
                    recovered = self.recover_dispatch(interrupted[0])
                    if recovered["status"] != "dispatched":
                        return recovered
                    saved = self.receipts(sha)
                pending = [x for x in saved if x.get("status") == "waiting_activation_checks"]
                require(len(pending) <= 1, "ambiguous pending activation")
                if pending:
                    receipt = pending[0]
                    pr = self.client.get(f"/pulls/{receipt['pull_request']}")
                    runs = self.client.list(f"/actions/workflows/ci.yml/runs?head_sha={pr['head']['sha']}&event=pull_request", "workflow_runs")
                    matching = [x for x in runs if any(p.get("number") == pr["number"] for p in x.get("pull_requests", []))]
                    if not matching:
                        return receipt
                    chosen = max(matching, key=lambda x: x["id"])
                    if chosen.get("status") != "completed":
                        return receipt
                    run = self.authenticate({"workflow_run": chosen})
                    return self.merge_activation(run)
                active = [x for x in saved if x.get("status") == "dispatched"]
                require(len(active) <= 1, "ambiguous pending qualification")
                if active:
                    receipt = active[0]
                    run = self.client.get(f"/actions/runs/{receipt['run_id']}")
                    if run.get("status") != "completed":
                        return receipt
                    return self.reconcile({"workflow_run": run})
                return self.start(sha, retry=retry)
            run = self.authenticate(event)
            if str(run["path"]).split("@", 1)[0] == CI_PATH:
                if run["conclusion"] != "success":
                    if run["event"] == "pull_request":
                        return self.merge_activation(run)
                    return self.result("blocked_ci", candidate_sha=run["head_sha"], reason="CI did not succeed")
                if run["event"] == "pull_request":
                    return self.merge_activation(run)
                if self.main() != run["head_sha"]:
                    return self.result("superseded", candidate_sha=run["head_sha"], reason="main advanced; wait for current main CI")
                return self.start(run["head_sha"], retry=retry)
            receipt = self.find_request(run)
            if receipt.get("status") in {"qualified", "activation_merged", "superseded"}:
                return receipt
            if run["conclusion"] != "success":
                receipt.update(status="failed", attempt=run["run_attempt"], reason="qualification failed; explicit resume --retry is required")
                return self.save(receipt)
            try:
                return self.shadow(run, receipt) if receipt["profile"] == "policy-shadow" else self.normal(run, receipt)
            except (ValueError, OSError, KeyError, TypeError, qualification.QualificationError) as exc:
                receipt.update(status="blocked_evidence", attempt=run["run_attempt"], reason=str(exc))
                return self.save(receipt)
        except (ValueError, OSError, KeyError, TypeError, qualification.QualificationError) as exc:
            return self.result("blocked", reason=str(exc))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "eligibility", "reconcile", "resume", "activation-proposal", "validate-pr"):
        item = sub.add_parser(command)
        item.add_argument("--root", type=Path, default=Path("."))
        item.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
        item.add_argument("--output", type=Path)
        item.add_argument("--event", type=Path)
        item.add_argument("--apply", action="store_true")
        item.add_argument("--retry", action="store_true")
        item.add_argument("--pull-request", type=int)
        item.add_argument("--head-sha")
        item.add_argument("--run-id", type=int)
        item.add_argument("--attempt", type=int, default=1)
        item.add_argument("--candidate-sha")
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            if args.candidate_sha:
                require(SHA.fullmatch(args.candidate_sha), "invalid inspection candidate SHA")
                client = GitHubClient(args.repository, os.environ.get("GITHUB_TOKEN", ""))
                controller = Coordinator(args.root, args.repository, client, config=load_config(args.root))
                result = controller.policy_at(args.candidate_sha)
            else:
                result = inspect(args.root)
        elif args.command == "eligibility":
            result = eligibility(args.root)
        else:
            config = load_config(args.root)
            if args.command in {"reconcile", "resume", "activation-proposal"} and (not config["enabled"] or (args.apply and not os.environ.get("RELEASE_AUTOMATION_TOKEN"))):
                result = {"schema_version": SCHEMA, "status": "blocked_setup", "reason": "Automation is disabled or RELEASE_AUTOMATION_TOKEN is missing; configure before resuming."}
            else:
                client = GitHubClient(args.repository, os.environ.get("GITHUB_TOKEN", ""))
                writer = GitHubClient(args.repository, os.environ["RELEASE_AUTOMATION_TOKEN"], write=True) if args.apply and os.environ.get("RELEASE_AUTOMATION_TOKEN") else None
                controller = Coordinator(args.root, args.repository, client, writer=writer, apply=args.apply, config=config)
                if args.command == "validate-pr":
                    require(args.pull_request is not None, "--pull-request is required")
                    result = controller.validate_pr(args.pull_request, head_sha=args.head_sha)
                elif args.command == "activation-proposal":
                    blocked = controller.setup()
                    if blocked:
                        result = blocked
                    else:
                        activation = {"candidate_sha": args.candidate_sha, "run_id": args.run_id, "attempt": args.attempt}
                        verified = controller._verify_activation(activation)
                        identifier = verified["audit"].get("request_id")
                        matches = [x for x in controller.receipts(args.candidate_sha) if x["request_id"] == identifier]
                        require(len(matches) == 1, "shadow run requires one authenticated dispatch receipt")
                        result = controller.activation_proposal(verified, controller.main(), matches[0])
                else:
                    result = controller.reconcile(strict(args.event.read_bytes()) if args.event else {}, retry=args.retry, manual=args.command == "resume")
    except (ValueError, OSError, KeyError, TypeError, qualification.QualificationError) as exc:
        result = {"schema_version": SCHEMA, "status": "blocked", "reason": str(exc)}
    if args.output:
        qualification.write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 1 if result["status"] in {"blocked", "blocked_evidence", "blocked_policy", "blocked_ci"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
