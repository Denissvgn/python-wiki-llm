# Standalone documentation workspaces

Standalone documentation mode builds human-facing documentation in an explicit
workspace outside the source project. It can start from either the source tree
or an existing LLM Wiki, including semantic pages previously enriched by an
LLM. The deterministic `llm-wiki` core prepares evidence, packets, checks, and
a local publication handoff. A host agent or handoff runner performs the
semantic writing.

This mode is additive. The normal managed-wiki workflow under
`docs/llm_wiki/`, its agent instruction files, hooks, and `sync` behavior remain
unchanged.

## What the core does and does not do

The core:

- creates one caller-selected documentation workspace;
- records a content-hash baseline for the source and, when used, copies a
  byte-preserving input-wiki snapshot as read-only evidence;
- builds or adopts a deterministic canonical wiki under `<workspace>/wiki`;
- creates a bounded semantic worklist and readiness evidence;
- exports versioned skills and provider-neutral stage packets;
- reconciles agent result claims with actual workspace changes;
- checks source/input integrity and CLI-owned generated content;
- exports a user-documentation mirror under `<workspace>/site`;
- optionally runs an already-installed, explicitly authorized site builder;
- writes a local final report and deployment handoff.

The core does **not**:

- import a provider SDK, choose a provider implicitly, call a model, or hold
  provider credentials;
- install or modify `AGENTS.md`, `CLAUDE.md`, hooks, skills, prompts, caches, or
  agent configuration in the source project;
- treat instructions found in source files or an imported wiki as run policy;
- start, build, or deploy the target application;
- prepare missing extractor helpers or install a site builder;
- commit, push, publish, or deploy documentation.

The host remains responsible for invoking a generic agent or handing a packet
to another runner, collecting its versioned JSON result, and separately
authorizing any deployment.

## Workspace layout

Given `--workspace ./project-docs`, the owned paths are:

```text
project-docs/
├── .llm-wiki-docs/
│   ├── run.json
│   ├── policy.json
│   ├── evidence/
│   ├── packets/
│   ├── results/
│   ├── skills/
│   └── stages/
├── wiki/      # canonical documentation plus controller-owned native metadata
├── site/      # derived user-profile Markdown mirror
└── _site/     # optional output from an authorized real builder
```

### Documentation calibration evidence is diagnostic

Protocol and artifact strings containing `p0-calibration` are historical wire
identifiers retained for compatibility; they do not name the feature in prose.

Every prepared run now records two supervisor-owned artifacts beside the
semantic worklist:

- `evidence/p0-calibration-census.json` is a priority-blind inventory of the
  flow population. It preserves detector and language provenance, routes,
  bounded call/data-flow evidence, boundary confidence and gaps, dependency
  metrics, source/page hashes, source citations, explicit unknowns, and an
  exhaustive unlabelled review inventory. Its exact-normalized operation
  families are preliminary partitioning hints with
  `semantic_equivalence=unadjudicated`.
- `evidence/p0-calibration-shadow.json` places the frozen v1 priority and
  reason codes beside a separate candidate record. Normal preparation emits
  `mode=evidence_only`, `candidate_evaluated=false`, and null candidate fields
  because it has no sealed labels or qualified candidate policy.

Both files are included in the supervisor control-integrity snapshot. A legacy
wiki without a surface-index flow list uses a flow-page fallback and records
`population.complete=false`; it does not claim that the fallback is a complete
source inventory.

These artifacts do not change the semantic worklist or current priority rule.
A host may use them as inputs to a separately isolated calibration runner, but
must not promote a candidate to the default without independent labels,
holdout custody, real-agent comparison, and the declared compatibility gates.
Missing authorization or enforceable role/holdout isolation is a fail-closed
`BLOCKED_NO_SHIP` result, not permission to infer labels in-process.

### Protected calibration admission and intake

The calibration controller is a sibling lifecycle, not another state of the
documentation run. It consumes exactly two independently prepared controls
whose source identity, worklist, complete census, and read-only-source evidence
match. It then freezes a deterministic, priority-blind evidence bundle in a
new protected root. The controls and their `llm-wiki-documentation-run/v1`
state remain unchanged.

The examples in this section assume `/path/to/operator-calibration` is a
dedicated operator directory outside the source and implementation checkout.
Its controller, two controls, manifests, and pre-created packet directory are
siblings. Substitute equivalent absolute paths on Windows.

```bash
llm-wiki docs calibration prepare \
  --root /path/to/operator-calibration/controller \
  --control-workspace /path/to/operator-calibration/control-a \
  --control-workspace /path/to/operator-calibration/control-b \
  --execution-manifest /path/to/operator-calibration/execution-manifest.json

llm-wiki docs calibration admit \
  --root /path/to/operator-calibration/controller \
  --authority-grant /path/to/operator-calibration/authority-grant.json

llm-wiki docs calibration status \
  --root /path/to/operator-calibration/controller
```

For the local profile, start from this manifest shape and replace every
placeholder with a real absolute executable identity and digest-pinned image:

