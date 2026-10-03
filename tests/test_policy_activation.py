"""Hosted activation requires original nonpromoting proof and trusted policy bytes."""

from copy import deepcopy
import base64
import io
import json
from pathlib import Path
import tarfile
import urllib.parse

import pytest

from release import hosted_evidence as hosted, knowledge_maintenance as maintenance, policy_activation as activation
from llm_wiki_cli.services import health_policy as hp
from tests.hosted_evidence_fixtures import HostedEvidence, source_archive
from tests.test_knowledge_maintenance import evidence, raw
from tests.test_knowledge_maintenance import preflight_project as preflight_project
from tests.test_knowledge_health_refresh import recorded_project as recorded_project
from tests.test_health_details import _doctor

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "example/agent-wiki"
SHA = "a" * 40
RUN = 123
REQUEST = "f" * 64


class ShadowEvidence:
    def __init__(self, root):
        config = json.loads((ROOT / maintenance.POLICY_PATH).read_bytes())
        config.update(schema_version=maintenance.CONFIG_SCHEMA, policy=hp.POLICY_ID)
        config["activation"]["implementation_sha256"] = "0" * 64
        self.config = config
        inputs = {name: (ROOT / name).read_bytes() for name in maintenance.POLICY_INPUTS}
        self.source_files = {**inputs, maintenance.POLICY_PATH: raw(config)}
        self.policy_root = root / "trusted"
        for name, content in self.source_files.items():
            target = self.policy_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        archive = source_archive(self.source_files)
        self.identity = {
            "schema_version": "agent-wiki-release-identity/v1", "repository": REPOSITORY,
            "source": {"sha": SHA, "tree": "b" * 40, "archive_sha256": hosted.sha256(archive), "commit_epoch": 1727000000},
            "version": "2.2.0", "tag": "v2.2.0", "mode": "policy-shadow",
        }
        report, ci, before, binding = evidence(root / "wiki")
        binding["source_archive_sha256"] = "sha256:" + self.identity["source"]["archive_sha256"]
        self.maintenance = {
            "ci-report.json": raw(ci), "preflight.json": raw(before),
            "policy.json": raw(hp.derive_policy(raw(ci), raw(before), binding=binding)),
            "doctor.json": raw(_doctor(report)),
        }
        directory = root / "evidence"
        directory.mkdir()
        for name, content in self.maintenance.items():
            (directory / name).write_bytes(content)
        result = maintenance.admit(directory, self.identity, maintenance.policy(raw(config), policy_shadow=True))
        assert result["status"] == "pass", result
        result["activation_proof"] = {
            "schema_version": "agent-wiki-release-policy-shadow/v1", "qualification": "nonpromoting",
            "policy": hp.POLICY_ID, "implementation_sha256": hosted.sha256(inputs[maintenance.LEAF_PATH]),
        }
        self.receipt = result
        self.decision = {
            "schema_version": activation.DECISION_SCHEMA, "candidate_sha": SHA,
            "candidate_tree": self.identity["source"]["tree"], "candidate_version": self.identity["version"],
            "status": "pass", "nonpromoting": True,
            "gates": {"source": "PASS", "integrity": "PASS", "maintenance": "PASS"},
        }
        self.run = {
            "id": RUN, "run_attempt": 1, "head_sha": SHA,
            "head_branch": "codex/qualification/" + SHA,
            "display_title": "Release qualification [" + REQUEST + "]",
            "event": "workflow_dispatch", "path": hosted.WORKFLOW,
            "status": "completed", "conclusion": "success",
            "repository": {"id": 10, "full_name": REPOSITORY},
            "head_repository": {"id": 10, "full_name": REPOSITORY},
        }
        self.jobs = [{
            "id": number, "run_id": RUN, "run_attempt": 1, "head_sha": SHA,
            "name": name, "status": "completed", "conclusion": "success",
            "started_at": "2026-09-22T10:00:00Z", "completed_at": "2026-09-22T10:10:00Z",
        } for number, name in enumerate(sorted({item[0] for item in activation.CONTRACT.values()}), 1)]
        self.jobs.append({**self.jobs[0], "id": 20, "name": "Assemble immutable qualified release", "conclusion": "skipped"})
        self.files = {
            "candidate-source": {"identity.json": raw(self.identity), "candidate-source.tar": archive,
                                 "SHA256SUMS": (self.identity["source"]["archive_sha256"] + "  candidate-source.tar\n").encode()},
            "qualification-harnesses": {"qualification-harnesses.tar": source_archive(self.source_files)},
            "evidence-rd-10": {"maintenance/" + name: content for name, content in self.maintenance.items()},
            "knowledge-maintenance-verification": {"verification.json": raw(result)},
            "qualification-decision": {"decision.json": raw(self.decision)},
        }
        self.artifacts = [{
            "id": number, "name": name, "expired": False,
            "created_at": "2026-09-22T10:05:00Z", "updated_at": "2026-09-22T10:05:00Z",
            "workflow_run": {"id": RUN, "head_sha": SHA, "repository_id": 10, "head_repository_id": 10},
        } for number, name in enumerate(self.files, 100)]
        self.archives = {}
        for name in self.files:
            self.replace(name)

    def replace(self, name, files=None):
        if files is not None:
            self.files[name] = files
        artifact = next(item for item in self.artifacts if item["name"] == name)
        content = HostedEvidence.zip(self.files[name])
        self.archives[artifact["id"]] = content
        artifact["digest"] = "sha256:" + hosted.sha256(content)

    def replace_source(self, files):
        archive = source_archive(files)
        self.identity["source"]["archive_sha256"] = hosted.sha256(archive)
        self.files["candidate-source"].update({
            "identity.json": raw(self.identity), "candidate-source.tar": archive,
            "SHA256SUMS": (hosted.sha256(archive) + "  candidate-source.tar\n").encode(),
        })
        self.replace("candidate-source")

    def get(self, path):
        assert path == f"/actions/runs/{RUN}"
        return deepcopy(self.run)

    def list(self, path, key):
        assert path in {f"/actions/runs/{RUN}/artifacts", f"/actions/runs/{RUN}/attempts/1/jobs"}
        return deepcopy(self.jobs if key == "jobs" else self.artifacts)

    def archive(self, artifact_id):
        return self.archives[artifact_id]

    def verify(self, **kwargs):
        return activation.verify_shadow(REPOSITORY, RUN, 1, SHA, self.policy_root, client=self, **kwargs)


