# HostBrokerAuthenticationUnavailable

**Location:** `src/llm_wiki_cli/services/calibration/host_broker.py:27`
**Kind:** Class
**Bases:** `HostBrokerAuthenticationError`
**Module:** [host_broker](../modules/host_broker.md)

## Description

Raised when no supported host-authenticator context is active.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HostBrokerAuthenticationUnavailable (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n1["HostBrokerAuthenticationError (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/services/calibration/controller.py"]
    n4["require_process_host_broker_authenticator (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n5["use_calibration_host_broker_authenticator (src/llm_wiki_cli/services/calibration/host_broker.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/host_broker.md"
    click n1 "../modules/host_broker.md"
    click n2 "../modules/api.md"
    click n3 "../modules/controller.md"
    click n4 "../modules/host_broker.md"
    click n5 "../modules/host_broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [host_broker](../modules/host_broker.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `HostBrokerAuthenticationError` | [host_broker](../modules/host_broker.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `controller` | import | [controller](../modules/controller.md) | — |
| `require_process_host_broker_authenticator` | call | [host_broker](../modules/host_broker.md) | 2 |
| `use_calibration_host_broker_authenticator` | call | [host_broker](../modules/host_broker.md) | 1 |
