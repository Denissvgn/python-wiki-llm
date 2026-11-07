"""End-to-end publication impact, exact review bases and CLI boundaries."""

from copy import deepcopy
import json

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.knowledge_evidence import hash_json, sha256_bytes
from llm_wiki_cli.services.publication_config import validate_publication_config
from llm_wiki_cli.services.markdown_sections import parse_markdown_document
from llm_wiki_cli.services import publication_impact as impact


def config(root=None):
    value = {
        "schema_version": "llm-wiki-publication/v1",
        "source_policy": "default-branch",
        "architecture": {"baseline": "existing-wiki", "root": "wiki"},
        "target": {"kind": "github-wiki", "repository": "self"},
        "enforcement": "advisory",
        "publish": False,
        "topics": [
            {
                "id": "accounts",
                "owner": "maintainers",
                "wiki_page": "Accounts.md",
                "edit_at": "wiki",
                "depends_on": [{"architecture_page": "modules/accounts.md"}],
            }
        ],
    }
    return validate_publication_config(value, consumer_root=root)


def seal(value, key):
    return {**value, key: hash_json({k: v for k, v in value.items() if k != key})}


def basis(policy=None, text="old", extra=()):
    document = parse_markdown_document(text, "llm-wiki://modules/accounts")
    page = {
        "canonical_path": "modules/accounts.md",
        "kind": "modules",
        "id": "accounts",
        "locator": document.page_locator,
        "mcp_uri": document.page_locator,
        "role": "semantic",
        "uid": None,
        "raw_hash": hash_json(text),
        "normalized_hash": document.exact_hash,
        "section_ordering_hash": document.ordering_hash,
        "sections": [],
        "source_mapping": None,
        "source_basis": {
            "scope": "module",
            "source_path": "accounts.py",
            "extractor_ref": "python",
            "source_content_hash": hash_json(text),
            "concept_observation_hash": None,
            "aggregate_input_hash": None,
            "extensions": {},
        },
    }
    pages = [page]
    for value in extra:
        parsed = parse_markdown_document("guide", "llm-wiki://guides/new")
        pages.append(
            {
                **page,
                **value,
                "id": "new",
                "kind": "guides",
                "role": "semantic",
                "locator": parsed.page_locator,
                "mcp_uri": parsed.page_locator,
                "section_ordering_hash": parsed.ordering_hash,
            }
        )
    native = seal(
        {
            "schema_version": "llm-wiki-publication-snapshot/v1",
            "complete": True,
            "pages": pages,
            "coverage": {
                "scope": "canonical-native-pages",
                "page_count": len(pages),
                "section_model": "native-atx/v1",
                "source_mapping": "non-exhaustive",
            },
            "freshness": {"scope": "snapshot-only", "state": "not-evaluated"},
            "commitments": {
                **{
                    key: hash_json("options")
                    for key in (
                        "source_snapshot_hash",
                        "markdown_snapshot_hash",
                        "generation_options_hash",
                        "surface_index_hash",
                        "knowledge_index_hash",
                        "evaluated_envelope_hash",
                        "governance_hash",
                        "producer_hash",
                        "manifest_hash",
                    )
                },
                "manifest_storage_version": 8,
            },
        },
        "snapshot_id",
    )
    return seal(
        {
            "schema_version": impact.BASIS_SCHEMA,
            "config": policy or config(),
            "architecture": native,
            "files": {},
            "targets": {
                "accounts": {"state": "available", "hash": hash_json("public text")}
            },
        },
        "basis_id",
    )


def test_many_to_many_union_keeps_all_dependency_reasons():
    before = basis()
    policy = config()
    second = deepcopy(policy["topics"][0])
    second.update(id="troubleshooting", wiki_page="Troubleshooting.md")
    policy["topics"].append(second)
    after = basis(policy, "new")
    report = impact.compare_publication_impact(after, before)
    assert report["complete"] and report["review_required"]
    assert {f["subject"] for f in report["findings"]} == {"accounts", "troubleshooting"}
    assert report == impact.compare_publication_impact(after, before)


