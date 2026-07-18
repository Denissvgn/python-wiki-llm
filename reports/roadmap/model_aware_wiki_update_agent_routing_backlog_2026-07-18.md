# Model-Aware Wiki Update Agent Routing Backlog

> For implementation agents: execute this backlog in dependency order. Keep
> deterministic extraction, synchronization, and validation separate from LLM
> routing. Update task status and evidence in this file as work lands. Preserve
> unrelated worktree changes and make scoped commits unless the user requests a
> different commit strategy.

**Goal:** Route routine LLM Wiki page maintenance to a bounded, lower-cost
worker while reserving the more capable supervising model for work selection,
ambiguous reasoning, escalation, and final reconciliation. Apply the policy to
both generated generic-agent guidance and prompt/CLI handoff workflows without
coupling the core package to one provider.

**Architecture:** Add a provider-neutral `wiki_update_economy` routing profile.
Generated instructions and handoff packets request that profile; a supported
runner adapter or an external generic-agent host resolves it to a concrete
model. The supervisor owns and approves the work envelope, heavy-gate schedule,
escalation decision, and final evidence. An economy runner cannot launch without
that approved bounded packet. The worker may edit only named semantic wiki
surfaces, never stages or commits, and returns a semantic result. The
controller/supervisor separately records routing evidence and validates the
filesystem delta before any human/supervisor commit.

**Current multi-provider recommendation (2026-07-18):** choose a qualified
economy binding from the operator's available provider: Codex
`gpt-5.6-terra`, Anthropic Claude Haiku 4.5, Google Gemini 3.1 Flash-Lite,
Mistral Small 4, DeepSeek V4 Flash, or Alibaba Qwen 3.6 Flash are candidate
starting points. Corresponding capable routes remain available for bounded
escalation. Section 1.3 records exact example IDs and official evidence. No
provider is the normative default, and native Anthropic, Gemini, Mistral,
DeepSeek, and Qwen transports must not be forced through an OpenAI-compatible
API when their runner supports a native path.

**Compatibility target:** Python 3.9+, Windows, macOS, and Ubuntu. The current
package metadata and CI baseline are Python 3.10+, so MWR-000 and MWR-010 must
reconcile that existing mismatch before this feature can claim Python 3.9
qualification.

**Tech stack:** argparse CLI, JSON local configuration, subprocess
runner adapters, generated Markdown instructions, bundled skills, JSONL
observability, pytest, Ruff.

---

- Date: 2026-07-18
- Status: Proposed; not implemented
- Owner: Unassigned
- Related plan: [Agent-Driven Standalone Documentation Implementation Plan](agent_driven_standalone_documentation_implementation_plan_2026-07-14.md)
- Compatibility decision: additive and opt-in first; existing initialized
  repositories and handoff commands keep their current runner defaults until
  an operator configures or accepts model-aware routing

**Current shipment boundary:** The standalone documentation implementation can
select credential-free, host-owned model-policy labels, but it does not ship a
provider-native transport, invoke any catalog model, verify current price or
capability, or write an authoritative execution receipt. The concrete bindings,
native/provider-specific runner adapters, effective-model attestation, and
routing receipts in this backlog remain proposed work under MWR-001, MWR-006,
MWR-008, and MWR-010. A configured `provider_family`, tier, endpoint protocol,
or model string is metadata—not proof that a provider, transport, or model was
actually used.

## 1. Product Decision

Use a capability route with a replaceable concrete model binding.

The durable contract is **not** "always use the cheapest model." Price,
availability, context limits, tool support, and model names change. A model
that cannot inspect the repository, use tools safely, preserve generated
surfaces, or report uncertainty is not economical if the supervisor must redo
all of its work.

The selected hierarchy is:

1. deterministic LLM Wiki commands collect evidence and own generated content;
2. a capable supervisor chooses and bounds semantic page work;
3. an economy worker performs routine edits inside that envelope;
4. deterministic validation checks the result;
5. the supervisor reconciles evidence and escalates only when a declared
   trigger fires.

The supervisor should review a compact result packet and targeted diff, not
repeat the entire editing pass. That preserves the intended model and token
savings.

### 1.1 Required capability floor for an economy worker

The concrete model bound to `wiki_update_economy` must be able to:

- read repository diffs, source evidence, wiki manifests, and Markdown pages;
- use the host's file and command tools without shell interpolation;
- distinguish agent-owned semantic prose from CLI-owned generated blocks;
- make narrow multi-file edits while preserving paths and links;
- follow a bounded work packet and return a structured result;
- state uncertainty and stop instead of inventing unsupported claims;
- handle the packet's context size without silent truncation.

Cost is a selection criterion only after this capability floor is met.

### 1.2 Model naming policy

- Generated, portable instruction files name `wiki_update_economy`, not a
  provider model ID.
- The local routing configuration binds the profile to a named
  runner/backend/publisher/model tuple and optional effort/budget controls.
- Documentation shows date-stamped examples from multiple providers, including
  both native non-OpenAI transports and gateway/local backends.
- Metrics and handoff receipts record the actual resolved model when the host
  can prove it.
- If generic mode cannot select or observe a worker model, it reports routing
  as `unverified`; it must not claim that the cost policy was applied.

### 1.3 Date-stamped multi-provider candidate catalog

The following candidates are operator-facing starting points, verified against
official provider documentation on 2026-07-18. They are not compiled runtime
defaults. Each must pass the wiki-update qualification suite through the exact
runner/backend combination before it can become a selected binding. Prices are
provider list-price snapshots per one million tokens and are evidence of model
positioning, not a promise or an automatic cross-provider ranking.

