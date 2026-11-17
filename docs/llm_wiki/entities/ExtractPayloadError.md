# ExtractPayloadError

**Location:** `src/llm_wiki_cli/services/extract_format.py:102`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [extract_format](../modules/extract_format.md)

## Description

An extract payload does not follow its format.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ExtractPayloadError (src/llm_wiki_cli/services/extract_format.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n3["_check_data_flow_details (src/llm_wiki_cli/services/extract_format.py)"]
    n4["_check_entrypoints (src/llm_wiki_cli/services/extract_format.py)"]
    n5["_check_inventory (src/llm_wiki_cli/services/extract_format.py)"]
    n6["_check_limitations (src/llm_wiki_cli/services/extract_format.py)"]
    n7["_check_unsupported (src/llm_wiki_cli/services/extract_format.py)"]
    n8["_fields (src/llm_wiki_cli/services/extract_format.py)"]
    n9["_ids (src/llm_wiki_cli/services/extract_format.py)"]
    n10["_mapping (src/llm_wiki_cli/services/extract_format.py)"]
    n11["_portable (src/llm_wiki_cli/services/extract_format.py)"]
    n12["_sequence (src/llm_wiki_cli/services/extract_format.py)"]
    n13["validate_extract_payload (src/llm_wiki_cli/services/extract_format.py)"]
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
    click n0 "../modules/extract_format.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/extract_format.md"
    click n4 "../modules/extract_format.md"
    click n5 "../modules/extract_format.md"
    click n6 "../modules/extract_format.md"
    click n7 "../modules/extract_format.md"
    click n8 "../modules/extract_format.md"
    click n9 "../modules/extract_format.md"
    click n10 "../modules/extract_format.md"
    click n11 "../modules/extract_format.md"
    click n12 "../modules/extract_format.md"
    click n13 "../modules/extract_format.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extract_format](../modules/extract_format.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `_check_data_flow_details` | call | [extract_format](../modules/extract_format.md) | 9 |
| `_check_entrypoints` | call | [extract_format](../modules/extract_format.md) | 2 |
| `_check_inventory` | call | [extract_format](../modules/extract_format.md) | 5 |
| `_check_limitations` | call | [extract_format](../modules/extract_format.md) | 3 |
| `_check_unsupported` | call | [extract_format](../modules/extract_format.md) | 2 |
| `_fields` | call | [extract_format](../modules/extract_format.md) | 3 |
| `_ids` | call | [extract_format](../modules/extract_format.md) | 1 |
| `_mapping` | call | [extract_format](../modules/extract_format.md) | 1 |
| `_portable` | call | [extract_format](../modules/extract_format.md) | 1 |
| `_sequence` | call | [extract_format](../modules/extract_format.md) | 1 |
| `validate_extract_payload` | call | [extract_format](../modules/extract_format.md) | 5 |