def test_review_clears_and_reopens_on_covered_source_or_target_change():
    before, after = basis(), basis(text="new")
    report = impact.compare_publication_impact(after, before)
    finding = report["findings"][0]
    ledger = impact.resolve_publication_finding(
        report,
        after,
        finding_id=finding["id"],
        reviewer="alice",
        reason="The public contract is unchanged",
    )
    resolved = impact.compare_publication_impact(after, before, reviews=ledger)
    assert resolved["ready"] and not resolved["review_required"]
    assert impact.compare_publication_impact(
        basis(text="newer"), before, reviews=ledger
    )["review_required"]
    edited = deepcopy(after)
    edited["targets"]["accounts"]["hash"] = hash_json("edited public page")
    edited = seal(edited, "basis_id")
    assert impact.compare_publication_impact(edited, before, reviews=ledger)[
        "review_required"
    ]


def test_removed_binding_still_reaches_former_public_target():
    before = basis()
    policy = config()
    policy["topics"] = []
    after = basis(policy, "new")
    report = impact.compare_publication_impact(after, before)
    assert any(
        f["subject"] == "accounts" and f["kind"] == "topic" for f in report["findings"]
    )
    assert any(f["status"] == "unmapped" for f in report["findings"])


def test_remapped_topic_keeps_a_review_obligation_at_the_former_destination():
    before = basis()
    policy = config()
    policy["topics"][0]["wiki_page"] = "Replacement.md"
    report = impact.compare_publication_impact(basis(policy), before)
    assert {finding["wiki_page"] for finding in report["findings"]} == {
        "Accounts.md",
        "Replacement.md",
    }
    assert any(
        finding["subject"].startswith("previous:") for finding in report["findings"]
    )


def test_new_unmapped_pages_require_explicit_exclusion():
    extra = [
        {
            "canonical_path": "guides/new.md",
            "normalized_hash": hash_json("guide"),
            "sections": [],
        }
    ]
    after = basis(extra=extra)
    report = impact.compare_publication_impact(after, basis())
    assert report["coverage"]["unmapped"] == 1
    policy = config()
    policy["exclusions"] = [
        {"pattern": "guides/*", "reason": "Internal operator material"}
    ]
    report = impact.compare_publication_impact(basis(policy, extra=extra), basis())
    assert report["coverage"]["unmapped"] == 0


def test_missing_native_page_is_incomplete_and_cannot_be_acknowledged():
    before, after = basis(), basis(text="new")
    after["architecture"]["pages"] = []
    after["architecture"]["coverage"]["page_count"] = 0
    after["architecture"] = seal(after["architecture"], "snapshot_id")
    after = seal(after, "basis_id")
    report = impact.compare_publication_impact(after, before)
    assert not report["complete"]
    with pytest.raises(ValueError, match="complete topic"):
        impact.resolve_publication_finding(
            report,
            after,
            finding_id=report["findings"][0]["id"],
            reviewer="x",
            reason="ignore",
        )


def test_stale_and_tampered_evidence_is_rejected():
    report = impact.compare_publication_impact(basis(text="new"), basis())
    with pytest.raises(ValueError, match="stale"):
        impact.resolve_publication_finding(
            report,
            basis(text="later"),
            finding_id=report["findings"][0]["id"],
            reviewer="x",
            reason="ok",
        )
    tampered = basis()
    tampered["config"]["publish"] = True
    with pytest.raises(ValueError):
        impact.compare_publication_impact(tampered)


def test_section_dependency_retains_source_evidence():
    policy = config()
    dep = policy["topics"][0]["depends_on"][0]
    dep["section"] = "llm-wiki://modules/accounts#section/Behavior~1"
    before = basis(policy)
    page = before["architecture"]["pages"][0]
    parsed = parse_markdown_document("# Behavior\nsame prose", page["locator"])
    page["sections"] = [
        {**s.to_payload(), "ownership": "semantic", "semantic_hash": s.exact_hash}
        for s in parsed.sections
    ]
    page["section_ordering_hash"] = parsed.ordering_hash
    before["architecture"] = seal(before["architecture"], "snapshot_id")
    before = seal(before, "basis_id")
    after = deepcopy(before)
    after["architecture"]["pages"][0]["source_basis"]["source_content_hash"] = (
        hash_json("new code")
    )
    after["architecture"] = seal(after["architecture"], "snapshot_id")
    after = seal(after, "basis_id")
    assert impact.compare_publication_impact(after, before)["review_required"]


