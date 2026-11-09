# helper_preparation Module

**Path:** `src/llm_wiki_cli/services/helper_preparation.py`

## Description

Plans and prepares bundled extractor helpers during an explicitly requested
setup operation. Language detection uses the same source snapshot as
`prepare-extractors`, including the configured selection and exclusions.
Python-only selections need no helper cache.

`ensure_source_helpers` reuses helpers whose manifests match their source,
platform, and artifact identities. Missing or stale helpers are prepared in
the resolved cache. Individual cache-write failures become failed results so
other selected helpers can still complete; initialization checks the full
result list before creating its scaffold or agent configuration. Valid helper
reuse does not require the build toolchain, although TypeScript analysis still
needs Node.js at runtime. Read-only analysis never invokes this setup service.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `extractor_helpers` |
| `.helper_cache` | `HelperPreparationError`, `cache_roots`, `ensure_helper`, `lookup_helper`, `validate_handle` |
| `.helper_runtime` | `PreparedHelperHandle`, `bind_helper`, `current_helper_operation`, `pinned_helper`, `required_helper_languages` |
| `.progress` | `current_progress`, `phase` |
| `.source_snapshot` | `SourceSnapshot`, `build_source_snapshot` |
| `__future__` | `annotations` |
| `collections.abc` | `Iterable`, `Mapping` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `typing` | `TYPE_CHECKING` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["integrations/wiki-candidate/prepare.py"]
    n1["src/llm_wiki_cli/commands/init_cmd.py"]
    n2["src/llm_wiki_cli/commands/prepare_extractors_cmd.py"]
    n3["src/llm_wiki_cli/services/extraction_service.py"]
    n4["src/llm_wiki_cli/services/extractor_helpers.py"]
    n5["src/llm_wiki_cli/services/helper_cache.py"]
    n6["src/llm_wiki_cli/services/helper_preparation.py"]
    n7["src/llm_wiki_cli/services/helper_runtime.py"]
    n8["src/llm_wiki_cli/services/progress.py"]
    n9["src/llm_wiki_cli/services/source_snapshot.py"]
    n0 --> n5
    n0 --> n6
    n0 --> n7
    n1 --> n4
    n1 --> n6
    n2 --> n4
    n2 --> n6
    n2 --> n9
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n4 --> n5
    n4 --> n7
    n5 --> n4
    n5 --> n7
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n8
    n6 --> n9
    n7 --> n4
    n7 --> n9
    n9 --> n8
    click n0 "../modules/wiki-candidate_prepare.md"
    click n1 "../modules/init_cmd.md"
    click n2 "../modules/prepare_extractors_cmd.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extractor_helpers.md"
    click n5 "../modules/helper_cache.md"
    click n6 "../modules/helper_preparation.md"
    click n7 "../modules/helper_runtime.md"
    click n8 "../modules/progress.md"
    click n9 "../modules/source_snapshot.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [wiki-candidate_prepare](../modules/wiki-candidate_prepare.md) |
| Inbound | [init_cmd](../modules/init_cmd.md) |
| Inbound | [prepare_extractors_cmd](../modules/prepare_extractors_cmd.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Outbound | [extractor_helpers](../modules/extractor_helpers.md) |
| Outbound | [helper_cache](../modules/helper_cache.md) |
| Outbound | [helper_runtime](../modules/helper_runtime.md) |
| Outbound | [progress](../modules/progress.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_helper_progress` | `(message: str) -> None` | — | — |
| `prepare_operation_helpers` | `(snapshot: SourceSnapshot, registry: Mapping[str, str], *, only_files: Iterable[str] \| None = None, cache_dir: str \| None = None) -> tuple[PreparedHelperHandle, ...]` | — | Resolve helpers before capture, without changing an inspection's policy. |
| `selected_helper_languages` | `(src_dir: str \| Path, *, source_selection: str \| Path \| None = None) -> list[str]` | — | — |
| `ensure_source_helpers` | `(src_dir: str \| Path, *, cache_dir: str \| None = None, source_selection: str \| Path \| None = None) -> list[helpers.HelperPrepareResult]` | — | Prepare missing/stale helpers, reusing valid artifacts without build tools. |