# CommittedKnowledgeState

**Location:** `src/llm_wiki_cli/services/knowledge_orchestration.py:177`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_orchestration](../modules/knowledge_orchestration.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One command's captured prior commit, including explicit absent/invalid state.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `wiki_root` | `Path` | *required* | — |
| `artifacts` | `ValidatedKnowledgeArtifacts \| None` | `field(repr=False)` | — |
| `captured_bytes` | `Mapping[str, bytes \| None]` | `field(repr=False)` | — |
| `_issued` | `object \| None` | `field(default=None, init=False, repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `require_for` | `(wiki_dir: str \| Path) -> None` | — | — |
| `assert_current` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["CommittedKnowledgeState (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n1["_preflight_sync_governance (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_try_sync_knowledge_reuse (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["_previous_committed_artifacts (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n4["_previous_committed_producer (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n5["capture_committed_knowledge (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n6["committed_governance_bundle_id (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n7["committed_runtime_provenance (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_orchestration.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/knowledge_orchestration.md"
    click n4 "../modules/knowledge_orchestration.md"
    click n5 "../modules/knowledge_orchestration.md"
    click n6 "../modules/knowledge_orchestration.md"
    click n7 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_orchestration](../modules/knowledge_orchestration.md) | 2 | `_issued`, `artifacts`, `captured_bytes`, `wiki_root` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_preflight_sync_governance` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_try_sync_knowledge_reuse` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_previous_committed_artifacts` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `_previous_committed_producer` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `capture_committed_knowledge` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) | 1 |
| `capture_committed_knowledge` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `committed_governance_bundle_id` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `committed_runtime_provenance` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
