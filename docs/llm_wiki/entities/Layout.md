# Layout

**Location:** `src/llm_wiki_engine/layout.py:15`
**Kind:** Class
**Bases:** —
**Module:** [layout](../modules/layout.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Where a wiki keeps its pages and machine state.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `wiki_dir` | `str` | `'docs/llm_wiki'` | — |
| `manifest` | `str` | `'.llm-wiki-manifest.json'` | — |
| `manifest_objects` | `str` | `'.llm-wiki-manifest'` | — |
| `knowledge_index` | `str` | `'.llm-wiki-knowledge.json'` | — |
| `knowledge_store` | `str` | `'.llm-wiki-knowledge'` | — |
| `surface_index` | `str` | `'.llm-wiki-surface.json'` | — |
| `governance` | `str` | `'.llm-wiki-governance.json'` | — |
| `governance_lock` | `str` | `'llm-wiki-governance.lock'` | — |
| `storage_lock` | `str` | `'llm-wiki-storage.lock'` | — |
| `maintenance_adoption` | `str` | `'.llm-wiki-maintenance-adoption.json'` | — |
| `verification_receipt` | `str` | `'.llm-wiki-verification.json'` | — |
| `page_move_recovery_prefix` | `str` | `'.llm-wiki-page-moves-'` | — |
| `breaker_state` | `str` | `'llm-wiki-breaker.json'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [layout](../modules/layout.md) | 0 | `breaker_state`, `governance`, `governance_lock`, `knowledge_index`, `knowledge_store`, `maintenance_adoption`, `manifest`, `manifest_objects`, `page_move_recovery_prefix`, `storage_lock`, `surface_index`, `verification_receipt` |
