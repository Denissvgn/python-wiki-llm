# PublicationConfigError

**Location:** `src/llm_wiki_cli/services/publication_config.py:50`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [publication_config](../modules/publication_config.md)

## Description

A field-specific failure in consumer-owned publication configuration.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PublicationConfigError (src/llm_wiki_cli/services/publication_config.py)"]
    n1["ValueError"]
    n2["_array (src/llm_wiki_cli/services/publication_config.py)"]
    n3["_check_path (src/llm_wiki_cli/services/publication_config.py)"]
    n4["_choice (src/llm_wiki_cli/services/publication_config.py)"]
    n5["_consumer_root (src/llm_wiki_cli/services/publication_config.py)"]
    n6["_content_profile (src/llm_wiki_cli/services/publication_config.py)"]
    n7["_content_repository_url (src/llm_wiki_cli/services/publication_config.py)"]
    n8["_content_source_path (src/llm_wiki_cli/services/publication_config.py)"]
    n9["_dependency (src/llm_wiki_cli/services/publication_config.py)"]
    n10["_json_object (src/llm_wiki_cli/services/publication_config.py)"]
    n11["_object (src/llm_wiki_cli/services/publication_config.py)"]
    n12["_public_content_path (src/llm_wiki_cli/services/publication_config.py)"]
    n13["_reference_providers (src/llm_wiki_cli/services/publication_config.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    n13 --> n0
    click n0 "../modules/publication_config.md"
    click n2 "../modules/publication_config.md"
    click n3 "../modules/publication_config.md"
    click n4 "../modules/publication_config.md"
    click n5 "../modules/publication_config.md"
    click n6 "../modules/publication_config.md"
    click n7 "../modules/publication_config.md"
    click n8 "../modules/publication_config.md"
    click n9 "../modules/publication_config.md"
    click n10 "../modules/publication_config.md"
    click n11 "../modules/publication_config.md"
    click n12 "../modules/publication_config.md"
    click n13 "../modules/publication_config.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [publication_config](../modules/publication_config.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_array` | call | [publication_config](../modules/publication_config.md) | 1 |
| `_check_path` | call | [publication_config](../modules/publication_config.md) | 2 |
| `_choice` | call | [publication_config](../modules/publication_config.md) | 1 |
| `_consumer_root` | call | [publication_config](../modules/publication_config.md) | 3 |
| `_content_profile` | call | [publication_config](../modules/publication_config.md) | 9 |
| `_content_repository_url` | call | [publication_config](../modules/publication_config.md) | 1 |
| `_content_source_path` | call | [publication_config](../modules/publication_config.md) | 3 |
| `_dependency` | call | [publication_config](../modules/publication_config.md) | 8 |
| `_json_object` | call | [publication_config](../modules/publication_config.md) | 1 |
| `_object` | call | [publication_config](../modules/publication_config.md) | 2 |
| `_public_content_path` | call | [publication_config](../modules/publication_config.md) | 2 |
| `_reference_providers` | call | [publication_config](../modules/publication_config.md) | 3 |

> References: showing 12 of 19 logical references; 7 omitted by the 12-row generated summary limit.
