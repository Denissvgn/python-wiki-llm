"""Publication patches bind the checked target, canonical bytes, and workspace review."""

from pathlib import Path
import subprocess

import pytest

from llm_wiki_cli.services import publication_maintenance as maintenance
from llm_wiki_cli.services.documentation_run import prepare_documentation_run
from llm_wiki_cli.services.documentation_run import publication as mapped
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.publication_candidate import export_publication_candidate
from tests.test_publication_candidate import accept_topics, configure
from tests.test_publication_impact import consumer as consumer


@pytest.fixture
def inputs(consumer, tmp_path_factory):
    configure(consumer, manual=True)
    candidate = consumer / "reports/candidate"
    receipt = export_publication_candidate(
        consumer, output_dir=candidate, target_dir="public"
    )
    workspace = tmp_path_factory.mktemp("semantic")
    prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=consumer / "wiki",
        source_root=consumer / "src",
        site_name="Public guide",
        project_purpose="Maintain accounts guidance.",
        audiences=["operator"],
        audience_intent={"operator": "Use the account API"},
    )
    return dict(
        consumer_root=consumer,
        workspace=workspace,
        candidate_dir=candidate,
        receipt=receipt,
        target_dir="public",
        topic_ids=["accounts"],
    )


def test_plan_scopes_authored_source_text_and_exact_evidence(inputs):
    pending = maintenance.prepare_publication_maintenance(**inputs)
    binding = pending["binding"]
    assert not pending["ready_for_repository_review"] and not pending["delivery_ready"]
    assert (
        pending["next_actions"]
        and binding["receipt_id"] == inputs["receipt"]["receipt_id"]
    )
    [topic] = binding["topics"]
    assert topic["id"] == "accounts" and topic["finding"]["review_basis"]
    source = inputs["consumer_root"] / topic["source_document"]
    copied = inputs["workspace"] / "mapped-docs" / topic["source_document"]
    assert copied.read_bytes() == source.read_bytes()
    assert topic["before_hash"] == sha256_bytes(source.read_bytes())
    assert not list((inputs["workspace"] / "mapped-docs").rglob("Notes.md"))
    assert maintenance.prepare_publication_maintenance(**inputs)["binding"] == binding


def test_empty_or_ineligible_selection_never_seeds_workspace(inputs):
    for keys in (["nonexistent"], ["notes"], [], ["accounts", "accounts"]):
        with pytest.raises(ValueError, match="topic"):
            maintenance.prepare_publication_maintenance(**{**inputs, "topic_ids": keys})
    ledger = accept_topics(inputs["receipt"])
    root = inputs["consumer_root"]
    output = root / "reports/reviewed"
    receipt = export_publication_candidate(
        root, output_dir=output, target_dir="public", reviews=ledger
    )
    result = maintenance.prepare_publication_maintenance(
        **{
            **inputs,
            "topic_ids": None,
            "receipt": receipt,
            "reviews": ledger,
            "candidate_dir": output,
        }
    )
    assert (
        result["status"] == "no-mapped-findings" and result["binding"]["topics"] == []
    )
    assert not (inputs["workspace"] / "mapped-docs").exists()


@pytest.mark.parametrize("change", ["canonical", "candidate", "target"])
def test_stale_input_fails_before_workspace_is_bound(inputs, change):
    doc = {
        "canonical": "docs/public/Accounts.md",
        "candidate": "reports/candidate/Accounts.md",
        "target": "public/Accounts.md",
    }[change]
    path = inputs["consumer_root"] / doc
    path.write_bytes(path.read_bytes() + b"\nOther change\n")
    with pytest.raises(ValueError):
        maintenance.prepare_publication_maintenance(**inputs)
    assert not (inputs["workspace"] / "mapped-docs").exists()


