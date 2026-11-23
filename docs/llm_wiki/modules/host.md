# host Module

**Path:** `src/llm_wiki_engine/host.py`

## Description

Host capabilities the engine uses instead of ambient process state.

Engine code starts processes, reads the environment, resolves the working
directory and reads the clock through :func:`current_host`. The default
:class:`Host` does exactly what the code did before, on this machine, so
callers that never choose a host see no change.

An embedding application subclasses :class:`Host`, for example to pin the
environment or to refuse subprocesses with :class:`NoProcessHost`, and runs
engine work inside :func:`using_host`. The choice is scoped to the current
context, so concurrent operations can use different hosts.

Human-readable progress and diagnostics go through :func:`emit`, which writes
to the host's ``stdout`` or ``stderr``. A host built with its own streams
captures that output; the default resolves ``sys.stdout``/``sys.stderr`` on
every write, so redirection and test capture keep working.

A host built with ``events=`` also receives structured
:class:`~llm_wiki_engine.engine_events.EngineEvent` objects for each
engine operation, including one ``message`` event per line written.

This is the only engine module that touches ``subprocess``, ``os.environ``,
the current directory, the clock and the standard streams directly.

## Imports

| Source | Symbols |
|--------|---------|
| `.engine_events` | `EngineEvent`, `EventSink`, `current_operation` |
| `__future__` | `annotations` |
| `collections.abc` | `Iterator`, `Mapping` |
| `contextlib` | `contextmanager` |
| `contextvars` | `ContextVar` |
| `copy` | `copy` |
| `datetime` | `date`, `datetime`, `timezone` |
| `io` | `io` |
| `os` | `os` |
| `pathlib` | `Path` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |
| `tempfile` | `tempfile` |
| `typing` | `Any`, `Literal`, `Protocol` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_engine/host.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/host.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (39) |
| Outbound | `src` (1) |

> All 40 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [TextSink](../entities/TextSink.md) | Class | 44 | `Protocol` | A writable text stream, such as ``sys.stdout`` or ``io.StringIO``. |
| [HostCapabilityError](../entities/HostCapabilityError.md) | Class | 52 | `PermissionError` | The active host does not grant this capability. |
| [Host](../entities/Host.md) | Class | 64 | — | This machine: real processes, live environment and cwd, wall clock. |
| [NoProcessHost](../entities/NoProcessHost.md) | Class | 143 | `Host` | A host that grants no subprocesses; everything else is local. |
| [Stream](../entities/Stream.md) | Type alias | 182 | `Literal['stdout', 'stderr']` | — |
| [MessageStream](../entities/MessageStream.md) | Class | 204 | — | A stream that writes to the active host and reports each line as an event. |
| [_Unpublished](../entities/Unpublished.md) | Class | 238 | `io.TextIOBase` | — |
| [_Discard](../entities/Discard.md) | Class | 243 | `_Unpublished` | — |
| [_Deferred](../entities/Deferred.md) | Class | 248 | `_Unpublished` | — |
| [ErrorRecorder](../entities/ErrorRecorder.md) | Class | 286 | — | Forwards writes to a host's stderr and keeps a copy for error messages. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_program` | `(args: Any) -> str` | — | — |
| `current_host` | `() -> Host` | — | The host chosen for this context, or the local default. |
| `using_host` | `(host: Host) -> Iterator[Host]` | `@contextmanager` | Run the enclosed engine work against ``host``. |
| `emit` | `(*values: object, stream: Stream = 'stdout', sep: str = ' ', end: str = '\n', flush: bool = False) -> None` | — | Write one human-readable line to the active host's stream. |
| `_publish_message` | `(host: Host, stream: Stream, line: str) -> None` | — | — |
| `deferred_stdout` | `() -> Iterator[None]` | `@contextmanager` | Publish stdout and its message events only after the enclosed checks succeed. |
| `discarding_stdout` | `() -> Iterator[Host]` | `@contextmanager` | Run the enclosed work with the active host's stdout discarded. |
| `discarding_output` | `() -> Iterator[Host]` | `@contextmanager` | Run the enclosed work with the active host's stdout and stderr discarded. |
| `recording_errors` | `() -> Iterator[ErrorRecorder]` | `@contextmanager` | Run the enclosed work with stderr still written, and recorded. |
