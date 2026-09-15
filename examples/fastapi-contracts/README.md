# FastAPI: document production router mounts

One application mounts the same router under `/api` and `/preview`. The source
also contains a temporary test application and a test-only registration on the
imported production application. The generated production contract keeps the
two real prefixes and excludes both test-origin registrations.

Prerequisites: Python 3.10+ and `agent-wiki-cli` 2.2.0 or newer. Documentation
uses static extraction: it does not import FastAPI, execute `tests/test_app.py`,
or start a server. To run or type-check the application separately, install
[requirements.txt](requirements.txt) in your environment. It pins
[FastAPI 0.141.1](https://pypi.org/project/fastapi/0.141.1/), which supports
Python 3.10+. These dependencies are optional for CLI users.

Copy the [project](project/) contents, including `.gitignore`, into a fresh
directory. **Run every command below from that copied project directory.**

## Generate the wiki

```sh
llm-wiki init --agent generic --no-skills --wiki-dir wiki
llm-wiki bootstrap --src-dir . --wiki-dir wiki --api-contracts
llm-wiki extract --src-dir . --deep --read-only --output output/inventory.json
```

Open `wiki/api-contracts.md`. Its production operations include:

| Method | Path | Handler |
|---|---|---|
| GET | `/api/books` | `list_books` |
| GET | `/preview/books` | `list_books` |

Both mounts belong to the single application declared in `app.py`. The query
parameter `limit` has a default of `10` and bounds of `1` and `100`. The response
model is `Book`. Follow handler/flow links to the source-backed flow page.

Neither `/test-app/books` nor `/test-only/books` belongs to the production
contract. `output/inventory.json` still contains `tests/test_app.py` under
`inventory`: filtering contract registrations does not erase raw test-source
inventory. Its `api_contracts` object contains the composed production graph.

## Repeat safely

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki
```

Use these commands for an existing wiki. Sync reuses the API-contract policy
saved by bootstrap. Unchanged input preserves the generated contract and
authored sections.

## Sync a source change

Add `Preview is a second production mount, not a temporary test application.`
under the **Notes** heading in `wiki/api-contracts.md`. In `routes.py`, change
the decorator path from `"/books"` to `"/reading-list"`.

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki
llm-wiki extract --src-dir . --deep --read-only --output output/inventory.json
```

The contract now contains `/api/reading-list` and `/preview/reading-list`.
Your Notes sentence and the handler's flow link remain; the two test prefixes
stay excluded.

The source contract covers recognized literal FastAPI declarations. Dynamic
prefixes and application factories can remain unknown. If you already have an
OpenAPI JSON/YAML export inside this project, `--openapi-file PATH` can make it
the authoritative contract; see [the CLI reference](../../docs/cli-reference.md).
Producing that export is separate from this static tutorial. Use a fresh
project copy for a new bootstrap and sync for subsequent runs.
