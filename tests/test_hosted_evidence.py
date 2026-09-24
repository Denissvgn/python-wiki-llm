"""No JUnit bytes qualify without authenticated hosted producer provenance."""

from copy import deepcopy
import os
from pathlib import Path
import zipfile
import io

import pytest

from release import hosted_evidence as h, qualification as q
from tests.hosted_evidence_fixtures import HostedEvidence


@pytest.fixture
def hosted(tmp_path, monkeypatch):
    return _hosted(tmp_path, monkeypatch, "unsharded")


@pytest.fixture
def sharded_hosted(tmp_path, monkeypatch):
    return _hosted(tmp_path, monkeypatch, "windows-sharded")


def _hosted(tmp_path, monkeypatch, core_layout):
    source = tmp_path / "source"
    source.mkdir()
    archive = source / "candidate-source.tar"
    archive.write_bytes(b"owned source")
    identity = {
        "schema_version": q.IDENTITY_SCHEMA,
        "repository": "owned/repo",
        "source": {
            "sha": "a" * 40,
            "tree": "b" * 40,
            "archive_sha256": q.sha256_file(archive),
            "commit_epoch": 1,
        },
        "version": "1.0.0",
        "tag": "v1.0.0",
        "mode": "candidate",
    }
    q.write_json(source / "identity.json", identity)
    (source / "SHA256SUMS").write_text(
        q.sha256_file(archive) + "  candidate-source.tar\n"
    )
    server = HostedEvidence(identity, 123, source, core_layout=core_layout)
    root = tmp_path / "bundle"
    for spec in server.specs(tmp_path / "inputs"):
        binding, _, directory = spec.partition("=")
        gate, label = binding.split(":")
        for path in Path(directory).rglob("*"):
            if path.is_file():
                output = root / "evidence" / gate / label / path.relative_to(directory)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(path.read_bytes())
    monkeypatch.setattr(h, "GitHub", server.client)
    return root, server


def test_exact_hosted_artifacts_produce_deterministic_complete_bindings(hosted):
    root, server = hosted
    result = h.verify(root, server.identity, server.context, server.run_id)
    assert result == h.verify(root, server.identity, server.context, server.run_id)
    assert set(result["bindings"]) == set(h.artifact_contract("legacy"))
    assert result["bindings"]["RD-03:slow"]["files"]["slow.xml"] == q.sha256_file(
        root / "evidence/RD-03/slow/slow.xml"
    )


@pytest.mark.parametrize(
    "mutation",
    ["bare-xml", "strip-json", "tamper", "unbound", "rename-label", "empty-junit-gate"],
)
def test_unbound_or_stripped_xml_cannot_pass_even_with_valid_gate_statuses(
    hosted, mutation
):
    root, server = hosted
    directory = root / "evidence/RD-03/slow"
    if mutation == "bare-xml":
        for path in directory.iterdir():
            if path.name != "slow.xml":
                path.unlink()
    elif mutation == "strip-json":
        for path in root.rglob("*.json"):
            path.unlink()
    elif mutation == "tamper":
        (directory / "slow.xml").write_text("<testsuite/>")
    elif mutation == "unbound":
        extra = root / "evidence/RD-09/injected/slow.xml"
        extra.parent.mkdir(parents=True)
        extra.write_bytes((directory / "slow.xml").read_bytes())
    elif mutation == "rename-label":
        directory.rename(directory.with_name("forged"))
    else:
        (directory / "slow.xml").unlink()
        (directory / "determinism.xml").unlink()
    with pytest.raises(h.EvidenceError):
        h.verify(root, server.identity, server.context, server.run_id)


