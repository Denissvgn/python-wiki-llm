"""Verify nonpromoting hosted policy proofs before generating activation records.

Downloaded source and harnesses are data only. Admission runs through the
trusted checkout's verifier, after comparing every policy implementation input.
"""

from __future__ import annotations

from copy import deepcopy
import base64
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import tempfile
from typing import Any
import urllib.parse
import zipfile

from release import hosted_evidence as hosted, knowledge_maintenance as maintenance

AUDIT_SCHEMA = "agent-wiki-policy-activation-audit/v1"
DECISION_SCHEMA = "agent-wiki-release-policy-decision/v1"
MAX_AUDIT = 64 * 1024
CONTRACT = {
    "candidate-source": ("RD-00 freeze candidate source", ("identity.json", "candidate-source.tar", "SHA256SUMS")),
    "qualification-harnesses": ("RD-00 freeze candidate source", ("qualification-harnesses.tar",)),
    "evidence-rd-10": ("RD-10 hosted composite Action", tuple("maintenance/" + name for name in ("ci-report.json", "preflight.json", "policy.json", "doctor.json"))),
    "knowledge-maintenance-verification": ("Repository knowledge maintenance", ("verification.json",)),
    "qualification-decision": ("Aggregate RD-00 through RD-13", ("decision.json",)),
}


def configuration_contract(config: dict) -> dict:
    """Bind every evaluated field except the replaceable activation record."""
    hosted.require(isinstance(config, dict), "invalid policy configuration contract")
    return deepcopy({key: value for key, value in config.items() if key != "activation"})


def _regular(path: Path) -> bytes:
    hosted.require(not any(parent.is_symlink() for parent in (path, *path.parents)), "redirected trusted policy input")
    return maintenance.read(path, 1024 * 1024)


def _tar_files(raw: bytes, required: tuple[str, ...]) -> dict[str, bytes]:
    """Read bounded regular members without extracting or executing the archive."""
    result: dict[str, bytes] = {}
    hosted.require(len(raw) <= hosted.MAX_EXPANDED, "source archive exceeds byte limit")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        names: set[str] = set()
        expanded = 0
        for member in archive:
            name = member.name.rstrip("/") if member.isdir() else member.name
            path = PurePosixPath(name)
            hosted.require(
                bool(name) and path.as_posix() == name and not path.is_absolute()
                and ".." not in path.parts and "\\" not in name and ":" not in name,
                "unsafe frozen archive member",
            )
            hosted.require(name not in names, "duplicate frozen archive member")
            names.add(name)
            expanded += member.size
            hosted.require(len(names) <= 100000 and expanded <= hosted.MAX_EXPANDED, "frozen archive expansion bound exceeded")
            hosted.require(member.isdir() or member.isfile(), "nonregular frozen archive member")
            if name in required:
                hosted.require(member.isfile() and member.size <= 1024 * 1024, "invalid frozen policy input")
                stream = archive.extractfile(member)
                hosted.require(stream is not None, "missing frozen policy input")
                assert stream is not None
                with stream:
                    result[name] = stream.read(member.size + 1)
                hosted.require(len(result[name]) == member.size, "frozen policy input length differs")
    hosted.require(set(result) == set(required), "missing frozen policy input")
    return result