@pytest.fixture
def shadow(tmp_path):
    return ShadowEvidence(tmp_path)


def test_original_hosted_proof_generates_only_activation_and_bounded_audit(shadow):
    verified = shadow.verify(request_id=REQUEST)
    assert verified["audit"]["configuration"] == activation.configuration_contract(shadow.config)
    assert verified["activation"] == {
        "proof_source_sha": SHA, "run_id": RUN, "attempt": 1,
        "comparison_sha256": hosted.sha256(shadow.files["knowledge-maintenance-verification"]["verification.json"]),
        "implementation_sha256": hosted.sha256((ROOT / maintenance.LEAF_PATH).read_bytes()),
    }
    assert set(verified["audit"]["artifacts"]) == set(activation.CONTRACT)
    assert verified["audit"]["receipt"] == shadow.receipt
    assert verified["audit"]["request_id"] == REQUEST
    assert len(raw(verified["audit"])) <= activation.MAX_AUDIT
    original = deepcopy(shadow.config)
    updated = activation.proposal(shadow.config, verified)
    assert shadow.config == original
    assert updated["activation"] == verified["activation"]
    assert {key: value for key, value in updated.items() if key != "activation"} == {key: value for key, value in original.items() if key != "activation"}
    assert maintenance.policy(raw(updated))["mode"] == "required"


