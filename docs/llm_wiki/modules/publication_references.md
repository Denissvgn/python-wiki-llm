# publication_references Module

**Path:** `src/llm_wiki_cli/services/publication_references.py`

## Description

Explicit, inert reference inputs for public documentation review.

## Imports

| Source | Symbols |
|--------|---------|
| `.cli_reference` | `get_cli_contract`, `parse_cli_contract`, `get_cli_contract` |
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
    n0["src/llm_wiki_cli/services/cli_reference.py"]
    n1["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n2["src/llm_wiki_cli/services/publication_config.py"]
    n3["src/llm_wiki_cli/services/publication_impact.py"]
    n4["src/llm_wiki_cli/services/publication_references.py"]
    n0 --> n1
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n4 --> n0
    n4 --> n1
    n4 --> n2
    click n0 "../modules/cli_reference.md"
    click n1 "../modules/knowledge_evidence.md"
    click n2 "../modules/publication_config.md"
    click n3 "../modules/publication_impact.md"
    click n4 "../modules/publication_references.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [publication_impact](../modules/publication_impact.md) |
| Outbound | [cli_reference](../modules/cli_reference.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [publication_config](../modules/publication_config.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `reference_identity` | `(provider: str, configuration: Mapping[str, Any]) -> str` | — | — |
| `capture_reference_inputs` | `(config, baseline, root, session)` | — | Read current and former providers through the caller's guarded session. |
| `recheck_reference_inputs` | `(captured, root)` | — | Recheck missing files and installed declarations after capture. |
| `reference_dependency_basis` | `(dep, basis, providers)` | — | Select one command subtree, retaining the provider's origin binding. |
| `_ancestor_context` | `(command)` | — | Global parser declarations also govern a selected descendant command. |
