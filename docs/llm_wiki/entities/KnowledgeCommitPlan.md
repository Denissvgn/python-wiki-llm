# KnowledgeCommitPlan

**Location:** `src/llm_wiki_cli/services/knowledge_artifacts.py:122`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_artifacts](../modules/knowledge_artifacts.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A fully validated, immutable three-artifact commit plan.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `surface_index` | `PlannedArtifactWrite` | *required* | — |
| `knowledge_index` | `PlannedArtifactWrite` | *required* | — |
| `manifest` | `PlannedArtifactWrite` | *required* | — |
| `committed_manifest` | `SyncManifest` | *required* | — |
| `evaluated_envelope_hash` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `changed` | `() -> bool` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeCommitPlan (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n1["_prepare_existing_mutation (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n2["build_knowledge_commit_plan (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n3["commit_knowledge_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n4["_build_knowledge_generation_plan (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n5["build_knowledge_generation_plan (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n6["build_runtime_knowledge_plan (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_artifacts.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/knowledge_artifacts.md"
    click n3 "../modules/knowledge_artifacts.md"
    click n4 "../modules/knowledge_generation.md"
    click n5 "../modules/knowledge_generation.md"
    click n6 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 | `committed_manifest`, `evaluated_envelope_hash`, `knowledge_index`, `manifest`, `surface_index` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_prepare_existing_mutation` | type_reference | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `build_knowledge_commit_plan` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `build_knowledge_commit_plan` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `commit_knowledge_artifacts` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `_build_knowledge_generation_plan` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) |
| `build_knowledge_generation_plan` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) |
| `build_runtime_knowledge_plan` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
