# prepare Module

**Path:** `src/llm_wiki_cli/services/documentation_run/prepare.py`

## Description

Documentation-run prepare services.

## Imports

| Source | Symbols |
|--------|---------|
| `..bootstrap_runtime` | `execute_bootstrap`, `_execute_documentation_workspace_refresh` |
| `..documentation_wiki_input` | `_adopt_documentation_wiki_snapshot_with_runtime` |
| `.contracts` | `*` |
| `.dependencies` | `*` |
| `.integrity` | `*` |
| `.refresh` | `*` |
| `.schema` | `*` |
| `.workspace` | `*` |
| `__future__` | `annotations` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
<!-- Thick arrows (==>) mark edges inside an import cycle. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n1["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n2["src/llm_wiki_cli/services/documentation_run/contracts.py"]
    n3["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n4["src/llm_wiki_cli/services/documentation_run/integrity.py"]
    n5["src/llm_wiki_cli/services/documentation_run/prepare.py"]
    n6["src/llm_wiki_cli/services/documentation_run/refresh.py"]
    n7["src/llm_wiki_cli/services/documentation_run/schema.py"]
    n8["src/llm_wiki_cli/services/documentation_run/workspace.py"]
    n9["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n1 ==> n2
    n1 ==> n3
    n1 ==> n4
    n1 ==> n5
    n1 ==> n6
    n1 ==> n7
    n1 ==> n8
    n2 ==> n3
    n2 ==> n7
    n3 --> n9
    n4 ==> n2
    n4 ==> n3
    n4 ==> n7
    n4 ==> n8
    n4 --> n9
    n5 --> n0
    n5 ==> n2
    n5 ==> n3
    n5 ==> n4
    n5 ==> n6
    n5 ==> n7
    n5 ==> n8
    n5 --> n9
    n6 ==> n2
    n6 ==> n3
    n6 ==> n4
    n6 ==> n7
    n6 ==> n8
    n7 ==> n2
    n7 ==> n3
    n8 ==> n2
    n8 ==> n3
    n8 ==> n7
    click n0 "../modules/bootstrap_runtime.md"
    click n1 "../modules/documentation_run___init__.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/documentation_run_dependencies.md"
    click n4 "../modules/integrity.md"
    click n5 "../modules/prepare.md"
    click n6 "../modules/refresh.md"
    click n7 "../modules/documentation_run_schema.md"
    click n8 "../modules/workspace.md"
    click n9 "../modules/documentation_wiki_input.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_run___init__](../modules/documentation_run___init__.md) |
| Outbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Outbound | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Outbound | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) |
| Outbound | [integrity](../modules/integrity.md) |
| Outbound | [refresh](../modules/refresh.md) |
| Outbound | [documentation_run_schema](../modules/documentation_run_schema.md) |
| Outbound | [workspace](../modules/workspace.md) |
| Outbound | [documentation_wiki_input](../modules/documentation_wiki_input.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `prepare_documentation_run` | `(workspace: str \| Path, *, baseline_strategy: str = 'bootstrap_source', source_root: str \| Path \| None = None, source_selection: str \| Path \| None = None, input_wiki_root: str \| Path \| None = None, freshness_policy: str = 'require-current', site_name: str, audiences: Iterable[str] \| None = None, project_purpose: str \| None = None, audience_intent: Mapping[str, str] \| None = None, live_service_url: str \| None = None, live_service_access_mode: str = 'unspecified', live_service_observation_allowed: bool = False, helper_cache_root: str \| Path \| None = None, capture_root: str \| Path \| None = None, trust_source_plugins: bool = False, semantic_budget: int = 30, adjustment_loop_limit: int = 3, distribution_format: str = 'mkdocs', link_mode: str = 'http', knowledge_mode: str = 'off', knowledge_public_repository_identity: str \| None = None, refresh: bool = False) -> DocumentationRun` | — | Prepare a run with transactional rollback for initial creation and refresh. |
| `_prepare_documentation_run_impl` | `(workspace: str \| Path, *, baseline_strategy: str = 'bootstrap_source', source_root: str \| Path \| None = None, source_selection: str \| Path \| None = None, input_wiki_root: str \| Path \| None = None, freshness_policy: str = 'require-current', site_name: str, audiences: Iterable[str] \| None = None, project_purpose: str \| None = None, audience_intent: Mapping[str, str] \| None = None, live_service_url: str \| None = None, live_service_access_mode: str = 'unspecified', live_service_observation_allowed: bool = False, helper_cache_root: str \| Path \| None = None, capture_root: str \| Path \| None = None, trust_source_plugins: bool = False, semantic_budget: int = 30, adjustment_loop_limit: int = 3, distribution_format: str = 'mkdocs', link_mode: str = 'http', knowledge_mode: str = 'off', knowledge_public_repository_identity: str \| None = None, refresh: bool = False, refresh_transaction: _RefreshArchiveTransaction, initial_prepare_transaction: _InitialPrepareTransaction) -> DocumentationRun` | — | Prepare or idempotently resume an external documentation workspace. |
