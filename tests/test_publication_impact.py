"""End-to-end publication impact, exact review bases and CLI boundaries."""

from copy import deepcopy
import json

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.knowledge_evidence import hash_json
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