```json
{
  "schema_version": "llm-wiki-p0-calibration-execution-manifest/v1",
  "profile": "local_no_egress",
  "roles": ["intake-a", "intake-b", "intake-c", "verifier"],
  "budgets": {
    "max_concurrent_workers": 3,
    "max_attempts_per_role": 2,
    "max_total_calls": 8,
    "max_packet_bytes": 1048576,
    "max_result_bytes": 1048576
  },
  "oci": {
    "runtime": "docker",
    "executable": "<absolute canonical docker-or-podman path>",
    "executable_sha256": "sha256:<64 lowercase hex characters>",
    "worker": {
      "image": "<registry/name>@sha256:<64 lowercase hex characters>",
      "entrypoint": ["/opt/calibration-worker"]
    },
    "probe": {
      "image": "<registry/name>@sha256:<64 lowercase hex characters>",
      "entrypoint": ["/opt/calibration-probe"]
    },
    "user": "1000:1000",
    "resources": {
      "pids_limit": 32,
      "memory_bytes": 536870912,
      "cpu_millis": 750,
      "tmpfs_bytes": 16777216
    },
    "timeout_seconds": 120,
    "termination_grace_seconds": 5,
    "max_packet_bytes": 1048576,
    "output_limits": {
      "stdout_bytes": 8192,
      "stderr_bytes": 4096,
      "result_bytes": 1048576
    }
  },
  "external_routes": []
}
```

The executable path must already be fully resolved, its basename must match
`docker` or `podman`, and its hash must cover that exact file. An image may not
carry a mutable tag beside its digest. The configured non-root UID/GID must be
able to write the role output mount.

`prepare` returns the new `cohort_id`, `execution_manifest_hash`, and
`evidence_bundle_hash`. Copy those exact values into the authority grant;
copy `budgets` and `external_routes` byte-for-byte from the frozen manifest:

```json
{
  "schema_version": "llm-wiki-p0-calibration-authority-grant/v1",
  "grant_id": "operator-grant-001",
  "cohort_id": "<prepare output cohort_id>",
  "decision_scope": "p0_policy_default",
  "profile": "local_no_egress",
  "evidence_bundle_hash": "<prepare output evidence_bundle_hash>",
  "execution_manifest_hash": "<prepare output execution_manifest_hash>",
  "allowed_roles": ["intake-a", "intake-b", "intake-c", "verifier"],
  "budgets": {
    "max_concurrent_workers": 3,
    "max_attempts_per_role": 2,
    "max_total_calls": 8,
    "max_packet_bytes": 1048576,
    "max_result_bytes": 1048576
  },
  "external_routes": [],
  "issued_at": "<current UTC RFC 3339 timestamp>",
  "expires_at": "<later UTC RFC 3339 timestamp>",
  "revocation": {
    "reference": "operator-revocations/001",
    "revoked": false
  },
  "authentication": {
    "method": "host-protected-operator",
    "principal": "<operator audit identity>",
    "reference": "<approval reference>",
    "verified_by_host": true
  }
}
```

The authentication object is audit metadata, not a self-authenticating grant.
Admission independently derives the current host principal and access
mechanism from the protected controller root and binds that evidence to the
grant, manifest, evidence bundle, and cohort. A root whose ownership, POSIX
mode, or Windows DACL is not restrictive fails closed.

The root must be new or empty and must not overlap a source, documentation
control, worker output, packet output, or implementation worktree. Immutable
numbered artifacts and transition records are canonical; `run.json` is a
rebuildable current-state snapshot. A dedicated controller lock, generation
and transition-head comparisons, guarded no-follow I/O, and crash recovery
protect state changes. Unknown files, ambiguous recovery, an indeterminate
dispatch, or unavailable enforcement blocks the cohort without erasing
evidence. Source/control mutation or ledger tampering rejects it.

For `local_no_egress`, the frozen manifest supplies the Docker or Podman
executable identity, digest-pinned worker and probe images, fixed entrypoints,
resource limits, and timeouts. Admission runs the probe image with a read-only
root filesystem, no capabilities, no new privileges, a non-root identity,
bounded resources, a temporary `/tmp`, no engine socket, and `--network none`.
The probe must demonstrate that controller, source, credential, other-role,
holdout-sentinel, network, and engine-socket access are denied.

The only persistent writable container target is a private, pre-created result
file. The broker mounts that file—not its host directory—read-write and sets
the `fsize` soft and hard limits to the exact frozen result-byte budget. Worker
and probe entrypoints must overwrite the supplied result path; they cannot
depend on creating a temporary sibling and renaming it into place. Admission
also attempts a one-byte-over-limit extension and sibling creation. Both must
be denied. Podman uses a keep-ID user namespace for this file handoff. If
Docker or Podman cannot enforce the file bind, identity mapping, read-only
parent, or file-size limit on the current host, admission is
`BLOCKED_NO_SHIP`. Treat this as host-specific evidence and do not infer the
same enforcement on another operating system or runtime installation.

`external_authorized` remains a credential-free protocol contract. It can
qualify only when a separately authenticated host broker establishes the
attestation and matching dispatch receipts outside the submitted JSON. The
package ships no provider credential, SDK, external-provider adapter, or
self-authenticating receipt path. The ordinary CLI exposes no authenticator
selector and remains fail-closed. An embedding Python host that has already
authenticated the broker scopes lifecycle calls with
`use_calibration_host_broker_authenticator`.

After admission, write each private packet to an explicit path:

