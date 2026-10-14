"""CLI adoption hints must identify captured flat models without mutation."""

import json
from pathlib import Path
import sys

import pytest

from llm_wiki_cli import api, cli


@pytest.mark.parametrize("root_state", ["flat", "future", "broken-json", "broken-flat"])
def test_native_cli_adoption_hint_only_for_valid_captured_flat_model(
    tmp_path, monkeypatch, capsys, root_state
):
    monkeypatch.chdir(tmp_path)
    source = Path("src")
    source.mkdir()
    (source / "app.py").write_text("def limit(value: int = 3) -> int:\n    return value\n")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    root = Path("wiki/.llm-wiki-knowledge.json")
    payload = json.loads(root.read_text())
    if root_state == "future":
        payload["schema_version"] = "llm-wiki-knowledge/v999"
        root.write_text(json.dumps(payload))
    elif root_state == "broken-json":
        root.write_text("{broken")
    elif root_state == "broken-flat":
        root.write_text(json.dumps({"schema_version": payload["schema_version"]}))
    request = {
        "schema_version": "llm-wiki-task-request/v2",
        "requirements": [{"id": "native", "facet": "concept", "selector": "llm-wiki://modules/app"}],
        "options": {"knowledge_mode": "required", "read_scope": "snapshot"},
    }
    Path("request.json").write_text(json.dumps(request))
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "task-context", "--request", "request.json",
                                     "--src-dir", "src", "--wiki-dir", "wiki"])
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    error = json.loads(output.err)["error"]
    assert error["code"] == "invalid-request"
    if root_state == "flat":
        assert error["details"]["reason"] == "flat-native-adoption-required"
        hint = error["details"]["next_action"]
        assert "With storage migration authorized" in hint
        assert "--dry-run" in hint and "outside source/wiki" in hint
        assert "Keep native requirements" in hint and "complete snapshot" in hint
    else:
        assert "next_action" not in error["details"]
    assert str(tmp_path) not in output.err
    assert before == {p.relative_to(tmp_path).as_posix(): p.read_bytes()
                      for p in tmp_path.rglob("*") if p.is_file()}
