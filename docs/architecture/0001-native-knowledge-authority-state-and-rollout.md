# ADR-0001: Native knowledge authority, state, and rollout

- **Status:** Accepted
- **Date:** 2026-07-25
- **Scope:** Native knowledge layer, beginning with the planned
  `.llm-wiki-knowledge.json` artifact

## Context

Knowledge-related state is currently split across canonical Markdown,
`SyncManifest`, the canonical surface registry, and the generated surface
index. The planned native knowledge layer adds a generated observation read
model. Without a single decision record, that artifact could become a competing
editable source of truth, persist an obsolete freshness verdict, or be combined
with files produced from another repository snapshot.

This ADR is normative for authority, load-state, commit, compatibility, and
rollout semantics. Its KNOW-002 addendum fixes the v1 taxonomy and
forward-compatibility policy, while its KNOW-004 addendum fixes bundle
identity, producer evidence, redaction, and no-exec policy. The packaged schema
remains normative for exact `llm-wiki-knowledge/v1` field names.

The relevant existing seams are:

- the product and artifact overview in the
  [README](../../README.md);
- page kinds, routes, MCP URIs, and coarse ownership in the
  [surface registry](../../src/llm_wiki_cli/services/wiki_surface.py);
- the existing `llm-wiki-surface-index/v1`
  [surface projection](../../src/llm_wiki_cli/services/wiki_surface_index.py);
- the current operational
  [sync manifest](../../src/llm_wiki_cli/commands/sync_cmd.py);
- the public [Python API](../../src/llm_wiki_cli/api.py);
- the
  [context service](../../src/llm_wiki_cli/commands/context_cmd.py); and
- the read-only [MCP service](../../src/llm_wiki_cli/services/mcp_server.py).

## Decision

LLM Wiki will use a native, evidence-aware knowledge contract and a generated,
rebuildable `.llm-wiki-knowledge.json` projection. The native contract is
canonical for the meaning of its API records, but the projection is not an
editable document store and does not supersede repository source, canonical
Markdown, or future explicit governance records.

### Authority by fact class

| Fact class | Authority | Role of persisted artifacts |
|---|---|---|
| Structural source and configuration facts | Repository source/configuration, interpreted by reproducible application-owned extractors | Inventory, caches, the manifest, and the knowledge index record observations and their basis; they do not override source/configuration |
| API wire-contract details from an explicitly selected OpenAPI input | That OpenAPI document for the details it defines; repository source remains authoritative for handler and linkage context | The selected relative input, hash, and analysis basis are operational evidence |
| Semantic prose | Canonical Markdown body | Generated projections may digest or quote its state but never become the editing authority |
| Page taxonomy, canonical paths, MCP URIs, and coarse `generated`/`semantic`/`mixed` ownership | The canonical surface registry | `PageKind` and `SurfaceRole` remain compatibility summaries; section-level ownership is deferred |
| Active canonical page presence and stored document bytes | Markdown files found at registry-defined paths | Semantic prose follows the authority above; generated structural claims still defer to source/configuration. `index.md` is navigation, and `.llm-wiki-surface.json` is a rebuilt discovery projection |
| Incremental generation baselines, source/page mappings, enabled-surface policy, and generation inputs | Sync machinery | The manifest is operational generation state, not a general knowledge or governance database |
| Page discovery for machine consumers | Current canonical pages interpreted through the surface registry | `.llm-wiki-surface.json` remains the deterministic `llm-wiki-surface-index/v1` read model |
| Knowledge record vocabulary and representation | The versioned native knowledge contract | The contract is normative for record meaning and shape, not for the truth of a represented observation |
| Knowledge observations, provenance, evidence basis, and extracted/inferred relationships | Repository evidence plus reproducible analysis for structural observations; canonical Markdown for link observations; the future governance ledger for governance relationships | A committed knowledge index is the validated read projection for those observations, not proof that an observation is true or current |
| Live freshness | A consumer's comparison of a persisted observation basis with one live evaluated basis | No generated artifact may persist a timeless `current` verdict |
| Extraction, lint, authorship, and verification | Each fact's own explicit producer or event | No one dimension implies any other, and they are never collapsed into a scalar trust score |
| Stable identity, aliases, lifecycle transitions, and review events | A future durable, merge-aware governance ledger changed through explicit operations | These decisions must not live only in the rebuildable manifest or knowledge index |
| Site, Obsidian, and possible OKF output | The applicable native contract plus canonical Markdown | These are disposable derived projections and never authoring authorities |

