# Go: follow an HTTP handler across files and packages

The executable registers an unexported `health` function from `handlers.go`
using `http.NewServeMux`. That handler calls the exported `store.Status`
function, which delegates to a private method in its own package.
Everything uses the Go standard library.

Prerequisites: `agent-wiki-cli` 2.1.0 or newer and a runnable Go toolchain
compatible with Go 1.21 source. Copy the [project](project/) contents, including
`.gitignore`, into a fresh directory. **Run every command below from that copied
project directory.** Documentation generation does not start the HTTP listener.

## Prepare the helper

Prepare once; subsequent commands reuse this explicit, ignored cache.
Preparation may need network access for the toolchain. See
[extractor preparation](../../docs/cli-reference.md) if `go` is not on `PATH`.

```sh
llm-wiki prepare-extractors --src-dir . --language go --cache-dir .helpers
```

## Generate the wiki

```sh
llm-wiki init --agent generic --no-skills --wiki-dir wiki
llm-wiki bootstrap --src-dir . --wiki-dir wiki --helper-cache-dir .helpers
llm-wiki extract --src-dir . --deep --helper-cache-dir .helpers --read-only --output output/inventory.json
```

Open `wiki/index.md` and its **User Flows** links. The important entries are:

| Category | File | Symbol |
|---|---|---|
| process | `cmd/server/main.go` | `main` |
| http | `cmd/server/handlers.go` | `health` |

Registration evidence points to `mux.HandleFunc` in `cmd/server/main.go`.
The HTTP flow reaches `internal/store/store.go:Status`, then the same-package
private method `Store.status`. Full extraction retains the handler and private
method with export visibility recorded separately.

`output/inventory.json` contains `entrypoints`, `data_flows`, and
`data_flow_details` with the captured call evidence.
The helper observes registrations and direct calls; it does not prove the
server starts or that a request reaches a particular runtime branch.

## Repeat safely

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki --helper-cache-dir .helpers
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki --helper-cache-dir .helpers
```

These commands preserve an unchanged wiki. Keep using the same helper-cache
argument; a cache prepared elsewhere can be supplied with its actual path.

## Sync a source change

In `internal/store/store.go`, rename the private method `status` to `message`
and change its caller from `s.status()` to `s.message()`.

```sh
llm-wiki sync --jobs 1 --src-dir . --wiki-dir wiki --helper-cache-dir .helpers
llm-wiki lint --jobs 1 --src-dir . --wiki-dir wiki --helper-cache-dir .helpers
llm-wiki extract --src-dir . --deep --helper-cache-dir .helpers --read-only --output output/inventory.json
```

The Store entity and the HTTP flow now refer to `Store.message`. The handler
still resolves to the same file and `store.Status` remains an exported target.

Import calls require explicit public visibility; missing metadata cannot make
a private function public. Function values and interface dispatch can remain
unresolved. Call order is captured source order, not a runtime execution trace.
This example does not promise a workflow page: workflows require direct calls
into at least three other selected modules. It also makes no claim about Cobra
command semantics. Use a fresh copy for another bootstrap; do not overwrite an
annotated wiki to repeat this tutorial.
