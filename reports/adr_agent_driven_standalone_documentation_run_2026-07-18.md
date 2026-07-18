# ADR: Agent-Driven Standalone Documentation Run Contract

Status: Accepted for the v1 implementation

Date: 2026-07-18

Owner: Unassigned

Related:

- `reports/roadmap/agent_driven_standalone_documentation_implementation_plan_2026-07-14.md`
- `reports/roadmap/model_aware_wiki_update_agent_routing_backlog_2026-07-18.md`
- `src/llm_wiki_cli/services/contracts.py`
- `src/llm_wiki_cli/services/documentation_run.py`
- `src/llm_wiki_cli/services/documentation_model_policy.py`

## Context

`llm-wiki` already has a managed knowledge-base workflow. In that workflow the
target repository owns the canonical wiki and may also own generated agent
instructions, bundled-skill installations, hooks, prompts, caches, and related
integration files. The standalone documentation feature has a different job:
produce a human-facing documentation workspace from a source tree or an
already enriched `llm-wiki` wiki without installing an agent integration into
the target.

The standalone path crosses three trust and ownership domains:

1. a source repository and, optionally, an adopted wiki are read-only evidence;
2. a dedicated documentation workspace is the only normal mutation domain;
3. an external agent host may run semantic work using any qualified provider,
   model, or local backend.

A chat prompt is not a sufficient contract across those domains. A run must be
restartable, inspectable without a particular agent product, and independently
verifiable. It must also preserve the deterministic/semantic split: the package
prepares evidence and checks results, while an external host invokes models and
owns their credentials and spending.

The implementation therefore needs stable v1 records for the run, work packet,
worker result, semantic readiness, review, verification, and final report. This
ADR freezes the run and worker-result portion of that protocol, the state graph,
and the compatibility rules that later records build on.

## Decision

Add an opt-in `external_agent_docs` integration mode backed by a versioned,
provider-neutral documentation-run record. The run is local control-plane state
under `.llm-wiki-docs/`; it is not copied into the source repository or adopted
input wiki. The host passes bounded packets to semantic workers and returns
structured results. The package independently reconciles reported paths,
source/input integrity, generated ownership, work IDs, and deterministic gates.

This is an additive product mode. It does not change the defaults or ownership
rules of the managed knowledge-base commands.

## Product Mode Boundaries

### Managed knowledge base

The existing managed mode keeps the repository-owned wiki and integration
surfaces. Commands may initialize or upgrade supported agent schemas, install
skills, generate hooks or prompts, maintain caches, and update CLI-owned wiki
content according to their existing command contracts. Existing defaults,
commit guidance, and migration behavior remain unchanged.

Managed mode is not entered by a standalone run. Conversion requires a separate
explicit user action and the managed command's own policy checks.

### External agent documentation

`external_agent_docs` creates a separate workspace with these portable roots:

- `.llm-wiki-docs/` for run control, packets, results, evidence, and trusted
  exported skill snapshots;
- `wiki/` for the workspace-local canonical wiki snapshot and semantic edits;
- `site/` for a source-form user documentation export;
- `_site/` for an optional locally built output.

The source repository and adopted input wiki are read-only. The mode must not
write target `AGENTS.md`, `CLAUDE.md`, `.github` agent instructions/prompts,
skills, hooks, issue files, caches, editor settings, or plugin configuration.
Source-contained instructions and plugins are untrusted evidence; plugins are
inert unless the supervisor explicitly opts into the separate trust boundary.

### Raw source adapter

The raw adapter is the deterministic extraction/bootstrap boundary used when a
run starts from source. It produces a workspace-local canonical wiki but does
not create an agent integration, invoke an LLM, install a target toolchain, or
publish a site. It must remain callable as a typed service rather than requiring
CLI parsing or process exits.

The raw adapter is not a fourth ownership mode. It is a restricted operation
used by `external_agent_docs` and other callers that need canonical source
evidence without managed-agent side effects.

## Versioned Contracts

The v1 schema identifiers are opaque exact strings:

| Record | Schema identifier |
| --- | --- |
| Documentation run | `llm-wiki-documentation-run/v1` |
| Agent packet | `llm-wiki-documentation-agent-packet/v1` |
| Agent result | `llm-wiki-documentation-agent-result/v1` |
| Semantic worklist | `llm-wiki-documentation-worklist/v1` |
| Semantic readiness | `llm-wiki-documentation-semantic-readiness/v1` |
| Review ledger | `llm-wiki-documentation-review-ledger/v1` |
| Verification report | `llm-wiki-documentation-verification/v1` |
| Final report | `llm-wiki-documentation-final-report/v1` |