### Locked decisions

The following decisions apply to all milestones:

1. Repository source and configuration are authoritative for structural facts.
2. Canonical Markdown is authoritative for semantic prose.
3. The sync manifest is operational generation state, not a general knowledge
   database.
4. The knowledge index is generated and rebuildable and must never be
   hand-edited.
5. `.llm-wiki-surface.json` remains on
   `llm-wiki-surface-index/v1` throughout the MVP.
6. Generated data persists observation bases, not a timeless
   `"freshness": "current"` value. Consumers compute freshness against a live
   evaluated snapshot.
7. Missing evidence, lifecycle, authorship, and verification are explicit
   `unknown` or `untracked` states, never optimistic defaults.
8. Extraction, lint success, authorship, and verification are distinct facts.
   There is no scalar trust score.
9. Module and entity fingerprints are concept-scoped. The existing file-level
   semantic hash is not sufficient for entity-level freshness.
10. Stable IDs, aliases, lifecycle transitions, and review events require a
    durable governance ledger outside the rebuildable manifest.
11. Metadata must never select or trigger document-supplied code, helpers,
    subprocesses, network calls, LLMs, or attesters. Existing
    application-owned extractor helpers retain their current policies.
12. Site, Obsidian, and OKF outputs remain derived projections.

### Observation basis is not live freshness

A persisted structural observation records the basis needed for a later
comparison: the source content, concept-scoped observation, applicable
extractor/plugin/schema/configuration/options basis, and evaluated snapshot.
The exact schema fields are a later contract decision.

A consumer may report `current` only after evaluating live inputs and
establishing that:

1. the live and recorded analyzer, schema, configuration, and option bases are
   compatible;
2. the live source content hash matches the recorded source content hash; and
3. the live concept-scoped observation matches its recorded observation.

A matching basis means "unchanged since this observation," not "true,"
"verified," or "approved." If no live evaluation occurred, freshness is
`unknown`, even when the artifact set is `valid`. A source-missing observation
also does not make a concept `deprecated`; evidence freshness and lifecycle are
separate dimensions. If the source bytes differ but the concept-scoped
observation still matches, the result is a nonsemantic source change rather
than `current`.

### V1 vocabulary and forward compatibility (KNOW-002 addendum)

The packaged
[`llm-wiki-knowledge/v1` JSON Schema](../../src/llm_wiki_cli/schemas/llm-wiki-knowledge-v1.schema.json)
defines the persisted record shape. The
[typed model and standard-library validator](../../src/llm_wiki_cli/services/knowledge_model.py)
define its runtime representation and semantic validation.

The initial domain concept kinds are `source-module`, `code-entity`,
`workflow`, `guide`, `user-flow`, `infrastructure-resource`, `api-contract`,
and `dependency-view`. Navigation and change-log pages use the explicit
document-only kinds `navigation-document` and `change-log-document`; consumers
may omit those records from a semantic graph.

The initial core relationships are `derived_from` and `links_to`. Link
resolution has four states: `resolved`, `external`, `ambiguous`, and
`unresolved`. Target classification is a separate dimension with `unknown`,
`concept`, `source`, `external`, `mail`, `anchor`, `asset`, and `malformed`
values. Every core `links_to` record preserves the observed raw and normalized
target spellings, label, and character range alongside a canonical locator,
canonical path, or external URI when resolution supplies one. This keeps the
source observation lossless without conflating what a target is with whether
it resolved.

V1 uses the following closed-core policy:

- Core record objects reject unknown fields. Custom fields must be carried
  inside an explicit `extensions` object.
- Every extension key and every non-core concept or relationship kind must use
  a qualified `namespace/name` spelling. Qualified unknown kinds and extension
  values are preserved through validation and serialization.
- Extension values may contain any finite JSON value unless the schema reserves
  that qualified key for a constrained v1 value. Unqualified unknown fields or
  kind values are invalid because they are indistinguishable from misspelled
  core vocabulary.
