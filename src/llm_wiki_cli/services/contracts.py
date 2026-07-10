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
when module-level side effects exist; ``main_block_calls`` for calls inside a
Python ``if __name__ == "__main__"`` guard; and ``extract --deep`` may include
a top-level ``data_flows`` list plus a top-level ``dependencies`` block.
Python dependency reconciliation treats ``sys.stdlib_module_names`` as the
stdlib source when available, falls back to the bundled Python 3.9 list in
dependency analysis, and uses the curated import-to-distribution aliases there
with optional project overrides from ``[tool.llm-wiki.dependency-aliases]``.
Reconstructable Python contracts also remain additive: parameter ``kind``
values preserve declaration separators, while class/attribute records may add
enum members, type-alias targets, normalized Pydantic field state, model
configuration, and validator metadata. Extraction remains syntax-only and
consumers must tolerate these optional records being absent.
Deep Python inventory may additionally expose per-file ``frameworks.fastapi``
declarations and the payload may expose top-level ``api_contracts`` assembled
from static syntax or an authoritative source-contained OpenAPI export. These
records, their diagnostics, and entry-point ``routes`` remain optional under
``llm-wiki-extract/v1``.
"""

from __future__ import annotations

EXTRACT_SCHEMA_VERSION = "llm-wiki-extract/v1"
BOOTSTRAP_SUMMARY_SCHEMA_VERSION = "llm-wiki-bootstrap-summary/v1"
BOOTSTRAP_SKIP_DATA_FLOW_FLAG = "--skip-data-flow"
EXTRACT_ADDITIVE_FIELDS = {
    "calls[].args",
    "calls[].kwargs",
    "classes[].attributes[].alias",
    "classes[].attributes[].annotated_metadata",
    "classes[].attributes[].constraints",
    "classes[].attributes[].default_factory",
    "classes[].attributes[].description",
    "classes[].attributes[].examples",
    "classes[].attributes[].line",
    "classes[].attributes[].literal_values",
    "classes[].attributes[].nullable",
    "classes[].attributes[].required",
    "classes[].attributes[].serialization_alias",
    "classes[].attributes[].unknowns",
    "classes[].attributes[].validation_alias",
    "classes[].attributes[].value",
    "classes[].inferred",
    "classes[].kind",
    "classes[].literal_values",
    "classes[].methods[].validator",
    "classes[].model_config",
    "classes[].model_config[].unknowns",
    "classes[].model_kind",
    "classes[].target",
    "classes[].type_params",
    "data_effects",
    "data_effects.inputs[].parameter_kind",
    "data_flows",
    "entrypoints[].routes",
    "frameworks.fastapi",
    "main_block_calls",
    "params[].kind",
    "api_contracts",
}
