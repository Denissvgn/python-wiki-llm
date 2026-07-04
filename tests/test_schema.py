"""Tests for schema block replacement."""

from llm_wiki_cli.services.schema import (
    CONSTRAINT_END,
    CONSTRAINT_START,
    build_schema_content,
    replace_schema_block,
)


def _squash_ws(content: str) -> str:
    return " ".join(content.split())


def test_replace_schema_block_preserves_literal_backslashes(tmp_path):
    schema_path = tmp_path / "AGENTS.md"
    schema_path.write_text(
        f"User intro\n\n{CONSTRAINT_START}\nold\n{CONSTRAINT_END}\n\nUser outro\n",
        encoding="utf-8",
    )
    new_content = f"{CONSTRAINT_START}\npath \\1 \\g<name>\n{CONSTRAINT_END}\n"

    replace_schema_block(schema_path, new_content)

    text = schema_path.read_text(encoding="utf-8")
    assert "path \\1 \\g<name>" in text
    assert "User intro" in text
    assert "User outro" in text


def test_agent_schema_mentions_current_sync_and_lint_runtime():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "llm-wiki sync --jobs auto --wiki-dir docs/llm_wiki --src-dir ." in content
    assert (
        "llm-wiki lint --strict --jobs auto --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --profile --cache-stats --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --strict --jobs auto --wiki-dir docs/llm_wiki "
        "--src-dir <repo> --allow-external-src" in content
    )
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "llm-wiki prepare-extractors --cache-dir .cache/llm-wiki-helpers" in content
    assert (
        "llm-wiki sync --cache-dir .cache/llm-wiki-inventory "
        "--helper-cache-dir .cache/llm-wiki-helpers" in content
    )
    assert "--include-tests go" in content
    assert "LLM_WIKI_GO=/path/to/go" in content
    assert "LLM_WIKI_GHC=/path/to/ghc" in content
    assert "prepared TypeScript/JavaScript/Go/Rust/Haskell helpers" in content
    assert "normal CLI extraction invokes the prepared Haskell helper" in content
    assert (
        "syntax-only Haskell inventory without typechecking the target project" in text
    )
    assert "does not start Haskell Language Server" in text
    assert (
        "Haskell dependency reconciliation reads Cabal `build-depends` statically"
        in text
    )
    assert (
        "Stack `extra-deps` and Nix package hints as optional advisory metadata" in text
    )
    assert "Unknown Haskell imports are ignored rather than guessed" in text
    assert "GHC 9.6.x is the supported Haskell helper toolchain" in text
    assert "newer GHC 9.x releases are best-effort" in text
    assert "Generated Haskell module pages render declared module names" in content
    assert "persistent inventory cache" in content
    assert "--allow-external-src" in content
    assert "project-root write guard" in content
    assert "large-diff guard" in content
    assert "semantic pass" in content
    assert "Lint passing is not enough" in content
    assert "_Auto-generated from ..._" in content


def test_agent_schema_mentions_dependency_architecture_responsibilities():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "dependencies.md" in content
    assert "load-order.md" in content
    assert "--skip-dependencies" in content
    assert "## Notes" in content
    assert "agent-owned" in content
    assert "Import cycles" in content
    assert "undeclared" in content
    assert "unused" in content
    assert "warning diagnostics" in content


def test_agent_schema_documents_haskell_inventory_contract():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "Haskell inventory stays additive under `llm-wiki-extract/v1`" in text
    assert (
        "Haskell file entries include `language`, `imports`, `classes`, and `functions`"
        in text
    )
    assert "`module` is present when the source declares one" in text
    assert "`module`, `qualified`, `alias`, and `line`" in content
    assert "`classes` stores type-oriented declarations" in text
    assert "`data`, `newtype`, `type`, `class`, or `instance`" in content
    assert "`functions` stores top-level signatures, functions, and values" in text
    assert "`signature`, `function`, or `value`" in content
    assert "`language_pragmas`, `exports`, and `deriving`" in text


def test_agent_schema_mentions_data_flow_review_responsibilities():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "## Data flow" in content
    assert "static-analysis gaps" in content
    assert "## Behavior" in content
    assert "observed side effects" in content


def test_agent_schema_mentions_canonical_surfaces_and_generated_ownership():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "canonical wiki surfaces" in content
    for path in [
        "docs/llm_wiki/index.md",
        "docs/llm_wiki/log.md",
        "docs/llm_wiki/entities/",
        "docs/llm_wiki/modules/",
        "docs/llm_wiki/workflows/",
        "docs/llm_wiki/guides/",
        "docs/llm_wiki/flows/",
        "docs/llm_wiki/infrastructure/",
        "docs/llm_wiki/dependencies.md",
        "docs/llm_wiki/load-order.md",
    ]:
        assert path in content
    assert "Do not edit generated Mermaid diagrams by hand" in content
    assert "Diagram style plugins may configure generated Mermaid flowchart" in content
    assert "cannot inject arbitrary Markdown" in content
    assert "semantic sections" in content
    assert "`sync` does not generate or overwrite guide prose" in content
    assert "Static-site mirror output" in content
    assert "not as an editable source of truth" in content
    assert (
        "Docusaurus exports include generated front matter and sidebars.json" in content
    )
    assert "Raw Node `http.createServer` and `https.createServer` calls" in content
    assert "optional lockfile-backed `versions`" in content
    assert "Haskell lockfile pinning is intentionally out of scope" in text


def test_ide_schema_mentions_incremental_sync_workflow():
    content = build_schema_content("copilot", "docs/llm_wiki")

    assert "llm-wiki sync --jobs auto" in content
    assert "If sync repairs only the manifest" in content
    assert "Sync output is a deterministic AST/docstring skeleton" in content
    assert "Passing lint is not enough" in content
    assert "_Auto-generated from ..._" in content
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "llm-wiki prepare-extractors --cache-dir .cache/llm-wiki-helpers" in content
    assert "--include-tests go" in content
    assert "LLM_WIKI_GO=/path/to/go" in content
    assert "LLM_WIKI_GHC=/path/to/ghc" in content
    assert "llm-wiki lint --strict --jobs auto" in content


def test_cli_agent_schema_mentions_manual_sync_workflow():
    content = build_schema_content("claude", "docs/llm_wiki")

    assert "llm-wiki sync --jobs auto" in content
    assert "llm-wiki generate-prompt" in content
    assert "updated automatically on commit" not in content
