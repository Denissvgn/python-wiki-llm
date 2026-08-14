# knowledge_verification Module

**Path:** `src/llm_wiki_cli/services/knowledge_verification.py`

## Description

Read-only machine-verification evaluation for native knowledge sessions.

Verification receipts are disposable evidence anchored to committed native
artifacts.  This module loads and evaluates a receipt without running any
checker, and returns the same coordinate-keyed summaries to every consumer.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_consumption` | `KnowledgeReadView`, `MachineVerificationAvailability`, `MachineVerificationReadView` |
| `.knowledge_evidence` | `hash_json` |
| `.knowledge_governance` | `GOVERNANCE_EXTENSION_KEY` |
| `.verification_contracts` | `VerificationReceipt`, `VerificationResult`, `build_artifact_verification_context`, `evaluate_verification_receipt`, `load_verification_receipt` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `replace` |
| `pathlib` | `Path` |
| `types` | `MappingProxyType` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/services/context_packet.py"]
    n2["src/llm_wiki_cli/services/context_service.py"]
    n3["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n4["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n5["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n6["src/llm_wiki_cli/services/knowledge_governance.py"]
    n7["src/llm_wiki_cli/services/knowledge_verification.py"]
    n8["src/llm_wiki_cli/services/lint_service.py"]
    n9["src/llm_wiki_cli/services/verification_contracts.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n7
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n7
    n2 --> n1
    n2 --> n3
    n2 --> n4
    n2 --> n7
    n3 --> n2
    n3 --> n4
    n3 --> n7
    n4 --> n7
    n6 --> n5
    n7 --> n4
    n7 --> n5
    n7 --> n6
    n7 --> n9
    n8 --> n4
    n8 --> n6
    n8 --> n7
    n8 --> n9
    n9 --> n5
    click n0 "../modules/api.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_service.md"
    click n3 "../modules/documentation_query_builder.md"
    click n4 "../modules/knowledge_consumption.md"
    click n5 "../modules/knowledge_evidence.md"
    click n6 "../modules/knowledge_governance.md"
    click n7 "../modules/knowledge_verification.md"
    click n8 "../modules/lint_service.md"
    click n9 "../modules/verification_contracts.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [context_packet](../modules/context_packet.md) |
| Inbound | [context_service](../modules/context_service.md) |
| Inbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Inbound | [knowledge_consumption](../modules/knowledge_consumption.md) |
| Inbound | [lint_service](../modules/lint_service.md) |
| Outbound | [knowledge_consumption](../modules/knowledge_consumption.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Outbound | [verification_contracts](../modules/verification_contracts.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `machine_verification_summaries` | `(wiki_dir: str \| Path, knowledge_view: KnowledgeReadView) -> Mapping[str, Mapping[str, Any]]` | — | Return the legacy coordinate-keyed adapter for API/query consumers. |
| `attach_machine_verification_read_view` | `(wiki_dir: str \| Path, knowledge_view: KnowledgeReadView) -> KnowledgeReadView` | — | Attach one fixed receipt evaluation to an operation-scoped read view. |
| `load_machine_verification_read_view` | `(wiki_dir: str \| Path, knowledge_view: KnowledgeReadView) -> MachineVerificationReadView` | — | Load and evaluate one fixed receipt without executing a checker. |
| `verification_summaries_for_concepts` | `(knowledge_view: KnowledgeReadView, evaluated: MachineVerificationReadView \| None = None) -> Mapping[str, Mapping[str, Any]]` | — | Adapt one receipt evaluation to the existing per-coordinate contract. |
| `machine_verification_summary` | `(receipt: VerificationReceipt, *, valid: bool, reasons: list[str]) -> dict[str, Any]` | — | Return a compact, bounded machine-only receipt summary. |
| `_frozen_summaries` | `(values: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]` | — | — |
| `_deep_copy` | `(value: object) -> Any` | — | — |