- Adding an unqualified core field or kind, removing a field or enum value, or
  changing an existing field's meaning requires a new schema version. A
  producer that needs forward-compatible v1 data must use a namespaced
  extension instead.

JSON Schema enforces the platform-portable wire shape and cross-field rules
expressible in Draft 2020-12. A payload is not a valid native knowledge record
merely because a generic schema validator accepts it: the typed validator
additionally enforces registry-derived paths and locators,
concept-kind/page-kind agreement,
whole-document ownership agreement, declared producer and source references,
producer limitation ordering, unique concept coordinates, and resolved
internal targets. Those rules depend on application registries, other records,
or ordering semantics and are intentionally semantic validation rather than
duplicated, partial schema logic.

In v1, `ObservationScope` (`module`, `entity`, or `aggregate`) names the
granularity of a reproducible structural fingerprint. It is not the future
concept/section/claim/relationship review scope. Likewise, semantic
`ownership` mirrors the document's coarse `SurfaceRole` because `page_hash` is
a whole-document mutation detector; section ownership and digest-bound review
remain deferred.

### Bundle identity, producer evidence, redaction, and no-exec policy

_KNOW-004 addendum._

The native bundle is portable across checkouts, but it is not anonymous and is
not automatically safe to publish. Repository identity, evaluated state,
producer evidence, and projection redaction are separate dimensions. None of
them is an attestation, permission, authentication result, or instruction to
execute code.

#### Repository identity

An application-owned envelope builder selects repository identity in this
strict order:

1. an explicitly configured public identity;
2. one normalized VCS remote identity; or
3. the literal `unknown`.

A configured public identity must already be a safe qualified namespace path
such as `github.com/acme/project`; its leading namespace/host segment is
lowercase, while later path-segment case is preserved. It has no scheme,
credentials, port, query, fragment, absolute path, dot segment, backslash,
trailing `.git`, or checkout-specific suffix. An invalid configured value is an
error rather than permission to silently use a different identity.

When no public identity is configured, a Git-aware builder selects exactly one
remote candidate: the current branch's upstream remote when one is identified,
otherwise `origin` when present, otherwise the sole configured remote. A
selected but missing or unusable candidate yields `unknown`; multiple
unselected remotes are ambiguous and also yield `unknown`. The builder does not
probe a remote or make a network request.

HTTPS, SSH, and SCP-like remote spellings normalize to
`lowercase-host/path`, preserving path-segment case. Normalization removes the
scheme, user information, credentials, query, fragment, a scheme's default
port, trailing slash, and one trailing `.git`. A non-default port, local path,
`file:` remote, malformed escape, empty or dot segment, or result outside the
safe identity grammar makes the candidate unusable. Raw remote strings are
input evidence only and are never persisted.

`bundle.repository.extensions["llm-wiki/identity-source"]` records
`configured-public`, `normalized-vcs`, or `unknown`. A non-`unknown` identity
must carry one of the first two values. An `unknown` identity has source
`unknown`, whether that default is explicit or omitted; canonical serialization
omits that default marker. This provenance lets a later public projection
distinguish intentionally public identity after an application-owned
build/load check; the self-described marker alone is not authorization to
disclose it.

The identity is repository-level, not checkout-level. A builder must never
derive it from an absolute checkout path, directory basename, local username,
machine name, revision hash, source hash, or other content fingerprint.
`unknown` is a nonidentity sentinel and never matches another `unknown`.
Equality of the same explicit non-`unknown` identity is necessary, but not
sufficient, for merge or deduplication; snapshot, schema, and governance
compatibility still apply. Equal snapshot hashes never collapse distinct or
unknown repositories.

#### Evaluated revision and working tree

For Git, `evaluated_revision` is `git:` followed by the complete lowercase
40- or 64-hex object ID that `HEAD` resolved to for the evaluated run. It is
never a branch, tag, abbreviated object ID, timestamp, or pathname. Non-Git,
unborn, or unevaluable state uses `unknown`.

