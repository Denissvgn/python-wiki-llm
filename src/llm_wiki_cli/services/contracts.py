"""Stable machine-readable contracts exposed by source-adapter commands.

The extract contract stays at ``llm-wiki-extract/v1`` while data-flow metadata
is added as optional fields. Consumers must tolerate inventories without
``data_effects``, call argument summaries, or top-level ``data_flows`` because
older payloads and non-Python extractors may not emit them. A schema version
bump is reserved for incompatible shape changes to existing fields.

Dependency/load-order architecture decisions also stay additive under the
current extract contract: deep Python inventory may include ``data_effects`` on
function entries, including bounded ``boundary_effects`` for filesystem,
environment, process, network, output, and logging calls; ``module_calls`` only
when module-level side effects exist; and ``extract --deep`` may include a
top-level ``data_flows`` list plus a top-level ``dependencies`` block. Python
dependency reconciliation treats ``sys.stdlib_module_names`` as the stdlib
source when available, falls back to the bundled Python 3.9 list in dependency
analysis, and uses the curated import-to-distribution aliases there with
optional project overrides from ``[tool.llm-wiki.dependency-aliases]``.
"""

from __future__ import annotations

EXTRACT_SCHEMA_VERSION = "llm-wiki-extract/v1"
BOOTSTRAP_SUMMARY_SCHEMA_VERSION = "llm-wiki-bootstrap-summary/v1"
BOOTSTRAP_SKIP_DATA_FLOW_FLAG = "--skip-data-flow"
EXTRACT_ADDITIVE_FIELDS = {
    "calls[].args",
    "calls[].kwargs",
    "data_effects",
    "data_flows",
}