```bash
llm-wiki docs calibration packet \
  --root /path/to/operator-calibration/controller \
  --role intake-a \
  --output /path/to/operator-calibration/packets/intake-a.json
llm-wiki docs calibration dispatch \
  --root /path/to/operator-calibration/controller \
  --role intake-a

# Only for a separately executed authenticated broker:
llm-wiki docs calibration record-result \
  --root /path/to/operator-calibration/controller \
  --dispatch-receipt /path/to/operator-calibration/broker/dispatch-receipt.json \
  --result /path/to/operator-calibration/broker/agent-result.json

llm-wiki docs calibration verify \
  --root /path/to/operator-calibration/controller \
  --no-advance
```

Issue `intake-a`, `intake-b`, and `intake-c` independently before issuing the
verifier. Every proposal and verifier disposition must cite the frozen source
evidence. The verifier must account for all proposal claims and retain a
coherent source-supported purpose, audience/task set, and primary journey.
Each role receives at most two attempts, and ambiguous or exhausted dispatches
fail closed.

Successful verification ends at `INTAKE_FROZEN`. The frozen task oracle,
label-field contract, and optimizer-search contract define fields, objectives,
constraints, seeds, and deterministic tie-breaking only. They contain no
labels, scores, weights, candidate policy, adoption decision, release
authority, or publication authority.

Only the workspace, an explicit helper cache, and an explicit disposable
capture root are eligible write roots. The source and adopted input wiki remain
forbidden write roots throughout the run.

The general source/workspace baseline accepts at most 100,000 regular files,
128 MiB per file, and 2 GiB in aggregate. The limits are checked before and
while each file is streamed so a file that grows during hashing cannot bypass
the budget. Oversized inputs fail closed; no partial baseline is accepted.

Each eligible write root must not overlap either evidence root: the workspace,
helper cache, and capture root cannot be the source or input-wiki root, an
ancestor of either root, or a descendant of either root. The examples assume
they are run from a parent or sibling directory rather than from inside the
target project.

### Supervisor and worker isolation

The workspace is owned by the host supervisor; it is not a directory-wide
worker sandbox. The host must enforce the packet's read/write split with
operating-system, container, agent-platform, or brokered file permissions:

- Keep `.llm-wiki-docs/run.json`, `policy.json`, `stages/`, `evidence/`,
  `packets/`, and `skills/` under supervisor-only write control. Workers may
  read only the packet-named evidence and exported skills.
- Give a worker write access only to the current packet's stage-allowed wiki
  surfaces and one bounded result handoff. If that handoff is placed under
  `.llm-wiki-docs/results/`, grant the exact stage result file or broker it back
  to the supervisor; never grant write access to the results directory or the
  rest of the control tree. Keep `.llm-wiki-manifest.json`,
  `.llm-wiki-surface.json`, and `.llm-wiki-knowledge.json` under supervisor-only
  write control even though they live in the wiki directory.
- Let the supervisor invoke `record-result` and own the persisted result,
  reconciliation evidence, stage receipts, and later transitions. A path named
  in a packet is contract metadata, not an operating-system permission grant.

The lifecycle rejects links and special files in its control tree and compares
recorded hashes and stage receipts, so ordinary accidental or partial tampering
is detected. Those receipts live in the same workspace, however, and are not a
cryptographic boundary against an actor that shares the supervisor's principal
and can replace the entire workspace plus its receipts. If the host cannot
isolate the control plane from a worker, the run evidence is not trustworthy
and the stage must not advance. This contract is identical for generic-agent
and handoff execution and for every hosted or local model provider.

## Prepare from source

Prepare required language helpers before the run. Preparation is explicit and
may use a cache outside the source repository:

```bash
llm-wiki prepare-extractors \
  --src-dir /path/to/project \
  --allow-external-src \
  --cache-dir /tmp/llm-wiki-helpers
```

Examples use POSIX-style paths for brevity. The commands accept ordinary
platform paths on Windows, macOS, and Linux; select a platform-appropriate
temporary/cache directory and pass builder arguments as argv, not a shell
command string.

Then create the standalone workspace:

```bash
llm-wiki docs prepare \
  --workspace ./project-docs \
  --baseline bootstrap-source \
  --src-dir /path/to/project \
  --allow-external-src \
  --helper-cache-dir /tmp/llm-wiki-helpers \
  --site-name "Project" \
  --audience user,operator \
  --audience-intent "user=install and complete the first task" \
  --audience-intent "operator=operate and troubleshoot safely" \
  --project-brief ./project-purpose.md \
  --site-format mkdocs \
  --file-friendly \
  --format json
```

`bootstrap-source` requires `--src-dir`. The deterministic bootstrap uses
source-adapter behavior, so it writes inside the workspace and does not install
target instructions. Source plugins are disabled by default because loading a
plugin executes source-repository code in the current process. Use
`--trust-source-plugins` only for a plugin tree you explicitly trust.

The supervisor supplies intake once. `--project-brief` is UTF-8 text;
`--audience` accepts comma-separated values and may be repeated. For CI, use a
single JSON intake file instead:

```json
{
  "project_purpose": "Help operators install and run Project safely.",
  "audiences": ["user", "operator"],
  "audience_intent": {
    "user": "install and complete the first task",
    "operator": "operate and troubleshoot safely"
  },
  "live_service": {
    "address": "https://staging.example.test",
    "access_mode": "anonymous",
    "observation_allowed": false
  }
}
```

