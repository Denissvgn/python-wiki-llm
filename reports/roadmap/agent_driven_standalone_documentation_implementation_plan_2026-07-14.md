# Agent-Driven Standalone Documentation Implementation Plan

- Date: 2026-07-14
- Updated: 2026-07-18
- Status: local deterministic lifecycle implementation complete; real-agent,
  cross-platform, and publication qualification remain (**NO_SHIP**)
- Implementation closeout:
  [Agent-Driven Standalone Documentation Implementation Closeout](../standalone_documentation_implementation_closeout_2026-07-18.md)
- Parent roadmap:
  [Multi-Language Expansion & Product Evolution](roadmap_multi_language_and_evolution_2026-07-10.md)
- Related routing backlog:
  [Model-Aware Wiki Update Agent Routing](model_aware_wiki_update_agent_routing_backlog_2026-07-18.md)
- Scope: generate and maintain agent-enhanced architecture and user documentation
  for an external project from either its source or an existing LLM Wiki, without
  installing repository-local agent instructions into that project
- Compatibility decision: additive; the existing managed agent knowledge-base
  workflow remains supported and unchanged by default

---

## 1. Revised product decision

The standalone documentation path must be **agent-driven**, not
deterministic-only.

The deterministic layer is an evidence compiler and structural scaffold. It is
good at repeatable source inventory, stable page ownership, links, diagrams,
manifests, and validation. It is intentionally weak at product meaning, reading
order, architecture rationale, workflow explanation, audience selection, and
task-oriented prose. Publishing its raw output as finished user documentation
would repeat the failure already observed in real-project docsite dogfood: a
structurally valid reference inventory can still be a poor documentation
experience.

The target workflow is therefore:

1. establish the canonical wiki baseline in a separate documentation workspace,
   either by building it deterministically from source or by adopting a validated
   snapshot of an existing LLM Wiki whose agent-authored enrichments are
   preserved;
2. give a documentation agent a bounded, versioned work packet and trusted
   bundled skills;
3. run a dedicated `wiki-semantic-enhance` stage so the agent can refactor and
   enhance **agent-owned semantic surfaces** while protecting generated
   structure;
4. use the enhanced wiki as evidence for skill-driven user documentation;
5. run deterministic review, export, and site gates around the agent's work;
6. preserve unresolved or low-confidence work explicitly instead of fabricating
   completeness.

Here, **standalone** means independent of the target repository's agent-policy
files and lifecycle. It does not mean agent-free.

## 2. User job and boundaries

### 2.1 Job to be done

> When I need trustworthy architecture and user documentation for an existing
> project, I want to run LLM Wiki from a separate documentation workspace, using
> either the source project or wiki pages already generated and enriched through
> LLM Wiki, so a documentation agent can preserve prior semantic work, improve
> the canonical wiki, and publish useful guides without changing the source
> project or enrolling it in an agent knowledge-base workflow.

### 2.2 Product modes

| Mode | Source repository | Agent instructions | Agent role | Primary output |
|---|---|---|---|---|
| Managed agent knowledge base | Local, normally writable | Existing `init --agent` schema, skills, and optional hooks | Maintains architecture memory during code work | Repo-local canonical wiki |
| Agent-driven documentation workspace | Read-only external source and/or existing LLM Wiki | No target `AGENTS.md`, `CLAUDE.md`, IDE rules, hooks, or skills | Builds or adopts a wiki snapshot, preserves valid enrichments, and authors user docs from an explicit run packet | External canonical wiki plus user-docs site |
| Raw source adapter | Read-only input | None | Caller consumes deterministic data; no semantic pass implied | JSON/context or raw generated reference wiki |

The modes share extraction, rendering, query, lint, and export services. They do
not share mutation policy.

### 2.3 Baseline input options

The standalone workspace supports two explicit baseline strategies:

- `bootstrap_source` (default): build a new deterministic wiki snapshot from the
  selected source revision;
- `adopt_existing_wiki`: validate and copy an existing canonical wiki produced by
  `llm-wiki bootstrap`, `sync`, or the managed skill workflows into the external
  workspace. Human/agent-owned semantic prose, including prior LLM enrichments,
  is preserved as candidate evidence rather than regenerated automatically.

The existing wiki is always a read-only input. The copied workspace snapshot
becomes the run's canonical wiki; migrations, refreshes, semantic edits, and site
exports apply only to that snapshot. When the source tree is available, the run
must compare the imported manifest/surface metadata with the selected source
revision. When it is unavailable, wiki-only authoring may proceed only with
explicit `unverified` freshness, and the run cannot claim source-verified
`publish_ready` status until source evidence is supplied and reconciled.

The CLI must never silently replace an invalid, stale, or unsupported wiki input
with a fresh bootstrap. It reports the incompatibility and requires an explicit
choice to repair/refresh the workspace copy, continue with limited unverified
provenance, or stop.

### 2.4 Non-goals

- Do not replace or deprecate `llm-wiki init --agent ...`.
- Do not rename or remove `bootstrap --source-adapter`.
- Do not publish a second PyPI distribution or an empty `standalone` extra.
- Do not add a provider-specific LLM client to the core package in the first
  implementation.
- Do not let an agent hand-edit CLI-owned tables, diagrams, manifests, surface
  indexes, or generated blocks.
- Do not edit, sync, upgrade, or otherwise mutate an adopted input wiki in place.
- Do not treat prior LLM-enriched prose as automatically correct merely because
  it already exists; preserve it first, then ground or defer its important claims.
- Do not claim that every entity/module page needs bespoke prose before user docs
  can ship.
- Do not execute the target application, target build system, untrusted plugins,
  or captured product workflows implicitly.
- Do not deploy or publish to a remote host without separate authorization.

## 3. Why the earlier documentation-only plan was insufficient

The earlier direction correctly separated package installation from agent-file
mutation, but it treated documentation generation as a mostly deterministic
library operation. That misses the product's strongest existing architecture:

- `wiki-bootstrap` already defines a centrality-ranked semantic pass after the
  deterministic bootstrap;
- `user-docs-author` explicitly defines deterministic evidence, agent-authored
  guide prose, and a checker-driven adjustment loop;
- `onboarding-guide`, `usage-examples`, `doc-review`, and `publish-docs` already
  split narrative, evidence capture, review, and distribution responsibilities;
- user-profile site checks already distinguish a generated reference mirror from
  publishable human documentation.

The missing capability is not another renderer. It is a portable orchestration
and trust contract that lets a documentation agent use those workflows outside
the target repository without injecting local instructions.

### 3.1 Alternatives considered