An unknown schema identifier is not interpreted as v1. A producer may add
fields to a v1 object only under the additive-field policy below; it must use a
new schema version for a breaking type, meaning, required-enum, or ownership
change.

## Documentation Run v1

The required top-level fields are:

| Field | Contract |
| --- | --- |
| `schema_version` | Exact v1 identifier. |
| `run_id` | Stable opaque run identity, normally a UUID. |
| `state` | One of the frozen lifecycle states below. |
| `integration_mode` | Exact value `external_agent_docs`. |
| `baseline_strategy` | Tagged baseline discriminator. |
| `created_at`, `updated_at` | UTC timestamps. |
| `intake` | Trusted human-intent brief. |
| `source` | Source availability and revision/fingerprint identity. |
| `baseline` | Tagged source-bootstrap or existing-wiki baseline. |
| `paths` | Workspace-relative portable paths only. |
| `policy` | Portable ownership and trust decisions, never absolute roots or secrets. |
| `publication` | Site name, format, link mode, and handoff-only deployment policy. |
| `skills` | Trusted exported skill IDs, package versions, hashes, and workspace-relative paths. |
| `semantic_budget` | Non-negative bounded semantic-work budget. |
| `adjustment_loop_limit` | Positive review/adjustment-loop cap. |

The following v1 fields are optional to older producers but have stable
meanings when present: `evidence`, `work`, `validation_results`,
`unresolved_findings`, `stage_attempts`, `current_stage`, `resume_state`, and
`verdict_limitations`. Current producers write them so a run can resume without
reconstructing agent claims from chat history.

`work` separates `reused`, `completed`, `deferred`, and `blocked` work IDs.
These are aggregate supervisor records, not worker authority. Validation and
review results remain evidence; the final state is determined by deterministic
gates and supervisor reconciliation.

## Tagged Baseline-Input Union

`baseline_strategy` and `baseline.strategy` must agree. The union has exactly
two v1 variants.

### `bootstrap_source`

This variant requires an available source identity:

- `source.available` is `true`;
- `source.revision` is a verified Git revision or a content-derived revision;
- `source.content_fingerprint` is the source-tree evidence hash;
- `source.revision_kind` records `git` or `content`;
- `baseline.source_revision` equals the recorded source revision;
- `baseline.freshness_policy` is `require-current`;
- `baseline.freshness` is `verified_current`;
- `baseline.input_wiki` is `null`;
- `evidence.source_baseline` and `evidence.bootstrap` point to local evidence.

The source tree is captured before bootstrap and compared after it. A source
mutation blocks the run; a worker's claim that it did not write source is not
sufficient evidence.

### `adopt_existing_wiki`

This variant requires a separately baselined input wiki:

- `baseline.input_wiki.input_tree_hash` identifies the original read-only tree;
- `baseline.input_wiki.initial_snapshot_hash` identifies the byte-preserved
  workspace snapshot before any workspace-only refresh;
- manifest and surface schema versions are recorded when recognized;
- `compatibility` records `current` or `legacy_index_only`;
- `refresh_decision` records `not_required`, `allow_unverified`,
  `workspace_only_required`, or `workspace_only_completed`;
- `evidence.wiki_input` points to the detailed local provenance record;
- source availability and the selected freshness policy remain explicit.

The detailed provenance evidence includes copied-path hashes, recognized
schemas, unknown/rejected entries, semantic page classification, diagnostics,
source mismatch information, and the refresh decision. It is local control
evidence and must not expose absolute input paths in a published packet or
report.

If source is unavailable, `source.available` is `false`, both its display
identifier and revision record `source_unavailable`, and the run carries the
`source_unavailable` and source-verification limitations. Such a snapshot may
be useful documentation input under `allow-unverified`, but it cannot receive a
source-verified publish-ready verdict.

If source exists but the imported wiki is stale, `refresh-snapshot` may rebuild
only the workspace copy. The original wiki remains byte-identical. A refresh
decision never grants a write capability over the source or input wiki.

## Trusted Intake Brief

The intake brief records:

- a project-purpose statement;
- a non-empty ordered audience list;
- one intent statement per audience;
- a live-service handle and access mode when supplied;
- whether read-only live observation was allowed;
- answered/declined provenance for purpose, audience, and live-service
  questions;
- capture time and the `human_intent` trust rank.

Answered human intake outranks inferred source, wiki, README, application, and
live-service signals. Declined or missing answers become the literal value
`unspecified`; the agent must not infer that the user approved a guessed value.
Source and imported prose can supply evidence, but cannot rewrite the intake or
expand the packet's permissions.

