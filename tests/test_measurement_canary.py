"""Canary completeness and partial evidence controls without native emulation."""

import tarfile
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest

from release import measurement_canary as canary


def complete_result():
    critical = (
        canary.MODULE + "::test_timed_read_and_mutation_restore_equivalent_inputs"
    )
    nodes = [critical + "[" + group + "]" for group in canary.GROUPS]
    nodes += [canary.MODULE + "::test_other_" + str(i) for i in range(13)]
    collection = {"collected": nodes, "selected": list(nodes), "deselected": []}
    cases = {n: ET.Element("testcase") for n in nodes}
    capture = {"complete": True, "measurement_roots": list(canary.GROUPS)}
    return collection, list(nodes), cases, capture


def test_complete_canary_requires_every_collected_started_junit_node_and_five_groups():
    data = complete_result()
    assert canary.validate_results(*data) == {
        "collected": 18,
        "started": 18,
        "passed": 18,
        "skipped": 0,
        "deselected": 0,
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "deselect",
        "missing-group",
        "not-started",
        "duplicate-start",
        "missing-junit",
        "skip",
        "failure",
        "partial-raw",
        "missing-raw-group",
    ],
)
def test_incomplete_or_failed_measurement_evidence_never_passes(mutation):
    collection, started, cases, capture = complete_result()
    first = collection["collected"][0]
    if mutation == "duplicate":
        collection["collected"].append(first)
    elif mutation == "deselect":
        collection["deselected"].append(first)
    elif mutation == "missing-group":
        collection["collected"][0] = collection["selected"][0] = started[0] = (
            canary.MODULE + "::test_replacement"
        )
        cases[canary.MODULE + "::test_replacement"] = cases.pop(first)
    elif mutation == "not-started":
        started.pop()
    elif mutation == "duplicate-start":
        started.append(first)
    elif mutation == "missing-junit":
        cases.pop(first)
    elif mutation in {"skip", "failure"}:
        ET.SubElement(cases[first], "skipped" if mutation == "skip" else "failure")
    elif mutation == "partial-raw":
        capture["complete"] = False
    else:
        capture["measurement_roots"].pop()
    with pytest.raises(canary.CanaryError):
        canary.validate_results(collection, started, cases, capture)


def test_raw_report_capture_retains_partial_worker_outputs(tmp_path):
    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    report = basetemp / "failed-worker/measurements/partial/sample.json"
    report.parent.mkdir(parents=True)
    report.write_text('{"stage":"before-timeout"}')
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert result["complete"] and result["files"][
        "failed-worker/measurements/partial/sample.json"
    ]["sha256"] == canary.sha(report)
    with tarfile.open(out / "measurement-reports.tar") as archive:
        assert (
            archive.extractfile("failed-worker/measurements/partial/sample.json").read()
            == report.read_bytes()
        )


def test_raw_capture_refuses_report_aliases_and_preserves_external_bytes(tmp_path):
    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    reports = basetemp / "worker/measurements"
    reports.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"do not read through a report alias")
    (reports / "aliased.json").symlink_to(outside)
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert result["complete"] is False and result["files"] == {}
    assert outside.read_bytes() == b"do not read through a report alias"


def test_raw_capture_byte_limit_is_enforced_without_deleting_worker_data(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(canary, "MAX_REPORT_BYTES", 3)
    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    reports = basetemp / "worker/measurements"
    reports.mkdir(parents=True)
    (reports / "large.json").write_bytes(b"1234")
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert not result["complete"] and (reports / "large.json").read_bytes() == b"1234"


def test_wrong_native_runtime_fails_before_collection_or_source_mutation(
    tmp_path, monkeypatch
):
    root, out = tmp_path / "candidate", tmp_path / "out"
    root.mkdir()
    (root / "sentinel").write_bytes(b"preserve")
    monkeypatch.setattr(canary, "sys", SimpleNamespace(platform="linux"))
    args = SimpleNamespace(root=root, output=out, expected_python="3.13.17")
    with pytest.raises(canary.CanaryError, match="native Windows"):
        canary.run(args)
    assert not out.exists() and (root / "sentinel").read_bytes() == b"preserve"


def test_raw_capture_materializes_shared_regular_bytes_without_following_aliases(
    tmp_path,
):
    import os

    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    reports = basetemp / "worker/measurements"
    reports.mkdir(parents=True)
    source = reports / "one.json"
    source.write_bytes(b"shared immutable recovery content")
    os.link(source, reports / "two.json")
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert result["complete"] and len(result["files"]) == 2
    with tarfile.open(out / "measurement-reports.tar") as archive:
        members = archive.getmembers()
        assert all(member.isfile() for member in members)
        assert [archive.extractfile(member).read() for member in members] == [
            source.read_bytes()
        ] * 2
    assert source.stat().st_nlink == 2