@pytest.mark.parametrize("field", ["schema_version", "mode", "policy", "src_dir", "wiki_dir", "selection", "thresholds"])
def test_proposal_rejects_every_unevaluated_configuration_field(shadow, field):
    verified = shadow.verify()
    current = deepcopy(shadow.config)
    current[field] = {"strict": 0.95} if field == "thresholds" else "changed"
    with pytest.raises(hosted.EvidenceError, match="configuration contract|required policy"):
        activation.proposal(current, verified)


def test_activation_only_changes_do_not_invalidate_the_evaluated_contract(shadow):
    verified = shadow.verify()
    current = deepcopy(shadow.config)
    current["activation"]["implementation_sha256"] = "1" * 64
    assert activation.proposal(current, verified)["activation"] == verified["activation"]


def test_main_policy_proof_requires_explicit_manual_verification(shadow):
    shadow.run["head_branch"] = "main"
    with pytest.raises(hosted.EvidenceError, match="run identity"):
        shadow.verify()
    verified = shadow.verify(main_proof=True)
    assert verified["activation"]["proof_source_sha"] == SHA
    assert verified["audit"]["request_id"] is None
    with pytest.raises(hosted.EvidenceError, match="coordinator identity"):
        shadow.verify(main_proof=True, request_id=REQUEST)


@pytest.mark.parametrize("field", ["candidate_sha", "proof_source_sha"])
def test_policy_reads_legacy_and_explicit_proof_source_names(shadow, field):
    config = deepcopy(shadow.config)
    source = maintenance.activation_source_sha(config["activation"])
    config["activation"].pop("candidate_sha", None)
    config["activation"].pop("proof_source_sha", None)
    config["activation"][field] = source
    config["activation"]["implementation_sha256"] = hosted.sha256((ROOT / maintenance.LEAF_PATH).read_bytes())
    assert maintenance.policy(raw(config))["mode"] == "required"
    assert maintenance.activation_source_sha(config["activation"]) == source
    config["activation"]["proof_source_sha" if field == "candidate_sha" else "candidate_sha"] = "b" * 40
    with pytest.raises(ValueError, match="exactly one"):
        maintenance.policy(raw(config))


def test_shadow_replay_rejects_configuration_only_changes_to_trusted_checkout(shadow):
    current = deepcopy(shadow.config)
    current["thresholds"] = {"strict": 0.95}
    (shadow.policy_root / maintenance.POLICY_PATH).write_bytes(raw(current))
    with pytest.raises(hosted.EvidenceError, match="configuration differs"):
        shadow.verify()


