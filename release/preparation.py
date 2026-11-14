"""Read-only dependency planning for source, reviewed wiki capture and policy approval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import tomllib

if __package__ in {None, ""}:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import hosted_evidence as hosted
from release import knowledge_maintenance as maintenance
from release import manual_release as manual
from release import preflight_targets
from release import pr_ci

SCHEMA = "agent-wiki-release-preparation/v1"


def changes_since(root: Path, base: str, head: str) -> list[dict]:
    # A preparation baseline may be HEAD itself or an equal-tree commit. The
    # PR selector intentionally requires a nonempty diff, so keep its admission
    # contract and handle this read-only comparison before calling it.
    comparison = manual.git(root, "diff", "--quiet", "--no-ext-diff", "--no-textconv", base, head, "--", check=False)
    manual.require(comparison.returncode in {0, 1}, "Preparation source comparison failed")
    if comparison.returncode == 0:
        return []
    fields = manual.git(root, "diff", "--name-status", "-z", "--find-renames", "--no-ext-diff", "--no-textconv", base, head, "--").stdout.split("\0")
    rows = []
    while fields and fields[0]:
        status = fields.pop(0)
        manual.require(re.fullmatch(r"[AMDT]|R[0-9]{1,3}", status) is not None and len(fields) >= 2,
                       "Unsupported preparation diff record")
        old = pr_ci.safe_path(fields.pop(0))
        new = pr_ci.safe_path(fields.pop(0)) if status.startswith("R") else old
        rows.append({"status": status, "old": old, "path": new})
        manual.require(len(rows) <= pr_ci.MAX_PATHS, "Preparation diff exceeds path bound")
    return rows


def source_status(root: Path, config: dict) -> dict:
    """Compare captured source bytes without extracting or changing the wiki."""
    from llm_wiki_cli.services.knowledge_envelope import hash_source_snapshot
    from llm_wiki_cli.services.knowledge_model import _parse_bundle
    from llm_wiki_cli.services.knowledge_packs import PACKED_SCHEMAS, parse_packed_root
    from llm_wiki_cli.services.knowledge_storage import parse_store_root
    from llm_wiki_cli.services.source_selection import validate_persisted_source_selection_identity
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot
    from llm_wiki_cli.services.sync_manifest import SyncManifest

    root = manual.safe(root)
    try:
        wiki = manual.safe(root / config["wiki_dir"])
        manifest = SyncManifest.load(wiki)
        raw = maintenance.read(wiki / ".llm-wiki-knowledge.json")
        manual.require(manifest.artifact_hashes is not None
                       and manifest.artifact_hashes.knowledge_index_hash == "sha256:" + manual.digest(raw),
                       "Knowledge root differs from the committed manifest")
        data = hosted._json(raw)
        if data["schema_version"] in PACKED_SCHEMAS:
            data = parse_packed_root(raw)["store"]
        elif data["schema_version"] == "llm-wiki-knowledge/v2":
            data = parse_store_root(raw)
        bundle = _parse_bundle(data["bundle"], "bundle")
        source_root = manual.safe(root / config["src_dir"])
        manual.require(source_root.is_relative_to(root), "Selected source root escapes the checkout")
        snapshot = build_source_snapshot(source_root, source_selection=config["selection"])
        actual = hash_source_snapshot(snapshot.to_consumed_inputs())
        selection_issue = None
        try:
            validate_persisted_source_selection_identity(
                manifest.generation_inputs, snapshot.source_selection_identity,
                operation="release preparation", live_selection_inputs=snapshot.source_selection_inputs,
            )
        except ValueError as exc:
            selection_issue = str(exc)
        recorded = {p: row["hash"] for p, row in manifest.sources.items()}
        infrastructure = manifest.generation_inputs.get("infrastructure", {})
        if isinstance(infrastructure, dict):
            recorded.update({p: row["source_content_hash"] for p, row in infrastructure.get("sources", {}).items()})
        current = snapshot.hashes_for()
        changed = [p for p, value in sorted(recorded.items()) if current.get(p) != value]
        revision = bundle.repository.evaluated_revision
        captured_sha = revision[4:] if re.fullmatch(r"git:[0-9a-f]{40}", revision) else None
        selected_changes = []
        diff_status = "unavailable"
        diff_issue = None
        if captured_sha:
            observed_head = manual.git(root, "rev-parse", "HEAD", check=False)
            head = observed_head.stdout.strip()
            ancestor = manual.git(root, "merge-base", "--is-ancestor", captured_sha, head, check=False) if observed_head.returncode == 0 else None
            if ancestor is not None and ancestor.returncode == 0:
                def selected(path):
                    if path is None:
                        return False
                    try:
                        return snapshot.path_is_effectively_selected((root / path).relative_to(source_root).as_posix())
                    except ValueError:
                        return False
                try:
                    selected_changes = [r for r in changes_since(root, captured_sha, head)
                                        if selected(r["path"]) or selected(r["old"])]
                    diff_status = "observed"
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    # Git history is diagnostic. It cannot erase an already
                    # observed source-snapshot mismatch or imply a matching one.
                    diff_issue = str(exc)
        mismatch = actual != bundle.snapshot.source_snapshot_hash or bool(selection_issue)
        return {"status": "capture-required" if mismatch else "source-current",
                "captured_source_sha": captured_sha, "captured_source_hash": bundle.snapshot.source_snapshot_hash,
                "current_source_hash": actual, "changed_recorded_paths": changed,
                "selected_changes_since_capture": selected_changes, "capture_diff_status": diff_status,
                "capture_diff_issue": diff_issue,
                "selection_issue": selection_issue, "selection": snapshot.source_selection_identity,
                "selected_inputs": len(current), "runtime_verified": False,
                "reason": "Required release health evaluates exact source bytes, including nonsemantic changes."
                if mismatch else "Current source snapshot matches the committed writer snapshot."}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "unknown", "reason": str(exc), "runtime_verified": False}


def policy_status(root: Path) -> dict:
    raw = maintenance.read(root / maintenance.POLICY_PATH)
    declared = hosted._json(raw)
    digest = (maintenance.composite_policy_digest(lambda name: maintenance.read(root / name))
              if declared.get("schema_version") == maintenance.CONFIG_V2_SCHEMA
              else manual.digest(maintenance.read(root / maintenance.LEAF_PATH)))
    try:
        config = maintenance.policy(raw, implementation_hash=digest)
        status = "current" if config["mode"] == "required" else config["mode"]
    except maintenance.ActivationMismatch:
        config = maintenance.policy(raw, implementation_hash=digest, policy_shadow=True)
        config["mode"] = declared["mode"]
        status = "approval-required"
    return {"status": status, "implementation_sha256": digest, "configuration": config,
            "historical_proof_source_sha": maintenance.activation_source_sha(config["activation"])
            if config["mode"] == "required" else None}


def capture_prerequisite(root: Path) -> dict:
    policy = policy_status(root)
    sources = source_status(root, policy["configuration"])
    targets = preflight_targets.inspect(root, policy["configuration"]["wiki_dir"], lambda name: maintenance.read(root / name))
    try:
        version = maintenance.version_check(root, policy["configuration"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        version = {"status": "unknown", "reason": str(exc)}
    required = policy["configuration"]["mode"] == "required"
    blocked = required and (sources["status"] == "capture-required"
                            or targets["status"] == "capture-required"
                            or sources["status"] == "source-current" and version["status"] == "blocked")
    return {"required": blocked, "sources": sources, "version": version, "policy": policy, "target_runtime": targets}


def require_capture_current(root: Path) -> dict:
    result = capture_prerequisite(root)
    manual.require(not result["required"],
                   "Review and merge the target-host wiki capture before policy evaluation or final rehearsal")
    return result


def inspect(root: Path, *, base_ref: str | None = None) -> dict:
    root = manual.safe(root)
    identity = manual.source(root)
    prerequisite = capture_prerequisite(root)
    policy, sources = prerequisite["policy"], prerequisite["sources"]
    baseline = base_ref
    if baseline is None:
        tag = manual.git(root, "describe", "--tags", "--abbrev=0", identity["candidate_sha"], check=False)
        baseline = tag.stdout.strip() if tag.returncode == 0 else None
    version_diff = None
    if baseline:
        base = manual.git(root, "rev-parse", "--verify", baseline + "^{commit}").stdout.strip()
        project = tomllib.loads(manual.git(root, "show", base + ":pyproject.toml").stdout)
        version_diff = {"base_ref": baseline, "base_sha": base,
                        "base_version": project["project"]["version"], "candidate_version": identity["version"],
                        "changes": changes_since(root, base, identity["candidate_sha"])}
    from release import preflight
    environment = preflight._environment(root)
    helper = preflight._helper(root, environment)
    targets = prerequisite["target_runtime"]
    capture = prerequisite["required"]
    approval = policy["status"] == "approval-required"
    from release import preflight_contracts
    input_errors = preflight_contracts.release_input_errors(root)
    steps = [
        {"id": "source-review", "requires": [], "status": "committed", "sha": identity["candidate_sha"]},
        {"id": "release-inputs", "requires": ["source-review"], "status": "blocked" if input_errors else "passed", "errors": input_errors},
        {"id": "wiki-preview", "requires": ["release-inputs"], "status": "required" if capture else "source-current",
         "workflow": "reviewed-wiki-capture.yml", "inputs": {"operation": "preview", "candidate-sha": identity["candidate_sha"]}},
        {"id": "wiki-capture", "requires": ["wiki-preview"], "status": "awaiting-reviewed-preview" if capture else "source-current",
         "workflow": "reviewed-wiki-capture.yml", "approval": "approved-preview-sha256"},
        {"id": "wiki-import-review", "requires": ["wiki-capture"], "status": "pending" if capture else "source-current",
         "command": "release/wiki_capture.py preview-import"},
        {"id": "wiki-commit-and-merge", "requires": ["wiki-import-review"], "status": "pending" if capture else "source-current"},
        {"id": "policy-evaluate", "requires": ["wiki-commit-and-merge"],
         "status": "waiting-wiki" if capture and approval else "required" if approval else policy["status"],
         "command": "release/policy_renewal.py evaluate"},
        {"id": "policy-approval-review", "requires": ["policy-evaluate"],
         "status": "pending" if approval else policy["status"], "command": "release/policy_renewal.py prepare"},
        {"id": "final-plan", "requires": ["wiki-commit-and-merge", "policy-approval-review"],
         "status": "waiting-preparation" if capture or approval else "eligible-for-inspection"},
    ]
    return {"schema_version": SCHEMA, **identity, "version_diff": version_diff, "wiki": sources, "policy": policy,
            "target_runtime": targets, "active_environment": environment, "helper": helper, "steps": steps,
            "next_action": "finish-release-inputs" if input_errors else "wiki-preview" if capture else "policy-evaluate" if approval else "final-plan",
            "publication_authority": False,
            "normal_qualification": "Fresh native Action, knowledge maintenance and release qualification remain required."}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("inspect",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        from release import preflight
        root = manual.safe(args.root)
        report = inspect(root, base_ref=args.base_ref)
        preflight.write_document(args.output, report, root=root)
        print(json.dumps({"next_action": report["next_action"], "candidate_sha": report["candidate_sha"],
                          "output": str(args.output)}, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print("Release preparation failed: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
