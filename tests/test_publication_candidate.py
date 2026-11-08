"""Public wiki candidates preserve target ownership and exact review bases."""

from copy import deepcopy
import json
import shutil
from types import MappingProxyType

import pytest

from llm_wiki_cli.services import publication_candidate as candidate
from llm_wiki_cli.services import publication_impact as impact
from llm_wiki_cli.services.knowledge_evidence import hash_json, sha256_bytes
from tests.test_publication_impact import consumer as consumer


def configure(root, *, manual=False):
    path = root / ".llm-wiki/publication.json"
    policy = json.loads(path.read_text())
    dependency = policy["topics"][0]["depends_on"]
    docs = root / "docs/public"
    docs.mkdir(parents=True)
    (docs / "Home.md").write_text(
        "# Home\n\n[Accounts](Accounts.md#accounts)\n", encoding="utf-8"
    )
    (docs / "Accounts.md").write_text(
        "# Accounts\n\n[Home](Home.md) [Limits](assets/limits.txt)\n", encoding="utf-8"
    )
    (docs / "_Sidebar.md").write_text(
        "[Home](Home.md)\n[Accounts](Accounts.md)\n", encoding="utf-8"
    )
    (docs / "assets").mkdir()
    (docs / "assets/limits.txt").write_text("Maximum: 10\n", encoding="utf-8")
    policy["content"] = {
        "root": "docs/public",
        "assets": [
            {
                "source_document": "docs/public/assets/limits.txt",
                "wiki_path": "assets/limits.txt",
                "owner": "maintainers",
            }
        ],
        "adoptions": [
            {
                "path": "Accounts.md",
                "expected_hash": sha256_bytes(
                    (root / "public/Accounts.md").read_bytes()
                ),
                "reason": "Import the reviewed public account guide",
            }
        ],
    }
    policy["topics"] = [
        {
            "id": stem,
            "owner": "maintainers",
            "wiki_page": name,
            "edit_at": "repository",
            "source_document": f"docs/public/{name}",
            "depends_on": dependency,
        }
        for stem, name in (
            ("home", "Home.md"),
            ("accounts", "Accounts.md"),
            ("navigation", "_Sidebar.md"),
        )
    ]
    if manual:
        (root / "public/Notes.md").write_text(
            "# Notes\n\nHandwritten notes.\n", encoding="utf-8"
        )
        policy["topics"].append(
            {
                "id": "notes",
                "owner": "editors",
                "wiki_page": "Notes.md",
                "edit_at": "wiki",
                "depends_on": dependency,
            }
        )
    path.write_text(json.dumps(policy), encoding="utf-8")
    return policy


def export(root, output="reports/candidate", **kwargs):
    return candidate.export_publication_candidate(
        root, output_dir=output, target_dir="public", **kwargs
    )


def accept_topics(receipt):
    ledger = None
    for finding in receipt["impact"]["findings"]:
        if finding["kind"] == "topic":
            ledger = impact.resolve_publication_finding(
                receipt["impact"],
                receipt["basis"],
                finding_id=finding["id"],
                reviewer="alice",
                reason="Reviewed the proposed public content",
                reviews=ledger,
                decision="retired"
                if any(r["kind"] == "mapping-retired" for r in finding["reasons"])
                else "still-current",
            )
    return ledger


def test_candidate_is_deterministic_and_preserves_manual_content(consumer):
    configure(consumer, manual=True)
    before = {p.name: p.read_bytes() for p in (consumer / "public").iterdir()}
    first = export(consumer)
    second = export(consumer, "reports/second")
    assert first == second
    assert (consumer / "reports/candidate/Notes.md").read_bytes() == before["Notes.md"]
    assert {p.name: p.read_bytes() for p in (consumer / "public").iterdir()} == before
    assert "(Accounts#accounts)" in (consumer / "reports/candidate/Home.md").read_text()
    assert first["checks"]["ok"] and not first["ready"] and not first["delivery_ready"]
    assert "Notes.md" not in first["ownership"]
    assert first["basis"]["targets"]["accounts"]["hash"] == sha256_bytes(
        (consumer / "reports/candidate/Accounts.md").read_bytes()
    )
    candidate.validate_publication_receipt(first)


