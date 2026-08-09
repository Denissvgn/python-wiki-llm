# _SnapshotBuckets

**Location:** `src/llm_wiki_cli/services/source_snapshot.py:396`
**Kind:** Class
**Bases:** —
**Module:** [source_snapshot](../modules/source_snapshot.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `_SnapshotBuckets` in `src/llm_wiki_cli/services/source_snapshot.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `files_by_language` | `dict[str, list[SourceFile]]` | *required* | — |
| `dockerfile_candidates` | `list[SourceFile]` | *required* | — |
| `compose_candidates` | `list[SourceFile]` | *required* | — |
| `yaml_candidates` | `list[SourceFile]` | *required* | — |
| `package_markers` | `list[SourceFile]` | *required* | — |
| `unsupported_files_by_language` | `dict[str, list[SourceFile]]` | *required* | — |
| `gitignore_contents` | `dict[str, bytes \| None]` | *required* | — |
| `gitignore_rules` | `list[_GitignoreRule]` | *required* | — |
| `include_tests` | `frozenset[str]` | *required* | — |
| `source_selection_policy` | `SourceSelectionPolicy \| None` | *required* | — |
| `selected_regular_paths` | `set[str]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_SnapshotBuckets (src/llm_wiki_cli/services/source_snapshot.py)"]
    n1["_build_source_snapshot (src/llm_wiki_cli/services/source_snapshot.py)"]
    n2["_collect_source_selection_controls (src/llm_wiki_cli/services/source_snapshot.py)"]
    n3["_collect_source_tree (src/llm_wiki_cli/services/source_snapshot.py)"]
    n4["_new_snapshot_buckets (src/llm_wiki_cli/services/source_snapshot.py)"]
    n5["_prune_dirnames (src/llm_wiki_cli/services/source_snapshot.py)"]
    n6["_record_generated_javascript_bundle_candidate (src/llm_wiki_cli/services/source_snapshot.py)"]
    n7["_record_gitignore_rules (src/llm_wiki_cli/services/source_snapshot.py)"]
    n8["_record_infrastructure_candidates (src/llm_wiki_cli/services/source_snapshot.py)"]
    n9["_record_language_candidate (src/llm_wiki_cli/services/source_snapshot.py)"]
    n10["_record_source_file (src/llm_wiki_cli/services/source_snapshot.py)"]
    n11["_record_unsupported_language_candidate (src/llm_wiki_cli/services/source_snapshot.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/source_snapshot.md"
    click n1 "../modules/source_snapshot.md"
    click n2 "../modules/source_snapshot.md"
    click n3 "../modules/source_snapshot.md"
    click n4 "../modules/source_snapshot.md"
    click n5 "../modules/source_snapshot.md"
    click n6 "../modules/source_snapshot.md"
    click n7 "../modules/source_snapshot.md"
    click n8 "../modules/source_snapshot.md"
    click n9 "../modules/source_snapshot.md"
    click n10 "../modules/source_snapshot.md"
    click n11 "../modules/source_snapshot.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_snapshot](../modules/source_snapshot.md) | 0 | `compose_candidates`, `dockerfile_candidates`, `files_by_language`, `gitignore_contents`, `gitignore_rules`, `include_tests`, `package_markers`, `selected_regular_paths`, `source_selection_policy`, `unsupported_files_by_language`, `yaml_candidates` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_build_source_snapshot` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_collect_source_selection_controls` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_collect_source_tree` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_new_snapshot_buckets` | call | [source_snapshot](../modules/source_snapshot.md) |
| `_new_snapshot_buckets` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_prune_dirnames` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_record_generated_javascript_bundle_candidate` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_record_gitignore_rules` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_record_infrastructure_candidates` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_record_language_candidate` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_record_source_file` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
| `_record_unsupported_language_candidate` | type_reference | [source_snapshot](../modules/source_snapshot.md) |