`working_tree` is independent of the revision. It is `dirty` when the
application-owned status evaluation sees any staged change, tracked
modification or deletion, or non-ignored untracked entry in the evaluated work
tree; ignored entries are excluded. It is `clean` only after that evaluation
completes with none of those conditions, and otherwise is `unknown`. Neither
field participates in repository identity.

#### Snapshot and observation hash domains

All v1 hash fields use lowercase SHA-256 wire values. Each field has a distinct
semantic commitment domain and must not substitute for another. Fields that
commit to persisted bytes hash those bytes directly; fields that commit to a
set or normalized observation serialize that structure in stable path/key
order:

| Field | Commitment |
|---|---|
| `source_snapshot_hash` | The selected repository-relative source and configuration inputs actually consumed by the run, including each normalized path and exact content digest |
| `markdown_snapshot_hash` | The active canonical Markdown path set and UTF-8 content, with POSIX paths and LF line endings |
| `surface_index_hash` | The exact persisted `.llm-wiki-surface.json` bytes |
| `generation_options_hash` | The allowlisted, effective behavior-affecting generation options, including defaults |
| `source_content_hash` | The exact content basis for one structural source observation |
| `concept_observation_hash` | The normalized, concept-scoped structural observation |
| `aggregate_input_hash` | The ordered contributing evidence for one aggregate observation; it is not a fifth bundle snapshot hash |
| `page_hash` | The complete canonical Markdown document bytes used by that semantic observation |

Exact tagged framing for structured source, Markdown, option, observation, and
aggregate inputs belongs to the later envelope builder milestone; the
`surface_index_hash` and projection commitments remain raw hashes of exact
persisted bytes. Later framing may not change the semantic domains above. Hash
inputs exclude wall-clock time, absolute checkout roots, temporary files,
caches, logs, process IDs, thread or completion order, and other machine-local
state.

#### Producer and analyzer evidence

`bundle.producer.tool` identifies the application-owned writer. Every
extractor or plugin that materially contributed persisted observations is
listed with a stable ID and version. Its `configuration_hash`, when present,
commits to a canonical allowlist of effective, non-secret,
behavior-affecting settings including defaults. Raw plugin settings,
credentials, environment dumps, and machine-local absolute filesystem paths
are never persisted.

A builder must include `configuration_hash` when it can completely and safely
represent that basis. If it cannot, it omits the optional hash, adds the stable
limitation code `configuration-basis-unknown`, and consumers treat the basis as
incompatible for a positive freshness result. A conforming application-owned
builder emits limitations as sorted, deduplicated machine codes describing
material analysis boundaries, not diagnostic logs or a channel for raw
configuration. JSON Schema enforces the code grammar and uniqueness; the typed
validator also enforces stable ordering and the configuration/limitation
pairing. A change to a contributing component's ID, version, safe configuration
hash, or limitations changes the producer basis even when source and snapshot
hashes are unchanged. Validation checks representation and internal
consistency; it cannot attest that producer claims are true or complete.

Producer records describe what already ran; they do not declare what a reader
should load. Extractor references resolve only against an application-owned
registry selected before artifact parsing. Missing or unknown references fail
validation or basis compatibility without importing anything named by the
artifact.

#### Redaction profiles

Projection profile is trusted caller policy supplied out of band. It is never a
persisted bundle field and cannot be selected by an extension, plugin record,
actor, link, or other artifact value.

| Profile | Required boundary |
|---|---|
| `internal` | May retain configured-public and normalized-VCS identities, evaluated revision and tree state, actor identity, producer evidence, raw lossless link observations, and schema-valid extensions. It still forbids credentials, raw remotes, machine-local absolute filesystem paths, environment dumps, and raw plugin settings. |
| `public-portable` | Retains repository identity only when trusted current-run configuration establishes source `configured-public`; otherwise emits `unknown`. It retains the required identity-source marker, emits unknown revision and tree state, strips or coarsens local actor identity, drops other extensions by default, and omits private plugin records and unreviewed private links or evidence. Only an explicit application-owned public allowlist may retain additional fields. |

A public projection drops an entire observation when a required lossless core
field contains credentialed or private material; it does not rewrite the raw
observation into something falsely presented as lossless. Exact public
allowlists and exporter mechanics belong to KNOW-501. The packaged native JSON
Schema is platform-portable, not proof that an instance is safe for public
release.

