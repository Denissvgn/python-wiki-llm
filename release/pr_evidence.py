"""Compare a hosted PR plan to a locally exercised selection and original Git tree."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import (
    manual_release as manual,
    pr_ci as ci,
    qualification_automation as automation,
)

CONTRACTS = (
    "base_sha",
    "head_sha",
    "candidate_tree",
    "repository",
    "policy_sha256",
    "groups",
    "lanes",
    "jobs",
    "skip_edges",
)


def compare(root, local, plan, merge, remote_tree):
    manual.require(
        all(plan[k] == local[k] for k in CONTRACTS)
        and plan.get("typescript_families", []) == local.get("typescript_families", []),
        "Hosted and local CI selections or revisions differ",
    )
    head = local["head_sha"]
    manual.require(
        local["candidate_sha"] == head
        and plan["mode"] == "pull-request"
        and plan["qualification"] is False,
        "PR head/plan identity differs",
    )
    manual.require(
        merge["sha"] == plan["candidate_sha"]
        and [p["sha"] for p in merge["parents"]] == [local["base_sha"], head]
        and merge["tree"]["sha"] == remote_tree["sha"] == plan["candidate_tree"]
        and remote_tree["truncated"] is False,
        "Incomplete merge parents or tree",
    )
    manual.require(ci.git(root, "rev-parse", head + "^{tree}").decode().strip() == plan["candidate_tree"],
                   "Local head tree differs from the authenticated CI tree")
    listing = ci.tree(root, head)
    remote = {}
    for item in remote_tree["tree"]:
        if item["type"] == "tree":
            continue
        name = ci.safe_path(item["path"])
        manual.require(
            name not in remote and item["type"] == "blob", "Unexpected tree entry"
        )
        remote[name] = (item["mode"], item["sha"])
    manual.require(listing == remote, "Full path, mode and blob map differs")
    full_map = {path: (mode, "blob", oid) for path, (mode, oid) in listing.items()}
    return {
        "head_sha": head,
        "hosted_merge_sha": merge["sha"],
        "tree": remote_tree["sha"],
        "files": len(remote),
        "full_path_mode_type_blob_map_sha256": ci.digest(ci.canonical(full_map)),
        "selection_verified": True,
        "publication_authority": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--local-plan", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    root = manual.safe(args.root)
    work = manual.safe(root / args.work)
    manual.Store(root, work)
    work.mkdir(parents=True, exist_ok=False)
    local = ci.read_json(args.local_plan)
    repo = local["repository"]
    token = (
        os.environ.get("GITHUB_TOKEN")
        or subprocess.check_output(
            ["gh", "auth", "token", "--hostname", "github.com"], text=True
        ).strip()
    )
    backend = manual.GitHubBackend(root, work, repo, token)
    client = backend.client = automation.GitHubClient(repo, token, write=False)
    run = client.get(f"/actions/runs/{args.run_id}")
    manual.require(
        run["id"] == args.run_id
        and run["run_attempt"] == args.attempt
        and run["event"] == "pull_request"
        and run["head_sha"] == local["head_sha"]
        and run["path"] == ci.WORKFLOW
        and run["name"] == "CI"
        and run["repository"]["full_name"] == repo,
        "Wrong CI producer",
    )
    pr = client.get(f"/pulls/{args.pr}")
    manual.require(
        pr["number"] == args.pr
        and pr["base"]["ref"] == "main"
        and pr["base"]["sha"] == local["base_sha"]
        and pr["head"]["sha"] == local["head_sha"]
        and pr["head"]["repo"]["id"] == run["head_repository"]["id"]
        and pr["base"]["repo"]["id"] == run["repository"]["id"],
        "Wrong pull request",
    )
    files = backend._artifact(
        {"candidate_sha": run["head_sha"]},
        run,
        f"pr-ci-plan-{args.attempt}",
        "Select affected PR contracts",
    )
    plan = ci.read_json(files / "plan.json")
    manual.require(
        (plan["pull_request"], plan["run_id"], plan["run_attempt"])
        == (args.pr, args.run_id, args.attempt),
        "PR plan run binding differs",
    )
    result = compare(
        root,
        local,
        plan,
        client.get("/git/commits/" + plan["candidate_sha"]),
        client.get("/git/trees/" + plan["candidate_tree"] + "?recursive=1"),
    )
    manual.require(
        client.get(f"/actions/runs/{args.run_id}")["run_attempt"] == args.attempt,
        "CI attempt changed",
    )
    ci.write_json(work / "source-equivalence.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