def _artifact(client: Any, artifact: dict, job: dict, run: dict) -> tuple[dict[str, bytes], dict]:
    workflow = artifact.get("workflow_run", {})
    hosted.require(
        artifact.get("expired") is False and type(artifact.get("id")) is int and artifact["id"] > 0
        and workflow.get("id") == run["id"] and workflow.get("head_sha") == run["head_sha"]
        and workflow.get("repository_id") == run["repository"]["id"]
        and workflow.get("head_repository_id") == run["head_repository"]["id"],
        "artifact is expired or belongs to another candidate",
    )
    hosted.require(
        hosted.timestamp(job["started_at"]) <= hosted.timestamp(artifact.get("created_at")) <= hosted.timestamp(job["completed_at"])
        and hosted.timestamp(job["started_at"]) <= hosted.timestamp(artifact.get("updated_at")) <= hosted.timestamp(job["completed_at"]),
        "artifact is outside its producer attempt",
    )
    digest = artifact.get("digest")
    hosted.require(isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None, "invalid GitHub artifact digest")
    raw = client.archive(artifact["id"])
    hosted.require(isinstance(raw, bytes) and "sha256:" + hosted.sha256(raw) == digest, "GitHub artifact archive digest mismatch")
    inventory = hosted.zip_inventory(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        files = {name: archive.read(name) for name in inventory}
    return files, {
        "artifact_id": artifact["id"], "artifact_digest": digest,
        "producer_job_id": job["id"], "producer": job["name"], "files": inventory,
    }


def _identity(value: Any, repository: str, candidate_sha: str, archive: bytes) -> dict:
    hosted.require(isinstance(value, dict) and set(value) == {"schema_version", "repository", "source", "version", "tag", "mode"}, "invalid policy-shadow identity fields")
    source = value.get("source")
    hosted.require(isinstance(source, dict) and set(source) == {"sha", "tree", "archive_sha256", "commit_epoch"}, "invalid policy-shadow source identity")
    assert isinstance(source, dict)
    hosted.require(
        value["schema_version"] == "agent-wiki-release-identity/v1"
        and value["mode"] == "policy-shadow" and value["repository"] == repository
        and source["sha"] == candidate_sha and isinstance(source["tree"], str)
        and re.fullmatch(r"[0-9a-f]{40}", source["tree"]) is not None
        and type(source["commit_epoch"]) is int and source["commit_epoch"] > 0
        and source["archive_sha256"] == hosted.sha256(archive)
        and isinstance(value["version"], str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){2}(?:[a-zA-Z0-9.+-]*)", value["version"]) is not None
        and value["tag"] == "v" + value["version"],
        "policy-shadow identity differs from the frozen candidate",
    )
    return value


def verify_shadow(
    repository: str, run_id: int, attempt: int, candidate_sha: str,
    policy_root: Path, *, client: Any = None, request_id: str | None = None,
    main_proof: bool = False,
) -> dict:
    """Authenticate one completed pinned run and replay its original policy evidence."""
    hosted.require(isinstance(repository, str) and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None, "invalid repository")
    hosted.require(type(run_id) is int and run_id > 0 and type(attempt) is int and attempt > 0, "invalid policy-shadow run identity")
    hosted.require(isinstance(candidate_sha, str) and re.fullmatch(r"[0-9a-f]{40}", candidate_sha) is not None, "invalid candidate SHA")
    hosted.require(request_id is None or (isinstance(request_id, str) and re.fullmatch(r"[0-9a-f]{64}", request_id) is not None), "invalid renewal request identity")
    hosted.require(type(main_proof) is bool and (not main_proof or request_id is None), "manual main proof cannot use a coordinator identity")
    client = client if client is not None else hosted.GitHub(repository)
    try:
        run = client.get(f"/actions/runs/{run_id}")
        hosted.require(
            isinstance(run, dict) and run.get("id") == run_id and run.get("run_attempt") == attempt
            and run.get("head_sha") == candidate_sha
            and run.get("head_branch") == ("main" if main_proof else "codex/qualification/" + candidate_sha)
            and run.get("event") == "workflow_dispatch" and run.get("path", "").partition("@")[0] == hosted.WORKFLOW
            and run.get("status") == "completed" and run.get("conclusion") == "success"
            and run.get("repository", {}).get("full_name") == repository
            and run.get("head_repository", {}).get("full_name") == repository
            and type(run.get("repository", {}).get("id")) is int
            and run["repository"]["id"] == run.get("head_repository", {}).get("id"),
            "hosted policy-shadow run identity differs or did not succeed",
        )
        hosted.require(request_id is None or run.get("display_title") == f"Release qualification [{request_id}]", "hosted policy-shadow request identity differs")
        jobs = client.list(f"/actions/runs/{run_id}/attempts/{attempt}/jobs", "jobs")
        producers = {}
        for name in sorted({row[0] for row in CONTRACT.values()}):
            matches = [job for job in jobs if job.get("name") == name]
            hosted.require(len(matches) == 1, "missing or ambiguous hosted policy producer: " + name)
            job = matches[0]
            hosted.require(
                job.get("status") == "completed" and job.get("conclusion") == "success"
                and job.get("run_id") == run_id and job.get("run_attempt") == attempt
                and job.get("head_sha") == candidate_sha and type(job.get("id")) is int and job["id"] > 0,
                "hosted policy producer did not succeed for this attempt: " + name,
            )
            producers[name] = job
        hosted.require(all(
            job.get("name") in producers
            or (job.get("status") == "completed" and job.get("conclusion") == "skipped")
            for job in jobs
        ), "policy shadow executed jobs outside its bounded profile")
        bundles = [job for job in jobs if job.get("name") == "Assemble immutable qualified release"]
        hosted.require(len(bundles) <= 1 and all(job.get("status") == "completed" and job.get("conclusion") == "skipped" for job in bundles), "policy shadow attempted release assembly")
        artifacts = client.list(f"/actions/runs/{run_id}/artifacts", "artifacts")
        hosted.require(not any(artifact.get("name") == "qualified-release" for artifact in artifacts), "policy shadow produced a qualified release")
        files: dict[str, dict[str, bytes]] = {}
        commitments = {}
        for name, (producer, required) in CONTRACT.items():
            matches = [artifact for artifact in artifacts if artifact.get("name") == name]
            hosted.require(len(matches) == 1, "missing or ambiguous hosted policy artifact: " + name)
            files[name], commitments[name] = _artifact(client, matches[0], producers[producer], run)
            hosted.require(set(required) <= files[name].keys(), "hosted policy artifact lacks required files: " + name)
        source = files["candidate-source"]
        identity = _identity(hosted._json(source["identity.json"]), repository, candidate_sha, source["candidate-source.tar"])
        hosted.require(source["SHA256SUMS"] == (identity["source"]["archive_sha256"] + "  candidate-source.tar\n").encode("ascii"), "source checksum differs from identity")
        inputs = (*maintenance.POLICY_INPUTS, maintenance.POLICY_PATH)
        frozen = _tar_files(source["candidate-source.tar"], inputs)
        harness = _tar_files(files["qualification-harnesses"]["qualification-harnesses.tar"], inputs)
        trusted = {name: _regular(policy_root / name) for name in maintenance.POLICY_INPUTS}
        hosted.require(all(frozen[name] == harness[name] == trusted[name] for name in trusted), "frozen policy implementation differs from trusted checkout")
        hosted.require(harness[maintenance.POLICY_PATH] == frozen[maintenance.POLICY_PATH], "frozen harness policy configuration differs from source")
        original_config = hosted._json(frozen[maintenance.POLICY_PATH])
        hosted.require(original_config.get("mode") == "required", "automatic activation requires a required policy")
        evaluated_contract = configuration_contract(original_config)
        current_config = hosted._json(_regular(policy_root / maintenance.POLICY_PATH))
        hosted.require(evaluated_contract == configuration_contract(current_config),
                       "frozen policy configuration differs from trusted checkout")
        implementation = (
            maintenance.composite_policy_digest(trusted.__getitem__)
            if original_config.get("schema_version") == maintenance.CONFIG_V2_SCHEMA
            else hosted.sha256(trusted[maintenance.LEAF_PATH])
        )
        config = maintenance.policy(frozen[maintenance.POLICY_PATH], implementation_hash=implementation, policy_shadow=True)
        receipt_raw = files["knowledge-maintenance-verification"]["verification.json"]
        receipt = hosted._json(receipt_raw)
        with tempfile.TemporaryDirectory(prefix="wiki-policy-proof-") as directory:
            evidence = Path(directory)
            for name in ("ci-report.json", "preflight.json", "policy.json", "doctor.json"):
                (evidence / name).write_bytes(files["evidence-rd-10"]["maintenance/" + name])
            rebuilt = maintenance.admit(evidence, identity, config)
        hosted.require(rebuilt["status"] == "pass", "replayed policy evidence failed: " + str(rebuilt.get("error")))
        rebuilt["activation_proof"] = {
            "schema_version": "agent-wiki-release-policy-shadow/v1", "qualification": "nonpromoting",
            "policy": config["policy"], "implementation_sha256": implementation,
        }
        hosted.require(receipt == rebuilt, "captured shadow receipt differs from replayed evidence")
        decision = hosted._json(files["qualification-decision"]["decision.json"])
        hosted.require(isinstance(decision, dict) and decision.get("nonpromoting") is True and decision == {
            "schema_version": DECISION_SCHEMA, "candidate_sha": candidate_sha,
            "candidate_tree": identity["source"]["tree"], "candidate_version": identity["version"],
            "status": "pass", "nonpromoting": True,
            "gates": {"source": "PASS", "integrity": "PASS", "maintenance": "PASS"},
        }, "policy shadow decision is incomplete or promoting")
        activation = {
            "proof_source_sha": candidate_sha, "run_id": run_id, "attempt": attempt,
            "comparison_sha256": hosted.sha256(receipt_raw), "implementation_sha256": implementation,
        }
        audit = {
            "schema_version": AUDIT_SCHEMA, "repository": repository, "candidate_sha": candidate_sha,
            "candidate_tree": identity["source"]["tree"], "candidate_version": identity["version"],
            "run_id": run_id, "attempt": attempt, "request_id": request_id,
            "implementation_sha256": implementation, "verification_sha256": activation["comparison_sha256"],
            "configuration": evaluated_contract,
            "artifacts": commitments, "receipt": receipt,
        }
        hosted.require(len(json.dumps(audit, sort_keys=True, separators=(",", ":")).encode("utf-8")) <= MAX_AUDIT, "policy activation audit exceeds byte limit")
        return {"activation": activation, "audit": audit}
    except hosted.EvidenceError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, tarfile.TarError, zipfile.BadZipFile) as exc:
        raise hosted.EvidenceError("invalid hosted policy proof: " + str(exc)[:1000]) from exc