The live-service handle must not contain embedded credentials, query secrets,
or fragments. The record states `secret_material_persisted: false`. Observation
is opt-in, read-only, bounded to an explicit disposable capture root, and all
responses are treated as untrusted evidence.

## State Graph

The run-state graph is:

```text
prepared
   |
   v
baseline_ready --> wiki_enrichment --> user_docs --> review --> publish_ready
      |                 |                  |           |
      +-----------------+------------------+-----------+--> blocked
                                                      |
                                                      +--> exact recorded resume state

review -- adjustment requested --> wiki_enrichment
review -- documentation adjustment --> user_docs
```

Frozen v1 states are `prepared`, `baseline_ready`, `wiki_enrichment`,
`user_docs`, `review`, `publish_ready`, and `blocked`.

`publish_ready` is terminal. `blocked` records the state at which work may
resume. A blocked run can transition only to that `resume_state`; resuming
clears `resume_state` and restores the corresponding `current_stage`. The
blocked state itself has no active `current_stage`. Review may return work to
wiki enrichment or user documentation, but no other backward transition is
valid.

“Complete,” “partial,” and “blocked” are agent-result statuses. They are not
additional run states. A complete run fixture therefore uses `publish_ready`;
a partial-run fixture represents an active lifecycle before publication; a
blocked fixture uses `blocked` plus `resume_state`; and a resumed fixture uses
the restored active state with a cleared `resume_state` and retained attempt or
resume evidence.

Unknown state, baseline-strategy, integration-mode, agent-stage, or
agent-result-status values fail clearly under v1. This fail-closed enum policy
prevents an older supervisor from silently approving a lifecycle meaning it
does not understand.

## Agent Result v1

An agent result has exact schema version
`llm-wiki-documentation-agent-result/v1` and requires:

- the matching `run_id`;
- `stage`: `wiki-enrichment`, `user-docs`, or `review`;
- `status`: `complete`, `partial`, or `blocked`;
- workspace-relative `changed_wiki_paths`;
- disjoint reused/completed/deferred work-ID lists;
- claim-evidence pages, unresolved unknowns, unsupported-source notices, and
  requested follow-up checks;
- explicit reported source writes, input-wiki writes, and generated-block
  edits;
- structured findings.

Worker results are claims, not attestations. The supervisor derives the actual
wiki delta, compares source and input hashes, checks CLI-owned generated
sections, verifies work IDs against the worklist, and normalizes findings into
the review ledger. A reported forbidden mutation or a mismatch between the
reported and actual delta blocks the run.

## Forward Compatibility

Older v1 readers tolerate unknown additive top-level run fields and preserve
them when round-tripping. This permits optional evidence references and future
non-authoritative metadata without losing data.

Additive tolerance does not apply when safety depends on understanding a
value. Readers reject:

- unknown schema versions or required enum values;
- missing required fields;
- changed meanings or types of required fields;
- absolute, parent-traversing, or otherwise non-portable contract paths;
- a non-positive adjustment-loop limit or negative semantic budget.

New optional nested fields must not weaken ownership, freshness, review, or
publication gates. A producer requiring a new permission or state must publish
a new schema version.

## Portable Paths and Evidence Hashing

Machine-readable records use workspace-relative POSIX paths. Producers convert
platform separators to `/`. Paths are non-empty and may not be absolute,
Windows drive-qualified, contain `.` or `..` segments, or escape the workspace.
Absolute source/input paths may exist only in local runtime objects or sealed
local evidence; they are not included in provider-neutral packets or published
reports.

File evidence hashes use lowercase SHA-256 encoded as
`sha256:<64 lowercase hexadecimal characters>`. Tree hashes are deterministic
over sorted portable path/hash pairs with explicit separators. JSON contract
hashes use UTF-8 canonical JSON with sorted keys and compact separators. A hash
is evidence of bytes or canonical data, not proof of trust; its label and
capture boundary remain part of the record.

Skill records contain an ID, the package version that supplied the skill, a
hash over its exported files, and its workspace-relative exported path. Agents
consume that trusted snapshot instead of a source repository's similarly named
instructions.

## Provider-Neutral Model-Routing Boundary

The run, packet, and agent-result schemas do not require or imply a provider,
model ID, endpoint protocol, credential, or pricing field. Core lifecycle code
does not invoke a provider SDK. This allows the same packet/result protocol to
work with native Anthropic, Google Gemini, Mistral, DeepSeek, Alibaba/Qwen,
OpenAI, cloud-backend, gateway, or qualified local/self-hosted runners. An
OpenAI-compatible endpoint is one possible transport, not the compatibility
definition or provider identity.