Pass it with `--intake-file ./intake.json`. Direct intake flags and
`--intake-file` cannot be mixed. Missing or declined answers are stored as
`unspecified`, not inferred from untrusted source prose.

Project-brief, intake, and result files use a 1,000,000-byte input limit. The CLI
reads only the limit plus one byte before rejecting an oversized file, so the
limit is also a memory-allocation boundary rather than a check after a full
read. Run v1 readers do not coerce trusted values: purpose, audiences, audience
intent, live-service decisions, timestamps, policy labels, source revisions,
schema versions, and run-local skill bindings must have their canonical types
and relationships.

`--observe-live-service` records a supervisor permission decision and validates
that an explicit disposable `--capture-dir` was supplied. The deterministic
core makes no HTTP request and captures nothing. A host that later performs an
observation must authorize that execution separately and make any resulting
evidence available through the stage packet's declared read/write contract;
the permission flag alone does not grant packet access to the capture root.

## Adopt an existing enriched wiki

Use `existing-wiki` to reuse a canonical wiki created by `llm-wiki bootstrap`,
`sync`, or the bundled wiki skills. Semantic overview, guide, workflow, module,
and entity prose—including previous LLM enrichments—is copied into the
workspace before later classification:

```bash
llm-wiki docs prepare \
  --workspace ./project-docs \
  --baseline existing-wiki \
  --input-wiki-dir /path/to/project/docs/llm_wiki \
  --src-dir /path/to/project \
  --wiki-freshness require-current \
  --allow-external-src \
  --site-name "Project" \
  --audience user,operator \
  --project-brief ./project-purpose.md \
  --site-format mkdocs \
  --file-friendly \
  --format json
```

At import time the snapshot service:

- requires `index.md` and recognizes legacy, manifest v4, and current manifest
  v5 metadata forms;
- copies eligible regular files byte-for-byte before any workspace refresh;
- records input-tree, per-file, initial-snapshot, schema, generated-owner, and
  semantic-page evidence;
- enforces the same fail-closed resource budget during snapshot and later
  fingerprint checks: at most 8,192 entries, 4,096 regular files, 64 MiB per
  file, 512 MiB total, and 16 path components; semantic inspection is further
  bounded to 4 MiB per Markdown page and 16 MiB across inspected Markdown;
  usage and limits are recorded in `wiki-input.json`;
- rejects symlinks, reparse points, non-regular files, path escapes,
  non-portable/colliding names, agent-policy files, and cache content;
- inventories unknown regular wiki entries instead of silently discarding
  them;
- leaves the input wiki unchanged.

The accepted metadata forms are deliberately distinct:

| Input form | Adoption behavior |
|---|---|
| No metadata and a canonical `index.md` | Preserve the legacy index-only behavior. |
| Manifest v4 plus its surface index, with no knowledge index | Validate and preserve the pre-native pair. |
| Markerless manifest v5 plus its surface index, with no knowledge index | Validate the v5 surface-only state without claiming native knowledge. |
| Marked manifest v5 plus matching surface and knowledge indexes | Validate the complete native projection as one committed trio. |

An orphan artifact, partial or mixed trio, unexpected knowledge index, corrupt
JSON, unsupported future version, marker mismatch, cross-artifact mismatch, or
canonical Markdown snapshot mismatch is rejected. Validation uses the exact
guarded bytes collected during the bounded snapshot; it does not reopen an
untrusted artifact by pathname. Artifact metadata is inert and cannot select or
execute a source plugin.

Manifest v5 is the current writer format. The manifest, surface index, and
knowledge index are controller-owned generated artifacts in the workspace.
Their fingerprints are part of generated ownership, and workers must never
edit, remove, add, or regenerate them. A v4 or markerless v5 input remains
representable without fabricating a knowledge fingerprint.

Imported pages are classified independently for reuse and grounding. Existing
prose is not rewritten merely for style. Important claims must still be
grounded in current source/wiki evidence before they are used in published
human documentation.

### Freshness policies

Choose the policy explicitly:

- `require-current` fails closed unless the source is available and compatible.
  For manifest v4, the current supported-source inventory must have the same
  paths and hashes as the imported manifest, and recorded generation inputs
  such as OpenAPI must still match. For a manifest v5 native trio, the same
  source comparison is combined with independent live evaluation of the
  effective generation options, deep-inventory policy, semantic-preservation
  default, extractor registry, and explicitly trusted producer commitments.
  The recorded generation-options hash is never accepted as live evidence. A
  failed live projection remains unverified; a computed source or
  generation-basis mismatch is verified stale. Neither can pass this policy.
- `refresh-snapshot` requires a readable source. It first records and copies the
  input, then refreshes only `<workspace>/wiki` from source. Imported semantic
  prose is retained for later grounding/reuse, and the controller commits the
  refreshed native projection in the workspace; the original input wiki is
  never refreshed or modified.
- `allow-unverified` permits wiki-only adoption when source is unavailable. The
  limitation remains visible in packets and reports and cannot support a
  source-verified `publish_ready` verdict. A validated native projection may be
  used as snapshot-only evidence, but live freshness is not evaluated and the
  run never upgrades it to a current-source claim.

Example workspace-only refresh:

