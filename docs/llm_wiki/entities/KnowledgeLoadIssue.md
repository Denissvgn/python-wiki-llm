# KnowledgeLoadIssue

**Location:** `src/llm_wiki_cli/services/knowledge_loader.py:45`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_loader](../modules/knowledge_loader.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One stable, path-safe artifact load diagnostic.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `code` | `str` | *required* | — |
| `artifact_path` | `str` | *required* | — |
| `message` | `str` | *required* | — |
| `field` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeLoadIssue (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n1["_unsupported_reason (src/llm_wiki_cli/services/knowledge_consumption.py)"]
    n2["KnowledgeReadView.findings (src/llm_wiki_cli/services/knowledge_consumption.py)"]
    n3["_issue_from_artifact_error (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n4["_live_governance_issues (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n5["_load_manifest (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n6["_load_once (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n7["_marker_issues (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n8["_read_artifact (src/llm_wiki_cli/services/knowledge_loader.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_loader.md"
    click n1 "../modules/knowledge_consumption.md"
    click n2 "../modules/knowledge_consumption.md"
    click n3 "../modules/knowledge_loader.md"
    click n4 "../modules/knowledge_loader.md"
    click n5 "../modules/knowledge_loader.md"
    click n6 "../modules/knowledge_loader.md"
    click n7 "../modules/knowledge_loader.md"
    click n8 "../modules/knowledge_loader.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_loader](../modules/knowledge_loader.md) | 0 | `artifact_path`, `code`, `field`, `message` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_unsupported_reason` | type_reference | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `KnowledgeReadView.findings` | type_reference | [knowledge_consumption](../modules/knowledge_consumption.md) | — |
| `_issue_from_artifact_error` | call | [knowledge_loader](../modules/knowledge_loader.md) | 1 |
| `_issue_from_artifact_error` | type_reference | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `_live_governance_issues` | call | [knowledge_loader](../modules/knowledge_loader.md) | 6 |
| `_live_governance_issues` | type_reference | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `_load_manifest` | call | [knowledge_loader](../modules/knowledge_loader.md) | 4 |
| `_load_manifest` | type_reference | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `_load_once` | call | [knowledge_loader](../modules/knowledge_loader.md) | 7 |
| `_marker_issues` | call | [knowledge_loader](../modules/knowledge_loader.md) | 1 |
| `_marker_issues` | type_reference | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `_read_artifact` | call | [knowledge_loader](../modules/knowledge_loader.md) | 4 |

> References: showing 12 of 18 logical references; 6 omitted by the 12-row generated summary limit.