@pytest.mark.parametrize("recorded_project", ["current"], indirect=True)
def test_composite_v2_proof_replays_real_analysis_comparison(preflight_project, tmp_path):
    from llm_wiki_cli.services import knowledge_maintenance as runtime, lint_service
    from llm_wiki_cli.services.health_details import CapturedHealthDetails
    from tests.test_health_details import _ci

    shadow = ShadowEvidence(tmp_path / "hosted")
    shadow.config.update(schema_version=maintenance.CONFIG_V2_SCHEMA, policy=hp.POLICY_V2_ID)
    (shadow.policy_root / maintenance.POLICY_PATH).write_bytes(raw(shadow.config))
    shadow.source_files[maintenance.POLICY_PATH] = raw(shadow.config)
    shadow.replace_source(shadow.source_files)
    shadow.identity.update(version="9.8.6", tag="v9.8.6")
    shadow.files["candidate-source"]["identity.json"] = raw(shadow.identity)
    shadow.replace("candidate-source")
    shadow.replace("qualification-harnesses", {"qualification-harnesses.tar": source_archive(shadow.source_files)})
    before = runtime.preflight(**preflight_project, comparison_policy="analysis-v1")
    assert before["status"] == "ready", before
    report = lint_service.build_report("wiki", "source", strict=True, knowledge_drift_report=True,
                                      include_plugins=False, include_health_details=True, comparison_policy="analysis-v1")
    assert report.health_details is not None
    detail = report.health_details.to_payload()
    detail["scope"].update(src_dir="candidate", wiki_dir="candidate/docs/llm_wiki")
    report.src_dir, report.wiki_dir = "candidate", "candidate/docs/llm_wiki"
    report.health_details = CapturedHealthDetails(json.dumps(detail))
    binding = before["binding"]
    binding.update(candidate_sha=SHA, candidate_tree="b" * 40, candidate_version="9.8.6",
                   src_dir="candidate", wiki_dir="candidate/docs/llm_wiki",
                   source_archive_sha256="sha256:" + shadow.identity["source"]["archive_sha256"])
    ci = _ci(report, schema="v4")
    shadow.maintenance = {"ci-report.json": raw(ci), "preflight.json": raw(before),
                          "policy.json": raw(hp.derive_policy(raw(ci), raw(before), binding=binding)),
                          "doctor.json": raw(_doctor(report, schema="v4"))}
    directory = tmp_path / "v2-evidence"
    directory.mkdir()
    for name, content in shadow.maintenance.items():
        (directory / name).write_bytes(content)
    receipt = maintenance.admit(directory, shadow.identity, maintenance.policy(raw(shadow.config), policy_shadow=True))
    assert receipt["status"] == "pass", receipt
    digest = maintenance.composite_policy_digest(lambda name: (ROOT / name).read_bytes())
    receipt["activation_proof"] = {"schema_version": "agent-wiki-release-policy-shadow/v1", "qualification": "nonpromoting",
                                    "policy": hp.POLICY_V2_ID, "implementation_sha256": digest}
    shadow.replace("evidence-rd-10", {"maintenance/" + name: content for name, content in shadow.maintenance.items()})
    shadow.replace("knowledge-maintenance-verification", {"verification.json": raw(receipt)})
    shadow.decision["candidate_version"] = "9.8.6"
    shadow.replace("qualification-decision", {"decision.json": raw(shadow.decision)})
    verified = shadow.verify()
    assert verified["activation"]["implementation_sha256"] == digest
    assert activation.proposal(shadow.config, verified)["mode"] == "required"


@pytest.mark.parametrize("field,value", [
    ("head_sha", "c" * 40), ("run_attempt", 2), ("head_branch", "main"),
    ("event", "pull_request"), ("path", ".github/workflows/ci.yml"),
    ("status", "in_progress"), ("conclusion", "failure"),
])
def test_run_must_be_successful_pinned_shadow_producer(shadow, field, value):
    shadow.run[field] = value
    with pytest.raises(hosted.EvidenceError, match="run identity"):
        shadow.verify()


@pytest.mark.parametrize("field", ["repository", "head_repository"])
def test_proof_cannot_come_from_fork_or_other_repository(shadow, field):
    shadow.run[field] = {"id": 20, "full_name": "hostile/fork"}
    with pytest.raises(hosted.EvidenceError, match="run identity"):
        shadow.verify()


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "failed", "wrong-attempt", "wrong-sha"])
def test_each_policy_job_must_succeed_once_for_exact_attempt(shadow, mutation):
    job = next(item for item in shadow.jobs if item["name"] == "Repository knowledge maintenance")
    if mutation == "missing": shadow.jobs.remove(job)
    elif mutation == "duplicate": shadow.jobs.append(deepcopy(job))
    elif mutation == "failed": job["conclusion"] = "failure"
    elif mutation == "wrong-attempt": job["run_attempt"] = 2
    else: job["head_sha"] = "c" * 40
    with pytest.raises(hosted.EvidenceError, match="hosted policy producer"):
        shadow.verify()


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "expired", "wrong-run", "wrong-repository", "wrong-sha", "old-attempt", "digest-mismatch", "missing-member", "unsafe-member"])
def test_artifact_origin_inventory_and_bytes_are_authenticated(shadow, mutation):
    artifact = next(item for item in shadow.artifacts if item["name"] == "evidence-rd-10")
    if mutation == "missing": shadow.artifacts.remove(artifact)
    elif mutation == "duplicate": shadow.artifacts.append(deepcopy(artifact))
    elif mutation == "expired": artifact["expired"] = True
    elif mutation == "wrong-run": artifact["workflow_run"]["id"] = RUN + 1
    elif mutation == "wrong-repository": artifact["workflow_run"]["head_repository_id"] = 50
    elif mutation == "wrong-sha": artifact["workflow_run"]["head_sha"] = "c" * 40
    elif mutation == "old-attempt": artifact["created_at"] = "2026-09-20T10:05:00Z"
    elif mutation == "digest-mismatch": shadow.archives[artifact["id"]] += b"altered"
    elif mutation == "missing-member":
        shadow.files["evidence-rd-10"].pop("maintenance/doctor.json")
        shadow.replace("evidence-rd-10")
    else:
        shadow.files["evidence-rd-10"]["../unsafe"] = b"hostile"
        shadow.replace("evidence-rd-10")
    with pytest.raises(hosted.EvidenceError):
        shadow.verify()


