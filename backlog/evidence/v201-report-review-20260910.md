# Verification review of the v2.0.1 forensic findings

Engineering review record, 2026-09-10. Source revision:
`1f281a14389c4efefeb1968dd4681704151ed7f7` (`agent-wiki-cli` 2.0.1).

**Result: four confirmed bugs from nine numbered findings.** The
[separate fixing backlog](../v201-verified-bugs-20260910.md) contains only those
four bugs. The other five findings describe deliberate behavior, a limitation,
or a possible enhancement without establishing the alleged correctness failure.
Some observations in the report are accurate while their root-cause explanation
or proposed fix is not.

The input was `reports/agent_verification_findings_report_python_wiki_llm_v201_20260910.md`.
Its SHA-256 is `4a6a5e0a0f7940c63499feb908301b72b82b6eaed2072823024ed8fd1b871edf`.
Its recommendations and embedded commands were treated as claims to assess,
not instructions to implement. The input report remains unchanged and ignored
by Git. No product implementation, generated wiki, or public documentation was
changed as part of this review.

## Verification scope and evidence

- Inspected current source, the corresponding checked-in generated pages, and
  relevant existing tests. The external audit workspace and its original timing,
  sampling, and execution logs were not independently re-run or certified.
- Ran the required initial context command once:
  `.venv/bin/llm-wiki context --budget 8000 --src-dir . --format markdown --focus changed --read-only`.
  It exited 1 because the TypeScript helper is not prepared. That environment
  prerequisite failure is not proof of a code defect. No helper installation,
  full bootstrap, live doctor run, or full test suite was performed.
- Ran [bounded reproduction probes](../../tests/verify_v201_report.py) for all
  nine claims. [Saved output](v201-findings-observations.json) records the exact
  observations on Linux with Python 3.14.4. The script is an evidence collector,
  not a regression suite asserting that the current product is correct.
- For FINDING-03, validated the reported JavaScript module and producer in
  isolation from the large knowledge artifact, then replayed its recorded
  source/observation basis. The changed-producer comparison is a controlled
  in-memory input, not an implemented fix or a live-source freshness verdict.
- Ran 45 focused existing tests: **45 passed in 1.44 seconds**. Their coverage
  helps distinguish intended behavior from defects but does not cover all
  identified bugs. Windows, macOS, and other Python versions were not run.

Reproduce the observations from the repository root:

```bash
.venv/bin/python tests/verify_v201_report.py
```

Existing-test command used, with no other heavy gate running:

```bash
.venv/bin/pytest -q \
  tests/test_extract.py::TestGetCallGraph \
  tests/test_extract.py::TestResolveCallEdges \
  tests/test_diagrams.py::TestSequenceDiagram \
  tests/test_dependencies.py::TestImportTimeEdges \
  tests/test_module_maps.py \
  tests/test_bootstrap.py::TestGenerateFlowMd \
  tests/test_bootstrap.py::TestGenerateLoadOrderMd \
  tests/test_knowledge_freshness.py::test_unknown_extractor_configuration_is_incompatible \
  tests/test_doctor.py::test_strict_mode_escalates_indeterminate_drift
```

## Disposition of every finding

| Report finding | Verdict | Evidence and corrected interpretation | Backlog |
|---|---|---|---|
| FINDING-01: phantom recursion | Confirmed presentation bug; resolver attribution rejected | An unresolved receiver call retains `to.file=None` and its full name. Sequence rendering collapses caller and callee by bare symbol. | VB-03 / P2 |
| FINDING-02: type hints as workflow steps | Confirmed structural correctness bug | A no-call body acquires a three-item sequence from annotations; a body with three real calls is missed when signature references are absent. | VB-02 / P1 |
| FINDING-03: JavaScript unknown producer | Confirmed provenance bug | Emitted language is `javascript`; the registry key is `typescript`. Direct lookup loses the known producing entry point and configuration. | VB-01 / P1 |
| FINDING-04: TYPE_CHECKING cycles | Alleged runtime-cycle bug not reproduced | The local view retains coupling edges intentionally, but runtime cycles and local cycle warnings are empty. Scope labels would improve clarity. | Excluded |
| FINDING-05: TypedDict optionality | Confirmed extraction and rendering bug | Actual runtime key sets say `selection` is optional; inventory and entity output say required. | VB-04 / P2 |
| FINDING-06: sequence starvation | Confirmed limitation; no violated correctness contract established | The first 30 interactions are intentionally shown and omissions/depth limits are disclosed. Main-path selection would be a separate design change. | Excluded |
| FINDING-07: polyglot order | No incorrect dependency constraint demonstrated | Independent JavaScript/Rust nodes appear in a valid topological order; no cross-runtime edges are manufactured. Runtime grouping could improve presentation. | Excluded |
| FINDING-08: missing explanations | Source documentation gap / enhancement | The source has no relevant docstrings, and the generator emits its documented source fallback. No supplied source prose is lost. | Excluded |
| FINDING-09: missing context cache flag | Confirmed interface asymmetry; enhancement | The parser rejects the flag, but supported and documented `LLM_WIKI_CACHE_DIR` selection works. No promised context option was found. | Excluded |

