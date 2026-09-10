# scan_python_files

**Entry point:** `python_extractor._scan_python_files`
**Modules involved:** [common](../modules/common.md), [config](../modules/config.md), [fastapi_contracts](../modules/fastapi_contracts.md), [imports](../modules/imports.md), [python_bindings](../modules/python_bindings.md), [python_contracts](../modules/python_contracts.md), [python_extractor](../modules/python_extractor.md)

> Scan Python files under *src_dir* and return a raw inventory dict.

The returned dict maps *relative* filepath strings (relative to
*src_dir*) to file entry dicts.  The ``"language"`` key is
intentionally absent here — callers (e.g. :class:`PythonExtractor`)
are responsible for stamping it.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.build_gitignore_matcher`
2. `common.discover_source_files`
3. `python_bindings.analyze_python_bindings`
4. `python_contracts.finalize_model_kinds`
5. `fastapi_contracts.extract_fastapi_declarations`
6. `imports.build_module_path_resolver`
7. `python_contracts.finalize_inventory_model_kinds`

## Touches

- [common](../modules/common.md)
- [config](../modules/config.md)
- [fastapi_contracts](../modules/fastapi_contracts.md)
- [imports](../modules/imports.md)
- [python_bindings](../modules/python_bindings.md)
- [python_contracts](../modules/python_contracts.md)
- [python_extractor](../modules/python_extractor.md)

## Behavior

This workflow starts at `python_extractor._scan_python_files`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