@pytest.fixture
def consumer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/accounts.py").write_text("class Account:\n    pass\n")
    api.bootstrap_wiki("src", "wiki")
    (tmp_path / ".llm-wiki").mkdir()
    policy = config(tmp_path)
    policy["exclusions"] = [
        {"pattern": "*", "reason": "Only mapped accounts topic is public"}
    ]
    (tmp_path / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    (tmp_path / "public").mkdir()
    (tmp_path / "public/Accounts.md").write_text(
        "# Accounts\n\nAccounts identify people.\n"
    )
    return tmp_path


def invoke(monkeypatch, *args):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "docs", "impact", *args])
    try:
        cli.main()
    except SystemExit as exc:
        return exc.code
    return 0


def test_content_assets_capture_current_and_former_inputs(consumer):
    config_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(config_path.read_text())
    policy["content"] = {
        "root": "public-source",
        "assets": [
            {
                "source_document": "public-source/before.png",
                "wiki_path": "assets/diagram.png",
                "owner": "maintainers",
            }
        ],
    }
    source = consumer / "public-source"
    source.mkdir()
    (source / "before.png").write_bytes(b"first public image")
    config_path.write_text(json.dumps(policy))
    before = impact.capture_publication_basis(consumer, target_dir="public")
    assert before["files"]["public-source/before.png"] == sha256_bytes(
        b"first public image"
    )
    policy["content"]["assets"][0]["source_document"] = "public-source/after.png"
    config_path.write_text(json.dumps(policy))
    (source / "before.png").unlink()
    (source / "after.png").write_bytes(b"replacement public image")
    after = impact.capture_publication_basis(
        consumer, target_dir="public", baseline=before
    )
    assert after["files"]["public-source/before.png"] is None
    assert after["files"]["public-source/after.png"] == sha256_bytes(
        b"replacement public image"
    )


def test_missing_content_asset_is_recorded_as_known_missing(consumer):
    config_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(config_path.read_text())
    policy["content"] = {
        "root": "public-source",
        "assets": [
            {
                "source_document": "public-source/missing.pdf",
                "wiki_path": "assets/guide.pdf",
                "owner": "maintainers",
            }
        ],
    }
    config_path.write_text(json.dumps(policy))
    captured = impact.capture_publication_basis(consumer)
    assert captured["files"]["public-source/missing.pdf"] is None


def test_target_projection_is_pure_detached_and_deterministic(consumer, monkeypatch):
    original = impact.capture_publication_basis(consumer, target_dir="public")
    unchanged = deepcopy(original)
    raw = b"# Accounts\n\nA revised public description.\n"
    monkeypatch.setattr(
        impact,
        "publication_path",
        lambda *args: pytest.fail("projection must not use the filesystem"),
    )
    projected = impact.project_publication_targets(original, {"Accounts.md": raw})
    assert projected == impact.project_publication_targets(
        original, {"Accounts.md": raw}
    )
    assert projected["basis_id"] != original["basis_id"]
    assert projected["targets"]["accounts"] == impact.publication_target_observation(
        original["config"]["topics"][0], raw
    )
    assert original == unchanged


def test_projected_targets_retain_previous_destination_obligations(consumer):
    before = impact.capture_publication_basis(consumer, target_dir="public")
    config_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(config_path.read_text())
    policy["topics"][0]["wiki_page"] = "New-Accounts.md"
    config_path.write_text(json.dumps(policy))
    inputs = impact.capture_publication_basis(
        consumer, target_dir="public", baseline=before
    )
    projected = impact.project_publication_targets(
        inputs, {"New-Accounts.md": b"# Accounts\n\nMoved page.\n"}, baseline=before
    )
    former = next(key for key in projected["targets"] if key.startswith("previous:"))
    assert projected["targets"][former] == {"state": "missing", "hash": None}
    assert projected["targets"]["accounts"]["state"] == "available"


