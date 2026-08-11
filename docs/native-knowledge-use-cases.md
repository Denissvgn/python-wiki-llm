# Native Knowledge Layer: Real-World Use Cases and Value

This guide describes implemented capabilities, optional integrations, and
candidate evaluation designs. It does not report completed field evaluations.

## Executive conclusion

The native knowledge layer's real value is not that it creates another
repository graph. Its value is that it qualifies repository documentation and
static-analysis observations before an agent, CI job, or downstream tool relies
on them.

The strongest product statement is:

> LLM Wiki is an evidence-aware repository memory that tells agents and CI what
> a concept is, what source observation produced it, whether that observation
> still compares to live code, and why.

A shorter positioning statement is:

> Fresh, evidence-qualified repository context for coding agents and
> documentation CI.

This is meaningfully different from ordinary repository search, generated
documentation, or retrieval-augmented generation:

- search retrieves a plausible item;
- generated documentation explains an observed item;
- the native layer additionally reports whether the item is available,
  comparable, stale, unsupported, reviewed, bounded, or backed by a resolvable
  structural observation.

That qualification layer is the defensible part of the project. The Markdown
wiki, source extractors, graph, context builder, MCP server, and projections are
delivery mechanisms around it.

## The problem it can solve

Coding agents and maintainers regularly consume repository context with no
machine-readable answer to five questions:

1. Did this information come from source, prose, an inference, or a governance
   decision?
2. Does its recorded observation basis still compare to the live repository?
3. Is the information absent, invalid, unsupported, or merely unmatched?
4. Is a graph result complete enough for the current question, or was it
   truncated or limited upstream?
5. Did a human review this exact semantic section, and is that review still
   valid after subsequent edits?

Conventional repository indexes generally answer none or only part of these
questions. This creates predictable failure modes:

- an agent confidently uses stale architecture prose;
- CI can detect changed files but cannot identify which documented concepts
  drifted;
- a graph query silently looks complete even when analysis or response limits
  omitted observations;
- a rename breaks long-lived links and agent memory;
- a page-level approval remains attached after the reviewed paragraph changes;
- public projections leak internal metadata or imply live freshness they did
  not evaluate.

After bootstrap or sync commits a knowledge-capable wiki, its generated
observations are the normal bounded evidence plane for knowledge-aware agents.
The implementation has the primitives needed to keep that plane qualified:

- explicit `ready`, `absent`, `degraded`, and `unsupported` availability;
- persisted observation bases and read-time freshness;
- structural evidence distinct from semantic review and machine verification;
- exact concept locators, optional durable UIDs, aliases, and lifecycle events;
- evidence-backed typed relationships with resolution and coverage;
- section ownership and scoped semantic hashes;
- bounded context, API, and MCP responses with totals and truncation;
- opt-in, redacted Site and Obsidian projections.

The normative behavior is documented in
[Native knowledge reads](../docs/native-knowledge.md).

## Who receives value

### Coding-agent and IDE integrators

They receive a stable read contract over MCP or Python rather than another
prompt-sized repository dump. An agent can branch on availability, select
current evidence-backed concepts, traverse bounded relationships, and request
detailed evidence only when needed.

### Repository and documentation maintainers

They can opt into concept-level native drift diagnostics by passing
`--knowledge-drift-report` to `lint` or `ci-check`. Native drift findings remain
nonblocking warnings; structural integrity, projection, governance, review, and
verification failures retain their normal validation behavior. The useful unit
becomes “the documented `User` concept changed” instead of only “some bytes in
`models.py` changed.”

### Documentation-platform and developer-portal teams

They receive Markdown-first content plus a validated metadata projection. The
canonical prose remains editable and portable; Site and Obsidian exports remain
disposable, privacy-scoped views.

### Knowledge and RAG platform authors

They receive qualification metadata for chunks and links without being forced
to adopt LLM Wiki as a vector store. Native knowledge can sit around a retrieval
system as a trust and filtering envelope.

### Static-analysis and developer-tool authors

They receive a typed, evidence-carrying graph that preserves unresolved,
ambiguous, external, and coverage-limited observations instead of coercing them
into false certainty.

## Why the developer community may care

The community value is a reusable vocabulary and boundary, not just this
project's JSON file:

- **Availability is not emptiness.** An absent or rejected projection is not an
  empty trustworthy graph.
- **Freshness is computed, not asserted forever.** A persisted hash records an
  observation basis; a live reader decides whether it is still comparable.
