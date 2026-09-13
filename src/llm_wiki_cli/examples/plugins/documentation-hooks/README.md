# Documentation hooks sample plugin

This plugin adds task entry points and bounded Mermaid style hints to LLM Wiki.
Use `agent-wiki-cli` 2.1.0 or newer on Python 3.10+. No model service, worker
framework, or additional Python dependency is required.

| File | Role |
|---|---|
| `llm-wiki-plugin.json` | Declares the `documentation-hooks` plugin and its two components |
| `detectors.py` | Implements `documentation-hooks/worker-tasks` through `detectors:detect_worker_tasks` |
| `styles.py` | Implements `documentation-hooks/brand-flowcharts` through `styles:style_flowcharts` |

The detector normalizes path separators and case, then matches paths ending in
`tasks.py` and function names `handle_task` or `task_handler`. This literal
suffix rule also matches names such as `worker_tasks.py`. It returns category
`task` and label `task-handler`; the core assigns the stable entry ID
`task-task-handler` for the single-handler example. It is a naming convention,
not a Celery/RQ adapter or proof that a worker schedules the function.

## Try it in a fresh project

Run the commands from a new project directory. Create `tasks.py` there:

```python
def handle_task(title: str) -> str:
    """Normalize a task title without contacting a service."""
    return title.strip()
```

Create `.gitignore` so generated content and plugin source stay out of the
application inventory:

```gitignore
/wiki/
/vendor/
/.llm-wiki/
/AGENTS.md
__pycache__/
```

```sh
llm-wiki init --agent generic --no-skills --wiki-dir wiki
llm-wiki plugins samples export documentation-hooks --dest vendor/documentation-hooks
llm-wiki plugins validate vendor/documentation-hooks
llm-wiki install vendor/documentation-hooks --yes --wiki-dir wiki
llm-wiki bootstrap --src-dir . --wiki-dir wiki
```

If you already exported this README and its three neighboring files to
`vendor/documentation-hooks`, skip the export command. Export does not replace
an existing directory by default. Files do not activate a plugin until you run
`install`; hooks are Python code, so install only a plugin you trust. Here
`--yes` accepts installation of the bundled sample you have inspected.

Open `wiki/flows/task-task-handler.md`. The data-flow diagram contains:

```text
s1["1. handle_task"]
classDef entry fill:#2E7D32,stroke:#2E7D32
class s1 entry
```

A Mermaid viewer shows the first task node in green. The hook maps the actual
`1. handle_task` and `1. task_handler` labels only when the surface is
`data_flow` and its category is `task`. It leaves other task steps and unrelated
data flows uncolored. Relationship/dependency flowcharts retain the sample's
`task-handler` label hint and left-to-right direction. Sequence diagrams are
outside this hook's supported surfaces. These are color, class, and direction
hints; they do not change graph edges or the renderer's reserved classes.

## Change and repeat

Rename the function in `tasks.py` to `task_handler`, keeping its body, then run:

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki
```

The same flow page now identifies `task_handler` and colors its first node.
Use sync for later runs and a fresh working copy for another bootstrap.

To install from a source checkout instead of exporting, run
`llm-wiki install PATH --yes --wiki-dir wiki` from your project directory,
replacing `PATH` with the absolute path to
`examples/plugins/documentation-hooks` in that checkout. The
[full repository tutorial](https://github.com/Denissvgn/python-wiki-llm/tree/main/examples/plugin-hooks)
adds a storage call to make transfers and filesystem boundaries visible.

The older sample name `m4-documentation-hooks` remains an export alias with a
deprecation warning. Use `documentation-hooks` for new commands; installed
component references are unchanged.
