# ReviewEvent

**Location:** `src/llm_wiki_cli/services/knowledge_governance.py:238`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_governance](../modules/knowledge_governance.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One section-scoped, digest-bound human review event.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `event_id` | `str` | *required* | — |
| `concept_uid` | `str` | *required* | — |
| `section_locator` | `str` | *required* | — |
| `scope_hash` | `str` | *required* | — |
| `evidence` | `ReviewEvidence` | *required* | — |
| `reviewer` | `GovernanceActor` | *required* | — |
| `method` | `str` | *required* | — |
| `method_version` | `str` | *required* | — |
| `authored_at` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_payload` | `() -> dict[str, object]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ReviewEvent (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n2["_parse_review_event (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n3["_review_event_digest_payload (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n4["_review_event_summary (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n5["_validate_review_event_fields (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n6["add_review_event (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n7["evaluate_review_event (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_governance.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_governance.md"
    click n5 "../modules/knowledge_governance.md"
    click n6 "../modules/knowledge_governance.md"
    click n7 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_governance](../modules/knowledge_governance.md) | 1 | `authored_at`, `concept_uid`, `event_id`, `evidence`, `method`, `method_version`, `reviewer`, `scope_hash`, `section_locator` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) | — |
| `_parse_review_event` | call | [knowledge_governance](../modules/knowledge_governance.md) | 1 |
| `_parse_review_event` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_review_event_digest_payload` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_review_event_summary` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `_validate_review_event_fields` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
| `add_review_event` | call | [knowledge_governance](../modules/knowledge_governance.md) | 1 |
| `evaluate_review_event` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) | — |
