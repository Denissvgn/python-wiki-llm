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

LLM Wiki uses a native, evidence-aware knowledge contract and a generated,
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

### Live freshness evaluation (KNOW-201 addendum)

Live freshness is computed by one pure comparison service over a validated
knowledge index and already evaluated live values. The live input explicitly
separates present source-content hashes from reliably missing source paths and
supplies locator-scoped observation bases, the effective generation-options
hash, schema version, and normalized producer record. Absence from a supplied
hash map is not evidence that a source is missing. The evaluator performs no
filesystem access, source discovery, extraction, subprocess, network, clock,
or write operation.

Every recorded concept receives exactly one locator-indexed result containing
the computed state, a stable reason code, safe recorded/live basis details,
and whether a live comparison occurred. Counts contain all computed-freshness
states, including zero-valued states. Navigation, change-log, aggregate, and
other structurally unmodeled concepts remain `unknown`.

For a reliable module/entity observation, comparison uses this precedence:

1. missing live evaluation or an unreliable recorded/live observation basis is
   `unknown`;
2. an explicitly and reliably absent mapped source is `source-missing`;
3. incompatible schema, tool, referenced extractor, contributing plugin, or
   generation-options bases are `basis-incompatible`;
4. matching source and concept hashes are `current`;
5. changed source bytes with a matching concept hash are
   `nonsemantic-source-change`;
6. changed source bytes with a changed concept hash are `source-changed`; and
7. identical source bytes producing a different concept hash under an
   otherwise identical basis are `basis-incompatible`, because the record or
   producer may be corrupt or nondeterministic.

Only the concept's referenced extractor is compared, so a change to an
unrelated language extractor does not stale that concept. M1 does not record
per-concept plugin or generation-option attribution, so the complete declared
contributing plugin set and effective generation-options hash are compared
conservatively. Component extensions do not silently redefine compatibility;
core identity, version, safe configuration hash, and limitations do.
An applicable component carrying `version-unknown` or
`configuration-basis-unknown` cannot support a positive freshness result even
when the same unknown marker appears on both sides.

The `current` result is described only as "unchanged since observation."
Freshness results are consumer-side values and are never written back into the
knowledge index, manifest, lifecycle, verification, or review state.

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
- Core collection arrays are semantically unordered. Canonical v1 payloads sort
  producer extractors and plugins by component ID, concepts by locator, and
  relationships by compact canonical JSON of the complete normalized record
  with object keys sorted. Array order inside extension values remains
  significant and is preserved.
- Adding an unqualified core field or kind, removing a field or enum value, or
  changing an existing field's meaning requires a new schema version. A
  producer that needs forward-compatible v1 data must use a namespaced
  extension instead.

#### Lossless Markdown link collection (KNOW-105 addendum)

The knowledge link collector is a pure boundary over the already discovered
canonical page registry, the exact Markdown strings for those pages, and the
already evaluated set of asset paths. It performs no page or asset scan.
Collection retains every supported occurrence, including duplicates, and has
no result cap. Results are ordered by canonical source path and half-open
character location so caller input order cannot affect the output.

V1 observes inline Markdown links and images using the established media
parser. The raw target, normalized target, label, and zero-based half-open
Python string offsets refer to the exact Markdown string later committed by
`page_hash`. Percent escapes, query strings, fragments, case, and backslashes
remain lossless in the observation; URI query/fragment removal, percent
decoding, and Windows-separator conversion occur only for canonical-route
lookup. Reference-style links, raw HTML links, autolinks, and wikilinks are not
added by this slice.

Ordinary fenced code is excluded with an offset-preserving mask. URL-bearing
`click <node> "<target>"` directives inside an explicit Mermaid fence are
collected separately with `mermaid-click` syntax provenance. They remain
Markdown-origin `links_to` relationships on the v1 wire. The knowledge-index
builder preserves the syntax discriminator in the qualified
`llm-wiki/link-syntax` relationship extension. Mermaid callbacks, `href` forms,
and a general Mermaid parser are outside this contract.

Target class and resolution remain independent. Exact unique page routes and
locators resolve as concepts; missing Markdown routes remain unresolved
concepts; fragment-only links resolve as anchors; valid absolute URIs and
`mailto:` targets are external; and known or missing local media retain the
asset class with the corresponding resolution. Empty, unsafe, or unusable
spellings remain explicit malformed or unknown observations rather than being
reported as missing concepts. Protocol-relative targets do not acquire an
invented scheme and therefore cannot claim the v1 absolute `external_uri`
coordinate. The evaluated asset set must be disjoint from active canonical
page routes, and `.md` paths outside the asset namespace remain concept
routes, so precedence cannot vary between collection and construction.

