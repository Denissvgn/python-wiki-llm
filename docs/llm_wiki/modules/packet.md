# packet Module

**Path:** `src/llm_wiki_cli/services/documentation_run/packet.py`

## Description

Documentation-run packet services.

## Imports

| Source | Symbols |
|--------|---------|
| `.contracts` | `*` |
| `.dependencies` | `*` |
| `.integrity` | `*` |
| `.schema` | `*` |
| `.workspace` | `*` |
| `__future__` | `annotations` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
<!-- Thick arrows (==>) mark edges inside an import cycle. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n1["src/llm_wiki_cli/services/documentation_run/contracts.py"]
    n2["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n3["src/llm_wiki_cli/services/documentation_run/integrity.py"]
    n4["src/llm_wiki_cli/services/documentation_run/packet.py"]
    n5["src/llm_wiki_cli/services/documentation_run/schema.py"]
    n6["src/llm_wiki_cli/services/documentation_run/workspace.py"]
    n0 ==> n1
    n0 ==> n2
    n0 ==> n3
    n0 ==> n4
    n0 ==> n5
    n0 ==> n6
    n1 ==> n2
    n1 ==> n4
    n1 ==> n5
    n3 ==> n1
    n3 ==> n2
    n3 ==> n5
    n3 ==> n6
    n4 ==> n1
    n4 ==> n2
    n4 ==> n3
    n4 ==> n5
    n4 ==> n6
    n5 ==> n1
    n5 ==> n2
    n6 ==> n1
    n6 ==> n2
    n6 ==> n5
    click n0 "../modules/documentation_run___init__.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_dependencies.md"
    click n3 "../modules/integrity.md"
    click n4 "../modules/packet.md"
    click n5 "../modules/documentation_run_schema.md"
    click n6 "../modules/workspace.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_run___init__](../modules/documentation_run___init__.md) |
| Inbound | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Outbound | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Outbound | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) |
| Outbound | [integrity](../modules/integrity.md) |
| Outbound | [documentation_run_schema](../modules/documentation_run_schema.md) |
| Outbound | [workspace](../modules/workspace.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_render_packet_markdown` | `(payload: Mapping[str, Any]) -> str` | — | — |
| `build_documentation_agent_packet` | `(workspace: str \| Path, *, stage: str) -> DocumentationAgentPacket` | — | Build and persist a provider-neutral packet for one agent stage. |
