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
    validate_cli_contract,
)
from llm_wiki_cli.services.knowledge_evidence import hash_json
from llm_wiki_cli.services import publication_impact as impact
from tests.test_publication_impact import consumer as consumer


def app_contract(
    *,
    name="guest",
    other_help="Remove an account",
    version="1.0.0",
    endpoint="production",
    parser_options=None,
    version_option=False,
):
    parser = argparse.ArgumentParser(prog="accounts", **(parser_options or {}))
    if version_option:
        parser.add_argument_group("Release display").add_argument(
            "--version", action="version", version=version
        )
    parser.add_argument_group("Network").add_argument("--endpoint", default=endpoint)
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
    "parser_options",
    [
        {"allow_abbrev": False},
        {"fromfile_prefix_chars": "@"},
        {"prefix_chars": "-+"},
    ],
)
def test_changed_ancestor_parsing_policy_reopens_descendant_review(
    consumer, parser_options
):
    configure(consumer)
    path = consumer / "app-reference.json"
    path.write_text(json.dumps(app_contract()))
    before = capture(consumer)
    path.write_text(json.dumps(app_contract(parser_options=parser_options)))
    report = impact.compare_publication_impact(capture(consumer, before), before)
    assert report["complete"] and report["review_required"]


@pytest.mark.parametrize("command", [["create"], ["add"]])
def test_valid_external_ungrouped_ancestor_argument_remains_reviewable(
    consumer, command
):
    configure(consumer, command=command)
    path = consumer / "app-reference.json"

    def saved_contract(endpoint):
        contract = app_contract(endpoint=endpoint)
        argument = next(
            item for item in contract["root"]["arguments"] if item["dest"] == "endpoint"
        )
        group = next(
            item
            for item in contract["root"]["groups"]
            if item["id"] == argument["group"]
        )
        group["members"].remove(argument["id"])
        argument["group"] = None
        contract["contract_id"] = hash_json(
            {key: value for key, value in contract.items() if key != "contract_id"}
        )
        validate_cli_contract(contract)
        return contract

    path.write_text(json.dumps(saved_contract("production")))
    before = capture(consumer)
    unchanged = impact.compare_publication_impact(capture(consumer, before), before)
    assert unchanged["complete"] and not unchanged["review_required"]
    path.write_text(json.dumps(saved_contract("staging")))
    report = impact.compare_publication_impact(capture(consumer, before), before)
    assert report["complete"] and report["review_required"]


@pytest.mark.parametrize("command", [["create"], ["add"]])
def test_ancestor_subcommand_boundary_reopens_positional_syntax_review(
    consumer, command
):
    configure(consumer, command=command)
    path = consumer / "app-reference.json"

    def parser(after):
        value = argparse.ArgumentParser(prog="accounts")
        if not after:
            value.add_argument("context", nargs="?", default="default")
        commands = value.add_subparsers(dest="action")
        commands.add_parser("create", aliases=["add"])
        if after:
            value.add_argument("context", nargs="?", default="default")
        return value

    original, changed = parser(False), parser(True)
    assert original.parse_args(["user", *command]).context == "user"
    with pytest.raises(SystemExit):
        changed.parse_args(["user", *command])

    def write_contract(value):
        contract = build_cli_contract(
            value,
            package={"name": "accounts", "version": "1", "requires_python": None},
            program="accounts",
        )
        path.write_text(json.dumps(contract))

    write_contract(original)
    before = capture(consumer)
    write_contract(changed)
    report = impact.compare_publication_impact(capture(consumer, before), before)
    assert report["complete"] and report["review_required"]


def test_ancestor_subparser_namespace_change_reopens_descendant_review(consumer):
    configure(consumer)
    path = consumer / "app-reference.json"
    original = app_contract()
    path.write_text(json.dumps(original))
    before = capture(consumer)
    changed = deepcopy(original)
    selector = next(
        item for item in changed["root"]["arguments"] if item["action"] == "subparsers"
    )
    selector["dest"] = "operation"
    changed["contract_id"] = hash_json(
        {key: value for key, value in changed.items() if key != "contract_id"}
    )
    validate_cli_contract(changed)
    path.write_text(json.dumps(changed))
    report = impact.compare_publication_impact(capture(consumer, before), before)
    assert report["complete"] and report["review_required"]


@pytest.mark.parametrize("command", [["create"], ["add"], []])
def test_added_ancestor_display_action_does_not_shift_scoped_review(consumer, command):
    configure(consumer, command=command)
    path = consumer / "app-reference.json"
    path.write_text(json.dumps(app_contract()))
    before = capture(consumer)
    path.write_text(json.dumps(app_contract(version_option=True)))
    report = impact.compare_publication_impact(capture(consumer, before), before)
    assert report["complete"] and report["changed"]
    assert report["review_required"] == (not command)


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


def test_reference_capture_budget_counts_utf8_without_ascii_expansion(
    consumer, monkeypatch
):
    from llm_wiki_cli.services import publication_references

    value = app_contract(name="é" * 512)
    policy = configure(consumer)
    policy["reference_providers"]["another"] = {
        "kind": "contract-file",
        "path": "app-reference.json",
    }
    (consumer / ".llm-wiki/publication.json").write_text(json.dumps(policy))
    (consumer / "app-reference.json").write_text(
        json.dumps(value, ensure_ascii=False), encoding="utf-8"
    )
    budget = 2 * len(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    )
    monkeypatch.setattr(publication_references, "MAX_CAPTURE_BYTES", budget)
    assert len(capture(consumer)["references"]) == 2


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
