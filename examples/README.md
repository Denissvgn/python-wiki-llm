# Examples

Start with the question you want the wiki to answer.

| Example | What you will see | Prerequisites |
|---|---|---|
| [Python basics](python-basic/README.md) | Entity and module pages, a process flow, source refresh, and bounded context | Python 3.10+ |
| [Native knowledge](native-knowledge/README.md) | Drift decisions, shared native inspection, coverage and a qualified handoff | Python 3.10+ |
| [FastAPI contracts](fastapi-contracts/README.md) | Two production router mounts, with test-only registrations excluded | Python 3.10+; FastAPI is optional for documentation |
| [Go HTTP](go-http/README.md) | A process entry, a handler in another file, and package-scoped calls | A runnable Go toolchain and a prepared Go helper |
| [Plugin hooks](plugin-hooks/README.md) | A custom task flow with a green entry node | Python 3.10+ and the bundled sample plugin |

Use an activated environment with `agent-wiki-cli` 2.2.0 or newer installed.
When working from a source checkout, install that checkout into your environment
first; sample export reads the installed resources. See
[working from source](../docs/wiki-guide.md#working-from-source).
The commands below use the installed `llm-wiki` executable on Windows, macOS,
and Linux; they do not assume a particular virtual-environment directory.

Copy an example's **`project/` contents**, including `.gitignore`, into a new
working directory. Open a terminal in that directory and follow its README.
You can also work directly in `project/`; generated `wiki/` and `output/`
directories are ignored. A copied project has no repository history to depend on.

The CLI tutorials start with `init` and `bootstrap`; the native knowledge
tutorial bootstraps through the library API without agent configuration.
All use `sync` for later runs. Bootstrap does not replace a wiki you have already edited. Use a fresh
working copy when you want to start over. Helper and dependency preparation may
need network access; documentation commands then run locally without a model,
HTTP listener, task worker, or external service.

The tutorials are repository resources. The
[documentation-hooks plugin](plugins/documentation-hooks/README.md) and its
self-contained README are also available from an installed CLI through
`llm-wiki plugins samples export documentation-hooks`.