@pytest.mark.parametrize(
    "files",
    [
        {"../outside.md": b"public"},
        {"/outside.md": b"public"},
        {"Accounts.md": "not bytes"},
        {"Accounts.md": b"one", "accounts.md": b"two"},
        {"assets/a.png": b"one", "assets/a.png/nested.png": b"two"},
        {1: b"public"},
    ],
)
def test_target_projection_rejects_unsafe_file_maps(consumer, files):
    captured = impact.capture_publication_basis(consumer)
    with pytest.raises(ValueError):
        impact.project_publication_targets(captured, files)


def test_target_observation_handles_plain_anchors_and_missing_bytes():
    topic = {"wiki_page": "Guide.md", "anchor": "details"}
    raw = b"# Guide\n\n## Details\n\nA public section.\n"
    assert impact.publication_target_observation(topic, None) == {
        "state": "missing",
        "hash": None,
    }
    assert impact.publication_target_observation(topic, raw)["state"] == "available"
    assert (
        impact.publication_target_observation(
            topic, raw + b"\n## Details\n\nAmbiguous.\n"
        )["state"]
        == "unresolved-anchor"
    )


def test_consumer_cli_capture_review_and_rerun(consumer, monkeypatch, capsys):
    assert invoke(monkeypatch, "--target-dir", "public", "--output", "report.json") == 0
    report = json.loads((consumer / "report.json").read_text())
    topic = next(f for f in report["findings"] if f["kind"] == "topic")
    assert (
        invoke(
            monkeypatch,
            "resolve",
            "--target-dir",
            "public",
            "--report",
            "report.json",
            "--finding",
            topic["id"],
            "--decision",
            "still-current",
            "--reviewer",
            "alice",
            "--reason",
            "Initial public description matches",
            "--output",
            "reviews.json",
        )
        == 0
    )
    assert (
        invoke(
            monkeypatch,
            "--target-dir",
            "public",
            "--reviews",
            "reviews.json",
            "--output",
            "resolved.json",
        )
        == 0
    )
    assert json.loads((consumer / "resolved.json").read_text())["ready"]
    assert (
        invoke(
            monkeypatch, "snapshot", "--target-dir", "public", "--output", "basis.json"
        )
        == 0
    )
    capsys.readouterr()
    assert (
        invoke(monkeypatch, "--target-dir", "public", "--baseline", "basis.json") == 0
    )
    assert not json.loads(capsys.readouterr().out)["changed"]


def test_cli_required_and_incomplete_exit_codes(consumer, monkeypatch, capsys):
    path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(path.read_text())
    policy["enforcement"] = "required"
    path.write_text(json.dumps(policy))
    assert invoke(monkeypatch, "--target-dir", "public") == 1
    (consumer / "wiki/.llm-wiki-knowledge.json").unlink()
    assert invoke(monkeypatch, "--target-dir", "public", "--output", "broken.json") == 2
    assert not json.loads((consumer / "broken.json").read_text())["complete"]


def test_output_cannot_replace_native_or_target_input(consumer, monkeypatch):
    page = consumer / "public/Accounts.md"
    previous = page.read_bytes()
    assert (
        invoke(monkeypatch, "--target-dir", "public", "--output", "public/Accounts.md")
        == 2
    )
    assert page.read_bytes() == previous


@pytest.mark.parametrize("kind", ["reference", "source_file", "source_document"])
@pytest.mark.parametrize("action", [[], ["snapshot"]])
@pytest.mark.parametrize("overlap", ["exact", "descendant", "ancestor"])
def test_publication_artifacts_do_not_create_declared_missing_inputs(
    consumer, monkeypatch, kind, action, overlap
):
    policy_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(policy_path.read_text())
    target = (
        "app-input.json/contract.json" if overlap == "ancestor" else "app-input.json"
    )
    output = (
        "app-input.json/report.json" if overlap == "descendant" else "app-input.json"
    )
    if kind == "reference":
        policy["reference_providers"] = {
            "app": {"kind": "contract-file", "path": target}
        }
        policy["topics"][0]["depends_on"] = [{"reference": "app"}]
    elif kind == "source_file":
        policy["topics"][0]["depends_on"].append({"source_file": target})
    else:
        policy["topics"][0].update(edit_at="repository", source_document=target)
    policy_path.write_text(json.dumps(policy))
    assert (
        invoke(monkeypatch, *action, "--target-dir", "public", "--output", output) == 2
    )
    assert not (consumer / "app-input.json").exists()


