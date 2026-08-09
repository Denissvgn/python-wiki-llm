# OriginValidationMiddleware

**Location:** `src/llm_wiki_cli/services/mcp_server.py:248`
**Kind:** Class
**Bases:** —
**Module:** [mcp_server](../modules/mcp_server.md)

## Description

Minimal ASGI middleware that rejects unexpected browser origins.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(app, *, port: int, allowed_origins: list[str] \| tuple[str, ...] \| None = None)` | — | — |
| `__call__` | *(async)* `(scope, receive, send)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [mcp_server](../modules/mcp_server.md) | 2 | — |