def test_a_different_adopted_wiki_cannot_supply_patch_evidence(
    inputs, tmp_path_factory
):
    other = tmp_path_factory.mktemp("other")
    (other / "app.py").write_text("class Other: pass\n", encoding="utf-8")
    workspace = tmp_path_factory.mktemp("other-wiki")
    prepare_documentation_run(
        workspace,
        source_root=other,
        site_name="Other",
        project_purpose="Different project",
        audiences=["operator"],
        audience_intent={"operator": "Read."},
    )
    with pytest.raises(ValueError, match="this consumer"):
        maintenance.prepare_publication_maintenance(
            **{**inputs, "workspace": workspace}
        )
    assert not (workspace / "mapped-docs").exists()


def test_newly_broken_target_from_reviewed_bytes_cannot_be_handed_off(
    inputs, monkeypatch
):
    pending = maintenance.prepare_publication_maintenance(**inputs)
    binding = pending["binding"]
    [topic] = binding["topics"]
    path = topic["source_document"]
    updated = {path: b"# Accounts\n\n[Missing](Does-Not-Exist)\n"}
    review = {
        "binding_id": binding["binding_id"],
        "mapped_files": {path: sha256_bytes(updated[path])},
    }
    monkeypatch.setattr(
        mapped,
        "collect_reviewed_publication_edits",
        lambda *_a, **_kw: (review, updated),
    )
    with pytest.raises(ValueError, match="Patched candidate failed"):
        maintenance.build_publication_patch(**inputs)
    assert (inputs["consumer_root"] / path).read_bytes() != updated[path]


def test_final_workspace_reread_detects_a_change_during_artifact_preparation(
    inputs, monkeypatch
):
    binding = maintenance.prepare_publication_maintenance(**inputs)["binding"]
    [topic] = binding["topics"]
    path = topic["source_document"]
    canonical = inputs["consumer_root"] / path
    original = canonical.read_bytes()
    edits = iter([original + b"\nBefore.\n", original + b"\nAfter.\n"])

    def reviewed(*_args, **_kwargs):
        raw = next(edits)
        return {
            "binding_id": binding["binding_id"],
            "mapped_files": {path: sha256_bytes(raw)},
        }, {path: raw}

    monkeypatch.setattr(mapped, "collect_reviewed_publication_edits", reviewed)
    with pytest.raises(ValueError, match="Reviewed workspace changed"):
        maintenance.build_publication_patch(**inputs)
    assert canonical.read_bytes() == original


@pytest.mark.parametrize(
    "original,updated",
    [
        (b"", b"one"),
        (b"last line", b""),
        ("one\r\ntwo\u2028three\nend".encode(), "one\r\ntwo\u2028four\nnew".encode()),
        (
            b"row\n" * 3000 + b"old\n" + b"tail\n" * 3000,
            b"row\n" * 3000 + b"NEW\n" + b"tail\n" * 3000,
        ),
        (b"line\n" * 5000, b"before\n" + b"line\n" * 5000),
        (b"A\n" * 5000 + b"X", b"A\n" * 5000 + b"X\n"),
        (b"", b"\n" * 20_001),
    ],
    ids=[
        "empty-before",
        "empty-after",
        "mixed-lines",
        "middle",
        "prepend",
        "final-lf",
        "many-lines",
    ],
)
def test_git_patch_preserves_reviewed_bytes_and_portable_filenames(
    tmp_path, original, updated
):
    path = Path("public") / "Résumé accounts.md"
    (tmp_path / path.parent).mkdir()
    destination = tmp_path / path
    destination.write_bytes(original)
    patch = maintenance._document_patch(path.as_posix(), original, updated).encode()
    subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=tmp_path,
        input=patch,
        check=True,
    )
    assert destination.read_bytes() == updated
    if b"NEW" in updated:
        assert len(patch) < 400


def test_review_binding_budget_is_actionable(inputs, monkeypatch):
    monkeypatch.setattr(maintenance, "_MAX_TOPICS", 1)
    with pytest.raises(ValueError, match="at most 1"):
        maintenance.prepare_publication_maintenance(**{**inputs, "topic_ids": None})