@pytest.mark.parametrize(
    "mutation",
    [
        "run-failed",
        "run-sha",
        "run-attempt",
        "repo",
        "job-failed",
        "job-skipped",
        "job-cancelled",
        "job-missing",
        "job-duplicate",
        "job-sha",
        "expired",
        "artifact-run",
        "artifact-sha",
        "artifact-time",
        "artifact-duplicate",
        "digest-missing",
        "digest-mismatch",
        "archive-tampered",
    ],
)
def test_remote_provenance_cannot_be_replaced_by_self_asserted_receipts(
    hosted, mutation
):
    root, server = hosted
    artifact = server.artifacts[0]
    job = next(
        j
        for j in server.jobs
        if j["name"] == "RD-03 slow, scale, bounds, and determinism"
    )
    if mutation == "run-failed":
        server.run["conclusion"] = "failure"
    elif mutation == "run-sha":
        server.run["head_sha"] = "f" * 40
    elif mutation == "run-attempt":
        server.run["run_attempt"] = 2
    elif mutation == "repo":
        server.run["head_repository"]["full_name"] = "elsewhere/repo"
    elif mutation.startswith("job-"):
        variant = mutation.removeprefix("job-")
        if variant == "missing":
            server.jobs.remove(job)
        elif variant == "duplicate":
            server.jobs.append(deepcopy(job))
        elif variant == "sha":
            job["head_sha"] = "f" * 40
        else:
            job["conclusion"] = {
                "failed": "failure",
                "skipped": "skipped",
                "cancelled": "cancelled",
            }[variant]
    elif mutation == "expired":
        artifact["expired"] = True
    elif mutation == "artifact-run":
        artifact["workflow_run"]["id"] = 124
    elif mutation == "artifact-sha":
        artifact["workflow_run"]["head_sha"] = "f" * 40
    elif mutation == "artifact-time":
        artifact["created_at"] = "2026-09-21T00:00:00Z"
    elif mutation == "artifact-duplicate":
        server.artifacts.append(deepcopy(artifact))
    elif mutation == "digest-missing":
        artifact.pop("digest")
    elif mutation == "digest-mismatch":
        artifact["digest"] = "sha256:" + "0" * 64
    elif mutation == "archive-tampered":
        server.archives[artifact["id"]] += b"changed"
    with pytest.raises(h.EvidenceError):
        h.verify(root, server.identity, server.context, server.run_id)


def test_shadow_job_cannot_be_relabelled_as_a_qualifying_producer(hosted):
    root, server = hosted
    job = next(
        j
        for j in server.jobs
        if j["name"] == "RD-03 slow, scale, bounds, and determinism"
    )
    job["name"] = "Ubuntu suites shadow comparison"
    with pytest.raises(h.EvidenceError, match="hosted producer"):
        h.verify(root, server.identity, server.context, server.run_id)


@pytest.mark.parametrize(
    "member",
    [
        "../escape.xml",
        "/absolute.xml",
        "C:/drive.xml",
        "sub\\test.xml",
        "a//b.xml",
        "a/./b.xml",
        "slow.xml\x00hidden",
        "sub\\",
        "sub//",
    ],
)
@pytest.mark.parametrize("separator", ["/", "\\"], ids=["posix", "windows"])
def test_hosted_zip_members_are_bounded_and_canonical(member, separator, monkeypatch):
    # Exercise CPython's actual host-dependent ZIP normalization on every CI
    # platform. The fixture must retain the malformed name in the ZIP headers.
    with monkeypatch.context() as platform:
        platform.setattr(os, "sep", separator)
        platform.setattr(os, "altsep", "/" if separator == "\\" else None)
        raw = HostedEvidence.zip({member: b"owned"})
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            assert archive.infolist()[0].orig_filename == member
        with pytest.raises(h.EvidenceError, match="artifact member"):
            h.zip_inventory(raw)


@pytest.mark.parametrize("separator", ["/", "\\"], ids=["posix", "windows"])
def test_canonical_zip_names_and_directories_work_on_every_host(separator, monkeypatch):
    with monkeypatch.context() as platform:
        platform.setattr(os, "sep", separator)
        platform.setattr(os, "altsep", "/" if separator == "\\" else None)
        raw = HostedEvidence.zip(
            {"sub/": b"", "sub/test.xml": b"owned", "slow.xml": b"other"}
        )
        assert h.zip_inventory(raw) == {
            "slow.xml": h.sha256(b"other"),
            "sub/test.xml": h.sha256(b"owned"),
        }


def test_symlink_zip_members_are_rejected():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        entry = zipfile.ZipInfo("link.xml")
        entry.external_attr = 0o120777 << 16
        archive.writestr(entry, b"target")
    with pytest.raises(h.EvidenceError, match="symlink"):
        h.zip_inventory(stream.getvalue())


