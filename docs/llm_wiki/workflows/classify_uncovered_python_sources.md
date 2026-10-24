# classify_uncovered_python_sources

**Entry point:** `module_coverage.classify_uncovered_python_sources`
**Modules involved:** [module_coverage](../modules/module_coverage.md), [python_extractor](../modules/python_extractor.md), [python_imports](../modules/python_imports.md), [source_selection](../modules/source_selection.md)

> Explain only proven omissions; all unavailable proof stays uncovered.

Reads are guarded, hash-checked and limited to 1 MiB per selected file.
Alias chains stop after 16 hops. Namespace checks inspect only the expected
initializer's presence; an existing unselected initializer is never read.
Neither discovery nor inventory is modified.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `python_imports.PythonModuleIndex.build`
2. `python_extractor.module_alias_target`
3. `python_extractor.module_alias_target`
4. `source_selection.locate_exact_repository_path`

## Touches

- [module_coverage](../modules/module_coverage.md)
- [python_extractor](../modules/python_extractor.md)
- [python_imports](../modules/python_imports.md)
- [source_selection](../modules/source_selection.md)

## Behavior

This workflow starts at `module_coverage.classify_uncovered_python_sources`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
