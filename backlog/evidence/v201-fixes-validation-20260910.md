# Validation of the four v2.0.1 forensic fixes

Engineering record for the implementation of
[VB-01 through VB-04](../v201-verified-bugs-20260910.md). The baseline review
and its original observations remain unchanged as historical evidence.

The fixes are committed separately: VB-01 `bd1a21d`, VB-02 `8e09a07`,
VB-03 `efa565a`, and VB-04 `91b2b55`.

## Implementation

| Ticket | Result | Main regression coverage |
|---|---|---|
| VB-01 | JavaScript resolves the selected TypeScript-family producer while retaining its precise content language and existing built-in component ID. Explicit JavaScript plugins take precedence. Mixed-language plugin configuration is independent of file order. | [Producer tests](../../tests/test_knowledge_producer_languages.py), [migration tests](../../tests/test_verified_bug_migrations.py) |
| VB-02 | Workflows use resolved in-body call sites, preserve aliases and repeated calls, and require three distinct other project modules. Qualified method entries and call-site source paths are retained. Annotation/prose references do not create steps. Legacy link migration independently retains type-reference context without generating workflows or guessing among duplicate callable names. | [Call graph tests](../../tests/test_extract.py), [bootstrap tests](../../tests/test_bootstrap.py), [legacy migration tests](../../tests/test_migrate.py), [retirement tests](../../tests/test_verified_bug_migrations.py) |
| VB-03 | Sequence participant IDs include callable location or unresolved receiver scope; readable labels are independent of IDs. The call-data table uses the same labels without mutating analysis payloads. Actual recursion remains a self-message. | [Flow rendering tests](../../tests/test_bootstrap.py), [sequence renderer tests](../../tests/test_diagrams.py) |
| VB-04 | Known TypedDict ancestry, local totality, and `Required`/`NotRequired` determine key presence. Unknown totality stays unknown; imported base resolution is conservative. The entity renderer has a Presence column, separate from defaults and nullability. | [TypedDict tests](../../tests/test_python_typed_dicts.py), [migration tests](../../tests/test_verified_bug_migrations.py), [inventory contract](../../tests/test_extractor_inventory_contracts.py) |

The existing inventory cache and knowledge-reuse implementation fingerprints
include the changed source modules. Cached extraction and old builder evidence
therefore do not silently hide the new interpretation after an implementation
change. Missing provenance is still incompatible; no freshness gate was relaxed.

## Regressions observed before repair

- VB-01: four new failures covering `.js`, `.jsx`, family-plugin attribution,
  and producer-configuration invalidation.
- VB-02: three new failures covering annotation/prose false positives, real
  body calls with aliases/repetition, and qualified method entry points.
- VB-03: two new failures for an unresolved delegate and a same-named callable
  in another file; the real-recursion control already passed.
- VB-04: three new failures covering inherited totality, explicit presence
  overrides, and unknown totality; ordinary dataclass behavior already passed.

## Completed focused checks

- Producer, runtime knowledge generation, and freshness selection: **73 passed**.
- TypedDict, entity-page, and Python observation-cache selection: **27 passed**.
- Extract/bootstrap/sync/diagram/inventory-contract selection in the normal
  environment: **522 passed, 4 skipped**. The skips require prepared helpers.
- Migration selection with the existing prepared TypeScript helper cache:
  **5 passed**. Both fresh and historically unknown JavaScript artifacts pass
  strict doctor after the appropriate observation/refresh. Immediate sync
  preserves artifact bytes and modification times; forced knowledge rebuilding
  preserves content. TypedDict presence changes update both pages and structural
  observation hashes. Generated-only obsolete workflows retire; authored
  Behavior blocks retirement before any protected artifacts change.
- Pyright on the changed implementation modules: **0 errors, 0 warnings**.
- Focused Ruff correctness checks and Git whitespace checks passed.

The first broad selection used a shared `LLM_WIKI_CACHE_DIR`. Three failures
came from tests deliberately expecting no Haskell helper or a default Git
inventory-cache location; those passed with the environment override removed.
Two older fixtures qualified workflows using annotations alone. They now make
real calls while retaining their collision and first-sync assertions.

## Full-suite environment investigation

The default test temporary directory is below an existing read-only `/tmp/.git`.
Ten observed governance tests attempted to open
`/tmp/.git/llm-wiki-governance.lock` and failed with `EROFS`. This was reproduced
in three selected cases. All three passed under a newly initialized, disposable
Git boundary containing their pytest temporary directories. Product governance
locking was not weakened or redirected globally.

The full `.venv/bin/pytest -q` run completed all 7,163 collected cases:
**7,006 passed, 144 skipped, 13 failed**, in 824.92 seconds. Ten failures were
the temporary-directory lock issue above. Two were additional workflow
initialization fixtures whose annotation-only bodies needed real calls. One
revealed that legacy link migration had relied on the old annotation-derived
workflow detector. Migration now uses structural references separately for
existing page links; its original compatibility test remains unchanged.

All **13 failure cases passed** on a targeted rerun using the isolated Git
boundary. The complete migration and sync-runtime regression modules then
passed **38 tests, with 1 helper-dependent skip**, including a new check that
ambiguous callable names cannot authorize legacy link rewrites. The implementation
was not subjected to another complete suite after that bounded migration change;
its owning modules and every prior failure were rechecked instead.

[Post-fix observations](v201-fixes-observations.json) show that the delegate has
distinct participants, annotation-only workflow chains disappear, actual calls
qualify, JavaScript has a configuration hash, and `selection` is optional.
The observation script still reports the historical checked-in JavaScript
artifact's unknown basis until that artifact is regenerated; the migration
tests separately establish that real fresh and refreshed artifacts pass doctor.

## Compatibility and documentation

Validation runs use Linux and the project Python 3.14.4 virtual environment.
Windows/macOS execution and a Python 3.9 installation are not claimed. The
existing package metadata requires Python 3.10+; the implementation introduces
no new dependency on a newer interpreter or on `typing_extensions` at runtime.
All changed implementation files parse with Python 3.9's grammar.
Inspected source annotations are parsed statically rather than imported.

README and the separate companion wiki document workflow detection, participant
identity, TypedDict presence, JavaScript provenance, and the supported refresh
path for historical artifacts. Internal verification details stay in this
engineering record.
