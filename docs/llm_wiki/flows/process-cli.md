# cli

**Entry point:** `main` (`process`)
**Source:** [cli](../modules/cli.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [cli](../modules/cli.md), [progress](../modules/progress.md), [resource_diagnostics](../modules/resource_diagnostics.md)

**Related modules:** [analysis_compatibility](../modules/analysis_compatibility.md), [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [llm_wiki_cli___init__](../modules/llm_wiki_cli___init__.md), and 5 more

**Complete related modules:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [llm_wiki_cli___init__](../modules/llm_wiki_cli___init__.md)
- [maintenance_queue](../modules/maintenance_queue.md)
- [progress](../modules/progress.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [runtime_output](../modules/runtime_output.md)
- [services_contracts](../modules/services_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as main
    participant p1 as _build_parser
    participant p2 as parser.parse_args
    participant p3 as comparison_scope
    participant p4 as getattr
    participant p5 as _dispatch_command
    participant p6 as print
    participant p7 as sys.exit
    participant p8 as str
    participant p9 as os.environ.get
    participant p10 as resource_failure_hint
    participant p11 as argparse.ArgumentParser
    participant p12 as _ACTIVE.set
    participant p13 as Progress(…).run
    participant p14 as tuple
    participant p15 as parser.add_argument (src/llm_wiki_cli/cli.py:_build_parser)
    participant p16 as selected_policy
    participant p17 as Progress
    participant p18 as _exception_chain
    participant p19 as parser.add_subparsers (src/llm_wiki_cli/cli.py:_build_parser)
    participant p20 as _ACTIVE.reset
    participant p21 as _COMMAND_MODULES[…].run
    participant p22 as isinstance (src/llm_wiki_cli/services….py:resource_failure_hint)
    participant p23 as _register_commands
    p0->>p1: _build_parser
    p0-->>p2: parser.parse_args
    p0->>p3: comparison_scope
    p0-->>p4: getattr(args, 'comparison_policy', 'auto')
    p0->>p5: _dispatch_command
    p0-->>p6: print('\nAborted.')
    p0-->>p7: sys.exit(130)
    p0-->>p6: print(str(...), file=sys.stderr)
    p0-->>p8: str(exc)
    p0-->>p7: sys.exit(1)
    p0-->>p6: print(..., file=sys.stderr)
    p0-->>p7: sys.exit(2)
    p0-->>p9: os.environ.get('LLM_WIKI_DEBUG')
    p0-->>p6: print(..., file=sys.stderr)
    p0->>p10: resource_failure_hint
    p0-->>p6: print(..., file=sys.stderr)
    p0-->>p7: sys.exit(1)
    p1-->>p11: argparse.ArgumentParser(description='LLM Wiki CLI')
    p3-->>p12: _ACTIVE.set(selected_policy(...))
    p5-->>p13: Progress(…).run
    p10-->>p14: tuple(_exception_chain(...))
    p1-->>p15: parser.add_argument (src/llm_wiki_cli/cli.py:_build_parser)('--version', action='version', version=...)
    p3->>p16: selected_policy
    p5->>p17: Progress
    p10->>p18: _exception_chain
    p1-->>p19: parser.add_subparsers (src/llm_wiki_cli/cli.py:_build_parser)(dest='command', required=True)
    p3-->>p20: _ACTIVE.reset(token)
    p5-->>p21: _COMMAND_MODULES[…].run(args)
    p10-->>p22: isinstance (src/llm_wiki_cli/services….py:resource_failure_hint)(current, MemoryError)
    p1->>p23: _register_commands
```

> Call sequence diagram shows 30 of 708 interactions; 678 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 24 (9 omitted); unresolved 7 of 550 (543 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/cli.py:_register_commands` | 6 | [src/llm_wiki_cli/cli.py](../modules/cli.md) | internal | 35 |
| `src/llm_wiki_cli/cli.py:_add_init_command` | 7 | - | unresolved | 9 |
| `src/llm_wiki_cli/cli.py:_add_init_command` | 7 | [src/llm_wiki_cli/cli.py](../modules/cli.md) | internal | 2 |
| `src/llm_wiki_cli/cli.py:_add_helper_cache_argument` | 14 | - | unresolved | 1 |
| `src/llm_wiki_cli/cli.py:_add_source_selection_argument` | 19 | - | unresolved | 1 |
| `src/llm_wiki_cli/cli.py:_add_extract_command` | 21 | - | unresolved | 12 |
| `src/llm_wiki_cli/cli.py:_add_extract_command` | 21 | [src/llm_wiki_cli/cli.py](../modules/cli.md) | internal | 3 |
| `src/llm_wiki_cli/cli.py:_add_include_tests_argument` | 31 | - | unresolved | 1 |
> Omission summary shows 8 of 84 groups; 76 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. main"]
    s2["2. _build_parser"]
    s3["3. argparse.ArgumentParser"]
    s4["4. parser.add_argument (src/llm_wiki_cli/cli.py:_build_parser)"]
    s5["5. parser.add_subparsers (src/llm_wiki_cli/cli.py:_build_parser)"]
    s6["6. _register_commands"]
    s7["7. _add_init_command"]
    s8["8. subparsers.add_parser (src/llm_wiki_cli/cli.py:_add_init_command)"]
    s9["9. init_parser.add_argument"]
    s10["10. init_parser.add_argument"]
    s11["11. init_parser.add_argument"]
    s12["12. init_parser.add_argument"]
    s1 -->|"_build_parser(data not statically known)"| s2
    s2 -. "argparse.ArgumentParser(description='LLM Wiki CLI')" .-> s3
    s2 -. "parser.add_argument (src/llm_wiki_cli/cli.py:_build_parser)('--version', action='version', version=...)" .-> s4
    s2 -. "parser.add_subparsers (src/llm_wiki_cli/cli.py:_build_parser)(dest='command', required=True)" .-> s5
    s2 -->|"_register_commands(subparsers)"| s6
    s6 -->|"_add_init_command(subparsers)"| s7
    s7 -. "subparsers.add_parser (src/llm_wiki_cli/cli.py:_add_init_command)('init', help='Scaffold LLM Wiki structure and schema')" .-> s8
    s7 -. "init_parser.add_argument('--agent', choices=AGENT_CHOICES, default=None, help='Target agent format (default: stored agent, or generic for a new project)')" .-> s9
    s7 -. "init_parser.add_argument('--wiki-dir', default=DEFAULT_WIKI_DIR, help='Wiki directory to create (default: docs/llm_wiki)')" .-> s10
    s7 -. "init_parser.add_argument('--no-quality-hints', action='store_true', default=None, help='Omit agent quality guidelines from the constraint block')" .-> s11
    s7 -. "init_parser.add_argument(…)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["environment_read os.environ.get"]
    s1 -. "environment_read os.environ.get" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    click s1 "../modules/cli.md"
    click s2 "../modules/cli.md"
    click s6 "../modules/cli.md"
    click s7 "../modules/cli.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `main` | - | `PathValidationError`, `sys`, `RuntimeOutputError`, `sys`, `sys`, `sys` | - | - |
| `_build_parser` | - | `__version__` | - | `parser` |
| `argparse.ArgumentParser` | - | - | - | - |
| `parser.add_argument (src/llm_wiki_cli/cli.py:_build_parser)` | - | - | - | - |
| `parser.add_subparsers (src/llm_wiki_cli/cli.py:_build_parser)` | - | - | - | - |
| `_register_commands` | `subparsers` | - | - | - |
| `_add_init_command` | `subparsers` | `AGENT_CHOICES`, `DEFAULT_WIKI_DIR` | - | - |
| `subparsers.add_parser (src/llm_wiki_cli/cli.py:_add_init_command)` | - | - | - | - |
| `init_parser.add_argument` | - | - | - | - |
| `init_parser.add_argument` | - | - | - | - |
| `init_parser.add_argument` | - | - | - | - |
| `init_parser.add_argument` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| main | _build_parser | 2627 | `_build_parser(data not statically known)` |
| _build_parser | argparse.ArgumentParser | 261 | `argparse.ArgumentParser(description='LLM Wiki CLI')` |
| _build_parser | parser.add_argument (src/llm_wiki_cli/cli.py:_build_parser) | 262 | `parser.add_argument('--version', action='version', version=...)` |
| _build_parser | parser.add_subparsers (src/llm_wiki_cli/cli.py:_build_parser) | 265 | `parser.add_subparsers(dest='command', required=True)` |
| _build_parser | _register_commands | 266 | `_register_commands(subparsers)` |
| _register_commands | _add_init_command | 301 | `_add_init_command(subparsers)` |
| _add_init_command | subparsers.add_parser (src/llm_wiki_cli/cli.py:_add_init_command) | 380 | `subparsers.add_parser('init', help='Scaffold LLM Wiki structure and schema')` |
| _add_init_command | init_parser.add_argument | 383 | `init_parser.add_argument('--agent', choices=AGENT_CHOICES, default=None, help='Target agent format (default: stored agent, or generic for a new project)')` |
| _add_init_command | init_parser.add_argument | 389 | `init_parser.add_argument('--wiki-dir', default=DEFAULT_WIKI_DIR, help='Wiki directory to create (default: docs/llm_wiki)')` |
| _add_init_command | init_parser.add_argument | 394 | `init_parser.add_argument('--no-quality-hints', action='store_true', default=None, help='Omit agent quality guidelines from the constraint block')` |
| _add_init_command | init_parser.add_argument | 400 | `init_parser.add_argument('--no-skills', action='store_true', default=None, help="Skip installing the wiki-reference skill into the agent's skills directory (.claude/skills for claude, .llm-wiki/skills otherwise)")` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `main` | 2635 |
| output | `print` | `main` | 2638 |
| output | `print` | `main` | 2641 |
| environment_read | `os.environ.get` | `main` | 2644 |
| output | `print` | `main` | 2646 |
| output | `print` | `main` | 2649 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_build_parser` | `argparse.ArgumentParser` | 261 |
| unresolved_call | `_build_parser` | `parser.add_argument` | 262 |
| unresolved_call | `_build_parser` | `parser.add_subparsers` | 265 |
| unresolved_call | `_add_init_command` | `subparsers.add_parser` | 380 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 383 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 389 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 394 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 400 |
| step_limit | `main` | `first 12 steps` | 0 |

## Behavior

This flow starts at `main` and is classified as `process`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
