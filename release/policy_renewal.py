"""Manual main-branch policy evaluation and independently verified approval PRs."""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
from pathlib import Path
import re
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release import knowledge_maintenance as maintenance, policy_activation
from release.qualification_automation import (
    APIError,
    GitHubClient,
    canonical,
    load_config,
    qualification_inputs,
    require,
    strict,
)
from release.qualification import QualificationError, _run

REPOSITORY = "Denissvgn/python-wiki-llm"
BRANCH_PREFIX = "codex/manual-policy-activation/"


def main_identity(root: Path, client) -> str:
    ref = client.get("/git/ref/heads/main")
    sha = ref.get("object", {}).get("sha")
    require(
        ref.get("ref") == "refs/heads/main"
        and ref.get("object", {}).get("type") == "commit"
        and isinstance(sha, str)
        and re.fullmatch(r"[0-9a-f]{40}", sha),
        "main identity is unavailable",
    )
    require(
        _run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip() == sha,
        "main advanced or checkout is not current main; rerun from main",
    )
    return sha


def evaluate(
    root: Path, repository: str, client, *, apply: bool, correlation: str
) -> dict:
    sha = main_identity(root, client)
    identifier = hashlib.sha256(
        canonical({"source": sha, "renewal": correlation})
    ).hexdigest()
    payload = {
        "ref": "main",
        "inputs": qualification_inputs(sha, "policy-shadow", identifier),
    }
    if apply:
        client.request(
            "POST", "/actions/workflows/release-qualification.yml/dispatches", payload
        )
    return {
        "status": "dispatched" if apply else "planned",
        "proof_source_sha": sha,
        "request_id": identifier,
        "inputs": payload,
        "url": f"https://github.com/{repository}/actions/workflows/release-qualification.yml",
    }


def prepare(
    root: Path,
    repository: str,
    client,
    *,
    run_id: int,
    attempt: int,
    output: Path,
    verifier=policy_activation.verify_shadow,
) -> dict:
    base = main_identity(root, client)
    run = client.get(f"/actions/runs/{run_id}")
    source = run.get("head_sha")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source),
        "proof source SHA is unavailable",
    )
    comparison = client.get(f"/compare/{source}...{base}")
    require(
        comparison.get("status") in {"ahead", "identical"}
        and comparison.get("merge_base_commit", {}).get("sha") == source,
        "proof source is not in main history",
    )
    verified = verifier(
        repository, run_id, attempt, source, root, client=client, main_proof=True
    )
    config = strict((root / maintenance.POLICY_PATH).read_bytes())
    updated = policy_activation.proposal(config, verified)
    digest = verified["activation"]["implementation_sha256"]
    files = {
        maintenance.POLICY_PATH: canonical(updated),
        f"release/policy-activations/{digest}.json": canonical(verified["audit"]),
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return {
        "status": "proposal_ready",
        "proof_source_sha": source,
        "base_sha": base,
        "branch": BRANCH_PREFIX + digest,
        "files": list(files),
        "proposal": str(output),
    }


def create_pr(repository: str, result: dict, reader, writer, *, config: dict) -> dict:
    actor = writer.get_user()
    bot = config["trusted_bot"]
    trusted = (
        bool(bot.get("login"))
        and actor.get("login") == bot["login"]
        and actor.get("id") == bot["id"]
    )
    if not trusted:
        permission = reader.get(f"/collaborators/{actor['login']}/permission")
        require(
            permission.get("permission") in {"admin", "maintain", "write"},
            "approval PR credential must belong to a repository maintainer or the configured bot",
        )
    base, branch = result["base_sha"], result["branch"]
    require(
        reader.get("/git/ref/heads/main")["object"]["sha"] == base,
        "main advanced before approval proposal",
    )
    try:
        reader.get("/git/ref/heads/" + branch)
    except APIError as exc:
        if exc.status != 404:
            raise
    else:
        raise ValueError(
            "approval branch already exists; review its PR before creating another proposal"
        )
    parent = reader.get("/git/commits/" + base)
    entries = []
    for name in result["files"]:
        raw = (Path(result["proposal"]) / name).read_bytes()
        blob = writer.request(
            "POST",
            "/git/blobs",
            {"content": base64.b64encode(raw).decode(), "encoding": "base64"},
        )
        entries.append(
            {"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]}
        )
    tree = writer.request(
        "POST", "/git/trees", {"base_tree": parent["tree"]["sha"], "tree": entries}
    )
    commit = writer.request(
        "POST",
        "/git/commits",
        {
            "message": "Renew reviewed main policy approval",
            "tree": tree["sha"],
            "parents": [base],
        },
    )
    require(
        reader.get("/git/ref/heads/main")["object"]["sha"] == base,
        "main advanced before approval branch creation",
    )
    writer.request(
        "POST", "/git/refs", {"ref": "refs/heads/" + branch, "sha": commit["sha"]}
    )
    pr = writer.request(
        "POST",
        "/pulls",
        {
            "base": "main",
            "head": branch,
            "title": "Renew verified repository policy approval",
            "body": f"Record the reviewed policy proof from `{result['proof_source_sha']}`. "
            "The proof source remains historical after merging this activation-only update. "
            "Independent proof verification and normal branch review are required before merge.",
        },
    )
    return {
        **result,
        "status": "pull_request_created",
        "url": pr["html_url"],
        "head_sha": commit["sha"],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("evaluate", "prepare"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--proof-run-id", type=int)
    parser.add_argument("--proof-attempt", type=int, default=1)
    parser.add_argument(
        "--proposal", type=Path, default=Path("policy-approval-proposal")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        require(args.proof_attempt > 0, "proof attempt must be positive")
        reader = GitHubClient(
            args.repository,
            os.environ.get("GITHUB_TOKEN", ""),
            write=args.apply and args.operation == "evaluate",
        )
        if args.operation == "evaluate":
            result = evaluate(
                root,
                args.repository,
                reader,
                apply=args.apply,
                correlation=os.environ.get("GITHUB_RUN_ID", "manual"),
            )
        else:
            require(
                args.proof_run_id is not None and args.proof_run_id > 0,
                "a successful proof run ID is required",
            )
            assert args.proof_run_id is not None
            result = prepare(
                root,
                args.repository,
                reader,
                run_id=args.proof_run_id,
                attempt=args.proof_attempt,
                output=args.proposal,
            )
            credential = os.environ.get("POLICY_RENEWAL_TOKEN", "")
            if args.apply and credential:
                result = create_pr(
                    args.repository,
                    result,
                    reader,
                    GitHubClient(args.repository, credential, write=True),
                    config=load_config(root),
                )
            else:
                result["next_step"] = (
                    "Download policy-approval-proposal and open a maintainer PR from the named branch. "
                    "For automatic PR creation, configure RELEASE_AUTOMATION_TOKEN or the GitHub App credentials described in docs/automation.md."
                )
        args.output.write_bytes(canonical(result))
        print(canonical(result).decode())
        return 0
    except (ValueError, OSError, KeyError, TypeError, QualificationError) as exc:
        args.output.write_bytes(canonical({"status": "blocked", "reason": str(exc)}))
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
