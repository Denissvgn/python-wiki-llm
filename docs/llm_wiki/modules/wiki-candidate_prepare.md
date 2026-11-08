# prepare Module

**Path:** `integrations/wiki-candidate/prepare.py`

## Description

Prepare the selected helpers and check a consumer's existing native evidence.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `argparse` | `argparse` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_cli.services.documentation_native` | `evaluate_documentation_native_freshness` |
| `llm_wiki_cli.services.helper_cache` | `ensure_helper` |
| `llm_wiki_cli.services.helper_preparation` | `selected_helper_languages` |
| `llm_wiki_cli.services.helper_runtime` | `helper_operation` |
| `llm_wiki_cli.services.knowledge_evidence` | `hash_json` |
| `llm_wiki_cli.services.knowledge_freshness` | `REASON_CONCEPT_OBSERVATION_CHANGED` |
| `llm_wiki_cli.services.knowledge_loader` | `load_knowledge_state` |
| `llm_wiki_cli.services.publication_config` | `load_publication_config`, `publication_path` |
| `llm_wiki_cli.services.source_retirement` | `retired_entity_mappings` |
| `pathlib` | `Path` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["integrations/wiki-candidate/prepare.py"]
    n1["src/llm_wiki_cli/services/documentation_native.py"]
    n2["src/llm_wiki_cli/services/helper_cache.py"]
    n3["src/llm_wiki_cli/services/helper_preparation.py"]
    n4["src/llm_wiki_cli/services/helper_runtime.py"]
    n5["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n6["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n7["src/llm_wiki_cli/services/knowledge_loader.py"]
    n8["src/llm_wiki_cli/services/publication_config.py"]
    n9["src/llm_wiki_cli/services/source_retirement.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n0 --> n9
    n1 --> n5
    n1 --> n6
    n1 --> n9
    n2 --> n4
    n3 --> n2
    n3 --> n4
    n6 --> n5
    n9 --> n5
    click n0 "../modules/wiki-candidate_prepare.md"
    click n1 "../modules/documentation_native.md"
    click n2 "../modules/helper_cache.md"
    click n3 "../modules/helper_preparation.md"
    click n4 "../modules/helper_runtime.md"
    click n5 "../modules/knowledge_evidence.md"
    click n6 "../modules/knowledge_freshness.md"
    click n7 "../modules/knowledge_loader.md"
    click n8 "../modules/publication_config.md"
    click n9 "../modules/source_retirement.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Outbound | [documentation_native](../modules/documentation_native.md) |
| Outbound | [helper_cache](../modules/helper_cache.md) |
| Outbound | [helper_preparation](../modules/helper_preparation.md) |
| Outbound | [helper_runtime](../modules/helper_runtime.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [knowledge_freshness](../modules/knowledge_freshness.md) |
| Outbound | [knowledge_loader](../modules/knowledge_loader.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [source_retirement](../modules/source_retirement.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_write` | `(path: Path, document: dict) -> None` | — | — |
| `prepare` | `(mode: str, consumer: Path, config_path: str, source_dir: str, evidence: Path, cache: Path) -> None` | — | — |
