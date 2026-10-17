# Qualified context packets

A qualified context packet is a canonical, provider-neutral record of the
bounded context produced by `llm-wiki`. It binds the normalized context
request and response to the source snapshot, available native-knowledge
envelope, generator version and policy, freshness evaluation state, bounds,
warnings, limitations, path-policy receipt, and a domain-separated packet
digest.

Two schema versions are supported. Starting with 3.0.0, omitted protocol and
knowledge-mode options select `llm-wiki-qualified-context-packet/v2` and
`llm-wiki-context/v2`, with `knowledge_mode: "auto"`. Supplying `knowledge_mode`
as `off`, `auto`, or `required` also uses this current contract. Version 2
uses `qualified-context-policy-v2`, separate packet and policy digest domains,
a canonical source-priority binding, and bounded native-knowledge selection.

### Compatibility and migration

Version 3.0.0 changes the omission behavior provided by 2.5.0. Update packet
consumers to accept v2 before upgrading. Normal CLI packet flags, versionless
CLI packet request files, the Python packet API, and MCP packet calls share
the current default. They disclose unavailable native knowledge through the
qualified fallback; reads never initialize or upgrade storage.

API and CLI applications requiring canonical v1 packets must send an explicit
`protocol: "llm-wiki-context/v1"` request and omit `knowledge_mode`. This returns
the `llm-wiki-qualified-context-packet/v1` schema. Explicit raw v2 requests must
include one of the three exact lowercase mode values;
omitting the protocol uses the library's current defaults. Null and unknown
versions remain invalid. Supplying both a packet request field and a separate
Python mode argument is invalid. MCP `get_context_packet` uses v2; a client
that only understands v1 must be updated before upgrading its server.

`context_knowledge_contract()` from
`llm_wiki_cli.services.context_knowledge_contract` returns the current
`llm-wiki-context-knowledge-contract/v2` descriptor, including packet defaults
for each interface. Plain context responses retain their separate compatibility
contract. The frozen v1 descriptor remains available through
`context_knowledge_contract(schema_version="llm-wiki-context-knowledge-contract/v1")`;
its validator accepts both supported descriptor schemas without conversion.
Selecting a descriptor does not change server behavior.

The packet schema changed because v2 adds evidence-selection and response
semantics. A v1 parser must not reinterpret v2 bytes, and a v2 producer must
not add mode fields to a v1 packet. Structural validation continues to reject
unknown schema versions rather than guessing a compatible shape.

Packet JSON uses sorted object keys, UTF-8, finite JSON numbers, compact
separators, and exactly one final line feed. The `packet_id` is a
version-specific, domain-separated SHA-256 digest of the canonical semantic
packet excluding only `packet_id`. Rebuilding from the same normalized request
and captured semantic read produces the same bytes.
Observation times, absolute input roots, inode values, and other
machine-local capture details are not part of those bytes.

The assurance level is `content-integrity`. It means that structural
validation can detect a change to the retained canonical bytes and their
declared internal bindings. It is not an authenticity, authorization,
historical durability, or external-witness claim.

## Construction

Python callers can build the packet in memory:

```python
from llm_wiki_cli.api import build_qualified_context

packet = build_qualified_context(
    src_dir=".",
    wiki_dir="docs/llm_wiki",
    request={
        "budget_tokens": 32000,
        "focus": ["changed", "neighbors"],
        "format": "json",
        "filters": {},
        "prefer_fresh": False,
    },
)

packet_bytes = packet.to_bytes()
```

The command-line form uses the existing context command:

```console
llm-wiki context --src-dir . --wiki-dir docs/llm_wiki \
  --budget 32000 --focus changed --format packet
```

For filters or a reusable request, put the semantic options in `context-request.json`:

```json
{
  "budget_tokens": 32000,
  "focus": ["all"],
  "format": "json",
  "filters": {"language": "python"}
}
```

```console
llm-wiki context --request context-request.json --format packet
```

For v1/v2 requests, `--format packet` selects canonical packet delivery while
the file's `format` controls its inner JSON or Markdown representation. Other
explicit format flags must agree with the request. Put budget, focus,
freshness preference, and knowledge mode in the file; command-line overrides
are rejected before reading source or wiki content. A v3 request continues to
own its outer format, including its packet-and-accounting envelope.

The source directory must exist and be a directory. An existing empty source
is allowed; a missing source is an unavailable input. Missing optional wiki
knowledge retains the selected mode's fallback behavior.

`build_context` and MCP `get_context` return a context response.
`build_qualified_context`, CLI `--format packet`, and MCP
`get_context_packet` return the full qualified packet envelope. The Python and
MCP `query_documentation` operations return a bounded query result, not a
packet.

