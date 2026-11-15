"""A domain pack decides source classification and page naming for an operation."""

from __future__ import annotations

import os
from pathlib import Path, PurePath

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.engine import (
    CODE_DOCS_PACK,
    BuiltInPageRenderer,
    DomainPack,
    Engine,
    EntityPageRequest,
    ExtensionSourceClassifier,
    ModulePageRequest,
    NoProcessHost,
    StemPageNamer,
)
from llm_wiki_cli.extractors.common import LANGUAGE_EXTENSIONS
from llm_wiki_cli.services import bootstrap_runtime, sync_manifest
from llm_wiki_cli.services.domain_pack import current_pack, uses_default_pack, using_pack
from llm_wiki_cli.services.source_snapshot import SourceSnapshotError, build_source_snapshot

NOTES = DomainPack("team/notes", ExtensionSourceClassifier({"notes": (".md", ".txt")}))


class PrefixedPageNamer(StemPageNamer):
    def module_pages(self, inventory):
        return {path: f"mod_{name}" for path, name in super().module_pages(inventory).items()}

    def entity_pages(self, inventory, module_pages):
        return {key: f"ent_{name}" for key, name in super().entity_pages(inventory, module_pages).items()}


PREFIXED = CODE_DOCS_PACK.with_page_namer(PrefixedPageNamer())


class OwnerRenderer(BuiltInPageRenderer):
    def __init__(self, team: str) -> None:
        self.team = team
        self.requests: list[ModulePageRequest | EntityPageRequest] = []

    def _with_owner(self, request) -> str:
        self.requests.append(request)
        return request.builtin_markdown().rstrip("\n") + f"\n\n## Owner\n\n{self.team}\n"

    def render_module(self, request):
        return self._with_owner(request)

    def render_entity(self, request):
        return self._with_owner(request)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_the_code_docs_pack_classifies_the_built_in_languages() -> None:
    classifier = CODE_DOCS_PACK.classifier

    assert current_pack() is CODE_DOCS_PACK and uses_default_pack()
    assert classifier.source_kinds() is LANGUAGE_EXTENSIONS
    assert classifier.classify(PurePath("pkg/app.py"), frozenset()) == ("python", None)
    assert classifier.classify(PurePath("pkg/app_test.go"), frozenset()) == ("go", "go-tests-excluded")
    assert classifier.classify(PurePath("pkg/app_test.go"), frozenset({"go"})) == ("go", None)
    assert classifier.classify(PurePath("README.md"), frozenset()) == (None, None)
    assert classifier.inventory_language("web/app.js") == "javascript"
    assert classifier.inventory_language("web/app.ts") == "typescript"
    assert CODE_DOCS_PACK.describe()["source_kinds"]["haskell"] == [".hs", ".lhs"]


def test_a_pack_classifier_decides_which_files_are_sources(tmp_path) -> None:
    _write(tmp_path / "guide.md", "# Guide\n")
    _write(tmp_path / "notes/todo.txt", "todo\n")
    _write(tmp_path / "app.py", "x = 1\n")

    with using_pack(NOTES):
        snapshot = build_source_snapshot(tmp_path)
        assert not uses_default_pack()
        assert sync_manifest._infer_language_from_path("guide.md") == "notes"

    assert {kind: snapshot.language_paths(kind) for kind in snapshot.files_by_language} == {
        "notes": ["guide.md", "notes/todo.txt"],
    }
    assert build_source_snapshot(tmp_path).language_paths("python") == ["app.py"]


def test_built_in_extractors_skip_languages_the_pack_does_not_classify(tmp_path, monkeypatch) -> None:
    _write(tmp_path / "src/app.py", "class Account:\n    value: int\n")
    monkeypatch.chdir(tmp_path)

    with using_pack(NOTES):
        result = api.extract_source("src", deep=True)

    assert result["inventory"] == {}
    assert api.extract_source("src", deep=True)["inventory"]


def test_a_classifier_must_return_a_declared_source_kind(tmp_path) -> None:
    class Stray(ExtensionSourceClassifier):
        def classify(self, path, include_tests):
            return ("stray", None) if path.suffix == ".md" else (None, None)

    _write(tmp_path / "guide.md", "# Guide\n")
    with using_pack(DomainPack("team/stray", Stray({"notes": (".txt",)}))):
        with pytest.raises(SourceSnapshotError, match="undeclared source kind 'stray'"):
            build_source_snapshot(tmp_path)


def test_every_page_map_uses_the_pack_page_namer() -> None:
    inventory = {"one/model.py": {"classes": [{"name": "Account"}]}, "two/model.py": {"classes": []}}

    with using_pack(PREFIXED):
        modules = bootstrap_runtime.build_module_page_map(inventory)
        entities = bootstrap_runtime.build_entity_occurrence_page_map(inventory)
        assert sync_manifest._build_module_page_map(inventory) == modules
        assert sync_manifest._build_entity_occurrence_page_map(inventory, {}) == entities

    assert modules == {"one/model.py": "mod_one_model", "two/model.py": "mod_two_model"}
    assert entities == {("Account", "one/model.py", 1): "ent_Account"}
    assert bootstrap_runtime.build_module_page_map(inventory)["one/model.py"] == "one_model"


