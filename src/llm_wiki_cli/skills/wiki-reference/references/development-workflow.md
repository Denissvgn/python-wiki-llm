# Development workflow

## Contents

- [Frame and ground the change](#frame-and-ground-the-change)
- [Change and verify independently](#change-and-verify-independently)
- [Select checks from contracts and environments](#select-checks-from-contracts-and-environments)
- [Retain the reason and refresh knowledge](#retain-the-reason-and-refresh-knowledge)
- [Deliver and improve the next task](#deliver-and-improve-the-next-task)

Read this topic for substantive code changes or investigations to connect the
request, scoped evidence, independent verification, and durable project knowledge.
It owns the development procedure, not its specialist operations. It does not
authorize edits, execution, setup, Git actions, publication, or a wider read scope.
User, repository, and host rules remain authoritative.

The installed library owns current schema and storage selection. For normal
work, omit task and compact-view version fields; supply requirements, budgets
and scope. Init and project upgrade install current workflow defaults, and
bootstrap/upgrade prepare current native storage with recovery preimages.
Readers never upgrade data. Explicit older contracts are compatibility tools,
not choices for an agent's ordinary work. Ordinary maintenance ownership does
not invent human review, and optional publication/privacy settings remain under
their existing authorization rules.

Small mechanical work can use direct inspection and proportionate checks. This
reduces retrieval and record ceremony, not relevant maintenance or delivery
obligations. A read-only investigation can mark change-dependent steps not
applicable and verify its requested findings instead of inventing an edit.

## Frame and ground the change

State the intended behavior and independent acceptance criteria. Resolve the
actual source/wiki roots, source selection, executable, helper cache, and
permitted actions from the project and caller. Use exact coordinates relative to
the chosen source root; preserve these bindings throughout the task.

Use the narrowest useful evidence route in
[Context and query selection](context-query.md). Search results are candidates;
choose exact owners and inspect relevant source before editing. Preserve missing,
stale, unsupported, ambiguous, unavailable, and truncated evidence as gaps. A small
response does not establish a small scan. Stop repeating retrieval that adds no
useful evidence and use permitted direct inspection or a scoped follow-up.

For supplied-path impact, choose `source_policy: "discovery"` when discovery
exclusions must hold and the active interface supports it. Keep filesystem,
selection, extraction, and inventory `present` separate. If that capability is
unavailable or its diagnostic contradicts observed source, retain the gap and
inspect permitted evidence; never reinterpret inventory absence as a missing
file or silently switch to an exclusion override.

Source-only evidence needs no wiki. Required native evidence that fails remains
unresolved; never silently migrate, bootstrap, or downgrade it to source-only
success. Read [Qualified knowledge consumption](knowledge-consumption.md) before
interpreting availability or negative results. Provider coverage does not prove
runtime behavior, prose correctness, or completed review.

## Change and verify independently

Connect each criterion to its source owner, proposed change, compatibility effect,
remaining assumption, and an independently specified check. Make the authorized
bounded change, run those checks, and inspect actual outcomes. Checks should match
the change and applicable repository requirements; repeat successful gates only
for changed inputs, failures, or unresolved concerns.

Establish the capabilities required by a check before running it: prepared
helpers, runtime/toolchain, and relevant process or socket permissions. A missing
prerequisite is an environment failure, not a product defect or passing coverage.
Use [Extractors and dependencies](extractors-dependencies.md) for helper recovery.
Retain the original failure and successful corrective reruns separately.

## Select checks from contracts and environments

Discover supported environments and existing verification commands from the
project's instructions, declared interfaces, packaging, CI and relevant source.
Connect each affected criterion to its independently expected outcome, source
owner, relevant environment or capability, and verification route. Use the
project's own commands and support scope; do not invent another language,
platform, CI provider or mandatory matrix. The conversation or an existing
permitted record can hold these decisions; no new manifest is required.

For an affected interface boundary, identify its representation and semantics:
native filesystem path, canonical repository path, URI, shell argument,
serialized key, byte stream or platform metadata. Fixtures and expected values
must follow that interface contract. Translate only at the declared boundary
and retain strict rejection rules. A backslash can be a literal POSIX filename
character; replacing every backslash can change a valid native path. Metadata
fields with the same name may have different meanings across APIs or runtimes;
compare shared meanings across interfaces while retaining change detection
within each interface.

Choose a small, discriminating check before a broad suite. Flavored path objects
can expose spelling assumptions locally; forced fault or capability cases can
exercise decoder limits and supported stream alternatives. These simulations
do not certify native behavior. When filesystem, process or runtime semantics
matter, verify the relevant declared native environments using existing runners
and maintained commands. Missing access leaves an applicable gate pending;
local success does not replace required hosted qualification.

Audit conditional checks against the current candidate. An applicable missing
prerequisite needs a named verification owner and successful evidence from its
capable environment before the gate can pass. An unavailable optimization must
not skip verification of a supported fallback. Mark truly inapplicable cases
with a reason; never admit blanket skips or count them as covered. Before owning
sync or qualifying extraction, check both prepared helper identity and active
execution runtime under the same cache base. Inspect package, helper and runtime
bases separately; do not manufacture compatibility for runtime-bound observations.
Use the authorized setup route or leave the prerequisite unresolved.

Classify retained failures as environment, fixture, product or workflow issues
before correcting them. Verify the correction with an independently expected,
discriminating case and the affected required gates on the actual candidate.
Keep the original failed attempt and source/evidence identities. A successful
fallback does not erase the initial failure. Apply these checks proportionately:
small mechanical or read-only work does not require a new matrix, task file or
target execution merely to follow this procedure.

Before qualifying measurements, run `llm-wiki doctor --analysis-inputs --format json`
and retain its result. This read-only check covers the installed provider's
Python/helper census and registered implementation files, not project source,
runtime/helper readiness or semantic correctness. An unavailable result leaves
measurement qualification pending. For provider source additions, review
`services/analysis_contracts.json`: presentation/consumer files belong in the
census; observation code also needs its correct producer input lists. Classify
deliberately, rerun the preflight and affected checks, and retain the failed
attempt. Never automatically register files or infer producer trust from a
passing census. Other projects' application files are outside this registry.

If a check inspects tracked publication inputs, stage the exact reviewed candidate
only when existing authority and [Repository handoff](repository-handoff.md)
permit it. Keep private records outside that candidate. Update independently
declared current-project source expectations when the intended boundary changes;
do not rewrite historical campaign evidence to match a new producer.

## Retain the reason and refresh knowledge

Preserve the durable contract and rationale in the appropriate authored section.
An existing affected wiki within scope follows
[Maintenance and validation](maintenance.md): owning sync, semantic review,
re-anchor after canonical prose changes, then validation. Serialize the writer
and subsequent qualifying reads. Choosing source-only evidence does not waive
this maintenance. Without an affected in-scope wiki, retain the reason in the
permitted handoff; bootstrap remains an explicit separate choice.

Reconcile or rebuild evidence after saved source, selection, ignore, configuration,
helper, or provider changes. On resume, validate retained context and recheck its
current basis. Validation alone proves neither currentness nor semantics; session
events and an empty maintenance queue do not replace that comparison.

For development of the provider itself, pin the planning provider's artifact and
freeze independent expected outcomes before evaluating its replacement. An
editable installation changes with its source. Other projects do not need two
provider environments merely to follow this procedure.

## Deliver and improve the next task

Hand off actual changes, reasons, criterion outcomes, evidence basis, knowledge
status, remaining gaps, and next action. Keep each required gate pending,
satisfied, or blocked; mark inapplicable gates with a reason. Failure preserves
the last completed gate and adds an attempt. A complete task claim requires every
required gate to be satisfied; a qualified partial handoff remains incomplete.

Disclose observed tool discrepancies. When reporting is enabled or requested,
retain a bounded reproduction, expected/actual behavior, provider and target
identities, roots/selection, evidence, impact, workaround, and acceptance criteria
at a permitted private destination under the repository-handoff rules. Separate
library defects, unsupported scope, environment failures, and workflow proposals.
Do not hide a failed read behind a successful fallback.

Record a reusable action as proposed until another task confirms it; confirm
across projects before claiming transfer. Promotion into persistent instructions
is a separately reviewed change. Label estimated costs and unavailable model
usage; do not infer a general speedup from a successful read.

The conversation or an authorized local record can hold this handoff. Separate
task files, profiles, sessions, compact delivery, governance adoption,
automatic report files, and model orchestration are not prerequisites. The
optional native-coding recipe adds explicitly selected interface details to this
procedure; loading it does not activate a profile.
