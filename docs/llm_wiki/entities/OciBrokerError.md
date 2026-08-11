# OciBrokerError

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:133`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [broker](../modules/broker.md)

## Description

Raised when OCI configuration or dispatch evidence is unsafe.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["OciBrokerError (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["ValueError"]
    n2["_ResultArtifactError (src/llm_wiki_cli/services/calibration/broker.py)"]
    n3["_absolute_regular_directory (src/llm_wiki_cli/services/calibration/broker.py)"]
    n4["_absolute_regular_file (src/llm_wiki_cli/services/calibration/broker.py)"]
    n5["_bounded_int (src/llm_wiki_cli/services/calibration/broker.py)"]
    n6["_bounded_text (src/llm_wiki_cli/services/calibration/broker.py)"]
    n7["_build_oci_run_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n8["_canonical_sha256 (src/llm_wiki_cli/services/calibration/broker.py)"]
    n9["_dispatch_container_name (src/llm_wiki_cli/services/calibration/broker.py)"]
    n10["_execute_container_command (src/llm_wiki_cli/services/calibration/broker.py)"]
    n11["_file_identity (src/llm_wiki_cli/services/calibration/broker.py)"]
    n12["_load_bounded_json_object (src/llm_wiki_cli/services/calibration/broker.py)"]
    n13["_LocalEgressCanary.__init__ (src/llm_wiki_cli/services/calibration/broker.py)"]
    n14["_LocalEgressCanary._run_host_control (src/llm_wiki_cli/services/calibration/broker.py)"]
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
    n14 --> n0
    click n0 "../modules/broker.md"
    click n2 "../modules/broker.md"
    click n3 "../modules/broker.md"
    click n4 "../modules/broker.md"
    click n5 "../modules/broker.md"
    click n6 "../modules/broker.md"
    click n7 "../modules/broker.md"
    click n8 "../modules/broker.md"
    click n9 "../modules/broker.md"
    click n10 "../modules/broker.md"
    click n11 "../modules/broker.md"
    click n12 "../modules/broker.md"
    click n13 "../modules/broker.md"
    click n14 "../modules/broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `_ResultArtifactError` | [broker](../modules/broker.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_absolute_regular_directory` | call | [broker](../modules/broker.md) | 3 |
| `_absolute_regular_file` | call | [broker](../modules/broker.md) | 4 |
| `_bounded_int` | call | [broker](../modules/broker.md) | 2 |
| `_bounded_text` | call | [broker](../modules/broker.md) | 2 |
| `_build_oci_run_command` | call | [broker](../modules/broker.md) | 2 |
| `_canonical_sha256` | call | [broker](../modules/broker.md) | 1 |
| `_dispatch_container_name` | call | [broker](../modules/broker.md) | 1 |
| `_execute_container_command` | call | [broker](../modules/broker.md) | 1 |
| `_file_identity` | call | [broker](../modules/broker.md) | 1 |
| `_load_bounded_json_object` | call | [broker](../modules/broker.md) | 2 |
| `_LocalEgressCanary.__init__` | call | [broker](../modules/broker.md) | 3 |
| `_LocalEgressCanary._run_host_control` | call | [broker](../modules/broker.md) | 2 |

> References: showing 12 of 67 logical references; 55 omitted by the 12-row generated summary limit.
