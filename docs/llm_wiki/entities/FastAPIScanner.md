# _FastAPIScanner

**Location:** `src/llm_wiki_cli/extractors/fastapi_contracts.py:288`
**Kind:** Class
**Bases:** `ast.NodeVisitor`
**Module:** [fastapi_contracts](../modules/fastapi_contracts.md)

## Description

_Auto-generated from `_FastAPIScanner` in `src/llm_wiki_cli/extractors/fastapi_contracts.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(tree: ast.Module, filepath: str)` | — | — |
| `scope` | `() -> str` | `@property` | — |
| `_qualname` | `(name: str) -> str` | — | — |
| `_record_binding` | `(target: ast.AST, value: ast.AST, line: int) -> None` | — | — |
| `visit_Assign` | `(node: ast.Assign) -> None` | — | — |
| `visit_AnnAssign` | `(node: ast.AnnAssign) -> None` | — | — |
| `visit_Expr` | `(node: ast.Expr) -> None` | — | — |
| `_visit_function` | `(node: ast.FunctionDef \| ast.AsyncFunctionDef) -> None` | — | — |
| `visit_FunctionDef` | `(node: ast.FunctionDef) -> None` | — | — |
| `visit_AsyncFunctionDef` | `(node: ast.AsyncFunctionDef) -> None` | — | — |
| `visit_ClassDef` | `(node: ast.ClassDef) -> None` | — | — |
| `_visit_conditional` | `(node: ast.AST) -> None` | — | — |
| `result` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_FastAPIScanner (src/llm_wiki_cli/extractors/fastapi_contracts.py)"]
    n1["ast.NodeVisitor"]
    n2["extract_fastapi_declarations (src/llm_wiki_cli/extractors/fastapi_contracts.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/fastapi_contracts.md"
    click n2 "../modules/fastapi_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [fastapi_contracts](../modules/fastapi_contracts.md) | 13 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ast.NodeVisitor` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `extract_fastapi_declarations` | call | [fastapi_contracts](../modules/fastapi_contracts.md) |
