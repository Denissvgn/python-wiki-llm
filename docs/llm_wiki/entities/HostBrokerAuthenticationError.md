# HostBrokerAuthenticationError

**Location:** `src/llm_wiki_cli/services/calibration/host_broker.py:23`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [host_broker](../modules/host_broker.md)

## Description

Raised when external broker authentication is unavailable or invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HostBrokerAuthenticationError (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n1["ValueError"]
    n2["HostBrokerAuthenticationUnavailable (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n3["src/llm_wiki_cli/api.py"]
    n4["src/llm_wiki_cli/services/calibration/controller.py"]
    n5["_require_bounded_text (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n6["_require_hash (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n7["HostBrokerAuthenticationProof.__post_init__ (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n8["require_attestation_authentication (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n9["require_receipt_authentication (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/host_broker.md"
    click n2 "../modules/host_broker.md"
    click n3 "../modules/api.md"
    click n4 "../modules/controller.md"
    click n5 "../modules/host_broker.md"
    click n6 "../modules/host_broker.md"
    click n7 "../modules/host_broker.md"
    click n8 "../modules/host_broker.md"
    click n9 "../modules/host_broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [host_broker](../modules/host_broker.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `HostBrokerAuthenticationUnavailable` | [host_broker](../modules/host_broker.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `controller` | import | [controller](../modules/controller.md) | — |
| `_require_bounded_text` | call | [host_broker](../modules/host_broker.md) | 1 |
| `_require_hash` | call | [host_broker](../modules/host_broker.md) | 1 |
| `HostBrokerAuthenticationProof.__post_init__` | call | [host_broker](../modules/host_broker.md) | 4 |
| `require_attestation_authentication` | call | [host_broker](../modules/host_broker.md) | 3 |
| `require_receipt_authentication` | call | [host_broker](../modules/host_broker.md) | 3 |
