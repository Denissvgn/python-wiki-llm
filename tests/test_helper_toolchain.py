"""The pack's helper toolchain, and helper processes behind the host."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.engine import (
    CODE_DOCS_PACK,
    BundledHelperToolchain,
    DomainPack,
    Engine,
    HelperToolchain,
    NoHelperToolchain,
    NoProcessHost,
)
from llm_wiki_cli.extractors.go_extractor import GoExtractor
from llm_wiki_cli.extractors.haskell_extractor import HaskellExtractor
from llm_wiki_cli.extractors.rust_extractor import RustExtractor
from llm_wiki_cli.services import extractor_helpers, helper_cache, helper_preparation
from llm_wiki_cli.services.host import HostCapabilityError, using_host

REFUSED = "the host does not grant subprocesses"


def _no_process(*args, **kwargs):
    pytest.fail("a subprocess was started behind a host that grants none")


@pytest.mark.parametrize(
    "extractor, module, filename",
    [
        (GoExtractor, "go_extractor", "main.go"),
        (RustExtractor, "rust_extractor", "src/lib.rs"),
        (HaskellExtractor, "haskell_extractor", "Main.hs"),
    ],
)
def test_prepared_helpers_do_not_run_behind_a_no_process_host(
    tmp_path, monkeypatch, extractor, module, filename
):
    source = tmp_path / filename
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("-- placeholder\n", encoding="utf-8")
    monkeypatch.setattr(
        f"llm_wiki_cli.extractors.{module}.get_prepared_binary",
        lambda *a, **k: tmp_path / "helper",
    )
    monkeypatch.setattr(subprocess, "run", _no_process)
    instance = extractor()
    with using_host(NoProcessHost()):
        result = instance.extract(str(tmp_path))
    assert not result
    assert instance.last_error == REFUSED


def test_helper_probes_and_builds_ask_the_host(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", _no_process)
    monkeypatch.setattr(subprocess, "Popen", _no_process)
    with using_host(NoProcessHost()):
        assert extractor_helpers.command_output(["go", "version"]) is None
        assert extractor_helpers._go_version("go") == (None, REFUSED)
        assert extractor_helpers._ghc_version("ghc") == (None, REFUSED)
        with pytest.raises(HostCapabilityError, match="cargo"):
            helper_cache._run(["cargo", "build"], cwd=tmp_path, env={}, timeout=5)


def test_the_code_docs_pack_prepares_the_bundled_helpers():
    assert isinstance(CODE_DOCS_PACK.helper_toolchain, BundledHelperToolchain)
    assert CODE_DOCS_PACK.describe()["helper_toolchain"] == (
        "llm_wiki_cli.services.domain_pack.BundledHelperToolchain"
    )
    with pytest.raises(TypeError, match="HelperToolchain"):
        CODE_DOCS_PACK.with_helper_toolchain(object())  # type: ignore[arg-type]
    without = CODE_DOCS_PACK.with_helper_toolchain(NoHelperToolchain())
    assert isinstance(without.helper_toolchain, NoHelperToolchain)
    assert without.classifier is CODE_DOCS_PACK.classifier


class RecordingToolchain(HelperToolchain):
    def __init__(self) -> None:
        self.prepared: list[tuple[str, ...]] = []

    def languages(self, snapshot, registry, *, only_files=None):
        return ()

    def prepare(self, snapshot, registry, *, only_files=None, cache_dir=None):
        self.prepared.append(tuple(sorted(k for k, v in snapshot.files_by_language.items() if v)))
        return ()


def _source_tree(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/billing.py").write_text("class Invoice:\n    total: int\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))


def test_extraction_prepares_helpers_through_the_pack(tmp_path, monkeypatch):
    _source_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(
        helper_preparation, "prepare_operation_helpers",
        lambda *a, **k: pytest.fail("the bundled toolchain was used"),
    )
    toolchain = RecordingToolchain()
    pack = DomainPack(
        "team/recording", CODE_DOCS_PACK.classifier, helper_toolchain=toolchain
    )
    Engine(host=NoProcessHost(), pack=pack).call(api.bootstrap_wiki, "src", "wiki")
    assert toolchain.prepared and set(toolchain.prepared) == {("python",)}
    assert (tmp_path / "wiki/entities/Invoice.md").is_file()


def test_a_pack_without_helpers_never_prepares_one(tmp_path, monkeypatch):
    _source_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(
        helper_preparation, "prepare_operation_helpers",
        lambda *a, **k: pytest.fail("a helper was prepared"),
    )
    pack = CODE_DOCS_PACK.with_helper_toolchain(NoHelperToolchain())
    engine = Engine(host=NoProcessHost(), pack=pack)
    engine.call(api.bootstrap_wiki, "src", "wiki")
    assert (tmp_path / "wiki/entities/Invoice.md").is_file()
    assert engine.capabilities()["pack"]["helper_toolchain"].endswith("NoHelperToolchain")  # type: ignore[index]
