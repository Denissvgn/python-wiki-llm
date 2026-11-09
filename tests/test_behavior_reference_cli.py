"""Exercise behavior references through the public CLI and Python boundaries."""

from importlib import metadata
import json
import sys
from types import MappingProxyType

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import behavior_reference
from llm_wiki_cli.services.knowledge_evidence import hash_json


def invoke(monkeypatch, *options):
    monkeypatch.setattr(
        sys, "argv", ["llm-wiki", "reference", "behavior", *map(str, options)]
    )
    cli.main()


def test_installed_facts_from_foreign_project(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    package = metadata.distribution("agent-wiki-cli")
    # A consumer can even have the same project name or local skill names.
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname="agent-wiki-cli"\nversion="{package.version}"\nrequires-python="==0.0"\n',
        encoding="utf-8",
    )
    foreign_skill = tmp_path / ".llm-wiki/skills/consumer-only/SKILL.md"
    foreign_skill.parent.mkdir(parents=True)
    foreign_skill.write_text("# Consumer only\n", encoding="utf-8")
    before = set(tmp_path.rglob("*"))

    invoke(monkeypatch)
    observed = json.loads(capsys.readouterr().out)
    assert observed == api.get_behavior_facts()
    assert observed["facts"]["package"] == {
        "name": package.metadata["Name"],
        "version": package.version,
        "requires_python": package.metadata["Requires-Python"],
    }
    assert "consumer-only" not in {s["id"] for s in observed["facts"]["skills"]}
    assert str(tmp_path) not in json.dumps(observed)
    api.validate_behavior_facts(MappingProxyType(observed))
    invoke(monkeypatch, "--format", "markdown")
    assert capsys.readouterr().out == api.render_behavior_reference(
        MappingProxyType(observed)
    )
    assert set(tmp_path.rglob("*")) == before


def test_saved_reference_uses_reviewed_data_and_preserves_input(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "reference data" / "facts.json"
    invoke(monkeypatch, "--output", source)
    assert not capsys.readouterr().out
    saved = json.loads(source.read_bytes())
    saved["facts"]["package"]["version"] = "1.2.3"
    saved["contract_id"] = hash_json(
        {key: value for key, value in saved.items() if key != "contract_id"}
    )
    source.write_text(json.dumps(saved, ensure_ascii=False), encoding="utf-8")
    original = source.read_bytes()
    monkeypatch.setattr(
        behavior_reference,
        "get_behavior_facts",
        lambda: pytest.fail("Unexpected live export"),
    )
    rendered = tmp_path / "reference data" / "facts.md"
    invoke(monkeypatch, "--input", source, "--format", "markdown", "--output", rendered)
    assert rendered.read_bytes() == api.render_behavior_reference(saved).encode("utf-8")
    assert "1.2.3" in rendered.read_text(encoding="utf-8")
    invoke(monkeypatch, "--input", source)
    assert json.loads(capsys.readouterr().out) == saved
    with pytest.raises(SystemExit) as same:
        invoke(monkeypatch, "--input", source, "--output", source)
    assert same.value.code == 2 and source.read_bytes() == original


def test_invalid_saved_facts_do_not_overwrite_output(tmp_path, monkeypatch):
    original = api.get_behavior_facts()
    original["facts"]["package"]["requires_python"] = ">=9"
    source = tmp_path / "stale.json"
    source.write_text(json.dumps(original), encoding="utf-8")
    destination = tmp_path / "reviewed.md"
    destination.write_bytes(b"Keep the reviewed document.\n")
    with pytest.raises(SystemExit) as failure:
        invoke(
            monkeypatch,
            "--input",
            source,
            "--format",
            "markdown",
            "--output",
            destination,
        )
    assert failure.value.code == 2
    assert destination.read_bytes() == b"Keep the reviewed document.\n"
    with pytest.raises(api.InvalidRequestError):
        api.validate_behavior_facts(original)


def test_json_at_exact_byte_limit_can_be_loaded_again(tmp_path, monkeypatch):
    facts = api.get_behavior_facts()
    compact = json.dumps(
        facts, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    monkeypatch.setattr(behavior_reference, "MAX_BEHAVIOR_FACTS_BYTES", len(compact))
    path = tmp_path / "facts.json"
    invoke(monkeypatch, "--output", path)
    assert path.read_bytes() == compact
    assert behavior_reference.load_behavior_facts(path) == facts
