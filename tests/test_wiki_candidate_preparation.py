"""The candidate action selects runtimes and checks existing native evidence."""

import json
from pathlib import Path
import runpy
import shutil

import pytest

from tests.test_publication_candidate import configure
from tests.test_publication_impact import consumer as consumer


ROOT = Path(__file__).resolve().parents[1]
prepare = runpy.run_path(str(ROOT / "integrations/wiki-candidate/prepare.py"))[
    "prepare"
]
CONFIG = ".llm-wiki/publication.json"


def test_python_bootstrap_needs_no_external_toolchain(tmp_path, monkeypatch):
    source = tmp_path / "consumer"
    shutil.copytree(
        ROOT / "examples/sibling-wiki", source, ignore=shutil.ignore_patterns("reports")
    )
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    cache = tmp_path / "helpers"
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: pytest.fail("Unexpected toolchain invocation"),
    )
    prepare("toolchains", source, CONFIG, ".", evidence, cache)
    prepare("check", source, CONFIG, ".", evidence, cache)
    assert json.loads((evidence / "helper-plan.json").read_bytes())["languages"] == []
    assert json.loads((evidence / "helpers.json").read_bytes()) == {}
    assert not (evidence / "native-integrity.json").exists()


def test_plan_installs_only_the_selected_locked_toolchain(tmp_path, monkeypatch):
    source = tmp_path / "consumer"
    shutil.copytree(
        ROOT / "examples/sibling-wiki", source, ignore=shutil.ignore_patterns("reports")
    )
    (source / "project/app.ts").write_text(
        "export const answer = 42;\n", encoding="utf-8"
    )
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    calls = []
    original = prepare.__globals__["subprocess"].run

    def capture(args, **kwargs):
        if args[0].endswith("setup-llm-wiki-ci-toolchains.sh"):
            calls.append(args)
            return
        return original(args, **kwargs)

    monkeypatch.setattr("subprocess.run", capture)
    prepare("toolchains", source, CONFIG, ".", evidence, tmp_path / "helpers")
    assert json.loads((evidence / "helper-plan.json").read_bytes())["languages"] == [
        "typescript"
    ]
    assert [command[command.index("--mode") + 1] for command in calls] == ["routine"]
    (source / "project/app.ts").unlink()
    with pytest.raises(ValueError, match="selection changed"):
        prepare("check", source, CONFIG, ".", evidence, tmp_path / "helpers")


def test_existing_wiki_requires_current_sources_before_export(consumer, tmp_path):
    configure(consumer)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    cache = tmp_path / "helpers"
    prepare("toolchains", consumer, CONFIG, "src", evidence, cache)
    prepare("check", consumer, CONFIG, "src", evidence, cache)
    assert json.loads((evidence / "native-integrity.json").read_bytes())["ok"]
    assert json.loads((evidence / "native-freshness.json").read_bytes())["current"]
    (consumer / "src/accounts.py").write_text(
        "class Renamed:\n    pass\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="(?i)native wiki"):
        prepare("check", consumer, CONFIG, "src", evidence, cache)