#### No execution and no access-control meaning

Every string and extension value in a knowledge artifact is inert data.
Parsing, validation, serialization, loading, freshness comparison, and
projection must not, because of artifact metadata:

- import or evaluate a module or entry point;
- execute a helper, command, subprocess, hook, or plugin;
- install or activate code;
- open a network connection or invoke an LLM or attester; or
- select a projection profile.

Only code and registries already selected by the application may perform an
explicitly authorized operation. Component IDs, versions, limitations,
extractor references, actor model names, URLs, and extension keys are evidence
or observations, never dispatch selectors.

Artifact metadata also cannot authenticate a principal, grant a role,
authorize disclosure, enforce an ACL, or establish trust. Access-looking
extensions may round-trip as inert namespaced data, but callers must ignore
them for authorization and apply access policy outside the artifact. Unknown
components, profiles, or policy-like metadata therefore fail closed or remain
unavailable; they never opt into broader behavior.

### Knowledge-load states

The shared loader will use the following state vocabulary. Stable reason codes
may refine a state, including distinguishing malformed data from an unsupported
future schema version.

| State | Meaning | Required loader behavior |
|---|---|---|
| `valid` | Knowledge, surface, and manifest schemas validate; safe paths, the normalized Markdown snapshot, and required page parity hold; exact projection byte hashes and envelope commitments agree | Return the committed knowledge and surface projections. Do not infer live freshness, truth, authorship, lifecycle, or verification |
| `absent` | No knowledge projection is available, as in a legacy wiki, deliberate deletion rollback, or a manifest-declared file that is now missing | Return an independently validated surface-v1 view with no knowledge or freshness claims. A reason code distinguishes ordinary absence from a declared artifact that is missing. Absence is not an empty trustworthy knowledge graph |
| `invalid` | An artifact is malformed, schema-invalid, unsafe, unsupported, internally inconsistent, or an uncommitted knowledge file has no usable manifest marker | Never serve the invalid knowledge payload. Reject it, invoke an explicitly authorized rebuild policy, or produce a degraded result |
| `mixed-snapshot` | Two or more present, individually readable commit components disagree with the manifest marker, exact byte hashes, envelope, Markdown/page parity, or each other | Never combine or serve the knowledge payload. Reject, explicitly rebuild all projections from one evaluated snapshot, or produce a degraded result |
| `degraded` | An explicit policy-selected result after an `invalid` or `mixed-snapshot` condition, while an independently validated surface-v1 view is still available | Return only that fallback view plus structured issues and the underlying cause. Knowledge, evidence, graph, freshness, lifecycle, and verification remain unavailable or `unknown` |

`invalid` and `mixed-snapshot` describe detected artifact conditions.
`degraded` describes the deliberately reduced capability returned under a
fallback policy; it is not another spelling of `valid`, `absent`, or an empty
result. If even the fallback surface cannot be independently validated, the
loader must reject instead of degrading.

`absent` describes knowledge availability, not overall artifact integrity.
Ordinary absence with no manifest commitment is clean compatibility. A
`declared-artifact-missing` reason is a manifest-validation failure and remains
a structured, non-clean integrity finding. Compatibility consumers may
continue with independently validated surface-only data because knowledge is
unavailable and its freshness is `unknown`; strict policies may reject or
require repair. A loader must never silently normalize that reason to ordinary
absence.

Read-only API, context, query, site, and MCP paths must not repair files as a
side effect. A rebuild requires an explicit caller policy and a write-authorized
callback or command path.

### Manifest-last commit protocol

The manifest is the logical commit marker for the generated artifact set. It
does not provide a filesystem-wide transaction or a Git commit.

Writers must:

1. reuse one source snapshot and extraction run;
2. finish the intended canonical Markdown changes, then construct the next
   surface bytes, knowledge bytes, evaluated envelope, and manifest commitment
   from that same in-memory run;
3. validate the complete next state and deterministically serialize JSON with
   repository-relative normalized paths, sorted keys, and one trailing newline,
   so the same complete evaluated envelope produces byte-identical output;
4. in dry-run mode, report the plan and stop without any writes;
5. atomically replace the surface projection;
6. atomically replace the knowledge projection;
7. hash the exact persisted bytes of both projections; and
8. atomically replace the manifest last with both projection hashes and the
   evaluated-envelope commitment.