- **Evidence, freshness, review, verification, and lifecycle are independent.**
  A clean extractor run does not prove prose true or approved.
- **Unknowns survive normalization.** Ambiguous links, unsupported analyzers,
  missing locations, and truncated samples remain visible.
- **Identity can outlive layout.** Optional UIDs and aliases allow durable
  references while keeping current Markdown paths human-readable.
- **Consumers are bounded and deterministic.** A result says what was returned,
  what was omitted, and what upstream coverage means.
- **Metadata remains inert.** Document or knowledge content cannot select code,
  commands, network requests, plugins, or verification procedures.

These rules are useful to agent frameworks, documentation generators, and
repository-context systems even if they use a different storage format.

Adjacent products validate demand for reusable repository context and
docs-as-code:

- [GitHub Copilot Spaces](https://docs.github.com/en/copilot/concepts/context/spaces)
  packages reusable, synchronized context for Copilot.
- [Sourcegraph Cody context](https://sourcegraph.com/docs/cody/core-concepts/context)
  uses search and code-graph context to ground coding assistance.
- [Backstage TechDocs](https://backstage.io/docs/features/techdocs/creating-and-publishing/)
  treats documentation as code and publishes it through a developer portal.
- The [Model Context Protocol server model](https://modelcontextprotocol.io/docs/learn/server-concepts)
  supplies a standard delivery surface for resources and tools.
- Empirical work on
  [outdated software documentation](https://arxiv.org/abs/2212.01479)
  supports treating documentation drift as a recurring engineering problem.

LLM Wiki should not claim those products lack freshness or provenance features
in all forms. Its own differentiator is narrower: one local, deterministic
contract that joins Markdown, structural observations, live comparability,
typed relationships, and optional governance.

## Value model

The native layer creates value through this chain:

```text
source + canonical Markdown
        |
        v
recorded observations + producer basis
        |
        v
validated committed projection
        |
        +--> live freshness comparison
        +--> typed relationships and coverage
        +--> durable identity and scoped review
        |
        v
qualified context for CI, agents, and projections
```

The value disappears if a consumer drops the qualifiers and treats the
projection as an always-current knowledge database. Every proposed workflow
therefore needs to preserve availability, evidence, freshness, bounds, and
authority boundaries.

## Use cases

| ID | Use case | Primary actor | User value | Current availability | Adoption tier |
|---|---|---|---|---|---|
| NK-UC-001 | Concept-level documentation drift diagnostics | Maintainer / reviewer | Surface stale repository documentation for review or external policy | Implemented as opt-in, nonblocking diagnostics | Core |
| NK-UC-002 | Evidence-qualified context for coding agents | Agent / IDE integrator | Reduce confident use of stale or unsupported context | Implemented | Core |
| NK-UC-003 | Evidence-backed change-impact analysis | Developer / reviewer | Find affected code and docs with visible graph limits | Implemented with a bundled workflow | Core |
| NK-UC-004 | Qualified onboarding and incident orientation | New contributor / responder | Reach the relevant architecture faster without presenting static evidence as runtime truth | Implemented with bundled guidance | Recommended |
| NK-UC-005 | Durable concept identity through refactors | Maintainer / tool integrator | Preserve links, lifecycle, and memory across moves | Implemented, opt-in | Recommended |
| NK-UC-006 | Section-scoped review and safe verification | Reviewer / governance owner | Keep review validity precise and auditable | Implemented, opt-in | Recommended |
| NK-UC-007 | Privacy-scoped Site and Obsidian projections | Docs publisher / PKM user | Publish useful metadata without moving authority or leaking private detail | Implemented, opt-in | Recommended |
| NK-UC-008 | Trust metadata around RAG | Retrieval-platform author | Filter or label retrieved chunks by evidence and freshness | Core metadata is available; an external adapter is not included | Optional |
| NK-UC-009 | Specialized static triage acceleration | Security / dependency / infrastructure reviewer | Rank static evidence while keeping gaps and limits explicit | Static workflows are available; native enrichment varies by workflow | Optional |

## NK-UC-001 — Concept-level documentation drift diagnostics

### Job to be done

When a pull request changes code, report whether committed documentation and
structural observations still compare to the affected concepts so maintainers
or a separately configured CI policy can decide what follow-up is required.
LLM Wiki's native drift findings are diagnostic-only and never form a built-in
blocking gate.

### Actors

- pull-request author;
- repository maintainer;
- documentation owner;
- CI platform.

### Trigger

A branch changes source, extractor configuration, generated documentation
inputs, governance state, or canonical Markdown.

### Preconditions

- the wiki and manifest are version-controlled;
- the knowledge projection has been generated at least once, or the repository
  intentionally remains in compatible surface-only mode;
- CI can run the same supported extractor configuration used by the project.

### Workflow

1. CI runs `llm-wiki ci-check --knowledge-drift-report` without first
   rewriting the wiki.
2. Strict validation loads the committed manifest, surface, Markdown, and
   knowledge projection as one snapshot.
3. A live comparison classifies promised module/entity observations.
4. Structural, projection, governance, review, and verification failures keep
   the ordinary `ci-check` behavior. Native drift findings such as changed or
   missing sources and incompatible bases are emitted as warning diagnostics
   and do not change the exit status.
5. `nonsemantic-source-change` remains a diagnostic rather than a hard failure.
6. The developer runs `wiki-sync`, reviews semantic surfaces, and reruns the
   diagnostics. An external CI wrapper may separately apply its own policy to
   the structured report.

### Output

- stable finding category and reason;
- affected concept locator or canonical page;
- low-cardinality aggregate summary suitable for CI;
- no raw evidence or private repository metadata in the ordinary report.

### Real value

This creates a documentation-specific review signal that is more precise than
“docs changed with code” and more conservative than an LLM judging prose from
scratch. It can surface stale concepts even when Markdown links and syntax
remain valid, without silently changing repository merge policy.

### Success measures

- at least 80% of surfaced drift findings are actionable;
- a planned four-week evaluation across three to five repositories surfaces at
  least five real stale-documentation defects;
- fewer than one false alarm per ten pull requests;
- `unknown` plus `basis-incompatible` below 20% after setup stabilization;
- less than 15% CI wall-time overhead relative to the existing documentation
  validation command.

### Boundaries

- “current” means unchanged since the recorded observation, not semantically
  correct;
- native drift findings are opt-in, warning-only diagnostics; any blocking
  policy belongs to an external CI integration;
- CI should not auto-edit or auto-approve semantic prose;
- a legacy wiki with no declared projection remains compatible;
- the check is only as broad as extractor and analyzer coverage.

## NK-UC-002 — Evidence-qualified context for coding agents

### Job to be done

Before an agent answers an architecture question or edits code, supply bounded
repository context that exposes whether the referenced concepts are current,
stale, unsupported, or unavailable.

### Actors

- coding agent;
- IDE or agent-framework integrator;
- maintainer supervising an agent.

### Trigger

The agent needs repository-wide orientation, a named concept, or a neighborhood
of related concepts.

### Workflow

1. For a broad task, build one live documentation query service or one bounded
   context request.
2. Inspect `knowledge.availability`, `reason`, and
   `freshness_evaluated` before interpreting matches. In explicit v2 context,
   also branch on `status`, `selected`, and `fallback.used`.
3. Use exact locators, canonical paths, durable UIDs, or persisted aliases for
   identity. Do not fuzzy-resolve concept identity.
4. For ordinary work, prefer compact results and typed traversal without raw
   evidence samples.
5. Request `explain_evidence` or `include_evidence=true` only for diagnostics
   that need repository-sensitive details.
6. Preserve totals, truncation, analyzer coverage, unresolved targets, and
   warnings in the agent's conclusion.
7. Fall back to validated surface/Markdown and targeted source reads when
   native knowledge is absent, degraded, or unsupported.
8. Use `prefer_fresh` only when current-first ordering within the same
   relevance tier is useful under budget pressure. It is not a filter or a
   validity threshold.

### Delivery options

The CLI selects the same explicit v2 contract as a raw
`llm-wiki-context/v2` request:

```console
llm-wiki context --budget 32000 --knowledge-mode auto --read-only
```

Other supported interfaces are:

- Python `query_documentation(...)` for bounded exact or supplied-impact
  queries, and `build_documentation_query_service(...)` when several live
  full-inventory queries should share one service;
- MCP `query_documentation`, `get_context`, `get_context_packet`, and the
  dedicated exact concept and traversal tools.

The shared documentation-query dispatcher discloses whether a request used
only the committed snapshot, targeted supplied-path extraction, or a full
inventory. Symbol, entrypoint, and dependency operations require an explicit
full-inventory opt-in. Supplied paths and unified diffs never establish a
global live-freshness claim.

`auto` preserves a successful read-only route through validated surface,
Markdown, and targeted source/runtime evidence when native knowledge is
unavailable. `required` returns `knowledge-required-unavailable` instead. A
ready snapshot-only projection can satisfy `required`, but remains explicitly
not live-qualified. See [Native knowledge reads](native-knowledge.md) for the
exact status, reason, fallback, and bound fields.

### Real value

The layer helps the agent decide how much confidence and follow-up inspection a
piece of context deserves. It also avoids repeatedly scanning the repository
when several queries share one constructed service.

### Success measures

Run an A/B evaluation on 15–20 historical engineering tasks across at least
three repositories, holding model and task prompts constant:

- task correctness;
- time to a maintainer-accepted answer or patch;
- token and tool-call use;
- stale-context errors;
- native query use and fallback rate.

Continue if qualified context improves correctness by at least 10 percentage
points or reduces time/tokens by at least 15% without a quality regression.

### Boundaries

- context output limits emitted material, not necessarily scan cost;
- status-only operations do not evaluate freshness;
- a `found: false` result under unavailable knowledge is not proof of absence;
- loaded knowledge is inert, but building a live service can use configured,
  trusted extractor plugins.

## NK-UC-003 — Evidence-backed change-impact analysis

### Job to be done

Before changing a concept, identify the likely code and documentation blast
radius while making ambiguity, unresolved edges, analyzer coverage, and
response truncation visible.

### Actors

- feature developer;
- refactoring owner;
- pull-request reviewer;
- incident remediator.

### Trigger

A proposed change names a symbol, source file, entry point, concept locator, or
durable UID.

### Workflow

1. Resolve the target exactly with `get_concept` when a native identity exists.
2. Use legacy call/flow/dependency queries for detailed source-inventory shapes
   that the typed graph does not replace.
3. Use `traverse_typed_graph` for persisted, typed concept relationships,
   filtering by direction, kind, origin, and resolution.
4. Inspect compact evidence counts and analyzer coverage before deciding that a
   neighborhood is complete enough.
5. Use `explain_evidence` for the small set of decisive edges.
6. Map impacted concepts to canonical wiki pages and semantic sections.
7. Produce a code-impact summary plus a documentation-update checklist.

### Real value

Legacy call and dependency queries answer useful topology questions. Native
knowledge adds durable identity, typed origins, evidence, resolution, and
coverage. Together they produce a more defensible impact report than either
alone.

### Success measures

Build 25–30 maintainer-authored impact questions with expected affected nodes
and documents:

- required-edge recall and precision;
- answer time;
- unresolved/ambiguous handling;
- percentage of conclusions that disclose applicable coverage limits;
- documentation-update accuracy.

Continue if the workflow improves accuracy by 20 percentage points or reduces
analysis time by 25%, with at least 70% of required edges resolving.

### Boundaries

- the graph is a set of static observations, not transitive or runtime truth;
- a non-truncated response does not imply complete analyzer coverage;
- unresolved or external endpoints must not be silently discarded;
- source reads remain necessary for behavior not captured by extractors.

## NK-UC-004 — Qualified onboarding and incident orientation

### Job to be done

Help a new contributor or incident responder find the relevant flows,
components, dependencies, and documentation quickly while clearly separating
static architecture observations from live system behavior.

### Actors

- new engineer;
- on-call responder;
- architecture reviewer;
- support engineer.

### Trigger

The user asks “where does this request enter?”, “what owns this behavior?”, or
“what should I read first?”

### Workflow

1. Start from authored onboarding guides or a focused architecture page.
2. Verify the wiki through strict lint or a live context/query operation.
3. Follow exact concept references and typed relationships for the relevant
   flows.
4. Prefer current, evidence-present concepts while retaining visible stale or
   unknown warnings when they are relevant.
5. For incidents, corroborate static observations with logs, metrics, traces,
   deployed configuration, and live runtime state.
6. Record documentation gaps discovered during the investigation for the
   normal sync/review workflow.

### Real value

The layer reduces navigation and confidence-checking time. It does not replace
good narrative guides; it makes their linked structural claims easier to
qualify and revisit.

### Success measures

- five maintainers unfamiliar with a repository complete three orientation
  questions;
- at least three complete setup and first navigation in under 15 minutes;
- at least two reuse the workflow during the following month;
- no participant mistakes static freshness for deployed runtime state.

### Boundaries

- native knowledge is repository state, not production state;
- authored guides remain the human learning surface;
- an incident conclusion needs runtime corroboration.

## NK-UC-005 — Durable concept identity through refactors

### Job to be done

Keep concept references, lifecycle decisions, aliases, and review history
attached to the same logical item when files and pages move.

### Actors

- maintainer of a long-lived or high-churn repository;
- documentation platform owner;
- downstream tool storing concept references.

### Trigger

A module, entity, guide, or architecture concept is renamed, moved,
deprecated, or superseded.

### Workflow

1. Opt in with `llm-wiki knowledge init`.
2. Store durable UIDs in downstream references while continuing to display
   human-readable current paths.
3. Let supported sync/migration renames carry identity automatically.
4. For ambiguous moves, stage an explicit `knowledge move`, then synchronize.
5. Preserve historical coordinates as aliases.
6. Record lifecycle changes explicitly; do not infer them from source removal.
7. Resolve governance conflicts manually and regenerate projections.

### Real value

This is useful where external agent memory, review history, or portal links must
survive repository reorganization. It is unnecessary overhead for short-lived
or low-change repositories.

### Success measures

- percentage of supported renames that retain the intended UID;
- alias lookup success after moves;
- false move/merge rate;
- governance conflict frequency and resolution time;
- percentage of downstream consumers that use the UID rather than only a path.

### Boundaries

- durable governance is opt-in;
- there is no implicit concept merge;
- lifecycle is an authored decision, not inferred deletion;
- the version-controlled ledger is authoritative; the generated projection is
  disposable.

## NK-UC-006 — Section-scoped review and safe verification

### Job to be done

Record that a human reviewed one semantic section and invalidate that review
only when its semantic scope or evidence basis changes. Keep deterministic
machine checks separate.

### Actors

- documentation reviewer;
- domain owner;
- compliance or release coordinator using repository-local evidence;
- CI maintainer.

### Trigger

A high-value explanation, decision, guide section, or workflow needs explicit
human review, or a fixed application-owned integrity check needs a disposable
receipt.

### Workflow

1. Initialize governance if durable review is required.
2. Identify the exact semantic section locator and concept UID.
3. Record a human review with reviewer, method, version, and authored time.
4. On later reads, compute whether the section, evidence basis, or concept
   changed.
5. Use `knowledge verify` only for registered pure checkers.
6. Treat human review, structural freshness, authorship, and machine results as
   independent dimensions.

### Real value

Page-level approval is too broad and becomes noisy when generated blocks churn.
Section-level review preserves useful human assurance while invalidating it
precisely when the reviewed meaning or basis changes.

### Success measures

- valid reviews surviving generated-only churn;
- changed semantic sections invalidating reviews correctly;
- reviewer time per event;
- false-valid and false-expired review rate;
- percentage of high-value sections with a named consumer for review state.

### Boundaries

- this is repository-local governance, not a compliance certification;
- verification receipts are unsigned and disposable;
- document content cannot choose a checker or command;
- review does not make structural evidence current, and freshness does not make
  prose reviewed.

## NK-UC-007 — Privacy-scoped Site and Obsidian projections

### Job to be done

Publish or mirror selected native metadata without changing canonical authority,
claiming live freshness, or exposing private producer and repository details.

### Actors

- documentation publisher;
- internal developer-portal owner;
- Obsidian user;
- multi-repository documentation hub owner.

### Trigger

A maintained, governed wiki is exported to a static site or an Obsidian vault.

### Workflow

1. Synchronize and validate the canonical wiki.
2. Explicitly choose `--knowledge-metadata summary`; legacy output remains the
   default.
3. Use `public-portable` for public output and `internal` only for controlled
   internal destinations.
4. Export and check with matching knowledge options.
5. Treat exported freshness as `not-evaluated` unless a service caller already
   supplied a complete live evaluation.
6. Validate source knowledge hash parity, UID uniqueness, successors, page
   mapping, and hub collisions.
7. Rebuild disposable output rather than hand-editing metadata.

### Real value

The projection makes identity, lifecycle, review state, and typed relationships
useful outside the native JSON while retaining a clear privacy and authority
boundary.

### Success measures

- zero private identity, actor, path, credential, environment, or raw evidence
  leaks in the public profile;
- exact export/check parity;
- no stale enriched mirror accepted;
- downstream usage of UIDs, lifecycle, or relationship sections;
- successful rebuild after deleting the derived output.

### Boundaries

- the metadata option is opt-in;
- projection profiles govern added metadata, not the publication safety of
  canonical prose or media;
- public identity requires explicit corroboration;
- Site/Obsidian output never becomes authoritative.

## NK-UC-008 — Trust metadata around RAG

### Job to be done

Let a retrieval system label, filter, or rerank repository documentation chunks
using native availability, freshness, evidence, identity, lifecycle, and review
metadata.

### Actors

- retrieval-platform author;
- enterprise search integrator;
- agent-memory developer.

### Candidate workflow

1. The existing retrieval system performs chunking, embedding, indexing, and
   search.
2. A thin adapter joins chunks to exact canonical pages, concept locators, or
   section locators.
3. The adapter stores safe projection fields rather than raw evidence.
4. At query time, the consumer can prefer current, active, reviewed concepts or
   visibly retain stale/unknown results.
5. The answer cites both the content and its qualification state.

### Real value

This addresses a common RAG weakness: relevance alone does not indicate whether
retrieved repository context still compares to source or retains valid review.

### Entry condition

Do not build a vector database, embedding pipeline, or general retrieval server
inside the native layer. Proceed only when a named external consumer provides:

- its chunk identity and update contract;
- required qualification fields;
- expected query-time behavior;
- a benchmark corpus;
- a maintainer and delivery path.

### Success measures

- stale-context answer rate;
- retrieval relevance before and after qualification;
- percentage of chunks joined exactly rather than heuristically;
- latency and index-size overhead;
- percentage of users who act on the qualification metadata.

## NK-UC-009 — Specialized static triage acceleration

### Job to be done

Improve security, dependency, and infrastructure triage by using qualified
concept relationships and coverage to prioritize source inspection.

### Candidate workflows

- trace potentially affected import sites from entry points;
- distinguish resolved, ambiguous, external, and unresolved relationships;
- preserve analyzer gaps and truncation as unknown surface;
- map findings back to stable concept/page identities;
- inspect raw source and runtime evidence for decisive conclusions.

### Real value

The native layer can reduce navigation work and make static-analysis limitations
more visible. It is a feeder, not a vulnerability, exploitability, or runtime
assurance engine.

### Boundaries

- do not replace SAST, dependency advisory services, or runtime telemetry;
- no graph path proves a vulnerability reachable;
- no missing edge proves a path safe;
- source and specialist-tool evidence overrides a stale or limited projection.

## Recommended product workflow

The smallest coherent product loop is:

```text
bootstrap/sync
    -> strict lint and ci-check
    -> optional nonblocking `--knowledge-drift-report` diagnostics
    -> MCP/context query with explicit availability
    -> targeted code or semantic-doc change
    -> sync and review
```

Optional governance and distribution extend the loop:

```text
knowledge init
    -> stable UIDs / lifecycle / scoped review
    -> sync
    -> opt-in Site or Obsidian metadata
    -> matching projection check
```

This is the most direct demonstration. A large schema tour is less persuasive
than showing one stale documented concept surfaced by an opt-in CI diagnostic,
one agent query that reports why it is stale, and one targeted update that
clears the finding. An external CI policy may choose to gate on the structured
diagnostic, but the native finding itself remains nonblocking.

## Adoption levels

| Level | Capability | Required commitment | Appropriate user |
|---|---|---|---|
| 0 — Surface only | Markdown, surface navigation, legacy graph/query workflows | Existing wiki | Users who need documentation but not native qualification |
| 1 — Generated observations | Committed knowledge projection and strict validation | Bootstrap/sync with knowledge-capable artifacts | Most active repositories |
| 2 — Qualified consumption | Live context, API, MCP, opt-in drift diagnostics, typed traversal | Supported extractor environment and consumer integration | Agent-heavy teams |
| 3 — Durable governance | UIDs, aliases, lifecycle, scoped review, verification receipts | Version-controlled governance ledger and maintainers | High-churn, long-lived repositories |
| 4 — Derived distribution | Redacted Site/Obsidian summaries | Explicit projection profile and validation | Portals, public docs, PKM users |

Users should be allowed to stop at any level. Governance and enriched
projections should not be made mandatory for the core diagnostic/context value.

## Anti-use-cases and non-goals

The project should not position the native layer as:

- a general-purpose enterprise knowledge graph;
- a graph database or graph-query language;
- a vector database or RAG replacement;
- a source-code search replacement;
- a runtime dependency, topology, or observability source;
- a scalar trust or confidence score;
- proof that prose is correct;
- a policy enforcement or authorization system;
- a cryptographic attestation or compliance platform;
- a vulnerability scanner or exploitability engine;
- automatic semantic documentation authoring;
- an OKF implementation without a named OKF consumer.

It is likely over-engineering for:

- small or short-lived repositories;
- prose-only documentation with no source-derived structural claims;
- projects that do not use agents, documentation CI, or a maintained wiki;
- users who need fuzzy semantic search but not evidence qualification;
- repositories whose extractor coverage is too incomplete for the questions
  being asked.

## Risks to product value

### Qualification metadata is ignored

If skills and integrations consume only paths and prose, the native layer
becomes expensive JSON with little user-visible behavior. Every flagship
workflow needs to demonstrate a decision altered by availability, freshness,
evidence, resolution, or bounds.

### “Current” is marketed as “true”

This would erase the most important contract distinction. Product copy,
examples, and skills must consistently say “unchanged since observation.”

### Governance arrives before demand

UIDs, lifecycle events, and reviews have real maintenance cost. They should be
introduced only to repositories with long-lived references or a concrete review
consumer.

### Analyzer coverage is mistaken for graph completeness

Every graph-facing workflow must expose analyzer coverage separately from query
truncation and evidence-sample truncation.

### Context cost is hidden

Token budgets bound output, not full source scanning. Agent integrations should
reuse a built service and avoid broad context for narrow tasks.

### Native qualification is skipped by an integration

Bundled skills now preserve native availability, stable reasons, live versus
snapshot-only freshness, and qualifier boundaries where those signals are
relevant. Impact analysis also consumes exact native identity and bounded typed
relationships, while publication workflows apply explicit projection profiles.
Some source-first workflows do not need native metadata. The remaining risk is
an external integration dropping qualifiers or treating a snapshot-only result
as a live source comparison.

## Candidate evaluation scenarios

The following scenarios are hypothetical designs for future evaluation. They
do not claim that a cohort was recruited, a study was run, or a result was
observed.

### Scenario A — Drift diagnostics in CI

- **Possible cohort:** three to five actively changing repositories.
- **Proposed duration:** four weeks.
- **Mode:** collect native warning diagnostics; any blocking experiment policy
  is external to LLM Wiki.
- **Measure:** actionable precision, unique native findings, unknown and
  incompatible rates, triage time, runtime.
- **Decision:** consider an external enforcement policy only after the
  NK-UC-001 thresholds are met.

### Scenario B — Agent context A/B

- **Cohort:** 15–20 historical issues across at least three repositories.
- **Control:** current source/wiki navigation and legacy graph queries.
- **Treatment:** identical agent/model plus qualified native context.
- **Measure:** correctness, maintainer acceptance time, tokens, tool calls,
  stale-context errors.
- **Decision:** continue only with measured quality or efficiency improvement.

### Scenario C — Impact graph benchmark

- **Corpus:** 25–30 maintainer-authored blast-radius questions.
- **Measure:** expected-node accuracy, document checklist accuracy, ambiguity
  handling, time, coverage disclosure.
- **Decision:** use results to choose which typed relationship families deserve
  further analyzer investment.

### Scenario D — Governance evaluation

- **Cohort:** one high-churn subsystem for four to six weeks.
- **Measure:** UID survival, review invalidation, authoring time, merge
  conflicts, downstream UID use.
- **Decision:** freeze expansion if event volume is low or no consumer uses the
  state.

### Scenario E — External onboarding

- **Cohort:** five maintainers unfamiliar with the selected repositories.
- **Measure:** setup time, orientation-task completion, retained use, confusion
  between static and runtime evidence.
- **Decision:** refine the quickstart and skill workflow before adding features.

## Practical validation priorities

A practical evaluation should demonstrate:

1. opt-in CI diagnostics that surface a real stale concept without changing the
   command's exit status;
2. an agent query that explains availability, freshness, evidence, and bounds;
3. impact analysis that combines legacy source queries with the typed graph;
4. an opt-in public projection that demonstrably preserves privacy and parity.

If future evaluations do not improve maintainer or agent outcomes, the
appropriate response is to simplify or narrow the layer rather than add more
graph types.
