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
        ".llm-wiki/source-selection.json",
        ".llm-wiki/source-selection.json/receipt.json",
        "project/.llm-wiki/source-selection.json",
        "project/.llm-wiki/source-selection.json/receipt.json",
        "project/.LLM-WIKI/SOURCE-SELECTION.JSON",
        ".gitignore/receipt.json",
        "project/.gitignore/receipt.json",
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


def test_receipt_cannot_create_a_missing_bootstrap_selection_file(
    candidate_consumer, monkeypatch
):
    selection = candidate_consumer / "project/.llm-wiki/source-selection.json"
    assert not selection.exists()
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "project/.llm-wiki/source-selection.json",
        )
        == 2
    )
    assert not selection.exists()
    assert not selection.parent.exists()
    assert not (candidate_consumer / "out/candidate").exists()


@pytest.mark.parametrize("kind", ["reference", "source_file"])
def test_missing_input_case_alias_cannot_become_receipt(
    candidate_consumer, monkeypatch, kind
):
    from llm_wiki_cli.services import publication_candidate

    path = candidate_consumer / ".llm-wiki/publication.json"
    policy = json.loads(path.read_text())
    if kind == "reference":
        policy["reference_providers"] = {
            "app": {"kind": "contract-file", "path": "data.json"}
        }
    else:
        policy["topics"][0]["depends_on"].append({"source_file": "data.json"})
    path.write_text(json.dumps(policy))
    monkeypatch.setattr(
        publication_candidate,
        "export_publication_candidate",
        lambda *_args, **_kwargs: pytest.fail("Input guard must precede mutation"),
    )
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "DATA.json",
        )
        == 2
    )
    assert not (candidate_consumer / "DATA.json").exists()
    assert not (candidate_consumer / "out/candidate").exists()


@pytest.mark.parametrize("action", ["check", "review"])
@pytest.mark.parametrize(
    "output",
    ["project/.llm-wiki/source-selection.json", "project/.gitignore/proposal.json"],
)
def test_check_and_review_metadata_reserve_absent_source_controls(
    candidate_consumer, monkeypatch, action, output
):
    from llm_wiki_cli.services import publication_candidate

    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 0
    )
    before = {
        path.relative_to(
            candidate_consumer / "out/candidate"
        ).as_posix(): path.read_bytes()
        for path in (candidate_consumer / "out/candidate").rglob("*")
        if path.is_file()
    }
    if action == "check":
        monkeypatch.setattr(
            publication_candidate,
            "check_publication_candidate",
            lambda *_args, **_kwargs: pytest.fail(
                "Control guard must precede checking"
            ),
        )
        extra = ["--target-dir", "public"]
    else:
        monkeypatch.setattr(
            publication_candidate,
            "review_publication_candidate",
            lambda *_args, **_kwargs: pytest.fail("Control guard must precede review"),
        )
        extra = [
            "--target-dir",
            "public",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed",
        ]
    assert (
        invoke(
            monkeypatch,
            action,
            "--candidate-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
            "--output",
            output,
            *extra,
        )
        == 2
    )
    assert not (candidate_consumer / output).exists()
    assert not (candidate_consumer / "project/.llm-wiki").exists()
    assert not (candidate_consumer / "project/.gitignore").exists()
    assert {
        path.relative_to(
            candidate_consumer / "out/candidate"
        ).as_posix(): path.read_bytes()
        for path in (candidate_consumer / "out/candidate").rglob("*")
        if path.is_file()
    } == before


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


@pytest.mark.parametrize("case", ["target-output", "stale-target", "missing-target"])
def test_review_protects_and_rechecks_its_original_target(
    candidate_consumer, monkeypatch, case
):
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 0
    )
    target = candidate_consumer / "public/Manual.md"
    original = target.read_bytes()
    if case == "stale-target":
        target.write_bytes(original + b"Changed target.\n")
    output = (
        "public/proposal.json" if case == "target-output" else "reports/proposal.json"
    )
    extra = [] if case == "missing-target" else ["--target-dir", "public"]
    assert (
        invoke(
            monkeypatch,
            "review",
            "--candidate-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed",
            "--output",
            output,
            *extra,
        )
        == 2
    )
    assert not (candidate_consumer / output).exists()
    assert target.read_bytes() == (
        original + b"Changed target.\n" if case == "stale-target" else original
    )


@pytest.mark.parametrize("change", ["architecture", "dependency"])
def test_review_reserves_current_config_inputs_beside_saved_receipt(
    candidate_consumer, monkeypatch, change
):
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 0
    )
    path = candidate_consumer / ".llm-wiki/publication.json"
    policy = json.loads(path.read_text())
    if change == "architecture":
        policy["architecture"]["root"] = "other-project"
        (candidate_consumer / "other-project").mkdir()
        output = "other-project/.llm-wiki/source-selection.json"
    else:
        policy["topics"][0]["depends_on"].append({"source_file": "new-input.json"})
        output = "new-input.json"
    path.write_text(json.dumps(policy))
    assert (
        invoke(
            monkeypatch,
            "review",
            "--target-dir",
            "public",
            "--candidate-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed",
            "--output",
            output,
        )
        == 2
    )
    assert not (candidate_consumer / output).exists()


def test_artifact_only_review_does_not_require_a_local_target(
    candidate_consumer, monkeypatch
):
    (candidate_consumer / "docs/Home.md").write_text(
        "# Home\n\nPublic overview.\n", encoding="utf-8"
    )
    assert (
        invoke(
            monkeypatch,
            "export",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 0
    )
    assert (
        invoke(
            monkeypatch,
            "review",
            "--candidate-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed",
            "--output",
            "reports/proposal.json",
        )
        == 0
    )
    assert (candidate_consumer / "reports/proposal.json").is_file()


def test_review_rejects_control_directory_as_target_before_target_read(
    candidate_consumer, monkeypatch
):
    from llm_wiki_cli.services import publication_candidate

    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            "public",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 0
    )
    monkeypatch.setattr(
        publication_candidate,
        "validate_candidate_target",
        lambda *_args, **_kwargs: pytest.fail(
            "Control directory must not be read as target"
        ),
    )
    assert (
        invoke(
            monkeypatch,
            "review",
            "--target-dir",
            ".llm-wiki",
            "--candidate-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed",
            "--output",
            "reports/proposal.json",
        )
        == 2
    )
    assert not (candidate_consumer / "reports/proposal.json").exists()


def test_curated_target_inside_control_parent_remains_supported(
    candidate_consumer, monkeypatch
):
    nested = candidate_consumer / ".llm-wiki/targets/public"
    nested.mkdir(parents=True)
    (nested / "Manual.md").write_bytes(
        (candidate_consumer / "public/Manual.md").read_bytes()
    )
    assert (
        invoke(
            monkeypatch,
            "export",
            "--target-dir",
            ".llm-wiki/targets/public",
            "--output-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
        )
        == 0
    )
    assert (
        invoke(
            monkeypatch,
            "review",
            "--target-dir",
            ".llm-wiki/targets/public",
            "--candidate-dir",
            "out/candidate",
            "--receipt",
            "reports/receipt.json",
            "--reviewer",
            "alice",
            "--reason",
            "Reviewed",
            "--output",
            "reports/proposal.json",
        )
        == 0
    )


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
            "--target-dir",
            "public",
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
            "--target-dir",
            "public",
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
