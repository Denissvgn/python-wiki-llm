"""End-to-end compatibility gate for the graph and section extensions."""

from __future__ import annotations

import json
import textwrap
import types
from pathlib import Path

from llm_wiki_cli import api
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services.contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.mcp_server import McpWikiService


def _sync(wiki_dir: Path) -> None:
    sync_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki_dir),
            jobs=1,
            no_cache=True,
        )
    )


def _knowledge_payload(wiki_dir: Path) -> dict:
    return json.loads(
        (wiki_dir / ".llm-wiki-knowledge.json").read_text(encoding="utf-8")
    )


def _concept_for_path(payload: dict, canonical_path: str) -> dict:
    return next(
        concept
        for concept in payload["concepts"]
        if concept["document"]["canonical_path"] == canonical_path
    )


def _section_for_title(
    payload: dict,
    *,
    page_locator: str,
    title: str,
) -> dict:
    extension = payload["extensions"][SECTION_OWNERSHIP_EXTENSION_KEY]
    page = next(
        page for page in extension["pages"] if page["page_locator"] == page_locator
    )
    return next(section for section in page["sections"] if section["title"] == title)


def _main_source(*, changed: bool) -> str:
    signature = "flag=False" if changed else ""
    lines = [
        '"""Process entry points and graph boundaries."""',
        "",
        "import os",
    ]
    if changed:
        lines.append("import json")
    lines.extend(
        [
            "",
            f"def main({signature}):",
            '    """Main entry."""',
            "    step_0()",
            "    User()",
        ]
    )
    lines.extend(f"    missing_{index:02d}()" for index in range(21))
    lines.extend("    os.getcwd()" for _ in range(25))
    lines.extend(
        [
            f"    return flag if {changed!r} else None",
            "",
        ]
    )
    for index in range(8):
        body = (
            f"    return step_{index + 1}()"
            if index < 7
            else "    return None"
        )
        lines.extend([f"def step_{index}():", body, ""])
    if changed:
        lines.extend(
            [
                "def generated_helper(value=None):",
                "    return value",
                "",
            ]
        )
    lines.extend(
        [
            'if __name__ == "__main__":',
            "    main()",
            "",
        ]
    )
    return "\n".join(lines)


