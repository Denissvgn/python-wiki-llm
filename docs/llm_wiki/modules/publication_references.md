# publication_references Module

**Path:** `src/llm_wiki_cli/services/publication_references.py`

## Description

Explicit, inert reference inputs for public documentation review.

## Imports

| Source | Symbols |
|--------|---------|
| `.behavior_reference` | `get_behavior_facts` |
| `.cli_reference` | `get_cli_contract`, `parse_cli_contract` |
| `.knowledge_evidence` | `hash_json` |
| `.publication_config` | `publication_path` |
| `__future__` | `annotations` |
| `copy` | `deepcopy` |
| `json` | `json` |
| `typing` | `Any`, `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/behavior_reference.py"]
    n1["src/llm_wiki_cli/services/cli_reference.py"]
    n2["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n3["src/llm_wiki_cli/services/publication_config.py"]
    n4["src/llm_wiki_cli/services/publication_impact.py"]
    n5["src/llm_wiki_cli/services/publication_references.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n3 --> n0
    n4 --> n2
    n4 --> n3
    n4 --> n5
    n5 --> n0
    n5 --> n1
    n5 --> n2
    n5 --> n3
    click n0 "../modules/behavior_reference.md"
    click n1 "../modules/cli_reference.md"
    click n2 "../modules/knowledge_evidence.md"
    click n3 "../modules/publication_config.md"
    click n4 "../modules/publication_impact.md"
    click n5 "../modules/publication_references.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [publication_impact](../modules/publication_impact.md) |
| Outbound | [behavior_reference](../modules/behavior_reference.md) |
| Outbound | [cli_reference](../modules/cli_reference.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [publication_config](../modules/publication_config.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `reference_identity` | `(provider: str, configuration: Mapping[str, Any]) -> str` | — | — |
| `_installed_contract` | `(kind, cache)` | — | Capture each opt-in provider once during this observation. |
| `capture_reference_inputs` | `(config, baseline, root, session)` | — | Read current and former providers through the caller's guarded session. |
| `recheck_reference_inputs` | `(captured, root)` | — | Recheck missing files and installed declarations after capture. |
| `reference_dependency_basis` | `(dep, basis, providers)` | — | Commit a complete reference, one command subtree or one named fact group. |
| `_ancestor_context` | `(command)` | — | Global parser declarations also govern a selected descendant command. |