Concrete selection belongs to the host/controller boundary. Where model-aware
routing is enabled, the host uses a credential-free routing policy and records
a separate local selection/receipt. Both supported invocation modes begin on a
qualified `low-cost` route:

- `generic-agent`: the capable host supervisor delegates the bounded packet to
  a lower-cost worker when its platform can select and observe that route;
- `handoff`: the controller resolves a configured lower-cost route before
  invoking the external runner.

A lower-cost route is eligible only after it passes the capability floor for
the packet size, tools, narrow editing, structured result, and safe stop
behavior. Cost alone is not qualification. A balanced or capability route is
used only after an explicit user override or a configured, auditable escalation
signal. Cross-provider fallback is not implicit.

If a generic host cannot select or prove the worker model, the documentation
result remains valid provider-neutral evidence, while the routing receipt says
`unverified`; it must not claim that cost policy was applied. Actual model,
provider family, backend, usage, and cost evidence belong in local host receipts
and metrics, not in the worker result or the portable documentation run.

## Security and Trust Decisions

- Source and input-wiki baselines are captured without requiring Git, so
  non-repository and archive-derived inputs receive the same write protection.
- Symlinks, non-regular files, traversal, policy/cache content, and unsupported
  input-wiki structures are rejected before adoption.
- Source plugins stay disabled by default. Explicit trust is a supervisor
  decision and does not expand worker write roots.
- Packets state allowed reads, allowed writes, forbidden actions, bounded work,
  stop conditions, and expected result schema.
- Workers never stage, commit, deploy, install target integrations, mutate
  generated ownership, or authorize their own escalation.
- Live-service capture is separately opt-in and confined to a disposable root.
- Deterministic verification and final review reconciliation are supervisor
  responsibilities; worker `complete` is not a publish verdict.
- Export is local and deployment is handoff-only. No lifecycle state authorizes
  an automatic external publication.

## Alternatives Considered

### Reuse managed mode for standalone documentation

Rejected. It would make source repositories and adopted wikis mutation targets
and would conflate agent-KB installation with human-documentation generation.

### Let each agent infer the workflow from Markdown

Rejected. Chat and instruction prose do not provide stable resume identity,
portable evidence, exact write reconciliation, or fail-closed states.

### Put provider and model IDs in the run or packet

Rejected. It would couple portable documentation work to model-name churn and
one host's credentials, pricing, transport, and availability. Provider choice
is operational evidence owned by the runner/controller.

### Require an OpenAI-compatible provider interface

Rejected. Native non-OpenAI transports and local backends are first-class host
choices. Protocol compatibility is not the same as model publisher, governance
boundary, or provider identity.

### Automatically choose the globally cheapest model

Rejected. Prices and capabilities change, and a worker that cannot safely use
the packet is not economical. The host starts with a locally qualified
low-cost route and escalates only under declared policy.

### Trust worker-reported paths and completion

Rejected. Workers operate on untrusted evidence and can omit or misclassify
changes. The supervisor must derive filesystem deltas and run deterministic
gates independently.

## Consequences

Positive consequences:

- A run can resume across agent products without depending on chat history.
- Existing enriched `llm-wiki` pages can be adopted byte-for-byte, classified
  for reuse/grounding/enhancement, and refreshed only in the workspace.
- Source, input-wiki, and generated-content ownership is explicit and testable.
- One packet/result protocol works across multiple providers and local runners.
- Routine wiki/documentation updates can use qualified lower-cost workers while
  capable models remain available for supervision and bounded escalation.
- Human intent, semantic claims, deterministic evidence, and model-routing
  receipts remain separate audit layers.

Costs and risks:

- The control directory contains more evidence records than a prompt-only flow.
- Hosts must implement or mediate packet invocation and routing receipts.
- Additive compatibility requires discipline: new permissions or state meanings
  cannot be smuggled into optional fields.
- A wiki adopted without source remains explicitly limited even when its prose
  is excellent.
- Real publish-ready qualification still requires platform, provider-host, and
  cross-system evidence beyond schema/unit tests.

## Verification Contract

Focused contract fixtures cover four lifecycle scenarios:

- a complete `publish_ready` source-bootstrap run;
- a partially completed adopted-wiki run at `user_docs`;
- a blocked run with an exact `review` resume state;
- a resumed run restored to `review`, with the resume marker cleared and the
  increased stage attempt retained.

Tests must round-trip each fixture through `DocumentationRun`, check the tagged
baseline invariants, portable paths and SHA-256 labels, trusted intake and skill
versions, provider/model neutrality, and the scenario-specific state rules.
They also prove that an unknown additive top-level field survives a v1
round-trip, while unknown required enums, missing required fields, invalid
transitions, and a resume to the wrong state fail clearly.