The authority-userinfo rule in the redaction section applies before emission:
the complete affected observation is omitted, including Mermaid clicks. Query
strings and arbitrary extension values are not heuristically scanned in this
slice.

#### Pure knowledge-index construction (KNOW-106 addendum)

The knowledge-index builder consumes one already validated KNOW-104 envelope,
the active canonical page registry, exact Markdown strings, exact surface-index
bytes, in-memory manifest mappings/evidence/tombstones, and already collected
KNOW-105 link observations. Canonical page path is the join key. The builder
requires exact page/content/surface parity and verifies both the LF-normalized
Markdown snapshot commitment and the exact surface-index byte commitment
before constructing records. It does not read a path, rebuild an inventory,
invoke an extractor, inspect Git, use a clock, access the network, or write an
artifact.

Every active page produces exactly one concept and document. The existing
page-kind registry supplies the concept kind, document coordinates, and role;
the surface index supplies the title. Index and log pages remain explicit
document-only concepts with not-applicable structural evidence. Other
non-module/entity pages remain structurally unknown. Module/entity pages use
their manifest evidence basis when available, preserve partial evidence as
unknown without inventing an observation hash, and retain an explicit unknown
facet when no reliable basis exists. A source-missing tombstone may preserve
its last recorded basis, but the builder does not compute or persist a live
freshness verdict.

Each semantic facet commits the exact supplied Markdown UTF-8 bytes in
`page_hash`, mirrors the whole-document surface role, uses unknown authorship,
and labels verification `untracked`. A structural basis produces one matching
`derived_from` observation. Each supplied safe link occurrence produces one
`links_to` observation with its lossless fields, source `page_hash`, and
syntax-provenance extension; multiplicity is preserved. Credential-bearing
authority userinfo causes the complete affected link observation to be
omitted. Surface `outgoing_internal_links` remains a separate lossy projection
and is never used to infer knowledge relationships.

Builder validation rejects duplicate active routes or locators, unsafe
coordinates, page/surface/evidence mismatches, undeclared extractor
references, invalid link locations, and resolved internal targets outside the
active registry. Each link is re-parsed at its exact source offsets; its
lossless fields, syntax, and deterministic non-asset classification must match
that occurrence and its normalized target. Broken but unambiguous internal
links remain recorded as unresolved. Construction then round-trips through the
typed v1 model so its cross-record validation and canonical collection
ordering remain the single wire-contract authority.

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

Command orchestration also excludes the exact target paths of
`.llm-wiki-surface.json`, `.llm-wiki-knowledge.json`, and
`.llm-wiki-manifest.json` from this status evaluation. Those generated files
commit the evaluated envelope or are committed by it, so observing their own
pending replacement would make the envelope recursively depend on its prior
output state. The exclusion is file-specific: canonical Markdown, assets, and
every other staged, tracked, deleted, or non-ignored untracked path remain
material to `working_tree`. A target path outside the evaluated Git work tree
does not create a broader exclusion.

Sync and migration capture this repository evidence once, after evaluating the
run inputs and before writing canonical Markdown or generated projections.
Apply and dry-run reuse that same pre-write snapshot, including when the source
root and wiki are sibling directories in one Git work tree.

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

#### Concept-scoped structural observations

_KNOW-102 addendum._

Module and entity observation hashes use compact canonical JSON with sorted
object keys, UTF-8 encoding, and a `scope` member in the normalized payload.
Source path, exact source-content hash, and extractor identity remain separate
basis dimensions; they are not folded into the concept observation. Arrays
retain extractor order and multiplicity because declaration order, repeated
observations, and one-based same-name occurrence coordinates can be material.

A module observation contains the source language, an optional declared module
name, imports, module-facing class/type declaration summaries, and top-level
function signature summaries. TypeScript and JavaScript module observations
also include the exports, constant summaries, and module-call signals rendered
by their module concept. Class/type summaries contain declaration identity and
module-facing kind, inheritance, and target facts, not attributes or methods.
Consequently an entity edit changes its module observation only when it changes
one of those module-facing declaration facts. Import and top-level signature
changes always change the module observation.

