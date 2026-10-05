# Making a change

Identify the exact implementation, read the evidence that affects the intended
edit, then verify the saved change through the coding host. Wiki observations
help locate and qualify that work; they do not approve a patch.

## Resolve one owner

Start from an exact source-root-relative coordinate. For the
[orientation example](orientation.md#start-without-a-wiki), it is `app.py:limit`.
A repeated declaration can require a qualified owner and occurrence, such as
`app.py:Batch.cap#2`. A short name can be ambiguous. Do not select one match
because its title looks plausible.

A source-contract requirement records the declaration's signature and captured
source facts. Add callers or callees only when useful, then read their static
coverage and source-selection limits. A selected-source read cannot establish
that no other module calls the declaration.

For an explicitly authorized full source inventory, save this as
`symbol-query.json` in the example workspace:

```json
{
  "operation": "symbol",
  "value": "app.py:limit",
  "allow_full_inventory": true,
  "limit": 20
}
```

```bash
llm-wiki query --request symbol-query.json --src-dir src --wiki-dir wiki
```

This broader route is an explicit cost choice. Check `found`, `ambiguous`,
`matches`, caller/callee coverage and unresolved endpoints before using it.
Python `api.query_documentation` accepts the same operation object; MCP wraps
it under `request`. Reuse one built documentation service for related live graph
questions when appropriate rather than rebuilding its inventory each time.

The [call resolver](../modules/python_calls.md), at
`src/llm_wiki_cli/services/python_calls.py:resolve_python_call`, recognizes
supported local/imported calls and eligible constructed receivers. Factories,
dynamic dispatch, uncertain imports or modified class dispatch can remain
unresolved. The [graph query service](../modules/documentation_queries.md), at
`src/llm_wiki_cli/services/documentation_queries.py:DocumentationGraphQueryService.callers`,
retains that uncertainty. Call-site and constructor locations describe static
source observations; they do not prove the receiver's runtime type.

## Inspect the decisive source

Read the declaration body and the relevant callers, defaults, global values and
collaborators before editing. Use the exact source locations and canonical
module links supplied by the evidence. An empty bounded caller list means no
caller was returned in that scope, not that no runtime caller exists.

Make only the authorized change. The host decides which behavioral checks are
needed for the changed contract, including boundary cases and dependencies.
Static signatures and diagrams cannot substitute for that verification.

## Compare observations without overstating them

| Observation | What a matching result supports |
| --- | --- |
| Source-byte commitment | The captured file bytes match that commitment. |
| Recorded structural observation | The comparable recorded declaration structure matches; a body change can still matter. |
| Executable syntax observation | The selected module, class or callable's normalized syntax matches under a compatible producer and scope. |

The [implementation comparison](../modules/implementation_evidence.md), at
`src/llm_wiki_cli/services/implementation_evidence.py:compare_implementation_observations`,
keeps source, executable and documentation changes separate. Module scope covers
module syntax, class scope includes its methods, and a callable comparison does
not cover unrelated globals or dependencies. A matching method observation can
coexist with a changed module observation and changed runtime behavior.

Missing, incompatible or bounded observations remain qualified unavailable or
truncated. Matching syntax is not semantic approval, security assurance or proof
that every dependency behaves the same. Do not treat structural freshness as an
executable or runtime verdict.

## Re-read and hand off

After saving changes, capture the task again and compare coverage, source basis
and relevant observations. Session events are invalidation hints, not freshness
proof. Save or defer unsaved buffers. The
[session owner](../modules/context_session.md), at
`src/llm_wiki_cli/services/context_session.py:ContextSession`, revalidates consumed
inputs before reuse; a saved receipt is historical until reconciled or freshly
read against the current workspace.

Preserve the reason for the change in an affected authored documentation section
when that update is authorized. Follow the complete
[documentation maintenance loop](maintaining-documentation.md), then hand off
exact coordinates, the request/result identity, remaining gaps and the host's
behavioral findings. Keep agent review separate from human governance approval.