def test_exact_candidate_and_topic_review_enable_local_readiness(consumer):
    configure(consumer)
    receipt = export(consumer)
    approval = candidate.review_publication_candidate(
        receipt, reviewer="bob", reason="Reviewed the complete artifact and operations"
    )
    checked = candidate.check_publication_candidate(
        consumer,
        candidate_dir="reports/candidate",
        receipt=receipt,
        target_dir="public",
        reviews=accept_topics(receipt),
        candidate_review=approval,
    )
    assert checked["candidate_id"] == receipt["candidate_id"]
    assert checked["ready"] and not checked["delivery_ready"]
    assert checked["receipt_id"] != receipt["receipt_id"]
    assert checked["target"]["remote_verified"] is False


@pytest.mark.parametrize("change", ["candidate", "source", "asset", "manual", "config"])
def test_check_rejects_changed_inputs_or_candidate(consumer, change):
    configure(consumer, manual=True)
    receipt = export(consumer)
    paths = {
        "candidate": "reports/candidate/Accounts.md",
        "source": "docs/public/Accounts.md",
        "asset": "docs/public/assets/limits.txt",
        "manual": "public/Notes.md",
    }
    if change == "config":
        path = consumer / ".llm-wiki/publication.json"
        policy = json.loads(path.read_text())
        policy["topics"][0]["owner"] = "another-owner"
        path.write_text(json.dumps(policy))
    else:
        path = consumer / paths[change]
        path.write_bytes(path.read_bytes() + b"Changed.\n")
    with pytest.raises(ValueError):
        candidate.check_publication_candidate(
            consumer,
            candidate_dir="reports/candidate",
            receipt=receipt,
            target_dir="public",
        )


def test_manual_content_requires_exact_import_adoption(consumer):
    policy = configure(consumer)
    policy["content"].pop("adoptions")
    path = consumer / ".llm-wiki/publication.json"
    path.write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="adoption"):
        export(consumer)
    policy["content"]["adoptions"] = [
        {
            "path": "Accounts.md",
            "expected_hash": sha256_bytes(b"wrong"),
            "reason": "Import",
        }
    ]
    path.write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="Adoption"):
        export(consumer)
    assert not (consumer / "reports/candidate").exists()


def test_artifact_only_source_bootstrap_needs_no_target_or_html(consumer):
    policy = configure(consumer)
    policy["content"].pop("adoptions")
    policy["architecture"] = {"baseline": "bootstrap-source", "root": "src"}
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    result = candidate.export_publication_candidate(consumer, output_dir="reports/new")
    assert result["target"]["mode"] == "artifact-only" and result["checks"]["ok"]
    assert (consumer / "reports/new/Home.md").is_file()
    assert not result["delivery_ready"]


@pytest.mark.parametrize(
    "output",
    [
        ".",
        "docs/public/out",
        "wiki/out",
        "public/out",
        "docs/public",
        ".llm-wiki/publication.json/out",
    ],
)
def test_outputs_cannot_overlap_inputs(consumer, output):
    configure(consumer)
    with pytest.raises(ValueError):
        export(consumer, output)


def test_mixed_or_anchored_repository_ownership_is_not_replaced(consumer):
    policy = configure(consumer)
    policy["topics"][1]["anchor"] = "accounts"
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="whole-page"):
        export(consumer)