| Approach | Decision | Reason |
|---|---|---|
| Deterministic `docs build` only | Reject | Reproduces the structurally valid but semantically weak reference-site failure |
| Run `init --agent` in the target | Reject for standalone mode | Enrolls the target in agent policy and violates the requested isolation boundary |
| Core package calls one LLM provider | Defer | Couples credentials, billing, model policy, and transport to the deterministic package |
| Rely only on the current agent to remember a skill sequence | Reject as the durable contract | Hidden chat state is not resumable or independently auditable |
| Explicit workspace plus runner-neutral packet/result schemas | Select | Preserves isolation, skill reuse, replay, and provider neutrality |
| Blindly copy an existing wiki and trust all enriched prose | Reject | Loses source freshness, ownership, structural-integrity, and claim-grounding guarantees |
| Validated read-only wiki snapshot with explicit provenance | Select | Reuses prior LLM Wiki work without mutating its source or pretending stale/unsupported claims are current |
| Writable MCP transaction server for agent edits | Later experiment | Useful after semantic ownership and stale-write transactions are stable, but larger than the MVP |
| Optional runner plugins | Later extension | Appropriate only after multiple platforms prove the same neutral handoff |

## 4. Selected architecture

### 4.1 Topology

```text
read-only source project ----> deterministic bootstrap ---\
                                                        +--> canonical workspace wiki + worklist
read-only existing LLM Wiki --> validate + snapshot -----/          ^
        + first-stage human intake (purpose, audience, live service) |
        |
        v
wiki semantic agent pass
        |
        v
enhanced canonical wiki + explicit remainder
        |
        v
user-docs agent pass using bundled skills
        |
        v
independent review + deterministic site gates
        |
        v
publishable local artifact / deployment handoff
```

The initial implementation may use one documentation agent for the wiki and
user-docs phases, but it must keep the phase packets and results separate so an
independent reviewer or a future second worker can replay and validate them.
The source-bootstrap and existing-wiki branches converge only after the baseline
provenance and freshness gates pass. `wiki-bootstrap` remains the managed
first-adoption workflow; the new
`wiki-semantic-enhance` skill extracts its semantic-pass rules into a resumable
stage that can also serve external workspaces.

### 4.2 Roles

| Role | Owns | Must not do |
|---|---|---|
| Supervisor / host agent | First-stage intake interview, permissions, source/wiki provenance, workspace, stage transitions, heavy-gate scheduling, final verdict | Treat a worker's self-report as final proof; re-ask intake after the first stage |
| Deterministic CLI | Extraction, generated wiki structure, validated wiki snapshot adoption, worklist signals, lint/CI/site checks, state schemas | Write semantic prose, trust imported prose without evidence, or call an LLM |
| Wiki semantic agent | P0 semantic pages, centrality-ranked module/entity explanations, architecture rationale, explicit remainder | Edit generated blocks or source code |
| User-docs agent | Product overview, audience guides, reading paths, usage examples where executable, user-profile adjustments | Promote unsupported claims or edit derived site output |
| Reviewer | Claim/evidence sampling, generated-block integrity, unresolved finding classification, publish-readiness recommendation | Quietly fix or hide unresolved findings without recording them |

The main supervisor remains the final validator. Worker result packets are
evidence, not self-authorizing completion decisions.

### 4.3 Core implementation principle

Keep core package code deterministic and runner-neutral. The package prepares
and validates an agent run; an agent platform executes the semantic skills.

The first release should not implement `generate_documentation()` as a function
that appears to synchronously create finished prose. Prefer lifecycle APIs such
as:

```python
run = prepare_documentation_run(...)
packet = build_documentation_agent_packet(run, stage="wiki_enrichment")
record_documentation_agent_result(run, result)
report = verify_documentation_run(run)
```

For an existing-wiki baseline, preparation also uses a typed snapshot boundary
such as `adopt_documentation_wiki_snapshot(...)`; it must not route through a
shell copy or mutate the input directory.

An optional runner-plugin surface can be evaluated later, after at least two
agent platforms successfully consume the same packet/result contract.

## 5. Documentation workspace contract

### 5.1 Proposed layout

```text
<workspace>/
  .llm-wiki-docs/
    run.json
    policy.json
    stages/
      01-baseline.json
      02-wiki-enrichment.json
      03-user-docs.json
      04-review.json
    packets/
      wiki-enrichment.md
      user-docs.md
      review.md
    results/
      wiki-enrichment.json
      user-docs.json
      review.json
    evidence/
      bootstrap.json
      wiki-input.json
      lint.json
      ci-check.json
      site-check.json
    skills/
      agent-docs/
      wiki-semantic-enhance/
      user-docs-author/
      ...
  wiki/
    index.md
    guides/
    entities/
    modules/
    flows/
    infrastructure/
    bootstrap-remainder.md
  site/
  _site/
```

The exact hidden-directory name may change during implementation, but all run
control artifacts must remain inside the explicit documentation workspace.

### 5.2 Run schema

Add an additive `llm-wiki-documentation-run/v1` contract with at least:

- run id and state (`prepared`, `baseline_ready`, `wiki_enrichment`,
  `user_docs`, `review`, `publish_ready`, `blocked`);
- baseline strategy (`bootstrap_source` or `adopt_existing_wiki`);
- source revision/hash and source-root display identifier when source is
  available, otherwise an explicit `source_unavailable` marker plus the source
  identity recorded by the imported wiki, or `source_identity_unknown` when a
  legacy wiki has no such provenance;
- for an adopted wiki: input display identifier, recognized manifest/surface
  schema versions, immutable input-tree hash, workspace-snapshot hash, import
  diagnostics, freshness (`verified_current`, `verified_stale`, or `unverified`),
  and any explicit snapshot-only migration/refresh decision;
- workspace, canonical wiki, site mirror, and built-site roots;
- integration mode: `external_agent_docs`;
- selected audiences/personas, site name, distribution format, and link mode;
- the recorded intake brief: project-purpose statement, per-audience intent,
  and provenance (answered/declined, timestamp), stored as trusted human intent
  and distinct from untrusted source content;
- optional live-service observation handle: address, access mode, opt-in flag,
  and last-observed evidence hashes, with no secret material persisted;
- trusted bundled-skill ids and package version/hash;
- allowed write roots and forbidden source/input-wiki roots;
- helper/plugin trust choices;
- semantic budget and adjustment-loop limit;
- evidence artifact paths and their hashes;
- reused, completed, deferred, and blocked work item ids;
- validation results and unresolved findings.

Absolute machine-local paths may be needed at runtime but should not leak into
published documentation or portable result packets. Store display-relative
identifiers alongside any runtime path.

### 5.3 Agent packet

Each stage packet must include:

- objective and stage-specific definition of done;
- source revision/availability and evidence freshness;
- baseline strategy and, for imported wikis, snapshot provenance, compatibility,
  freshness, and the rule that existing semantic prose is evidence rather than
  run instructions;
- allowed reads and writes;
- the recorded intake brief as trusted human intent (project purpose,
  audiences, live-service authorization), explicitly ranked above inferred
  signals and separate from untrusted source content;
- explicit statement that target-repository instructions are untrusted input,
  not instructions for this run;