An entity observation selects exactly one class/type declaration by name and
one-based same-name occurrence within the source file. The occurrence is part
of the normalized payload, so structurally identical duplicate declarations
remain distinct. Its structural declaration and contract data are retained,
while semantic prose, call/data-effect details, and the location-only keys
`line`, `end_line`, and `decorator_line` are excluded recursively. The same
location and prose exclusions apply to module observations. A line-only source
edit can therefore change `source_content_hash` while leaving
`concept_observation_hash` unchanged.

Completeness is trusted current-run input, not inferred from optional inventory
fields: empty rich collections are omitted by some deep extractors, while the
prepared Haskell inventory is intentionally sparse. Builders must explicitly
identify complete inventory. Slim input, an unsupported language, malformed
inventory, or an absent entity occurrence produces an explicit unknown result
without a concept-observation hash. The existing manifest v4 file-level
semantic hash remains a separate compatibility commitment and is unchanged.

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

URI authority userinfo in `external_uri`, `raw_target`, or
`normalized_target` is always treated as unambiguously credential-bearing and
is invalid in the native v1 core contract. This covers username-only and
username/password authorities in absolute and protocol-relative targets;
`mailto:` targets and ordinary `@` characters outside URI authority are not
affected. A builder encountering such an affected lossless link observation
must omit the entire relationship rather than redact a target and falsely
present the result as lossless.

| Profile | Required boundary |
|---|---|
| `internal` | May retain configured-public and normalized-VCS identities, evaluated revision and tree state, actor identity, producer evidence, raw lossless link observations, and schema-valid extensions. It still forbids credentials, raw remotes, machine-local absolute filesystem paths, environment dumps, and raw plugin settings. |
| `public-portable` | Retains repository identity only when trusted current-run configuration establishes source `configured-public`; otherwise emits `unknown`. It retains the required identity-source marker, emits unknown revision and tree state, strips or coarsens local actor identity, drops other extensions by default, and omits private plugin records and unreviewed private links or evidence. Only an explicit application-owned public allowlist may retain additional fields. |

A public projection drops an entire observation when a required lossless core
field contains credentialed or private material; it does not rewrite the raw
observation into something falsely presented as lossless. Exact public
allowlists, exporter mechanics, and heuristic secret detection in query strings
or arbitrary extension values belong to KNOW-501. The packaged native JSON
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

The shared loader uses the following state vocabulary. Stable reason codes
may refine a state, including distinguishing malformed data from an unsupported
future schema version.

| State | Meaning | Required loader behavior |
|---|---|---|
| `valid` | Knowledge, surface, and manifest schemas validate; safe paths, the normalized Markdown snapshot, and required page parity hold; exact projection byte hashes and envelope commitments agree | Return the committed knowledge and surface projections. Do not infer live freshness, truth, authorship, lifecycle, or verification |
| `absent` | No knowledge projection is available and no complete manifest commitment declares one, as in a legacy wiki or a completed deletion rollback | Return an independently validated surface-v1 view with no knowledge or freshness claims. Absence is not an empty trustworthy knowledge graph |
| `invalid` | An artifact is malformed, schema-invalid, unsafe, unsupported, internally inconsistent, uncommitted, or declared by the manifest but missing | Never serve the invalid knowledge payload. Reject it, invoke an explicitly authorized rebuild policy, or produce a degraded result |
| `mixed-snapshot` | Two or more present, individually readable commit components disagree with the manifest marker, exact byte hashes, envelope, Markdown/page parity, or each other | Never combine or serve the knowledge payload. Reject, explicitly rebuild all projections from one evaluated snapshot, or produce a degraded result |
| `degraded` | An explicit policy-selected result after an `invalid` or `mixed-snapshot` condition, while an independently validated surface-v1 view is still available | Return only that fallback view plus structured issues and the underlying cause. Knowledge, evidence, graph, freshness, lifecycle, and verification remain unavailable or `unknown` |

`invalid` and `mixed-snapshot` describe detected artifact conditions.
`degraded` describes the deliberately reduced capability returned under a
fallback policy; it is not another spelling of `valid`, `absent`, or an empty
result. If even the fallback surface cannot be independently validated, the
loader must reject instead of degrading.

`absent` describes clean knowledge unavailability: no projection and no
complete manifest commitment. A missing projection named by a complete marker
is instead `invalid` with `declared-artifact-missing`; the loader never silently
normalizes that integrity failure to ordinary absence. The default `reject`
policy raises with structured issues. `rebuild` invokes one explicitly supplied
callback at most once, rereads all artifacts, and succeeds only if the reread is
`valid`. `degraded` may return only an independently validated, page-current
surface view and records the original `invalid` or `mixed-snapshot` state; it
never exposes knowledge from the failed set.

