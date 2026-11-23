# KnowledgeCommitResult

**Location:** `src/llm_wiki_engine/knowledge_artifacts.py:248`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_artifacts](../modules/knowledge_artifacts.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Outcome of a real or dry-run commit.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `surface_index` | `PlannedArtifactWrite \| SpooledArtifactWrite` | *required* | — |
| `knowledge_index` | `PlannedArtifactWrite \| SpooledArtifactWrite` | *required* | — |
| `manifest` | `PlannedArtifactWrite \| SpooledArtifactWrite` | *required* | — |
| `committed_manifest` | `SyncManifest` | *required* | — |
| `evaluated_envelope_hash` | `str` | *required* | — |
| `dry_run` | `bool` | *required* | — |
| `storage_objects` | `tuple[PlannedArtifactWrite \| SpooledArtifactWrite, ...]` | `()` | — |
| `storage_format` | `str` | `'v1'` | — |
| `maintenance_adoption` | `PlannedArtifactWrite \| SpooledArtifactWrite \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `changed` | `() -> bool` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeCommitResult (src/llm_wiki_engine/knowledge_artifacts.py)"]
    n1["_emit_bootstrap_json_summary (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["_finalize_bootstrap_artifacts (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["src/llm_wiki_cli/services/documentation_native.py"]
    n4["_commit_runtime_knowledge (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n5["finalize_runtime_knowledge (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n6["unchanged_commit_result (src/llm_wiki_cli/services/knowledge_reuse.py)"]
    n7["_finalize_prepared_sync (src/llm_wiki_cli/services/sync_runtime.py)"]
    n8["_print_sync_artifact_actions (src/llm_wiki_cli/services/sync_runtime.py)"]
    n9["commit_knowledge_artifacts (src/llm_wiki_engine/knowledge_artifacts.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/knowledge_artifacts.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/documentation_native.md"
    click n4 "../modules/knowledge_orchestration.md"
    click n5 "../modules/knowledge_orchestration.md"
    click n6 "../modules/knowledge_reuse.md"
    click n7 "../modules/sync_runtime.md"
    click n8 "../modules/sync_runtime.md"
    click n9 "../modules/knowledge_artifacts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 | `committed_manifest`, `dry_run`, `evaluated_envelope_hash`, `knowledge_index`, `maintenance_adoption`, `manifest`, `storage_format`, `storage_objects`, `surface_index` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_emit_bootstrap_json_summary` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_finalize_bootstrap_artifacts` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) | — |
| `_commit_runtime_knowledge` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `finalize_runtime_knowledge` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `unchanged_commit_result` | call | [knowledge_reuse](../modules/knowledge_reuse.md) | 1 |
| `_finalize_prepared_sync` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_print_sync_artifact_actions` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `commit_knowledge_artifacts` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `commit_knowledge_artifacts` | type_reference | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