def test_unowned_deletion_and_implicit_retirement_are_blocked(consumer):
    policy = configure(consumer)
    receipt = export(consumer)
    receipt = candidate.check_publication_candidate(
        consumer,
        candidate_dir="reports/candidate",
        receipt=receipt,
        target_dir="public",
        reviews=accept_topics(receipt),
        candidate_review=candidate.review_publication_candidate(
            receipt, reviewer="alice", reason="Reviewed artifact"
        ),
    )
    # Simulate the explicitly reviewed candidate becoming the next local target.
    for path in receipt["files"]:
        destination = consumer / "public" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((consumer / "reports/candidate" / path).read_bytes())
    policy["content"].pop("adoptions")
    policy["topics"] = [t for t in policy["topics"] if t["id"] != "accounts"]
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="explicit removals"):
        export(consumer, "reports/next", previous_receipt=receipt)
    policy["content"]["removals"] = [
        {"path": "Unknown.md", "expected_hash": None, "reason": "Remove"}
    ]
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    with pytest.raises(ValueError):
        export(
            consumer,
            "reports/next",
            previous_receipt=receipt,
            baseline=receipt["basis"],
        )


def test_owned_retirement_requires_and_retains_exact_review(consumer):
    policy = configure(consumer)
    original = export(consumer)
    accepted = candidate.check_publication_candidate(
        consumer,
        candidate_dir="reports/candidate",
        receipt=original,
        target_dir="public",
        reviews=accept_topics(original),
        candidate_review=candidate.review_publication_candidate(
            original, reviewer="alice", reason="Reviewed artifact"
        ),
    )
    for path in accepted["files"]:
        destination = consumer / "public" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((consumer / "reports/candidate" / path).read_bytes())
    policy["content"].pop("adoptions")
    policy["content"]["removals"] = [
        {
            "path": "Accounts.md",
            "expected_hash": accepted["files"]["Accounts.md"],
            "reason": "Retire the account guide",
        }
    ]
    policy["topics"] = [
        topic for topic in policy["topics"] if topic["id"] != "accounts"
    ]
    (consumer / "docs/public/Home.md").write_text("# Home\n\nPublic home.\n")
    (consumer / "docs/public/_Sidebar.md").write_text("[Home](Home.md)\n")
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    proposed = export(
        consumer,
        "reports/retired",
        previous_receipt=accepted,
        baseline=accepted["basis"],
    )
    assert not (consumer / "reports/retired/Accounts.md").exists()
    assert (consumer / "public/Accounts.md").exists()
    assert any(
        op["kind"] == "remove" and op["path"] == "Accounts.md"
        for op in proposed["operations"]
    )
    checked = candidate.check_publication_candidate(
        consumer,
        candidate_dir="reports/retired",
        receipt=proposed,
        target_dir="public",
        previous_receipt=accepted,
        baseline=accepted["basis"],
        reviews=accept_topics(proposed),
        candidate_review=candidate.review_publication_candidate(
            proposed, reviewer="bob", reason="Reviewed retirement"
        ),
    )
    assert checked["ready"] and not checked["delivery_ready"]


def test_unreviewed_receipt_does_not_grant_ownership(consumer):
    configure(consumer)
    receipt = export(consumer)
    with pytest.raises(ValueError, match="accepted"):
        export(consumer, "reports/unreviewed", previous_receipt=receipt)


def test_oversized_composed_tree_is_rejected_before_writes(consumer, monkeypatch):
    configure(consumer)
    (consumer / "docs/public/assets/limits.txt").write_bytes(b"x" * 120_000)
    monkeypatch.setattr(candidate, "MAX_TREE_BYTES", 100_000)
    with pytest.raises(ValueError, match="Composed candidate"):
        export(consumer)
    assert not (consumer / "reports/candidate").exists()


def test_review_tree_recomputes_checks_instead_of_trusting_receipt(consumer):
    configure(consumer)
    (consumer / "docs/public/Home.md").write_text("# Home\n\n[Missing](#missing)\n")
    receipt = export(consumer)
    assert not receipt["checks"]["ok"]
    receipt["checks"] = {"ok": True, "findings": []}
    receipt["candidate_id"] = candidate._proposal(receipt)
    receipt["receipt_id"] = hash_json(
        {key: value for key, value in receipt.items() if key != "receipt_id"}
    )
    candidate.validate_publication_receipt(receipt)
    with pytest.raises(ValueError, match="checks differ"):
        candidate.validate_candidate_tree(consumer, "reports/candidate", receipt)