@pytest.mark.parametrize("input_name", maintenance.POLICY_INPUTS)
def test_frozen_policy_inputs_must_equal_trusted_checkout(shadow, input_name):
    files = dict(shadow.source_files)
    files[input_name] += b" changed"
    shadow.replace_source(files)
    shadow.replace("qualification-harnesses", {"qualification-harnesses.tar": source_archive(files)})
    with pytest.raises(hosted.EvidenceError, match="trusted checkout"):
        shadow.verify()


@pytest.mark.parametrize("mutation", ["source-checksum", "source-mode", "source-archive", "harness-config", "harness-missing", "archive-symlink", "archive-duplicate"])
def test_source_and_harness_are_bound_without_executing_downloaded_code(shadow, mutation):
    if mutation == "source-checksum":
        shadow.files["candidate-source"]["SHA256SUMS"] = b"incorrect"
    elif mutation == "source-mode":
        identity = deepcopy(shadow.identity)
        identity["mode"] = "candidate"
        shadow.files["candidate-source"]["identity.json"] = raw(identity)
    elif mutation == "source-archive":
        shadow.files["candidate-source"]["candidate-source.tar"] += b"changed"
    elif mutation.startswith("harness"):
        files = dict(shadow.source_files)
        if mutation == "harness-config": files[maintenance.POLICY_PATH] += b"\n"
        else: files.pop(maintenance.LEAF_PATH)
        shadow.replace("qualification-harnesses", {"qualification-harnesses.tar": source_archive(files)})
    else:
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            for name, content in shadow.source_files.items():
                entry = tarfile.TarInfo(name)
                entry.size = len(content)
                archive.addfile(entry, io.BytesIO(content))
            entry = tarfile.TarInfo(maintenance.LEAF_PATH if mutation == "archive-duplicate" else "link")
            if mutation == "archive-symlink":
                entry.type = tarfile.SYMTYPE
                entry.linkname = "/hostile"
            archive.addfile(entry)
        shadow.files["qualification-harnesses"]["qualification-harnesses.tar"] = stream.getvalue()
        shadow.replace("qualification-harnesses")
    shadow.replace("candidate-source")
    with pytest.raises(hosted.EvidenceError):
        shadow.verify()