| Model publisher | Economy candidate | Capable escalation | Official evidence and important constraints |
| --- | --- | --- | --- |
| OpenAI/Codex host | `gpt-5.6-terra` (low effort for mechanical refresh; medium for bounded synthesis); evaluate `gpt-5.6-luna` for high-volume, tightly mechanical packets | `gpt-5.6-sol` or current capable supervisor | [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model); host availability and pricing are deployment-specific |
| Anthropic | Pinned `claude-haiku-4-5-20251001` (`claude-haiku-4-5` alias), $1 input / $5 output | `claude-sonnet-5`; exceptional `claude-opus-4-8` | [Anthropic models](https://platform.claude.com/docs/en/about-claude/models/overview) and [tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview); backend-specific IDs differ for Bedrock and Vertex |
| Google | Stable `gemini-3.1-flash-lite`, $0.25 input / $1.50 output | Stable `gemini-3.5-flash`; preview Pro requires explicit opt-in | [Flash-Lite model and capabilities](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite) and [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing); avoid hot-swapped `*-latest` aliases for reproducible bindings |
| Mistral | Pinned `mistral-small-2603`, $0.15 input / $0.60 output | `mistral-medium-3-5`, $1.50 / $7.50 | [Mistral Small 4](https://docs.mistral.ai/models/model-cards/mistral-small-4-0-26-03) and [model catalog](https://docs.mistral.ai/models/overview); do not introduce retired Devstral aliases |
| DeepSeek | `deepseek-v4-flash`, $0.14 cache-miss input / $0.28 output | `deepseek-v4-pro`, $0.435 / $0.87 | [DeepSeek models and pricing](https://api-docs.deepseek.com/quick_start/pricing/) and [V4 agent capabilities](https://api-docs.deepseek.com/news/news260424/); do not add `deepseek-chat` or `deepseek-reasoner`, which retire 2026-07-24 |
| Alibaba/Qwen | Pinned `qwen3.6-flash-2026-04-16`; use `qwen3-coder-next` for code-heavy evidence work | Pinned `qwen3.7-plus-2026-05-26` | [Qwen models](https://www.alibabacloud.com/help/en/model-studio/text-generation-model), [Qwen Coder](https://www.alibabacloud.com/help/en/model-studio/qwen-coder), and [pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing); availability and price require deployment region/scope |
| Local/self-hosted | No universal default: qualify an open-weight model such as `mistral-small-2603`, `qwen3-coder-next`, or `gpt-oss-20b` on the operator's exact Ollama, LM Studio, vLLM, or other runtime | Hosted or larger local `wiki_update_capable` binding selected explicitly | Record hardware, quantization, context limit, tool/edit support, latency, energy/hosting proxy, model hash, and license; an OpenAI-compatible local endpoint is only a transport, not the provider-neutral contract |

Supported transport classes must include:

- provider-native Anthropic/Claude and Google Gemini paths;
- provider-native or runner-supported Mistral, DeepSeek, and Alibaba Model
  Studio paths;
- OpenAI-native and explicit OpenAI-compatible gateway/backend paths, while
  preserving the underlying model publisher and never treating protocol
  compatibility as provider identity;
- cloud backends such as Amazon Bedrock, Google Vertex AI, and Microsoft
  Foundry where the selected runner supports them;
- explicit gateways such as OpenRouter, recording both gateway and underlying
  model publisher;
- operator-qualified local backends such as Ollama or LM Studio.

Gateway and local support does not make an OpenAI-compatible protocol the core
contract. The binding records its actual endpoint protocol. Cross-provider or
cross-backend fallback is disabled unless the operator explicitly declares and
audits an ordered fallback policy.

### 1.4 Capability and cost profiles

Profiles express task intent and qualification, not a vendor ranking:

| Profile | Intended use | Selection rule | Escalation behavior |
| --- | --- | --- | --- |
| `wiki_update_economy` | Bounded, routine semantic refresh in generic-agent and packet handoff modes | Choose the lowest-cost locally available binding that passes the capability floor, packet-size limit, tool/edit contract, and current qualification suite | Stop after the configured economy attempt cap; do not silently spend on a capable route |
| `wiki_update_capable` | Ambiguous architecture, conflicting evidence, security/API/migration claims, or an explicitly approved escalation subset | Choose a qualified higher-capability binding under an explicit budget/effort cap | Return to the supervisor after one bounded attempt; no recursive escalation |
| Supervisor route | Work selection, packet approval, deterministic-gate ownership, final reconciliation, and publication judgment | Keep the host's explicitly selected capable model; it is not a worker default and is never inferred from an economy failure | Supervisor decides stop versus the single allowed capable escalation |

Each concrete binding records a relative profile plus dated capability and cost
evidence. Hosted cost evidence includes currency, input/output units, cache and
thinking-token treatment, region/gateway markup, source URL, and `verified_at`.
Local cost evidence uses predeclared hardware/time/energy or hosting proxies and
must not pretend to be comparable list-price token billing. Stale or missing
cost evidence prevents an automatic recommendation but does not invalidate a
manually selected, capability-qualified binding.

## 2. Verified Current Baseline

| Surface | Current behavior | Gap |
| --- | --- | --- |
| Generic schema | `init --agent generic` renders `AGENTS.md` from shared wiki instructions | No lower-cost worker route, concrete-model lookup, result packet, or escalation contract |
| Bundled `wiki-sync` skill | Defines deterministic sync, semantic edits, lint, and separate commit ownership | No economy-worker delegation or supervisor reconciliation contract |
| Prompt handoff | Hooks and `generate-prompt` produce a prompt for human/agent review | Prompt values carry no requested profile, model, policy, or routing receipt fields |
| CLI handoff | `trigger-agent` invokes Claude, Aider, or OpenCode with fixed argv | No model/profile flag; runner defaults choose the model implicitly |
| Trigger outcome | Agent subprocess failures are observed internally | Some timeout, execution, and nonzero cases can return normally to the CLI, preventing reliable escalation |
| Local config | `.git/.llm-wiki-agent` persists agent and instruction preferences | No versioned routing block; `init`/`upgrade` would currently discard unknown experimental keys |
| Team config | Strict agent policy schema supports prompt templates, lint rules, and skills | No shared abstract routing policy; concrete provider IDs do not belong in the first portable contract |
| Metrics | JSONL events include agent, mode, duration, exit code, and breaker state | No requested/resolved model, resolution source, attempt, override, or escalation reason |
| Standalone documentation plan | Defines runner-neutral packets/results and defers provider-specific runners | Executed handoffs do not yet require an auditable resolved route/model |
| Python support | Repository instructions require Python 3.9+, while package metadata and the current CI matrix start at Python 3.10 | Compatibility target and executable qualification evidence disagree |

Primary implementation touch points:

- `src/llm_wiki_cli/services/schema.py`
- `src/llm_wiki_cli/skills/wiki-sync/SKILL.md`
- `src/llm_wiki_cli/skills/wiki-sync/reference.md`
- `src/llm_wiki_cli/config.py`
- `src/llm_wiki_cli/commands/init_cmd.py`
- `src/llm_wiki_cli/commands/upgrade_cmd.py`
- `src/llm_wiki_cli/commands/status_cmd.py`
- `src/llm_wiki_cli/commands/generate_prompt_cmd.py`
- `src/llm_wiki_cli/commands/trigger_cmd.py`
- `src/llm_wiki_cli/services/metrics.py`
- `src/llm_wiki_cli/cli.py`
- `README.md`

## 3. Scope

### 3.1 Generic agent mode

For `init --agent generic`, the generated `AGENTS.md` will tell the capable
supervisor to request `wiki_update_economy` for bounded routine page work. The
detailed envelope, edit boundaries, result schema, and escalation rules live in
the bundled `wiki-sync` skill/reference so the generated schema stays concise.

Generic mode is guidance, not an execution engine. The host is responsible for
mapping the route and creating the worker. When the host cannot choose a model,
the supervisor may complete the existing workflow itself, but must describe the
route as unavailable or unverified rather than pretending delegation occurred.

### 3.2 Prompt-only handoff mode

`generate-prompt` and hook-created prompts will include:

- requested routing profile and routing policy;
- candidate binding IDs plus backend/publisher/model recommendations only when
  supplied by local configuration;
- the bounded page/evidence envelope;
- allowed and forbidden surfaces;
- required result fields and escalation conditions.

Hooks remain prompt-only and must not begin spending or invoke an agent.

### 3.3 CLI runner handoff mode

`trigger-agent` will resolve a requested profile or explicit binding before
launch. When routing is enabled, it must consume a supervisor-approved,
versioned packet; the current unconstrained prompt path remains legacy-only
until such a packet exists. Per-runner adapters translate the resolved model
into validated argv. The controller writes an authoritative local result
receipt, propagates failed outcomes as nonzero CLI exits, runs post-worker
reconciliation, and records routing evidence in best-effort metrics. It never
stages, commits, stashes, resets, or reverts user work.

### 3.4 Standalone documentation handoffs

The locally implemented standalone documentation lifecycle remains
runner-neutral when it prepares work packets. Its current packet requests
`wiki_update_economy` without choosing a provider, and its host-owned model
selector emits credential-free labels outside that packet. The worker result
remains semantic-only and never attests model identity. This backlog adds the
authoritative controller/host receipt: once a runner executes the packet, that
receipt records the requested route, configured model argument, effective model
or `unverified` state, resolution source, attempt count, and escalation outcome.

## 4. Out of Scope

- Shipping a provider SDK or credentials manager in the core package.
- Automatically querying provider pricing or choosing the globally cheapest
  model at runtime.
- Hardcoding `gpt-5.6-terra`, Claude, Gemini, Mistral, DeepSeek, Qwen, or any
  vendor ID into shared generated schemas.
- Treating model selection alone as evidence of documentation quality.
- Letting an economy worker edit source code, CLI-owned generated blocks,
  manifests, generated diagrams/tables, or unrelated wiki pages.
- Allowing `--force` to bypass routing, budget, ownership, or validation rules.
- Automatic fallback to a more expensive model without explicit policy and an
  auditable escalation reason.
- Silent fallback to another provider/backend, which can change credentials,
  data-governance boundaries, residency, price, or effective model.
- Estimating cost from token counts when the runner does not return authoritative
  usage and price metadata.
- Changing hooks from prompt generation into automatic agent execution.

## 5. Alternatives Considered

| Approach | Decision | Reason |
| --- | --- | --- |
| Put one cheap model name in every `AGENTS.md` | Reject | Provider lock-in and model-name drift; repositories would need instruction churn for an operational mapping change |
| Select the cheapest available model automatically | Reject | Price alone does not prove tools, context, safe editing, or sufficient semantic quality |
| Add only `trigger-agent --model` | Insufficient alone | Helps direct runners but does not cover generic delegation, prompt handoff, policy, validation, or auditability |
| Let every runner inherit its last-used/default model | Reject as cost policy | Hidden defaults can silently select a more capable and expensive model |
| Capability profile plus local concrete binding | Select | Portable contract, explicit cost intent, provider isolation, and independently testable precedence |
| Commit concrete provider bindings in team policy in the first release | Defer | Useful for controlled teams, but it can leak vendor assumptions and is harder to migrate safely |
| Core package directly orchestrates a supervisor and workers | Defer | Larger credentials/billing/runtime commitment than needed for model-aware handoff |

## 6. Routing Contract

### 6.1 Provider and binding terminology

A portable binding must not overload the word `provider`. It records:

- `binding_id`: stable local name selected by policy or CLI;
- `route`: `wiki_update_economy`, `wiki_update_capable`, or another versioned
  capability profile the binding has passed;
- `runner`: `claude`, `aider`, `opencode`, or an external generic host;
- `execution_owner`: `controller` for a directly launched runner or
  `external_host` for guidance-only generic-host bindings; only the execution
  owner can produce the first-party routing attestation;
- `backend`: the account/endpoint that serves the request, such as direct
  Anthropic, Google AI, Bedrock, Vertex, Foundry, OpenRouter, or Ollama;
- `model_publisher`: the organization that owns the model, independently of a
  gateway/backend;
- `provider_model_id`: pinned provider-native model ID when one exists;
- `model_ref`: exact opaque string passed to the selected runner;
- `endpoint_protocol`: configured expectation such as native Anthropic, native
  Gemini, OpenAI-compatible, or `runner-managed-unverified`; it is not runtime
  proof by itself;
- `variant`: effort/thinking/budget settings supported by that exact runner;
- `deployment_scope`: region/project/account scope when it affects model
  availability, price, or data handling;
- `stability`, `verified_at`, and retirement/deprecation metadata.

Valid model references may contain `/`, `:`, `@`, dots, and cloud-specific
syntax. Validation is adapter-specific; do not apply one OpenAI-style model-ID
grammar to every provider.

### 6.2 Roles

| Role | Preferred route | Responsibilities |
| --- | --- | --- |
| Deterministic CLI | None | Inventory, generated surfaces, sync, lint, ownership checks, receipts |
| Economy worker | `wiki_update_economy` | Bounded semantic page edits and structured result |
| Supervisor | Current capable model | Scope, packet creation, heavy-gate ownership, review, reconciliation, escalation |
| Escalation worker | `wiki_update_capable` or supervisor | Only the unresolved subset that triggered escalation |

### 6.3 Economy-eligible work

All of the following must be true before delegation:

- affected pages and evidence inputs are explicitly listed;
- the change is routine semantic maintenance, such as refreshing prose,
  navigation wording, summaries, examples, or links from a bounded diff;
- the relevant extractor/surface manifest is supported and current enough for
  the requested claim;
- no security, public API, cross-cutting architecture, migration, or release
  interpretation is required;
- generated ownership boundaries are known;
- the packet fits the configured model context limit;
- deterministic validation can detect structural breakage after the edit.

### 6.4 Mandatory escalation or stop conditions

- evidence is missing, contradictory, stale, or unsupported;
- the worker reports uncertainty or an incomplete context window;
- source behavior spans multiple subsystems and the intended explanation is
  ambiguous;
- security, authentication, data handling, public API compatibility,
  deployment, migration, or release claims are involved;
- the worker touches a forbidden surface or edits outside its envelope;
- lint, ownership, link, source-reconciliation, or result-schema validation
  fails;
- the economy route cannot resolve to a capability-qualified model;
- one explicitly permitted economy retry fails.

The default policy stops and returns the failure to the supervisor. A capable
model escalation is opt-in and capped at one attempt; no unbounded autonomous
retry loop is allowed.

### 6.5 Resolution precedence

For direct runner handoff, resolve in this order:

1. explicit CLI `--binding` naming a validated local binding;
2. an explicit runner/backend/publisher/model tuple, recorded as an ephemeral
   binding rather than an ambiguous model string;
3. explicit `--routing-profile` resolved through the local agent-specific
   binding;
4. the local default routing profile for wiki updates;
5. legacy runner default only when no routing policy exists yet or policy is
   explicitly `off`;
6. stop before launch with `routing_unresolved` when an enabled `prefer` or
   `require` policy has no qualified binding.

`--model` alone is insufficient for an enabled policy because aliases and
gateway-qualified identifiers can resolve differently. An explicit ephemeral
binding does not bypass capability, budget, ownership, data-governance, or
validation policy. The receipt records the override and its source. Under
`prefer`, a supervising host may explicitly choose its existing capable
workflow after reporting the unresolved economy route; `trigger-agent` never
makes that potentially expensive choice silently. Under `require`, the host
must stop until a qualified binding is available.

### 6.6 Proposed local configuration shape

The exact key names are finalized by MWR-000, but the initial design target is:

```json
{
  "routing": {
    "wiki_update": {
      "profile": "wiki_update_economy",
      "policy": "prefer",
      "bindings": {
        "codex-terra-generic": {
          "route": "wiki_update_economy",
          "runner": "generic",
          "execution_owner": "external_host",
          "backend": "codex-host",
          "model_publisher": "openai",
          "provider_model_id": "gpt-5.6-terra",
          "model_ref": "gpt-5.6-terra",
          "endpoint_protocol": "host-native",
          "variant": {"effort": "low"},
          "stability": "host-catalog",
          "verified_at": "2026-07-18"
        },
        "anthropic-haiku-claude": {
          "route": "wiki_update_economy",
          "runner": "claude",
          "execution_owner": "controller",
          "backend": "anthropic",
          "model_publisher": "anthropic",
          "provider_model_id": "claude-haiku-4-5-20251001",
          "model_ref": "claude-haiku-4-5-20251001",
          "endpoint_protocol": "native-anthropic",
          "variant": {"effort": "low"},
          "stability": "pinned",
          "verified_at": "2026-07-18"
        },
        "gemini-flash-lite-aider": {
          "route": "wiki_update_economy",
          "runner": "aider",
          "execution_owner": "controller",
          "backend": "google-ai",
          "model_publisher": "google",
          "provider_model_id": "gemini-3.1-flash-lite",
          "model_ref": "gemini/gemini-3.1-flash-lite",
          "endpoint_protocol": "native-gemini",
          "stability": "pinned",
          "verified_at": "2026-07-18"
        },
        "deepseek-v4-flash-opencode": {
          "route": "wiki_update_economy",
          "runner": "opencode",
          "execution_owner": "controller",
          "backend": "deepseek",
          "model_publisher": "deepseek",
          "provider_model_id": "deepseek-v4-flash",
          "model_ref": "deepseek/deepseek-v4-flash",
          "endpoint_protocol": "runner-managed-unverified",
          "stability": "pinned",
          "verified_at": "2026-07-18"
        }
      },
      "runner_defaults": {
        "generic": "codex-terra-generic",
        "claude": "anthropic-haiku-claude",
        "aider": "gemini-flash-lite-aider",
        "opencode": "deepseek-v4-flash-opencode"
      },
      "max_economy_attempts": 1,
      "allow_capable_escalation": false
    }
  }
}
```

This data belongs in the existing local `.git/.llm-wiki-agent` surface for the
first release. Secrets, API keys, and provider credentials never belong there.
Bindings whose `execution_owner` is `external_host` are non-authoritative
guidance; the local CLI cannot execute or attest them. Only compatible
Claude/Aider/OpenCode bindings are direct runner bindings. Example `model_ref`
values must still be confirmed against the installed runner's model catalog at
implementation/configuration time.
Shared team policy may later select an abstract profile and caps, but concrete
model IDs remain local unless a team deliberately opts into sharing them.

## 7. Work and Result Packets

### 7.1 Required worker envelope

Every economy-worker assignment includes:

- packet/schema version and unique run ID;
- supervisor approval identity/state and approval timestamp;
- requested route, policy, and capability floor;
- source revision/diff identity and wiki manifest identity;
- exact editable page paths and exact evidence paths;
- requested semantic changes and explicit non-goals;
- forbidden generated blocks/surfaces;
- allowed commands and which agent owns each heavy gate;
- acceptance checks and output/result location;
- escalation triggers and attempt cap.

### 7.2 Required result

The worker returns semantic machine-readable fields plus a human summary:

- `status`: `success`, `partial`, `blocked`, or `failed`;
- changed page paths;
- evidence used per material claim or page;
- checks requested and checks actually run;
- unresolved items and uncertainty;
- forbidden-surface confirmation;
- escalation recommendation and reason.

The untrusted worker does not attest which model executed it. The controller or
generic host writes a separate routing receipt containing the requested
profile, binding ID, runner, configured backend, model publisher,
provider-native model ID, exact runner argument, configured endpoint protocol,
execution owner, variant, deployment scope, resolution source, and attempt.
The effective backend/protocol/publisher/model is recorded only when runner
output or a trusted host API proves it; otherwise each unresolved layer is
`unverified`. A gateway/backend must not be silently attributed to the model
publisher.

An agent subprocess exit code of zero is transport success, not final quality
success. The controller/supervisor must validate the semantic result and actual
filesystem delta.

## 8. Dependency Order

| ID | Title | Priority | Depends on | Type |
| --- | --- | --- | --- | --- |
| MWR-000 | Routing ADR, vocabulary, and contracts | P0 | None | Design/contracts |
| MWR-001 | Provider/backend/runner binding schema and resolver | P0 | MWR-000 | Code/tests |
| MWR-002 | CLI policy controls, migration, and status | P0 | MWR-001 | Code/tests/docs |
| MWR-004 | `wiki-sync` worker envelope and result contract | P0 | MWR-000 | Skill/tests |
| MWR-003 | Generic-agent delegation guidance | P0 | MWR-000, MWR-004 | Schema/tests |
| MWR-005 | Supervisor-approved packet and prompt-only handoff | P0 | MWR-001, MWR-004 | Code/tests |
| MWR-006 | Model-aware runner adapters and trigger outcomes | P0 | MWR-001, MWR-002, MWR-005 | Code/tests |
| MWR-007 | Post-worker reconciliation and capped escalation | P0 | MWR-004, MWR-006 | Code/tests |
| MWR-008 | Routing receipts, metrics, and audit status | P1 | MWR-005, MWR-006, MWR-007 | Code/tests |
| MWR-009 | Standalone documentation packet integration | P1 | MWR-004, MWR-008 | Plan/contracts/tests |
| MWR-010 | Cross-platform, security, and compatibility qualification | P0 | MWR-001 through MWR-008 | Tests/report |
| MWR-011 | Documentation, sibling wiki, pilot, and default graduation | P1 | MWR-001 through MWR-010 | Docs/pilot/closeout |

## 9. Task Decomposition

## MWR-000 - Routing ADR, Vocabulary, And Contracts

Priority: P0
Status: Proposed
Depends on: None
Type: Design/contracts

### Goal

Freeze the provider-neutral policy, versioned packet/result fields, trust
boundary, and compatibility behavior before changing generated instructions or
runner argv.

### Files

- Add: `reports/adr_model_aware_wiki_update_routing_2026-07-18.md`
- Modify: this backlog with the accepted contract
- Reference:
  `reports/roadmap/agent_driven_standalone_documentation_implementation_plan_2026-07-14.md`

### Tasks

- [ ] Define `wiki_update_economy`, `wiki_update_capable`, `prefer`, `require`,
  `off`, `resolved`, `unverified`, and `routing_unresolved`.
- [ ] Define `binding_id`, `runner`, `backend`, `model_publisher`,
  `route`, `execution_owner`, `provider_model_id`, `model_ref`,
  `endpoint_protocol`, `variant`, and `deployment_scope`; prohibit a single
  ambiguous `provider` field.
- [ ] Version the routing request, worker envelope, result, and execution
  receipt schemas.
- [ ] Define economy eligibility, capability floor, escalation triggers,
  retry caps, and supervisor responsibilities.
- [ ] Decide which routing fields are local-only and which abstract policy
  fields may later be committed in team configuration.
- [ ] Threat-model model-ID injection, hidden runner defaults, forged worker
  results, stale configuration, secrets in receipts, expensive retry loops,
  gateway misattribution, and silent cross-provider fallback.
- [ ] Reconcile the repository's Python 3.9+ instruction with current
  `pyproject.toml` and CI metadata; record any dependency/syntax blockers and
  keep feature completion blocked until the chosen support claim is executable.
- [ ] Maintain the date-stamped multi-provider candidate catalog with native
  Anthropic and Gemini examples plus Mistral, DeepSeek, Qwen, gateways, and
  local backends; require implementation-time capability/lifecycle checks.
- [ ] Define the minimum supported matrix: at least two non-OpenAI model
  publishers and at least one native non-OpenAI transport must pass end to end.

### Acceptance Criteria

- A reviewer can determine exactly when an economy worker may be used, how a
  concrete model is selected, and when the supervisor must stop or escalate.
- No provider ID or price is part of a portable schema invariant.
- The contract represents publisher and serving backend separately and does
  not require an OpenAI-compatible endpoint.
- Legacy behavior and opt-in migration are explicit.

### Focused Verification

```bash
git diff --check
```

## MWR-001 - Provider, Backend, Runner Binding Schema And Resolver

Priority: P0
Status: Proposed
Depends on: MWR-000
Type: Code/tests

### Goal

Persist typed multi-provider bindings safely in `.git/.llm-wiki-agent` and
resolve a requested profile deterministically without invoking a provider.

### Files

- Modify: `src/llm_wiki_cli/config.py`
- Add: `src/llm_wiki_cli/services/model_routing.py`
- Test: config and new resolver tests under `tests/`

### Tasks

- [ ] Add a versioned routing configuration structure with strict known keys,
  bounded string lengths, and enum validation.
- [ ] Implement the complete binding fields from Section 6.1, including
  route, execution owner, lifecycle timestamps, and region/deployment scope
  where relevant.
- [ ] Store optional dated cost evidence separately from the portable route:
  source URL, currency/unit, input/output/cache/thinking treatment, region or
  gateway markup, and `verified_at` for hosted models; hardware, quantization,
  model hash, context, measured latency, and a predeclared local cost proxy for
  self-hosted models. Never place credentials in this catalog.
- [ ] Validate `model_ref` with the selected adapter/backend grammar; accept
  legitimate `/`, `:`, `@`, dots, and cloud IDs while rejecting empty strings,
  NULs, controls, and excessive length.
- [ ] Support multiple named bindings and explicit per-runner defaults without
  an implicit cross-provider fallback order.
- [ ] Keep direct runner bindings separate from external-host bindings; the
  resolver must never claim it executed an `external_host`-owned binding.
  Ollama/LM Studio used through Aider or OpenCode remain direct controller-owned
  runner bindings.
- [ ] Implement explicit-binding, explicit ephemeral tuple, profile-binding,
  legacy-default, and strict unresolved precedence without reading credentials.
- [ ] Return a typed resolution containing requested profile, binding ID,
  runner, backend, publisher, configured model reference, variant, source,
  policy, override flag, and pre-launch verification state; only the later
  execution receipt may claim an effective model.
- [ ] Detect known-expired bindings and floating aliases; warn or fail according
  to policy instead of silently substituting a newer model.
- [ ] Preserve unknown future configuration safely during read/upgrade or fail
  with a clear version error; do not silently discard routing keys.
- [ ] Keep paths and serialization portable on Windows, macOS, and Ubuntu.

### Acceptance Criteria

- Resolution is deterministic and has no network side effects.
- Native Anthropic/Gemini and provider-qualified gateway/local bindings can be
  represented without translating them into an OpenAI model schema.
- An unresolved enabled policy returns `routing_unresolved` before any agent
  subprocess starts; `require` also forbids host-level capable fallback.
- Existing config without a routing block reads with byte-compatible legacy
  behavior.

### Focused Verification

```bash
.venv/bin/pytest tests/ -q -k "config or model_routing"
```

## MWR-002 - CLI Policy Controls, Migration, And Status

Priority: P0
Status: Proposed
Depends on: MWR-001
Type: Code/tests/docs

### Goal

Expose routing configuration and inspection without surprising existing
initialized repositories.

### Files

- Modify: `src/llm_wiki_cli/cli.py`
- Modify: `src/llm_wiki_cli/commands/init_cmd.py`
- Modify: `src/llm_wiki_cli/commands/upgrade_cmd.py`
- Modify: `src/llm_wiki_cli/commands/status_cmd.py`
- Test: `tests/test_cli.py` and relevant init/upgrade/status tests

### Tasks

- [ ] Add documented init/upgrade controls for profile, policy, and local
  named bindings without accepting secrets.
- [ ] Let init/upgrade select a named default binding per configured runner;
  direct `trigger-agent` binding/override arguments remain owned by MWR-006.
- [ ] Show profile, selected binding, runner, configured backend, model
  publisher, model reference, lifecycle date, policy, and `unverified` state in
  `status` without printing credentials or sensitive environment data.
- [ ] Keep `status` read-only and cache-only; inspection must never contact a
  provider or start an authentication flow.
- [ ] Preserve routing configuration through `init` and `upgrade` re-rendering.
- [ ] Keep existing installations on legacy runner defaults until explicit
  opt-in; provide an idempotent migration path.
- [ ] Once routing is enabled, never fall through silently to a runner's
  implicit model; surface `routing_unresolved` for an explicit host decision.
- [ ] Ensure `--force` does not override routing or budget policy.

### Acceptance Criteria

- Existing command lines behave as before.
- An operator can configure and inspect a route without manually editing JSON.
- CLI validation errors identify the invalid field and return nonzero.

### Focused Verification

```bash
.venv/bin/pytest tests/test_cli.py tests/test_status.py -q
```

## MWR-003 - Generic-Agent Delegation Guidance

Priority: P0
Status: Proposed
Depends on: MWR-000, MWR-004
Type: Schema/tests

### Goal

Teach a generic supervising agent to delegate only bounded routine wiki page
updates through the economy route while preserving current behavior when the
host lacks model-aware subagents.

### Files

- Modify: `src/llm_wiki_cli/services/schema.py`
- Test: `tests/test_schema.py`
- Test: init/upgrade golden or rendering tests

### Tasks

- [ ] Add a concise generic-only routing section rather than changing the
  shared Claude/Aider/OpenCode instructions unintentionally.
- [ ] Request `wiki_update_economy`; do not hardcode a vendor model in the
  generated schema.
- [ ] Tell hosts that require a concrete model ID to treat the local
  named external-host bindings as candidates and attest their own selection;
  when a host supports named routes directly, pass the route unchanged.
- [ ] State explicitly that the host may choose a capability-qualified
  Anthropic, Gemini, Mistral, DeepSeek, Qwen, OpenAI, gateway, or local model;
  no provider has preference merely because it appears first in documentation.
- [ ] State the supervisor duties: select pages/evidence, retain heavy-gate
  ownership, validate the returned diff/result, and escalate ambiguity.
- [ ] Link or point to the bundled `wiki-sync` skill for the detailed packet.
- [ ] Define fallback: if the host cannot select/report the worker model, mark
  routing `unverified` and use the existing supervisor workflow.
- [ ] Verify upgrade re-renders the block once, without duplicate markers.

### Acceptance Criteria

- Fresh and upgraded generic schemas describe the economy route and safe
  fallback.
- Non-generic schemas do not acquire accidental provider-specific wording.
- The instruction cannot be read as permission for workers to run concurrent
  repository-wide heavy gates.

### Focused Verification

```bash
.venv/bin/pytest tests/test_schema.py tests/test_init.py tests/test_upgrade.py -q
```

## MWR-004 - `wiki-sync` Worker Envelope And Result Contract

Priority: P0
Status: Proposed
Depends on: MWR-000
Type: Skill/tests

### Goal

Put the detailed, reusable economy-worker procedure behind progressive
disclosure in the existing wiki synchronization skill.

### Files

- Modify: `src/llm_wiki_cli/skills/wiki-sync/SKILL.md`
- Modify: `src/llm_wiki_cli/skills/wiki-sync/reference.md`
- Test: `tests/test_skills.py`
- Test: `tests/test_package_metadata.py`

### Tasks

- [ ] Define the supervisor/worker division and economy eligibility checklist.
- [ ] Add the bounded envelope and result fields from Section 7.
- [ ] State editable semantic surfaces and forbidden generated/source surfaces.
- [ ] Require workers to leave the index untouched and never stage, commit,
  stash, reset, or revert; the supervisor/human owns acceptance and commit.
- [ ] Keep `sync` and `lint` serial and supervisor-owned unless explicitly
  assigned; prohibit delegated full-repository gates by default.
- [ ] Add stop/escalation rules for uncertainty, unsupported extractors, stale
  evidence, validation failure, and out-of-envelope edits.
- [ ] Include a minimal generic-host procedure that selects and attests one
  named binding without assuming a provider-specific spawning API.
- [ ] Include at least Anthropic Haiku, Gemini Flash-Lite, and one
  Mistral/DeepSeek/Qwen example beside Codex `gpt-5.6-terra`, all date-stamped
  and described as operator-qualified candidates rather than package law.

### Acceptance Criteria

- A worker can perform the assignment without receiving the entire supervisor
  conversation.
- A supervisor can validate the result without repeating all prose generation.
- Packaged skill tests prove the updated reference ships in distributions.

### Focused Verification

```bash
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
```

## MWR-005 - Supervisor-Approved Packet And Prompt-Only Handoff

Priority: P0
Status: Proposed
Depends on: MWR-001, MWR-004
Type: Code/tests

### Goal

Create a versioned supervisor-approved work packet, then make generated
handoff prompts carry its cost-aware route and bounded result contract while
keeping hooks side-effect free.

### Files

- Modify: `src/llm_wiki_cli/commands/generate_prompt_cmd.py`
- Add: `src/llm_wiki_cli/services/wiki_update_packet.py`
- Modify: `src/llm_wiki_cli/cli.py`
- Modify if needed: `src/llm_wiki_cli/services/plugins.py`
- Add: `tests/test_wiki_update_packet.py`
- Test: `tests/test_generate_prompt.py`
- Test: `tests/test_hook.py`
- Test: `tests/test_plugins.py`

### Tasks

- [ ] Define one normalized packet model and render both JSON and Markdown from
  it; include exact editable/evidence paths, pre-run hashes, ownership rules,
  requested route, checks, stop conditions, and `draft`/`approved` state.
- [ ] Let `generate-prompt` emit a deterministic draft packet, but require a
  capable supervisor or human to approve the exact page/evidence scope before
  economy execution.
- [ ] Treat the explicit `trigger-agent --packet` invocation plus a valid
  approved packet as the launch authorization; hook-created drafts are never
  executable by themselves.
- [ ] Add safe prompt-template values for requested profile, policy, model
  candidate binding IDs, runner, backend, publisher, configured model
  reference, verification state, packet version, and result location.
- [ ] Keep the trusted packet provider-neutral: it requests the abstract route;
  provider candidates belong to local prompt/render context and the execution
  receipt, not the worker's semantic policy.
- [ ] Render the default prompt with eligibility, edit boundaries, result
  fields, and escalation triggers.
- [ ] Preserve custom templates through documented optional placeholders and
  deterministic missing-field behavior.
- [ ] Mark every concrete provider/model as a recommendation unless the
  executing host can verify the binding; prompt text alone is not routing
  proof.
- [ ] Replace the current stage/commit instruction in economy prompts with an
  explicit prohibition; legacy prompt behavior changes only through a separate
  compatibility decision.
- [ ] Keep hook installation and execution prompt-only with no model invocation
  or spend.

### Acceptance Criteria

- One normalized approved packet drives both JSON and Markdown handoff views.
- A generated prompt has enough information for a human or host to choose the
  economy worker and return the expected result, but a draft cannot authorize a
  direct economy launch.
- Existing custom prompt templates remain compatible.
- Hook tests prove no agent process is launched.

### Focused Verification

```bash
.venv/bin/pytest tests/test_wiki_update_packet.py tests/test_generate_prompt.py tests/test_hook.py tests/test_plugins.py -q
```

## MWR-006 - Model-Aware Runner Adapters And Trigger Outcomes

Priority: P0
Status: Proposed
Depends on: MWR-001, MWR-002, MWR-005
Type: Code/tests

### Goal

Resolve and pass an explicit model safely for supported runners, and make every
launch outcome visible to the CLI.

### Files

- Modify: `src/llm_wiki_cli/commands/trigger_cmd.py`
- Add: `src/llm_wiki_cli/services/agent_runners.py`
- Modify: `src/llm_wiki_cli/cli.py`
- Test: `tests/test_trigger.py`
- Test: `tests/test_cli.py`

Runner interface references to recheck at implementation time:
[Claude CLI](https://docs.anthropic.com/en/docs/claude-code/cli-usage),
[Aider options](https://aider.chat/docs/config/options.html),
[Aider providers](https://aider.chat/docs/llms.html),
[OpenCode CLI](https://opencode.ai/docs/cli), and
[OpenCode providers](https://opencode.ai/docs/providers).

### Tasks

- [ ] Add `trigger-agent --packet`, `--routing-profile`, `--routing-policy`, and
  `--binding`; an ephemeral override requires `--backend`,
  `--model-publisher`, `--endpoint-protocol`, and `--model` together. Add
  variant/budget flags only after runner capability is verified.
- [ ] Define `--model` strictly as the runner-native `model_ref`; accept a
  separate `--provider-model-id` when a pinned publisher ID exists. If it is
  absent for a gateway/local alias, record publisher-model identity as
  `unverified` rather than guessing from `model_ref`.
- [ ] Require a valid approved packet whenever routing is enabled; keep the
  unconstrained current prompt path limited to routing-off legacy behavior.
- [ ] Load, validate, and hash the approved packet before launch; bind its
  digest to the prompt and receipt, and fail if it changes during execution.
- [ ] Replace the monolithic command switch with typed Claude, Aider, and
  OpenCode argv builders.
- [ ] Verify each supported runner's current model/budget flags against its
  installed or official interface at implementation time and pin tests to the
  supported syntax.
- [ ] Pass the binding's validated `model_ref` as one argv element; never use a
  shell or accept arbitrary extra runner arguments.
- [ ] Support the validated model surfaces each runner actually exposes:
  Claude `--model`/effort/budget with native Anthropic or its externally
  configured Bedrock/Vertex/Foundry backend; Aider main plus optional
  weak/editor/reasoning settings across native providers, gateways, and local
  models; and OpenCode provider/model plus variant selection.
- [ ] Keep provider credentials in each runner's supported environment/config;
  never put API keys, bearer tokens, base-URL secrets, or credential references
  on generated argv or in receipts.
- [ ] Reconcile the current stale OpenCode `task` transport with supported
  noninteractive `opencode run -m provider/model` behavior before adding model
  routing.
- [ ] Disable runner-native model fallback flags by default; a cross-provider or
  cross-backend fallback requires its own named binding, explicit ordered
  policy, and receipt entries for every attempt.
- [ ] Preflight provider/model availability through runner-native discovery
  where available (`aider --list-models`, OpenCode's catalog, Claude model
  validation) without treating API compatibility as tool-edit capability.
- [ ] Make discovery cache-only and noninteractive by default: it must not
  connect a provider, refresh remote catalogs, initialize files, or prompt for
  authentication. Network/catalog refresh is a separate explicit operator
  action; safe discovery failure returns `routing_unresolved`.
- [ ] Add a typed `TriggerResult` with `success`, `skipped`, `failed`,
  `timed_out`, and `routing_unresolved` outcomes.
- [ ] Propagate timeout, unsupported-runner, execution exception, and agent
  nonzero results as nonzero top-level CLI exits.
- [ ] Preserve existing no-auto-commit and permission-safety behavior.
- [ ] Verify the worker leaves the Git index unchanged; staging or committing
  is a failed outcome even when the subprocess exits zero.

### Acceptance Criteria

- Exact argv tests cover every runner, native non-OpenAI bindings, gateway IDs,
  local IDs, variants, and explicit binding override.
- Enabled routing without an approved packet fails before subprocess launch.
- Model strings containing NULs, control characters, empty content, or excess
  length are rejected before subprocess launch.
- No failed agent run can be reported as a successful CLI invocation.
- Unsupported runner/backend combinations fail before launch instead of being
  coerced into an OpenAI-compatible path.

### Focused Verification

```bash
.venv/bin/pytest tests/test_trigger.py tests/test_cli.py -q
```

## MWR-007 - Post-Worker Reconciliation And Capped Escalation

Priority: P0
Status: Proposed
Depends on: MWR-004, MWR-006
Type: Code/tests

### Goal

Ensure lower-cost execution does not weaken ownership, structural validation,
or claim honesty.

### Files

- Modify: `src/llm_wiki_cli/commands/trigger_cmd.py`
- Add: `src/llm_wiki_cli/services/wiki_update_handoff.py`
- Test: `tests/test_trigger.py`
- Test: focused packet/result validation tests

### Tasks

- [ ] Capture pre-existing index/worktree state and content hashes before the
  run, then validate the returned result against only the newly introduced
  filesystem delta.
- [ ] Allow unrelated dirty paths, but refuse an economy launch when an editable
  or protected packet path already has overlapping user changes. Never
  auto-stash, reset, checkout, revert, or delete those changes.
- [ ] Reject source changes, generated-block changes, paths outside the packet,
  missing result fields, and claimed checks not supported by evidence.
- [ ] Run the configured serial deterministic post-checks with the controller as
  owner; do not allow nested worker fan-out.
- [ ] Permit at most one explicitly configured economy retry for a retryable
  transport or bounded validation failure.
- [ ] Permit at most one capable escalation only when policy enables it and a
  declared escalation trigger is recorded.
- [ ] Escalate only the unresolved subset, not the whole original packet.
- [ ] Return a failed/blocked result when reconciliation cannot prove success.
- [ ] Leave all accepted changes unstaged and uncommitted for supervisor/human
  review and an explicit later commit.

### Acceptance Criteria

- Agent exit zero cannot bypass result, ownership, or deterministic checks.
- Unrelated dirty work survives byte-for-byte, and overlapping dirty target
  pages stop before launch.
- Retry and escalation counts are finite and testable.
- The supervisor receives a compact diff/result/evidence bundle for final
  judgment.

### Focused Verification

```bash
.venv/bin/pytest tests/test_trigger.py -q -k "result or reconcile or retry or escalation"
```

## MWR-008 - Routing Receipts, Metrics, And Audit Status

Priority: P1
Status: Proposed
Depends on: MWR-005, MWR-006, MWR-007
Type: Code/tests

### Goal

Make cost-aware routing observable without mistaking best-effort metrics for
authoritative proof.

### Files

- Modify: `src/llm_wiki_cli/services/metrics.py`
- Modify: `src/llm_wiki_cli/commands/trigger_cmd.py`
- Modify: `src/llm_wiki_cli/commands/status_cmd.py`
- Modify: `src/llm_wiki_cli/commands/uninstall_cmd.py`
- Modify: `src/llm_wiki_cli/cli.py`
- Test: `tests/test_metrics.py`
- Test: `tests/test_status.py`

### Tasks

- [ ] Write the authoritative latest-run receipt to
  the repository control surface (displayed as
  `.git/llm-wiki-trigger-result.json` for a normal checkout) by default, with a
  validated explicit output override and atomic cross-platform replacement;
  resolve linked worktrees and non-Git fallback locations explicitly.
- [ ] Record requested profile, binding ID, runner, configured backend,
  endpoint protocol, model publisher, provider-native ID, exact `model_ref`,
  variant, deployment scope, resolution source, policy, attempt, budget cap
  when known, result status, and escalation reason.
- [ ] Record effective backend/endpoint-protocol/publisher/model only when
  trusted runner output or a host API proves them; otherwise use `unverified`
  even when a model argv was passed. Never present a configured string or
  gateway as proof of the underlying serving route.
- [ ] Never record prompts, source snippets, credentials, environment secrets,
  or raw provider responses in metrics.
- [ ] Extend JSONL events with non-sensitive routing fields while retaining
  their best-effort status.
- [ ] Report actual usage/cost only when returned as structured authoritative
  provider metadata; label unavailable values instead of estimating.
- [ ] Let `status` summarize the last authoritative receipt and distinguish it
  from metrics availability.
- [ ] Remove the default receipt through `uninstall` alongside the existing
  local runtime artifacts; never delete an explicit external output path.

### Acceptance Criteria

- An operator can prove which binding/backend/publisher/model was requested and
  verified, or see `unverified` at the unresolved layer.
- Metrics write failure does not erase the authoritative run outcome.
- Existing metrics readers tolerate absent new fields.

### Focused Verification

```bash
.venv/bin/pytest tests/test_metrics.py tests/test_status.py tests/test_trigger.py -q
```

## MWR-009 - Standalone Documentation Packet Integration

Priority: P1
Status: Proposed
Depends on: MWR-004, MWR-008
Type: Plan/contracts/tests

### Goal

Complete routing evidence for the current agent-driven standalone documentation
workspace without putting provider details into its deterministic core schemas.

### Files

- Modify:
  `reports/roadmap/agent_driven_standalone_documentation_implementation_plan_2026-07-14.md`
- Modify: `src/llm_wiki_cli/services/documentation_run.py`
- Modify: `src/llm_wiki_cli/services/documentation_model_policy.py`
- Modify: `docs/standalone-documentation.md`
- Test: `tests/test_documentation_protocol.py`
- Test: `tests/test_documentation_model_policy.py`
- Test: `tests/test_documentation_workspace.py`

### Tasks

- [x] State that packet preparation requests an abstract route and remains
  provider-neutral.
- [ ] Require the controller/host receipt for every executed wiki semantic or
  user-doc handoff to record the effective model, `unverified`, or
  `routing_unresolved` state.
- [x] Add the requested abstract route to the current packet and keep the worker
  result semantic-only.
- [ ] Add configured/effective binding, backend, publisher, and model evidence
  to the trusted controller/host receipt without invalidating source or
  adopted-wiki provenance.
- [ ] Use the economy route for routine page enrichment and reserve the capable
  route for architecture ambiguity, claim conflicts, review, and escalation.
- [ ] Ensure adopted LLM-enriched wiki pages are not automatically reprocessed;
  route only the stale, ungrounded, or requested semantic subset.
- [ ] Keep publishing qualification dependent on evidence/review gates, not
  model class.

### Acceptance Criteria

- Runner-neutral packets stay replayable across providers.
- Executed handoffs are auditable and their trusted receipts cannot claim an
  economy route without an effective model or explicit `unverified` state.
- Existing-wiki adoption preserves valid enrichments and avoids unnecessary
  model spend.

### Focused Verification

```bash
git diff --check
.venv/bin/pytest tests/ -q -k "packet or handoff or workspace"
```

## MWR-010 - Cross-Platform, Security, And Compatibility Qualification

Priority: P0
Status: Proposed
Depends on: MWR-001 through MWR-008
Type: Tests/report

### Goal

Prove routing is safe and compatible on Python 3.9+ across Windows, macOS, and
Ubuntu before changing defaults.

### Files

- Modify: focused tests named by earlier tasks
- Modify as required by the accepted support decision: `pyproject.toml`
- Modify as required by the accepted support decision:
  `.github/workflows/ci.yml`
- Add: dated qualification report under `reports/`

### Tasks

- [ ] Test Windows paths/spaces, POSIX paths, Unicode model IDs where allowed,
  subprocess quoting, atomic receipts, and timeout cleanup.
- [ ] Audit the feature and its dependencies for Python 3.9 syntax/runtime
  compatibility; add Python 3.9 to CI and align `requires-python` before
  claiming the repository instruction is met.
- [ ] Test malicious model values, shell metacharacters, NUL/control characters,
  excessive length, unknown profiles, invalid policies, and corrupted config.
- [ ] Parameterize binding tests across Anthropic, Gemini, Mistral, DeepSeek,
  Qwen, a gateway-qualified model, a Bedrock/Vertex-style reference, and a local
  alias; include valid `/`, `:`, and `@` identifiers.
- [ ] Qualify at least one self-hosted binding through its actual local runtime,
  including context/tool/edit support and model hash; do not count endpoint
  protocol compatibility alone as a successful model qualification.
- [ ] Test backend/publisher/model conflicts, expired aliases, region-scoped
  Qwen bindings, gateway attribution, and prohibited silent cross-provider
  fallback.
- [ ] Test legacy config, opt-in migration, downgrade/read behavior, custom
  prompt templates, and missing runner executables.
- [ ] Test exact argv for supported runner versions and fail clearly for stale
  or unsupported transports.
- [ ] Keep unit/contract tests credential-free and network-free; run separately
  authorized provider integration pilots for at least two non-OpenAI
  publishers, including one native non-OpenAI protocol path.
- [ ] Require trusted `effective_endpoint_protocol` evidence for the native
  non-OpenAI gate; a configured `endpoint_protocol` string alone cannot pass
  qualification.
- [ ] Test generic mode with a model-aware host, a host that cannot select a
  model, and a worker that returns no model identity.
- [ ] Test bounded context, out-of-envelope changes, deterministic gate failure,
  one retry, one escalation, and no escalation.
- [ ] Run full serial project gates only after focused tests pass and helper
  prerequisites are prepared.

### Acceptance Criteria

- Focused security and compatibility tests pass on all supported operating
  systems and Python versions represented in CI.
- Package metadata, CI, and repository instructions agree on the supported
  Python floor; otherwise qualification remains blocked rather than waived.
- There is no shell interpolation or secret-bearing routing telemetry.
- At least two non-OpenAI provider families pass end-to-end qualification, and
  at least one qualified path has trusted effective-protocol evidence that it
  does not depend on an OpenAI-compatible API.
- Legacy users see no automatic runner/model change.

### Focused Verification

```bash
.venv/bin/pytest tests/test_trigger.py tests/test_generate_prompt.py tests/test_schema.py tests/test_skills.py tests/test_metrics.py tests/test_status.py -q
.venv/bin/python -m compileall src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
```

## MWR-011 - Documentation, Sibling Wiki, Pilot, And Default Graduation

Priority: P1
Status: Proposed
Depends on: MWR-001 through MWR-010
Type: Docs/pilot/closeout

### Goal

Document the model policy, prove that it saves capable-model work without
lowering quality, and define the evidence required before any default changes.

### Files

- Modify: `README.md`
- Modify: relevant bundled skill docs
- Modify separately: `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki`
- Add: dated pilot and closeout reports under `reports/`
- Modify: changelog/release notes when the feature is released

### Tasks

- [ ] Document generic, prompt-only, and CLI runner workflows, including
  `prefer`, `require`, `off`, unresolved routing, and explicit overrides.
- [ ] Show current configuration examples for Codex/OpenAI, Anthropic, Google,
  Mistral, DeepSeek, Qwen, a gateway/cloud backend, and a local backend, with a
  visible verification date and lifecycle/pricing drift warning.
- [ ] Explain runner/backend/publisher/model separation and show at least one
  native Anthropic or Gemini path that does not use an OpenAI-compatible API.
- [ ] Document the provider-catalog refresh procedure: recheck official model
  IDs, retirement, runner discovery, tool capability, scope/region, and price;
  never update a pinned binding silently.
- [ ] Explain that a lower-cost model is a routing preference, not a quality or
  publish-ready claim.
- [ ] Update the sibling wiki in its own working tree and commit flow after the
  implementation is accurate.
- [ ] Pilot on small, medium, and cross-cutting wiki diffs; compare eligible
  work coverage, supervisor intervention, validation failures, and rework.
- [ ] Include at least two non-OpenAI publisher families in the pilot and
  report results per binding/backend rather than pooling away provider-specific
  failures.
- [ ] Before the pilot, select an authoritative usage source or a fixed audited
  proxy for capable-supervisor work; do not choose a favorable proxy after
  results are known.
- [ ] Record routing resolution rate, economy completion rate, escalation rate,
  forbidden-edit rate, and supervisor-review effort.
- [ ] Graduate `prefer` to a new-install default only if the success criteria in
  Section 10 hold; never silently change existing installs.
- [ ] Update this backlog with commits, commands, evidence, and remaining
  limitations.

### Acceptance Criteria

- Users can configure a provider/backend/model binding without reading source
  code or translating it into an OpenAI-compatible endpoint.
- Generic and handoff docs use the same terminology and escalation semantics.
- Main-repo and sibling-wiki changes are verified and committed separately.
- Default graduation is evidence-based and reversible.

### Focused Verification

```bash
.venv/bin/pytest tests/test_package_metadata.py tests/test_skills.py -q
git diff --check
```

## 10. Pilot Metrics And Graduation Gates

The first pilots compare model-aware routing with the current supervisor-only
workflow on equivalent bounded tasks. Do not infer currency cost when the host
cannot supply authoritative cost metadata.

Required measures:

- **routing resolution rate:** percent of eligible handoffs with a proven
  concrete model rather than `unverified`;
- **provider coverage:** accepted runs by runner, serving backend, model
  publisher, and binding, with native and gateway paths reported separately;
- **economy completion rate:** percent of economy assignments accepted after
  deterministic checks and supervisor reconciliation without full rewrite;
- **capable-model displacement:** supervisor work avoided, measured by bounded
  task count and, where authoritative, supervisor tokens/time;
- **escalation rate and reason:** split ambiguity, context, validation,
  transport, and capability failures;
- **rework rate:** worker assignments substantially rewritten by the supervisor;
- **ownership violations:** any source/generated/out-of-envelope edit;
- **quality regression:** lint, link, provenance, review, or publish-gate
  failures relative to the baseline;
- **actual cost:** only when provider usage and pricing evidence is available.

Do not compare provider list prices without normalizing cache behavior, region,
prompt/output volume, thinking tokens, gateway markup, and accepted-result
rate. A nominally cheap failed run followed by capable-model rework is charged
to the routed workflow in pilot analysis.

Proposed graduation gates for new installs:

- 100% of launched handoffs have a receipt with resolved or explicit
  `unverified` routing state;
- zero accepted ownership violations;
- zero masked nonzero/timeout trigger outcomes;
- at least 90% of economy-eligible pilot tasks pass deterministic checks;
- no material increase in post-review documentation defects;
- supervisor full-rewrite rate below 15%;
- at least a 30% reduction in capable-supervisor semantic-editing tokens or a
  predeclared audited time proxy versus matched supervisor-only tasks;
- when authoritative provider cost is available, at least a 20% reduction in
  median cost per accepted economy-eligible task;
- escalation remains bounded and every escalation has a declared reason;
- existing-install compatibility tests remain green.

If neither authoritative capable-model usage nor a credible predeclared proxy
is available, the feature may remain explicit opt-in but cannot graduate to a
new-install default. Quality-only evidence does not prove the requested
capacity or cost saving.

Kill or redesign the default if economy workers repeatedly require full
supervisor rewrites, fail ownership boundaries, or cannot be selected and
verified on the intended generic hosts. Retain explicit opt-in routing even if
default graduation is rejected.

## 11. Shared Verification Baseline

Run focused tests after each task. Before closeout, run heavy gates serially and
with the project virtual environment:

```bash
.venv/bin/pytest -q
.venv/bin/python -m compileall src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/llm-wiki lint --wiki-dir /path/to/test.wiki --src-dir . --jobs 1
git diff --check
```

The required repository context gate was attempted while preparing this
backlog and was initially inconclusive because the local Go and Haskell helpers
were not prepared. It was later completed during the standalone-documentation
implementation pass with an explicit prepared-helper cache:

```bash
.venv/bin/llm-wiki context --budget 8000 --src-dir . --format markdown --focus changed --read-only
```

That later result closes the drafting-time discovery gap for the current tree;
MWR implementation must still rerun the gate against its own final diff and
record the helper prerequisites in its closeout.

## 12. Delivery Rules

- Use `.venv/bin/python`, `.venv/bin/pytest`, and other `.venv/bin/` tools for
  every Python command.
- Preserve Python 3.9+ and Windows/macOS/Ubuntu compatibility.
- Run repository-wide `llm-wiki`, full pytest, coverage, and build gates
  serially; use `--jobs 1` for interactive LLM Wiki commands.
- The main agent owns heavy-gate scheduling. Economy workers receive a heavy
  gate only through an explicit bounded assignment.
- Stop on ENOSPC, EMFILE, ENFILE, ENOMEM, EAGAIN, `MemoryError`, or executor
  startup failure; do not retry automatically.
- Preserve unrelated and ignored worktree changes.
- Update `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki` when implementation
  changes user-facing behavior; verify and commit that sibling repository
  separately.
- `reports/` is ignored. Verify with `git check-ignore -v` and use
  `git add -f` only when the user explicitly requests committing the backlog or
  reports.

## 13. Definition Of Done

This backlog is complete only when:

- generic-agent instructions request bounded economy-worker routing and have a
  truthful fallback for hosts that cannot select or report a model;
- prompt-only handoffs carry the route, envelope, result, and escalation
  contract without invoking an agent;
- supported CLI runners resolve and pass a validated explicit model through
  provider-specific adapters;
- the binding/receipt contract distinguishes runner, serving backend, model
  publisher, provider-native ID, runner reference, and variant;
- end-to-end qualification passes for at least two non-OpenAI publishers,
  including one native non-OpenAI protocol path, without silent
  cross-provider fallback;
- failed, timed-out, and unresolved executions propagate nonzero outcomes;
- every executed handoff has an authoritative, non-sensitive routing receipt;
- worker edits are reconciled against packet scope, generated ownership, and
  deterministic checks before success;
- retry/escalation is capped and auditable;
- the standalone documentation plan and packet contracts use the same routing
  semantics;
- focused and full verification pass with extractor prerequisites accounted
  for;
- README, bundled skills, changelog/release material, and sibling wiki match
  shipped behavior;
- pilot evidence supports any new-install default change, while existing
  installs remain opt-in and compatible.
