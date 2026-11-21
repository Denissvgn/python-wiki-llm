"""A domain pack decides classification, naming, rendering and context for an operation."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path, PurePath

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.engine import (
    CODE_DOCS_PACK,
    BuiltInPageRenderer,
    CodeContextSource,
    ContextSource,
    DomainPack,
    Engine,
    EntityPageRequest,
    ExtensionSourceClassifier,
    ModulePageRequest,
    NoProcessHost,
    PageRequest,
    StemPageNamer,
)
from llm_wiki_cli.extractors.common import LANGUAGE_EXTENSIONS

from llm_wiki_cli.services import bootstrap_runtime
from llm_wiki_engine import markdown_sections, sync_manifest
from llm_wiki_cli.services.dependencies import analyze_dependencies
from llm_wiki_cli.services.domain_pack import current_pack, uses_default_pack, using_pack
from llm_wiki_cli.services.entrypoints import build_flow
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
        self.requests: list[ModulePageRequest | EntityPageRequest | PageRequest] = []

    def _with_owner(self, request) -> str:
        self.requests.append(request)
        return request.builtin_markdown().rstrip("\n") + f"\n\n## Owner\n\n{self.team}\n"

    def render_module(self, request):
        return self._with_owner(request)

    def render_entity(self, request):
        return self._with_owner(request)

    def render_page(self, request):
        return self._with_owner(request)


def _owned(markdown: str, team: str) -> str:
    return markdown.rstrip("\n") + f"\n\n## Owner\n\n{team}\n"


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

    assert entity == _owned(builtin_entity, "Billing team")
    assert module == _owned(builtin_module, "Billing team")
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


def test_the_pack_page_renderer_writes_every_other_page_kind(tmp_path) -> None:
    module = {"language": "python", "imports": [], "classes": [], "functions": []}
    analysis = analyze_dependencies({"billing.py": module}, str(tmp_path))
    flow = build_flow(
        {"id": "cli-main", "category": "cli", "file": "app.py", "symbol": "main", "label": "main"}, []
    )
    docker = {"type": "dockerfile", "stages": [], "base_images": [], "instructions": []}
    pages = {
        "index": lambda: bootstrap_runtime._generate_index_md(["Invoice"], []),
        "workflows": lambda: bootstrap_runtime._generate_workflow_md(
            "billing", {"entry": "app.bill", "modules_touched": ["app"], "chain": ["app.bill"]}
        ),
        "flows": lambda: bootstrap_runtime._generate_flow_md(flow),
        "infrastructure": lambda: bootstrap_runtime._generate_infrastructure_md("Dockerfile", docker),
        "api-contracts": lambda: bootstrap_runtime._generate_api_contracts_md({"operations": []}),
        "dependencies": lambda: bootstrap_runtime._generate_dependencies_md(analysis),
        "load-order": lambda: bootstrap_runtime._generate_load_order_md(analysis),
    }
    builtin = {kind: render() for kind, render in pages.items()}
    renderer = OwnerRenderer("Platform")

    with using_pack(CODE_DOCS_PACK.with_page_renderer(renderer)):
        rendered = {kind: render() for kind, render in pages.items()}

    assert rendered == {kind: _owned(markdown, "Platform") for kind, markdown in builtin.items()}
    requests = [request for request in renderer.requests if isinstance(request, PageRequest)]
    assert requests == renderer.requests
    assert [request.page_kind.value for request in requests] == list(pages)
    index, workflow, _, infrastructure, *_ = requests
    assert index.inputs["entity_names"] == ["Invoice"] and index.inputs["log_present"] is True
    assert (workflow.inputs["name"], workflow.inputs["module_pages"]) == ("billing", None)
    assert (infrastructure.inputs["source_path"], infrastructure.inputs["info"]) == ("Dockerfile", docker)
    with pytest.raises(TypeError):
        index.inputs["log_present"] = False  # type: ignore[index]
    with pytest.raises(ValueError, match="its own request type"):
        PageRequest("modules", {}, lambda: "")  # type: ignore[arg-type]


def _replace_section(page: Path, heading: str, body: str) -> None:
    text = page.read_text(encoding="utf-8")
    text, count = re.subn(
        rf"(## {heading}\n\n).*?(?=\n## |\Z)", lambda match: f"{match.group(1)}{body}\n", text, count=1, flags=re.S
    )
    assert count == 1
    page.write_text(text, encoding="utf-8")


def test_sync_keeps_reviewed_sections_of_rendered_pages(tmp_path, monkeypatch) -> None:
    _write(tmp_path / "src/billing.py", "class Invoice:\n    total: int\n")
    _write(
        tmp_path / "src/app.py",
        "from flask import Flask\nfrom .billing import Invoice\n\napp = Flask(__name__)\n\n\n"
        "@app.route('/invoices')\ndef list_invoices():\n    return [Invoice()]\n",
    )
    _write(tmp_path / "src/Dockerfile", "FROM python:3.12\nCOPY src /app\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    wiki = tmp_path / "wiki"
    pages = ["index.md", "flows/http-list_invoices.md", "infrastructure/Dockerfile.md",
             "dependencies.md", "load-order.md"]

    Engine(host=NoProcessHost(), pack=CODE_DOCS_PACK.with_page_renderer(OwnerRenderer("Team A"))).call(
        api.bootstrap_wiki, "src", "wiki"
    )
    assert all((wiki / page).read_text(encoding="utf-8").endswith("## Owner\n\nTeam A\n") for page in pages)
    _replace_section(wiki / "flows/http-list_invoices.md", "Behavior", "Lists invoices for the dashboard.")
    _replace_section(wiki / "infrastructure/Dockerfile.md", "Notes", "Reviewed by ops.")
    _replace_section(wiki / "dependencies.md", "Notes", "Billing depends on nothing.")
    index = wiki / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\n## Team links\n\nSee the handbook.\n", encoding="utf-8")
    _write(tmp_path / "src/billing.py", "class Invoice:\n    total: int\n\n\nclass Refund:\n    amount: int\n")

    engine = Engine(host=NoProcessHost(), pack=CODE_DOCS_PACK.with_page_renderer(OwnerRenderer("Team B")))
    engine.call(api.sync_wiki, "src", "wiki")

    text = {page: (wiki / page).read_text(encoding="utf-8") for page in pages}
    assert all(t.count("## Owner") == 1 and "## Owner\n\nTeam B\n" in t for t in text.values())
    assert "Lists invoices for the dashboard." in text["flows/http-list_invoices.md"]
    assert "Reviewed by ops." in text["infrastructure/Dockerfile.md"]
    assert "Billing depends on nothing." in text["dependencies.md"]
    assert "[Refund]" in text["index.md"] and text["index.md"].endswith("## Team links\n\nSee the handbook.\n")
    assert engine.call(api.lint_wiki, "src", "wiki")["ok"]


def test_index_sections_the_new_index_writes_are_not_carried_forward() -> None:
    old = "# Index\n\n## Modules\n\n- a\n\n## Owner\n\nTeam A\n\n## Team links\n\nhandbook\n"
    new = "# Index\n\n## Modules\n\n- b\n\n## Owner\n\nTeam B\n"

    assert markdown_sections.preserve_index_custom_sections(old, new) == (
        "# Index\n\n## Modules\n\n- b\n\n## Owner\n\nTeam B\n\n## Team links\n\nhandbook\n"
    )
    assert markdown_sections.preserve_index_custom_sections(old, "# Index\n\n## Modules\n\n- b\n").endswith(
        "## Owner\n\nTeam A\n\n## Team links\n\nhandbook\n"
    )


class FolderContextSource(CodeContextSource):
    """Relates sources in one folder and counts their classes."""

    def related_sources(self, inventory):
        return {
            path: {other for other in inventory if other != path and PurePath(other).parent == PurePath(path).parent}
            for path in inventory
        }

    def entry(self, data, detail):
        return {**super().entry(data, detail), "class_count": len(data.get("classes", []))}


FOLDERS = CODE_DOCS_PACK.with_context_source(FolderContextSource())


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=root, check=True, capture_output=True,
    )


def _context_project(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / "pkg/a.py", "class Account:\n    total: int\n")
    _write(tmp_path / "pkg/b.py", "class Budget:\n    limit: int\n")
    _write(tmp_path / "other/c.py", "from pkg.a import Account\n\nclass Cart:\n    owner: Account\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "start")
    _write(tmp_path / "pkg/a.py", "class Account:\n    total: int\n    tax: int\n")
    _git(tmp_path, "commit", "-qam", "change")


def test_the_code_context_source_relates_sources_by_imports() -> None:
    source = CODE_DOCS_PACK.context_source
    inventory = {"src/pkg/a.py": {}, "src/pkg/b.py": {"imports": [{"module": "pkg.a"}]}, "notes.md": {}}

    assert isinstance(source, ContextSource)
    assert source.related_sources(inventory) == {
        "src/pkg/a.py": {"src/pkg/b.py"}, "src/pkg/b.py": {"src/pkg/a.py"}, "notes.md": set(),
    }
    data = {"language": "python", "classes": [{"name": "A", "line": 1, "doc": "x"}], "functions": []}
    assert source.entry(data, "summary") == {"classes": ["A"]}
    assert source.entry(data, "slim") == {"classes": [{"name": "A", "bases": [], "line": 1}], "functions": []}
    assert source.entry(data, "deep") == {"classes": data["classes"], "functions": []}


def test_a_pack_context_source_ranks_and_shows_budgeted_context(tmp_path, monkeypatch) -> None:
    _context_project(tmp_path, monkeypatch)

    default = api.build_context(".", focus=["changed", "neighbors"])
    with using_pack(FOLDERS):
        folders = api.build_context(".", focus=["changed", "neighbors"])

    def priorities(payload):
        return {path: entry["priority"] for path, entry in payload["files"].items()}

    assert priorities(default) == {"pkg/a.py": "high", "other/c.py": "medium", "pkg/b.py": "low"}
    assert priorities(folders) == {"pkg/a.py": "high", "pkg/b.py": "medium", "other/c.py": "low"}
    assert folders["files"]["pkg/b.py"]["class_count"] == 1
    assert "class_count" not in default["files"]["pkg/b.py"]


def test_qualified_packets_need_the_built_in_context_source(tmp_path, monkeypatch) -> None:
    _context_project(tmp_path, monkeypatch)

    assert api.build_qualified_context(".").to_payload()["schema_version"]
    with using_pack(FOLDERS), pytest.raises(api.WorkspaceStateError) as refused:
        api.build_qualified_context(".")
    assert refused.value.details == {"field": "context_source"}
    assert "built-in context source" in str(refused.value.__cause__)
    with using_pack(NOTES):
        assert api.build_qualified_context(".").to_payload()["schema_version"]


def test_a_context_source_must_return_mappings() -> None:
    class Broken(CodeContextSource):
        def related_sources(self, inventory):
            return None

        def entry(self, data, detail):
            return None

    from llm_wiki_cli.services import context_service

    with using_pack(CODE_DOCS_PACK.with_context_source(Broken())):  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="mapping of related sources"):
            context_service._build_import_graph({})
        with pytest.raises(TypeError, match="mapping entry"):
            context_service._build_entry({}, "high", "deep")


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
    with pytest.raises(TypeError, match="ContextSource"):
        NOTES.with_context_source(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DomainPack"):
        Engine(pack=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DomainPack"), using_pack(object()):  # type: ignore[arg-type]
        pass
    assert NOTES.describe() == {
        "name": "team/notes",
        "source_kinds": {"notes": [".md", ".txt"]},
        "classifier": "llm_wiki_engine.pack_interfaces.ExtensionSourceClassifier",
        "page_namer": "llm_wiki_cli.services.domain_pack.StemPageNamer",
        "page_renderer": "llm_wiki_cli.services.domain_pack.BuiltInPageRenderer",
        "context_source": "llm_wiki_cli.services.domain_pack.CodeContextSource",
        "reference_providers": ["llm-wiki-cli", "llm-wiki-behavior", "contract-file"],
        "helper_toolchain": "llm_wiki_cli.services.domain_pack.BundledHelperToolchain",
        "extractors": {},
    }


def test_pack_interfaces_live_in_the_engine_and_stay_importable_here():
    import llm_wiki_engine.pack_interfaces as engine_side
    from llm_wiki_cli.services import domain_pack as cli_side

    # The CLI keeps its own subclasses (with today's defaults) of these names.
    specialized = {"BuiltInPageRenderer", "DomainPack", "StemPageNamer"}
    for name in engine_side.__all__:
        if name == "current_pack":
            continue
        if name in specialized:
            assert issubclass(getattr(cli_side, name), getattr(engine_side, name)), name
        elif hasattr(cli_side, name):
            assert getattr(cli_side, name) is getattr(engine_side, name), name
    assert cli_side.using_pack is engine_side.using_pack
    # The CLI's current pack defaults to the code-documentation pack; the engine has none.
    assert cli_side.current_pack() is cli_side.CODE_DOCS_PACK
    with pytest.raises(LookupError):
        engine_side.current_pack()
    # The code-documentation pack and its defaults stay with the CLI.
    assert cli_side.CODE_DOCS_PACK.classifier.__class__.__module__ == cli_side.__name__
    assert not hasattr(engine_side, "CODE_DOCS_PACK")
