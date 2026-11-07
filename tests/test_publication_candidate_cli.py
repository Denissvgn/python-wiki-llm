"""Candidate CLI review binds metadata and bytes without modifying inputs."""

from __future__ import annotations

import json

import pytest

from llm_wiki_cli import api, cli


@pytest.fixture
def candidate_consumer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "project").mkdir()
    (tmp_path / "project/app.py").write_text(
        "def account():\n    return 'member'\n", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/Home.md").write_text(
        "# Accounts\n\nSee [[Manual]].\n", encoding="utf-8"
    )
    (tmp_path / "docs/_Sidebar.md").write_text(
        "[Accounts](Home.md)\n", encoding="utf-8"
    )
    (tmp_path / "public").mkdir()
    (tmp_path / "public/Manual.md").write_text(
        "# Manual\n\nHandwritten guidance.\n", encoding="utf-8"
    )
    (tmp_path / ".llm-wiki").mkdir()
    policy = {
        "schema_version": "llm-wiki-publication/v1",
        "architecture": {"baseline": "bootstrap-source", "root": "project"},
        "target": {"kind": "github-wiki", "repository": "self"},
        "enforcement": "advisory",
        "publish": False,
        "content": {"root": "docs"},
        "topics": [
            {
                "id": "home",
                "owner": "maintainers",
                "wiki_page": "Home.md",
                "edit_at": "repository",
                "source_document": "docs/Home.md",
                "depends_on": [{"source_file": "project/app.py"}],
            },
            {
                "id": "navigation",
                "owner": "maintainers",
                "wiki_page": "_Sidebar.md",
                "edit_at": "repository",
                "source_document": "docs/_Sidebar.md",
                "depends_on": [{"source_file": "docs/Home.md"}],
            },
        ],
        "exclusions": [
            {"pattern": "*", "reason": "Only the mapped public overview is in scope"}
        ],
    }
    (tmp_path / ".llm-wiki/publication.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    return tmp_path


def invoke(monkeypatch, *arguments):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "docs", "wiki", *arguments])
    try:
        cli.main()
    except SystemExit as exc:
        return exc.code
    return 0


@pytest.mark.parametrize(
    "receipt",
    [
        "reports/candidate/receipt.json",
        "docs/receipt.json",
        "package.json",
        ".git/receipt.json",
        ".llm-wiki/publication.json",
    ],
)
def test_candidate_metadata_guard_runs_before_tree_creation(
    candidate_consumer, monkeypatch, receipt
):
    from llm_wiki_cli.services import publication_candidate

    monkeypatch.setattr(
        publication_candidate,
        "export_publication_candidate",
        lambda *_args, **_kwargs: pytest.fail(
            "Output guard must precede candidate mutation"
        ),
    )
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "reports/candidate",
            "--receipt",
            receipt,
        )
        == 2
    )
    assert not (candidate_consumer / "reports/candidate").exists()
    assert (
        json.loads((candidate_consumer / ".llm-wiki/publication.json").read_text())[
            "publish"
        ]
        is False
    )


@pytest.mark.parametrize("malformed", [{"files": [123]}, {"references": []}])
def test_malformed_baseline_fails_before_candidate_mutation(
    candidate_consumer, monkeypatch, malformed
):
    from llm_wiki_cli.services import publication_candidate

    path = candidate_consumer / "accepted.json"
    path.write_text(json.dumps(malformed), encoding="utf-8")
    original = path.read_bytes()
    monkeypatch.setattr(
        publication_candidate,
        "export_publication_candidate",
        lambda *_args, **_kwargs: pytest.fail(
            "Malformed basis must fail before mutation"
        ),
    )
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--baseline",
            "accepted.json",
            "--output-dir",
            "reports/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 2
    )
    assert path.read_bytes() == original
    assert not (candidate_consumer / "reports/candidate").exists()
    assert not (candidate_consumer / "reports/receipt.json").exists()


def test_candidate_cli_requires_exact_topic_and_artifact_review(
    candidate_consumer, monkeypatch, capsys
):
    manual = (candidate_consumer / "public/Manual.md").read_bytes()
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "reports/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 0
    )
    receipt = json.loads((candidate_consumer / "reports/receipt.json").read_text())
    assert (
        receipt["checks"]["ok"]
        and not receipt["ready"]
        and not receipt["delivery_ready"]
    )
    assert (candidate_consumer / "reports/candidate/Manual.md").read_bytes() == manual
    assert (candidate_consumer / "public/Manual.md").read_bytes() == manual
    assert (
        invoke(
            monkeypatch,
            "check",
            "--target-dir",
            "public",
            "--candidate-dir",
            "reports/candidate",
            "--receipt",
            "reports/receipt.json",
            "--require-ready",
        )
        == 1
    )
    assert (
        invoke(
            monkeypatch,
            "review",
            "--candidate-dir",
            "reports/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed the exact candidate",
            "--output",
            "reports/candidate/approval.json",
        )
        == 2
    )
    assert not (candidate_consumer / "reports/candidate/approval.json").exists()
    assert (
        invoke(
            monkeypatch,
            "review",
            "--candidate-dir",
            "reports/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed the exact candidate",
            "--output",
            "reports/approval.json",
        )
        == 0
    )
    ledger = None
    for finding in receipt["impact"]["findings"]:
        if finding["kind"] == "topic":
            ledger = api.resolve_publication_finding(
                receipt["impact"],
                receipt["basis"],
                finding_id=finding["id"],
                reviewer="alice",
                reason="The proposed topic matches the source",
                reviews=ledger,
            )
    (candidate_consumer / "reports/topics.json").write_text(
        json.dumps(ledger), encoding="utf-8"
    )
    assert (
        invoke(
            monkeypatch,
            "check",
            "--target-dir",
            "public",
            "--candidate-dir",
            "reports/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviews",
            "reports/topics.json",
            "--candidate-review",
            "reports/approval.json",
            "--output",
            "reports/checked.json",
            "--require-ready",
        )
        == 0
    )
    checked = json.loads((candidate_consumer / "reports/checked.json").read_text())
    assert checked["candidate_id"] == receipt["candidate_id"]
    assert checked["ready"] and not checked["delivery_ready"]
    assert checked["target"]["remote_verified"] is False
    (candidate_consumer / "reports/candidate/Home.md").write_text(
        "# Changed\n", encoding="utf-8"
    )
    assert (
        invoke(
            monkeypatch,
            "check",
            "--target-dir",
            "public",
            "--candidate-dir",
            "reports/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 2
    )
    assert (candidate_consumer / "public/Manual.md").read_bytes() == manual
    capsys.readouterr()
