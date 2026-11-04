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
    n0["src"]
    n1["src/llm_wiki_cli/services/python_implementation.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/python_implementation.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (13) |
| Outbound | `src` (1) |

> All 14 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

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
