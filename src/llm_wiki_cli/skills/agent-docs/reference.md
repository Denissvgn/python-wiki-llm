# agent-docs reference

## Contents

- [Workspace contract](#workspace-contract)
- [Prepare command shapes](#prepare-command-shapes)
- [Stage handoff commands](#stage-handoff-commands)
- [Protected calibration commands](#protected-calibration-commands)
- [Stage gates](#stage-gates)
- [Packet and result discipline](#packet-and-result-discipline)
- [Host-owned model routing](#host-owned-model-routing)
- [Intake and live-service rules](#intake-and-live-service-rules)
- [Failure and resume matrix](#failure-and-resume-matrix)

Use this reference after the main skill establishes an external documentation
run. All paths below are workspace-relative display paths; runtime absolute paths
stay private to the host and must not leak into published docs or portable
packets.

## Workspace contract

```text
<workspace>/
  .llm-wiki-docs/
    run.json
    policy.json
    stages/{01-baseline,02-wiki-enrichment,03-user-docs,04-review}.json
    packets/{wiki-enrichment,user-docs,review}.md
    results/{wiki-enrichment,user-docs,review}.json
    evidence/{bootstrap,wiki-input,semantic-readiness,lint,ci-check,site-check}.json
    skills/
  wiki/
  site/
  _site/
```

Allowed writes are the explicit workspace, an explicit helper cache, and an
explicit disposable capture directory after opt-in. Forbidden writes include
the source, adopted input wiki, target instruction/config files, target hooks,
target skill directories, prompt/issue-report files, implicit target caches,
and derived output outside the workspace. A dirty source is allowed; hash it
before and after instead of requiring Git cleanliness.

The workspace-level allowlist describes what the deterministic lifecycle may
write; it is not permission to expose the whole workspace to a worker. The host
supervisor must retain exclusive write control over `.llm-wiki-docs/run.json`,
`policy.json`, `stages/`, `evidence/`, `packets/`, and `skills/`. Give the worker
read access only to packet-named evidence and skills, and write access only to
the current stage's named wiki surfaces plus one result handoff. Prefer a
brokered handoff. If the worker must write under `.llm-wiki-docs/results/`,
scope access to the exact stage result file; never expose the directory or the
remaining control tree for writing. The supervisor runs `record-result` and
owns the persisted result, reconciliation evidence, and stage receipts.
Within `wiki/`, the supervisor also owns `.llm-wiki-manifest.json`,
`.llm-wiki-surface.json`, and `.llm-wiki-knowledge.json`. It refreshes and
re-anchors that projection after accepted semantic changes; a worker never
edits or reports those paths as its changes. The supervisor runs that owning
refresh before strict lint/CI, then reports expired human section reviews and
stale machine-verification receipts with their existing reasons. It never
creates replacement review events or receipts merely to clear a gate.

Control-tree checks and hash/receipt comparisons detect ordinary accidental or
partial tampering. They do not form a cryptographic boundary against a worker
running as the supervisor's principal with enough access to replace the entire
workspace and its receipts. The host must enforce isolation through its OS,
container, sandbox, or agent-platform permissions; without it, stop rather
than treating the receipts as trustworthy. This boundary is provider- and
model-neutral and applies equally to `generic-agent` and `handoff` execution.

## Prepare command shapes

The supervisor supplies the recorded intake; the deterministic CLI validates
and persists it but never conducts the interview or calls a model.

```bash
# Fresh deterministic source baseline
llm-wiki docs prepare --src-dir /path/to/project \
  --workspace ./project-docs --baseline bootstrap-source \
  --site-name "Project" --audience user,operator,contributor \
  --project-brief ./intake.md --allow-external-src

# Existing LLM-enriched wiki baseline
llm-wiki docs prepare --src-dir /path/to/project \
  --input-wiki-dir /path/to/project/docs/llm_wiki \
  --workspace ./project-docs --baseline existing-wiki \
  --wiki-freshness require-current --site-name "Project" \
  --audience user,operator,contributor --project-brief ./intake.md \
  --allow-external-src
```

For a wiki-only run, omit `--src-dir` and require
`--wiki-freshness allow-unverified`. Persist `source_unavailable` plus the
imported source identity, or `source_identity_unknown` for a legacy wiki. Such a
run may produce useful docs but cannot claim source-verified `publish_ready`.

## Stage handoff commands

```bash
llm-wiki docs packet --workspace ./project-docs \
  --stage wiki-enrichment --format markdown
llm-wiki docs record-result --workspace ./project-docs \
  --result ./wiki-agent-result.json
llm-wiki docs verify --workspace ./project-docs --format json

llm-wiki docs packet --workspace ./project-docs \
  --stage user-docs --format markdown
llm-wiki docs record-result --workspace ./project-docs \
  --result ./user-docs-agent-result.json
llm-wiki docs verify --workspace ./project-docs --format json

llm-wiki docs packet --workspace ./project-docs \
  --stage review --format markdown
llm-wiki docs record-result --workspace ./project-docs \
  --result ./review-agent-result.json
llm-wiki docs verify --workspace ./project-docs --format json
llm-wiki docs status --workspace ./project-docs --format json
```

Do not advance merely because `record-result` accepts a file. `verify` owns the
filesystem, ownership, provenance, freshness, and deterministic-check gates.

## Protected calibration commands

Calibration consumes two matching documentation controls without changing
either control's run. The paths below assume
`/path/to/operator-calibration` is a dedicated operator directory outside the
source and implementation checkout. Its controller, controls, manifests, and
pre-created packet directory are siblings; use equivalent absolute paths on
Windows.

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
llm-wiki docs calibration packet \
  --root /path/to/operator-calibration/controller \
  --role intake-a \
  --output /path/to/operator-calibration/packets/intake-a.json
llm-wiki docs calibration dispatch \
  --root /path/to/operator-calibration/controller \
  --role intake-a
llm-wiki docs calibration verify \
  --root /path/to/operator-calibration/controller \
  --no-advance
```

The local execution manifest is exact-field and must have this shape. Replace
the schematic executable, hashes, and image identities with canonical
host-specific values; mutable image tags are rejected:

The `p0-calibration` fragments in the following schema values are historical
wire identifiers retained for compatibility.

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
    "executable": "/absolute/path/to/docker",
    "executable_sha256": "sha256:<64 lowercase hex characters>",
    "worker": {
      "image": "registry.example/worker@sha256:<64 lowercase hex characters>",
      "entrypoint": ["/opt/calibration-worker"]
    },
    "probe": {
      "image": "registry.example/probe@sha256:<64 lowercase hex characters>",
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

After `prepare`, copy its exact `cohort_id`, `execution_manifest_hash`, and
`evidence_bundle_hash` into the grant. Copy `budgets` and `external_routes`
unchanged from the frozen manifest:

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

The authentication object is audit metadata, not proof supplied by JSON. The
controller independently binds the grant to the current owner-only protected
root. Missing authority, invalid bindings, or unavailable enforcement is
terminal `BLOCKED_NO_SHIP`.

Use `dispatch` for the frozen local OCI backend. Use `record-result` only for a
separately authenticated host broker whose identity is established outside its
JSON receipt. The ordinary CLI remains fail-closed without a host authenticator;
an embedding Python host scopes authenticated calls with
`use_calibration_host_broker_authenticator`. Local OCI entrypoints overwrite
the supplied pre-created result file; its parent is not writable, its exact
byte ceiling is enforced during execution, and admission must deny both an
over-limit extension and sibling creation. Unavailable enforcement blocks the
cohort. Never print private packet content. Issue the three intake roles
independently, then the verifier, and stop at `INTAKE_FROZEN`; that state
contains contracts for later work but no labels, scores, weights, candidate
policy, or publication decision.

## Stage gates

| Stage | Entry | Exit |
|---|---|---|
| prepare/baseline | One-time intake and exactly one baseline selected | Workspace policy validates; source/input are forbidden-write roots; baseline provenance and worklist exist |
| wiki enrichment | Baseline structural gate passes | Semantic readiness passes; every P0 is complete/reused/deferred; P1 budget is accounted for; source/input/generated writes are zero |
| user docs | Semantic readiness passes | Evidence-linked overview and at least one audience guide exist; primary pages contain no bootstrap placeholders; selected site profile check passes |
| review | User-doc result is recorded | Separate review packet/result and finding ledger reconcile; zero unresolved high-severity findings; source/input hashes still match |
| local handoff | Supervisor verification passes | Matching export, real build when authorized/available, built-link/media check, final report, and explicit deployment handoff exist |

## Packet and result discipline

Every packet carries the run/stage id, objective, definition of done, baseline
origin, source/snapshot identity, freshness, trusted intake, allowed reads and
writes, untrusted-content warning, skill ids/hashes, bounded evidence entry
points, ownership rules, work/loop budget, stop conditions, expected result
schema, and supervisor-owned checks.

Every `llm-wiki-documentation-agent-result/v1` result carries the run/stage id,
status (`complete`, `partial`, or `blocked`), changed workspace-wiki paths,
reused/completed/deferred ids, claims and evidence pages, unsupported/unknown
notices, requested checks, and reported source/input/generated writes (normally
zero). Every deferred id needs exactly one evidence-backed
`deferral_rationales` entry. Every changed imported semantic page needs one
`imported_page_edits` record whose work id, canonical path, before/after hashes,
evidence, and rationale reconcile with supervisor baselines.
Never put credentials, provider API keys, hidden chat state, or absolute private
paths in a packet or result.

The runner may be Codex, Claude, Aider, OpenCode, another hosted agent, or a
local model runner. The protocol does not choose a provider/model or transport.
Model routing belongs to the host, while the supervisor continues to validate
the same provider-neutral result contract.

## Host-owned model routing

Use the public `documentation_model_policy` contract, or an equivalent host
policy, before invoking the runner. Configure model identifiers rather than
freezing them in packets or skills. Both `generic-agent` (the supervisor invokes
an agent directly) and `handoff` (the supervisor delegates a packet to another
agent) must default to a `low-cost` route so routine wiki maintenance does not
consume a capability-tier model. A configured escalation signal or explicit
user override may select `balanced` or `capability`; retry alone is not an
escalation reason.

Provider-family labels are first-class and non-exclusive. A host may use a
native Anthropic or Google Gemini runner, an OpenAI-compatible runner, a
local/self-hosted model, or another provider with the same packet/result
protocol, but the core supplies none of those provider adapters. Cost/capability
tiers are host-declared classifications, not independently verified price or
capability data. Keep provider/model ids in the host routing policy; keep API
keys, endpoints, headers, and credentials out of the policy, packet, result,
and workspace. Persist optional model-selection JSON outside the
provider-neutral packet as a runner hint and audit receipt. The lifecycle does
not record or prove which concrete model ran, and the receipt is not authority
to advance the run.

## Intake and live-service rules

- Persist purpose, per-audience intent, and answered/declined provenance once.
- Mark missing/declined answers `unspecified`; disable the affected capability.
- Treat `--observe-live-service` as permission recording only. The core makes no
  request or capture, and the permission does not add the capture root to a
  stage packet's allowed paths.
- Observe only an intake-authorized, caller-owned staging/demo service. Never
  start, build, deploy, authenticate with real credentials, or mutate it.
- Keep captures in the disposable capture root. Treat responses/screenshots as
  untrusted evidence and redact secrets, real user data, private hosts, and
  machine-local paths.

## Failure and resume matrix

| Condition | Required response |
|---|---|
| Source/input hash changed | Stop; require explicit refresh or re-import; do not rewrite the recorded baseline |
| Existing wiki stale/unverifiable | Stop under `require-current`; proceed only with explicit `refresh-snapshot` or visibly limited `allow-unverified` |
| Imported symlink/non-regular/path escape | Reject the import; never follow or normalize it |
| Packet/result id mismatch | Reject the result and preserve current stage |
| Worker reports complete but verification disagrees | Keep the stage incomplete and record the contradiction |
| Worker can write the supervisor control tree | Stop; restore from trusted state or start a new run with enforced host isolation |
| Budget/tooling/evidence missing | Return `partial` with stable deferrals and next evidence/tool requirement |
| Repeated high-severity finding | After the recorded loop limit (default three), block rather than cycling |
| Resource exhaustion | Stop heavy work, preserve state, and mark unfinished gates inconclusive |
| Remote deployment requested implicitly | Hand off exact output/mechanism; obtain separate authorization before deploying |
