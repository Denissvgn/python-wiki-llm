"""Declared target prerequisites cannot become runtime or publication authority."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import base64

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import doctor_cmd
from llm_wiki_cli.services import analysis_targets as targets
from llm_wiki_cli.services import analysis_compatibility as ac

ROOT = Path(__file__).parents[1]


def record(component="llm-wiki/extractor/infrastructure", *, portable=False):
    runtime = (
        ac.digest({"profile": "qualified-python-observations/v1"})
        if component == "agent-wiki-cli"
        else ac.digest(
            {
                "python": {"profile": "qualified-python-observations/v1"},
                "helper": "",
                "dependencies": {},
            }
        )
        if portable
        else ac.digest({"deliberately": "runtime-bound"})
    )
    return ac.make_record(
        component,
        "structural-observations/v1",
        "sha256:" + "1" * 64,
        "sha256:" + "2" * 64,
        runtime,
        {"platform": "darwin/arm64", "python": "3.14.5", "helper": ""},
    )


def owner(**changes):
    return {
        "owner": "project-native-owner",
        "platform": "darwin",
        "machine": "arm64",
        "python": "3.14.5",
        "implementation": "CPython",
        **changes,
    }


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        (owner(), "requirements-match"),
        (owner(platform="linux", python="3.13"), "capture-required"),
        (owner(python="3.14"), "unknown"),
        (
            owner(platform=None, machine=None, python=None, implementation=None),
            "unknown",
        ),
    ],
)
def test_nonportable_environment_comparison_is_independent_of_package_identity(
    declared, expected
):
    captured = {"llm-wiki/extractor/infrastructure": record()}
    before = deepcopy((captured, declared))
    result = targets.compare_targets(captured, [declared])
    assert result["status"] == expected
    assert (
        result["target_execution_verified"] is False
        and result["source_inventory_performed"] is False
    )
    assert (captured, declared) == before
    assert result["rows"][0]["recorded"]["implementation"] == "sha256:" + "1" * 64
    assert "not target runtime identity" in result["qualification"]


def test_registered_portability_requires_runtime_commitment_and_target_profile():
    r = record("llm-wiki/extractor/python", portable=True)
    result = targets.compare_targets(
        {r["component"]: r}, [owner(platform="linux", machine="x86_64", python="3.13")]
    )
    assert result["rows"][0]["state"] == "portable"
    assert result["status"] == "requirements-match"
    assert (
        targets.compare_targets(
            {r["component"]: r}, [owner(platform="linux", machine=None)]
        )["status"]
        == "unknown"
    )
    assert (
        targets.compare_targets(
            {r["component"]: r}, [owner(platform="freebsd", machine="x86_64")]
        )["status"]
        == "unknown"
    )
    nonportable = record("llm-wiki/extractor/python")
    assert (
        targets.compare_targets(
            {nonportable["component"]: nonportable}, [owner(platform="linux")]
        )["status"]
        == "capture-required"
    )


def test_missing_invalid_or_unselected_records_never_prove_matching():
    assert targets.compare_targets({}, [owner()])["status"] == "unknown"
    assert targets.compare_targets({"bad": record()}, [owner()])["status"] == "unknown"
    assert targets.compare_targets({}, [])["status"] == "unknown"
    assert (
        targets.compare_targets(
            {"llm-wiki/extractor/infrastructure": record()},
            [owner(components=["not-recorded"])],
        )["status"]
        == "unknown"
    )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        True,
        [{"owner": "a", "platform": False}],
        [{"owner": "a", "python": "latest"}],
        [{"owner": "a", "command": "execute-me"}],
        [{"owner": "a"}, {"owner": "a"}],
        [owner(components=[])],
        [owner(helpers={"python": False})],
    ],
)
def test_target_metadata_is_closed_data(payload):
    with pytest.raises(ValueError):
        targets.normalize_targets(payload)


def test_omitted_rows_do_not_hide_capture_requirement():
    many = [owner(owner=f"owner-{i}") for i in range(16)]
    # Distinct supported component captures produce >32 rows.
    records = {}
    for name in (
        "agent-wiki-cli",
        "llm-wiki/extractor/python",
        "llm-wiki/extractor/infrastructure",
    ):
        records[name] = record(name)
    many[-1]["platform"] = "linux"
    result = targets.compare_targets(records, many)
    assert result["bounds"] == {"total": 48, "returned": 32, "truncated": True}
    assert (
        result["status"] == "capture-required"
        and result["counts"]["capture-required"] > 0
    )


def test_snapshot_reader_and_cli_do_not_scan_sources_or_execute(
    monkeypatch, tmp_path, capsys
):
    from llm_wiki_cli.services import (
        source_snapshot,
        extraction_service,
        analysis_capture,
    )

    def forbidden(*args, **kwargs):
        pytest.fail("target prerequisite inspection performed forbidden work")

    monkeypatch.setattr(source_snapshot, "build_source_snapshot", forbidden)
    monkeypatch.setattr(extraction_service, "get_inventory_result", forbidden)
    monkeypatch.setattr(analysis_capture, "capture_analysis", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    fixture = json.loads(
        (ROOT / "tests/fixtures/scoped_repair_2_5_0_mixed.json").read_text()
    )
    for name, content in fixture["files"].items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(content))
    wiki = tmp_path / "wiki"
    names = [
        ".llm-wiki-knowledge.json",
        ".llm-wiki-manifest.json",
        ".llm-wiki-surface.json",
    ]
    before = {n: hashlib.sha256((wiki / n).read_bytes()).hexdigest() for n in names}
    result = targets.inspect_targets(
        wiki, [owner(platform="linux", machine="x86_64", python="3.13")]
    )
    assert result["snapshot_binding"] is not None, result
    assert before == {
        n: hashlib.sha256((wiki / n).read_bytes()).hexdigest() for n in names
    }
    monkeypatch.chdir(tmp_path)
    Path("targets.json").write_text(json.dumps({"targets": [owner(platform="linux")]}))
    with pytest.raises(SystemExit) as inspected:
        doctor_cmd.run(
            cli._build_parser().parse_args(
                [
                    "doctor",
                    "--target-runtime",
                    "targets.json",
                    "--wiki-dir",
                    "wiki",
                    "--format",
                    "json",
                ]
            )
        )
    assert inspected.value.code == 2
    assert (
        json.loads(capsys.readouterr().out)["snapshot_binding"]
        == result["snapshot_binding"]
    )
    with pytest.raises(SystemExit) as stopped:
        doctor_cmd.run(
            cli._build_parser().parse_args(
                [
                    "doctor",
                    "--target-runtime",
                    "targets.json",
                    "--wiki-dir",
                    "missing",
                    "--format",
                    "json",
                ]
            )
        )
    assert stopped.value.code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "unknown"
    assert not Path("missing").exists()


def test_target_file_parser_rejects_duplicate_fields_and_future_commands(tmp_path):
    path = tmp_path / "targets.json"
    for raw in (
        '{"targets":[],"targets":[]}',
        '{"targets":[],"run":"shell"}',
        '{"targets":[{"owner":"x","python":NaN}]}',
    ):
        path.write_text(raw)
        with pytest.raises(ValueError):
            targets.load_targets(path)


def test_helper_portability_needs_declared_matching_toolchain():
    from llm_wiki_cli.services.analysis_capture import registry

    rules = registry()
    toolchain = rules["portable_helper_toolchains"]["typescript"]
    helper = (
        toolchain + "; active-node " + toolchain.split(";", 1)[0].removeprefix("node ")
    )
    component = "llm-wiki/extractor/javascript"
    r = ac.make_record(
        component,
        "structural-observations/v1",
        "sha256:" + "1" * 64,
        "sha256:" + "2" * 64,
        ac.digest(
            {
                "python": {"profile": "qualified-python-observations/v1"},
                "helper": helper,
                "dependencies": {},
            }
        ),
        {"platform": "darwin/arm64", "python": "3.14.5", "helper": helper},
    )
    target = owner(platform="linux", machine="x86_64", python="3.13")
    assert targets.compare_targets({component: r}, [target])["status"] == "unknown"
    target["helpers"] = {component: helper}
    assert (
        targets.compare_targets({component: r}, [target])["rows"][0]["state"]
        == "portable"
    )
    target["helpers"][component] = "declared-other-helper"
    assert (
        targets.compare_targets({component: r}, [target])["status"]
        == "capture-required"
    )


def test_bounded_response_retains_global_mismatch_even_when_rows_are_omitted():
    records = {
        name: record(name)
        for name in (
            "llm-wiki/extractor/python",
            "llm-wiki/extractor/infrastructure",
            "agent-wiki-cli",
        )
    }
    many = [
        owner(owner=f"owner-{i}" + "界" * 180, capture_route="界" * 500)
        for i in range(16)
    ]
    many[-1]["platform"] = "linux"
    result = targets.compare_targets(records, many)
    assert (
        len(json.dumps(result, ensure_ascii=True).encode()) <= targets.MAX_TARGET_BYTES
    )
    assert result["status"] == "capture-required" and result["bounds"]["truncated"]


@pytest.mark.parametrize("extra", [["--strict"], ["--comparison-policy", "exact-v1"]])
def test_target_mode_cannot_replace_strict_health_or_comparison_policy(extra):
    args = cli._build_parser().parse_args(
        ["doctor", "--target-runtime", "missing.json", *extra]
    )
    with pytest.raises(ValueError, match="checks declared prerequisites only"):
        doctor_cmd.run(args)


def test_large_component_sets_are_unknown_without_materializing_unbounded_rows():
    result = targets.compare_targets({str(i): None for i in range(65)}, [owner()])
    assert (
        result["status"] == "unknown"
        and result["selection"]["component_limit_exceeded_or_invalid"]
    )
    assert result["bounds"]["total"] == 1


def test_explicit_component_selection_discloses_unselected_requirements():
    records = {
        name: record(name)
        for name in ("llm-wiki/extractor/python", "llm-wiki/extractor/infrastructure")
    }
    result = targets.compare_targets(
        records, [owner(components=["llm-wiki/extractor/infrastructure"])]
    )
    assert result["selection"]["unselected_component_pairs"] == 1
    assert result["bounds"]["total"] == 1 and not result["target_execution_verified"]