def test_bootstrap_sync_query_context_and_mcp_share_graph_and_section_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [project]
            name = "graph-section-e2e"
            version = "0.1.0"

            [project.scripts]
            graph-section-e2e = "main:main"
            """
        ),
        encoding="utf-8",
    )
    for package, description in (
        ("pkg_a", "First duplicate."),
        ("pkg_b", "Second duplicate."),
    ):
        package_dir = project / package
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (package_dir / "models.py").write_text(
            textwrap.dedent(
                f'''\
                class User:
                    """{description}"""

                    def identity(self):
                        return "{package}"
                '''
            ),
            encoding="utf-8",
        )
    (project / "main.py").write_text(_main_source(changed=False), encoding="utf-8")

    wiki_dir = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)
    bootstrap_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki_dir),
            overwrite=False,
            depth="full",
            skip_workflows=True,
            source_adapter=True,
            format="text",
        )
    )
    capsys.readouterr()

    initial = _knowledge_payload(wiki_dir)
    main_concept = _concept_for_path(initial, "modules/main.md")
    main_locator = main_concept["locator"]
    initial_functions = _section_for_title(
        initial,
        page_locator=main_locator,
        title="Functions",
    )

    main_page = wiki_dir / "modules" / "main.md"
    edited_main = main_page.read_text(encoding="utf-8").replace(
        "Main entry.",
        "Operator-owned entry documentation.",
    )
    assert edited_main != main_page.read_text(encoding="utf-8")
    main_page.write_text(edited_main, encoding="utf-8")

    index_page = wiki_dir / "index.md"
    custom_section = (
        "\n## Operator notes\n\n"
        "This section is intentionally maintained by the wiki owner.\n"
    )
    index_page.write_text(
        index_page.read_text(encoding="utf-8") + custom_section,
        encoding="utf-8",
    )
    markdown_before_noop_sync = {
        path.relative_to(wiki_dir).as_posix(): path.read_bytes()
        for path in sorted(wiki_dir.rglob("*.md"))
    }

    _sync(wiki_dir)
    capsys.readouterr()

    markdown_after_noop_sync = {
        path.relative_to(wiki_dir).as_posix(): path.read_bytes()
        for path in sorted(wiki_dir.rglob("*.md"))
    }
    assert markdown_after_noop_sync["modules/main.md"] == (
        markdown_before_noop_sync["modules/main.md"]
    )
    assert {
        path
        for path in markdown_before_noop_sync
        if markdown_after_noop_sync[path] != markdown_before_noop_sync[path]
    } <= {"index.md"}
    assert custom_section.strip() in index_page.read_text(encoding="utf-8")

    _sync(wiki_dir)
    capsys.readouterr()
    assert {
        path.relative_to(wiki_dir).as_posix(): path.read_bytes()
        for path in sorted(wiki_dir.rglob("*.md"))
    } == markdown_after_noop_sync

    semantic = _knowledge_payload(wiki_dir)
    semantic_functions = _section_for_title(
        semantic,
        page_locator=main_locator,
        title="Functions",
    )
    assert semantic_functions["ownership"] == "mixed"
    assert semantic_functions["structural_hash"] == (
        initial_functions["structural_hash"]
    )
    assert semantic_functions["semantic_hash"] != initial_functions["semantic_hash"]

    (project / "main.py").write_text(_main_source(changed=True), encoding="utf-8")
    _sync(wiki_dir)
    capsys.readouterr()

    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID
    final = _knowledge_payload(wiki_dir)
    graph = final["extensions"][TYPED_GRAPH_EXTENSION_KEY]
    assert graph["schema_version"] == "llm-wiki-typed-graph/v1"
    final_functions = _section_for_title(
        final,
        page_locator=main_locator,
        title="Functions",
    )
    assert final_functions["structural_hash"] != (
        semantic_functions["structural_hash"]
    )
    assert final_functions["semantic_hash"] == semantic_functions["semantic_hash"]
    assert "Operator-owned entry documentation." in main_page.read_text(
        encoding="utf-8"
    )

    index_locator = _concept_for_path(final, "index.md")["locator"]
    operator_notes = _section_for_title(
        final,
        page_locator=index_locator,
        title="Operator notes",
    )
    assert operator_notes["ownership"] == "semantic"
    assert operator_notes.get("structural_hash") is None
    assert operator_notes["semantic_hash"] == operator_notes["exact_hash"]
    assert custom_section.strip() in index_page.read_text(encoding="utf-8")

    initial_imports = _section_for_title(
        semantic,
        page_locator=main_locator,
        title="Imports",
    )
    final_imports = _section_for_title(
        final,
        page_locator=main_locator,
        title="Imports",
    )
    assert initial_imports["ownership"] == final_imports["ownership"] == "generated"
    assert initial_imports["structural_hash"] != final_imports["structural_hash"]
    assert initial_imports.get("semantic_hash") is None
    assert final_imports.get("semantic_hash") is None

    duplicate_users = [
        concept
        for concept in final["concepts"]
        if concept["concept_kind"] == "code-entity"
        and concept["title"] == "User"
    ]
    assert len(duplicate_users) == 2
    assert len({concept["locator"] for concept in duplicate_users}) == 2

    call_edges = [edge for edge in graph["edges"] if edge["kind"] == "calls"]
    assert {"resolved", "ambiguous", "external", "unresolved"} <= {
        edge["resolution"] for edge in call_edges
    }
    bounded_external = next(
        edge for edge in call_edges if edge["resolution"] == "external"
    )
    assert bounded_external["coverage"] == {
        "observed": 25,
        "emitted": 20,
        "omitted": 5,
        "limit": 20,
        "truncated": True,
        "limitations": [],
    }
    data_flow_coverage = next(
        coverage
        for coverage in graph["coverage"]
        if coverage["analyzer"] == "data-flows"
    )
    assert "upstream-flow-depth-limit-reached" in data_flow_coverage["limitations"]
    flow_coverage = next(
        coverage
        for coverage in graph["coverage"]
        if coverage["analyzer"] == "flows"
    )
    assert flow_coverage["observed"] > flow_coverage["emitted"]
    assert flow_coverage["omitted"] == (
        flow_coverage["observed"] - flow_coverage["emitted"]
    )
    assert flow_coverage["truncated"] is True
    assert "flow-steps-are-statically-inferred" in flow_coverage["limitations"]
    flow_pages = sorted((wiki_dir / "flows").glob("*.md"))
    assert len(flow_pages) == 1
    flow_markdown = flow_pages[0].read_text(encoding="utf-8")
    truncated_gap = next(
        line
        for line in flow_markdown.splitlines()
        if line.startswith("| truncated_flow |")
    )
    assert truncated_gap.endswith("| 0 |")

    query_service = api.build_documentation_query_service(
        str(project),
        wiki_dir=str(wiki_dir),
        limit=20,
        read_only=True,
    )
    query_result = api.traverse_typed_graph(
        main_locator,
        service=query_service,
        kinds=["calls"],
    )
    mcp_result = McpWikiService(
        src_dir=str(project),
        wiki_dir=str(wiki_dir),
    ).traverse_typed_graph(
        main_locator,
        kinds=["calls"],
        limit=20,
    )
    context = api.build_context(
        str(project),
        budget=200_000,
        focus="all",
        filters={
            "surface": "modules",
            "relationship_kind": "calls",
        },
        wiki_dir=str(wiki_dir),
        read_only=True,
    )
    context_page = next(
        page
        for page in context["surface"]["pages"]
        if page["canonical_path"] == "modules/main.md"
    )
    context_graph = context_page["typed_graph"]
    expected_bounds = {
        "total": query_result["total"],
        "returned": query_result["returned"],
        "truncated": query_result["truncated"],
    }
    assert expected_bounds == {
        "total": mcp_result["total"],
        "returned": mcp_result["returned"],
        "truncated": mcp_result["truncated"],
    }
    assert expected_bounds == {
        "total": context_graph["filtered_total"],
        "returned": context_graph["returned"],
        "truncated": context_graph["truncated"],
    }
    assert expected_bounds["total"] > expected_bounds["returned"] == 20

    calls_coverage = next(
        coverage
        for coverage in graph["coverage"]
        if coverage["analyzer"] == "calls"
    )
    size_and_coverage = {
        "knowledge_bytes": (
            wiki_dir / ".llm-wiki-knowledge.json"
        ).stat().st_size,
        "graph_bytes": len(
            json.dumps(
                graph,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ),
        "calls_observed": calls_coverage["observed"],
        "calls_emitted": calls_coverage["emitted"],
    }
    assert size_and_coverage["knowledge_bytes"] > size_and_coverage["graph_bytes"] > 0
    assert size_and_coverage["knowledge_bytes"] < 2_000_000
    assert size_and_coverage["graph_bytes"] < 1_000_000
    assert size_and_coverage["calls_observed"] == (
        size_and_coverage["calls_emitted"]
    )
    assert size_and_coverage["calls_observed"] >= 50
