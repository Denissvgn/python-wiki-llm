# publication_config Module

**Path:** `src/llm_wiki_cli/services/publication_config.py`

## Description

Portable consumer policy for read-only publication impact and review.

Whole-page dependencies use whole content commitments. Structural or semantic
facets require an exact native section with independently committed ownership.
Reference dependencies require an explicitly declared, non-executable provider.

## Imports

| Source | Symbols |
|--------|---------|
| `.concept_identity` | `ConceptIdentityError`, `validate_locator` |
| `.source_selection` | `SourceSelectionError`, `locate_exact_repository_path`, `path_is_link_or_reparse` |
| `.validation` | `portable_path_key`, `require_repository_relative_path` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `stat` | `stat` |
| `typing` | `Any` |
| `unicodedata` | `unicodedata` |
| `urllib.parse` | `quote`, `unquote` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/publication_cmd.py"]
    n1["src/llm_wiki_cli/services/concept_identity.py"]
    n2["src/llm_wiki_cli/services/publication_config.py"]
    n3["src/llm_wiki_cli/services/publication_contracts.py"]
    n4["src/llm_wiki_cli/services/publication_impact.py"]
    n5["src/llm_wiki_cli/services/publication_references.py"]
    n6["src/llm_wiki_cli/services/source_selection.py"]
    n7["src/llm_wiki_cli/services/validation.py"]
    n0 --> n2
    n0 --> n4
    n1 --> n7
    n2 --> n1
    n2 --> n6
    n2 --> n7
    n3 --> n1
    n3 --> n2
    n3 --> n7
    n4 --> n2
    n4 --> n3
    n4 --> n5
    n5 --> n2
    n6 --> n7
    click n0 "../modules/publication_cmd.md"
    click n1 "../modules/concept_identity.md"
    click n2 "../modules/publication_config.md"
    click n3 "../modules/publication_contracts.md"
    click n4 "../modules/publication_impact.md"
    click n5 "../modules/publication_references.md"
    click n6 "../modules/source_selection.md"
    click n7 "../modules/validation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [publication_cmd](../modules/publication_cmd.md) |
| Inbound | [publication_contracts](../modules/publication_contracts.md) |
| Inbound | [publication_impact](../modules/publication_impact.md) |
| Inbound | [publication_references](../modules/publication_references.md) |
| Outbound | [concept_identity](../modules/concept_identity.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [validation](../modules/validation.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [PublicationConfigError](../entities/PublicationConfigError.md) | 45 | `ValueError` | A field-specific failure in consumer-owned publication configuration. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_object` | `(value: object, field: str, required: set[str], optional: set[str] \| None = None) -> Mapping[str, Any]` | — | — |
| `_text` | `(value: object, field: str, maximum: int = 1024) -> str` | — | — |
| `_choice` | `(value: object, field: str, choices: set[str]) -> str` | — | — |
| `_array` | `(value: object, field: str, maximum: int, *, nonempty: bool = False) -> list[Any]` | — | — |
| `_relative_path` | `(value: object, field: str) -> str` | — | — |
| `_consumer_root` | `(value: str \| Path) -> Path` | — | — |
| `_check_path` | `(root: Path \| None, path: str, field: str, spellings: dict[tuple[str, ...], tuple[str, ...]]) -> None` | — | — |
| `publication_path` | `(root: Path, relative: str) -> Path` | — | Return a confined exact-case path, including a safely absent leaf. |
| `_section` | `(value: object, field: str) -> str` | — | — |
| `_dependency` | `(value: object, field: str, root: Path \| None, architecture_root: str, spellings: dict[tuple[str, ...], tuple[str, ...]], reference_providers: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_reference_providers` | `(value: object, root: Path \| None, spellings: dict[tuple[str, ...], tuple[str, ...]]) -> dict[str, dict[str, Any]]` | — | — |
| `validate_publication_config` | `(payload: Mapping[str, Any], *, consumer_root: str \| Path \| None) -> dict[str, Any]` | — | Validate detached policy; None checks imported policy without filesystem I/O. |
| `_json_object` | `(pairs: list[tuple[str, Any]]) -> dict[str, Any]` | — | — |
| `_reject_constant` | `(value: str) -> None` | — | — |
| `read_publication_json` | `(path: str \| Path, *, max_bytes: int = _MAX_CONFIG_BYTES) -> dict[str, Any]` | — | Read bounded regular JSON; callers confine its parent with publication_path. |
| `load_publication_config` | `(consumer_root: str \| Path, *, config_path: str \| Path = PUBLICATION_CONFIG_PATH) -> dict[str, Any]` | — | Load an explicit consumer's regular JSON config without following links. |
