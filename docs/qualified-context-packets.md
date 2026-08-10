# Qualified context packets

A qualified context packet is a canonical, provider-neutral record of the
bounded context produced by `llm-wiki`. It binds the normalized context
request and response to the source snapshot, available native-knowledge
envelope, generator version and policy, freshness evaluation state, bounds,
warnings, limitations, path-policy receipt, and a domain-separated packet
digest.

Two schema versions are active. Omitting `knowledge_mode` retains
`llm-wiki-qualified-context-packet/v1` and `llm-wiki-context/v1`. Supplying
`knowledge_mode` as `off`, `auto`, or `required` selects
`llm-wiki-qualified-context-packet/v2` and `llm-wiki-context/v2`. Version 2
uses `qualified-context-policy-v2`, separate packet and policy digest domains,
a canonical source-priority binding, and bounded native-knowledge selection.

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
        "knowledge_mode": "auto",
    },
)

packet_bytes = packet.to_bytes()
```

The command-line form uses the existing context command:

```console
llm-wiki context --src-dir . --wiki-dir docs/llm_wiki \
  --budget 32000 --focus changed --knowledge-mode auto --format packet
```

`build_context` and MCP `get_context` return a context response.
`build_qualified_context`, CLI `--format packet`, and MCP
`get_context_packet` return the full qualified packet envelope. The Python and
MCP `query_documentation` operations return a bounded query result, not a
packet.

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

`basis.knowledge` records captured native-knowledge provenance separately from
the requested mode. Consequently, `off` disables selection without pretending
that the recorded basis was absent. `basis.freshness` records either the
evaluated aggregate and digest or an explicit unevaluated reason. A
snapshot-only basis never becomes live-current during validation or
reconciliation.

`auto` returns a read-only fallback when native knowledge is unavailable.
`required` returns a structured `knowledge-required-unavailable` error instead
of a packet. Recovery instructions preserve the resolved source root, wiki
root, active source-selection policy, and explicit external-source
authorization. An unsupported projection schema first requires updating the
installed package and verifying version support; it is not repaired by a
plain sync or a project-local upgrade command.

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