@pytest.mark.parametrize("mutation", ["receipt-hash", "wrong-candidate", "wrong-doctor", "editable-install", "wrong-scope"])
def test_receipt_is_replayed_from_original_policy_and_parity_inputs(shadow, mutation):
    if mutation == "receipt-hash": shadow.receipt["evidence_sha256"]["doctor.json"] = "sha256:" + "0" * 64
    elif mutation == "wrong-candidate": shadow.receipt["candidate_sha"] = "c" * 40
    elif mutation == "wrong-doctor": shadow.files["evidence-rd-10"]["maintenance/doctor.json"] = b'{}'
    else:
        preflight = json.loads(shadow.files["evidence-rd-10"]["maintenance/preflight.json"])
        if mutation == "editable-install": preflight["installed"]["editable"] = True
        else: preflight["binding"]["src_dir"] = "outside-candidate"
        shadow.files["evidence-rd-10"]["maintenance/preflight.json"] = raw(preflight)
    shadow.replace("knowledge-maintenance-verification", {"verification.json": raw(shadow.receipt)})
    shadow.replace("evidence-rd-10")
    with pytest.raises(hosted.EvidenceError, match="replayed|replay"):
        shadow.verify()


@pytest.mark.parametrize("mutation", ["promotion-job", "promoting-artifact", "failed-decision", "promoting-decision", "incomplete-decision", "wrong-decision-candidate"])
def test_policy_shadow_cannot_claim_release_qualification(shadow, mutation):
    if mutation == "promotion-job": shadow.jobs[-1]["conclusion"] = "success"
    elif mutation == "promoting-artifact": shadow.artifacts.append({"name": "qualified-release"})
    elif mutation == "failed-decision": shadow.decision["status"] = "fail"
    elif mutation == "promoting-decision": shadow.decision["nonpromoting"] = False
    elif mutation == "incomplete-decision": shadow.decision["gates"].pop("integrity")
    else: shadow.decision["candidate_sha"] = "c" * 40
    shadow.replace("qualification-decision", {"decision.json": raw(shadow.decision)})
    with pytest.raises(hosted.EvidenceError, match="bounded profile|assembly|qualified release|decision"):
        shadow.verify()


def test_policy_profile_rejects_other_release_jobs_even_when_successful(shadow):
    shadow.jobs.append({**shadow.jobs[0], "name": "RD-11 independent build a", "id": 99})
    with pytest.raises(hosted.EvidenceError, match="bounded profile"):
        shadow.verify()


def test_audit_is_bounded_even_for_large_authenticated_artifact_inventory(shadow):
    shadow.files["evidence-rd-10"].update({f"owned-{number}.txt": b"data" for number in range(1000)})
    shadow.replace("evidence-rd-10")
    with pytest.raises(hosted.EvidenceError, match="audit exceeds"):
        shadow.verify()


def test_proposal_keeps_required_mode_and_rejects_other_policy_contract(shadow):
    verified = shadow.verify()
    config = deepcopy(shadow.config)
    config["mode"] = "disabled"
    with pytest.raises(hosted.EvidenceError, match="required"):
        activation.proposal(config, verified)
    config = deepcopy(shadow.config)
    config.update(schema_version=maintenance.CONFIG_V2_SCHEMA, policy=hp.POLICY_V2_ID)
    with pytest.raises(hosted.EvidenceError, match="contract"):
        activation.proposal(config, verified)


