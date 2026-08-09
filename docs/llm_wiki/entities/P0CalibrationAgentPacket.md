# P0CalibrationAgentPacket

**Location:** `src/llm_wiki_cli/services/calibration/controller.py:385`
**Kind:** Class
**Bases:** —
**Module:** [controller](../modules/controller.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One bounded, provider-neutral role packet.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `payload` | `dict[str, Any]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `from_dict` | `(payload: Mapping[str, Any]) -> 'P0CalibrationAgentPacket'` | `@classmethod` | — |
| `packet_id` | `() -> str` | `@property` | — |
| `role` | `() -> str` | `@property` | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `to_json` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["P0CalibrationAgentPacket (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1["build_calibration_agent_packet (src/llm_wiki_cli/api.py)"]
    n2["build_calibration_agent_packet (src/llm_wiki_cli/services/calibration/controller.py)"]
    n3["P0CalibrationAgentPacket.from_dict (src/llm_wiki_cli/services/calibration/controller.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/controller.md"
    click n1 "../modules/api.md"
    click n2 "../modules/controller.md"
    click n3 "../modules/controller.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [controller](../modules/controller.md) | 5 | `payload` |

### References

| Reference | Kind | Source |
|---|---|---|
| `build_calibration_agent_packet` | type_reference | [api](../modules/api.md) |
| `build_calibration_agent_packet` | type_reference | [controller](../modules/controller.md) |
| `P0CalibrationAgentPacket.from_dict` | type_reference | [controller](../modules/controller.md) |
