# _BindingAnalyzer

**Location:** `src/llm_wiki_cli/extractors/python_bindings.py:326`
**Kind:** Class
**Bases:** —
**Module:** [python_bindings](../modules/python_bindings.md)

## Description

_Auto-generated from `_BindingAnalyzer` in `src/llm_wiki_cli/extractors/python_bindings.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(tree)` | — | — |
| `function` | `(node, closure: set[str], class_name: str \| None = None)` | — | — |
| `static_method` | `(node) -> bool` | — | — |
| `constructor` | `(node, env)` | — | — |
| `call_binding` | `(node, env)` | — | — |
| `helper_path` | `(node, env)` | — | — |
| `namespace_value` | `(node, env)` | — | — |
| `mutator_value` | `(node, env)` | — | — |
| `invalidate_target` | `(binding, env, member = '*')` | — | — |
| `invalidate_names` | `(names, env)` | — | — |
| `invalidate_members` | `(node, env)` | — | — |
| `expression` | `(node, env: dict, closure: set[str], *, capture = True)` | — | — |
| `block` | `(body, env: dict, closure: set[str], *, capture: bool, module: bool = False)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_BindingAnalyzer (src/llm_wiki_cli/extractors/python_bindings.py)"]
    n1["analyze_python_bindings (src/llm_wiki_cli/extractors/python_bindings.py)"]
    n1 --> n0
    click n0 "../modules/python_bindings.md"
    click n1 "../modules/python_bindings.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [python_bindings](../modules/python_bindings.md) | 13 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `analyze_python_bindings` | call | [python_bindings](../modules/python_bindings.md) | 1 |
