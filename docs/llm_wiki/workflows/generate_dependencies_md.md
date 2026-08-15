# generate_dependencies_md

**Entry point:** `bootstrap_runtime._generate_dependencies_md`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [diagrams](../modules/diagrams.md), [io](../modules/io.md), [services_dependencies](../modules/services_dependencies.md)

> Render ``dependencies.md`` from a :func:`analyze_dependencies` bundle.

Sections: a linked internal-module Mermaid ``flowchart`` (cyclic edges
thickened), import **Cycles**, a **Fan-in / Fan-out** table, **External
dependencies** grouped by language, and semantic ``## Notes``.
Deterministic; degrades cleanly with no cycles or no external deps.

**Cycles** reports only groups that are cyclic while they load. Groups joined
solely by deferred or ``TYPE_CHECKING`` imports follow, called out as the
non-problem they are, so a project is not told to fix the lazy boundary it
deliberately built.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.io`
2. `dependencies.analyze_dependencies`
3. `diagrams.flowchart`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [diagrams](../modules/diagrams.md)
- [io](../modules/io.md)
- [services_dependencies](../modules/services_dependencies.md)

## Behavior

Renders `dependencies.md` deterministically from dependency analysis and the
canonical module page map. It emits a bounded linked Mermaid projection,
explicit cycle groups, complete fan-in/fan-out rankings, and declared-versus-
used packages grouped by language. Large graphs collapse to package level or
report omitted edges, while the human-owned `Notes` section remains separate
from generated structure.