@pytest.mark.parametrize("kind", ["source", "reference", "native"])
def test_all_evidence_is_rechecked_after_rendering(consumer, monkeypatch, kind):
    from llm_wiki_cli.services import publication_links
    from tests.test_publication_references import app_contract

    policy = configure(consumer)
    if kind == "source":
        source = consumer / "src/accounts.py"
        policy["topics"][0]["depends_on"].append({"source_file": "src/accounts.py"})
    elif kind == "reference":
        source = consumer / "contract.json"
        source.write_text(json.dumps(app_contract()))
        policy["reference_providers"] = {
            "app": {"kind": "contract-file", "path": "contract.json"}
        }
        policy["topics"][0]["depends_on"].append(
            {"reference": "app", "command": ["create"]}
        )
    else:
        source = consumer / "wiki/modules/accounts.md"
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    original = publication_links.prepare_wiki_markdown
    changed = False

    def concurrent_change(*args, **kwargs):
        nonlocal changed
        if not changed:
            changed = True
            source.write_text(
                json.dumps(app_contract(name="changed"))
                if kind == "reference"
                else source.read_text() + "\n# Concurrent change\n"
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(publication_links, "prepare_wiki_markdown", concurrent_change)
    with pytest.raises(ValueError):
        export(consumer)
    assert not (consumer / "reports/candidate").exists()


def test_provider_identity_includes_runtime_registry(consumer, monkeypatch):
    package = consumer / "fake-package"
    (package / "services").mkdir(parents=True)
    (package / "a.py").write_text("VALUE = 1\n")
    (package / "py.typed").touch()
    registry = package / "services/analysis_contracts.json"
    payload = {
        "classified_python_files": ["a.py"],
        "classified_helper_files": [],
        "policy": "first",
    }
    registry.write_text(json.dumps(payload))
    monkeypatch.setattr(
        candidate, "__file__", str(package / "services/publication_candidate.py")
    )
    first = candidate._provider()
    payload["policy"] = "second"
    registry.write_text(json.dumps(payload))
    assert candidate._provider()["fingerprint"] != first["fingerprint"]


@pytest.mark.parametrize(
    "path", [".git/new-candidate", ".hg/new-candidate", ".venv/new-candidate"]
)
def test_output_never_writes_into_control_state(consumer, path):
    configure(consumer)
    with pytest.raises(ValueError, match="VCS or runtime"):
        export(consumer, path)
    assert not (consumer / path).exists()


def test_bootstrap_root_keeps_preserved_code_out_of_selected_sources(consumer):
    policy = configure(consumer)
    policy["architecture"] = {"baseline": "bootstrap-source", "root": "."}
    for topic in policy["topics"]:
        topic["depends_on"] = [{"source_file": "src/accounts.py"}]
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    (consumer / "public/example.py").write_text("VALUE = 1\n")
    with pytest.raises(ValueError, match="source|selection|excluded"):
        export(consumer)
    assert not (consumer / "reports/candidate").exists()
    safe = export(consumer, "out/candidate")
    assert (
        candidate.check_publication_candidate(
            consumer, candidate_dir="out/candidate", receipt=safe, target_dir="public"
        )["candidate_id"]
        == safe["candidate_id"]
    )
    external = consumer.parent / (consumer.name + "-artifact")
    outside = export(consumer, external)
    assert (
        candidate.check_publication_candidate(
            consumer, candidate_dir=external, receipt=outside, target_dir="public"
        )["candidate_id"]
        == outside["candidate_id"]
    )
    assert outside["files"] == safe["files"]


def test_explicit_public_reports_asset_directory_is_supported(consumer):
    policy = configure(consumer)
    policy["content"]["assets"][0]["wiki_path"] = "reports/limits.txt"
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    receipt = export(consumer)
    assert receipt["checks"]["ok"]
    assert (consumer / "reports/candidate/reports/limits.txt").read_bytes() == (
        consumer / "docs/public/assets/limits.txt"
    ).read_bytes()


@pytest.mark.parametrize("control", [".git", ".GIT", ".hG", ".SvN"])
def test_target_vcs_entries_are_never_copied(consumer, control):
    configure(consumer)
    metadata = consumer / "public" / control
    metadata.mkdir()
    (metadata / "config").write_text("private VCS settings\n")
    result = export(consumer)
    assert not any(
        path.casefold().startswith(control.casefold() + "/") for path in result["files"]
    )
    assert not (consumer / "reports/candidate" / control).exists()
    assert (metadata / "config").read_text() == "private VCS settings\n"


@pytest.mark.parametrize(
    "target", [".git", ".GIT/objects", "private/.sVn", ".llm-wiki-knowledge"]
)
def test_target_root_cannot_be_control_state(consumer, target):
    configure(consumer)
    directory = consumer / target
    directory.mkdir(parents=True)
    (directory / "config").write_text("private state\n")
    with pytest.raises(ValueError, match="VCS or runtime"):
        candidate.export_publication_candidate(
            consumer, output_dir="reports/candidate", target_dir=target
        )
    assert not (consumer / "reports/candidate").exists()


def test_public_target_copy_can_be_stored_under_local_artifact_metadata(consumer):
    configure(consumer)
    target = ".llm-wiki/targets/public"
    shutil.copytree(consumer / "public", consumer / target)
    receipt = candidate.export_publication_candidate(
        consumer, output_dir="reports/candidate", target_dir=target
    )
    assert receipt["checks"]["ok"]
    candidate.validate_candidate_target(consumer, target, receipt)


def test_custom_configuration_parent_cannot_be_exported_as_a_public_target(consumer):
    policy = configure(consumer)
    directory = consumer / "policies"
    directory.mkdir()
    config = directory / "publication.json"
    config.write_text(json.dumps(policy))
    before = config.read_bytes()
    with pytest.raises(ValueError, match="configuration or source-selection"):
        candidate.export_publication_candidate(
            consumer,
            config_path="policies/publication.json",
            output_dir="reports/candidate",
            target_dir="policies",
        )
    assert config.read_bytes() == before
    assert not (consumer / "reports/candidate").exists()


def test_review_rechecks_original_target_and_rejects_control_roots(consumer):
    configure(consumer, manual=True)
    receipt = export(consumer)
    candidate.validate_candidate_target(consumer, "public", receipt)
    with pytest.raises(ValueError, match="required"):
        candidate.validate_candidate_target(consumer, None, receipt)
    with pytest.raises(ValueError, match="VCS or runtime"):
        candidate.validate_candidate_target(consumer, ".GIT", receipt)
    (consumer / "public/Notes.md").write_text("# Notes\n\nChanged manual content.\n")
    with pytest.raises(ValueError, match="Original target differs"):
        candidate.validate_candidate_target(consumer, "public", receipt)


def test_artifact_only_review_does_not_invent_a_local_target(consumer):
    policy = configure(consumer)
    policy["content"].pop("adoptions")
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    receipt = candidate.export_publication_candidate(
        consumer, output_dir="reports/artifact-only"
    )
    candidate.validate_candidate_target(consumer, None, receipt)
    with pytest.raises(ValueError, match="Artifact-only"):
        candidate.validate_candidate_target(consumer, "public", receipt)


@pytest.mark.parametrize(
    "relationship",
    [
        "exact",
        "ancestor",
        "descendant",
        "case-exact",
        "case-ancestor",
        "case-descendant",
    ],
)
def test_output_cannot_occupy_a_missing_contract_namespace(consumer, relationship):
    policy = configure(consumer)
    kind = relationship.removeprefix("case-")
    contract = "missing.json/contract.json" if kind == "ancestor" else "missing.json"
    stem = "MISSING.JSON" if relationship.startswith("case-") else "missing.json"
    output = stem + "/child" if kind == "descendant" else stem
    policy["reference_providers"] = {"app": {"kind": "contract-file", "path": contract}}
    policy["topics"][0]["depends_on"].append({"reference": "app"})
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="declared input"):
        export(consumer, output)
    assert not (consumer / "missing.json").exists()
    assert not (consumer / "MISSING.JSON").exists()