## Confirmed bugs and corrections to the report

### FINDING-01: participant identity is lost during rendering

The reported `mcp-check_wiki` page does contain `p0-->>p0`. However,
[_resolve_call](../../src/llm_wiki_cli/services/extraction_service.py#L2582)
explicitly restricts same-file/global symbol fallback to calls without an
attribute receiver. It returns an unresolved edge for `service.check_wiki()`;
the page's own **Static analysis gaps** section says so.

[_flow_interactions](../../src/llm_wiki_cli/services/bootstrap_runtime.py#L2465)
uses only `step['symbol']` for both participant identities. The
[renderer](../../src/llm_wiki_cli/services/diagrams.py#L324) then allocates one
alias for the two equal strings. The defect is a false self-message in the
diagram and indistinguishable labels in call-data rows, not a demonstrated
recursive edge in the call resolver. Existing data-flow step IDs remain
distinct. A blanket anti-self-loop guard would hide genuine recursion and
would not fix other same-named participant collisions.

### FINDING-02: the workflow builder does not consume body calls

[_function_references_symbol](../../src/llm_wiki_cli/services/extraction_service.py#L2429)
matches imported names as substrings in parameter/return types, decorators, and
docstrings. [_referenced_import_chain](../../src/llm_wiki_cli/services/extraction_service.py#L2444)
turns those matches into the chain, in imported-symbol iteration order.
[_generate_workflow_md](../../src/llm_wiki_cli/services/bootstrap_runtime.py#L2337)
labels it a static call-chain projection and a numbered `Sequence`.

The no-call fixture produces `types_a.A`, `types_b.B`, `types_c.C`. The real-call
fixture captures `C`, `B`, `A` but produces no workflow. Thus the problem is
broader than forgetting to skip annotation AST nodes: this builder does not use
the captured body calls at all. The actual extractor already separates body
calls from signatures. The report's suggested `services/workflows.py` does not
exist in this checkout.

### FINDING-03: an emitted-language/producer-family mismatch

The [registry](../../src/llm_wiki_cli/config.py#L279) registers the shared Node
helper as `typescript`; [output normalization](../../src/llm_wiki_cli/extractors/common.py#L102)
labels `.js`/`.jsx` records `javascript`.
[_producer_evidence](../../src/llm_wiki_cli/services/knowledge_orchestration.py#L1234)
looks up `registry.get(language)` and therefore supplies no configuration for
JavaScript. [Envelope construction](../../src/llm_wiki_cli/services/knowledge_envelope.py#L1820)
correctly records that missing basis as unknown. This is not a separate
JavaScript plugin failing to calculate its own hash.

With the same reported module hashes on both sides, freshness returns
`basis-incompatible / extractor-configuration-unknown`. A producer built with
the missing alias supplied as a controlled input returns `current` when used
on both sides. [Strict classification](../../src/llm_wiki_cli/services/doctor_service.py#L599)
returns exit 2 for indeterminate drift. The defect is established without
claiming a new full doctor execution or reproducing the report's entire count
of 1,147 concepts. Missing or unsupported freshness in other concepts requires
its own classification; removing this defect is not a guarantee that any
arbitrary repository will pass doctor.

Retain conservative handling of genuinely missing provenance. The report's
alternative proposal to treat unknown configuration as a known static default
would bypass evidence rather than repair the source of the missing metadata.

### FINDING-05: both extraction and the basic renderer need correction

The actual [TypedDict subclass](../../src/llm_wiki_cli/api_types.py#L60) reports
`selection` in `__optional_keys__`. Its eight inherited keys remain required.
The [attribute extractor](../../src/llm_wiki_cli/extractors/python_contracts.py#L393)
sets `required` based on whether the annotation has an assigned value, while
the [basic attribute renderer](../../src/llm_wiki_cli/services/bootstrap_runtime.py#L1743)
independently infers `*required*` from a missing default. Correcting only one
layer is insufficient.

The report's statement that `total=False` makes all keys optional is too broad
for inherited TypedDicts: it controls keys declared in that class; inherited
requiredness is retained. Storing `*optional*` as a default string would also
conflate dictionary key presence with value defaults.

## Why five findings are excluded from the bug backlog

### FINDING-04: coupling is not an import-time cycle warning

[build_dependency_graph](../../src/llm_wiki_cli/services/dependencies.py#L140)
explicitly exposes both all-import `edges` for coupling and
`import_time_edges` for runtime load constraints. The metadata field is
`scope='type_checking'`, not the report's claimed `is_type_checking=True`.
[analyze_dependencies](../../src/llm_wiki_cli/services/dependencies.py#L3030)
keeps runtime and deferred cycles separate; [module maps](../../src/llm_wiki_cli/services/module_maps.py#L218)
take cycle groups from the runtime `cycles` result.

The reproduction retains both local arrows but reports `runtime_cycles=[]`,
`cycle_participation=False`, and no local cycle warning. The supplied module
page likewise has ordinary coupling arrows, without the thick-arrow cycle
warning. A visible scope legend, dashed type-only edges, or a scope column is
reasonable presentation work, but the alleged fatal circular-import detection
is not established. Deleting type-only edges from every dependency view would
lose intended coupling information.

### FINDING-06: a bounded static projection with explicit omissions

[build_flow](../../src/llm_wiki_cli/services/entrypoints.py#L1179) performs a
bounded depth-first static traversal. [_bounded_sequence_diagram](../../src/llm_wiki_cli/services/bootstrap_runtime.py#L2497)
selects the first 30 interactions subject to additional diagram budgets.
The `cli-context` page explicitly discloses 30 of 1,669 interactions and the
depth limit. The reproduction emits 30 of 40 with the correct omitted count;
the [existing test](../../tests/test_bootstrap.py#L3197) asserts this policy.

The omitted main path is a useful quality concern, but the page does not claim
complete runtime behavior. Choosing a representative main path or grouping
argument-parser calls needs a defined selection policy. A global blacklist of
built-ins is not an established correctness fix and could hide relevant calls.

### FINDING-07: disconnected runtimes do not invalidate a topological order

A topological order constrains only nodes joined by dependency edges. The
reproduction orders the JavaScript/Rust nodes first and still satisfies every
Python import constraint; there are zero cross-runtime edges. Existing tests
[retain isolated language modules](../../tests/test_bootstrap.py#L3860), and the
[generated notes](../../src/llm_wiki_cli/services/bootstrap_runtime.py#L3276)
describe a static dependency projection.

Grouping by runtime or independent component would make the page clearer. The
report has not demonstrated that JavaScript or Rust is imported by Python, or
that an actual dependency is ordered incorrectly. Removing disconnected
modules would change the intended inventory coverage.

### FINDING-08: absent source prose is not dropped evidence

`ci_check_cmd.py` has no module docstring or docstrings for its four functions.
[The renderer](../../src/llm_wiki_cli/services/bootstrap_runtime.py#L1928) emits
the source-location fallback for that case. The report also mentions
`_WorkflowResult` without a separate catalog finding; it has no source docstring
and uses the same fallback policy.

Adding explanatory source docstrings or semantic descriptions is worthwhile,
but the report identifies no lost docstring, wrong extracted fact, or contract
requiring automatic prose synthesis. This is excluded from a proven-bugs-only
backlog.

### FINDING-09: an unsupported convenience flag with a documented alternative

[_add_context_command](../../src/llm_wiki_cli/cli.py#L1880) does omit
`--helper-cache-dir`; the parser reproduction returns exit 2. Context's
[inventory adapter](../../src/llm_wiki_cli/services/context_service.py#L274)
also has no matching parameter, so adding just the parser option would not
implement the feature.

However, [helper cache resolution](../../src/llm_wiki_cli/services/extractor_helpers.py#L95)
supports `LLM_WIKI_CACHE_DIR`, and the [README](../../README.md#L966) documents
that setting. The probe verifies this path selection. The report's claim that
the environment variable is undocumented is false. An explicit context flag
would be an interface enhancement; no promised flag or broken supported cache
selection was found. A helper not prepared at the selected location is a
separate environment prerequisite.

## Limits on the report's aggregate conclusions

The original sample counts mix affected pages with independent defect classes.
The 62.1% sampled-page figure is not a proven codebase-wide bug rate, and this
review does not reproduce that sampling experiment. Several presumed
root-cause files (`python_ast.py`, `services/workflows.py`,
`services/load_order.py`, `call_graph_tracer.py`) do not exist here. Use the
verified locations above when implementing fixes.

The useful outcome is four evidence-backed tickets with bounded impact and
concrete acceptance checks. All four defects remain open after this review.
