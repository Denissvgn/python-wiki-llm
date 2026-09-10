# Verified bug backlog: v2.0.1 forensic report

Engineering planning record, 2026-09-10. Reviewed source revision:
`1f281a14389c4efefeb1968dd4681704151ed7f7`.

Four independent bugs are confirmed. This backlog contains proposed fixes;
none has been implemented. The [verification review](evidence/v201-report-review-20260910.md)
records the disposition of every original finding, including the five that do
not establish a correctness defect. [Recorded observations](evidence/v201-findings-observations.json)
and the [reproduction script](../tests/verify_v201_report.py) provide the evidence.

| ID | Priority | Original finding | Confirmed defect | Status |
|---|---|---|---|---|
| VB-01 | P1 | FINDING-03 / report BUG-01 | JavaScript output cannot acquire known producer configuration from the default registry | Open |
| VB-02 | P1 | FINDING-02 / report BUG-02 | Workflow call chains are assembled from signatures and prose instead of body calls | Open |
| VB-03 | P2 | FINDING-01 / report BUG-03 | Sequence participants with different identities collapse onto the same symbol label | Open |
| VB-04 | P2 | FINDING-05 / report BUG-05 | Optional TypedDict keys are extracted and rendered as required | Open |

P1 means a supported operation is blocked or a generated structural surface
systematically asserts incorrect facts. P2 means a narrower output correctness
defect. No evidence here establishes a P0 outage, data loss, or runtime recursion.

## VB-01: Preserve known provenance for JavaScript output

**Impact.** Built-in extraction can produce valid JavaScript module pages whose
structural freshness is always `basis-incompatible`, even with identical
recorded and evaluated source/observation hashes. The reason is
`extractor-configuration-unknown`; strict doctor classifies indeterminate drift
as unhealthy, exit 2.

**Proof.** The probe passes `demo.js` and `demo.ts` inventory records through the
real producer builder with the default registry. TypeScript receives a
configuration hash; JavaScript receives `None` and
`configuration-basis-unknown`. Replaying the reported Obsidian module's recorded
basis produces `basis-incompatible`. Supplying the missing registry mapping to
the in-memory producer inputs, then using that producer on both comparison
sides, produces `current`. This is a focused provenance/freshness reproduction,
not a fresh end-to-end doctor run.

**Fix locations.**

