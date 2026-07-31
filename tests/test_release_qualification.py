"""Fail-closed contracts for release qualification and promotion."""

from __future__ import annotations

import argparse
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from release import qualification


SHA = "1" * 40
TREE = "2" * 40
ARCHIVE_SHA = "3" * 64
REPOSITORY = "example/agent-wiki"
RUN_ID = 12345
VERSION = "1.5.0"
WORKFLOW_REF = "refs/heads/knowledge_layer"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _smoke(path: Path, artifact: Path, kind: str) -> dict:
    payload = {
        "schema_version": qualification.SMOKE_SCHEMA,
        "artifact": {
            "filename": artifact.name,
            "sha256": qualification.sha256_file(artifact),
            "kind": kind,
        },
        "version": VERSION,
        "result": {
            "cli_version": f"llm-wiki {VERSION}",
            "doctor_status": "healthy",
            "sync_sha256": "4" * 64,
        },
    }
    _write_json(path, payload)
    return payload


@pytest.fixture
def qualified_bundle(tmp_path: Path) -> tuple[Path, dict]:
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / f"agent_wiki_cli-{VERSION}-py3-none-any.whl"
    sdist = dist / f"agent_wiki_cli-{VERSION}.tar.gz"
    wheel.write_bytes(b"deterministic wheel")
    sdist.write_bytes(b"deterministic sdist")
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    source_archive = frozen / "candidate-source.tar"
    source_archive.write_bytes(b"frozen source archive")
    identity = {
        "schema_version": qualification.IDENTITY_SCHEMA,
        "repository": REPOSITORY,
        "source": {
            "sha": SHA,
            "tree": TREE,
            "archive_sha256": qualification.sha256_file(source_archive),
            "commit_epoch": 1_788_134_400,
        },
        "version": VERSION,
        "tag": f"v{VERSION}",
        "mode": "candidate",
    }
    identity_path = frozen / "identity.json"
    _write_json(identity_path, identity)
    (frozen / "SHA256SUMS").write_text(
        f"{qualification.sha256_file(source_archive)}  candidate-source.tar\n",
        encoding="ascii",
    )
    wheel_smoke_path = tmp_path / "wheel.json"
    sdist_smoke_path = tmp_path / "sdist.json"
    wheel_smoke = _smoke(wheel_smoke_path, wheel, "wheel")
    sdist_smoke = _smoke(sdist_smoke_path, sdist, "sdist")
    comparison = {
        "schema_version": qualification.SMOKE_COMPARISON_SCHEMA,
        "version": VERSION,
        "wheel_sha256": wheel_smoke["artifact"]["sha256"],
        "sdist_sha256": sdist_smoke["artifact"]["sha256"],
        "result_sha256": qualification._smoke_result_sha256(wheel_smoke["result"]),
        "equal": True,
    }
    comparison_path = tmp_path / "comparison.json"
    _write_json(comparison_path, comparison)
    gate_decision = {
        "schema_version": qualification.DECISION_SCHEMA,
        "candidate_sha": SHA,
        "candidate_version": VERSION,
        "gates": {
            **{
                gate: "PASS"
                for gate in qualification.QUALIFIED_GATES
            },
            "RD-13": "BLOCKED",
        },
        "failed": [],
        "blocked": ["RD-13"],
        "decision": "BLOCKED",
    }
    gate_decision_path = tmp_path / "gate-decision.json"
    _write_json(gate_decision_path, gate_decision)
    evidence_specs = []
    for gate in qualification.QUALIFIED_GATES:
        if gate == "RD-00":
            evidence_specs.append(f"{gate}:source={frozen}")
            continue
        evidence = tmp_path / "gate-input" / gate / "result.json"
        evidence.parent.mkdir(parents=True)
        _write_json(evidence, {"gate": gate, "status": "PASS"})
        evidence_specs.append(f"{gate}:result={evidence}")
    bundle = tmp_path / "bundle"
    args = argparse.Namespace(
        identity=identity_path,
        dist=dist,
        wheel_smoke=wheel_smoke_path,
        sdist_smoke=sdist_smoke_path,
        smoke_comparison=comparison_path,
        gate_decision=gate_decision_path,
        evidence=evidence_specs,
        workflow_run_id=RUN_ID,
        output=bundle,
    )
    assert qualification.build_bundle(args) == 0
    manifest = qualification.load_json(bundle / "qualification-manifest.json")
    return bundle, manifest