Read-only API, context, query, site, and MCP paths must not repair files as a
side effect. A rebuild requires an explicit caller policy and a write-authorized
callback or command path.

The KNOW-101 extraction retained manifest v4 fields and behavior while moving
persistence and evidence primitives to service-level boundaries shared by
bootstrap, sync, lint, migrate, and team operations. `commands.sync_cmd`
continues to re-export `SyncManifest` and its manifest constants for one
compatibility cycle. Artifact JSON is UTF-8 with sorted keys, LF formatting,
and one trailing newline, and is replaced atomically through a unique
same-directory temporary file whose cleanup is guaranteed on failure.

### Manifest v5 operational evidence state

_KNOW-103 addendum._

Manifest v5 preserves the complete v4 `sources`, `surfaces`, and
`generation_inputs` values and adds only rebuildable operational state:

| Field | Meaning |
|---|---|
| `page_source_mappings` | Last observed module/entity source coordinate keyed by canonical page path. Entity coordinates include the exact name and one-based occurrence |
| `evidence_baselines` | Known or explicitly unknown evidence for active module/entity pages. Known and partial bases use the KNOW-102 scope, relative source path, extractor reference, source-content hash, and optional concept-observation hash |
| `tombstones` | Evidence retained for stale pages. A `source-missing` tombstone requires the last valid known basis; otherwise the tombstone is `unknown-provenance` with a machine-readable unknown reason |
| `artifact_hashes` | Optional all-or-none exact-byte hashes for the surface index, knowledge index, and evaluated envelope |

The page path is an operational locator, not a stable UID. Module mappings
contain only a source path. Entity mappings additionally contain the exact
entity name and occurrence; duplicate declarations are never collapsed to a
name-only mapping.

Loading manifest v4 deterministically produces v5 state without reading source
or Markdown. Its existing fields are retained, recoverable page/source
mappings are copied, and their evidence is explicitly
`legacy-manifest-no-evidence`. No tombstone or artifact commitment is invented.
Legacy ambiguous duplicate mappings are left unrecoverable rather than guessed.
Saving writes v5.

Reconciliation operates on the already evaluated inventory, supplied
concept-observation bases, the prior manifest, and an explicit set of retained
page paths. A retained page whose prior known basis loses its source becomes a
`source-missing` tombstone with that exact basis. Missing, invalid, deleted, or
previously unknown manifest evidence remains `unknown-provenance`; repair and
reseed never promote it to source-missing and never infer provenance from page
text. If the exact source coordinate remains live under a different canonical
page path, the retained old page becomes `unknown-provenance` with
`source-mapping-changed`; it is never misclassified as `source-missing`. If a
page is no longer retained, its operational tombstone may be dropped.
Reappearance removes the tombstone and restores a prior known basis only when
its mapping and source-content hash still match.

Before a retained source-missing basis reuses an extractor component ID that
is active in the next envelope, generation compares the prior committed
tool and referenced extractor records with their current normalized versions,
configuration hashes, limitations, and extensions. If either prior record is
unavailable or differs, the stale page is retained as `unknown-provenance` with
`producer-basis-incompatible`; it is never attributed to the upgraded
same-ID producer.

Chunked migration carries regeneration proof across process boundaries in the
temporary `.llm-wiki-migration-progress.json` receipt. Each entry commits the
relative structural page, source-content hash, and exact written page bytes.
A later chunk promotes the page only when those bytes are unchanged and still
equal the current deterministic migration output. The receipt is written
atomically before returning from a chunk and removed only after the final
manifest-last artifact commit succeeds.

`artifact_hashes` contains `surface_index_hash`, `knowledge_index_hash`, and
`evaluated_envelope_hash`. The group is omitted unless all three canonical
SHA-256 values describe one complete commit. Migration, repair, reseed, and
ordinary manifest reconstruction clear it. The manifest-last writer derives and
installs it only after both canonical projections have been atomically replaced
and their persisted bytes verified. Loading and saving an unchanged v5 manifest
preserves a complete commitment without rehashing files.

Manifest state contains no stable UID, alias, lifecycle decision, review event,
signature, timeless freshness verdict, or inferred governance fact.

### Evaluated bundle envelope

_KNOW-104 addendum._