```bash
llm-wiki docs prepare \
  --workspace ./project-docs \
  --baseline existing-wiki \
  --input-wiki-dir /path/to/project/docs/llm_wiki \
  --src-dir /path/to/project \
  --wiki-freshness refresh-snapshot \
  --allow-external-src \
  --site-name "Project" \
  --audience user
```

Example source-unavailable adoption:

```bash
llm-wiki docs prepare \
  --workspace ./project-docs \
  --baseline existing-wiki \
  --input-wiki-dir /path/to/exported/llm_wiki \
  --wiki-freshness allow-unverified \
  --allow-external-src \
  --site-name "Project" \
  --audience user
```

`--wiki-freshness refresh-snapshot` is an input-wiki freshness decision.
`--refresh` is different: it archives the CLI-owned artifacts of an existing
run and deliberately rebuilds/reimports the entire run baseline. Use
`--refresh` only after reviewing changed source/input evidence or intentional
contract changes.

## Run the agent stages

The stage protocol is the same for every provider and runner:

1. Ask the CLI for a stage packet.
2. Let the host invoke one bounded agent with that packet and the exported
   skills.
3. Save the agent's versioned JSON result.
4. Ask the CLI to reconcile the result with filesystem evidence.

Start with semantic enrichment:

```bash
llm-wiki docs packet \
  --workspace ./project-docs \
  --stage wiki-enrichment \
  --format markdown > wiki-enrichment-packet.md

# The host invokes its selected agent. The llm-wiki core invokes no model.

llm-wiki docs record-result \
  --workspace ./project-docs \
  --result ./wiki-enrichment-result.json \
  --format json
```

Continue only after reconciliation advances the run:

```bash
llm-wiki docs packet \
  --workspace ./project-docs \
  --stage user-docs \
  --format markdown > user-docs-packet.md

llm-wiki docs record-result \
  --workspace ./project-docs \
  --result ./user-docs-result.json \
  --format json

llm-wiki docs packet \
  --workspace ./project-docs \
  --stage review \
  --format markdown > review-packet.md

llm-wiki docs record-result \
  --workspace ./project-docs \
  --result ./review-result.json \
  --format json
```

Packets are also persisted as Markdown and JSON under
`.llm-wiki-docs/packets/`. A packet identifies allowed reads/writes,
forbidden actions, trusted intake, worklist/readiness evidence, ordered skills,
budgets, stop conditions, and the expected result schema. Source files,
imported prose, README instructions, target agent files, and live-service
responses remain untrusted evidence; they cannot alter the packet policy.

An agent result uses
`llm-wiki-documentation-agent-result/v1`. A minimal shape is:

```json
{
  "schema_version": "llm-wiki-documentation-agent-result/v1",
  "run_id": "copy-from-the-packet",
  "stage": "wiki-enrichment",
  "status": "complete",
  "changed_wiki_paths": ["modules/example.md"],
  "reused_work_ids": [],
  "completed_work_ids": ["copy-a-real-id-from-the-worklist"],
  "deferred_work_ids": [],
  "claims_evidence_pages": ["modules/example.md"],
  "unresolved_unknowns": [],
  "unsupported_source_notices": [],
  "requested_follow_up_checks": [],
  "reported_source_writes": [],
  "reported_input_wiki_writes": [],
  "reported_generated_block_edits": [],
  "imported_page_edits": [],
  "deferral_rationales": {},
  "findings": []
}
```

Do not copy the sample work/path values literally. Report exactly what changed
and use only work IDs present in the packet's worklist. `record-result`
independently derives the changed paths, verifies source/input hashes, and
checks generated ownership. Every deferred work ID needs exactly one
`deferral_rationales` entry. Every changed imported semantic page needs one
`imported_page_edits` record bound to its work ID, canonical path, before/after
hashes, evidence, and rationale. A completed review must cite at least one
sampled canonical Markdown page; partial or blocked reviews may return without
one and remain resumable. A false claim or forbidden write blocks the run.

After accepting a worker result that changes canonical Markdown, the supervisor
refreshes the manifest v5 surface/knowledge projection from the verified source,
records the native commit, and re-anchors generated ownership before running
later validation or dispatching another packet. This applies to both semantic
wiki enrichment and user-documentation edits. Workers report only their
authorized Markdown paths; controller-generated artifact paths are recorded
separately. If source is unavailable or cannot be verified, the controller
skips native refresh, records the snapshot-only limitation, and does not claim
current native knowledge.

## Bundled skills

Preparation exports a versioned, hashed run-local copy of the relevant skills
under `.llm-wiki-docs/skills/`; it does not install them in the source project.
`agent-docs` is exported for the host supervisor and describes orchestration,
intake, trust, resume, and handoff. Stage packets then select only the bounded
worker skills needed for that stage:

- `wiki-semantic-enhance` grounds/reuses existing prose and completes the
  semantic worklist without touching generated owners;
- `user-docs-author`, `onboarding-guide`, `usage-examples`, and `publish-docs`
  guide the human-doc stage; usage capture remains separately authorized;
- `doc-review` drives independent evidence-backed finding reconciliation.

Skill instructions do not grant extra filesystem or execution authority. The
packet and recorded policy remain the controlling contract.

## Provider-neutral, low-cost host routing