class ActivationPullRequest:
    def __init__(self, shadow):
        self.shadow = shadow
        self.verified = shadow.verify(request_id=REQUEST)
        self.digest = self.verified["activation"]["implementation_sha256"]
        self.audit_path = "release/policy-activations/" + self.digest + ".json"
        self.base, self.head = "c" * 40, "d" * 40
        self.bot = {"login": "activation[bot]", "id": 45}
        self.pr = {
            "number": 42, "user": deepcopy(self.bot), "state": "open", "draft": False,
            "head": {"ref": "codex/policy-activation/" + self.digest, "sha": self.head, "repo": {"full_name": REPOSITORY}},
            "base": {"ref": "main", "sha": self.base, "repo": {"full_name": REPOSITORY}},
            "changed_files": 2,
        }
        self.main = {"ref": "refs/heads/main", "object": {"type": "commit", "sha": self.base}}
        self.commit = {"sha": self.head, "parents": [{"sha": self.base}]}
        self.comparison = {"status": "ahead", "merge_base_commit": {"sha": SHA}}
        self.changed = [{"filename": maintenance.POLICY_PATH, "status": "modified"}, {"filename": self.audit_path, "status": "added"}]
        self.updated = activation.proposal(shadow.config, self.verified)
        self.contents = {(name, self.base): (ROOT / name).read_bytes() for name in maintenance.POLICY_INPUTS}
        self.contents[(maintenance.POLICY_PATH, self.base)] = raw(shadow.config)
        self.contents[(maintenance.POLICY_PATH, SHA)] = raw(shadow.config)
        self.contents[(maintenance.POLICY_PATH, self.head)] = raw(self.updated)
        self.contents[(self.audit_path, self.head)] = raw(self.verified["audit"])

    def get(self, path):
        if path == "/pulls/42": return deepcopy(self.pr)
        if path == "/git/ref/heads/main": return deepcopy(self.main)
        if path == "/git/commits/" + self.head: return deepcopy(self.commit)
        if path == f"/compare/{SHA}...{self.base}": return deepcopy(self.comparison)
        if path.startswith("/contents/"):
            encoded, _, query = path.removeprefix("/contents/").partition("?")
            name, ref = urllib.parse.unquote(encoded), urllib.parse.parse_qs(query)["ref"][0]
            content = self.contents[(name, ref)]
            return {"type": "file", "encoding": "base64", "size": len(content), "content": base64.b64encode(content).decode("ascii")}
        return self.shadow.get(path)

    def list(self, path, key=None):
        if path == "/pulls/42/files": return deepcopy(self.changed)
        return self.shadow.list(path, key)

    def archive(self, artifact_id):
        return self.shadow.archive(artifact_id)

    def validate(self, **kwargs):
        return activation.validate_activation_pr(REPOSITORY, 42, policy_root=self.shadow.policy_root, client=self,
                                                 trusted_bot=self.bot, head_sha=self.head, **kwargs)


def test_activation_pr_replays_bot_proof_and_checks_exact_two_file_change(shadow):
    client = ActivationPullRequest(shadow)
    result = client.validate()
    assert result["status"] == "pass" and result["head_sha"] == client.head
    assert result["activation"] == client.verified["activation"]


def test_manual_approval_pr_replays_main_proof_and_preserves_historical_sha(shadow):
    client = ActivationPullRequest(shadow)
    shadow.run["head_branch"] = "main"
    verified = shadow.verify(main_proof=True)
    client.pr["head"]["ref"] = "codex/manual-policy-activation/" + client.digest
    client.pr["user"] = {"login": "maintainer", "id": 1234}
    client.pr["author_association"] = "OWNER"
    client.contents[(maintenance.POLICY_PATH, client.head)] = raw(activation.proposal(shadow.config, verified))
    client.contents[(client.audit_path, client.head)] = raw(verified["audit"])
    result = client.validate()
    assert result["activation"]["proof_source_sha"] == SHA
    assert client.base != SHA
    client.pr["author_association"] = "NONE"
    with pytest.raises(hosted.EvidenceError, match="authorized proposer"):
        client.validate()


def test_pr_verifier_rejects_base_configuration_drift_after_the_shadow_run(shadow):
    client = ActivationPullRequest(shadow)
    current = deepcopy(shadow.config)
    current["thresholds"] = {"strict": 0.95}
    changed = deepcopy(client.updated)
    changed["thresholds"] = current["thresholds"]
    client.contents[(maintenance.POLICY_PATH, client.base)] = raw(current)
    client.contents[(maintenance.POLICY_PATH, client.head)] = raw(changed)
    with pytest.raises(hosted.EvidenceError, match="configuration differs from current main"):
        client.validate()


def test_ordinary_pull_request_does_not_require_activation_bot_identity(shadow):
    client = ActivationPullRequest(shadow)
    client.pr["head"]["ref"] = "codex/ordinary-fix"
    client.pr["user"] = {"login": "human", "id": 1234}
    assert client.validate() == {"status": "ignored", "pull_request": 42}


