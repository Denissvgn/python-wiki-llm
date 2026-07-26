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
DOCUMENTATION_RUN_SCHEMA_VERSION = "llm-wiki-documentation-run/v1"
DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION = "llm-wiki-documentation-agent-packet/v1"
DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION = "llm-wiki-documentation-agent-result/v1"
DOCUMENTATION_WORKLIST_SCHEMA_VERSION = "llm-wiki-documentation-worklist/v1"
DOCUMENTATION_SEMANTIC_READINESS_SCHEMA_VERSION = (
    "llm-wiki-documentation-semantic-readiness/v1"
)
DOCUMENTATION_REVIEW_LEDGER_SCHEMA_VERSION = "llm-wiki-documentation-review-ledger/v1"
DOCUMENTATION_VERIFICATION_SCHEMA_VERSION = "llm-wiki-documentation-verification/v1"
DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION = "llm-wiki-documentation-final-report/v1"
DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION = "llm-wiki-documentation-model-routing/v1"
DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION = (
    "llm-wiki-documentation-model-selection/v1"
)
P0_FLOW_CENSUS_SCHEMA_VERSION = "llm-wiki-p0-flow-census/v1"
P0_CALIBRATION_SHADOW_SCHEMA_VERSION = "llm-wiki-p0-calibration-shadow/v1"
P0_CALIBRATION_PREFLIGHT_SCHEMA_VERSION = "llm-wiki-p0-calibration-preflight/v1"
P0_CALIBRATION_VERDICT_SCHEMA_VERSION = "llm-wiki-p0-calibration-verdict/v1"
P0_CALIBRATION_RUN_SCHEMA_VERSION = "llm-wiki-p0-calibration-run/v1"
P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-execution-manifest/v1"
)
P0_CALIBRATION_CONTROL_RECORD_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-control-record/v1"
)
P0_CALIBRATION_ADMISSION_SCHEMA_VERSION = "llm-wiki-p0-calibration-admission/v1"
P0_CALIBRATION_EVIDENCE_BUNDLE_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-evidence-bundle/v1"
)
P0_CALIBRATION_AUTHORITY_GRANT_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-authority-grant/v1"
)
P0_CALIBRATION_ISOLATION_ATTESTATION_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-isolation-attestation/v1"
)
P0_CALIBRATION_ROLE_CAPABILITY_MATRIX_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-role-capability-matrix/v1"
)
P0_CALIBRATION_ISOLATION_PROBE_RESULT_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-isolation-probe-result/v1"
)
P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION = "llm-wiki-p0-calibration-agent-packet/v1"
P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION = "llm-wiki-p0-calibration-agent-result/v1"
P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-dispatch-receipt/v1"
)
P0_CALIBRATION_ACCESS_EVENT_SCHEMA_VERSION = "llm-wiki-p0-calibration-access-event/v1"
P0_CALIBRATION_TRANSITION_SCHEMA_VERSION = "llm-wiki-p0-calibration-transition/v1"
P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-verification-report/v1"
)
P0_CALIBRATION_FROZEN_INTAKE_SCHEMA_VERSION = "llm-wiki-p0-calibration-frozen-intake/v1"
P0_CALIBRATION_TASK_ORACLE_SCHEMA_VERSION = "llm-wiki-p0-calibration-task-oracle/v1"
P0_CALIBRATION_LABEL_FIELD_CONTRACT_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-label-field-contract/v1"
)
P0_CALIBRATION_OPTIMIZER_SEARCH_CONTRACT_SCHEMA_VERSION = (
    "llm-wiki-p0-calibration-optimizer-search-contract/v1"
)
P0_CALIBRATION_DECISION_SCOPE = "p0_policy_default"
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