`llm-wiki-knowledge/v1` and its existing `BundleRecord` wire shape remain
unchanged. The builder produces the existing `repository`, `snapshot`, and
`producer` records and validates them through the v1 typed contract. The
normalized extracted-inventory commitment, for which v1 has no unqualified
core field, is stored at
`bundle.snapshot.extensions["llm-wiki/inventory-hash"]`. It is a required
canonical SHA-256 value on application-built envelopes.

The separately hashable evaluated envelope is
`llm-wiki-evaluated-envelope/v1` and contains exactly its `schema_version` and
the validated v1 `bundle`. Its deterministic JSON uses UTF-8, sorted object
keys, LF line endings, and one trailing newline. The
`evaluated_envelope_hash` committed by manifest v5 is the SHA-256 of
those exact serialized bytes.

Structured commitments use compact canonical JSON with sorted object keys,
UTF-8 encoding, and an explicit top-level `domain` member. Their v1 domain tags
and payloads are:

| Commitment | Domain tag and framed payload |
|---|---|
| Selected source/configuration inputs | `llm-wiki/source-snapshot/v1`; `inputs` records contain `kind`, repository-relative POSIX `path`, and exact `content_hash`, sorted by kind and path |
| Normalized extracted inventory | `llm-wiki/inventory-snapshot/v1`; `inventory` retains material array order and multiplicity while object keys serialize canonically |
| Canonical Markdown | `llm-wiki/markdown-snapshot/v1`; `pages` records contain canonical path and the hash of LF-normalized UTF-8 content, sorted by path |
| Effective generation options | `llm-wiki/generation-options/v1`; `options` contains the complete application allowlist with effective defaults |
| Producer configuration | `llm-wiki/component-configuration/v1`; `configuration` contains only the complete safe behavior-affecting allowlist |
| Aggregate evidence | `llm-wiki/aggregate-input/v1`; `inputs` preserves caller-supplied contributor order and multiplicity |

The surface-index commitment remains the raw SHA-256 of its exact generated
bytes and is not placed in a structured frame. Source/configuration inputs are
captured before envelope construction and include every selected language,
Docker, Compose, YAML, package, OpenAPI, plugin, and selection input actually
consumed by the run. Each physical repository path appears exactly once;
assigning the same path to multiple input kinds or supplying conflicting
digests is invalid. Absolute checkout roots, timestamps, caches, completion
order, and other machine-local state are excluded. Caller extensions fail
closed on machine-local absolute paths or `file:` URIs. Inventory producers
must remove machine-local extractor state at their normalization boundary;
the envelope builder validates repository-relative top-level source keys and
requires every inventory source to be present in the selected input set while
retaining valid slash-prefixed semantic values such as API routes and prose.

`consumed_inputs_from_captured_hashes()` is the no-I/O adapter for bootstrap and
sync orchestration. It requires identical path sets for exact
captured content hashes and selected-kind candidates. Overlapping candidates
use the fixed precedence OpenAPI, Compose, Docker, package, plugin, selection,
generic YAML, then language source, so a Compose YAML file is committed once
with one stable classification. KNOW-109 and KNOW-110 must populate this
capture during the existing evaluated run, including `.gitignore` and other
selection inputs, OpenAPI and package/configuration files, and enabled plugin
metadata; they may not reconstruct it with a later source scan.

`build_evaluated_envelope()` is pure over supplied repository evidence,
content commitments, normalized inventory, Markdown content, exact surface
bytes, effective options, and producer metadata. It performs no scan, file
read, write, subprocess, network request, helper execution, plugin activation,
or LLM call. `collect_git_repository_evidence()` is a separate,
application-selected local collection step. It may invoke local Git but never
contacts a remote or scans source content; its raw remotes are inert input and
are never serialized. Collection ignores ambient system/global Git
configuration and local include files for identity selection, disables
filesystem-monitor helpers for status, and distinguishes detached HEAD from an
unevaluable branch lookup so failures cannot silently fall back to `origin`.

Repository identity selection remains configured public identity, then the
current branch's actually configured tracking remote, then `origin`, then the
sole configured remote, otherwise `unknown`. An invalid configured public
identity is an error and never falls through. A selected missing or unusable
remote produces `unknown` rather than another fallback. HTTPS, SSH, and
SCP-like remotes remove
scheme, user information, credentials, query, fragment, default port, trailing
slash, and one trailing `.git`; local/file remotes, non-default ports,
backslashes, malformed escapes, and empty or dot path segments are unusable.
The host is lowercase and later path-segment case is preserved.