- [config.py:279](../src/llm_wiki_cli/config.py#L279): the family is registered as `typescript`.
- [common.py:102](../src/llm_wiki_cli/extractors/common.py#L102): `.js`/`.jsx` output is labeled `javascript`.
- [knowledge_orchestration.py:1234](../src/llm_wiki_cli/services/knowledge_orchestration.py#L1234): producer selection looks up the emitted label directly.
- [knowledge_envelope.py:1820](../src/llm_wiki_cli/services/knowledge_envelope.py#L1820): missing configuration becomes an unknown-basis limitation.

**Fix plan.**

1. Resolve the producing extractor family separately from the inventory's
   precise language. Map built-in JavaScript output to the selected TypeScript
   extractor registration when constructing provenance. Keep the recorded
   language `javascript` and the existing JavaScript component identity.
2. Use the selected entry point, inventory mode, and emitted language in the
   existing safe configuration hash. Apply the same resolution in generation
   and live evaluation. Preserve explicit JavaScript plugin precedence and
   attribute TypeScript-family plugin output to its actual producer.
3. Keep unknown provenance conservative when the producing registration really
   is unavailable. Do not weaken freshness validation or register a second
   executing extractor merely to manufacture the missing lookup key.
4. Refresh affected artifacts through supported bootstrap/sync paths. A new
   binary cannot make an old unknown recorded basis reliable without a new
   observation; do not patch hashes into historical knowledge JSON.

**Acceptance and validation.**

- Add producer tests for `.js`, `.jsx`, `.ts`, `.tsx`, mixed inventories, missing
  registrations, and plugin overrides. Repeat identical inputs to verify stable
  hashes; relevant producer changes must still invalidate freshness.
- Add a small runtime knowledge generation/live-evaluation test showing a
  JavaScript module is `current` immediately after generation.
- With an already prepared TypeScript helper, bootstrap a minimal JavaScript
  fixture and run `doctor --strict --jobs 1`; require exit 0 when the fixture has
  no other health issues. Run the existing unknown-configuration tests unchanged.
- Validate old-artifact refresh, manifest/knowledge consistency, and a second
  no-change run. Cover producer reuse so old unknown metadata is not retained
  indefinitely after an explicitly requested refresh.

**Dependencies and risk.** No dependency on the other tickets. Producer hashes
and plugin attribution are compatibility-sensitive. This fix does not promise
that unrelated health diagnostics disappear.

## VB-02: Build workflow sequences from actual call evidence

**Impact.** A function with no calls can be documented as executing three or
more imported types. A function that really calls those modules can be missed
when its signature and docstring do not mention them. The generated `Sequence`
claims to be a static call-chain projection, so these are incorrect structural
facts, even though the page disclaims runtime ordering.

**Proof.** `annotations_only(a: A, b: B, c: C) -> A: return a` has an empty
captured call list but becomes the workflow `types_a.A -> types_b.B -> types_c.C`.
The companion `calls_only(): return C(B(A()))` has three captured calls and no
workflow. The repository's `append_log` page exhibits the same signature-derived
sequence.

**Fix locations.**

- [extraction_service.py:2429](../src/llm_wiki_cli/services/extraction_service.py#L2429): substring checks of annotations, decorators, and docstrings.
- [extraction_service.py:2444](../src/llm_wiki_cli/services/extraction_service.py#L2444): those references become the workflow chain.
- [bootstrap_runtime.py:2337](../src/llm_wiki_cli/services/bootstrap_runtime.py#L2337): the chain is rendered as `Sequence`.
- [sync_cmd.py:5148](../src/llm_wiki_cli/commands/sync_cmd.py#L5148): regeneration and preservation of existing workflow pages.

**Fix plan.**

1. Build candidate membership and sequence entries from captured in-body calls
   and their resolved targets. Reuse extraction/resolution primitives; do not
   add a second AST traversal that repeats the signature-reference heuristic.
2. Count distinct resolved project modules for the existing workflow threshold.
   Annotation, return-type, decorator, and docstring references may describe
   structural relationships but must not create call steps or qualify a
   function as a workflow by themselves.
3. Preserve call-site provenance, deterministic source ordering, alias handling,
   and qualified module identity. Treat constructor calls as calls. Preserve
   uncertainty for ambiguous targets; do not present a static traversal as a
   proven branch path or runtime evaluation order.
4. Audit all `get_call_graph()` consumers in extract, bootstrap, lint, and sync.
   Handle formerly generated workflows that no longer qualify through the
   existing managed-surface retirement rules. Preserve authored `Behavior`
   sections and unmanaged pages; check manifest and knowledge references.

**Acceptance and validation.**

- The no-call fixture must not produce a fabricated call sequence. Add negative
  cases for docstrings, similarly named symbols, return annotations, decorators,
  and classes mentioned only as types.
- Body calls across the threshold number of modules must be recognized even
  with no annotations. Cover imported aliases, module-name collisions, repeated
  calls, methods, nested scopes, and unresolved receivers.
- Revise tests that currently encode annotation-derived workflow membership.
  Add bootstrap and sync checks for generated-only and authored workflow pages
  that stop qualifying. Require deterministic output and intact links/metadata.
- Recheck the reported `append_log`, `print_dry_run_plan`, and
  `finalize_bootstrap_artifacts` cases: no type-only reference may appear as an
  executed step. Do not assert that an entire helper must be omitted solely
  because it is private.

**Dependencies and risk.** Can be implemented independently. Coordinate with
VB-03 if sequence identity helpers are shared. This has the largest surface
migration risk because workflow membership and page counts will change.

## VB-03: Separate participant identity from its displayed symbol

**Impact.** A wrapper forwarding to an unresolved method with the same name
renders as a self-message. Different internal modules with identical function
names can also collide because only the symbol is used as participant identity.
The underlying unresolved edge is not proof of recursive execution.

**Proof.** For `check_wiki(service): return service.check_wiki()`, resolution
returns `to.file=None`, `kind=unresolved`, and `name=service.check_wiki`. The
diagram nevertheless emits a single participant and `p0-->>p0: check_wiki`.
A real bare recursive call remains an internal edge in the control fixture.

**Fix locations.**

- [entrypoints.py:1144](../src/llm_wiki_cli/services/entrypoints.py#L1144): steps already preserve full edge metadata.
- [bootstrap_runtime.py:2465](../src/llm_wiki_cli/services/bootstrap_runtime.py#L2465): participant construction discards file and receiver identity.
- [diagrams.py:324](../src/llm_wiki_cli/services/diagrams.py#L324): aliases are keyed by the supplied participant value.

**Fix plan.**

1. Give internal participants stable identities based on source path and
   qualified callable symbol. Give unresolved/external participants identities
   based on caller scope and the full captured receiver expression, with a
   namespace distinct from internal identities.
2. Carry identity separately from a readable label into sequence rendering and
   participant-budget counting. Show enough receiver/module context to
   distinguish colliding labels. Keep the existing generic diagram-call
   contract compatible or adapt its callers together.
3. Keep resolution conservative. Do not force `service.check_wiki()` to the
   wrapper, guess a receiver type, or suppress genuine self-recursive edges.
4. Use distinguishable labels in the associated call-data rows. The data-flow
   diagram already uses separate step IDs; avoid changing edge semantics solely
   to repair presentation.

**Acceptance and validation.**

- Delegation renders two participants and no self-message; its unresolved
  classification and full call expression remain available.
- Same-named functions in different modules and different receiver expressions
  remain distinct. Real bare recursion and `self`/`cls` recursion still render
  self-messages when resolution establishes the same callable.
- Recheck `mcp-check_wiki`, `mcp-query_documentation`, and `api-get_concept`.
  Preserve deterministic aliases, escaping, diagram limits, omission counts,
  and external/unresolved arrow styles.
- Extend focused extraction, flow-rendering, and sequence-rendering tests.

**Dependencies and risk.** No blocking dependency. Compatibility risk is confined
to diagram inputs, labels, and generated text; callers of the generic renderer
must retain their existing behavior.

## VB-04: Preserve TypedDict key presence semantics

**Impact.** `ContextKnowledgeResult.selection` may be absent, but extraction sets
`required=True` and its entity page says `*required*`. Consumers relying on that
contract can access an absent key. This does not mean the field is nullable or
has a Python default value.

**Proof.** The actual class reports `__optional_keys__ == {'selection'}`. Its
eight inherited base keys remain required. Extraction of the same source sets
the `selection` attribute's `required` flag to true, and rendering repeats it.

**Fix locations.**

- [python_extractor.py:1125](../src/llm_wiki_cli/extractors/python_extractor.py#L1125): class extraction lacks TypedDict totality/inheritance classification.
- [python_contracts.py:380](../src/llm_wiki_cli/extractors/python_contracts.py#L380): any annotation without an assigned value becomes required.
- [bootstrap_runtime.py:1743](../src/llm_wiki_cli/services/bootstrap_runtime.py#L1743): the basic attribute table infers requiredness from a missing default, ignoring explicit field metadata.
- [api_types.py:48](../src/llm_wiki_cli/api_types.py#L48): required base and `total=False` subclass reproducing the error.

**Fix plan.**

1. Statically recognize TypedDict classes and resolvable inherited TypedDict
   bases, including import aliases. Capture the totality applying to keys
   declared in each class. Do not import or execute arbitrary source modules.
2. Compute key requiredness separately from defaults and nullability. Apply
   `Required`/`NotRequired` overrides where statically known. Preserve inherited
   keys' original requiredness; a subclass's `total=False` does not make every
   inherited key optional, and inherited `total=False` does not make new keys
   in a default-total subclass optional.
3. Render TypedDict key presence from the explicit metadata, including the
   existing basic-table path. Do not encode `*optional*` as a fictitious default
   string. Keep ordinary classes, dataclasses, and Pydantic handling intact.
4. Check inventory normalization and knowledge observation hashing, then
   regenerate affected entity pages and metadata through normal supported
   commands so optionality changes are visible to freshness consumers.

**Acceptance and validation.**

- `ContextKnowledgeResult.selection` extracts as `required=False` and renders
  optional; inherited required keys stay required.
- Cover direct `TypedDict(total=False)`, default totality, inherited bases,
  explicit `Required`/`NotRequired`, aliases, and unresolved-base behavior.
  Use runtime key sets only as test oracles for safe fixture classes.
- Cover optional-but-nonnullable and required-but-nullable keys, plus unchanged
  dataclass/Pydantic/default-field rendering.
- Add focused extractor, entity-rendering, and knowledge-observation tests;
  assert bootstrap/sync output parity after the schema fact changes.

**Dependencies and risk.** No dependency on the other tickets. Metadata and
observation hashes can change. Unknown inheritance must remain explicit rather
than being guessed from a class name.

## Execution and closure plan

1. Implement VB-01 first because it blocks strict health for affected JavaScript
   modules. Then address VB-02's systematically false workflow evidence.
2. Implement VB-03 and VB-04 as separate changes with their own targeted checks.
   These tickets can be scheduled independently; no parallel heavy gates are
   required.
3. For each implementation, demonstrate its acceptance cases failing before the
   fix and passing afterward. Existing tests passing during this review do not
   demonstrate that any of these four bugs is fixed.
4. Run heavy extraction, full-suite, lint, sync, and build checks serially; use
   `--jobs 1` where supported. Keep all Python tooling in the project's `.venv`.
   Use portable paths and fixture construction for Windows, macOS, and Ubuntu.
   Respect the requested Python 3.9+ source compatibility; the current package
   metadata separately declares `>=3.10`, so installation support for 3.9 is
   not established by this review.
5. After actual behavior changes, update affected user-facing documentation and
   the sibling wiki where applicable. Keep this engineering verification record
   and internal test details out of published product pages.
6. Close a ticket only with its acceptance evidence, artifact refresh checks,
   and any necessary migration notes. Do not close all findings merely because
   strict lint or a structurally valid Mermaid diagram passes.
