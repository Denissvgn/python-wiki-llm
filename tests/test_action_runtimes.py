"""Keep workflow and composite action dependencies on reviewed Node 24 runtimes."""

import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).parents[1]


def definitions():
    return sorted(
        path
        for suffix in ("yml", "yaml")
        for path in [
            *(ROOT / ".github/workflows").glob("*." + suffix),
            *(ROOT / "integrations").glob("*/action." + suffix),
        ]
    )


def action_steps(value):
    if isinstance(value, dict):
        if isinstance(value.get("uses"), str):
            yield value
        for child in value.values():
            yield from action_steps(child)
    elif isinstance(value, list):
        for child in value:
            yield from action_steps(child)


def test_every_executable_action_and_nested_dependency_has_a_reviewed_modern_runtime():
    policy = json.loads((ROOT / "release/action-runtimes.json").read_text())
    assert policy["schema_version"] == "agent-wiki-action-runtimes/v1"
    assert policy["minimum_node_major"] == 24
    actions = policy["actions"]
    pending = set()
    for path in definitions():
        value = yaml.safe_load(path.read_text())
        if "runs" in value:
            assert value["runs"]["using"] == "composite"
        pending.update(
            step["uses"]
            for step in action_steps(value)
            if not step["uses"].startswith("./")
        )
    seen = set()
    while pending:
        reference = pending.pop()
        if reference in seen:
            continue
        assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", reference), reference
        assert reference in actions, f"Action runtime requires review: {reference}"
        record = actions[reference]
        assert re.fullmatch(r"[0-9a-f]{64}", record["manifest_sha256"])
        assert record["using"] in {"node24", "composite"}, reference
        assert all(
            runtime == "docker" for runtime in record["generated_actions"].values()
        )
        if record["using"] == "node24":
            assert not record["dependencies"] and not record["generated_actions"]
        else:
            assert record["dependencies"] or record["generated_actions"]
        pending.update(record["dependencies"])
        seen.add(reference)
    assert seen == set(actions), "Remove unused runtime exemptions"


def test_artifact_runtime_upgrade_preserves_archives_and_rejects_digest_mismatches():
    upload = download = 0
    for path in definitions():
        for step in action_steps(yaml.safe_load(path.read_text())):
            if step["uses"].startswith("actions/upload-artifact@"):
                upload += 1
                assert step["with"]["archive"] is True, (path, step)
            elif step["uses"].startswith("actions/download-artifact@"):
                download += 1
                assert step["with"]["digest-mismatch"] == "error", (path, step)
    assert upload and download


def test_node_runtime_migration_does_not_use_warning_suppression_or_legacy_opt_outs():
    for path in definitions():
        text = path.read_text()
        assert "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION" not in text
        assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24" not in text
        assert "NODE_NO_WARNINGS" not in text
        assert "actions/attest-sbom@" not in text