def test_output_protects_former_contract_namespace_and_selection_controls(consumer):
    policy = configure(consumer)
    policy["reference_providers"] = {
        "app": {"kind": "contract-file", "path": "former.json"}
    }
    policy["topics"][0]["depends_on"].append({"reference": "app"})
    path = consumer / ".llm-wiki/publication.json"
    path.write_text(json.dumps(policy))
    baseline = impact.capture_publication_basis(consumer, target_dir="public")
    policy["reference_providers"]["app"]["path"] = "current.json"
    path.write_text(json.dumps(policy))
    for output in (
        "former.json",
        "former.json/candidate",
        ".gitignore",
        ".gitignore/candidate",
        ".llm-wiki/source-selection.json",
    ):
        with pytest.raises(ValueError, match="declared input"):
            export(consumer, output, baseline=baseline)
        assert not (consumer / output).exists()


def test_public_api_accepts_immutable_previous_receipt_mapping(consumer):
    from llm_wiki_cli import api

    policy = configure(consumer)
    proposal = export(consumer)
    accepted = candidate.check_publication_candidate(
        consumer,
        candidate_dir="reports/candidate",
        receipt=proposal,
        target_dir="public",
        reviews=accept_topics(proposal),
        candidate_review=candidate.review_publication_candidate(
            proposal, reviewer="alice", reason="Reviewed artifact"
        ),
    )
    original = deepcopy(accepted)
    frozen = MappingProxyType(accepted)
    candidate.validate_publication_receipt(frozen)
    for name in accepted["files"]:
        destination = consumer / "public" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((consumer / "reports/candidate" / name).read_bytes())
    policy["content"].pop("adoptions")
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    receipt = api.export_publication_candidate(
        consumer,
        output_dir="reports/immutable",
        target_dir="public",
        previous_receipt=frozen,
    )
    assert receipt["ownership"] == accepted["ownership"]
    assert accepted == original