def proposal(config: dict, verified: dict) -> dict:
    """Replace only the activation, retaining the caller's maintenance contract."""
    hosted.require(isinstance(config, dict) and config.get("mode") == "required", "automatic activation requires a required policy")
    hosted.require(configuration_contract(config) == verified["audit"].get("configuration"),
                   "activation proposal changes the evaluated configuration contract")
    result = deepcopy(config)
    result["activation"] = deepcopy(verified["activation"])
    maintenance.policy(json.dumps(result).encode("utf-8"), implementation_hash=verified["activation"]["implementation_sha256"])
    hosted.require(result["policy"] == verified["audit"]["receipt"]["activation_proof"]["policy"], "activation proposal changes policy contract")
    return result


def _content(client: Any, path: str, ref: str, *, limit: int = 1024 * 1024) -> bytes:
    value = client.get(f"/contents/{urllib.parse.quote(path, safe='/')}?ref={urllib.parse.quote(ref, safe='')}")
    hosted.require(
        isinstance(value, dict) and value.get("type") == "file" and value.get("encoding") == "base64"
        and type(value.get("size")) is int and 0 <= value["size"] <= limit
        and isinstance(value.get("content"), str),
        "missing, redirected or oversized activation input",
    )
    hosted.require(len(value["content"]) <= limit * 2, "oversized activation input encoding")
    raw = base64.b64decode(value["content"].replace("\n", ""), validate=True)
    hosted.require(len(raw) == value["size"], "activation input length differs")
    return raw