def test_duplicate_zip_members_are_rejected():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("slow.xml", b"original")
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("slow.xml", b"substituted")
    with pytest.raises(h.EvidenceError, match="duplicate"):
        h.zip_inventory(stream.getvalue())


@pytest.mark.parametrize("count", [-1, True, "1", None])
def test_invalid_pagination_cannot_drop_required_metadata(monkeypatch, count):
    monkeypatch.setenv("GITHUB_TOKEN", "owned-secret")
    client = h.GitHub("owned/repo")
    monkeypatch.setattr(client, "get", lambda path: {"total_count": count, "jobs": []})
    with pytest.raises(h.EvidenceError, match="paginated"):
        client.list("/owned", "jobs")


def test_artifact_archives_have_a_redirect_bound(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "owned-secret")
    calls = []

    def request(url, token, limit):
        calls.append(token)
        return 302, {"Location": "https://owned.invalid/loop"}, b""

    monkeypatch.setattr(h, "_http", request)
    with pytest.raises(h.EvidenceError, match="redirect bound"):
        h.GitHub("owned/repo").archive(1)
    assert calls == ["owned-secret", None, None, None, None]


def test_artifact_redirect_never_receives_the_api_bearer_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "owned-secret")
    calls = []

    def request(url, token, limit):
        calls.append((url, token))
        if len(calls) == 1:
            return 302, {"Location": "https://owned.invalid/signed"}, b""
        return 200, {}, b"owned zip"

    monkeypatch.setattr(h, "_http", request)
    assert h.GitHub("owned/repo").archive(1) == b"owned zip"
    assert [token for _, token in calls] == ["owned-secret", None]


def test_auth_cannot_be_sent_to_another_origin():
    with pytest.raises(h.EvidenceError, match="credentials"):
        h._http("https://owned.invalid/", "secret", 100)


def test_sharded_provenance_requires_planner_both_workers_and_logical_gate(
    sharded_hosted,
):
    root, server = sharded_hosted
    ledger = h.verify(root, server.identity, server.context, server.run_id)
    assert set(ledger["bindings"]) == set(
        h.artifact_contract("legacy", "windows-sharded")
    )
    for label in ("windows", "windows-plan", "windows-shard-0", "windows-shard-1"):
        assert ledger["bindings"]["RD-01:" + label]["producer_job_id"] > 0


@pytest.mark.parametrize(
    "binding", ["windows-plan", "windows-shard-0", "windows-shard-1", "windows"]
)
@pytest.mark.parametrize(
    "mutation",
    [
        "missing-job",
        "failed-job",
        "cancelled-job",
        "wrong-attempt",
        "missing-artifact",
        "stripped-sidecars",
    ],
)
def test_successful_logical_job_cannot_hide_an_invalid_shard_producer(
    sharded_hosted, binding, mutation
):
    root, server = sharded_hosted
    name, producer, _ = h.artifact_contract("legacy", "windows-sharded")[
        "RD-01:" + binding
    ]
    job = next(j for j in server.jobs if j["name"] == producer)
    artifact = next(a for a in server.artifacts if a["name"] == name)
    if mutation == "missing-job":
        server.jobs.remove(job)
    elif mutation in {"failed-job", "cancelled-job"}:
        job["conclusion"] = "failure" if mutation == "failed-job" else "cancelled"
    elif mutation == "wrong-attempt":
        job["run_attempt"] += 1
    elif mutation == "missing-artifact":
        server.artifacts.remove(artifact)
    else:
        directory = root / "evidence/RD-01" / binding
        for path in directory.glob("*.json"):
            path.unlink()
    with pytest.raises(h.EvidenceError):
        h.verify(root, server.identity, server.context, server.run_id)


def test_unsharded_provenance_cannot_adopt_shard_xml_by_changing_the_layout(
    sharded_hosted,
):
    root, server = sharded_hosted
    server.context["core_layout"] = "unsharded"
    with pytest.raises(h.EvidenceError, match="unbound"):
        h.verify(root, server.identity, server.context, server.run_id)
