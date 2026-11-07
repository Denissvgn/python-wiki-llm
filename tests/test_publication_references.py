"""Reference inputs participate in exact, scoped publication review."""

import argparse
from copy import deepcopy
import json

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.cli_reference import (
    build_cli_contract,
    get_cli_contract,
    render_cli_reference,
)
from llm_wiki_cli.services import publication_impact as impact
from tests.test_publication_impact import consumer as consumer


def app_contract(
    *,
    name="guest",
    other_help="Remove an account",
    version="1.0.0",
    endpoint="production",
):
    parser = argparse.ArgumentParser(prog="accounts")
    parser.add_argument("--endpoint", default=endpoint)
    commands = parser.add_subparsers(dest="action", required=True)
    create = commands.add_parser("create", aliases=["add"], help="Create an account")
    create.add_argument("--name", default=name)
    commands.add_parser("remove", help=other_help)
    return build_cli_contract(
        parser,
        program="accounts",
        package={
            "name": "accounts-example",
            "version": version,
            "requires_python": ">=3.11",
        },
    )


def configure(root, *, command=None, path="app-reference.json", builtin=False):
    target = root / ".llm-wiki/publication.json"
    policy = json.loads(target.read_text())
    policy["reference_providers"] = {
        "app": {"kind": "llm-wiki-cli"}
        if builtin
        else {"kind": "contract-file", "path": path}
    }
    policy["topics"][0]["depends_on"] = [
        {"reference": "app", "command": ["create"] if command is None else command}
    ]
    target.write_text(json.dumps(policy))
    return policy


def capture(root, baseline=None):
    return impact.capture_publication_basis(
        root, target_dir="public", baseline=baseline
    )


def test_changed_default_reopens_a_scoped_review(consumer):
    configure(consumer)
    path = consumer / "app-reference.json"
    path.write_text(json.dumps(app_contract()))
    before = capture(consumer)
    path.write_text(json.dumps(app_contract(name="visitor")))
    after = capture(consumer, before)
    report = impact.compare_publication_impact(after, before)
    finding = report["findings"][0]
    assert finding["status"] == "needs-review"
    ledger = impact.resolve_publication_finding(
        report,
        after,
        finding_id=finding["id"],
        reviewer="alice",
        reason="The overview has no fixed default-name claim",
    )
    assert impact.compare_publication_impact(after, before, reviews=ledger)["ready"]
    path.write_text(json.dumps(app_contract(name="customer")))
    changed = capture(consumer, before)
    assert impact.compare_publication_impact(changed, before, reviews=ledger)[
        "review_required"
    ]


@pytest.mark.parametrize("command", [["create"], ["add"], []])
def test_scope_excludes_unrelated_command_and_version_noise(consumer, command):
    configure(consumer, command=command)
    path = consumer / "app-reference.json"
    path.write_text(json.dumps(app_contract()))
    before = capture(consumer)
    path.write_text(
        json.dumps(app_contract(other_help="Delete a saved account", version="1.1.0"))
    )
    after = capture(consumer, before)
    report = impact.compare_publication_impact(after, before)
    assert report["changed"]
    assert report["review_required"] == (not command)


def test_changed_ancestor_default_reopens_descendant_review(consumer):
    configure(consumer)
    path = consumer / "app-reference.json"
    path.write_text(json.dumps(app_contract()))
    before = capture(consumer)
    path.write_text(json.dumps(app_contract(endpoint="staging")))
    report = impact.compare_publication_impact(capture(consumer, before), before)
    assert report["complete"] and report["review_required"]


@pytest.mark.parametrize(
    "problem", ["missing-file", "missing-command", "malformed", "duplicate-key"]
)
def test_unavailable_or_invalid_reference_never_clears_review(consumer, problem):
    configure(
        consumer, command=["unknown"] if problem == "missing-command" else ["create"]
    )
    path = consumer / "app-reference.json"
    if problem == "malformed":
        path.write_text('{"schema_version":"future"}')
    elif problem == "duplicate-key":
        path.write_text('{"schema_version":"bad","schema_version":"bad"}')
    elif problem != "missing-file":
        path.write_text(json.dumps(app_contract()))
    if problem in {"malformed", "duplicate-key"}:
        with pytest.raises(ValueError):
            capture(consumer)
    else:
        report = impact.compare_publication_impact(capture(consumer))
        assert not report["complete"] and not report["ready"]


def test_reference_file_is_rechecked_after_native_capture(consumer, monkeypatch):
    configure(consumer)
    path = consumer / "app-reference.json"
    path.write_text(json.dumps(app_contract()))
    original = impact.build_publication_snapshot
    calls = 0

    def mutate(root):
        nonlocal calls
        result = original(root)
        calls += 1
        if calls == 2:
            path.write_text(json.dumps(app_contract(name="late edit")))
        return result

    monkeypatch.setattr(impact, "build_publication_snapshot", mutate)
    with pytest.raises(ValueError):
        capture(consumer)


def test_rebound_provider_keeps_former_contract_live_for_retirement(consumer):
    configure(consumer)
    old = consumer / "app-reference.json"
    old.write_text(json.dumps(app_contract()))
    before = capture(consumer)
    new = consumer / "replacement-reference.json"
    new.write_text(json.dumps(app_contract(version="2.0.0")))
    policy = configure(consumer, path="replacement-reference.json")
    policy["topics"] = []
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    after = capture(consumer, before)
    assert len(after["references"]) == 2
    report = impact.compare_publication_impact(after, before)
    finding = report["findings"][0]
    ledger = impact.resolve_publication_finding(
        report,
        after,
        finding_id=finding["id"],
        reviewer="alice",
        reason="Retiring the old published topic",
        decision="retired",
    )
    assert impact.compare_publication_impact(after, before, reviews=ledger)["ready"]
    old.write_text(json.dumps(app_contract(name="changed former input")))
    assert impact.compare_publication_impact(
        capture(consumer, before), before, reviews=ledger
    )["review_required"]


def test_builtin_provider_is_explicit_and_legacy_capture_is_unchanged(
    consumer, monkeypatch
):
    from llm_wiki_cli.services import cli_reference

    original = get_cli_contract()
    monkeypatch.setattr(
        cli_reference,
        "get_cli_contract",
        lambda: pytest.fail("Legacy project exported installed CLI"),
    )
    assert "references" not in capture(consumer)
    monkeypatch.setattr(cli_reference, "get_cli_contract", lambda: deepcopy(original))
    configure(consumer, command=["sync"], builtin=True)
    candidate = capture(consumer)
    assert (
        next(iter(candidate["references"].values()))["contract"]["program"]
        == "llm-wiki"
    )
    assert impact.compare_publication_impact(candidate)["complete"]


def test_reference_cli_and_saved_renderer_use_the_same_contract(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv", ["arbitrary-entrypoint", "reference", "cli", "--output", "cli.json"]
    )
    cli.main()
    saved = json.loads((tmp_path / "cli.json").read_text())
    assert saved["program"] == "llm-wiki"
    monkeypatch.setattr(
        "sys.argv",
        ["entry", "reference", "render", "--input", "cli.json", "--format", "markdown"],
    )
    cli.main()
    assert capsys.readouterr().out == render_cli_reference(saved)
    monkeypatch.setattr(
        "sys.argv",
        ["entry", "reference", "render", "--input", "cli.json", "--output", "cli.json"],
    )
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert json.loads((tmp_path / "cli.json").read_text()) == saved