def test_former_reference_coordinate_stays_protected_during_rebinding(
    consumer, monkeypatch
):
    policy_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(policy_path.read_text())
    policy["reference_providers"] = {
        "app": {"kind": "contract-file", "path": "former.json"}
    }
    policy["topics"][0]["depends_on"] = [{"reference": "app"}]
    policy_path.write_text(json.dumps(policy))
    before = impact.capture_publication_basis(consumer, target_dir="public")
    (consumer / "accepted.json").write_text(json.dumps(before))
    policy["reference_providers"]["app"]["path"] = "current.json"
    policy_path.write_text(json.dumps(policy))
    assert (
        invoke(
            monkeypatch,
            "snapshot",
            "--target-dir",
            "public",
            "--baseline",
            "accepted.json",
            "--output",
            "former.json",
        )
        == 2
    )
    assert not (consumer / "former.json").exists()


def test_missing_accepted_ledger_is_not_replaced_by_an_error_report(
    consumer, monkeypatch
):
    assert (
        invoke(
            monkeypatch,
            "--target-dir",
            "public",
            "--reviews",
            "accepted-reviews.json",
            "--output",
            "accepted-reviews.json",
        )
        == 2
    )
    assert not (consumer / "accepted-reviews.json").exists()


def test_publication_tree_protection_follows_filesystem_case_aliases(
    consumer, monkeypatch
):
    alias = consumer / "PUBLIC"
    same_directory = alias.exists()
    result = invoke(
        monkeypatch, "--target-dir", "public", "--output", "PUBLIC/report.json"
    )
    if same_directory:
        assert result == 2
        assert not (consumer / "public/report.json").exists()
    else:
        assert result == 0
        assert (alias / "report.json").exists()


def test_snapshot_output_stays_within_its_read_budget(consumer, monkeypatch):
    from llm_wiki_cli.commands import publication_cmd

    expected = impact.capture_publication_basis(consumer, target_dir="public")
    budget = len(json.dumps(expected, ensure_ascii=False).encode("utf-8"))
    monkeypatch.setattr(publication_cmd, "MAX_JSON_BYTES", budget)
    monkeypatch.setattr(impact, "MAX_JSON_BYTES", budget)
    assert (
        invoke(
            monkeypatch, "snapshot", "--target-dir", "public", "--output", "basis.json"
        )
        == 0
    )
    path = consumer / "basis.json"
    assert path.stat().st_size <= budget
    assert impact.read_publication_document(path) == expected
    monkeypatch.setattr(publication_cmd, "MAX_JSON_BYTES", 64)
    assert (
        invoke(
            monkeypatch,
            "snapshot",
            "--target-dir",
            "public",
            "--output",
            "oversized.json",
        )
        == 2
    )
    assert not (consumer / "oversized.json").exists()


def test_no_edit_review_requires_actual_target(consumer):
    candidate = impact.capture_publication_basis(consumer)
    report = impact.compare_publication_impact(candidate)
    assert not report["ready"]
    with pytest.raises(ValueError, match="exact available target"):
        impact.resolve_publication_finding(
            report,
            candidate,
            finding_id=report["findings"][0]["id"],
            reviewer="alice",
            reason="ok",
        )


def test_source_only_consumer_uses_temporary_native_storage(consumer, monkeypatch):
    path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(path.read_text())
    policy["architecture"] = {"baseline": "bootstrap-source", "root": "src"}
    path.write_text(json.dumps(policy))
    before = {p: p.read_bytes() for p in (consumer / "src").rglob("*") if p.is_file()}
    assert (
        invoke(monkeypatch, "--target-dir", "public", "--output", "source-only.json")
        == 0
    )
    assert json.loads((consumer / "source-only.json").read_text())["complete"]
    assert {
        p: p.read_bytes() for p in (consumer / "src").rglob("*") if p.is_file()
    } == before