@pytest.mark.parametrize("mutation", ["wrong-bot-id", "wrong-bot-login", "fork", "wrong-base", "draft", "closed", "advanced-main", "extra-commit", "side-file", "wrong-head", "untrusted-policy", "changed-scope", "altered-audit", "altered-activation"])
def test_activation_pr_refuses_untrusted_or_superseded_changes(shadow, mutation):
    client = ActivationPullRequest(shadow)
    if mutation == "wrong-bot-id": client.pr["user"]["id"] += 1
    elif mutation == "wrong-bot-login": client.pr["user"]["login"] = "hostile"
    elif mutation == "fork": client.pr["head"]["repo"]["full_name"] = "hostile/fork"
    elif mutation == "wrong-base": client.pr["base"]["ref"] = "release"
    elif mutation == "draft": client.pr["draft"] = True
    elif mutation == "closed": client.pr["state"] = "closed"
    elif mutation == "advanced-main": client.main["object"]["sha"] = "e" * 40
    elif mutation == "extra-commit": client.commit["parents"] = [{"sha": "e" * 40}]
    elif mutation == "side-file": client.changed[1]["filename"] = "src/side.py"
    elif mutation == "wrong-head": client.pr["head"]["sha"] = "e" * 40
    elif mutation == "untrusted-policy": client.contents[(maintenance.LEAF_PATH, client.base)] += b"changed"
    elif mutation == "changed-scope":
        client.updated["wiki_dir"] = "other/wiki"
        client.contents[(maintenance.POLICY_PATH, client.head)] = raw(client.updated)
    elif mutation == "altered-audit":
        audit = deepcopy(client.verified["audit"])
        audit["candidate_tree"] = "e" * 40
        client.contents[(client.audit_path, client.head)] = raw(audit)
    else:
        client.updated["activation"]["comparison_sha256"] = "0" * 64
        client.contents[(maintenance.POLICY_PATH, client.head)] = raw(client.updated)
    with pytest.raises(hosted.EvidenceError):
        client.validate()


def test_shadow_request_identifier_is_bound_to_hosted_display_title(shadow):
    with pytest.raises(hosted.EvidenceError, match="request identity"):
        shadow.verify(request_id="e" * 64)


@pytest.mark.parametrize("request_value", ["", "qa-" + REQUEST, REQUEST.upper(), "f" * 63, "f" * 65, True])
def test_shadow_request_identity_requires_canonical_sha256(shadow, request_value):
    with pytest.raises(hosted.EvidenceError, match="invalid renewal request identity"):
        shadow.verify(request_id=request_value)


@pytest.mark.parametrize("mutation", ["unmerged", "wrong-ancestor"])
def test_activation_proof_must_come_from_merged_main_history(shadow, mutation):
    client = ActivationPullRequest(shadow)
    if mutation == "unmerged": client.comparison["status"] = "diverged"
    else: client.comparison["merge_base_commit"]["sha"] = "e" * 40
    with pytest.raises(hosted.EvidenceError, match="protected main history"):
        client.validate()


@pytest.mark.parametrize("operation", ["run", "jobs", "archive", "pull-request"])
def test_unavailable_hosted_service_blocks_activation_without_proposal(shadow, monkeypatch, operation):
    def unavailable(*args, **kwargs):
        raise OSError("hosted service unavailable")

    if operation == "pull-request":
        client = ActivationPullRequest(shadow)
        monkeypatch.setattr(client, "get", unavailable)
        with pytest.raises(hosted.EvidenceError, match="hosted service unavailable"):
            client.validate()
    else:
        monkeypatch.setattr(shadow, {"run": "get", "jobs": "list", "archive": "archive"}[operation], unavailable)
        with pytest.raises(hosted.EvidenceError, match="hosted service unavailable"):
            shadow.verify()
