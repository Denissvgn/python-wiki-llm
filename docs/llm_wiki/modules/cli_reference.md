# cli_reference Module

**Path:** `src/llm_wiki_cli/services/cli_reference.py`

## Description

Deterministic CLI reference data and inert Markdown from parser declarations.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `_provider_package_identity` |
| `..cli_declarations` | `build_cli_parser` |
| `.knowledge_storage_io` | `read_guarded` |
| `__future__` | `annotations` |
| `argparse` | `argparse` |
| `collections.abc` | `Mapping` |
| `functools` | `lru_cache` |
| `html` | `html` |
| `importlib` | `resources` |
| `json` | `json` |
| `llm_wiki_engine.knowledge_evidence` | `hash_json` |
| `math` | `math` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/__init__.py"]
    n1["src/llm_wiki_cli/api.py"]
    n2["src/llm_wiki_cli/cli_declarations.py"]
    n3["src/llm_wiki_cli/commands/reference_cmd.py"]
    n4["src/llm_wiki_cli/services/behavior_reference.py"]
    n5["src/llm_wiki_cli/services/cli_reference.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n7["src/llm_wiki_cli/services/reference_providers.py"]
    n8["src/llm_wiki_engine/knowledge_evidence.py"]
    n1 --> n4
    n1 --> n5
    n2 --> n0
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n4 --> n5
    n4 --> n6
    n4 --> n8
    n5 --> n0
    n5 --> n2
    n5 --> n6
    n5 --> n8
    n7 --> n4
    n7 --> n5
    n7 --> n8
    click n0 "../modules/llm_wiki_cli___init__.md"
    click n1 "../modules/api.md"
    click n2 "../modules/cli_declarations.md"
    click n3 "../modules/reference_cmd.md"
    click n4 "../modules/behavior_reference.md"
    click n5 "../modules/cli_reference.md"
    click n6 "../modules/knowledge_storage_io.md"
    click n7 "../modules/reference_providers.md"
    click n8 "../modules/knowledge_evidence.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [reference_cmd](../modules/reference_cmd.md) |
| Inbound | [behavior_reference](../modules/behavior_reference.md) |
| Inbound | [reference_providers](../modules/reference_providers.md) |
| Outbound | [llm_wiki_cli___init__](../modules/llm_wiki_cli___init__.md) |
| Outbound | [cli_declarations](../modules/cli_declarations.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [CLIReferenceError](../entities/CLIReferenceError.md) | 45 | `ValueError` | CLI declarations or supplied reference data violate the portable contract. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_text` | `(value: object) -> str \| None` | — | — |
| `_notes` | `(owner: object) -> list[str]` | — | — |
| `_value` | `(value: object, depth: int = 0) -> Any` | — | — |
| `_custom_symbol` | `(value: object) -> str` | — | — |
| `_symbol` | `(value: object) -> str \| None` | — | — |
| `_argument` | `(action, identity, group, exclusive)` | — | — |
| `_command` | `(parser, name, path, *, help_text = None, deprecated = False, seen = None)` | — | — |
| `build_cli_contract` | `(parser: argparse.ArgumentParser, *, package: Mapping[str, Any], program: str) -> dict[str, Any]` | — | Capture declarations without parsing arguments or executing application code. |
| `get_cli_contract` | `() -> dict[str, Any]` | — | Describe the installed llm-wiki CLI from its declarations, without loading commands. |
| `_schema` | `() -> dict[str, Any]` | `@lru_cache(maxsize=1)` | — |
| `_json_tree` | `(value: object, depth: int = 0, budget = None) -> None` | — | — |
| `_matches_type` | `(value, kind)` | — | — |
| `_validate_schema` | `(value, rule, root, field)` | — | — |
| `_validate_command` | `(node, expected_path, program)` | — | — |
| `validate_cli_contract` | `(contract: object) -> None` | — | Validate closed portable reference data and its complete commitment. |
| `_pairs` | `(pairs)` | — | — |
| `parse_cli_contract` | `(raw: bytes \| str) -> dict[str, Any]` | — | Validate exact observed UTF-8 JSON bytes without reopening their source. |
| `load_cli_contract` | `(path: str \| Path) -> dict[str, Any]` | — | Read one guarded contract file as data; never load an application CLI. |
| `_prose` | `(value: str) -> str` | — | — |
| `_code` | `(value: object) -> str` | — | — |
| `render_cli_reference` | `(contract: object) -> str` | — | Render validated metadata deterministically, including hidden declarations. |