def test_consumer_root_rebases_evidence_and_parent_ledger_options(
    consumer, tmp_path, monkeypatch
):
    outside = consumer / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    root_flags = ["--consumer-root", str(consumer), "--target-dir", "public"]
    assert invoke(monkeypatch, *root_flags, "--output", "report.json") == 0
    report = json.loads((consumer / "report.json").read_text())
    topic = next(f for f in report["findings"] if f["kind"] == "topic")
    (consumer / "accepted.json").write_text(
        json.dumps(
            {
                "schema_version": impact.REVIEWS_SCHEMA,
                "records": [
                    {
                        "topic": "other",
                        "owner": "maintainers",
                        "reviewer": "bob",
                        "reason": "Accepted",
                        "decision": "still-current",
                        "review_basis": hash_json("prior basis"),
                    }
                ],
            }
        )
    )
    assert (
        invoke(
            monkeypatch,
            *root_flags,
            "--reviews",
            "accepted.json",
            "resolve",
            "--report",
            "report.json",
            "--finding",
            topic["id"],
            "--decision",
            "still-current",
            "--reviewer",
            "alice",
            "--reason",
            "Accurate",
            "--output",
            "proposed.json",
        )
        == 0
    )
    assert (consumer / "proposed.json").is_file()
    assert len(json.loads((consumer / "proposed.json").read_text())["records"]) == 2
    assert not (outside / "proposed.json").exists()


def test_output_types_and_checkpoints_are_not_replaced_implicitly(
    consumer, monkeypatch
):
    flags = ["--target-dir", "public"]
    assert invoke(monkeypatch, "snapshot", *flags, "--output", "accepted.json") == 0
    before = (consumer / "accepted.json").read_bytes()
    assert invoke(monkeypatch, *flags, "--output", "accepted.json") == 2
    assert (consumer / "accepted.json").read_bytes() == before
    assert invoke(monkeypatch, "snapshot", *flags, "--output", "accepted.json") == 2
    assert (
        invoke(
            monkeypatch, "snapshot", *flags, "--output", "accepted.json", "--replace"
        )
        == 0
    )


@pytest.mark.parametrize(
    "changed", ["target", "source", "target-appeared", "source-appeared"]
)
def test_late_external_mutation_cannot_escape_native_revalidation(
    consumer, monkeypatch, changed
):
    policy_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(policy_path.read_text())
    policy["topics"][0]["depends_on"].append({"source_file": "limit.json"})
    policy_path.write_text(json.dumps(policy))
    if changed != "source-appeared":
        (consumer / "limit.json").write_text("1")
    if changed == "target-appeared":
        (consumer / "public/Accounts.md").unlink()
    original = impact.build_publication_snapshot
    calls = 0

    def mutate_after_native_validation(path):
        nonlocal calls
        value = original(path)
        calls += 1
        if calls == 2:
            destination = consumer / (
                "public/Accounts.md" if changed.startswith("target") else "limit.json"
            )
            destination.write_text("Changed external evidence")
        return value

    monkeypatch.setattr(
        impact, "build_publication_snapshot", mutate_after_native_validation
    )
    with pytest.raises(ValueError):
        impact.capture_publication_basis(consumer, target_dir="public")


def test_retired_mapping_and_deleted_page_can_be_reviewed(consumer):
    before = impact.capture_publication_basis(consumer, target_dir="public")
    policy_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(policy_path.read_text())
    policy["topics"] = []
    policy_path.write_text(json.dumps(policy))
    (consumer / "public/Accounts.md").unlink()
    after = impact.capture_publication_basis(
        consumer, target_dir="public", baseline=before
    )
    report = impact.compare_publication_impact(after, before)
    finding = report["findings"][0]
    with pytest.raises(ValueError, match="Decision must match"):
        impact.resolve_publication_finding(
            report, after, finding_id=finding["id"], reviewer="alice", reason="Retired"
        )
    ledger = api.resolve_publication_finding(
        report,
        after,
        finding_id=finding["id"],
        reviewer="alice",
        reason="The topic and public page were retired",
        decision="retired",
    )
    closed = impact.compare_publication_impact(after, before, reviews=ledger)
    assert closed["ready"] and closed["findings"][0]["status"] == "reviewed-retired"


