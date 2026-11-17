# publication_delivery Module

**Path:** `src/llm_wiki_cli/services/publication_delivery.py`

## Description

Pure validation and composition of a reviewed publication delivery or rollback.

The policy's publication target validates repository names and the restored
tree of a rollback.

## Imports

| Source | Symbols |
|--------|---------|
| `.publication_candidate` | `MAX_FILE_BYTES`, `MAX_FILES`, `MAX_TREE_BYTES`, `_PRIVATE`, `_REVISION`, `_VCS`, `_check_hash`, `_hash_map`, `_hashes`, `_validate_candidate_files`, `validate_publication_receipt` |
| `.publication_config` | `DELIVERY_CHECKPOINT_PATH`, `DELIVERY_CONFIG_SCHEMA_VERSION`, `publication_ref_name`, `target_repository`, `validate_publication_config` |
| `.publication_targets` | `current_publication_targets`, `publication_target` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `difflib` | `difflib` |
| `json` | `json` |
| `llm_wiki_engine.knowledge_evidence` | `canonical_json_bytes`, `hash_json`, `sha256_bytes` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["integrations/wiki-candidate/delivery/git_transport.py"]
    n1["integrations/wiki-candidate/delivery/publish.py"]
    n2["src/llm_wiki_cli/services/publication_candidate.py"]
    n3["src/llm_wiki_cli/services/publication_config.py"]
    n4["src/llm_wiki_cli/services/publication_delivery.py"]
    n5["src/llm_wiki_cli/services/publication_targets.py"]
    n6["src/llm_wiki_engine/knowledge_evidence.py"]
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n2 --> n6
    n3 --> n5
    n4 --> n2
    n4 --> n3
    n4 --> n5
    n4 --> n6
    n5 --> n3
    click n0 "../modules/git_transport.md"
    click n1 "../modules/publish.md"
    click n2 "../modules/publication_candidate.md"
    click n3 "../modules/publication_config.md"
    click n4 "../modules/publication_delivery.md"
    click n5 "../modules/publication_targets.md"
    click n6 "../modules/knowledge_evidence.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [git_transport](../modules/git_transport.md) |
| Inbound | [publish](../modules/publish.md) |
| Inbound | [publication_candidate](../modules/publication_candidate.md) |
| Outbound | [publication_candidate](../modules/publication_candidate.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [publication_targets](../modules/publication_targets.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_revision` | `(value: object) -> str` | — | — |
| `validate_rollback_review` | `(record: Mapping[str, Any], *, rollback_id: str) -> None` | — | Validate a host-accepted review record against the live rollback proposal. |
| `review_rollback` | `(proposal: Mapping[str, Any], *, reviewer: str, reason: str) -> dict[str, str]` | — | Prepare a private review record for the consumer's normal acceptance process. |
| `_public_hashes` | `(files: Mapping[str, bytes]) -> dict[str, str]` | — | — |
| `_checkpoint_bytes` | `(checkpoint: Mapping[str, Any]) -> bytes` | — | — |
| `_registered_repository` | `(value: object, field: str) -> None` | — | Accept a repository name that some registered publication target accepts. |
| `_validated_checkpoint` | `(raw: bytes, observed: Mapping[str, str]) -> dict[str, Any]` | — | — |
| `split_delivery_tree` | `(tree: Mapping[str, bytes]) -> tuple[dict[str, bytes], dict[str, Any] \| None]` | — | Separate the exact root checkpoint from public files and validate owned bytes. |
| `_scope` | `(policy, source_repository, target_repository, target_branch)` | — | — |
| `_match_scope` | `(checkpoint, scope)` | — | — |
| `_compose` | `(public, state)` | — | — |
| `plan_delivery` | `(receipt: Mapping[str, Any], candidate_files: Mapping[str, bytes], target_tree: Mapping[str, bytes], *, policy: Mapping[str, Any], source_repository: str, target_repository: str, target_branch: str, target_revision: str) -> tuple[dict[str, bytes], dict[str, Any] \| None]` | — | Build the exact proposed target bytes for a host-verified source/ref. |
| `_rollback_diff` | `(before, after)` | — | Retain exact file commitments plus bounded readable Markdown changes. |
| `plan_rollback` | `(current_tree: Mapping[str, bytes], historical_tree: Mapping[str, bytes], *, policy: Mapping[str, Any], source_repository: str, target_repository: str, target_branch: str, source_revision: str, target_revision: str, restore_revision: str) -> tuple[dict[str, bytes], dict[str, Any]]` | — | Propose a new target commit restoring earlier ownership and preserving manual changes. |
