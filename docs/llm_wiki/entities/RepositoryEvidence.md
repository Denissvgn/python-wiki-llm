# RepositoryEvidence

**Location:** `src/llm_wiki_cli/services/knowledge_envelope.py:233`
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

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RepositoryEvidence (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n1["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n2["src/llm_wiki_cli/commands/sync_cmd.py"]
    n3["build_repository_record (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n4["collect_git_repository_evidence (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n5["src/llm_wiki_cli/services/knowledge_generation.py"]
    n6["collect_runtime_repository_evidence (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_envelope.md"
    click n1 "../modules/migrate_cmd.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/knowledge_envelope.md"
    click n4 "../modules/knowledge_envelope.md"
    click n5 "../modules/knowledge_generation.md"
    click n6 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 0 | `evaluated_revision`, `remotes`, `remotes_evaluated`, `upstream_remote`, `upstream_remote_evaluated`, `working_tree` |

### References

| Reference | Kind | Source |
|---|---|---|
| `migrate_cmd` | import | [migrate_cmd](../modules/migrate_cmd.md) |
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) |
| `build_repository_record` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `build_repository_record` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `collect_git_repository_evidence` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `collect_git_repository_evidence` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `collect_git_repository_evidence` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) |
| `collect_runtime_repository_evidence` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
