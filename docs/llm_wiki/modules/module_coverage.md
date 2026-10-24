# module_coverage Module

**Path:** `src/llm_wiki_cli/services/module_coverage.py`

## Description

Static coverage explanations over selected, content-bound Python sources.

These routes are report metadata. They do not create inventory declarations,
canonical pages, durable aliases or runtime import equivalence.

## Imports

| Source | Symbols |
|--------|---------|
| `..extractors.python_extractor` | `_static_import_bindings`, `_static_type_checking_block`, `module_alias_target` |
| `.knowledge_storage` | `KnowledgeStorageError` |
| `.knowledge_storage_io` | `read_guarded` |
| `.python_imports` | `PythonModuleIndex` |
| `.source_selection` | `SourceSelectionError`, `locate_exact_repository_path` |
| `.source_snapshot` | `SourceSnapshot` |
| `__future__` | `annotations` |
| `ast` | `ast` |
| `collections.abc` | `Iterable`, `Mapping` |
| `hashlib` | `hashlib` |
| `pathlib` | `PurePosixPath` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/extractors/python_extractor.py"]
    n1["src/llm_wiki_cli/services/knowledge_storage.py"]
    n2["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n3["src/llm_wiki_cli/services/lint_service.py"]
    n4["src/llm_wiki_cli/services/module_coverage.py"]
    n5["src/llm_wiki_cli/services/python_imports.py"]
    n6["src/llm_wiki_cli/services/source_selection.py"]
    n7["src/llm_wiki_cli/services/source_snapshot.py"]
    n2 --> n1
    n3 --> n4
    n3 --> n6
    n3 --> n7
    n4 --> n0
    n4 --> n1
    n4 --> n2
    n4 --> n5
    n4 --> n6
    n4 --> n7
    n7 --> n6
    click n0 "../modules/python_extractor.md"
    click n1 "../modules/knowledge_storage.md"
    click n2 "../modules/knowledge_storage_io.md"
    click n3 "../modules/lint_service.md"
    click n4 "../modules/module_coverage.md"
    click n5 "../modules/python_imports.md"
    click n6 "../modules/source_selection.md"
    click n7 "../modules/source_snapshot.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [lint_service](../modules/lint_service.md) |
| Outbound | [python_extractor](../modules/python_extractor.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [python_imports](../modules/python_imports.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_no_implementation` | `(tree: ast.Module) -> bool` | — | — |
| `_package_binding_is_clear` | `(tree: ast.Module, child: str) -> bool` | — | Reject explicit child bindings, dynamic exports and executable setup. |
| `_alias_import` | `(tree: ast.Module, name: str) -> tuple[str, str, str]` | — | — |
| `classify_uncovered_python_sources` | `(snapshot: SourceSnapshot, inventory: Mapping, paths: Iterable[str]) -> dict[str, dict]` | — | Explain only proven omissions; all unavailable proof stays uncovered. |