def _verify_args(bundle: Path, manifest: dict, **overrides) -> argparse.Namespace:
    artifacts = {item["kind"]: item for item in manifest["artifacts"]}
    values = {
        "bundle": bundle,
        "repository": REPOSITORY,
        "workflow_run_id": RUN_ID,
        "candidate_sha": SHA,
        "wheel_sha256": artifacts["wheel"]["sha256"],
        "sdist_sha256": artifacts["sdist"]["sha256"],
        "repository_root": bundle.parent,
        "require_tag": False,
        "check_registry": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def _replace_support_payload(
    bundle: Path,
    manifest: dict,
    filename: str,
    payload: object,
) -> dict:
    path = bundle / filename
    _write_json(path, payload)
    changed = deepcopy(manifest)
    changed["supporting_files"][filename] = qualification.sha256_file(path)
    _write_json(bundle / "qualification-manifest.json", changed)
    return changed


def test_bundle_round_trip_binds_identity_artifacts_and_support(
    qualified_bundle: tuple[Path, dict],
) -> None:
    bundle, manifest = qualified_bundle

    assert qualification.verify_bundle(_verify_args(bundle, manifest)) == 0
    assert {
        gate: record["status"]
        for gate, record in manifest["gates"].items()
    } == {
        **{gate: "PASS" for gate in qualification.QUALIFIED_GATES},
        "RD-13": "BLOCKED",
    }
    assert all(
        manifest["gates"][gate]["evidence"]
        for gate in qualification.QUALIFIED_GATES
    )
    assert manifest["gates"]["RD-13"]["evidence"] == []
    assert {item["kind"] for item in manifest["artifacts"]} == {"wheel", "sdist"}


@pytest.mark.parametrize("mutation", ["missing", "extra", "artifact", "support"])
def test_bundle_rejects_file_set_and_digest_mutations(
    qualified_bundle: tuple[Path, dict],
    mutation: str,
) -> None:
    bundle, manifest = qualified_bundle
    if mutation == "missing":
        (bundle / "sbom.spdx.json").unlink()
    elif mutation == "extra":
        (bundle / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif mutation == "artifact":
        artifact = manifest["artifacts"][0]
        (bundle / "dist" / artifact["filename"]).write_bytes(b"mutated")
    else:
        (bundle / "smoke-wheel.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(qualification.QualificationError):
        qualification.verify_bundle(_verify_args(bundle, manifest))


def test_compare_smoke_recomputes_canonical_result_digest(tmp_path: Path) -> None:
    wheel = tmp_path / f"agent_wiki_cli-{VERSION}-py3-none-any.whl"
    sdist = tmp_path / f"agent_wiki_cli-{VERSION}.tar.gz"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    wheel_path = tmp_path / "wheel.json"
    sdist_path = tmp_path / "sdist.json"
    wheel_smoke = _smoke(wheel_path, wheel, "wheel")
    _smoke(sdist_path, sdist, "sdist")
    output = tmp_path / "comparison.json"

    assert (
        qualification.compare_smoke(
            argparse.Namespace(
                wheel=wheel_path,
                sdist=sdist_path,
                output=output,
            )
        )
        == 0
    )

    comparison = qualification.load_json(output)
    assert comparison["version"] == VERSION
    assert comparison["result_sha256"] == qualification._smoke_result_sha256(
        wheel_smoke["result"]
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "wheel-version",
        "sdist-result",
        "comparison-version",
        "comparison-result-digest",
        "comparison-extra-field",
    ),
)
def test_bundle_rejects_semantically_inconsistent_smoke_evidence(
    qualified_bundle: tuple[Path, dict],
    mutation: str,
) -> None:
    bundle, manifest = qualified_bundle
    if mutation.startswith("wheel"):
        filename = "smoke-wheel.json"
    elif mutation.startswith("sdist"):
        filename = "smoke-sdist.json"
    else:
        filename = "smoke-comparison.json"
    payload = qualification.load_json(bundle / filename)
    if mutation == "wheel-version":
        payload["version"] = "9.9.9"
    elif mutation == "sdist-result":
        payload["result"]["doctor_status"] = "degraded"
    elif mutation == "comparison-version":
        payload["version"] = "9.9.9"
    elif mutation == "comparison-result-digest":
        payload["result_sha256"] = "f" * 64
    else:
        payload["unexpected"] = True
    changed = _replace_support_payload(bundle, manifest, filename, payload)

    with pytest.raises(qualification.QualificationError, match="smoke|behavior"):
        qualification.verify_bundle(_verify_args(bundle, changed))


@pytest.mark.parametrize(
    "mutation",
    (
        "namespace",
        "creation-time",
        "package-name",
        "package-checksum",
        "extra-field",
    ),
)
def test_bundle_rejects_semantically_mutated_sbom(
    qualified_bundle: tuple[Path, dict],
    mutation: str,
) -> None:
    bundle, manifest = qualified_bundle
    filename = "sbom.spdx.json"
    sbom = qualification.load_json(bundle / filename)
    if mutation == "namespace":
        sbom["documentNamespace"] = "urn:uuid:00000000-0000-0000-0000-000000000000"
    elif mutation == "creation-time":
        sbom["creationInfo"]["created"] = "1970-01-01T00:00:00Z"
    elif mutation == "package-name":
        sbom["packages"][0]["name"] = "different.whl"
    elif mutation == "package-checksum":
        sbom["packages"][0]["checksums"][0]["checksumValue"] = "f" * 64
    else:
        sbom["unexpected"] = True
    changed = _replace_support_payload(bundle, manifest, filename, sbom)

    with pytest.raises(qualification.QualificationError, match="SBOM"):
        qualification.verify_bundle(_verify_args(bundle, changed))


@pytest.mark.parametrize(
    "mutation",
    (
        "subject",
        "source-tree",
        "dependency-digest",
        "builder",
        "workflow-run",
        "extra-field",
    ),
)
def test_bundle_rejects_semantically_mutated_provenance(
    qualified_bundle: tuple[Path, dict],
    mutation: str,
) -> None:
    bundle, manifest = qualified_bundle
    filename = "provenance.intoto.json"
    provenance = qualification.load_json(bundle / filename)
    predicate = provenance["predicate"]
    if mutation == "subject":
        provenance["subject"][0]["digest"]["sha256"] = "f" * 64
    elif mutation == "source-tree":
        predicate["buildDefinition"]["externalParameters"]["source_tree"] = "f" * 40
    elif mutation == "dependency-digest":
        dependency = predicate["buildDefinition"]["resolvedDependencies"][0]
        dependency["digest"]["gitTree"] = "f" * 40
    elif mutation == "builder":
        predicate["runDetails"]["builder"]["id"] = "https://example.invalid/builder"
    elif mutation == "workflow-run":
        predicate["runDetails"]["metadata"]["invocationId"] = (
            "https://example.invalid/actions/runs/999"
        )
    else:
        provenance["unexpected"] = True
    changed = _replace_support_payload(bundle, manifest, filename, provenance)

    with pytest.raises(qualification.QualificationError, match="provenance"):
        qualification.verify_bundle(_verify_args(bundle, changed))


def test_bundle_rejects_non_pass_gate(
    qualified_bundle: tuple[Path, dict],
) -> None:
    bundle, manifest = qualified_bundle
    changed = deepcopy(manifest)
    changed["gates"]["RD-09"]["status"] = "FAIL"
    _write_json(bundle / "qualification-manifest.json", changed)

    with pytest.raises(qualification.QualificationError, match="RD-09 must be PASS"):
        qualification.verify_bundle(_verify_args(bundle, manifest))


def test_bundle_rejects_mutated_gate_evidence(
    qualified_bundle: tuple[Path, dict],
) -> None:
    bundle, manifest = qualified_bundle
    entry = manifest["gates"]["RD-09"]["evidence"][0]
    (bundle / entry["path"]).write_text("mutated\n", encoding="utf-8")

    with pytest.raises(qualification.QualificationError, match="evidence digest"):
        qualification.verify_bundle(_verify_args(bundle, manifest))


def test_bundle_rejects_wrong_external_digests_and_identity(
    qualified_bundle: tuple[Path, dict],
) -> None:
    bundle, manifest = qualified_bundle

    with pytest.raises(qualification.QualificationError, match="wheel digest"):
        qualification.verify_bundle(
            _verify_args(bundle, manifest, wheel_sha256="f" * 64)
        )
    with pytest.raises(qualification.QualificationError, match="candidate SHA"):
        qualification.verify_bundle(
            _verify_args(bundle, manifest, candidate_sha="e" * 40)
        )
    with pytest.raises(qualification.QualificationError, match="run ID"):
        qualification.verify_bundle(
            _verify_args(bundle, manifest, workflow_run_id=RUN_ID + 1)
        )


def test_publish_mode_requires_tag_to_resolve_to_candidate(
    qualified_bundle: tuple[Path, dict],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, manifest = qualified_bundle

    monkeypatch.setattr(
        qualification,
        "_run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, TREE, ""),
    )
    with pytest.raises(qualification.QualificationError, match="does not resolve"):
        qualification.verify_bundle(
            _verify_args(bundle, manifest, require_tag=True)
        )


def test_registry_preflight_is_required_when_requested(
    qualified_bundle: tuple[Path, dict],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, manifest = qualified_bundle

    def unavailable(_version: str) -> None:
        raise qualification.QualificationError("registry unavailable")

    monkeypatch.setattr(qualification, "_check_registry_unused", unavailable)
    with pytest.raises(qualification.QualificationError, match="registry"):
        qualification.verify_bundle(
            _verify_args(bundle, manifest, check_registry=True)
        )


def test_workflow_run_identity_is_bound_to_repo_workflow_and_sha() -> None:
    workflow_ref = "refs/heads/knowledge_layer"
    payload = {
        "repository": {"full_name": REPOSITORY},
        "head_repository": {"full_name": REPOSITORY},
        "path": ".github/workflows/release-qualification.yml@knowledge_layer",
        "head_branch": "knowledge_layer",
        "event": "workflow_dispatch",
        "name": "Release qualification",
        "status": "completed",
        "conclusion": "success",
        "head_sha": SHA,
    }

    def validate(candidate: object, **overrides: str) -> None:
        arguments = {
            "repository": REPOSITORY,
            "workflow_path": ".github/workflows/release-qualification.yml",
            "workflow_name": "Release qualification",
            "workflow_ref": workflow_ref,
            "workflow_revision": SHA,
            "event": "workflow_dispatch",
            "candidate_sha": SHA,
            **overrides,
        }
        qualification.validate_workflow_run(candidate, **arguments)

    validate(payload)

    for field, value in (
        ("name", "Different workflow"),
        ("status", "in_progress"),
        ("conclusion", "failure"),
        ("head_sha", TREE),
        ("head_branch", "main"),
        ("event", "push"),
        ("path", ".github/workflows/release-qualification.yml@main"),
    ):
        changed = deepcopy(payload)
        changed[field] = value
        with pytest.raises(qualification.QualificationError, match="identity mismatch"):
            validate(changed)

    for repository_field in ("repository", "head_repository"):
        changed = deepcopy(payload)
        changed[repository_field]["full_name"] = "attacker/fork"
        with pytest.raises(qualification.QualificationError, match="repository"):
            validate(changed)

    with pytest.raises(qualification.QualificationError, match="revision"):
        validate(payload, workflow_revision=TREE)

    for unsafe_ref in (
        "knowledge_layer",
        "refs/tags/v1.5.0",
        "refs/heads/../knowledge_layer",
        "refs/heads/release@{1}",
        "refs/heads/release candidate",
        "refs/heads/release;echo-pwned",
        "refs/heads/release$(echo-pwned)",
    ):
        with pytest.raises(qualification.QualificationError, match="safe branch ref"):
            validate(payload, workflow_ref=unsafe_ref)

    with pytest.raises(qualification.QualificationError, match="candidate SHA"):
        validate(payload, candidate_sha=f"{SHA};echo-pwned")


def test_verify_workflow_run_parser_requires_ref_and_revision() -> None:
    parser = qualification._parser()
    arguments = parser.parse_args(
        [
            "verify-workflow-run",
            "--repository",
            REPOSITORY,
            "--workflow-run-id",
            "1234",
            "--candidate-sha",
            SHA,
            "--workflow-ref",
            "refs/heads/knowledge_layer",
            "--workflow-revision",
            SHA,
        ]
    )
    assert arguments.workflow_ref == "refs/heads/knowledge_layer"
    assert arguments.workflow_revision == SHA
    assert arguments.event == "workflow_dispatch"

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "verify-workflow-run",
                "--repository",
                REPOSITORY,
                "--workflow-run-id",
                "1234;echo-pwned",
                "--candidate-sha",
                SHA,
                "--workflow-ref",
                "refs/heads/knowledge_layer",
                "--workflow-revision",
                SHA,
            ]
        )


def test_aggregate_precedence_is_fail_then_blocked_then_go(tmp_path: Path) -> None:
    def decision(
        statuses: dict[str, str],
        *,
        allow_non_go_exit_zero: bool = False,
    ) -> tuple[int, str]:
        output = tmp_path / f"{len(list(tmp_path.iterdir()))}.json"
        args = argparse.Namespace(
            candidate_sha=SHA,
            candidate_version=VERSION,
            gate=[f"{gate}={status}" for gate, status in statuses.items()],
            output=output,
            allow_non_go_exit_zero=allow_non_go_exit_zero,
        )
        code = qualification.aggregate(args)
        return code, qualification.load_json(output)["decision"]

    all_pass = {gate: "PASS" for gate in qualification.REQUIRED_GATES}
    assert decision(all_pass) == (0, "GO")
    blocked = {**all_pass, "RD-13": "BLOCKED"}
    assert decision(blocked) == (1, "BLOCKED")
    assert decision(blocked, allow_non_go_exit_zero=True) == (0, "BLOCKED")
    failed = {**blocked, "RD-09": "FAIL"}
    assert decision(failed) == (1, "NO-GO")


def test_final_promotion_aggregate_requires_all_gates_pass(tmp_path: Path) -> None:
    statuses = {gate: "PASS" for gate in qualification.REQUIRED_GATES}

    for rd13_status, expected in (("BLOCKED", 1), ("FAIL", 1), ("PASS", 0)):
        output = tmp_path / f"promotion-{rd13_status}.json"
        args = argparse.Namespace(
            candidate_sha=SHA,
            candidate_version=VERSION,
            gate=[
                f"{gate}={rd13_status if gate == 'RD-13' else status}"
                for gate, status in statuses.items()
            ],
            output=output,
            allow_non_go_exit_zero=False,
        )
        assert qualification.aggregate(args) == expected


def _attestation_receipt(manifest: dict, predicate_type: str) -> list[dict]:
    workflow_uri = (
        f"https://github.com/{REPOSITORY}/"
        f"{qualification.QUALIFICATION_WORKFLOW_PATH}@{WORKFLOW_REF}"
    )
    subjects = [
        {
            "name": artifact["filename"],
            "digest": {"sha256": artifact["sha256"]},
        }
        for artifact in manifest["artifacts"]
    ]
    return [
        {
            "attestation": {
                "bundle": {
                    "mediaType": (
                        "application/vnd.dev.sigstore.bundle.v0.3+json"
                    )
                }
            },
            "verificationResult": {
                "mediaType": (
                    "application/vnd.dev.sigstore."
                    "verificationresult+json;version=0.1"
                ),
                "statement": {
                    "_type": "https://in-toto.io/Statement/v1",
                    "subject": subjects,
                    "predicateType": predicate_type,
                    "predicate": {},
                },
                "signature": {
                    "certificate": {
                        "certificateIssuer": "CN=sigstore-intermediate",
                        "subjectAlternativeName": workflow_uri,
                        "issuer": qualification.GITHUB_ACTIONS_OIDC_ISSUER,
                        "buildSignerURI": workflow_uri,
                        "buildSignerDigest": SHA,
                        "runnerEnvironment": "github-hosted",
                        "sourceRepositoryURI": (
                            f"https://github.com/{REPOSITORY}"
                        ),
                        "sourceRepositoryDigest": SHA,
                        "sourceRepositoryRef": WORKFLOW_REF,
                        "buildConfigURI": workflow_uri,
                        "buildConfigDigest": SHA,
                        "buildTrigger": "workflow_dispatch",
                        "runInvocationURI": (
                            f"https://github.com/{REPOSITORY}/actions/runs/"
                            f"{RUN_ID}/attempts/1"
                        ),
                    }
                },
                "verifiedTimestamps": [
                    {
                        "type": "Tlog",
                        "uri": "https://rekor.sigstore.dev",
                        "timestamp": "2026-07-31T00:00:00Z",
                    }
                ],
            },
        }
    ]


def _write_attestation_receipts(
    path: Path,
    manifest: dict,
    predicate_type: str,
) -> None:
    receipt = _attestation_receipt(manifest, predicate_type)
    path.write_text(
        "".join(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
            for _ in range(qualification.ATTESTATION_RECEIPT_COUNT)
        ),
        encoding="utf-8",
    )


def _load_attestation_receipt_lines(path: Path) -> list[list[dict]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def _rewrite_attestation_receipt_lines(
    path: Path,
    receipts: list[list[dict]],
) -> None:
    path.write_text(
        "".join(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
            for receipt in receipts
        ),
        encoding="utf-8",
    )


def _promotion_args(
    tmp_path: Path,
    bundle: Path,
    manifest: dict,
) -> argparse.Namespace:
    verification = tmp_path / "bundle-verification.json"
    assert (
        qualification.verify_bundle(
            _verify_args(bundle, manifest, output=verification)
        )
        == 0
    )
    bundle_receipt = qualification.load_json(verification)
    bundle_receipt["checks"]["registry_vacant"] = True
    _write_json(verification, bundle_receipt)
    workflow = tmp_path / "workflow-run-verification.json"
    _write_json(
        workflow,
        {
            "schema_version": qualification.WORKFLOW_VERIFICATION_SCHEMA,
            "repository": REPOSITORY,
            "workflow_run_id": RUN_ID,
            "candidate_sha": SHA,
            "workflow_path": qualification.QUALIFICATION_WORKFLOW_PATH,
            "workflow_ref": WORKFLOW_REF,
            "workflow_revision": SHA,
            "event": "workflow_dispatch",
        },
    )
    provenance = tmp_path / "build-provenance-attestations.jsonl"
    sbom = tmp_path / "sbom-attestations.jsonl"
    _write_attestation_receipts(
        provenance,
        manifest,
        qualification.SLSA_PROVENANCE_PREDICATE,
    )
    _write_attestation_receipts(
        sbom,
        manifest,
        qualification.SPDX_SBOM_PREDICATE,
    )
    return argparse.Namespace(
        manifest=bundle / "qualification-manifest.json",
        verification=verification,
        repository=REPOSITORY,
        workflow_run_id=RUN_ID,
        candidate_sha=SHA,
        rd13_evidence=[
            f"workflow-run={workflow}",
            f"build-provenance={provenance}",
            f"sbom-attestation={sbom}",
        ],
        require_tag=False,
        output=tmp_path / "promotion-decision.json",
    )


def test_promotion_decision_is_derived_from_verified_manifest(
    qualified_bundle: tuple[Path, dict],
    tmp_path: Path,
) -> None:
    bundle, manifest = qualified_bundle
    args = _promotion_args(tmp_path, bundle, manifest)

    assert qualification.finalize_promotion(args) == 0
    decision = qualification.load_json(args.output)
    assert decision["schema_version"] == qualification.PROMOTION_SCHEMA
    assert decision["decision"] == "GO"
    assert decision["gates"] == {
        gate: "PASS" for gate in qualification.REQUIRED_GATES
    }
    assert set(decision["rd13_evidence"]) == {
        "workflow-run",
        "build-provenance",
        "sbom-attestation",
    }


@pytest.mark.parametrize(
    "mutation",
    (
        "registry",
        "workflow-sha",
        "missing-attestation",
        "malformed-attestation",
        "missing-receipt",
        "extra-receipt",
        "empty-receipt",
        "mismatched-extra-result",
        "artifact-name",
        "artifact-digest",
        "missing-subject",
        "extra-subject",
        "predicate",
        "attestation-repository",
        "attestation-source-sha",
        "attestation-workflow",
        "attestation-run",
        "missing-timestamp",
        "tag",
    ),
)
def test_promotion_rejects_incomplete_or_mismatched_rd13_evidence(
    qualified_bundle: tuple[Path, dict],
    tmp_path: Path,
    mutation: str,
) -> None:
    bundle, manifest = qualified_bundle
    args = _promotion_args(tmp_path, bundle, manifest)
    if mutation == "registry":
        receipt = qualification.load_json(args.verification)
        receipt["checks"]["registry_vacant"] = False
        _write_json(args.verification, receipt)
    elif mutation == "workflow-sha":
        workflow_spec = next(
            spec for spec in args.rd13_evidence if spec.startswith("workflow-run=")
        )
        workflow_path = Path(workflow_spec.partition("=")[2])
        receipt = qualification.load_json(workflow_path)
        receipt["workflow_revision"] = TREE
        _write_json(workflow_path, receipt)
    elif mutation == "missing-attestation":
        attestation_spec = next(
            spec
            for spec in args.rd13_evidence
            if spec.startswith("sbom-attestation=")
        )
        Path(attestation_spec.partition("=")[2]).write_text("", encoding="utf-8")
    elif mutation == "tag":
        args.require_tag = True
    else:
        provenance_spec = next(
            spec
            for spec in args.rd13_evidence
            if spec.startswith("build-provenance=")
        )
        provenance_path = Path(provenance_spec.partition("=")[2])
        if mutation == "malformed-attestation":
            provenance_path.write_text("[not-json]\n[]\n", encoding="utf-8")
        else:
            receipts = _load_attestation_receipt_lines(provenance_path)
            if mutation == "missing-receipt":
                receipts = receipts[:1]
            elif mutation == "extra-receipt":
                receipts.append(deepcopy(receipts[0]))
            elif mutation == "empty-receipt":
                receipts[0] = []
            elif mutation == "mismatched-extra-result":
                mismatched = deepcopy(receipts[0][0])
                mismatched["verificationResult"]["statement"]["subject"][0][
                    "digest"
                ]["sha256"] = "f" * 64
                receipts[0].append(mismatched)
            elif mutation == "artifact-name":
                receipts[0][0]["verificationResult"]["statement"]["subject"][0][
                    "name"
                ] = "different.whl"
            elif mutation == "artifact-digest":
                receipts[0][0]["verificationResult"]["statement"]["subject"][0][
                    "digest"
                ]["sha256"] = "f" * 64
            elif mutation == "missing-subject":
                for receipt in receipts:
                    subjects = receipt[0]["verificationResult"]["statement"][
                        "subject"
                    ]
                    receipt[0]["verificationResult"]["statement"]["subject"] = (
                        subjects[:1]
                    )
            elif mutation == "extra-subject":
                receipts[0][0]["verificationResult"]["statement"][
                    "subject"
                ].append(
                    {
                        "name": "extra.tar.gz",
                        "digest": {"sha256": "f" * 64},
                    }
                )
            elif mutation == "predicate":
                receipts[0][0]["verificationResult"]["statement"][
                    "predicateType"
                ] = qualification.SPDX_SBOM_PREDICATE
            elif mutation == "attestation-repository":
                receipts[0][0]["verificationResult"]["signature"]["certificate"][
                    "sourceRepositoryURI"
                ] = "https://github.com/example/different"
            elif mutation == "attestation-source-sha":
                receipts[0][0]["verificationResult"]["signature"]["certificate"][
                    "sourceRepositoryDigest"
                ] = TREE
            elif mutation == "attestation-workflow":
                receipts[0][0]["verificationResult"]["signature"]["certificate"][
                    "buildSignerURI"
                ] = (
                    f"https://github.com/{REPOSITORY}/.github/workflows/"
                    f"different.yml@{WORKFLOW_REF}"
                )
            elif mutation == "attestation-run":
                receipts[0][0]["verificationResult"]["signature"]["certificate"][
                    "runInvocationURI"
                ] = f"https://github.com/{REPOSITORY}/actions/runs/999"
            else:
                receipts[0][0]["verificationResult"]["verifiedTimestamps"] = []
            _rewrite_attestation_receipt_lines(provenance_path, receipts)

    with pytest.raises(qualification.QualificationError):
        qualification.finalize_promotion(args)


def test_promotion_accepts_multiple_matching_attestations_per_receipt(
    qualified_bundle: tuple[Path, dict],
    tmp_path: Path,
) -> None:
    bundle, manifest = qualified_bundle
    args = _promotion_args(tmp_path, bundle, manifest)
    for label in ("build-provenance", "sbom-attestation"):
        spec = next(
            item for item in args.rd13_evidence if item.startswith(f"{label}=")
        )
        path = Path(spec.partition("=")[2])
        receipts = _load_attestation_receipt_lines(path)
        for receipt in receipts:
            receipt.append(deepcopy(receipt[0]))
        _rewrite_attestation_receipt_lines(path, receipts)

    assert qualification.finalize_promotion(args) == 0


def test_exact_skip_allowlist_rejects_reason_drift(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """
        <testsuite tests="1" skipped="1">
          <testcase classname="tests.test_example.TestCase" name="test_guard">
            <skipped message="Windows only" />
          </testcase>
        </testsuite>
        """,
        encoding="utf-8",
    )
    allowlist = tmp_path / "allowlist.json"
    _write_json(
        allowlist,
        {
            "schema_version": qualification.ALLOWLIST_SCHEMA,
            "entries": [
                {
                    "lane": "core-linux",
                    "node_id": "tests/test_example.py::TestCase::test_guard",
                    "reason": "different reason",
                    "owner_lane": "core-windows",
                }
            ],
        },
    )
    args = argparse.Namespace(
        junit=junit,
        lane="core-linux",
        allowlist=allowlist,
        output=tmp_path / "result.json",
        minimum_collected=1,
        minimum_passed=0,
        discovery=False,
    )

    with pytest.raises(qualification.QualificationError, match="skip contract"):
        qualification.verify_junit(args)


def test_skip_allowlist_rejects_unreviewed_owner_lane(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """
        <testsuite tests="1" skipped="1">
          <testcase classname="tests.test_example.TestCase" name="test_guard">
            <skipped message="Windows only" />
          </testcase>
        </testsuite>
        """,
        encoding="utf-8",
    )
    allowlist = tmp_path / "allowlist.json"
    _write_json(
        allowlist,
        {
            "schema_version": qualification.ALLOWLIST_SCHEMA,
            "entries": [
                {
                    "lane": "core-linux",
                    "node_id": "tests/test_example.py::TestCase::test_guard",
                    "reason": "Windows only",
                    "owner_lane": "REVIEW-REQUIRED",
                }
            ],
        },
    )
    args = argparse.Namespace(
        junit=junit,
        lane="core-linux",
        allowlist=allowlist,
        output=tmp_path / "result.json",
        minimum_collected=1,
        minimum_passed=0,
        discovery=False,
    )

    with pytest.raises(qualification.QualificationError, match="unreviewed"):
        qualification.verify_junit(args)


def test_discovery_generates_review_required_owner_lanes(tmp_path: Path) -> None:
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """
        <testsuite tests="1" skipped="1">
          <testcase classname="tests.test_example.TestCase" name="test_guard">
            <skipped message="Windows only" />
          </testcase>
        </testsuite>
        """,
        encoding="utf-8",
    )
    output = tmp_path / "allowlist.json"

    assert (
        qualification.discover_allowlist(
            argparse.Namespace(
                result=[f"core-linux={junit}"],
                output=output,
            )
        )
        == 0
    )

    assert qualification.load_json(output)["entries"] == [
        {
            "lane": "core-linux",
            "node_id": "tests/test_example.py::TestCase::test_guard",
            "owner_lane": "REVIEW-REQUIRED",
            "reason": "Windows only",
        }
    ]


def test_owner_lane_verifier_requires_every_owner_to_pass(tmp_path: Path) -> None:
    identity = tmp_path / "identity.json"
    _write_json(
        identity,
        {
            "schema_version": qualification.IDENTITY_SCHEMA,
            "repository": REPOSITORY,
            "source": {
                "sha": SHA,
                "tree": TREE,
                "archive_sha256": ARCHIVE_SHA,
                "commit_epoch": 1_788_134_400,
            },
            "version": VERSION,
            "tag": f"v{VERSION}",
            "mode": "candidate",
        },
    )
    allowlist = tmp_path / "allowlist.json"
    _write_json(
        allowlist,
        {
            "schema_version": qualification.ALLOWLIST_SCHEMA,
            "entries": [
                {
                    "lane": "core-linux",
                    "node_id": "tests/test_example.py::TestCase::test_guard",
                    "reason": "Windows only",
                    "owner_lane": "core-windows",
                }
            ],
        },
    )
    owner_junit = tmp_path / "owner.xml"
    owner_junit.write_text(
        """
        <testsuite tests="1">
          <testcase classname="tests.test_example.TestCase" name="test_guard" />
        </testsuite>
        """,
        encoding="utf-8",
    )
    output = tmp_path / "owner-lanes.json"
    passing = argparse.Namespace(
        identity=identity,
        allowlist=allowlist,
        owner_result=["core-windows=success"],
        owner_junit=[f"core-windows={owner_junit}"],
        output=output,
    )

    assert qualification.verify_owner_lanes(passing) == 0
    assert qualification.load_json(output) == {
        "schema_version": qualification.OWNER_LANE_SCHEMA,
        "identity": {
            "repository": REPOSITORY,
            "sha": SHA,
            "tree": TREE,
            "archive_sha256": ARCHIVE_SHA,
            "version": VERSION,
            "tag": f"v{VERSION}",
        },
        "identity_sha256": qualification.sha256_file(identity),
        "allowlist_sha256": qualification.sha256_file(allowlist),
        "entries_verified": 1,
        "required_owner_lanes": ["core-windows"],
        "owner_results": {
            "core-windows": {
                "junit_sha256": qualification.sha256_file(owner_junit),
                "result": "PASS",
                "verified_node_ids": [
                    "tests/test_example.py::TestCase::test_guard"
                ],
            }
        },
    }

    failing = argparse.Namespace(
        identity=identity,
        allowlist=allowlist,
        owner_result=["core-windows=failure"],
        owner_junit=[f"core-windows={owner_junit}"],
        output=output,
    )
    with pytest.raises(qualification.QualificationError, match="did not pass"):
        qualification.verify_owner_lanes(failing)

    missing = argparse.Namespace(
        identity=identity,
        allowlist=allowlist,
        owner_result=["core-macos=success"],
        owner_junit=[f"core-windows={owner_junit}"],
        output=output,
    )
    with pytest.raises(qualification.QualificationError, match="no result"):
        qualification.verify_owner_lanes(missing)

    missing_junit = argparse.Namespace(
        identity=identity,
        allowlist=allowlist,
        owner_result=["core-windows=success"],
        owner_junit=[f"core-macos={owner_junit}"],
        output=output,
    )
    with pytest.raises(
        qualification.QualificationError,
        match="no JUnit evidence",
    ):
        qualification.verify_owner_lanes(missing_junit)


@pytest.mark.parametrize("outcome", ["skipped", "failure", "error"])
def test_owner_lane_verifier_rejects_nonpassing_owned_node(
    tmp_path: Path,
    outcome: str,
) -> None:
    identity = tmp_path / "identity.json"
    _write_json(
        identity,
        {
            "schema_version": qualification.IDENTITY_SCHEMA,
            "repository": REPOSITORY,
            "source": {
                "sha": SHA,
                "tree": TREE,
                "archive_sha256": ARCHIVE_SHA,
                "commit_epoch": 1_788_134_400,
            },
            "version": VERSION,
            "tag": f"v{VERSION}",
            "mode": "candidate",
        },
    )
    allowlist = tmp_path / "allowlist.json"
    _write_json(
        allowlist,
        {
            "schema_version": qualification.ALLOWLIST_SCHEMA,
            "entries": [
                {
                    "lane": "core-linux",
                    "node_id": "tests/test_example.py::TestCase::test_guard",
                    "reason": "Windows only",
                    "owner_lane": "core-windows",
                }
            ],
        },
    )
    junit = tmp_path / "owner.xml"
    junit.write_text(
        f"""
        <testsuite tests="1">
          <testcase classname="tests.test_example.TestCase" name="test_guard">
            <{outcome} message="not a pass" />
          </testcase>
        </testsuite>
        """,
        encoding="utf-8",
    )

    with pytest.raises(qualification.QualificationError, match="did not pass"):
        qualification.verify_owner_lanes(
            argparse.Namespace(
                identity=identity,
                allowlist=allowlist,
                owner_result=["core-windows=success"],
                owner_junit=[f"core-windows={junit}"],
                output=tmp_path / "receipt.json",
            )
        )


def test_owner_lane_verifier_rejects_missing_or_duplicate_owned_node(
    tmp_path: Path,
) -> None:
    identity = tmp_path / "identity.json"
    _write_json(
        identity,
        {
            "schema_version": qualification.IDENTITY_SCHEMA,
            "repository": REPOSITORY,
            "source": {
                "sha": SHA,
                "tree": TREE,
                "archive_sha256": ARCHIVE_SHA,
                "commit_epoch": 1_788_134_400,
            },
            "version": VERSION,
            "tag": f"v{VERSION}",
            "mode": "candidate",
        },
    )
    allowlist = tmp_path / "allowlist.json"
    _write_json(
        allowlist,
        {
            "schema_version": qualification.ALLOWLIST_SCHEMA,
            "entries": [
                {
                    "lane": "core-linux",
                    "node_id": "tests/test_example.py::TestCase::test_guard",
                    "reason": "Windows only",
                    "owner_lane": "core-windows",
                }
            ],
        },
    )
    junit = tmp_path / "owner.xml"
    junit.write_text(
        """
        <testsuite tests="1">
          <testcase classname="tests.test_example.TestCase" name="other" />
        </testsuite>
        """,
        encoding="utf-8",
    )
    args = argparse.Namespace(
        identity=identity,
        allowlist=allowlist,
        owner_result=["core-windows=success"],
        owner_junit=[f"core-windows={junit}"],
        output=tmp_path / "receipt.json",
    )

    with pytest.raises(qualification.QualificationError, match="missing owned nodes"):
        qualification.verify_owner_lanes(args)

    junit.write_text(
        """
        <testsuite tests="2">
          <testcase classname="tests.test_example.TestCase" name="test_guard" />
          <testcase classname="tests.test_example.TestCase" name="test_guard" />
        </testsuite>
        """,
        encoding="utf-8",
    )
    with pytest.raises(qualification.QualificationError, match="duplicate node ID"):
        qualification.verify_owner_lanes(args)
