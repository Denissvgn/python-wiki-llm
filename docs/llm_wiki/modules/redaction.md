# redaction Module

**Path:** `src/llm_wiki_cli/services/redaction.py`

## Description

Shared best-effort redaction for credential-like text.

The patterns in this module intentionally combine the credential matchers used
by prompt generation, documentation calibration, OCI dispatch, and public
knowledge projection.  Pattern matching is a safety net, not proof that text is
free of secrets.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Callable` |
| `re` | `re` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/generate_prompt_cmd.py"]
    n1["src/llm_wiki_cli/services/calibration/broker.py"]
    n2["src/llm_wiki_cli/services/calibration/controller.py"]
    n3["src/llm_wiki_cli/services/knowledge_projection.py"]
    n4["src/llm_wiki_cli/services/redaction.py"]
    n0 --> n4
    n1 --> n4
    n2 --> n1
    n2 --> n4
    n3 --> n4
    click n0 "../modules/generate_prompt_cmd.md"
    click n1 "../modules/broker.md"
    click n2 "../modules/controller.md"
    click n3 "../modules/knowledge_projection.md"
    click n4 "../modules/redaction.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) |
| Inbound | [broker](../modules/broker.md) |
| Inbound | [controller](../modules/controller.md) |
| Inbound | [knowledge_projection](../modules/knowledge_projection.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_assignment_replacement` | `(match: re.Match[str]) -> str` | — | — |
| `_likely_secret_replacement` | `(match: re.Match[str]) -> str` | — | — |
| `redact_credentials` | `(text: str) -> tuple[str, int]` | — | Replace credential-like values in *text* and return the match count. |
