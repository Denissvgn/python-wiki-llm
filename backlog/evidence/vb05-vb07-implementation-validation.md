# Implementation validation: VB-05, VB-07, and VB-06

Engineering record for the [12:00 report backlog](../v201-verified-bugs-20260910-120000.md).
The original review and before-fix observations remain unchanged.

Implementation commits: VB-05 `645ace4`, VB-07 `6e817f9`, and VB-06 `3812e1e`.

## Implemented behavior

- **VB-05:** the shared route adapter attaches only concrete route evidence,
  normalizes optional IDs, preserves unknown operations, and retains handler
  ambiguity before filtering. The stored-route validator remains strict.
- **VB-07:** Python resolution uses exact source-relative module identities and
  scoped source/package roots, including literal custom packaging layouts.
  Nested stems/suffixes are not global aliases. Ambiguous Python candidates
  remain observations rather than unconditional graph edges. Distribution
  reconciliation reuses the resolved graph, and shared stdlib knowledge retains
  its Python 3.9 fallback.
- **VB-06:** both call representations share captured lexical binding facts.
  Builtins cannot borrow unrelated definitions; local imports stay local;
  aliases, receiver methods, re-exports, and package-child imports preserve
  justified targets. Uncertain assignments, closures, and shadowing remain
  unresolved. Legacy inventories remain usable without the new optional facts.

Import scopes are restamped from current packaging metadata after raw cache
reuse and before imported model inheritance is finalized. Cache fingerprints
include the new resolver and extractor helpers. Entity structural observations
exclude call-binding implementation details just as they exclude body calls.

## Failing-before evidence

The route projection selection initially had **9 failures**. The initial Python
scope selection had **5 failures**, including the false logging cycle and shared
root ambiguity. The initial lexical call selection had **16 failures** while
the genuine-recursion control passed. These failures were observed before
wiring in the corresponding implementations.

An additional valid `from . import child` package re-export exposed a cycle in
the new binding traversal. Its regression failed before the traversal was
corrected to use the explicitly imported child module.

## Focused validation

- API-contract, deep-extract, bootstrap, and sync API coverage: **57 passed**.
- Scoped import, dependency, and package selection: **117 passed**.
- Broader extraction/flow/relationship/cache selection: **408 passed, 4 skipped**,
  with one old global-name ambiguity fixture subsequently rewritten to declare
  genuine import roots; its updated case passes.
- Combined route/import/binding/migration/knowledge selection:
  **363 passed, 1 skipped**.
- Final targeted regressions: **39 passed**, covering route publication and
  recovery, no-change artifact bytes/mtimes, builtin shadows, aliases, closures,
  re-exports, caller/callee queries, typed graph materialization, scoped roots,
  ambiguity, and packaging-only changes with warm inventory entries.
- Static checking of changed implementation modules reported **0 errors and
  0 warnings**. Focused Ruff correctness and Git whitespace checks passed.

Recovery uses the supported `sync` path. Bootstrap remains first-use only;
the compatibility overwrite option was not re-enabled. Both simulated legacy
bootstrap and sync failures recover while retaining authored `Behavior`.

## Packet compatibility

The first full-suite run reached **1,100 passing tests** before a canonical
packet golden mismatch. Inspection showed only the new `python_bindings`
source field, the corresponding token/path counts, and the derived packet ID
had changed. Current v1/v2 packet goldens and their measured hash/size record
were updated; policy versions and assurance claims were unchanged.

The original packet bytes are retained in the `context-packet-v1-pre-bindings`
and `context-packet-v2-pre-bindings` fixtures. Explicit compatibility checks
validate and round-trip those bytes. All **100 packet and baseline tests pass**.

## Full-suite and reported-source verification

The complete suite finished with **7,066 passed, 144 skipped, and 4 failures**
in 901.10 seconds. All four failure cases passed on the follow-up run:

- The graph end-to-end fixture now imports `User` from explicitly declared
  alternative roots, retaining its real ambiguity/coverage assertions instead
  of relying on a previously fabricated global-name match.
- The source-selection census includes the four new helper modules: 172 Python
  files and two TypeScript-family files. The selected-source profile is unchanged.
- Two tests requiring a non-Git directory had discovered the temporary parent
  repository used to isolate governance locks. They passed under a disposable
  invalid Git-discovery boundary, with their original test bodies unchanged.
  Production Git detection was not relaxed.

The full suite was not repeated after these fixture-only corrections. The
affected cases were rerun together: **4 passed**. The 144 skipped cases retain
their existing environment/toolchain requirements; no skips were added to hide
failures.

The [reported-source verification](vb05-vb07-reported-source-validation.json)
uses a byte-exact snapshot of 12 selected Traid files: the eight original source
anchors plus the two reported HTTP callers and their RBAC/database helpers.
The external application was never imported or run. Its original source-file
checksums remained unchanged.

This snapshot generated **88 pages**, including 12 modules, 17 entities, 53
flows, and one workflow. Bootstrap and the first sync both exited **0**;
the metadata trio's bytes and modification times were unchanged by that sync.
Strict doctor reported **healthy, exit 0**. The permissions `set()` call has
no file target in either representation; both reported HTTP flows omit the
unrelated order-router cache; the logging import-time cycle is absent; every
emitted flow route has a concrete path. This is a selected-source verification,
not qualification of the entire multi-thousand-file external repository.

The original synthetic probe was rerun against the committed implementation;
its [post-fix observations](vb05-vb07-fixed-observations.json) retain the before/after
comparison without replacing the original report evidence.

Public documentation describes the supported route, import, binding, and
recovery behavior. Internal verification details remain in this engineering
record. Cross-platform code and fixtures are preserved; execution in this run
uses the project virtual environment on Linux with Python 3.14.4.
Changed implementation syntax was also checked with Python 3.9's grammar.
Windows/macOS runtime execution is not claimed, and the package's existing
Python 3.10+ installation requirement is unchanged.