def test_an_engine_generates_and_syncs_pages_with_its_pack(tmp_path, monkeypatch) -> None:
    _write(tmp_path / "src/billing.py", "class Invoice:\n    total: int\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    engine = Engine(host=NoProcessHost(), pack=PREFIXED)

    engine.call(api.bootstrap_wiki, "src", "wiki")
    engine.call(api.sync_wiki, "src", "wiki")

    pages = sorted(p.relative_to(tmp_path / "wiki").as_posix() for p in (tmp_path / "wiki").glob("*/*.md"))
    assert "modules/mod_billing.md" in pages and "entities/ent_Invoice.md" in pages
    assert "modules/billing.md" not in pages and "entities/Invoice.md" not in pages
    assert engine.capabilities()["pack"] == PREFIXED.describe()
    with engine.operation() as operation:
        assert operation.pack is current_pack() is PREFIXED


def test_the_pack_page_renderer_writes_every_module_and_entity_page() -> None:
    renderer = OwnerRenderer("Billing team")
    info = {"name": "Invoice", "line": 1, "attributes": [{"name": "total", "type": "int"}]}
    file_data = {"classes": [info], "functions": []}
    builtin_entity = bootstrap_runtime._generate_entity_md(info, "billing.py", {}, "billing")
    builtin_module = bootstrap_runtime._generate_module_md("billing.py", file_data, {"Invoice": "Invoice"})

    with using_pack(CODE_DOCS_PACK.with_page_renderer(renderer)):
        entity = bootstrap_runtime._generate_entity_md(info, "billing.py", {}, "billing")
        module = bootstrap_runtime._generate_module_md("billing.py", file_data, {"Invoice": "Invoice"})

    assert entity == builtin_entity.rstrip("\n") + "\n\n## Owner\n\nBilling team\n"
    assert module == builtin_module.rstrip("\n") + "\n\n## Owner\n\nBilling team\n"
    entity_request, module_request = renderer.requests
    assert isinstance(entity_request, EntityPageRequest)
    assert (entity_request.entity, entity_request.source_path, entity_request.module_page) == (
        info, "billing.py", "billing",
    )
    assert isinstance(module_request, ModulePageRequest)
    assert (module_request.source_path, dict(module_request.entity_pages)) == ("billing.py", {"Invoice": "Invoice"})
    assert module_request.module_dependencies is None and dict(module_request.module_pages) == {}


def test_sync_keeps_descriptions_and_refreshes_rendered_sections(tmp_path, monkeypatch) -> None:
    _write(tmp_path / "src/billing.py", "class Invoice:\n    total: int\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    page = tmp_path / "wiki/entities/Invoice.md"

    Engine(host=NoProcessHost(), pack=CODE_DOCS_PACK.with_page_renderer(OwnerRenderer("Team A"))).call(
        api.bootstrap_wiki, "src", "wiki"
    )
    assert page.read_text(encoding="utf-8").endswith("## Owner\n\nTeam A\n")
    text = page.read_text(encoding="utf-8")
    page.write_text(text.replace(
        "_Auto-generated from `Invoice` in `billing.py`._", "Invoices are issued monthly."
    ), encoding="utf-8")
    _write(tmp_path / "src/billing.py", "class Invoice:\n    total: int\n    tax: int\n")

    engine = Engine(host=NoProcessHost(), pack=CODE_DOCS_PACK.with_page_renderer(OwnerRenderer("Team B")))
    engine.call(api.sync_wiki, "src", "wiki")

    text = page.read_text(encoding="utf-8")
    assert "Invoices are issued monthly." in text and "| `tax` | `int` |" in text
    assert text.endswith("## Owner\n\nTeam B\n")
    assert (tmp_path / "wiki/modules/billing.md").read_text(encoding="utf-8").endswith("## Owner\n\nTeam B\n")
    assert engine.call(api.lint_wiki, "src", "wiki")["ok"]


def test_a_page_renderer_must_return_markdown_text() -> None:
    class Broken(BuiltInPageRenderer):
        def render_entity(self, request):
            return None

    broken = CODE_DOCS_PACK.with_page_renderer(Broken())  # type: ignore[arg-type]
    with using_pack(broken), pytest.raises(TypeError, match="Markdown text"):
        bootstrap_runtime._generate_entity_md({"name": "Invoice"}, "billing.py", {})


def test_pack_values_are_checked() -> None:
    with pytest.raises(ValueError, match="non-empty mapping"):
        ExtensionSourceClassifier({})
    with pytest.raises(ValueError, match="start with '.'"):
        ExtensionSourceClassifier({"notes": ("md",)})
    with pytest.raises(TypeError, match="sequence of strings"):
        ExtensionSourceClassifier({"notes": ".md"})
    with pytest.raises(ValueError, match="unknown source kind"):
        ExtensionSourceClassifier({"notes": (".md",)}, test_suffixes={"go": ("_test.go",)})
    with pytest.raises(ValueError, match="pack name"):
        DomainPack("", NOTES.classifier)
    with pytest.raises(TypeError, match="SourceClassifier"):
        DomainPack("team/notes", object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="PageNamer"):
        NOTES.with_page_namer(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="PageRenderer"):
        NOTES.with_page_renderer(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DomainPack"):
        Engine(pack=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DomainPack"), using_pack(object()):  # type: ignore[arg-type]
        pass
    assert NOTES.describe() == {
        "name": "team/notes",
        "source_kinds": {"notes": [".md", ".txt"]},
        "classifier": "llm_wiki_cli.services.domain_pack.ExtensionSourceClassifier",
        "page_namer": "llm_wiki_cli.services.domain_pack.StemPageNamer",
        "page_renderer": "llm_wiki_cli.services.domain_pack.BuiltInPageRenderer",
    }