Agent packets deliberately contain no provider credential, endpoint, SDK, or
provider-specific invocation. A host can route the same packet through native
Anthropic or Google Gemini, OpenAI/Codex or an explicit OpenAI-compatible
backend, Mistral, DeepSeek, Alibaba/Qwen, a gateway/cloud backend, or a
qualified local/self-hosted model. OpenAI API compatibility is a transport
property, not provider identity. Model identifiers are caller configuration
strings, not hard-coded protocol defaults.

The supported Python API provides credential-free selection metadata for two
host invocation modes:

- `generic-agent`: the host gives a bounded packet to a generic agent runner;
- `handoff`: the host serializes the same packet/result contract for another
  agent or platform.

Both mode defaults must select a `low-cost` route. A `balanced` or `capability`
route is used only when a configured signal matches an escalation rule or the
user supplies an explicit override. This preserves more capable and more
expensive models for work that needs them. Apply the routine low-cost selection
to ordinary wiki-enrichment/update packets in both generic-agent and handoff
flows; escalate only on the policy's recorded signals.

Provider families and tiers are host-maintained classification labels. The
current metadata uses `other` for provider families not named by its small v1
enum while preserving caller-supplied provider/model identifiers. The core
does not ship native Anthropic, Gemini, OpenAI, Mistral, DeepSeek, Qwen, or
other provider adapters; it does not query current prices or capabilities, and
it cannot verify that a configured `low-cost` model is actually inexpensive.
The host must keep those classifications current, invoke its own native or
compatible runner, and persist the returned selection receipt outside the
provider-neutral lifecycle packet. The lifecycle does not record or prove
which concrete model actually ran. First-class publisher/backend/transport
bindings, concrete adapters, price evidence, and runner receipts remain the
responsibility of a separate multi-provider routing layer rather than this
deterministic core contract.

