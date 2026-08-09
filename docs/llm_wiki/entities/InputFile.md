# _InputFile

**Location:** `src/llm_wiki_cli/services/documentation_wiki_input.py:351`
**Kind:** Class
**Bases:** —
**Module:** [documentation_wiki_input](../modules/documentation_wiki_input.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_InputFile` in `src/llm_wiki_cli/services/documentation_wiki_input.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `Path` | *required* | — |
| `relative_path` | `str` | *required* | — |
| `sha256` | `str` | *required* | — |
| `size` | `int` | *required* | — |
| `mtime_ns` | `int` | *required* | — |
| `ctime_ns` | `int` | *required* | — |
| `device` | `int` | *required* | — |
| `inode` | `int` | *required* | — |
| `root_descriptor` | `int \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_InputFile (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n1["_assert_input_files_resource_bounds (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n2["_assert_semantic_markdown_resource_bounds (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n3["_canonical_markdown_entries (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n4["_copy_file_bytes (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n5["_copy_regular_file (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n6["_decode_json_object (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n7["_InputTree.by_path (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n8["_inspect_markdown (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n9["_load_and_validate_metadata (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n10["_open_input_entry (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n11["_open_windows_input_leaf (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
    n12["_read_json_object (src/llm_wiki_cli/services/documentation_wiki_input.py)"]
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
    n12 --> n0
    click n0 "../modules/documentation_wiki_input.md"
    click n1 "../modules/documentation_wiki_input.md"
    click n2 "../modules/documentation_wiki_input.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/documentation_wiki_input.md"
    click n5 "../modules/documentation_wiki_input.md"
    click n6 "../modules/documentation_wiki_input.md"
    click n7 "../modules/documentation_wiki_input.md"
    click n8 "../modules/documentation_wiki_input.md"
    click n9 "../modules/documentation_wiki_input.md"
    click n10 "../modules/documentation_wiki_input.md"
    click n11 "../modules/documentation_wiki_input.md"
    click n12 "../modules/documentation_wiki_input.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_wiki_input](../modules/documentation_wiki_input.md) | 0 | `ctime_ns`, `device`, `inode`, `mtime_ns`, `path`, `relative_path`, `root_descriptor`, `sha256`, `size` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_assert_input_files_resource_bounds` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_assert_semantic_markdown_resource_bounds` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_canonical_markdown_entries` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_copy_file_bytes` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_copy_regular_file` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_decode_json_object` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_InputTree.by_path` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_inspect_markdown` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_load_and_validate_metadata` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_open_input_entry` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_open_windows_input_leaf` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_read_json_object` | type_reference | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