The knowledge envelope also binds the surface projection so that a knowledge
file cannot be paired with a separately generated surface file. Every reader
that serves knowledge must validate the manifest marker and both projections
before returning any knowledge claim.

If a writer fails before the final manifest replacement, the old marker remains
the last committed state. A newly written projection that conflicts with a
prior knowledge-capable marker loads as `mixed-snapshot`; if no knowledge-capable
marker exists, the orphan knowledge file is instead `invalid` and uncommitted.
Neither may be combined with another artifact. Repeating a byte-identical
commit should write nothing.

When both artifacts are written, current bootstrap and normal changed-state
sync finalization order the surface write before the manifest write. The
current manifest does not commit projection hashes, and some surface-only
refresh paths do not rewrite it. That partial ordering is not this protocol.

### Compatibility and rollout

Throughout M0–M2, knowledge-layer work must not change canonical Markdown bytes
beyond existing bootstrap/sync behavior, and the exact
`llm-wiki-surface-index/v1` contract remains the compatibility boundary.

- **M0 — Contract:** this ADR changes no runtime, file format, or canonical
  Markdown.
- **M1 — Generated observations:** add the experimental knowledge projection
  and validated loader. Preserve canonical Markdown bytes, paths, page IDs, MCP
  URIs, and the exact surface-index-v1 contract. Reuse the existing extraction
  run and commit the new projection through the manifest-last protocol.
- **M2 — Native consumption:** add evidence-aware lint, query, context, API,
  and MCP behavior additively. Legacy and absent knowledge remain usable in
  surface-only mode, and all bounded responses disclose totals and truncation.
  M2 is a stop/go gate: do not promote or continue merely because more JSON can
  be generated. At least two native consumers must materially improve behavior
  using the new evidence signals.
- **M3 — Typed graph and section scope:** add evidenced relationship types and
  section-level ownership without changing canonical prose authority.
- **M4 — Governance:** only now introduce explicit authoring for stable
  identity, aliases, lifecycle transitions, and digest-bound reviews, backed by
  a durable governance ledger.
- **M5 — Projections:** enrich site and Obsidian output and add an OKF mapping
  only if a real consumer justifies it; all remain derived.

Lifecycle and governance authoring are explicitly deferred until M4. Before
then, paths, page IDs, and MCP URIs are locators rather than promised stable
identities, and missing lifecycle data is `unknown`.

### Rollback

To roll back the feature, disable knowledge generation and delete the generated
`.llm-wiki-knowledge.json`. Compatibility consumers classify and ignore the
resulting `absent` knowledge state and continue with an independently validated
surface-index-v1 view. Deletion restores pre-feature behavior without changing
canonical Markdown, `.llm-wiki-surface.json`, or their paths.

If the manifest still contains a prior knowledge commitment, the loader reports
a structured `declared-artifact-missing` reason while retaining the `absent`
state. It does not serve knowledge, fabricate freshness, or treat the missing
optional projection as an empty trustworthy graph. A later writer must remove
the obsolete commitment before the artifact set is cleanly committed again.
That cleanup is not required for surface-only rollback consumption.

## Consequences

The knowledge index can make evidence and provenance consistently consumable
without becoming another editing authority. Persisted facts remain honest about
what was observed and when comparison is possible, and the commit marker makes
interrupted multi-file writes detectable.

This adds one generated artifact, cross-artifact validation, and an explicit
failure-state vocabulary. Writers must centralize finalization paths, and
knowledge-aware readers must use the shared loader instead of parsing the JSON
ad hoc. Older surface-only readers remain compatible, although they do not gain
the new integrity or evidence semantics.

## Deferred and out of scope

Except for the v1 taxonomy, compatibility, and KNOW-004 policy above, exact
record fields live in the packaged schema rather than prose in this ADR. This
decision does not implement writers, artifact loaders, a VCS collector, a
redacting exporter, signatures or attestation, define a stable-ID format,
define an OKF mapping, add section-level ownership, or provide filesystem-wide
transactions and cross-process locking. Those decisions require their named
later milestones and tests.