The evaluated revision is `git:` plus a complete lowercase 40- or 64-hex
object ID when available, otherwise `unknown`. Working-tree evaluation is
independent. After excluding only the three exact application-owned artifact
paths described above, any remaining staged, tracked, deleted, or non-ignored
untracked change is `dirty`; a successful empty evaluation is `clean`; and
non-Git, failed, or otherwise unevaluable state is `unknown`.

Generation options and component configuration are application-owned safe
allowlists. They must exclude raw secrets; unknown option keys, omitted
effective defaults, and machine-local absolute paths are rejected rather than
incorporated. The runtime option allowlist includes data-flow enablement,
workflow enablement, and dependency-graph detail even though those policies
are not part of the stable surface-index v1 payload. Bootstrap persists that
cross-command policy under
`generation_inputs["llm-wiki/generation-options/v1"]` so later sync and
migration runs reproduce the same option commitment.
Unavailable component versions serialize as `version: "unknown"` with the
stable `version-unknown` limitation. An analyzer whose complete safe
configuration basis is unavailable omits `configuration_hash` and includes
`configuration-basis-unknown`.

Plugin producer evidence is projected only from selected installed component
metadata and explicitly supplied safe settings. Stable plugin ID and version
are retained; behavior-bearing component fields are hashed canonically. A
missing per-plugin safe-settings entry means the complete configuration basis
is unavailable; only an explicit empty object establishes known-empty
settings.
Installation source, `plugin_dir`, installation time, raw lock records,
credentials, and arbitrary settings are excluded. Producer and plugin records
describe what the application already selected and ran; they never select or
load code from artifact metadata.

`hash_aggregate_inputs()` exposes the M3 hook for ordered cross-file evidence.
It is domain-separated, preserves contributor order and duplicates, and is
not an additional bundle snapshot hash.

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

`build_knowledge_commit_plan()` is the validation boundary: it accepts only
canonical surface and knowledge bytes, checks their page and evidence parity
with the supplied next-state manifest, derives the evaluated-envelope hash, and
plans created, updated, or unchanged results without writing. Active evidence
sources require canonical current source hashes; inactive legacy source records
may be preserved without being promoted into the active commitment.
`commit_knowledge_artifacts()` applies that immutable plan in the order above,
verifies persisted projection bytes before replacing the marker, and exposes
fault seams after each actual replacement. Dry-run invokes no write or fault
seam.

If a writer fails before the final manifest replacement, the old marker remains
the last committed state. A newly written projection that conflicts with a
prior knowledge-capable marker loads as `mixed-snapshot`; if no knowledge-capable
marker exists, the orphan knowledge file is instead `invalid` and uncommitted.
Neither may be combined with another artifact. Repeating a byte-identical
commit writes nothing and preserves all three byte streams.

Writing either projection or the manifest independently is outside this
protocol and does not establish a committed knowledge state. Callers that
produce knowledge must use the shared planning and commit boundary rather than
compose the older single-artifact writers.

### Compatibility and rollout

Throughout M0–M2, knowledge-layer work must not change canonical Markdown bytes
beyond existing bootstrap/sync behavior, and the exact
`llm-wiki-surface-index/v1` contract remains the compatibility boundary.
The richer KNOW-105 collector is deliberately parallel to, not a replacement
for, the surface index's legacy resolved-only, deduplicated link list. Its
stricter fence and Mermaid observation policy therefore cannot change surface
index v1 bytes.

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

To roll back the feature cleanly, disable knowledge generation, delete the
generated `.llm-wiki-knowledge.json`, and clear the manifest artifact commitment
through an authorized writer or migration path. Compatibility consumers then
classify the result as `absent` and continue with an independently validated
surface-index-v1 view. This restores pre-feature behavior without changing
canonical Markdown, `.llm-wiki-surface.json`, or their paths.

If only the knowledge file is deleted while the manifest still contains its
commitment, the loader reports `invalid` with the structured
`declared-artifact-missing` reason. It does not serve knowledge, fabricate
freshness, or treat the missing projection as an empty trustworthy graph. An
explicit degraded policy may still consume an independently validated,
page-current surface. A later writer must remove the obsolete commitment before
the artifact set returns to clean `absent` state.

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
record fields live in the packaged schema rather than prose in this ADR. The M1
implementation provides the deterministic writer and validated loader described
above. It does not provide a redacting exporter, signatures or attestation, a
stable-ID format, an OKF mapping, section-level ownership, filesystem-wide
transactions, or cross-process locking. Those capabilities require their named
later milestones and tests.
