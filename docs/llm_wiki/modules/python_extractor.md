# python_extractor Module

**Path:** `src/llm_wiki_cli/extractors/python_extractor.py`

## Description

Extracts Python declarations, bindings and optional implementation observations
with the built-in AST parser. Optional path diagnostics are owned by the scan
that reads and parses each selected file: syntax, decoding and read failures
retain a file scope, while successful parsing without documentable content
remains distinct from failure. The collector is reset for every extraction and
is disabled for ordinary calls; diagnostic collection retains its legacy inventory behavior. Explicit empty
retention returns the parser-produced record with an attributable `retained_empty`
outcome; module aliases are never promoted merely because emptiness was requested.

Lexical imports are collected inside class bodies, methods and nested scopes without re-entering declaration extraction. Top-level class imports are eager; enclosing function bodies defer them, and recognized TYPE_CHECKING guards retain type-only scope. Import records and location sidecars keep their existing shape.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `build_gitignore_matcher` |
| `..services.imports` | `build_module_path_resolver` |
| `..services.python_calls` | `PYTHON_LEXICAL_FUNCTIONS_SCHEMA` |
| `..services.python_implementation` | `capture`, `envelope`, `producer` |
| `..services.python_observations` | `DATA_EFFECT_OBSERVATIONS_SCHEMA`, `IMPORT_LOCATION_OBSERVATIONS_SCHEMA`, `data_effect_sidecar`, `import_sidecar` |
| `.common` | `IMPORT_SCOPE_DEFERRED`, `IMPORT_SCOPE_TYPE_CHECKING`, `discover_source_files` |
| `.fastapi_contracts` | `extract_fastapi_declarations` |
| `.python_bindings` | `CONSTRUCTOR_FACTS_VERSION`, `analyze_python_bindings` |
| `.python_contracts` | `class_kind`, `explicit_type_alias`, `expression_to_str`, `extract_class_attributes`, `extract_enum_attributes`, `extract_model_config`, `extract_parameters`, `extract_validator`, `finalize_inventory_model_kinds`, `finalize_model_kinds`, `inferred_type_alias`, `is_pydantic_model`, `is_typed_dict`, `type_alias_record` |
| `__future__` | `annotations` |
| `ast` | `ast` |
| `collections` | `Counter` |
| `pathlib` | `Path` |
| `symtable` | `symtable` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/config.py"]
    n1["src/llm_wiki_cli/extractors/common.py"]
    n2["src/llm_wiki_cli/extractors/fastapi_contracts.py"]
    n3["src/llm_wiki_cli/extractors/python_bindings.py"]
    n4["src/llm_wiki_cli/extractors/python_contracts.py"]
    n5["src/llm_wiki_cli/extractors/python_extractor.py"]
    n6["src/llm_wiki_cli/services/extraction_service.py"]
    n7["src/llm_wiki_cli/services/imports.py"]
    n8["src/llm_wiki_cli/services/module_coverage.py"]
    n9["src/llm_wiki_cli/services/python_calls.py"]
    n10["src/llm_wiki_cli/services/python_implementation.py"]
    n11["src/llm_wiki_cli/services/python_observations.py"]
    n1 --> n0
    n5 --> n0
    n5 --> n1
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n7
    n5 --> n9
    n5 --> n10
    n5 --> n11
    n6 --> n0
    n6 --> n1
    n6 --> n3
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n9
    n6 --> n10
    n6 --> n11
    n7 --> n0
    n7 --> n1
    n8 --> n5
    n9 --> n3
    n9 --> n7
    click n0 "../modules/config.md"
    click n1 "../modules/common.md"
    click n2 "../modules/fastapi_contracts.md"
    click n3 "../modules/python_bindings.md"
    click n4 "../modules/python_contracts.md"
    click n5 "../modules/python_extractor.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/imports.md"
    click n8 "../modules/module_coverage.md"
    click n9 "../modules/python_calls.md"
    click n10 "../modules/python_implementation.md"
    click n11 "../modules/python_observations.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [module_coverage](../modules/module_coverage.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [common](../modules/common.md) |
