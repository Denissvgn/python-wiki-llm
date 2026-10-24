# freshness_wording Module

**Path:** `src/llm_wiki_cli/services/freshness_wording.py`

## Description

Shared interpretation of the legacy structural freshness diagnostic.

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/doctor_service.py"]
    n1["src/llm_wiki_cli/services/freshness_wording.py"]
    n2["src/llm_wiki_cli/services/health_summary.py"]
    n3["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n4["src/llm_wiki_cli/services/knowledge_observability.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n4
    n2 --> n1
    n2 --> n4
    n3 --> n1
    n4 --> n1
    n4 --> n3
    click n0 "../modules/doctor_service.md"
    click n1 "../modules/freshness_wording.md"
    click n2 "../modules/health_summary.md"
    click n3 "../modules/knowledge_freshness.md"
    click n4 "../modules/knowledge_observability.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [doctor_service](../modules/doctor_service.md) |
| Inbound | [health_summary](../modules/health_summary.md) |
| Inbound | [knowledge_freshness](../modules/knowledge_freshness.md) |
| Inbound | [knowledge_observability](../modules/knowledge_observability.md) |
