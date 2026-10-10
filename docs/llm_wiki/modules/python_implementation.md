# python_implementation Module

**Path:** `src/llm_wiki_cli/services/python_implementation.py`

## Description

Bounded executable-syntax observations from an already captured Python AST.

No source is opened or application imported here. Available digests describe
captured syntax, never dependencies, prose correctness, or runtime equivalence.

## Imports

| Source | Symbols |
|--------|---------|
| `.analysis_capture` | `_CapturedAnalysis` |
| `__future__` | `annotations` |
| `ast` | `ast` |
| `collections` | `Counter` |
| `collections.abc` | `Mapping` |
| `hashlib` | `hashlib` |
| `io` | `io` |
| `json` | `json` |
| `math` | `math` |
| `pathlib` | `PurePosixPath` |
| `platform` | `platform` |
| `re` | `re` |
| `sys` | `sys` |
| `tokenize` | `tokenize` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/extractors/python_extractor.py"]
    n1["src/llm_wiki_cli/services/analysis_capture.py"]
    n2["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n3["src/llm_wiki_cli/services/extraction_service.py"]
    n4["src/llm_wiki_cli/services/implementation_evidence.py"]
    n5["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n6["src/llm_wiki_cli/services/maintenance_evidence.py"]
    n7["src/llm_wiki_cli/services/maintenance_service.py"]
    n8["src/llm_wiki_cli/services/maintenance_status.py"]
    n9["src/llm_wiki_cli/services/python_implementation.py"]
    n10["src/llm_wiki_cli/services/task_context_v2.py"]
    n11["src/llm_wiki_cli/services/task_implementation.py"]
    n0 --> n9
    n2 --> n3
    n2 --> n8
    n2 --> n9
    n3 --> n0
    n3 --> n1
    n3 --> n9
    n4 --> n9
    n5 --> n1
    n5 --> n9
    n6 --> n4
    n6 --> n9
    n7 --> n5
    n7 --> n6
    n7 --> n8
    n7 --> n9
    n8 --> n3
    n8 --> n4
    n8 --> n6
    n8 --> n7
    n8 --> n9
    n9 --> n1
    n10 --> n2
    n10 --> n3
    n10 --> n4
    n10 --> n8
    n10 --> n9
    n10 --> n11
    n11 --> n4
    n11 --> n9
    click n0 "../modules/python_extractor.md"
    click n1 "../modules/analysis_capture.md"
    click n2 "../modules/documentation_query_builder.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/implementation_evidence.md"
    click n5 "../modules/knowledge_orchestration.md"
    click n6 "../modules/maintenance_evidence.md"
    click n7 "../modules/maintenance_service.md"
    click n8 "../modules/maintenance_status.md"
    click n9 "../modules/python_implementation.md"
    click n10 "../modules/task_context_v2.md"
    click n11 "../modules/task_implementation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [python_extractor](../modules/python_extractor.md) |
| Inbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [implementation_evidence](../modules/implementation_evidence.md) |
| Inbound | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| Inbound | [maintenance_evidence](../modules/maintenance_evidence.md) |
| Inbound | [maintenance_service](../modules/maintenance_service.md) |
| Inbound | [maintenance_status](../modules/maintenance_status.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Inbound | [task_implementation](../modules/task_implementation.md) |
| Outbound | [analysis_capture](../modules/analysis_capture.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `canonical_bytes` | `(value: Any) -> bytes` | — | — |
| `_digest` | `(value: Any) -> str` | — | — |
| `analysis_identity` | `(captured: object) -> str \| None` | — | Bind only issuer-owned surrounding code/runtime and normalization config. |
| `producer` | `(analysis_hash: str \| None, *, language = 'python') -> dict[str, str] \| None` | — | — |
| `comparison_id` | `(value: Mapping[str, Any]) -> str` | — | — |
| `coordinate_supported` | `(coordinate: Mapping[str, Any], scope: str) -> bool` | — | — |
| `_docstring` | `(node: ast.AST) -> str \| None` | — | — |
| `_scalar` | `(value: Any) -> Any` | — | — |
| `_normalize` | `(value: Any) -> Any` | — | — |
| `_declarations` | `(tree: ast.AST, path: str)` | — | — |
| `_documentation` | `(node: ast.AST) -> list[dict[str, Any]]` | — | — |
| `_evidence` | `(node: ast.AST \| None, coordinate: dict[str, Any], scope: str, source_hash: str \| None, configured: dict[str, str], reason: str \| None) -> dict[str, Any]` | — | — |
| `capture` | `(tree: ast.Module \| None, data: bytes \| None, source_path: str, *, configured: dict[str, str] \| None, reason: str \| None = None, parsed_source: str \| None = None) -> dict[str, Any]` | — | Capture per-file rows from the same tree/bytes used by extraction. |
| `envelope` | `(files: Mapping[str, dict]) -> dict[str, Any]` | — | — |
