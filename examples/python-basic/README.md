# Python basics: keep a task's documentation current

This four-module program builds a `Task`, formats it, and saves a line of text.
You will generate its wiki, preserve an authored explanation while changing a
field, and retrieve context without running the program or calling a model.

Prerequisites: Python 3.10+ and an installed `agent-wiki-cli` 2.1.0 or newer.
No extractor helper or third-party application dependency is needed.
Copy the [project](project/) contents, including `.gitignore`, to a fresh working
directory. **Run every command below from that copied project directory.**

## Generate the wiki

```sh
llm-wiki init --agent generic --no-skills --wiki-dir wiki
llm-wiki bootstrap --src-dir . --wiki-dir wiki
```

Open `wiki/index.md`, `wiki/entities/Task.md`, and `wiki/modules/service.md`.
The entity's attributes include:

| Attribute | Type | Default |
|---|---|---|
| `title` | `str` | Required |
| `done` | `bool` | `False` |

The process flow starts at the guarded call in `app.py`. Its static path reaches
`main`, `format_task`, and `save_task`. Follow the **User Flows** links in the
index to the full sequence and data-flow pages.

## Repeat safely

For an existing wiki, use sync. With unchanged input, these commands preserve
the generated content and its authored sections.

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki
```

## Sync a source change

Add this sentence under **Description** in `wiki/entities/Task.md`, after the
existing description:

```markdown
Keep task titles in the user's original spelling.
```

In `models.py`, add `priority: int = 1` immediately after `done: bool = False`.

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki
```

`Task.md` now lists `priority` with type `int` and default `1`. Your authored
sentence remains. The source code controls the structural table; your description
explain a decision that syntax alone cannot establish.

## Search and context

```sh
llm-wiki search Task --src-dir . --wiki-dir wiki --format text
llm-wiki context --budget 1200 --budget-mode estimated --focus all --src-dir . --wiki-dir wiki --format json --read-only
```

Search locates the `Task` page. The context response includes the example's
symbols and reports its estimated accounting against the 1,200-token budget.
Estimated accounting does not require a tokenizer download and is not an exact
model-token count. See [context options](../../docs/cli-reference.md#context)
for local exact-tokenizer support.

Static calls show relationships in the selected source, not a proof that a
particular runtime branch executes. No `output/task.txt` is created by the
documentation commands. For another first run, use a fresh copy of `project/`;
keep using sync for the wiki you have annotated.
