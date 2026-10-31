# wiki_git_delivery Module

**Path:** `src/llm_wiki_cli/services/wiki_git_delivery.py`

## Description

Read-only completeness of an owned native snapshot under effective Git policy.

## Imports

| Source | Symbols |
|--------|---------|
| `.io` | `decode_markdown_bytes` |
| `.knowledge_governance` | `GOVERNANCE_FILENAME` |
| `.knowledge_storage` | `KnowledgeStorageError` |
| `.knowledge_storage_diagnostics` | `_git` |
| `.knowledge_storage_io` | `_absolute_path` |
| `.knowledge_storage_lifecycle` | `_committed_inputs` |
| `.maintenance_protocol` | `ADOPTION_FILENAME` |
| `.wiki_git_policy` | `_git_environment`, `classify_wiki_git_policy` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `hashlib` | `hashlib` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/knowledge_storage_cmd.py"]
    n1["src/llm_wiki_cli/services/io.py"]
    n2["src/llm_wiki_cli/services/knowledge_governance.py"]
    n3["src/llm_wiki_cli/services/knowledge_storage.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage_diagnostics.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n7["src/llm_wiki_cli/services/maintenance_protocol.py"]
    n8["src/llm_wiki_cli/services/wiki_git_delivery.py"]
    n9["src/llm_wiki_cli/services/wiki_git_policy.py"]
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n0 --> n8
    n2 --> n1
    n4 --> n3
    n4 --> n5
    n4 --> n6
    n5 --> n1
    n5 --> n3
    n6 --> n1
    n6 --> n2
    n6 --> n3
    n6 --> n5
    n6 --> n7
    n7 --> n1
    n7 --> n2
    n7 --> n3
    n7 --> n5
    n8 --> n1
    n8 --> n2
    n8 --> n3
    n8 --> n4
    n8 --> n5
    n8 --> n6
    n8 --> n7
    n8 --> n9
    click n0 "../modules/knowledge_storage_cmd.md"
    click n1 "../modules/io.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_storage.md"
    click n4 "../modules/knowledge_storage_diagnostics.md"
    click n5 "../modules/knowledge_storage_io.md"
    click n6 "../modules/knowledge_storage_lifecycle.md"
    click n7 "../modules/maintenance_protocol.md"
    click n8 "../modules/wiki_git_delivery.md"
    click n9 "../modules/wiki_git_policy.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [knowledge_storage_cmd](../modules/knowledge_storage_cmd.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Outbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Outbound | [wiki_git_policy](../modules/wiki_git_policy.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_command` | `(root: Path, arguments: list[str], *, data: bytes \| None = None, maximum: int = MAX_GIT_METADATA_BYTES) -> tuple[int, bytes]` | — | — |
| `_ignored` | `(root: Path, paths: list[str]) -> set[str]` | — | — |
| `_index` | `(root: Path) -> tuple[bytes, dict[bytes, list[tuple[bytes, bytes, bytes]]]]` | — | — |
| `_blobs` | `(root: Path, identities: set[bytes]) -> dict[bytes, bytes]` | — | — |
| `_require_absent_authority` | `(root: Path, paths: set[str]) -> None` | — | — |
| `_staged` | `(root: Path, expected: Mapping[str, bytes], markdown: set[str], absent: set[str])` | — | — |
| `inspect_wiki_git_delivery` | `(wiki_dir: str \| Path, *, staged: bool = False) -> dict[str, Any]` | — | Check every required native file; an explicit staged check gates handoff. |