def validate_activation_pr(
    repository: str, number: int, *, policy_root: Path, client: Any,
    trusted_bot: dict, head_sha: str | None = None,
) -> dict:
    """Authenticate the bot's two-file PR and independently replay its proof."""
    hosted.require(type(number) is int and number > 0, "invalid activation pull request")
    hosted.require(isinstance(repository, str) and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is not None, "invalid repository")
    try:
        pr = client.get(f"/pulls/{number}")
        branch = pr.get("head", {}).get("ref", "")
        manual = isinstance(branch, str) and branch.startswith("codex/manual-policy-activation/")
        prefix = "codex/manual-policy-activation/" if manual else "codex/policy-activation/"
        if not isinstance(branch, str) or not branch.startswith(prefix):
            return {"status": "ignored", "pull_request": number}
        digest = branch.removeprefix(prefix)
        hosted.require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "invalid activation branch digest")
        trusted_author = (
            isinstance(trusted_bot, dict) and isinstance(trusted_bot.get("login"), str) and bool(trusted_bot["login"])
            and type(trusted_bot.get("id")) is int and trusted_bot["id"] > 0
            and pr.get("user", {}).get("login") == trusted_bot["login"]
            and pr.get("user", {}).get("id") == trusted_bot["id"]
        )
        hosted.require(trusted_author or (manual and pr.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}),
                       "activation pull request is not owned by an authorized proposer")
        hosted.require(
            pr.get("head", {}).get("repo", {}).get("full_name") == repository
            and pr.get("base", {}).get("repo", {}).get("full_name") == repository
            and pr.get("base", {}).get("ref") == "main"
            and pr.get("state") == "open" and pr.get("draft") is False,
            "activation pull request has unsafe repository or base",
        )
        head = pr["head"]["sha"]
        base = pr["base"]["sha"]
        hosted.require(
            isinstance(head, str) and re.fullmatch(r"[0-9a-f]{40}", head) is not None
            and isinstance(base, str) and re.fullmatch(r"[0-9a-f]{40}", base) is not None
            and (head_sha is None or head_sha == head),
            "activation pull request head differs",
        )
        current = client.get("/git/ref/heads/main")
        hosted.require(current.get("ref") == "refs/heads/main" and current.get("object", {}).get("type") == "commit" and current["object"].get("sha") == base, "activation pull request base is superseded")
        commit = client.get("/git/commits/" + head)
        hosted.require(commit.get("sha") == head and isinstance(commit.get("parents"), list) and len(commit["parents"]) == 1 and commit["parents"][0].get("sha") == base, "activation pull request must contain one commit on current main")
        audit_path = "release/policy-activations/" + digest + ".json"
        changed = client.list(f"/pulls/{number}/files")
        hosted.require(
            type(pr.get("changed_files")) is int and pr["changed_files"] == 2
            and len(changed) == 2 and {item.get("filename") for item in changed} == {maintenance.POLICY_PATH, audit_path}
            and all(item.get("status") in {"added", "modified"} for item in changed),
            "activation pull request changes files outside its contract",
        )
        for name in maintenance.POLICY_INPUTS:
            hosted.require(_content(client, name, base) == _regular(policy_root / name), "current main policy differs from trusted checkout")
        base_config = hosted._json(_content(client, maintenance.POLICY_PATH, base, limit=65536))
        updated = hosted._json(_content(client, maintenance.POLICY_PATH, head, limit=65536))
        audit = hosted._json(_content(client, audit_path, head, limit=MAX_AUDIT))
        hosted.require(isinstance(base_config, dict) and isinstance(updated, dict) and isinstance(audit, dict), "invalid activation pull request inputs")
        hosted.require(
            {key: value for key, value in base_config.items() if key != "activation"}
            == {key: value for key, value in updated.items() if key != "activation"},
            "activation pull request changes policy or evaluation scope",
        )
        proposed = updated.get("activation")
        hosted.require(isinstance(proposed, dict) and proposed.get("implementation_sha256") == digest, "activation pull request digest differs from branch")
        assert isinstance(proposed, dict)
        proof_source = maintenance.activation_source_sha(proposed)
        evaluated_config = hosted._json(_content(client, maintenance.POLICY_PATH, proof_source, limit=65536))
        hosted.require(configuration_contract(evaluated_config) == configuration_contract(base_config),
                       "activation proof configuration differs from current main")
        comparison = client.get(f"/compare/{proof_source}...{base}")
        hosted.require(
            comparison.get("status") in {"ahead", "identical"}
            and comparison.get("merge_base_commit", {}).get("sha") == proof_source,
            "activation proof candidate is not in protected main history",
        )
        verified = verify_shadow(
            repository, proposed["run_id"], proposed["attempt"], proof_source,
            policy_root, client=client, request_id=audit.get("request_id"), main_proof=manual,
        )
        hosted.require(audit == verified["audit"] and updated == proposal(base_config, verified), "activation pull request differs from authenticated proof")
        return {"status": "pass", "pull_request": number, "head_sha": head, "base_sha": base, "activation": verified["activation"]}
    except hosted.EvidenceError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError) as exc:
        raise hosted.EvidenceError("invalid activation pull request: " + str(exc)[:1000]) from exc
