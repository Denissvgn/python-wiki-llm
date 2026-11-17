# RepositoryEvidence

**Location:** `src/llm_wiki_cli/services/knowledge_envelope.py:236`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_envelope](../modules/knowledge_envelope.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Already collected local VCS evidence; raw remotes are never serialized.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `remotes` | `Mapping[str, str \| None]` | `field(default_factory=dict)` | — |
| `remotes_evaluated` | `bool` | `True` | — |
| `upstream_remote` | `str \| None` | `None` | — |
| `upstream_remote_evaluated` | `bool` | `True` | — |
| `evaluated_revision` | `str \| None` | `None` | — |
| `working_tree` | `WorkingTreeState` | `WorkingTreeState.UNKNOWN` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RepositoryEvidence (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n1["build_repository_record (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n2["collect_git_repository_evidence (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n3["src/llm_wiki_cli/services/knowledge_generation.py"]
    n4["collect_runtime_repository_evidence (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n5["src/llm_wiki_cli/services/migrate_runtime.py"]
    n6["_sync_reuse_input_basis (src/llm_wiki_cli/services/sync_runtime.py)"]
    n7["_try_sync_knowledge_reuse (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_envelope.md"
    click n1 "../modules/knowledge_envelope.md"
    click n2 "../modules/knowledge_envelope.md"
    click n3 "../modules/knowledge_generation.md"
    click n4 "../modules/knowledge_orchestration.md"
    click n5 "../modules/migrate_runtime.md"
    click n6 "../modules/sync_runtime.md"
    click n7 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 0 | `evaluated_revision`, `remotes`, `remotes_evaluated`, `upstream_remote`, `upstream_remote_evaluated`, `working_tree` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_repository_record` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 1 |
| `build_repository_record` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `collect_git_repository_evidence` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 2 |
| `collect_git_repository_evidence` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `collect_runtime_repository_evidence` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `migrate_runtime` | import | [migrate_runtime](../modules/migrate_runtime.md) | — |
| `_sync_reuse_input_basis` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_try_sync_knowledge_reuse` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
