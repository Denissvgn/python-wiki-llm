# BootstrapRequest

**Location:** `src/llm_wiki_cli/services/bootstrap_service.py:27`
**Kind:** Class
**Bases:** —
**Module:** [bootstrap_service](../modules/bootstrap_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Deterministic bootstrap inputs shared by CLI and library callers.

``source_adapter`` defaults to true because library callers should not
mutate agent integration files.  The existing CLI explicitly supplies its
historical value when translating argparse options.

``overwrite`` is retained only as a compatibility tombstone.  Public
bootstrap is first-use only and rejects ``overwrite=True`` before source
extraction or target writes.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source_root` | `str \| Path` | *required* | — |
| `wiki_root` | `str \| Path` | *required* | — |
| `depth` | `str` | `'full'` | — |
| `skip_workflows` | `bool` | `False` | — |
| `skip_flows` | `bool` | `False` | — |
| `skip_data_flow` | `bool` | `False` | — |
| `skip_dependencies` | `bool` | `False` | — |
| `api_contracts` | `bool` | `False` | — |
| `openapi_file` | `str \| None` | `None` | — |
| `dependency_graph_detail` | `str` | `'auto'` | — |
| `overwrite` | `bool` | `False` | — |
| `source_adapter` | `bool` | `True` | — |
| `helper_cache_dir` | `str \| None` | `None` | — |
| `include_tests` | `Iterable[str] \| None` | `None` | — |
| `trust_source_plugins` | `bool` | `False` | — |
| `source_selection` | `str \| Path \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BootstrapRequest (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n1["bootstrap_wiki (src/llm_wiki_cli/api.py)"]
    n2["_bootstrap_run_options_from_request (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["_execute_documentation_workspace_refresh (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n4["execute_bootstrap (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n5["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n6["_prepare_documentation_run_impl (src/llm_wiki_cli/services/documentation_run/prepare.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/bootstrap_service.md"
    click n1 "../modules/api.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/documentation_run_dependencies.md"
    click n6 "../modules/prepare.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_service](../modules/bootstrap_service.md) | 0 | `api_contracts`, `dependency_graph_detail`, `depth`, `helper_cache_dir`, `include_tests`, `openapi_file`, `overwrite`, `skip_data_flow`, `skip_dependencies`, `skip_flows`, `skip_workflows`, `source_adapter` |

### References

| Reference | Kind | Source |
|---|---|---|
| `bootstrap_wiki` | call | [api](../modules/api.md) |
| `_bootstrap_run_options_from_request` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_execute_documentation_workspace_refresh` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `execute_bootstrap` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `dependencies` | import | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) |
| `_prepare_documentation_run_impl` | call | [prepare](../modules/prepare.md) |
| `_prepare_documentation_run_impl` | call | [prepare](../modules/prepare.md) |
