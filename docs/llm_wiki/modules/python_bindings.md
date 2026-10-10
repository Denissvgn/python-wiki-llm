# python_bindings Module

**Path:** `src/llm_wiki_cli/extractors/python_bindings.py`

## Description

Conservative syntax-only binding facts for captured Python calls.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `ast` | `ast` |
| `builtins` | `builtins` |
| `collections` | `Counter` |
| `copy` | `deepcopy` |
| `dataclasses` | `dataclass`, `field` |
| `sys` | `sys` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/extractors/python_bindings.py"]
    n1["src/llm_wiki_cli/extractors/python_extractor.py"]
    n2["src/llm_wiki_cli/services/extraction_service.py"]
    n3["src/llm_wiki_cli/services/python_calls.py"]
    n1 --> n0
    n2 --> n0
    n2 --> n1
    n2 --> n3
    n3 --> n0
    click n0 "../modules/python_bindings.md"
    click n1 "../modules/python_extractor.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/python_calls.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [python_extractor](../modules/python_extractor.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [python_calls](../modules/python_calls.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_ClassNamespaceEffects](../entities/ClassNamespaceEffects.md) | 224 | `ast.NodeVisitor` | Collect executed namespace effects, retaining explicit scope boundaries. |
| [_ScopeNames](../entities/ScopeNames.md) | 1125 | `ast.NodeVisitor` | — |
| [PythonBindings](../entities/PythonBindings.md) | 1268 | — | — |
| [_BindingState](../entities/BindingState.md) | 1275 | — | Private related graph; one deepcopy preserves receiver/mutator aliases. |
| [_BindingAnalyzer](../entities/BindingAnalyzer.md) | 1292 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_unresolved` | `(node, reason)` | — | — |
| `_callee_path` | `(node)` | — | — |
| `_module_declarations` | `(tree)` | — | — |
| `_module_classes` | `(tree)` | — | — |
| `_builtin_getter` | `(binding)` | — | — |
| `_builtin_dict` | `(binding)` | — | — |
| `_builtin_namespace_factory` | `(binding)` | — | — |
| `_builtin_attribute_mutator` | `(binding)` | — | — |
| `_known_callable` | `(binding)` | — | — |
| `_dict_namespace` | `(target, *, qualified = True)` | — | — |
| `_namespace_lookup` | `(target, member)` | — | — |
| `_getter_method` | `(node)` | — | — |
| `_namespace_mutated_names` | `(method, args, keywords, qualified)` | — | — |
| `_dispatch_facts` | `(tree, module)` | — | Qualify only allocation/dispatch syntax actually present in this AST. |
| `_lookup` | `(env: dict, name: str) -> dict` | — | — |
| `_target_names` | `(node: ast.AST) -> set[str]` | — | — |
| `_definition_expressions` | `(node, *, annotations_eager = True)` | — | — |
| `_walrus_names` | `(node: ast.AST) -> set[str]` | — | Find containing-scope writes without entering deferred callable bodies. |
| `_scope_names` | `(body: list[ast.stmt]) -> _ScopeNames` | — | — |
| `_parameters` | `(args: ast.arguments) -> set[str]` | — | — |
| `import_bindings` | `(node: ast.Import \| ast.ImportFrom) -> dict[str, dict]` | — | — |
| `_import_path` | `(binding, members = ())` | — | — |
| `_import_contains` | `(prefix, owner)` | — | — |
| `_import_mutation_affects` | `(constructor, member, mutation)` | — | — |
| `_public_binding` | `(value, *, constructed = False)` | — | Publish only existing public fact shapes; keep owner graphs private. |
| `analyze_python_bindings` | `(tree: ast.Module) -> PythonBindings` | — | — |
| `valid_python_constructor_facts` | `(inventory, *, require_capability = True)` | — | Validate published syntax facts without reading or parsing source. |
