"""Stdlib-only release admission for the captured repository-health policy."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tarfile

POLICY_PATH = "release/knowledge-maintenance.json"
CONFIG_SCHEMA = "agent-wiki-release-knowledge-maintenance/v1"
CONFIG_V2_SCHEMA = "agent-wiki-release-knowledge-maintenance/v2"
VERIFICATION_SCHEMA = "agent-wiki-release-knowledge-verification/v1"
LEAF_PATH = "src/llm_wiki_cli/services/health_policy.py"
POLICY_INPUTS = (LEAF_PATH, "src/llm_wiki_cli/services/analysis_compatibility.py",
                 "src/llm_wiki_cli/services/analysis_contracts.json", "release/knowledge_maintenance.py")


def composite_policy_digest(read_bytes) -> str:
    entries = {name: hashlib.sha256(read_bytes(name)).hexdigest() for name in POLICY_INPUTS}
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()



def leaf():
    path = Path(__file__).resolve().parents[1] / LEAF_PATH
    spec = importlib.util.spec_from_file_location("_release_health_policy", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def policy(raw: bytes, *, implementation_hash: str | None = None):
    module = leaf()
    value = module.strict_json(raw)
    if set(value) != {
        "schema_version",
        "mode",
        "policy",
        "src_dir",
        "wiki_dir",
        "selection",
        "activation",
    }:
        raise ValueError("invalid maintenance configuration fields")
    if (
        value["schema_version"] not in {CONFIG_SCHEMA, CONFIG_V2_SCHEMA}
        or value["policy"] != (module.POLICY_V2_ID if value["schema_version"] == CONFIG_V2_SCHEMA else module.POLICY_ID)
        or value["mode"] not in {"shadow", "required", "disabled"}
    ):
        raise ValueError("unsupported maintenance configuration")
    if (value["src_dir"], value["wiki_dir"], value["selection"]) != (
        ".",
        "docs/llm_wiki",
        ".llm-wiki/source-selection.json",
    ):
        raise ValueError(
            "release maintenance must evaluate the declared actual repository"
        )
    if value["mode"] == "required":
        activation = value["activation"]
        if not isinstance(activation, dict) or set(activation) != {
            "candidate_sha",
            "run_id",
            "attempt",
            "comparison_sha256",
            "implementation_sha256",
        }:
            raise ValueError(
                "required maintenance lacks a reviewed hosted activation record"
            )
        if (
            not re.fullmatch(r"[0-9a-f]{40}", str(activation["candidate_sha"]))
            or type(activation["run_id"]) is not int
            or activation["run_id"] <= 0
            or type(activation["attempt"]) is not int
            or activation["attempt"] <= 0
        ):
            raise ValueError("invalid activation run identity")
        if not re.fullmatch(r"[0-9a-f]{64}", str(activation["comparison_sha256"])):
            raise ValueError("invalid activation evidence digest")
        root = Path(__file__).resolve().parents[1]
        current = implementation_hash or (
            composite_policy_digest(lambda name: (root / name).read_bytes())
            if value["schema_version"] == CONFIG_V2_SCHEMA
            else hashlib.sha256((root / LEAF_PATH).read_bytes()).hexdigest()
        )
        if activation["implementation_sha256"] != current:
            raise ValueError("health policy changed since its reviewed shadow proof")
    return value


def read(path: Path, limit=64 * 1024 * 1024) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("missing, redirected or oversized maintenance evidence")
    return path.read_bytes()


def version_check(root: Path, config) -> dict:
    if config["mode"] == "disabled":
        return {
            "schema_version": "agent-wiki-release-knowledge-version/v1",
            "mode": "disabled",
            "status": "disabled",
            "candidate_version": None,
            "recorded_version": None,
            "remedy": "Additional maintenance policy is disabled; existing release gates still apply.",
        }
    module = leaf()
    text = (root / "pyproject.toml").read_text("utf-8")
    section = re.search(r"(?ms)^\[project\]\s*\n(.*?)(?=^\[|\Z)", text)
    versions = re.findall(
        r'(?m)^version\s*=\s*"([^"]+)"\s*(?:#.*)?$', section[1] if section else ""
    )
    if len(versions) != 1:
        raise ValueError("candidate requires one explicit project version")
    raw = module.strict_json(
        read(root / config["wiki_dir"] / ".llm-wiki-knowledge.json")
    )
    bundle = (
        raw["store"]["bundle"]
        if raw["schema_version"] in {"llm-wiki-knowledge/v3", "llm-wiki-knowledge/v4"}
        else raw["bundle"]
    )
    recorded = bundle["producer"]["tool"]["version"]
    ready = recorded == versions[0] and recorded != "unknown"
    deferred = False
    if config["schema_version"] == CONFIG_V2_SCHEMA:
        record = module.ac.component_record(bundle["producer"]["tool"])
        if record is None:
            ready = False
        if record is not None:
            module.ac.validate_record(record, "agent-wiki-cli")
            rules = module.strict_json(read(root / "src/llm_wiki_cli/services/analysis_contracts.json"))
            inputs = {name: hashlib.sha256(read(root / "src/llm_wiki_cli" / name).replace(b"\r\n", b"\n")).hexdigest() for name in sorted(rules["shared"])}
            ready = record["implementation"] == module.ac.digest(inputs)
            deferred = ready

    return {
        "schema_version": "agent-wiki-release-knowledge-version/v2" if config["schema_version"] == CONFIG_V2_SCHEMA else "agent-wiki-release-knowledge-version/v1",
        "mode": config["mode"],
        "status": "full-preflight-required" if deferred else "ready" if ready else "blocked",
        "candidate_version": versions[0],
        "recorded_version": recorded,
        "remedy": "Refresh the committed wiki with the intended installed candidate before qualification.",
    }


def admit(evidence: Path, identity, config, *, scope_prefix="candidate") -> dict:
    module = leaf()
    result = {
        "schema_version": VERIFICATION_SCHEMA,
        "mode": config["mode"],
        "candidate_sha": identity["source"]["sha"],
        "candidate_tree": identity["source"]["tree"],
        "candidate_version": identity["version"],
        "status": "disabled",
        "evidence_sha256": {},
        "error": None,
    }
    if config["mode"] == "disabled":
        return result
    try:
        payloads = {
            name: read(evidence / name)
            for name in ("ci-report.json", "preflight.json", "policy.json")
        }
        preflight = module.strict_json(payloads["preflight.json"])
        binding = preflight["binding"]
        expected = {
            "candidate_sha": identity["source"]["sha"],
            "candidate_tree": identity["source"]["tree"],
            "candidate_version": identity["version"],
            "source_archive_sha256": "sha256:" + identity["source"]["archive_sha256"],
            "src_dir": scope_prefix,
            "wiki_dir": scope_prefix + "/" + config["wiki_dir"],
        }
        if any(binding.get(key) != value for key, value in expected.items()):
            raise ValueError(
                "maintenance evidence belongs to a different candidate or scope"
            )
        receipt = module.strict_json(payloads["policy.json"])
        rebuilt = module.verify_policy(
            receipt,
            payloads["ci-report.json"],
            payloads["preflight.json"],
            binding=binding,
            validate_full_report=False,
        )
        if rebuilt["policy"] != config["policy"]:
            raise ValueError("captured policy differs from the configured release contract")
        if rebuilt["status"] != "pass":
            raise ValueError(
                "repository health policy failed: " + ", ".join(rebuilt["reasons"])
            )
        if config["schema_version"] == CONFIG_V2_SCHEMA:
            if receipt["policy"] != module.POLICY_V2_ID or module.strict_json(payloads["ci-report.json"])["knowledge_health"]["health_details"]["basis"]["policy"] != "analysis-v1":
                raise ValueError("release compatibility admission requires analysis-v1 evidence")
        if preflight["installed"]["editable"] is not False:
            raise ValueError("release maintenance requires a noneditable installation")
        if config["mode"] == "shadow":
            raw = read(evidence / "doctor.json")
            doctor = module.strict_json(raw)
            expected_doctor = module.strict_health_projection(
                module.strict_json(payloads["ci-report.json"])["knowledge_health"],
                validate_full_report=False,
            )
            if doctor != expected_doctor:
                raise ValueError(
                    "standalone strict doctor differs from the derived projection"
                )
            payloads["doctor.json"] = raw
        result.update(
            status="pass",
            evidence_sha256={
                name: module.digest(raw) for name, raw in payloads.items()
            },
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result.update(status="fail", error=str(exc)[:2000])
    return result


def bundle_policy(bundle: Path):
    source = bundle / "evidence/RD-00/source"
    archive = source / "candidate-source.tar"
    with tarfile.open(archive, "r:") as tar:
        names = [entry.name for entry in tar]
        if len(names) != len(set(names)):
            raise ValueError("duplicate frozen source archive member")
        try:
            member = tar.getmember(POLICY_PATH)
        except KeyError:
            return None  # Earlier qualified source predates this additional policy.
        if not member.isfile() or member.size > 65536:
            raise ValueError("invalid frozen maintenance configuration")
        stream = tar.extractfile(member)
        assert stream
        with stream:
            policy_bytes = stream.read()
        implementation_member = tar.getmember(LEAF_PATH)
        if (
            not implementation_member.isfile()
            or implementation_member.size > 1024 * 1024
        ):
            raise ValueError("invalid frozen health-policy implementation")
        implementation = tar.extractfile(implementation_member)
        if implementation is None:
            raise ValueError("frozen health-policy implementation is missing")
        with implementation:
            implementation_hash = hashlib.sha256(implementation.read()).hexdigest()
        if leaf().strict_json(policy_bytes)["schema_version"] == CONFIG_V2_SCHEMA:
            def frozen_input(name):
                item = tar.getmember(name)
                if not item.isfile() or item.size > 1024 * 1024:
                    raise ValueError("invalid composite policy input")
                stream = tar.extractfile(item)
                if stream is None:
                    raise ValueError("missing composite policy input")
                with stream:
                    return stream.read()
            implementation_hash = composite_policy_digest(frozen_input)
        config = policy(policy_bytes, implementation_hash=implementation_hash)
    identity = leaf().strict_json(read(source / "identity.json"))
    result = admit(bundle / "evidence/RD-10/action/maintenance", identity, config)
    if config["mode"] == "required" and result["status"] != "pass":
        raise ValueError("required bundled repository maintenance is missing or failed")
    if config["mode"] == "required":
        verified = leaf().strict_json(
            read(bundle / "evidence/RD-10/maintenance/verification.json")
        )
        if json.dumps(verified, sort_keys=True) != json.dumps(result, sort_keys=True):
            raise ValueError(
                "bundled maintenance producer verification differs from its inputs"
            )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    before = commands.add_parser("check-version")
    before.add_argument("--root", type=Path, required=True)
    check = commands.add_parser("verify")
    check.add_argument("--evidence", type=Path, required=True)
    check.add_argument("--identity", type=Path, required=True)
    check.add_argument("--policy", type=Path, required=True)
    for p in (before, check):
        p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config = policy(
            read(
                args.root / POLICY_PATH
                if args.command == "check-version"
                else args.policy
            )
        )
        result = (
            version_check(args.root, config)
            if args.command == "check-version"
            else admit(args.evidence, leaf().strict_json(read(args.identity)), config)
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
        print(json.dumps({"mode": config["mode"], "status": result["status"]}))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            meaning = {
                "shadow": "Diagnostic shadow; this result does not add a release blocker.",
                "required": "Required repository-health prerequisite.",
                "disabled": "Additional repository-health policy is explicitly disabled; existing gates remain required.",
            }[config["mode"]]
            with Path(summary).open("a", encoding="utf-8") as stream:
                stream.write(
                    "## Repository knowledge maintenance\n\n"
                    f"Mode: **{config['mode']}**. Result: **{result['status']}**.\n\n{meaning}\n\n"
                )
        if args.command == "check-version":
            return 1 if result["status"] == "blocked" else 0
        return (
            1
            if config["mode"] == "required"
            and result["status"] not in {"pass", "ready"}
            else 0
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"release maintenance evidence failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