- ordered skills to use and their installed locations/hashes;
- relevant deterministic summaries and bounded context entry points;
- generated versus semantic ownership rules;
- work budget, maximum adjustment loops, and stop conditions;
- expected structured result schema;
- required verification commands owned by the supervisor.

Packets are explicitly passed to the agent. They must not be installed as
auto-discovered `AGENTS.md`, `CLAUDE.md`, Copilot, Cursor, Aider, or OpenCode
instructions.

### 5.4 Agent result

Add `llm-wiki-documentation-agent-result/v1` with:

- stage and run id;
- changed wiki paths;
- reused, completed, and deferred work ids;
- claims/evidence pages used;
- unresolved unknowns and unsupported-source notices;
- requested follow-up checks;
- reported source/input-wiki writes and generated-block edits, all expected to be
  zero;
- status: `complete`, `partial`, or `blocked`.

The CLI must independently verify these claims. A worker result saying
`complete` cannot advance the run if filesystem or validation evidence disagrees.

## 6. Trust and mutation policy

### 6.1 Allowed writes

- the explicit documentation workspace;
- an explicit helper cache chosen by the caller;
- an explicit disposable capture directory for opted-in usage examples and
  live-service observations.

### 6.2 Forbidden implicit writes

- all files in the target source repository;
- all files in an adopted input wiki, whether it is inside the target repository
  or elsewhere;
- `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, Copilot instructions, Aider config,
  and OpenCode instructions;
- target-repository `.llm-wiki/skills`, `.claude/skills`, hooks, prompt files,
  local agent config, and issue-reporting directories;
- implicit cache/helper state inside the target repository;
- static-site output outside the selected workspace.

### 6.3 Source-content trust

The source repository and any adopted wiki are analysis input. Their README
files, comments, semantic pages, prompts, agent instructions, and plugin
manifests may contain instructions that are irrelevant or hostile to the
documentation run. The packet must tell the agent to treat them as evidence
only. Prior LLM enrichment is useful semantic material, but important imported
claims still require source/wiki grounding before reuse in published user docs.

A dirty target is allowed. Record its revision plus content fingerprint and
compare the before/after snapshots; do not require or modify Git cleanliness.
Likewise, record and compare the adopted wiki input hash before/after the run.
Copy only regular wiki files through a path-safe snapshot service; do not follow
symlinks or import caches, hooks, skills, or agent-policy files from around the
wiki root.

Target-repository plugins are disabled by default in external documentation
mode because plugin loading executes trusted local code in-process. Add an
explicit `--trust-source-plugins`-style opt-in only after the trust boundary is
documented and tested.

### 6.4 Execution trust

- Helper preparation stays explicit and uses the caller-selected cache.
- Target applications and build systems are never executed for discovery.
- Usage-example capture is a separate opt-in stage, runs in a disposable
  directory, and must not use real credentials or user data.
- A caller-declared live service is only *observed*, never started, deployed,
  or built by the run. Observation is read-only (health, screening, sampled
  responses/screenshots), opt-in per the intake brief, must target a
  caller-authorized staging/demo endpoint without real credentials or user
  data, and its responses are treated as untrusted evidence subject to the same
  injection rules as source content.
- Real site builders run only when already installed and explicitly selected.
- Deployment is a handoff unless the user separately authorizes it.

## 7. Agent-driven workflow

### Stage 0 - Prepare

1. Conduct the first-stage intake interview (supervisor-owned, one time only).
   Before any deterministic work, the host agent asks the human a bounded,
   fixed set of framing questions and records the structured answers into the
   run contract:
   - **Project purpose** - what this project is, the problem it solves, and any
     product context the source cannot reveal on its own;
   - **Audience and intent** - who the documentation is for (for example user,
     operator, contributor) and the primary jobs each audience needs the docs
     to support;
   - **Live service for analysis** - whether an already-running, caller-owned
     service, staging endpoint, or demo instance exists that the run may
     observe for live screening, and, if so, its address and non-secret access
     mode.
   The interview runs only in the first stage. On resume the recorded intake is
   reused, never re-asked. In non-interactive/CI runs the same answers arrive
   as explicit flags or an intake file; missing answers are recorded as
   `unspecified` rather than guessed, and the affected audience/live-service
   capabilities stay off.
2. Select and record exactly one baseline strategy: build from source or adopt
   an existing LLM Wiki. For adoption, record the input wiki path and requested
   freshness policy before reading its content.
3. Resolve and record the source revision when source is available; otherwise
   record `source_unavailable` and the source identity/revision declared by the
   imported manifest when present, or an explicit `source_identity_unknown` for
   a legacy wiki that cannot supply it.
4. Create the external documentation workspace.
5. Write the run/policy contract, recorded intake brief, source/input-wiki
   filesystem baselines, and allowed/forbidden roots.
6. Export only the selected, versioned bundled skills into the documentation
   workspace; never copy them into the target or adopted wiki.
7. Detect languages and report missing helpers when source is available; do not
   prepare implicitly.

The interview is an agent activity, not a deterministic CLI step: the
supervisor asks the questions and hands the structured answers to
`docs prepare`, which only validates and persists them. The deterministic
package still runs no model. Treat intake answers as authoritative human intent
that outranks inferred audience/purpose signals, while source-repo instructions
remain untrusted evidence.

Gate:

- the intake brief is recorded (with explicit `unspecified` markers where the
  human declined) and stored as trusted human intent, distinct from untrusted
  source content;
- any declared live service is recorded with its access mode and opt-in flag,
  and no secret is persisted into the workspace or published docs;
- workspace is writable;
- when selected, the source root is readable and recorded as forbidden for
  writes;
- when selected, the input wiki is recognized, readable, hashed, and recorded as
  forbidden for writes; symlinked/non-regular content is rejected;
- no target agent-integration artifact is created or modified;
- run state and policies validate against their schemas.

### Stage 1 - Deterministic baseline

1. Materialize exactly one baseline into `<workspace>/wiki`:
   - **Build from source:** run the existing deep bootstrap substrate in
     source-adapter/external-source mode.
   - **Adopt an existing wiki:** inspect the read-only input for `index.md`,
     `.llm-wiki-manifest.json`, `.llm-wiki-surface.json`, generated ownership
     markers, local-link safety, and supported schema versions; then create a
     path-safe workspace snapshot that preserves eligible files byte-for-byte.
     Legacy LLM Wikis with `index.md` but no manifest may be migrated only after
     the snapshot exists, and only inside the workspace.
2. For an adopted wiki, compare its manifest/source identity with the selected
   source when available. The default `require-current` policy stops on stale or
   unverifiable input. Explicit alternatives are `refresh-snapshot` (run
   deterministic sync/upgrade only against the workspace copy) and
   `allow-unverified` (continue with a visible limitation that prevents a
   source-verified `publish_ready` verdict). Never bootstrap over the imported
   snapshot and never refresh the input directory.
3. Collect the bootstrap/import summary, surface index, placeholder inventory,
   dependency centrality, flows, contract diagnostics, unsupported-source
   notices, and imported semantic-page inventory.
4. Generate a deterministic semantic worklist:
   - P0: landing context, important flow behavior, API/dependency/load-order
     notes, and high-signal runtime surfaces;
   - P1: central modules/entities with weak prose;
   - P2: long tail and unsupported/uncertain items;
   - imported semantic pages: `candidate_reuse`, `needs_grounding`,
     `needs_enhancement`, or `incompatible`, without treating pre-existence as
     proof of correctness.
5. Run strict structural validation before agent authoring.

Gate:

- no unexplained skipped generated files;
- structural lint is clean;
- every unsupported source or unknown is represented in evidence;
- when source is available, its filesystem hash is unchanged;
- for an adopted baseline, the input wiki hash is unchanged and snapshot
  provenance is complete;
- for an adopted baseline, before any explicit workspace-only migration/refresh,
  all eligible input wiki files match their snapshot hashes;
- for an adopted baseline, every imported semantic page is preserved and
  classified; no bootstrap output silently replaces prior LLM enrichment;
- for an adopted baseline, freshness is `verified_current`, or the run records
  the explicit limitation that prevents a source-verified `publish_ready`
  verdict.

### Stage 2 - Wiki semantic enrichment and refactoring

The wiki agent uses a new `wiki-semantic-enhance` skill derived from the existing
centrality-ranked `wiki-bootstrap` semantic rules and adapted for an external
source and separate workspace:

1. complete, validate for reuse, or explicitly defer every P0 item;
2. enhance the centrality-ranked P1 budget;
3. preserve existing enriched prose when its important claims remain grounded;
   record it as `reused` rather than rewriting it merely for style;
4. replace placeholder/copied-docstring-only or ungrounded semantic prose where
   evidence is sufficient;
5. write architecture rationale and flow behavior;
6. create or refine agent-owned overview/guide pages that provide a coherent
   information architecture over the raw generated reference;
7. record generator defects separately instead of patching generated blocks;
8. maintain a stable remainder backlog for the long tail.

"Refactor the wiki" means improve semantic organization, narrative pages, and
human-owned sections. It does not mean rewriting CLI-owned structure that the
next sync will overwrite.

Gate:

- all P0 items are complete or have explicit evidence-backed deferrals with the
  affected topic excluded from primary user docs;
- configured P1 budget is complete;
- no generated-block, source-file, or input-wiki writes occurred;
- for an adopted baseline, every imported semantic page is accounted for as
  preserved/reused, explicitly changed by the agent, or deferred with rationale;
- strict lint and `ci-check` pass;
- a reviewer can trace every completed work item to source/wiki evidence.

### Stage 3 - User documentation authoring

The documentation agent uses the existing skills as an ordered pipeline:

1. `user-docs-author` for the complete human-facing narrative layer;
2. `onboarding-guide` for persona-specific reading and first-task paths where
   needed;
3. `usage-examples` only when the relevant flow can be executed safely, or when
   the intake-declared live service can be observed read-only for screening
   evidence;
4. `publish-docs` only after user-profile checks are clean.

The user-docs layer must include, when supported by evidence:

- a concise product/project overview;
- audience and prerequisites;
- primary user/operator/contributor workflows;
- architecture and operational mental models;
- task-oriented guides with links to canonical evidence;
- a secondary generated-reference entry point;
- deferred-docs entries for gaps the agent cannot prove.

Gate:

- user profile has a real site name and at least one guide;
- primary published pages contain no bootstrap placeholders;
- every factual workflow/architecture section links to canonical wiki evidence;
- no raw generated inventory is promoted as the user landing page;
- site export/check passes for the selected distribution mode.

### Stage 4 - Review and adjustment

1. Normalize deterministic checker output and `doc-review` findings into one
   finding ledger.
2. Independently sample important user-facing claims, including claims reused
   from an imported LLM-enriched wiki, against available wiki/source evidence.
3. Verify generated-block, source-tree, and adopted input-wiki integrity.
4. Return valid defects to the appropriate agent stage.
5. Cap automated adjustment loops (default: three) and mark the run blocked or
   partial if the same high-severity issue persists.

Gate:

- zero unresolved high-severity correctness or safety findings;
- medium/low findings are fixed or explicitly deferred;
- when present, target source and adopted input wiki remain byte-identical;
- worker result packets reconcile with actual diffs and validation output.

### Stage 5 - Local publication handoff

1. Export the user profile.
2. Run the selected builder only when installed and authorized.
3. Validate built links/media in HTTP or direct-file mode.
4. Write a final run report with source availability, baseline provenance,
   coverage, deferrals, and exact deployment handoff.

Remote deployment remains outside this workflow unless separately authorized.

## 8. Proposed command and API surface

### 8.1 CLI MVP

```bash
llm-wiki docs prepare \
  --src-dir /path/to/project \
  --workspace ./project-docs \
  --baseline bootstrap-source \
  --site-name "Project" \
  --audience user,operator,contributor \
  --project-brief ./intake.md \
  --live-service-url https://staging.example.test \
  --allow-external-src

