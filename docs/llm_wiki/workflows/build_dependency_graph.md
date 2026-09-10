# build_dependency_graph

**Entry point:** `dependencies.build_dependency_graph`
**Modules involved:** [common](../modules/common.md), [imports](../modules/imports.md), [python_imports](../modules/python_imports.md), [services_dependencies](../modules/services_dependencies.md)

> Resolve each file's imports into an internal module-dependency graph.

For every file, each ``imports`` record is resolved to an internal target
file with the shared module-path resolver. Resolved targets become directed
``(from_file, to_file)`` edges (self-edges excluded, de-duplicated); imports
that resolve to no internal file land in ``unresolved``.

Returns ``{"edges": [(from_file, to_file), ...], "import_time_edges": [...],
"nodes": [...], "unresolved": [{"file", "module", "name"}, ...]}`` with every
list stably ordered. ``edges`` is every resolvable import, which is the
coupling view used for fan-in/fan-out and impact analysis;
``import_time_edges`` is the subset that actually runs when a module loads,
which is the view load order and cycle detection need. An import record with
no ``scope`` counts as import-time, so inventories from extractors that do
not classify imports keep the historical behavior of the two being equal.
A supported code-language inventory entry that has no ``imports`` field still
appears as an isolated node. Entries that explicitly provide an ``imports``
field retain the legacy node contract regardless of language; unknown,
untyped, and non-mapping entries without that field contribute no nodes or
edges and never raise.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `imports.build_module_path_resolver`
2. `python_imports.is_python_source`
3. `common.executes_at_import`

## Touches

- [common](../modules/common.md)
- [imports](../modules/imports.md)
- [python_imports](../modules/python_imports.md)
- [services_dependencies](../modules/services_dependencies.md)

## Behavior

This workflow starts at `dependencies.build_dependency_graph`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
