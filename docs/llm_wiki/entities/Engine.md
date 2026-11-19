# Engine

**Location:** `src/llm_wiki_cli/engine/__init__.py:260`
**Kind:** Class
**Bases:** —
**Module:** [engine___init__](../modules/engine___init__.md)

## Description

One configured engine; independent engines may run side by side.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(*, host: Host \| None = None, helper_preparation: HelperPreparation = 'never', helper_cache_dir: str \| Path \| None = None, comparison_policy: str = 'auto', validators: ValidatorRegistry = DEFAULT_VALIDATORS, kinds: KindRegistry = DEFAULT_KINDS, pack: DomainPack = CODE_DOCS_PACK, publication_targets: PublicationTargetRegistry = DEFAULT_PUBLICATION_TARGETS) -> None` | — | — |
| `host` | `() -> Host` | `@property` | — |
| `capabilities` | `() -> dict[str, object]` | — | What this engine may do, so a caller can explain a refused operation. |
| `operation` | `() -> Iterator[Operation]` | `@contextmanager` | Apply this engine's grants to all work inside the block. |
| `call` | `(function: Callable[_P, _R], /, *args: _P.args, **kwargs: _P.kwargs) -> _R` | — | Run ``function`` (typically from :mod:`llm_wiki_cli.api`) in one operation. |
| `_run` | `(name: str, request: object, execute: Callable[[], _R], describe: Callable[[_R], Mapping[str, Any]]) -> _R` | — | Run one use case in an operation, reporting its lifecycle to the host. |
| `_report` | `(kind: EventKind, name: str, operation_id: str, data: Callable[[], Mapping[str, Any]]) -> None` | — | — |
| `sync` | `(request: SyncRequest) -> SyncOutcome` | — | Incrementally update a managed wiki; progress goes to the host's streams. |
| `bootstrap` | `(request: BootstrapRequest) -> BootstrapResult` | — | Create a first-use wiki; progress goes to the host's streams. |
| `lint` | `(request: LintRequest) -> LintReport` | — | Check a wiki against its source; ``report.passed`` is the verdict. |
| `migrate` | `(request: MigrateRequest) -> MigrateOutcome` | — | Bring an older wiki to current page naming; progress goes to the host. |
| `upgrade` | `(request: UpgradeRequest) -> UpgradeOutcome` | — | Refresh the managed agent schema, skills and wiki layout in place. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [engine___init__](../modules/engine___init__.md) | 12 | — |