llm-wiki docs prepare \
  --src-dir /path/to/project \
  --input-wiki-dir /path/to/project/docs/llm_wiki \
  --workspace ./project-docs \
  --baseline existing-wiki \
  --wiki-freshness require-current \
  --site-name "Project" \
  --audience user,operator,contributor \
  --project-brief ./intake.md \
  --allow-external-src

llm-wiki docs packet --workspace ./project-docs \
  --stage wiki-enrichment --format markdown

llm-wiki docs record-result --workspace ./project-docs \
  --result ./wiki-agent-result.json

llm-wiki docs verify --workspace ./project-docs --format json

llm-wiki docs packet --workspace ./project-docs \
  --stage user-docs --format markdown

llm-wiki docs status --workspace ./project-docs --format json

llm-wiki docs export --workspace ./project-docs \
  --format mkdocs --file-friendly
```

Names are provisional. The important contract is that commands operate on an
explicit workspace and never discover or mutate target agent policy.

`--baseline bootstrap-source` and `--baseline existing-wiki` are mutually
exclusive strategies. Existing-wiki mode requires `--input-wiki-dir`; supplying
`--src-dir` enables source-revision and claim verification. Omitting source
requires an explicit `--wiki-freshness allow-unverified`, remains visible in all
packets/reports, and cannot produce a source-verified `publish_ready` verdict.
The only mutating freshness choice, `refresh-snapshot`, applies to the workspace
copy after its import hash is recorded, never to `--input-wiki-dir`.

The intake answers may be supplied interactively by the supervisor agent (the
default first-stage path) or non-interactively via
`--project-brief`/`--audience`/`--live-service-url` (or a single
`--intake-file`) for CI and resumable runs. `docs prepare` only records and
validates them and still runs no model; repeated `prepare` reuses the stored
intake rather than re-asking.

### 8.2 Python API MVP

Expose typed, non-`argparse` lifecycle functions:

- `prepare_documentation_run(...) -> DocumentationRun`;
- `adopt_documentation_wiki_snapshot(...) -> DocumentationWikiSnapshot`;
- `build_documentation_agent_packet(...) -> DocumentationAgentPacket`;
- `record_documentation_agent_result(...) -> DocumentationRun`;
- `verify_documentation_run(...) -> DocumentationVerificationReport`;
- `get_documentation_run_status(...) -> DocumentationRunStatus`.

They must raise typed exceptions rather than `SystemExit`, return structured
results rather than scrape console output, and preserve the same mutation policy
as the CLI. The snapshot result must expose recognized schema versions, copied
paths/hashes, rejected entries, freshness, and any workspace-only migration or
refresh evidence.

### 8.3 Later optional runner adapters

Only after the packet/result protocol works with at least two independent agent
platforms, consider a plugin-owned command such as:

```bash
llm-wiki docs run --workspace ./project-docs --runner <plugin-id>
```

The portable packet/result contract remains provider-neutral. It may request an
abstract capability route such as `wiki_update_economy`, but it must not require
an OpenAI-shaped endpoint or embed a concrete provider model id. The executing
host or optional runner resolves that route locally and records a separate,
trusted execution receipt.

Routine generic-agent wiki refreshes and bounded documentation handoffs should
prefer a capability-qualified lower-cost worker so the capable supervisor is
reserved for work selection, ambiguous architecture or claim reconciliation,
review, and explicit escalation. Native OpenAI/Codex, Anthropic, Google Gemini,
Mistral, DeepSeek, and Alibaba/Qwen transports; explicit gateway/cloud
backends; OpenAI-compatible transports; and qualified local/self-hosted models
are all valid bindings. None is the portable default, and OpenAI compatibility
is only a transport characteristic, not the provider-neutral identity model.
The binding, override, secret-handling, qualification, receipt, and cost-control
work is decomposed in the
[model-aware routing backlog](model_aware_wiki_update_agent_routing_backlog_2026-07-18.md).

The core package should not own API keys, model selection, billing, or
provider-specific prompt transport.

## 9. Implementation backlog

### 9.1 Dependency order

| ID | Title | Priority | Depends on | Primary type | Local status |
|---|---|---|---|---|---|
| ADW-000 | Correct existing cross-skill handoff defects | P0 | None | Skills/tests | Implemented |
| ADW-001 | Documentation-run ADR and schemas | P0 | None | Contract/docs/tests | Implemented |
| ADW-002 | Central integration and mutation policy | P0 | ADW-001 | Code/tests | Implemented |
| ADW-003 | Workspace filesystem baseline and integrity checks | P0 | ADW-001, ADW-002 | Code/tests | Implemented |
| ADW-004 | Bootstrap service boundary for lifecycle/API callers | P0 | ADW-002 | Refactor/tests | Implemented |
| ADW-005 | `docs prepare/status` CLI and Python API | P0 | ADW-003, ADW-004 | Code/tests/docs | Implemented |
| ADW-005A | Existing enriched-wiki adoption and snapshot provenance | P0 | ADW-003, ADW-004, ADW-005 | Code/tests/docs | Implemented |
| ADW-006 | Deterministic semantic worklist | P0 | ADW-004, ADW-005, ADW-005A | Code/tests | Implemented |
| ADW-007 | Agent packet/result protocol | P0 | ADW-001, ADW-006 | Code/tests | Implemented |
| ADW-008 | External agent-docs orchestration skill | P0 | ADW-000, ADW-005, ADW-007 | Skill/docs/tests | Implemented locally |
| ADW-009 | Dedicated `wiki-semantic-enhance` skill and readiness ledger | P0 | ADW-006, ADW-008 | Skills/tests | Implemented locally; real-agent acceptance outstanding |
| ADW-010 | User-docs skill-chain stage | P1 | ADW-008, ADW-009 | Skills/tests | Implemented locally; real-agent acceptance outstanding |
| ADW-011 | Review ledger and adjustment-loop controller | P1 | ADW-007, ADW-010 | Code/skill/tests | Implemented |
| ADW-012 | Workspace export/final report | P1 | ADW-010, ADW-011 | Code/docs/tests | Implemented |
| ADW-013 | Cross-platform and adversarial contract suite | P1 | ADW-002 through ADW-012, including ADW-005A | Tests/security | Implemented locally |
| ADW-014 | Real-project pilots, sibling wiki, and closeout | P1 | ADW-013 | Dogfood/docs/report | Partial; external qualification remains |

### ADW-000 - Correct existing cross-skill handoff defects

Files:

- `src/llm_wiki_cli/skills/wiki-bootstrap/SKILL.md`;
- `src/llm_wiki_cli/skills/user-docs-author/SKILL.md`;
- `src/llm_wiki_cli/skills/usage-examples/SKILL.md`;
- focused skill/package tests.

Tasks:

- replace the stale `.llm-wiki-surface-index.json` reference with the actual
  `.llm-wiki-surface.json` contract;
- add the missing file-friendly re-export step before file-mode checks in
  `user-docs-author`;
- require a real site rebuild after usage-example changes before checking
  `_site`;
- add assertions for complete command/handoff sequences rather than only phrase
  presence.

Acceptance:

- each skill's output is a valid precondition for the next skill;
- documented commands match the live CLI;
- the fixes do not introduce a new core-package LLM path.

### ADW-001 - Documentation-run ADR and schemas

Files:

- new ADR under `reports/`;
- `src/llm_wiki_cli/services/contracts.py`;
- new `src/llm_wiki_cli/services/documentation_run.py`;
- focused schema tests.

Tasks:

- freeze the run and agent-result v1 schemas;
- freeze the tagged baseline-input union for source bootstrap versus existing
  wiki adoption, including input/snapshot hashes, compatibility, provenance,
  source availability, freshness, and workspace-only refresh decisions;
- freeze the intake-brief sub-schema (project-purpose statement, per-audience
  intent, live-service handle, and answered/declined provenance) as trusted
  human intent within the run schema;
- define stage transitions and forward-compatible additive-field policy;
- define relative/portable path representation and evidence hashing;
- document managed-KB, external-agent-docs, and raw-adapter mode boundaries;
- add fixtures for complete, partial, blocked, and resumed runs.

Acceptance:

- invalid transitions and unknown required enum values fail clearly;
- additive unknown fields remain tolerable for older readers where safe;
- no schema requires a provider/model id;
- every run records either a verified source revision or explicit imported-wiki
  provenance with `source_unavailable`, plus the trusted skill/package version.

### ADW-002 - Central integration and mutation policy

Files:

- new or existing policy service under `src/llm_wiki_cli/services/`;
- `commands/bootstrap_cmd.py`, `commands/sync_cmd.py`, `commands/upgrade_cmd.py`,
  `commands/install_cmd.py`, and `commands/status_cmd.py` only where policy must
  propagate;
- `services/plugins.py` and `services/skills.py` for trust/install boundaries.

Tasks:

- centralize allowed write roots and agent-integration capability checks;
- make external-agent-docs mode forbid schema, skill, hook, prompt, issue-report,
  and target-cache writes;
- make an adopted input wiki a separately baselined forbidden-write root even
  when it lives outside the source repository;
- disable source plugin loading unless explicitly trusted;
- gate live-service observation behind the intake opt-in: read-only, no secret
  persisted, captures confined to the disposable capture directory, and
  responses tagged as untrusted evidence;
- keep existing commands/defaults unchanged outside the new mode;
- define explicit conversion into managed agent-KB mode; never convert silently.

Acceptance:

- policy is resolved once and passed through services rather than duplicated
  boolean checks;
- every supported agent schema file and adopted input-wiki file remains
  byte-identical during an external docs run;
- existing managed-KB init/upgrade/plugin tests remain green.

### ADW-003 - Workspace filesystem baseline and integrity checks

Files:

- `services/documentation_run.py` or a focused integrity helper;
- new `tests/test_documentation_workspace.py`.

Tasks:

- capture bounded source-tree and adopted-wiki file/hash baselines;
- reject workspace/output roots inside the source or input-wiki root by default;
- detect source/input-wiki writes, symlink escapes, output escapes, and
  generated-block mutations;
- support spaces, Unicode, Windows separators, and external absolute source
  roots;
- ensure transient state stays under explicit workspace/cache paths.

Acceptance:

- a successful run changes only allowlisted workspace/cache files;
- a source/input-wiki mutation or symlink escape blocks stage advancement;
- tests run without requiring a Git repository.

### ADW-004 - Bootstrap service boundary for lifecycle/API callers

Files:

- `commands/bootstrap_cmd.py`;
- new/existing service module for request/result types;
- `api.py`;
- bootstrap/API tests.

Tasks:

- separate bootstrap request execution from `argparse`, printing, and
  `SystemExit`;
- return the existing machine-readable summary as a typed result;
- preserve CLI output and `--source-adapter` compatibility;
- expose the shared manifest/surface compatibility readers needed by snapshot
  adoption without coupling the importer to `argparse`;
- allow explicit helper/cache/plugin policy injection;
- keep deterministic content identical for equivalent options.

Acceptance:

- CLI and API produce equivalent wiki trees and summary data;
- typed API errors replace command exits for library callers;
- current bootstrap tests pass without mass fixture rewrites.

### ADW-005 - `docs prepare/status` CLI and Python API

Files:

- new `commands/docs_cmd.py`;
- `cli.py`, `api.py`, package exports;
- `tests/test_cli.py`, `tests/test_api.py`, and workspace tests.

Tasks:

- implement workspace creation, run-state persistence, status, and resume;
- accept and persist the explicit baseline selection plus input-wiki/freshness
  options without silently switching strategies;
- record the supervisor-supplied intake brief (interactively, or via
  `--project-brief`/`--audience`/`--live-service-url`/`--intake-file`); persist
  it once, reuse it on resume, never re-ask, and mark declined answers
  `unspecified`;
- call the refactored deterministic bootstrap boundary for `bootstrap_source`;
  hand `adopt_existing_wiki` to the snapshot boundary in ADW-005A;
- emit text and JSON results with stable paths and next-stage guidance;
- do not run an LLM or install target instructions;
- support interruption and idempotent resume.

Acceptance:

- repeated `prepare` is idempotent for the same source revision or input-wiki
  hash and options;
- a changed source revision or input-wiki hash is reported and requires an
  explicit refresh/re-import decision;
- `status` reports a healthy external-agent-docs run without complaining that no
  target agent is configured;
- status and resume retain the original baseline strategy, input provenance, and
  freshness decision.

### ADW-005A - Existing enriched-wiki adoption and snapshot provenance

Files:

- new `src/llm_wiki_cli/services/documentation_wiki_input.py` (name
  provisional);
- documentation-run, CLI, and API surfaces from ADW-001/ADW-005;
- new `tests/test_documentation_wiki_input.py` plus focused CLI/API fixtures;
- README and sibling-wiki documentation when the feature ships.

Tasks:

- implement a typed, path-safe read-only importer for a canonical wiki produced
  by supported `llm-wiki` bootstrap/sync/skill workflows;
- recognize current manifest/surface schemas and legacy `index.md`-only wikis;
  perform any legacy manifest seeding or schema migration only after the
  workspace snapshot is complete;
- copy eligible regular files into `<workspace>/wiki` without following
  symlinks, importing adjacent agent-policy/cache content, normalizing semantic
  Markdown, or silently dropping unknown files;
- record input-tree, per-file, and initial snapshot hashes plus recognized
  schemas, rejected/unknown entries, generated ownership markers, and semantic
  page inventory in `wiki-input.json`;
- preserve prior human/LLM-owned enrichments byte-for-byte at import time and
  classify them for later grounding/reuse rather than sending every page back for
  automatic rewriting;
- compare manifest/source identity and content freshness when `--src-dir` is
  available; implement fail-closed `require-current`, explicit
  `refresh-snapshot`, and explicit limited `allow-unverified` policies;
- ensure sync/upgrade under `refresh-snapshot` targets only the workspace copy and
  preserves semantic/generated ownership contracts;
- make prepare, status, packet, resume, verify, export, and final-report paths
  expose the imported baseline and its limitations consistently.

Acceptance:

- an existing wiki containing LLM-enriched overview, guide, module, and entity
  prose can seed a documentation run without re-bootstrap and without byte
  changes to the input wiki;
- all eligible files match the recorded initial snapshot before any explicit
  workspace-only migration/refresh, and prior semantic prose remains present;
- stale, corrupt, unsupported, symlinked, or path-escaping inputs fail with
  actionable diagnostics and never fall back silently to source bootstrap;
- source-backed imports can reach `verified_current`; wiki-only or explicitly
  stale imports remain visibly limited and cannot claim source-verified
  `publish_ready`;
- Windows, macOS, and Ubuntu path behavior is covered without relying on Git.

### ADW-006 - Deterministic semantic worklist

Files:

- new worklist service;
- reuse dependency/surface/checker services;
- focused worklist tests.

Tasks:

- detect placeholders, copied-docstring-only prose, missing flow behavior,
  missing architecture notes, unsupported sources, and user-profile findings;
- inventory imported semantic prose and classify each eligible page as
  `candidate_reuse`, `needs_grounding`, `needs_enhancement`, or `incompatible`;
- reuse dependency centrality and entrypoint evidence;
- emit stable P0/P1/P2 ids with suggested bounded context and acceptance checks;
- keep long-tail deferral explicit.

Acceptance:

- identical inputs produce stable ordering and ids;
- P0 covers primary architecture/workflow surfaces;
- already-grounded imported enrichments can satisfy work as `reused` without
  forced stylistic rewriting;
- worklist facts never claim that an unknown is safe or complete.

### ADW-007 - Agent packet/result protocol

Files:

- documentation-run service and renderers;
- `services/contracts.py`;
- protocol fixtures/tests.

Tasks:

- render Markdown and JSON packets from the same normalized request;
- validate structured results and reconcile them with run/stage ids;
- include ownership, trust, budget, evidence, and stop conditions;
- include baseline origin, input/snapshot hashes, source freshness, imported
  semantic-page classifications, and any limitation on the final verdict;
- carry the intake brief as trusted human intent ranked above inferred signals
  and separate from untrusted source instructions;
- add content-injection fixtures where source instructions conflict with the run
  policy.

Acceptance:

- two mock agent clients can consume/return the protocol without CLI internals;
- malicious or irrelevant target instructions never alter packet policy;
- a self-reported completion cannot bypass filesystem or deterministic checks.

### ADW-008 - External agent-docs orchestration skill

Files:

- new `src/llm_wiki_cli/skills/agent-docs/SKILL.md` and `reference.md`;
- package-data registration;
- `tests/test_skills.py` and `tests/test_package_metadata.py`.

Tasks:

- define supervisor ownership and ordered stage handoffs;
- own the first-stage intake interview: ask the bounded framing questions
  (project purpose, audiences, live service) exactly once, write the structured
  brief through `docs prepare`, and never re-ask on resume;
- route to existing skills instead of duplicating their detailed contracts;
- route the selected baseline through source bootstrap or existing-wiki adoption
  and require an explicit decision when freshness cannot be verified;
- define result-packet writing, pause/resume, deferral, and failure behavior;
- enforce one-heavy-gate-at-a-time interactive scheduling;
- keep the source and adopted input wiki read-only and workspace-only mutation
  visible.

Acceptance:

- the skill can be explicitly exported/loaded by an external agent platform;
- installing the Python package still writes no project files;
- invoking the skill does not require an auto-discovered instruction file.

### ADW-009 - Dedicated `wiki-semantic-enhance` skill and readiness ledger

Files:

- new `src/llm_wiki_cli/skills/wiki-semantic-enhance/{SKILL.md,reference.md}`;
- targeted references from `src/llm_wiki_cli/skills/wiki-bootstrap/*` and
  `src/llm_wiki_cli/skills/wiki-sync/*`;
- worklist/result protocol tests;
- public docs when behavior ships.

Tasks:

- define a distinct, resumable semantic phase after deterministic bootstrap or
  validated existing-wiki adoption;
- reuse centrality/P0/P1 rules without duplicating their ranking source;
- support optional source-root plus wiki-root/workspace parameters and remove
  mandatory source-repo commit language for external mode;
- preserve semantic-only/generated-owner guardrails;
- emit a versioned semantic-readiness ledger covering reused enrichments, P0/P1
  completion, deferrals, unsupported coverage, and generator defects;
- write the remainder and run report inside the workspace;
- let managed `wiki-bootstrap` hand off to the same semantic contract without
  changing its public first-adoption promise.

Acceptance:

- an agent completes a pilot semantic pass without touching the source;
- all P0 items are complete or explicitly deferred;
- imported semantic content is preserved unless a result packet records and
  justifies its workspace-only edit;
- user-doc authoring cannot start until the readiness ledger passes;
- when source is available, sync can resume the same workspace after a later
  source revision; a wiki-only run can resume from its recorded snapshot hash.

### ADW-010 - User-docs skill-chain stage

Files:

- `src/llm_wiki_cli/skills/agent-docs/*`;
- targeted adjustments to `user-docs-author`, `onboarding-guide`,
  `usage-examples`, `doc-review`, and `publish-docs` only where external mode
  requires them;
- skill/package tests.

Tasks:

- define ordered entry/exit criteria for each skill;
- require the enhanced wiki gate before user docs;
- allow a grounded imported enrichment to satisfy that gate as `reused`, while
  preventing unverified imported claims from flowing into primary user docs;
- make usage capture optional and separately authorized;
- normalize deferred-docs and validation findings into run state;
- preserve derived-output ownership.

Acceptance:

- a complete run produces an evidence-linked overview and at least one audience
  guide;
- user-profile checks pass without hiding raw reference failures;
- missing capture tooling produces an honest deferral rather than a fake example.

### ADW-011 - Review ledger and adjustment-loop controller

Files:

- documentation run/review services;
- `src/llm_wiki_cli/skills/doc-review/*` and
  `src/llm_wiki_cli/skills/agent-docs/*`;
- focused review-loop tests.

Tasks:

- normalize lint, CI, site, built-site, media, and agent-review findings;
- preserve finding ids/status/evidence through adjustment loops;
- cap loops and detect repeated unresolved conditions;
- require independent supervisor reconciliation before `publish_ready`.

Acceptance:

- no finding disappears without a terminal status and rationale;
- three repeated high-severity failures block the run;
- reviewer and worker roles can be the same agent in MVP while their packets
  remain separately auditable.

### ADW-012 - Workspace export and final report

Files:

- `commands/docs_cmd.py` and API;
- site export/check services only as needed for workspace composition;
- docs/report tests.

Tasks:

- compose user-profile export, optional build, built-link/media checks, and final
  report generation;
- record distribution mode and deployment handoff;
- include source revision/availability, skill/package versions, worklist
  coverage, deferrals, baseline strategy, imported-wiki provenance/freshness
  when applicable, and validation evidence;
- never deploy automatically.

Acceptance:

- final report is sufficient to reproduce or resume the run;
- reference wiki remains canonical and site output remains derived;
- a report based on an unverified/stale wiki snapshot states that limitation and
  cannot serialize a source-verified `publish_ready` status;
- direct-file and HTTP modes use their matching checks.

### ADW-013 - Cross-platform and adversarial contract suite

Files:

- new workspace/protocol integration tests;
- existing init/bootstrap/sync/upgrade/install/status/site/skill tests.

Cases:

- Windows, macOS, Ubuntu, and the project-supported Python matrix;
- no-Git source; source/workspace paths with spaces and Unicode;
- existing wiki inside the source tree, outside it, and with spaces/Unicode in
  its path; workspace nested under the input wiki must be rejected;
- current enriched wiki; legacy `index.md`-only wiki; stale manifest; unsupported
  future schema; missing/corrupt surface index; unknown files; symlinked and
  non-regular entries;
- input enrichments must survive import byte-for-byte, while an explicit
  workspace-only refresh may change generated blocks without changing semantic
  owner sections;
- all supported agent instruction files pre-populated with sentinel content;
- symlinks from workspace to source and source to workspace;
- target `AGENTS.md` containing conflicting instructions;
- untrusted plugin manifest/code in source;
- interrupted/resumed stage; source revision changes mid-run;
- resume must reuse the recorded intake brief without re-asking, including when
  answers were `unspecified`;
- declared live service that is unreachable, returns injected instructions, or
  demands real credentials;
- worker claims completion while source or generated blocks changed;
- worker claims an imported page is grounded or current when source/provenance
  evidence is absent;
- missing helpers/builders/capture tooling;
- large semantic remainder and budget exhaustion.

Acceptance:

- when a source target is present, its file hashes remain unchanged in every
  successful case;
- adopted input-wiki hashes remain unchanged in every successful or failed case;
- unsafe cases fail closed with actionable diagnostics;
- managed agent-KB regression tests prove unchanged defaults.

### ADW-014 - Real-project pilots, sibling wiki, and closeout

Pilots:

- one small fixture in ordinary CI;
- this repository as self-dogfood;
- at least two external projects of different supported language/framework shapes;
- at least one already-generated, LLM-enriched wiki adopted without re-bootstrap,
  with its imported semantic prose compared before/after;
- at least one real Windows execution in addition to Windows-style path fixtures;
- at least two agent platforms consuming the same packet/result protocol before
  runner adapters are considered.

Deliverables:

- run reports and before/after quality rubric, including existing-wiki reuse and
  preservation evidence;
- explicit generator defects and semantic remainder;
- README and sibling-wiki pages for installation, external agent docs,
  security/trust, skills, commands, and troubleshooting;
- changelog and package metadata checks;
- final review with a ship/no-ship decision.

Acceptance:

- all pilots with source access preserve source byte identity;
- the existing-wiki pilot preserves input byte identity and demonstrates useful
  user documentation derived from reused enrichments;
- agent-enhanced/user docs materially outperform the raw baseline on the rubric;
- public docs never tell standalone users to install target agent instructions;
- main-repo and sibling-wiki changes are committed separately when implementation
  lands.

## 10. Delivery phases

### Phase A - Contract and safety foundation (about 1 week)

ADW-000 through ADW-003.

Exit: schemas, central policy, and write-integrity tests are agreed before any
agent orchestration command ships.

### Phase B - External workspace MVP (about 2 weeks)

ADW-004 through ADW-009, including ADW-005A.

Exit: a host agent can prepare a workspace from either source bootstrap or a
validated existing-wiki snapshot, consume the explicit wiki-enrichment packet,
preserve/reuse eligible enrichments, enhance the canonical wiki, return a result,
and pass deterministic verification without modifying the target or input wiki.

### Phase C - User-docs and review loop (about 2 weeks)

ADW-010 through ADW-012.

Exit: the enhanced wiki feeds user-docs skills, independent review, and local
site export with a reproducible final report.

### Phase D - Hardening and release decision (about 2-4 weeks)

ADW-013 and ADW-014.

Exit: cross-platform/adversarial tests and real-project pilots support an honest
ship/no-ship decision. Provider-specific automatic runners remain deferred.

Effort bands are planning estimates, not release promises. Stop after each phase
if the acceptance evidence does not justify the next investment.

## 11. Success metrics and kill criteria

| Surface | Success metric | Initial threshold | Kill/re-scope signal |
|---|---|---:|---|
| Source isolation | Target files modified | 0 | Any unexplained target mutation |
| Existing-wiki isolation | Adopted input-wiki files modified | 0 | Import/refresh requires in-place mutation |
| Import preservation | Eligible imported files changed before an explicit workspace-only migration/refresh | 0 | Prior enrichments are silently normalized, dropped, or overwritten |
| Import provenance | Imported baselines with recorded input/snapshot hashes and freshness | 100% | User docs cannot distinguish current, stale, or unverified wiki input |
| Agent integration isolation | Target schema/skill/hook/config files modified | 0 | Mode requires target-policy injection |
| Generated ownership | CLI-owned blocks modified by agent | 0 | Agent cannot stay inside semantic surfaces |
| Wiki semantic pass | P0 items complete or explicitly deferred | 100% | Central pages remain generic after allowed loops |
| P1 budget | Selected central pages completed | 100% of declared budget | Worklist is too noisy or context cost is unbounded |
| User-doc readiness | Published primary pages with bootstrap placeholders | 0 | User profile routinely promotes raw generated prose |
| Claim grounding | Sampled high-impact claims supported by linked evidence | >= 95% | Unsupported claims persist after review |
| Navigation/task value | Pilot reader tasks completed from docs | >= 80% on a versioned task set | Raw wiki performs similarly or better |
| Intake fidelity | Stated audience/purpose honored in published docs; intake re-asked on resume | 100% honored, 0 re-asks | Docs ignore the stated audience/purpose, or resume loses the intake |
| Live-service safety | Real credentials/user data used against the observed service; service mutated | 0 | Observation needs production secrets or changes the service |
| Reproducibility | Run resumes from recorded state and revision | 100% of pilots | Resume depends on hidden chat context |
| Portability | Supported OS CI/pilot contract | Ubuntu, macOS, Windows | Workspace/path policy is platform-specific |

The riskiest assumption is that a bounded semantic worklist plus existing skills
can improve user documentation enough without giving the agent unrestricted
source access or letting it rewrite generated structure. A second risk is that
existing LLM-enriched wikis vary enough in version, freshness, and ownership
markers that safe reuse becomes noisy. The cheapest tests are paired manual
packet/result pilots: one using the current `wiki-bootstrap` path and one using a
known enriched wiki snapshot, both feeding `user-docs-author`, before automatic
runner support.

## 12. Verification strategy for implementation

Focused verification grows with each slice. Expected core commands include:

```bash
.venv/bin/pytest tests/test_documentation_workspace.py tests/test_cli.py tests/test_api.py -q
.venv/bin/pytest tests/test_documentation_wiki_input.py -q
.venv/bin/pytest tests/test_bootstrap.py tests/test_sync.py tests/test_init.py tests/test_upgrade.py tests/test_install.py tests/test_status.py -q
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py tests/test_site_export.py -q
.venv/bin/python -m compileall src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
```

Run full `pytest`, builds, and repository-wide `llm-wiki` gates serially only at
phase boundaries. Use `--jobs 1` in interactive sessions. If resource-exhaustion
signals occur, stop rather than retrying parallel heavy gates.

The implementation must remain portable across Windows, macOS, and Ubuntu. The
project instructions require Python 3.9+ compatibility, while current package
metadata declares Python 3.10+; reconcile that policy explicitly before release
instead of advertising an untested floor.

## 13. Final recommendation

Proceed with completed Phase-B/Phase-C real-agent pilots: run the semantic,
user-docs, review, and export stages on both source-bootstrap and existing
enriched-wiki baselines, then finish Phase-D real Windows/macOS and
two-agent-platform qualification. Keep provider-specific embedded runners and
model-aware default graduation deferred until those packet/result and quality
gates pass.

The durable product is not a deterministic documentation library and not a
second agent knowledge-base installer. It is a **portable, agent-driven
documentation workspace**: deterministic evidence and guardrails below,
skill-driven semantic work in the middle, and deterministic review/publishing
gates above. That preserves the existing architecture-KB use case while making
standalone documentation genuinely useful to human readers.
