# Plugin hooks: add and style a task flow

This example installs the bundled `documentation-hooks` plugin. Its detector
recognizes `handle_task` or `task_handler` in paths ending with `tasks.py`; its
style hook colors the first matching task node green in a data-flow diagram.
This is a naming convention, not a Celery or RQ framework adapter.

Prerequisites: Python 3.10+ and `agent-wiki-cli` 2.1.0 or newer. When working from
source, install that checkout first so export reads its sample files.
Copy the [project](project/) contents, including
`.gitignore`, into a fresh directory. **Run every command below from that copied
project directory.** There is no worker to start and no application dependency
to install.

## Generate the wiki

```sh
llm-wiki init --agent generic --no-skills --wiki-dir wiki
llm-wiki plugins samples export documentation-hooks --dest vendor/documentation-hooks
llm-wiki plugins validate vendor/documentation-hooks
llm-wiki install vendor/documentation-hooks --yes --wiki-dir wiki
llm-wiki bootstrap --src-dir . --wiki-dir wiki
```

Merely placing plugin files under `examples/` or `vendor/` does not activate
them; `install` records the plugin in this project. Only install plugin code you
trust: its hooks execute during analysis. `--yes` accepts that installation for
the reviewed bundled sample. The ignored `vendor/` folder keeps plugin source
out of the application's inventory.

Open `wiki/flows/task-task-handler.md`. It identifies `tasks.py:handle_task`,
follows the call to `storage.save_result`, and includes a data-flow diagram with
these Mermaid lines:

```text
s1["1. handle_task"]
classDef entry fill:#2E7D32,stroke:#2E7D32
class s1 entry
```

In a Mermaid-capable viewer, the `1. handle_task` node is green. The flow label
`task-handler` and the diagram node label `1. handle_task` have different jobs;
the style hook matches the numbered node label. Sequence diagrams and unrelated
nodes do not receive that color. Flowchart direction is a separate bounded hint.

## Repeat safely

Export and install once per fresh project. For later documentation runs:

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki
```

## Sync a source change

In `tasks.py`, rename `handle_task` to `task_handler`, keeping the body.

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki
```

The same `task-task-handler.md` page now starts with `task_handler`; its first
data-flow node remains green. This demonstrates the detector's two supported
function names without inventing worker scheduling or runtime guarantees.

## Use a source plugin

From your project directory, you may instead install the local
`examples/plugins/documentation-hooks` directory from a source checkout using
`llm-wiki install PATH --yes --wiki-dir wiki`, replacing `PATH` with that plugin's
absolute path. The [plugin README](../plugins/documentation-hooks/README.md)
explains the manifest and component references and also works after export.

Use a fresh project copy for a new bootstrap. Existing plugin exports and wikis
are preserved unless you explicitly choose to replace them.
