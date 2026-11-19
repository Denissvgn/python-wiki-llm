# publication_references Module

**Path:** `src/llm_wiki_cli/services/publication_references.py`

## Description

Explicit, inert reference inputs for public documentation review.

Each declared provider kind is served by a
:class:`~.reference_providers.ReferenceProvider` of the active domain pack.

## Imports

| Source | Symbols |
|--------|---------|
| `.publication_config` | `publication_path` |
| `.reference_providers` | `reference_provider` |
| `__future__` | `annotations` |
| `copy` | `deepcopy` |
| `json` | `json` |
| `llm_wiki_engine.knowledge_evidence` | `hash_json` |
| `typing` | `Any`, `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/publication_config.py"]
    n1["src/llm_wiki_cli/services/publication_impact.py"]
    n2["src/llm_wiki_cli/services/publication_references.py"]
    n3["src/llm_wiki_cli/services/reference_providers.py"]
    n4["src/llm_wiki_engine/knowledge_evidence.py"]
    n0 --> n3
    n1 --> n0
    n1 --> n2
    n1 --> n4
    n2 --> n0
    n2 --> n3
    n2 --> n4
    n3 --> n4
    click n0 "../modules/publication_config.md"
    click n1 "../modules/publication_impact.md"
    click n2 "../modules/publication_references.md"
    click n3 "../modules/reference_providers.md"
    click n4 "../modules/knowledge_evidence.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [publication_impact](../modules/publication_impact.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [reference_providers](../modules/reference_providers.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `reference_identity` | `(provider: str, configuration: Mapping[str, Any]) -> str` | — | — |
| `_installed_contract` | `(kind, cache)` | — | Capture each opt-in provider once during this observation. |
| `capture_reference_inputs` | `(config, baseline, root, session)` | — | Read current and former providers through the caller's guarded session. |
| `recheck_reference_inputs` | `(captured, root)` | — | Recheck missing files and installed declarations after capture. |
| `reference_dependency_basis` | `(dep, basis, providers)` | — | Commit a complete reference or the part of it the dependency selects. |