Opt-in `--budget-mode exact --tokenizer tokenizer.json --format packet` uses
the `llm-wiki-context/v3` complete-output budget envelope. Its `packet` field
contains an existing qualified v2 packet; v3 does not define another qualified
packet schema. The outer accounting includes the nested packet, metadata, and
final newline. To use the existing packet validator, serialize the nested
packet with the canonical JSON rules above. The outer change-selection and
budget accounting fields are outside that packet's digest. See the
[context command](cli-reference.md#context) for counter identity, explicit changes,
estimated mode, and cannot-fit behavior.

The nested packet ID must not be used as an identity for the complete v3
envelope. Changing outer accounting or change-selection metadata does not
change that ID.

Construction captures one source inventory and one wiki and knowledge read
view. Both the response and evidence basis are derived from that view. It
checks the captured source and wiki anchors again before returning. A
concurrent mutation rejects construction instead of returning a detached
packet. Construction does not refresh or persist native artifacts and does
not call a model provider. Project-local extractor plugins are not loaded;
packet construction uses the built-in source adapters only.

Version 2 rejects symbolic links anywhere in the captured wiki tree. A link
that already exists is a path-policy error; a link introduced after the first
anchor is a concurrent-mutation error. Version 1 retains compatibility for
unread, noncanonical links, while canonical wiki pages and managed artifacts
are always read without following an escaping link.

The path-policy receipt reports counts for classified structural paths,
portable identities, public URIs, free text, and opaque values. Structural
paths must be normalized repository-relative paths. Slash-like strings in
source text, Markdown, URLs, and API routes remain opaque content rather than
being rejected merely because they resemble paths. The receipt explicitly
does not establish the absence of arbitrary sensitive content.

## Validation and reconciliation

Consumers must also check that the packet's normalized request is the request
they intended to use. Live reconciliation rebuilds the request embedded in the
packet; a `current` result does not independently establish consumer intent.

Packet API failures retain the existing `InvalidRequestError` and
`WorkspaceStateError` catch points and expose stable `code` and `details`
attributes. `PathPolicyError` remains an alias of `InvalidRequestError`.

| Code | Meaning |
|---|---|
| `invalid-request` | A request or packet-operation option is invalid. |
| `malformed-context-packet` | Supplied bytes fail canonical structure or integrity checks. |
| `unsupported-context-packet` | The packet declares an unsupported schema version. |
| `path-policy-error` | A source, wiki, or structural packet path violates the allowed policy. |
| `context-packet-unavailable` | A required input or read capability is unavailable. |
| `context-read-mutated` | Source or wiki state changed during the read; retry is required. |
| `workspace-state-error` | The workspace could not be read. |
| `maintenance-authority-unavailable` | Declared ordinary maintenance authority is missing, invalid or inconsistent; complete matching recovery is required. |
| `knowledge-required-unavailable` | Required native knowledge cannot be supplied; details explain the reason. |

Field-oriented failure records omit resolved machine roots and offending
untrusted values. Chained exceptions remain available for local debugging.
Packet CLI failures leave stdout empty and emit a JSON error record on stderr,
with exit code `1`; usage errors retain exit code `2`. The raw non-packet
protocol retains its existing JSON error envelope. MCP semantic packet errors
use `isError: true` with structured code/details and JSON text content;
transport argument validation remains the MCP SDK's responsibility.

Owned-authority refusal uses `maintenance-authority-unavailable` with the
original safe `maintenance-*` cause code, unavailable native evidence and a
bounded `recovery` object. The Python packet API retains its
`InvalidRequestError` catch point for this refusal. Full loader or maintenance
causes remain chained locally; structured results omit raw metadata and machine
roots. Raw and budgeted packet failures carry the same recovery requirements.

The recovery object supplies an `argv_template` for `llm-wiki maintenance recover`.
Bind `wiki_dir` to the original request's wiki root, `recovery_dir` to a complete
matching committed backup, and `expected_adoption_id` to the same existing
identity from a validated immutable marker or that matching backup. These are
caller-supplied facts; the reader does not discover a backup or allocate an ID.
Keep the original source root and selection for subsequent owning sync and
validation, and keep recovery bytes outside the wiki and source inputs.

A complete backup is necessary but does not guarantee that the current recovery
operation accepts the damaged tree. Missing projection files, conflicting
authored edits or newer authority can cause refusal; preserve that refusal and
the exact bytes for authorized complete restoration. Do not initialize another
marker, mix backups, or enable interrupted-recovery modes to bypass a guard.
The diagnostic grants no write permission and a read never repairs authority.
Required native evidence remains unsatisfied. Packet `off` retains its packet
integrity requirements; an explicitly source-only task remains a separate route.

Structural validation is offline:

```python
from llm_wiki_cli.api import validate_context_packet

validation = validate_context_packet(packet_bytes)
assert validation.valid
```

It rejects invalid UTF-8, duplicate keys, non-finite numbers, unsupported
schema or assurance values, unknown core fields, non-canonical bytes, digest
mismatches, inconsistent response bindings, and path-policy violations. A
successful structural result reports freshness as unevaluated because packet
bytes alone cannot prove that the source or knowledge is still current.

Live reconciliation performs a new read of caller-designated roots:

```python
from llm_wiki_cli.api import reconcile_context_packet

result = reconcile_context_packet(
    packet_bytes,
    src_dir=".",
    wiki_dir="docs/llm_wiki",
)
```

Each evaluated facet reports `matches_expected` separately from `current`.
Official read-only reconciliation may report a facet as current. Comparison
with an arbitrary caller-provided basis can report only `matches_expected`;
its `current` value is always null. Aggregate currentness uses the named
complete reconciliation policy. A current reconciliation means the packet's
bindings match the fresh read; it does not mean every concept has a current
freshness state. Consumers should inspect the packet's freshness counts. If
native freshness cannot be evaluated, the packet records the exact disclosure
`unevaluated (snapshot-only read)` and aggregate currentness remains
unevaluated rather than being fabricated.

## Explicit knowledge in version 2

The normalized request always carries `knowledge_mode` in version 2. The
response includes a `knowledge` outcome with mode, status, availability,
reason, selection flag, freshness-evaluation flag, independent bounds for
concepts, pages, and relationships, and a fallback disclosure. A selected
result also carries compact concepts, canonical page coordinates, typed and
native relationships, and bounded relationship-analyzer coverage. Raw
projection diagnostics, hashes, samples, and unsafe link text are not placed
in the selection.

The three modes are transport-independent:

| Mode | Packet response behavior |
|---|---|
| `off` | `response.knowledge` is disabled and not evaluated. No native selection is constructed, but `basis.knowledge` still records the captured projection state independently. |
| `auto` | Ready knowledge is selected. Unavailable knowledge returns a successful fallback with the exact availability, reason, bounds, and ordered fallback evidence. |
| `required` | Ready knowledge is selected. Unavailable knowledge raises `knowledge-required-unavailable`; no packet is emitted. Ready snapshot-only knowledge is allowed and remains explicitly unevaluated for live freshness. |

`basis.knowledge` records captured native-knowledge provenance separately from
the requested mode. Consequently, `off` disables selection without pretending
that the recorded basis was absent. `basis.freshness` records either the
evaluated aggregate and digest or an explicit unevaluated reason. A
snapshot-only basis never becomes live-current during validation or
reconciliation.

`auto` returns a read-only fallback when native knowledge is unavailable.
Depending on the captured state, its stable reason is
`knowledge-projection-not-present`,
`policy-selected-surface-only-fallback-after-invalid`,
`policy-selected-surface-only-fallback-after-mixed-snapshot`,
`surface-validation-failed`, `knowledge-basis-incompatible`,
`governance-missing`, or `knowledge-schema-version-unsupported`. A ready view
with no relevant concepts instead returns a successful fallback for both
`auto` and `required`, with availability `ready` and reason
`no-relevant-native-selection`.

For unavailable knowledge, `required` returns a structured
`knowledge-required-unavailable` error instead of a packet. Recovery
instructions preserve the resolved source root, wiki root, active
source-selection policy, and explicit external-source authorization. An
unsupported projection schema first requires updating the installed package
and verifying version support; it is not repaired by a plain sync or a
project-local upgrade command. A missing declared governance ledger must be
restored from version control or an owner-approved backup before regeneration;
fallback never initializes governance.

`prefer_fresh` remains false by default and does not control knowledge
selection. When requested, `response.ranking_policy` discloses whether a
current-first ordering was applied within an existing relevance tier under
budget pressure. It never filters stale content or upgrades currentness into
truth, review, or runtime evidence. The field is absent when the preference
was not requested.

Source and native results are bounded independently. Version 2 returns at most
20 concepts, 20 pages, and 40 relationships, with truthful total, returned,
and truncated values. Analyzer limitation codes are also bounded and include
their own bounds. If a legal selected result approaches the serialized
transport limit, the lowest-ranked relationships, then pages, then concepts
are removed deterministically. If even one concept cannot fit, `auto` reports
`knowledge-result-exceeds-size-limit` as a bounded fallback and `required`
reports the corresponding structured error.

## Explicit non-claims

Qualified context packets must not claim:

- that the source or packet author is authenticated;
- that repository transfer is authorized;
- that the packet is owner-resistant or tamperproof;
- that runtime state remains current after packet construction;
- that static evidence proves live production behavior;
- that no arbitrary secret or unregistered identity exists in source text; or
- that the context improves an agent.

It supports deterministic validation of the named internal bindings under the
declared assurance level. It does not prove the external truth of those
bindings.

## Limits and evolution

The version 1 parser accepts at most 16 MiB. Version 2 accepts at most 2 MiB.
Both accept at most 64 nested JSON levels, 250,000 JSON values, and two million
characters in any one string. They reject duplicate keys, unknown core fields,
noncanonical request defaults or ordering, and unknown schema versions. These
limits apply before any live source read.

Each version's core field set is exact. Adding a new required semantic field,
renaming or removing a field, changing a field's meaning, or changing the
canonical numeric or digest rules requires a new packet schema version.
Machine-local operational receipts and optional persistence metadata remain
outside the canonical packet.
