# Read, change and resume a coding task

The consumer has an off-by-one error: `cap` keeps two values when three are
permitted. Its caller lives in another module. Copy `project/` into a fresh
directory and install `agent-wiki-cli` into that directory's `.venv`. On Windows,
use `.venv\Scripts\python.exe` for the Python commands below.

## Prepare and inspect

```sh
.venv/bin/python client.py prepare
.venv/bin/python client.py read
llm-wiki search cap --src-dir src --wiki-dir wiki
llm-wiki task-context --src-dir src --wiki-dir wiki --request request.json
```

The request declares the cap and caller contracts as required evidence. Inspect
their source locations, defaults and coverage. The provider reads source without
importing the application. `bridge.py` shows an on-demand host adapter. The host
chooses whether to include its result in a model conversation.

For MCP, start `llm-wiki mcp --src-dir src --wiki-dir wiki --enable-sessions`.
Call `build_task_context` with `request.json`. For optional reuse, call
`open_context_session`, then `read_context_session` with the handle and request.
Include canonical text once and keep session metadata separate.

## Make the host-owned change

```sh
.venv/bin/python client.py handoff
.venv/bin/python client.py check
.venv/bin/python client.py change
.venv/bin/python client.py check
.venv/bin/python client.py resume
```

The first behavior check reports a mismatch. `change` explicitly edits the owned
example to retain the full permitted batch; the second check succeeds. These are
consumer commands, separate from provider reads. Resume validates the saved
request/result and reports the changed source basis. No model is invoked.

## Preserve the reason and refresh

```sh
.venv/bin/python client.py note
llm-wiki sync --src-dir src --wiki-dir wiki --no-plugins
.venv/bin/python client.py read
.venv/bin/python client.py handoff
.venv/bin/python client.py resume
```

The authored note explains why the cap exists and why a full batch retains every
item. Synchronization updates generated structure while preserving that note.
An unchanged basis does not approve the explanation or establish runtime correctness.

Add `--no-session` to read/handoff/resume commands to use cold reads. Lost or
repeated events remain hints: `bridge.event("saved")` never proves currentness.
Unsaved buffers return save/defer guidance. Closing or switching tasks drops the
cache. Retain the request, canonical context and a concise explanation across a
restart. See [workflow contracts and limits](../../docs/native-agent-workflow.md).