| Outbound | [fastapi_contracts](../modules/fastapi_contracts.md) |
| Outbound | [python_bindings](../modules/python_bindings.md) |
| Outbound | [python_contracts](../modules/python_contracts.md) |
| Outbound | [imports](../modules/imports.md) |
| Outbound | [python_calls](../modules/python_calls.md) |
| Outbound | [python_implementation](../modules/python_implementation.md) |
| Outbound | [python_observations](../modules/python_observations.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_DataEffectVisitor](../entities/DataEffectVisitor.md) | 523 | `ast.NodeVisitor` | — |
| [ComponentVisitor](../entities/ComponentVisitor.md) | 1131 | `ast.NodeVisitor` | — |
| [_LexicalBody](../entities/LexicalBody.md) | 1515 | `ast.NodeVisitor` | Current-body writes/calls, without entering deferred definitions. |
| [PythonExtractor](../entities/PythonExtractor.md) | 1889 | — | Extractor for Python source files using the built-in :mod:`ast` module. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_annotation_to_str` | `(node) -> str` | — | Convert an AST annotation node to a readable string. |
| `_default_to_str` | `(node) -> str` | — | Convert a default-value AST node to a readable string. |
| `_simple_reference_to_str` | `(node) -> str` | — | Return a dotted reference for simple name/attribute expressions. |
| `_is_simple_subscript_slice` | `(node) -> bool` | — | — |
| `_summarize_expression` | `(node) -> dict[str, str]` | — | Summarize an AST expression without retaining arbitrary source text. |
| `_extract_decorators` | `(node) -> list[str]` | — | Extract decorator names from a node. |
| `_call_arguments` | `(node: ast.Call) -> dict` | — | — |
| `_call_record` | `(node: ast.Call, *, include_arguments: bool = False) -> dict \| None` | — | Build a call record from an ``ast.Call`` node. |
| `_extract_calls` | `(node, *, binding_facts: dict[int, dict] \| None = None, bound_calls: list[dict] \| None = None) -> list[dict]` | — | Collect direct call targets within a function/method body. |
| `_bound_import_name` | `(alias: ast.alias, *, from_import: bool = False) -> str` | — | — |
| `_iter_binding_targets` | `(target) -> list[ast.AST]` | — | — |
| `_target_bound_names` | `(target) -> set[str]` | — | — |
| `_argument_bound_names` | `(args: ast.arguments) -> set[str]` | — | — |
| `_extract_module_globals` | `(tree: ast.Module) -> set[str]` | — | — |
| `_import_alias_target` | `(alias: ast.alias, *, module: str = '') -> tuple[str, str] \| None` | — | — |
| `_import_aliases_from_statement` | `(statement) -> dict[str, str]` | — | — |
| `_extract_import_aliases` | `(tree: ast.Module) -> dict[str, str]` | — | — |
| `_normalize_reference` | `(name: str, import_aliases: dict[str, str]) -> str` | — | — |
| `_open_mode` | `(node: ast.Call) -> str \| None` | — | — |
| `_classify_open_call` | `(node: ast.Call) -> str \| None` | — | — |
| `_classify_boundary_call` | `(normalized: str, node: ast.Call) -> str \| None` | — | — |
| `_boundary_call_record` | `(node: ast.Call, import_aliases: dict[str, str]) -> dict \| None` | — | — |
| `_environment_subscript_record` | `(node: ast.Subscript, import_aliases: dict[str, str], kind: str) -> dict \| None` | — | — |
| `_collect_function_scope` | `(node) -> tuple[set[str], set[str], dict[str, str]]` | — | — |
| `_attribute_read_name` | `(node: ast.Attribute) -> str` | — | — |
| `_write_record` | `(target, global_declarations: set[str]) -> dict \| None` | — | — |
| `_extract_data_effects` | `(node, params: list[dict], module_globals: set[str], module_import_aliases: dict[str, str], return_annotation: str, *, coverage: dict[str, dict] \| None = None) -> dict` | — | — |
| `_assign_target_name` | `(targets) -> str` | — | Name an assignment's target: ``app`` in ``app = Flask(...)``. |
| `_module_call_record` | `(call: ast.Call, target: str = '') -> dict \| None` | — | Build a module-level side-effect record, optionally with its bound name. |
| `_module_mutation_record` | `(statement: ast.Assign) -> dict \| None` | — | Record an import-time assignment that mutates state outside the module. |
| `_is_self_module_alias` | `(statement) -> bool` | — | Detect ``sys.modules[__name__] = other`` — a module replacing itself. |
| `module_alias_target` | `(tree: ast.Module) -> str` | — | Return the imported binding of a static self-module shim, else ``""``. |
| `_static_import_bindings` | `(statement: ast.AST) -> dict[str, str] \| None` | — | Capture direct import spellings; no module loading or attribute lookup. |
| `_static_type_checking_block` | `(statement: ast.AST, bindings: dict[str, str]) -> bool` | — | Recognize import-only mirrors behind a directly bound typing guard. |
| `_import_time_body` | `(statement, type_checking_names: set[str]) -> list` | — | Return the nested statements of *statement* that run at import time. |
| `_collect_module_calls` | `(body, calls: list[dict], type_checking_names: set[str]) -> None` | — | — |
| `_extract_module_calls` | `(tree: ast.Module) -> list[dict]` | — | Collect module-scope executable side effects (import-time work). |
| `_extract_function_info` | `(node, deep: bool = False, module_globals: set[str] \| None = None, module_import_aliases: dict[str, str] \| None = None, *, omit_method_receiver: bool = False, data_effect_observations: list[dict] \| None = None, observation_symbol: str \| None = None, call_binding_facts: dict[int, dict] \| None = None) -> dict` | — | Extract full function/method info from a FunctionDef or AsyncFunctionDef. |
| `_extract_class_attributes` | `(node, module_import_aliases: dict[str, str] \| None = None) -> list[dict]` | — | Extract annotated attributes from a class body (Pydantic fields, dataclass fields, etc.). |
| `_string_list` | `(node) -> list[str]` | — | Return the string constants of a ``List``/``Tuple`` literal (else empty). |
| `_safe_name_or_attribute` | `(node) -> dict \| None` | — | — |
| `_safe_constant_value` | `(node) -> dict \| None` | — | Summarize small static constant values without executing user code. |
| `_is_main_guard` | `(test) -> bool` | — | Detect an ``if __name__ == "__main__"`` test node. |
| `_collect_type_checking_names` | `(tree: ast.Module) -> set[str]` | — | Names bound to ``typing.TYPE_CHECKING`` anywhere in *tree*. |
| `_is_type_checking_test` | `(test, names: set[str]) -> bool` | — | Detect an ``if TYPE_CHECKING:`` / ``if typing.TYPE_CHECKING:`` test. |
| `_closed_lexical_functions` | `(tree, source, filepath, visitor, bindings, effects)` | — | Attest an unescaped, closure-free direct-helper subset without execution. |
| `_scan_python_files` | `(src_dir: str, deep: bool = False, only_files: list[str] \| None = None, include_empty: bool = False, source_files: list[str] \| None = None, data_effect_observations: list[dict] \| None = None, import_location_observations: list[dict] \| None = None, defer_inventory_model_kinds: bool = False, implementation_observations: dict[str, dict] \| None = None, implementation_analysis_hash: str \| None = None, path_outcomes: dict[str, dict] \| None = None, retain_empty_paths: tuple[str, ...] = ()) -> dict` | — | Scan Python files under *src_dir* and return a raw inventory dict. |