def test_retired_approval_reopens_on_former_live_dependency_changes():
    before = basis()
    policy = config()
    policy["topics"][0].update(
        wiki_page="Replacement.md", depends_on=[{"source_file": "stable.txt"}]
    )
    policy["exclusions"] = [
        {
            "pattern": "*",
            "reason": "Former evidence is retained only for retirement review",
        }
    ]
    after = basis(policy)
    after["files"]["stable.txt"] = hash_json("stable")
    previous_id = next(
        key
        for key in impact._topic_versions(policy, before)[0]
        if key.startswith("previous:")
    )
    after["targets"][previous_id] = deepcopy(after["targets"]["accounts"])
    after = seal(after, "basis_id")
    report = impact.compare_publication_impact(after, before)
    ledger = None
    for finding in report["findings"]:
        ledger = impact.resolve_publication_finding(
            report,
            after,
            finding_id=finding["id"],
            reviewer="alice",
            reason="Confirmed current topic and retired destination",
            reviews=ledger,
            decision="retired"
            if finding["subject"] == previous_id
            else "still-current",
        )
    assert impact.compare_publication_impact(after, before, reviews=ledger)["ready"]
    changed = deepcopy(after)
    changed["architecture"]["pages"][0]["source_basis"]["source_content_hash"] = (
        hash_json("new former implementation")
    )
    changed["architecture"] = seal(changed["architecture"], "snapshot_id")
    changed = seal(changed, "basis_id")
    reopened = impact.compare_publication_impact(changed, before, reviews=ledger)
    assert not reopened["ready"]
    assert (
        next(f for f in reopened["findings"] if f["subject"] == previous_id)["status"]
        == "needs-review"
    )


def test_formatted_heading_cannot_validate_an_invented_public_anchor(consumer):
    policy_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(policy_path.read_text())
    policy["topics"][0]["anchor"] = "upgrade-guidehttpsexamplecom"
    policy_path.write_text(json.dumps(policy))
    (consumer / "public/Accounts.md").write_text(
        "## Upgrade [guide](https://example.com)\n"
    )
    captured = impact.capture_publication_basis(consumer, target_dir="public")
    assert captured["targets"]["accounts"]["state"] == "unresolved-anchor"
    assert not impact.compare_publication_impact(captured)["complete"]


@pytest.mark.parametrize("preamble", [False, True])
def test_real_native_section_and_preamble_dependencies(consumer, preamble):
    if preamble:
        from dataclasses import replace
        from tests.knowledge_fixtures import one_module_two_entities_fixture
        from tests.test_knowledge_loader import _write_fixture_pages
        from tests.test_knowledge_generation import _planner_inputs
        from llm_wiki_cli.services.knowledge_generation import (
            build_knowledge_generation_plan,
        )
        from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts

        fixture = one_module_two_entities_fixture()
        fixture = replace(
            fixture,
            pages=tuple(
                replace(p, content="Preface.\n\n" + p.content)
                if p.page_kind == "modules"
                else p
                for p in fixture.pages
            ),
        )
        native_root = consumer / "prefix-wiki"
        _write_fixture_pages(native_root, fixture)
        commit_knowledge_artifacts(
            build_knowledge_generation_plan(_planner_inputs(native_root, fixture))
        )
        policy_path = consumer / ".llm-wiki/publication.json"
        policy = json.loads(policy_path.read_text())
        policy["architecture"]["root"] = "prefix-wiki"
        policy_path.write_text(json.dumps(policy))
    else:
        native_root = consumer / "wiki"
    snapshot = impact.build_publication_snapshot(native_root)
    if preamble:
        page = next(page for page in snapshot["pages"] if page.get("preamble"))
        section = page["preamble"]
        facets = ["whole"]
    else:
        page, section = next(
            (p, s)
            for p in snapshot["pages"]
            for s in p["sections"]
            if s.get("semantic_hash")
        )
        facets = ["semantic"]
    policy_path = consumer / ".llm-wiki/publication.json"
    policy = json.loads(policy_path.read_text())
    policy["topics"][0]["depends_on"] = [
        {
            "architecture_page": page["canonical_path"],
            "section": section["locator"],
            "facets": facets,
        }
    ]
    policy_path.write_text(json.dumps(policy))
    captured = impact.capture_publication_basis(consumer, target_dir="public")
    assert impact.compare_publication_impact(captured)["complete"]