Example `model-routing.json` (the model IDs are placeholders to replace with
your runner's configured IDs):

```json
{
  "schema_version": "llm-wiki-documentation-model-routing/v1",
  "routes": [
    {
      "route_id": "openai-compatible-low",
      "provider_family": "openai-compatible",
      "provider_id": "configured-openai-compatible-runner",
      "model_id": "configured-low-cost-model",
      "tier": "low-cost",
      "modes": ["generic-agent", "handoff"]
    },
    {
      "route_id": "anthropic-low",
      "provider_family": "anthropic",
      "provider_id": "configured-anthropic-runner",
      "model_id": "configured-low-cost-model",
      "tier": "low-cost",
      "modes": ["generic-agent", "handoff"]
    },
    {
      "route_id": "gemini-low",
      "provider_family": "google-gemini",
      "provider_id": "configured-gemini-runner",
      "model_id": "configured-low-cost-model",
      "tier": "low-cost",
      "modes": ["generic-agent", "handoff"]
    },
    {
      "route_id": "local-low",
      "provider_family": "local-self-hosted",
      "provider_id": "configured-local-runner",
      "model_id": "configured-local-model",
      "tier": "low-cost",
      "modes": ["generic-agent", "handoff"]
    },
    {
      "route_id": "other-low",
      "provider_family": "other",
      "provider_id": "configured-other-runner",
      "model_id": "configured-low-cost-model",
      "tier": "low-cost",
      "modes": ["generic-agent", "handoff"]
    },
    {
      "route_id": "capability-review",
      "provider_family": "other",
      "provider_id": "configured-capability-runner",
      "model_id": "configured-capability-model",
      "tier": "capability",
      "modes": ["generic-agent", "handoff"]
    }
  ],
  "mode_defaults": {
    "generic-agent": "local-low",
    "handoff": "other-low"
  },
  "escalation_rules": [
    {
      "rule_id": "capability-on-review-risk",
      "signals": ["high-severity-review", "repeated-failure"],
      "target_route_id": "capability-review",
      "modes": ["generic-agent", "handoff"],
      "from_tiers": ["low-cost", "balanced"],
      "priority": 10
    }
  ]
}
```

Select runner metadata without calling a provider:

```python
import json
from pathlib import Path

from llm_wiki_cli.api import (
    DocumentationModelOverride,
    DocumentationModelRoutingPolicy,
    DocumentationModelRoutingRequest,
    select_documentation_model,
)

policy = DocumentationModelRoutingPolicy.from_dict(
    json.loads(Path("model-routing.json").read_text(encoding="utf-8"))
)

routine = select_documentation_model(
    policy,
    DocumentationModelRoutingRequest(mode="generic-agent"),
)
assert routine.tier == "low-cost"

review = select_documentation_model(
    policy,
    DocumentationModelRoutingRequest(
        mode="handoff",
        signals=("high-severity-review",),
    ),
)

explicit = select_documentation_model(
    policy,
    DocumentationModelRoutingRequest(
        mode="handoff",
        override=DocumentationModelOverride(route_id="anthropic-low"),
    ),
)
```

The selection contains public route/provider/model labels, the tier, decision
basis, matched rule, and policy hash. It cannot carry credentials. The host
uses that metadata to invoke its configured runner and keeps the selection
separate from the provider-neutral agent packet. There is no `docs` CLI flag
that invokes a provider.

## Verify, export, and hand off

Inspect status at any time without requiring target agent configuration:

```bash
llm-wiki docs status --workspace ./project-docs --format json
```

After the review result is recorded, export the user profile:

```bash
llm-wiki docs export \
  --workspace ./project-docs \
  --format mkdocs \
  --file-friendly \
  --output-format json
```

`--format` and `--file-friendly` assert the distribution and link mode selected
during `docs prepare`; they do not silently change the prepared contract. An
export without `--build` still checks the derived Markdown mirror and writes a
final report, but records `built_site_not_verified` and remains a local artifact
with limitations.

Authorize an already-installed default MkDocs builder with:

```bash
llm-wiki docs export \
  --workspace ./project-docs \
  --format mkdocs \
  --file-friendly \
  --build \
  --output-format json
```

For a custom builder, pass argv directly without a shell. The command must be
the final CLI option and must produce `<workspace>/_site`:

```bash
llm-wiki docs export \
  --workspace ./project-docs \
  --build \
  --output-format json \
  --builder-command mkdocs build --strict -f site/mkdocs.yml
```

The CLI never installs the builder. A missing builder, failed build, missing
`_site`, broken links/media, unresolved high-severity findings, or integrity
failure stays visible in evidence and the final verdict.

An explicitly authorized build first safety-checks and removes only the prior
derived `<workspace>/_site`, then requires the builder invocation to recreate a
safe, non-empty tree containing HTML. This prevents a zero-exit no-op from
reusing stale output while allowing a deterministic rebuild whose bytes match
the previous artifact. A failed current build never inherits an earlier
`publish_ready` verdict.

Builder stdout and stderr are spooled to temporary files under the
supervisor-owned evidence directory. Reports retain only the final 10,000 bytes
of each stream and record total-byte and truncation metadata. This keeps a noisy
authorized builder from turning diagnostic capture into unbounded process
memory while preserving a useful error tail.

Run deterministic verification explicitly when diagnosing or rechecking a
workspace:

```bash
llm-wiki docs verify --workspace ./project-docs --format json
llm-wiki docs verify --workspace ./project-docs --format json --no-advance
```

`verify` exits nonzero when required evidence is missing or a check fails.
`--no-advance` reports the result without advancing an eligible review run.
Remote deployment is always a separate, explicitly authorized workflow.

## Python lifecycle API

The supported API mirrors the CLI without `argparse`, console scraping, or
`SystemExit`:

```python
import json
from pathlib import Path

from llm_wiki_cli.api import (
    DocumentationAgentResult,
    build_documentation_agent_packet,
    export_documentation_run,
    get_documentation_run_status,
    prepare_documentation_run,
    record_documentation_agent_result,
    verify_documentation_run,
)

workspace = Path("project-docs")
run = prepare_documentation_run(
    workspace,
    baseline_strategy="bootstrap_source",
    source_root="/path/to/project",
    site_name="Project",
    audiences=("user", "operator"),
    project_purpose="Help people install and operate Project.",
    audience_intent={
        "user": "install and complete the first task",
        "operator": "operate and troubleshoot safely",
    },
    helper_cache_root="/tmp/llm-wiki-helpers",
    distribution_format="mkdocs",
    link_mode="file",
)

packet = build_documentation_agent_packet(
    workspace,
    stage="wiki-enrichment",
)
Path("wiki-enrichment-packet.md").write_text(
    packet.to_markdown(), encoding="utf-8"
)

# A host runs an external agent and obtains the versioned JSON result.
result = DocumentationAgentResult.from_dict(
    json.loads(Path("wiki-enrichment-result.json").read_text(encoding="utf-8"))
)
record_documentation_agent_result(workspace, result)

status = get_documentation_run_status(workspace)

# Repeat the packet/result exchange for user-docs and review before export.
final_report = export_documentation_run(workspace, build=False)
verification = verify_documentation_run(workspace, advance=False)
```

The protected calibration lifecycle is also available through the same module:

```python
from llm_wiki_cli.api import (
    HostBrokerAuthenticator,
    P0CalibrationAgentResult,
    P0CalibrationDispatchReceipt,
    admit_calibration_run,
    build_calibration_agent_packet,
    dispatch_calibration_agent,
    get_calibration_run_status,
    prepare_calibration_run,
    record_calibration_agent_result,
    use_calibration_host_broker_authenticator,
    verify_calibration_run,
)

calibration_root = Path("/path/to/operator-calibration/controller")
calibration = prepare_calibration_run(
    calibration_root,
    control_workspaces=(
        "/path/to/operator-calibration/control-a",
        "/path/to/operator-calibration/control-b",
    ),
    execution_manifest=execution_manifest,
)
calibration = admit_calibration_run(
    calibration_root,
    authority_grant=authority_grant,
)
packet = build_calibration_agent_packet(
    calibration_root,
    role="intake-a",
)
status = get_calibration_run_status(calibration_root)
```

For the local profile, call `dispatch_calibration_agent`; for an
independently authenticated external broker, construct the versioned
`P0CalibrationDispatchReceipt` and `P0CalibrationAgentResult` types before
calling `record_calibration_agent_result`. Use
`verify_calibration_run(..., advance=False)` for a read-only eligibility
report.

An embedding host supplies an object implementing `HostBrokerAuthenticator`
only after authenticating the external broker through its own protected
mechanism. Scope admission and receipt imports explicitly:

```python
with use_calibration_host_broker_authenticator(authenticated_host_broker):
    admitted = admit_calibration_run(
        calibration_root,
        authority_grant=authority_grant,
        broker_attestation=broker_attestation,
    )
    record_calibration_agent_result(
        calibration_root,
        dispatch_receipt=dispatch_receipt,
        result=agent_result,
    )
```

The context is process-local, does not dynamically load code, and persists
only bounded secret-free proofs. The stock CLI remains fail-closed unless an
embedding host invokes it inside the same authenticated context.

For existing-wiki adoption, use:

```python
run = prepare_documentation_run(
    "project-docs",
    baseline_strategy="adopt_existing_wiki",
    input_wiki_root="/path/to/project/docs/llm_wiki",
    source_root="/path/to/project",
    freshness_policy="require-current",
    site_name="Project",
    audiences=("user",),
)
```

The lower-level `adopt_documentation_wiki_snapshot(...)` typed API is also
exported for integrations that need only a validated, byte-preserving snapshot.
The supported API also exports the lifecycle protocol constants
`DOCUMENTATION_RUN_SCHEMA_VERSION`,
`DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION`,
`DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION`,
`DOCUMENTATION_VERIFICATION_SCHEMA_VERSION`, and
`DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION`, so hosts do not need to duplicate
version strings when accepting packets, results, verification evidence, or the
final report.
Lifecycle failures use typed `DocumentationRunError`,
`DocumentationSchemaError`, `DocumentationTransitionError`, and
`DocumentationIntegrityError` exceptions. Preparation may also surface
`DocumentationPolicyError`, `BootstrapServiceError`, or
`DocumentationWikiInputError` from its deterministic policy, bootstrap, and
import boundaries. Model selection uses `DocumentationModelPolicyError`. These
public base errors are exported from `llm_wiki_cli.api`.

## Resume and troubleshooting

Repeated `docs prepare` with the same workspace and unchanged contract is
idempotent. Resume compatibility covers the baseline strategy, source/input,
helper-cache and capture roots, source-plugin trust decision, intake, freshness
policy, site name, distribution/link mode, semantic budget, adjustment-loop
limit, and source/input evidence. It reuses the recorded intake and run rather
than asking questions or rebuilding. A changed contract is rejected and
requires explicit `--refresh` or a new workspace; repeated preparation never
silently changes the recorded run.

Before an apparently compatible resume compares live source/input state, the
supervisor binds the portable policy to the current runtime paths and verifies
the recorded initial integrity anchors. Replacing a baseline evidence file
cannot therefore legitimize a changed source or input tree.

During an initial prepare, a same-process failure rolls back only lifecycle-owned
artifacts and preserves an initially empty workspace. Abrupt process loss
(`SIGKILL`, host crash, or power loss) cannot authenticate a safe destructive
cleanup boundary. Inspect that workspace before reuse; prefer a new workspace
when ownership is uncertain.

Use this recovery sequence:

1. Run `docs status --format json` and inspect `state`, `current_stage`,
   `next_actions`, and `limitations`.
2. Read `.llm-wiki-docs/run.json` and the named evidence/result files.
3. Correct only the owned workspace content or agent result indicated by the
   failed gate.
4. Build a new packet for the recorded resume stage and continue.
5. Use `--refresh` or a new workspace only when the source/input or run contract
   intentionally changed.

Common conditions:

- **Missing extractor helper:** stop, run `prepare-extractors` explicitly, then
  prepare again with `--helper-cache-dir`. The docs command does not install or
  build a helper implicitly.
- **Source changed since prepare:** the integrity check refuses resume. Review
  the change, then use explicit `--refresh` or create a new workspace.
- **Input wiki changed since import:** re-import with explicit `--refresh` or
  use a new workspace. The old snapshot remains evidence.
- **Input wiki exceeds an adoption limit:** split or trim the wiki/assets before
  adoption. The snapshot and secure resume fingerprint use identical fixed
  entry, file, byte, and depth limits; they never copy a partial oversized
  input.
- **Freshness cannot be proved:** use `require-current` with matching source,
  `refresh-snapshot` with source for a workspace-only refresh, or knowingly
  accept the visible `allow-unverified` limitation.
- **Changed-path mismatch/generated edit:** fix or revert the workspace edit and
  return an accurate result. Never alter source, the input wiki, a generated
  `.llm-wiki-manifest.json`, `.llm-wiki-surface.json`,
  `.llm-wiki-knowledge.json`, or CLI-owned generated Markdown sections.
- **Run is blocked:** resolve the recorded finding; a blocked run resumes only
  at its recorded stage.
- **Review loop exhausted:** unresolved or repeated high-severity findings stay
  blocked. Increase work only through a deliberate new/refresh decision, not by
  erasing the ledger.
- **No built-site proof:** install/select a trusted builder outside the run and
  rerun export with `--build`, or keep the honest local-artifact limitation.
  The explicit rebuild replaces the lifecycle-owned derived `_site`; a no-op or
  marker-only command cannot qualify stale output.
- **No source:** wiki-only work can still produce a checked local mirror under
  `allow-unverified`, but not a source-verified publication claim.

Dirty source repositories and repositories without Git are supported: the run
uses content fingerprints and before/after tree checks rather than requiring a
clean Git worktree. Source and input integrity remain mandatory regardless of
Git availability.