@pytest.mark.parametrize(
    "field", ["target-mode", "ownership-kind", "operation-kind", "finding"]
)
def test_resealed_malformed_enum_values_raise_actionable_errors(consumer, field):
    configure(consumer)
    receipt = export(consumer)
    if field == "target-mode":
        receipt["target"]["mode"] = []
    elif field == "ownership-kind":
        receipt["ownership"]["Home.md"]["kind"] = []
    elif field == "operation-kind":
        receipt["operations"][0]["kind"] = []
    else:
        receipt["checks"] = {"ok": False, "findings": [[]]}
    receipt["receipt_id"] = hash_json(
        {key: value for key, value in receipt.items() if key != "receipt_id"}
    )
    with pytest.raises(ValueError):
        candidate.validate_publication_receipt(receipt)


@pytest.mark.parametrize(
    "field", ["files", "ready", "provider", "candidate_id", "unknown"]
)
def test_receipt_commitments_and_readiness_are_validated(consumer, field):
    configure(consumer)
    receipt = export(consumer)
    damaged = deepcopy(receipt)
    if field == "files":
        damaged["files"]["../outside.md"] = sha256_bytes(b"bad")
    elif field == "ready":
        damaged["ready"] = True
    elif field == "provider":
        damaged["provider"]["fingerprint"] = "bad"
    elif field == "candidate_id":
        damaged["candidate_id"] = sha256_bytes(b"wrong")
    else:
        damaged["unknown"] = True
    damaged["receipt_id"] = hash_json(
        {k: v for k, v in damaged.items() if k != "receipt_id"}
    )
    with pytest.raises(ValueError):
        candidate.validate_publication_receipt(damaged)
