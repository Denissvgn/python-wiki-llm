# Load order

Topological module load / startup order and import-time side effects.

## Load order

<!-- Dependency-first order: each module loads after the internal modules it imports. -->
1. [render_summary](modules/render_summary.md)
2. [llm-wiki_main](modules/llm-wiki_main.md)
3. [src_main](modules/src_main.md)
4. [api_types](modules/api_types.md)
5. [detectors](modules/detectors.md)
6. [styles](modules/styles.md)
7. [extractors___init__](modules/extractors___init__.md)
8. [fastapi_contracts](modules/fastapi_contracts.md)
9. [python_contracts](modules/python_contracts.md)
10. [bootstrap_service](modules/bootstrap_service.md)
11. [circuit_breaker](modules/circuit_breaker.md)
12. [services_contracts](modules/services_contracts.md)
13. [extraction_jobs](modules/extraction_jobs.md)
14. [filesystem_guard](modules/filesystem_guard.md)
15. [lockfile](modules/lockfile.md)
16. [paths](modules/paths.md)
17. [redaction](modules/redaction.md)
18. [resource_diagnostics](modules/resource_diagnostics.md)
19. [secure_file](modules/secure_file.md)
20. [validation](modules/validation.md)
21. [data_flow](modules/data_flow.md)
22. [documentation_model_policy](modules/documentation_model_policy.md)
23. [documentation_review](modules/documentation_review.md)
24. [knowledge_evidence](modules/knowledge_evidence.md)
25. [io](modules/io.md)
26. [config](modules/config.md)
27. [common](modules/common.md)
28. [markdown_sections](modules/markdown_sections.md)
29. [plugins](modules/plugins.md)
30. [diagrams](modules/diagrams.md)
31. [plugin_samples](modules/plugin_samples.md)
32. [protected_artifacts](modules/protected_artifacts.md)
33. [skills](modules/skills.md)
34. [skills_cmd](modules/skills_cmd.md)
35. [services_schema](modules/services_schema.md)
36. [install_cmd](modules/install_cmd.md)
37. [plugins_cmd](modules/plugins_cmd.md)
38. [source_selection](modules/source_selection.md)
39. [hook_cmd](modules/hook_cmd.md)
40. [versioning](modules/versioning.md)
41. [bump_cmd](modules/bump_cmd.md)
42. [release_cmd](modules/release_cmd.md)
43. [wiki_git_policy](modules/wiki_git_policy.md)
44. [wiki_media](modules/wiki_media.md)
45. [site_html_check](modules/site_html_check.md)
46. [wiki_scaffold](modules/wiki_scaffold.md)
47. [wiki_surface](modules/wiki_surface.md)
48. [init_cmd](modules/init_cmd.md)
49. [upgrade_cmd](modules/upgrade_cmd.md)
50. [concept_identity](modules/concept_identity.md)
51. [knowledge_graph](modules/knowledge_graph.md)
52. [section_ownership](modules/section_ownership.md)
53. [knowledge_envelope](modules/knowledge_envelope.md)
54. [knowledge_governance](modules/knowledge_governance.md)
55. [knowledge_model](modules/knowledge_model.md)
56. [knowledge_freshness](modules/knowledge_freshness.md)
57. [knowledge_links](modules/knowledge_links.md)
58. [source_snapshot](modules/source_snapshot.md)
59. [dependency_versions](modules/dependency_versions.md)
60. [documentation_policy](modules/documentation_policy.md)
61. [imports](modules/imports.md)
62. [python_extractor](modules/python_extractor.md)
63. [api_contracts](modules/api_contracts.md)
64. [services_dependencies](modules/services_dependencies.md)
65. [entrypoints](modules/entrypoints.md)
66. [infrastructure_inventory](modules/infrastructure_inventory.md)
67. [infrastructure_sync](modules/infrastructure_sync.md)
68. [inventory_cache](modules/inventory_cache.md)
69. [extractor_helpers](modules/extractor_helpers.md)
70. [prepare_extractors_cmd](modules/prepare_extractors_cmd.md)
71. [go_extractor](modules/go_extractor.md)
72. [haskell_extractor](modules/haskell_extractor.md)
73. [rust_extractor](modules/rust_extractor.md)
74. [ts_extractor](modules/ts_extractor.md)
75. [module_maps](modules/module_maps.md)
76. [packages](modules/packages.md)
77. [extraction_service](modules/extraction_service.md)
78. [relationships](modules/relationships.md)
79. [sync_manifest](modules/sync_manifest.md)
80. [verification_contracts](modules/verification_contracts.md)
81. [wiki_lifecycle](modules/wiki_lifecycle.md)
82. [ci_installer](modules/ci_installer.md)
83. [install_ci_cmd](modules/install_ci_cmd.md)
84. [uninstall_cmd](modules/uninstall_cmd.md)
85. [wiki_surface_index](modules/wiki_surface_index.md)
86. [documentation_worklist](modules/documentation_worklist.md)
87. [knowledge_index](modules/knowledge_index.md)
88. [knowledge_artifacts](modules/knowledge_artifacts.md)
89. [knowledge_generation](modules/knowledge_generation.md)
90. [knowledge_loader](modules/knowledge_loader.md)
91. [knowledge_consumption](modules/knowledge_consumption.md)
92. [knowledge_verification](modules/knowledge_verification.md)
93. [knowledge_observability](modules/knowledge_observability.md)
94. [knowledge_cmd](modules/knowledge_cmd.md)
95. [status_cmd](modules/status_cmd.md)
96. [documentation_queries](modules/documentation_queries.md)
97. [documentation_claim_evidence](modules/documentation_claim_evidence.md)
98. [knowledge_orchestration](modules/knowledge_orchestration.md)
99. [bootstrap_runtime](modules/bootstrap_runtime.md)
100. [migrate_cmd](modules/migrate_cmd.md)
101. [review_cmd](modules/review_cmd.md)
102. [context_packet](modules/context_packet.md)
103. [context_service](modules/context_service.md)
104. [documentation_query_builder](modules/documentation_query_builder.md)
105. [planner](modules/planner.md)
106. [eval_lite___init__](modules/eval_lite___init__.md)
107. [documentation_native](modules/documentation_native.md)
108. [documentation_wiki_input](modules/documentation_wiki_input.md)
109. [knowledge_projection](modules/knowledge_projection.md)
110. [obsidian](modules/obsidian.md)
111. [obsidian_cmd](modules/obsidian_cmd.md)
112. [site_export](modules/site_export.md)
113. [site_cmd](modules/site_cmd.md)
114. [sync_analysis](modules/sync_analysis.md)
115. [sync_cmd](modules/sync_cmd.md)
116. [team](modules/team.md)
117. [team_cmd](modules/team_cmd.md)
118. [lint_service](modules/lint_service.md)
119. [metrics](modules/metrics.md)
120. [ci_check_cmd](modules/ci_check_cmd.md)
121. [generate_prompt_cmd](modules/generate_prompt_cmd.md)
122. [metrics_cmd](modules/metrics_cmd.md)
123. [trigger_cmd](modules/trigger_cmd.md)
124. [calibration___init__](modules/calibration___init__.md)
125. [broker](modules/broker.md)
126. [calibration_contracts](modules/calibration_contracts.md)
127. [controller](modules/controller.md)
128. [host_broker](modules/host_broker.md)
129. [documentation_run___init__](modules/documentation_run___init__.md)
130. [documentation_run_contracts](modules/documentation_run_contracts.md)
131. [documentation_run_dependencies](modules/documentation_run_dependencies.md)
132. [export](modules/export.md)
133. [integrity](modules/integrity.md)
134. [packet](modules/packet.md)
135. [prepare](modules/prepare.md)
136. [record](modules/record.md)
137. [refresh](modules/refresh.md)
138. [documentation_run_schema](modules/documentation_run_schema.md)
139. [verify](modules/verify.md)
140. [workspace](modules/workspace.md)
141. [docs_cmd](modules/docs_cmd.md)
142. [doctor_service](modules/doctor_service.md)
143. [api](modules/api.md)
144. [doctor_cmd](modules/doctor_cmd.md)
145. [mcp_server](modules/mcp_server.md)
146. [mcp_cmd](modules/mcp_cmd.md)
147. [cli](modules/cli.md)

## Module-level side effects

| Module | Import-time calls |
|--------|-------------------|
| [render_summary](modules/render_summary.md) | `FRESHNESS_STATES = frozenset`, `AVAILABILITY_STATES = frozenset`, `SNAPSHOT_STATES = frozenset`, `GOVERNANCE_STATES = frozenset`, `GOVERNANCE_LEDGER_STATES = frozenset`, `GOVERNANCE_PROJECTION_STATES = frozenset`, `DRIFT_STATES = frozenset`, `VERIFICATION_STATES = frozenset`, `RECORDED_RESULTS = frozenset`, `REPORT_FIELDS = frozenset`, `AVAILABILITY_FIELDS = frozenset`, `FRESHNESS_FIELDS = frozenset`, `SNAPSHOT_FIELDS = frozenset`, `GOVERNANCE_FIELDS = frozenset`, `DRIFT_FIELDS = frozenset`, `VERIFICATION_FIELDS = frozenset` |
| [llm-wiki_main](modules/llm-wiki_main.md) | `__export`, `module.exports = __toCommonJS`, `import_obsidian = require`, `import_child_process = require` |
| [api](modules/api.md) | `_CALIBRATION_CONTROLLER_TYPE_EXPORTS = frozenset`, `_CALIBRATION_HOST_TYPE_EXPORTS = frozenset`, `_CALIBRATION_CONTROLLER_MODULES = frozenset`, `_CALIBRATION_HOST_MODULES = frozenset`, `_WIKI_INPUT_ARTIFACT_CATEGORIES = frozenset`, `_WIKI_INPUT_WORKSPACE_CATEGORIES = frozenset`, `_P = ParamSpec`, `_R = TypeVar`, `adopt_documentation_wiki_snapshot = _api_boundary`, `fingerprint_documentation_wiki_input = _api_boundary`, `prepare_documentation_run = _api_boundary`, `get_documentation_run_status = _api_boundary`, `build_documentation_agent_packet = _api_boundary`, `record_documentation_agent_result = _api_boundary`, `verify_documentation_run = _api_boundary`, `select_documentation_model = _api_boundary`, `validate_documentation_model_selection = _api_boundary`, `setattr`, `prepare_p0_calibration_run = _deprecated_api_alias`, `admit_p0_calibration_run = _deprecated_api_alias`, `get_p0_calibration_run_status = _deprecated_api_alias`, `build_p0_calibration_agent_packet = _deprecated_api_alias`, `dispatch_p0_calibration_agent = _deprecated_api_alias`, `record_p0_calibration_agent_result = _deprecated_api_alias`, `verify_p0_calibration_run = _deprecated_api_alias`, `use_p0_calibration_host_broker_authenticator = _deprecated_api_alias` |
| [docs_cmd](modules/docs_cmd.md) | `KNOWLEDGE_MODE_CHOICES = tuple` |
| [knowledge_cmd](modules/knowledge_cmd.md) | `_RECOVERABLE_PROJECTION_CODES = frozenset` |
| [mcp_cmd](modules/mcp_cmd.md) | `_MCP_SERVICE_EXPORTS = frozenset`, `_MISSING = object` |
| [migrate_cmd](modules/migrate_cmd.md) | `_LINK_RE = re.compile`, `_HEADING_RE = re.compile`, `_LOCATION_RE = re.compile`, `_PATH_RE = re.compile` |
| [release_cmd](modules/release_cmd.md) | `_UNRELEASED_RE = re.compile`, `_REF_LINK_RE = re.compile`, `_GITHUB_REPO_RE = re.compile`, `_UNRELEASED_BODY_RE = re.compile` |
| [site_cmd](modules/site_cmd.md) | `SITE_FORMAT_CHOICES = sorted`, `SITE_PROFILE_CHOICES = sorted`, `LINK_MODE_CHOICES = sorted`, `KNOWLEDGE_METADATA_CHOICES = sorted`, `KNOWLEDGE_PROFILE_CHOICES = sorted` |
| [sync_cmd](modules/sync_cmd.md) | `_FLOW_CATEGORY_RE = re.compile`, `_NEUTRAL_FLOW_BEHAVIOR_RE = re.compile`, `_NEUTRAL_WORKFLOW_BEHAVIOR_RE = re.compile`, `_GENERATED_ENTRY_POINT_RE = re.compile` |
| [trigger_cmd](modules/trigger_cmd.md) | `GIT_DIR = Path` |
| [planner](modules/planner.md) | `_CONTENT_ADDRESS_RE = re.compile`, `_CAPABILITY_RE = re.compile`, `_MISSING = object`, `_TASK_FIELDS = frozenset`, `_ORACLE_FIELDS = frozenset` |
| [common](modules/common.md) | `_HASH_TOKEN_SPLIT_RE = re.compile`, `INCLUDE_TEST_LANGUAGES = frozenset`, `_BUNDLED_HELPER_IMPLEMENTATIONS = frozenset`, `_WINDOWS_BUNDLED_HELPER_IMPLEMENTATIONS = frozenset`, `BUNDLED_HELPER_IMPLEMENTATION_PATHS = frozenset` |
| [api_contracts](modules/api_contracts.md) | `_STATUS_REF_RE = re.compile`, `_PATH_PARAMETER_RE = re.compile`, `_SAFE_ID_RE = re.compile`, `_NONE_ANNOTATION_RE = re.compile`, `_UNKNOWN = object` |
| [bootstrap_runtime](modules/bootstrap_runtime.md) | `_SOURCE_DOC_LINK_RE = re.compile`, `_FLOWCHART_NODE_LINE = re.compile` |
| [broker](modules/broker.md) | `SUPPORTED_OCI_RUNTIMES = frozenset`, `SUPPORTED_AGENT_ROLES = frozenset`, `_SLUG_RE = re.compile`, `_IDEMPOTENCY_RE = re.compile`, `_PUBLIC_RECIPIENT_RE = re.compile`, `_CONTAINER_NAME_RE = re.compile`, `_IMAGE_RE = re.compile`, `_NUMERIC_USER_RE = re.compile`, `_HEX_32_RE = re.compile`, `_CONTROL_RE = re.compile`, `_RECEIPT_STATUSES = frozenset`, `_CLEANUP_STATUSES = frozenset`, `_restore_legacy_definition_modules` |
| [calibration_contracts](modules/calibration_contracts.md) | `_CALIBRATION_PRIORITIES = frozenset`, `_SOURCE_PROVENANCE = frozenset`, `_CONFIDENCE_VALUES = frozenset`, `_MUTATION_HTTP_METHODS = frozenset`, `_restore_legacy_definition_modules` |
| [controller](modules/controller.md) | `CALIBRATION_TERMINAL_STATES = frozenset`, `ADMISSION_PROFILES = frozenset`, `_PORTABLE_ID_RE = re.compile`, `_EXTERNAL_DISPATCH_FAILURE_REASONS = frozenset`, `_DOCUMENT_SUFFIXES = frozenset`, `_ROOT_DOCUMENT_NAMES = frozenset`, `_PROJECT_MANIFEST_NAMES = frozenset`, `_ALLOWED_ROOT_FILES = frozenset`, `_ALLOWED_ROOT_DIRS = frozenset`, `_FILE_URI_RE = re.compile`, `_WINDOWS_ABSOLUTE_PATH_RE = re.compile`, `_POSIX_ABSOLUTE_PATH_RE = re.compile`, `admit_p0_calibration_run = _deprecated_calibration_alias`, `build_p0_calibration_agent_packet = _deprecated_calibration_alias`, `dispatch_p0_calibration_agent = _deprecated_calibration_alias`, `get_p0_calibration_run_status = _deprecated_calibration_alias`, `prepare_p0_calibration_run = _deprecated_calibration_alias`, `record_p0_calibration_agent_result = _deprecated_calibration_alias`, `verify_p0_calibration_run = _deprecated_calibration_alias`, `_restore_legacy_definition_modules` |
| [host_broker](modules/host_broker.md) | `_HOST_BROKER_AUTHENTICATOR = ContextVar`, `_restore_legacy_definition_modules` |
| [ci_installer](modules/ci_installer.md) | `MANAGED_WORKFLOW_PATH = Path`, `_ACTION_REF_RE = re.compile`, `_MANAGED_HEADER_RE = re.compile` |
| [concept_identity](modules/concept_identity.md) | `_BUNDLE_ID_RE = re.compile`, `_QUALIFIED_KIND_RE = re.compile`, `_NATURAL_KEY_PREFIX_RE = re.compile`, `_NATURAL_KEY_PAYLOAD_RE = re.compile`, `_PERCENT_ESCAPE_RE = re.compile`, `_INVALID_PERCENT_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_URI_SCHEME_RE = re.compile`, `_COLLISION_CODE_RE = re.compile`, `_COLLISION_COORDINATE_TYPE_RE = re.compile`, `_UID_RE = re.compile`, `_RecordT = TypeVar` |
| [context_packet](modules/context_packet.md) | `_LIMITATION_RE = re.compile`, `_PORTABLE_URI_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_STRUCTURAL_PATH_FIELDS = frozenset`, `_PUBLIC_URI_FIELDS = frozenset`, `_RECONCILIATION_FACETS = frozenset`, `_RECONCILIATION_FACET_FIELDS = frozenset`, `_PACKET_TOP_LEVEL_FIELDS = frozenset` |
| [context_service](modules/context_service.md) | `_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile` |
| [data_flow](modules/data_flow.md) | `_COMMON_STATIC_CALLS = frozenset` |
| [services_dependencies](modules/services_dependencies.md) | `_DEPENDENCY_MODULE_LANGUAGES = frozenset`, `_WIRING_NAMES = frozenset`, `_PYTHON_STDLIB_FALLBACK = frozenset`, `_PYTHON_MANIFEST_EXCLUDED_DIRS = frozenset`, `_NODE_BUILTINS = frozenset`, `_TS_MANIFEST_EXCLUDED_DIRS = frozenset`, `_GO_MANIFEST_EXCLUDED_DIRS = frozenset`, `_RUST_INTERNAL_ROOTS = frozenset`, `_HASKELL_MANIFEST_EXCLUDED_DIRS = frozenset`, `_CABAL_FIELD_RE = re.compile`, `_CABAL_STANZA_RE = re.compile`, `_STACK_FIELD_RE = re.compile`, `_NIX_HASKELL_PACKAGE_SKIP_NAMES = frozenset`, `_REQUIREMENTS_PIN_RE = re.compile` |
| [dependency_versions](modules/dependency_versions.md) | `_EXCLUDED_DIRS = frozenset`, `_SOURCE_NAMES = frozenset`, `_PYTHON_NAME_RE = re.compile` |
| [diagrams](modules/diagrams.md) | `_CLASS_SAFE = re.compile`, `_COLOR_SAFE = re.compile` |
| [doctor_service](modules/doctor_service.md) | `_REASON_RE = re.compile`, `_FRESHNESS_STATES = tuple`, `_CONFIRMED_STALE_STATES = frozenset`, `_INDETERMINATE_STATES = frozenset`, `_VERIFICATION_UNHEALTHY_STATES = frozenset` |
| [documentation_claim_evidence](modules/documentation_claim_evidence.md) | `_CLAIM_FIELDS = frozenset`, `_CLAIM_REQUIRED = frozenset`, `_CAPTURE_FIELDS = frozenset`, `_CAPTURE_REQUIRED = frozenset`, `_RESOLUTIONS = frozenset`, `_EVIDENCE_STATES = frozenset`, `_FRESHNESS_STATES = frozenset`, `_EVALUATED_FRESHNESS_DISCLOSURE_RE = re.compile`, `_AVAILABILITY_STATES = frozenset`, `_OWNERSHIP_STATES = frozenset`, `_CAPTURE_STATES = frozenset`, `_REDACTION_STATES = frozenset`, `_ENVIRONMENT_MODES = frozenset`, `_RUNTIME_CAPTURE_SUFFIXES = frozenset`, `_UNINSPECTED_MEDIA_SUFFIXES = frozenset`, `_UNINSPECTED_MEDIA_LIMITATIONS = frozenset`, `_SAFE_ID_RE = re.compile`, `_MACHINE_REASON_RE = re.compile`, `_WINDOWS_DRIVE_RE = re.compile`, `_CREDENTIAL_VALUE_RE = re.compile`, `_MACHINE_ABSOLUTE_PATH_RE = re.compile` |
| [documentation_model_policy](modules/documentation_model_policy.md) | `SUPPORTED_PROVIDER_FAMILIES = frozenset`, `SUPPORTED_MODEL_TIERS = frozenset`, `SUPPORTED_INVOCATION_MODES = frozenset`, `SUPPORTED_SELECTION_BASES = frozenset`, `_SLUG_RE = re.compile`, `_HEX_DIGEST_RE = re.compile`, `_CONTROL_RE = re.compile`, `_PUBLIC_IDENTIFIER_RE = re.compile`, `_CREDENTIAL_VALUE_RE = re.compile`, `_SENSITIVE_KEYS = frozenset` |
| [documentation_policy](modules/documentation_policy.md) | `AGENT_POLICY_FILENAMES = frozenset`, `SOURCE_BASELINE_EXCLUDED_DIRS = frozenset` |
| [documentation_queries](modules/documentation_queries.md) | `_QUALIFIED_NAME_RE = re.compile` |
| [documentation_query_builder](modules/documentation_query_builder.md) | `_UNSET_LIVE_SELECTION_INPUTS = object` |
| [documentation_review](modules/documentation_review.md) | `SUPPORTED_REVIEW_SOURCES = frozenset`, `SUPPORTED_FINDING_SEVERITIES = frozenset`, `SUPPORTED_FINDING_STATUSES = frozenset`, `TERMINAL_FINDING_STATUSES = frozenset`, `SUPPORTED_PACKET_ROLES = frozenset`, `SUPPORTED_LEDGER_STATES = frozenset`, `_CATEGORY_RE = re.compile`, `_FINDING_FIELDS = frozenset`, `_PACKET_FIELDS = frozenset`, `_RECONCILIATION_FIELDS = frozenset`, `_LEDGER_FIELDS = frozenset`, `_PACKET_COLLECTION_FIELDS = frozenset` |
| [documentation_run___init__](modules/documentation_run___init__.md) | `__annotations__ = dict`, `_conditional_annotations = getattr`, `_MISSING = object`, `_HISTORICAL_CLASS_FIRSTLINENO = dict`, `_COMPATIBILITY_NAMES = tuple`, `_COMPATIBILITY_OWNERS = dict`, `_DELETED_COMPATIBILITY_OWNERS = dict` |
| [documentation_run_contracts](modules/documentation_run_contracts.md) | `SUPPORTED_RUN_STATES = frozenset`, `SUPPORTED_BASELINE_STRATEGIES = frozenset`, `SUPPORTED_AGENT_STAGES = frozenset`, `SUPPORTED_AGENT_RESULT_STATUSES = frozenset`, `_AGENT_RESULT_FIELDS = frozenset`, `_IMPORTED_PAGE_EDIT_FIELDS = frozenset`, `_AGENT_FINDING_FIELDS = frozenset`, `_AGENT_FINDING_STATUSES = frozenset`, `_AGENT_FINDING_SEVERITIES = frozenset`, `SUPPORTED_FRESHNESS_POLICIES = frozenset`, `SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES = frozenset`, `_NATIVE_ARTIFACT_PATHS = frozenset`, `_PACKET_FORBIDDEN_FIELDS = frozenset`, `_PACKET_FORBIDDEN_KEY_SUFFIXES = frozenset` |
| [documentation_wiki_input](modules/documentation_wiki_input.md) | `SUPPORTED_MANIFEST_VERSIONS = frozenset`, `FRESHNESS_POLICIES = frozenset`, `_HASH_RE = re.compile`, `_OPENAPI_GENERATION_INPUT_FIELDS = frozenset`, `_SUPPORTED_GENERATION_INPUTS = frozenset`, `_GENERATED_MARKER_RE = re.compile`, `_WINDOWS_RESERVED_NAMES = frozenset`, `_WINDOWS_FORBIDDEN_CHARS = frozenset`, `_CANONICAL_ROOT_FILES = frozenset`, `_CANONICAL_MARKDOWN_DIRS = frozenset`, `_REJECTED_DIRECTORY_NAMES = frozenset`, `_REJECTED_FILE_NAMES = frozenset` |
| [documentation_worklist](modules/documentation_worklist.md) | `IMPORTED_PAGE_CLASSIFICATIONS = frozenset`, `GROUNDING_STATUSES = frozenset`, `WORK_ITEM_STATUSES = frozenset`, `_USER_PROFILE_DEFERRED_CATEGORIES = frozenset`, `_USER_PROFILE_INDEX_CATEGORIES = frozenset`, `_PRIMARY_FLOW_CATEGORIES = frozenset`, `_MARKDOWN_COMMENT_RE = re.compile`, `_MARKDOWN_LINK_RE = re.compile`, `_HEADING_RE = re.compile`, `_SOURCE_PATH_RE = re.compile` |
| [entrypoints](modules/entrypoints.md) | `_CLI_DECORATORS = frozenset`, `_HTTP_DECORATORS = frozenset`, `_MCP_DECORATORS = frozenset`, `_PLUGIN_CATEGORY_RE = re.compile`, `_NODE_HTTP_MODULES = frozenset`, `_GO_HTTP_MODULES = frozenset`, `_GO_HANDLE_FUNC_RE = re.compile`, `_GO_LISTEN_AND_SERVE_RE = re.compile`, `_GO_HTTP_SERVER_RE = re.compile`, `_HASKELL_SERVE_RE = re.compile`, `_HASKELL_WARP_RUN_RE = re.compile` |
| [extraction_service](modules/extraction_service.md) | `_MISSING_INVENTORY_REQUEST = object`, `_INVALID_DIFF_PATH = object`, `_DOCKERFILE_ENV_PATTERN = re.compile`, `_DOCKERFILE_VOLUME_LIST_PATTERN = re.compile`, `_DOCKERFILE_LABEL_PATTERN = re.compile` |
| [imports](modules/imports.md) | `_GO_MODULE_EXCLUDED_DIRS = frozenset`, `_TS_CONFIG_EXCLUDED_DIRS = frozenset` |
| [knowledge_artifacts](modules/knowledge_artifacts.md) | `_KNOWLEDGE_SCHEMA_VERSION_RE = re.compile`, `_SURFACE_SCHEMA_VERSION_RE = re.compile` |
| [knowledge_consumption](modules/knowledge_consumption.md) | `_MACHINE_SCOPE_KINDS = frozenset`, `_MACHINE_INVALIDATION_REASONS = frozenset`, `_MACHINE_RESULT_VALUES = frozenset`, `_MACHINE_CHECKER_ID_RE = re.compile`, `_MACHINE_CHECKER_VERSION_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_MACHINE_SCOPE_UID_RE = re.compile`, `_MACHINE_SUBJECT_RE = re.compile` |
| [knowledge_envelope](modules/knowledge_envelope.md) | `_REPOSITORY_IDENTITY_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_INPUT_KIND_RE = re.compile`, `_WINDOWS_DRIVE_PREFIX_RE = re.compile`, `_MALFORMED_PERCENT_RE = re.compile`, `_SCP_REMOTE_RE = re.compile`, `_EFFECTIVE_LINE_ENDING_CONFIG_KEYS = frozenset`, `_CORE_EOL_VALUES = frozenset` |
| [knowledge_evidence](modules/knowledge_evidence.md) | `_SHA256_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_UNKNOWN_REASON_RE = re.compile`, `_SUPPORTED_OBSERVATION_LANGUAGES = frozenset`, `_LOCATION_ONLY_KEYS = frozenset` |
| [knowledge_freshness](modules/knowledge_freshness.md) | `_STRUCTURAL_PAGE_KINDS = frozenset`, `_REASON_DESCRIPTIONS = MappingProxyType`, `KNOWN_FRESHNESS_REASON_CODES = frozenset` |
| [knowledge_governance](modules/knowledge_governance.md) | `ALIAS_TYPES = frozenset`, `ACTOR_KINDS = frozenset`, `REVIEW_EVIDENCE_MODES = frozenset`, `REVIEW_EXPIRY_REASONS = frozenset`, `_SAFE_ID_RE = re.compile`, `_EVENT_ID_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_CONTROL_RE = re.compile`, `_SENSITIVE_RE = re.compile`, `_MISSING = object` |
| [knowledge_graph](modules/knowledge_graph.md) | `_QUALIFIED_NAME_RE = re.compile`, `_LIMITATION_RE = re.compile`, `_CONTROL_RE = re.compile`, `_URI_RE = re.compile` |
| [knowledge_index](modules/knowledge_index.md) | `_WINDOWS_ABSOLUTE_RE = re.compile`, `_MALFORMED_PERCENT_RE = re.compile`, `_MANIFEST_STRUCTURAL_PAGE_KINDS = frozenset`, `_STRUCTURAL_PAGE_KINDS = frozenset`, `_LINK_SYNTAX_VALUES = frozenset` |
| [knowledge_links](modules/knowledge_links.md) | `_MALFORMED_PERCENT_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_URI_CHARS_RE = re.compile` |
| [knowledge_model](modules/knowledge_model.md) | `_QUALIFIED_NAME_RE = re.compile`, `_REPOSITORY_IDENTITY_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_PERCENT_ESCAPE_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_URI_CHAR_RE = re.compile`, `_MISSING = object`, `PAGE_KIND_TO_CONCEPT_KIND = MappingProxyType`, `_SURFACE_KIND_BY_PAGE_KIND = MappingProxyType`, `_EnumT = TypeVar` |
| [knowledge_observability](modules/knowledge_observability.md) | `_FRESHNESS_COUNT_KEYS = frozenset`, `_EVIDENCE_ISSUE_KEYS = frozenset`, `_PHASE_DURATION_KEYS = frozenset`, `_REASON_VALUES = frozenset`, `_DEGRADED_REASON_VALUES = frozenset`, `_UNSUPPORTED_REASON_VALUES = frozenset`, `BASIS_INCOMPATIBLE_HINTS = MappingProxyType`, `BASIS_INCOMPATIBLE_REASON_CODES = frozenset` |
| [knowledge_orchestration](modules/knowledge_orchestration.md) | `_COMPONENT_PART_RE = re.compile`, `_RUNTIME_POLICY_KEYS = frozenset`, `_DEPENDENCY_GRAPH_DETAILS = frozenset` |
| [knowledge_projection](modules/knowledge_projection.md) | `_EVALUATED_FRESHNESS_DISCLOSURE_RE = re.compile`, `_RESERVED_EXTENSION_KEYS = frozenset`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_TRAVERSAL_RE = re.compile`, `_EMBEDDED_ABSOLUTE_RE = re.compile`, `_RAW_VCS_REMOTE_RE = re.compile`, `_CONTROL_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile`, `_SAFE_TOKEN_RE = re.compile`, `_REVIEW_EXPIRY_REASONS = frozenset`, `_REVIEW_STATES = frozenset`, `_MACHINE_INVALIDATION_REASONS = frozenset`, `_OMISSION_FIELDS = frozenset`, `_BASE_WARNING_VALUES = frozenset` |
| [lint_service](modules/lint_service.md) | `MERMAID_CLICK_RE = re.compile`, `MERMAID_NODE_RE = re.compile`, `_CountKey = TypeVar` |
| [lockfile](modules/lockfile.md) | `_CONTENTION_ERRNOS = frozenset`, `_WINDOWS_CONTENTION_ERRORS = frozenset` |
| [markdown_sections](modules/markdown_sections.md) | `GENERATED_INDEX_INTROS = frozenset`, `_ATX_HEADING_RE = re.compile`, `_FENCE_OPEN_RE = re.compile`, `_LEGACY_HEADING_RE = re.compile`, `_AUTO_GENERATED_RE = re.compile`, `_INDEX_GENERATED_HEADINGS = frozenset` |
| [mcp_server](modules/mcp_server.md) | `_SEARCH_KINDS = set`, `_QUALIFIED_GRAPH_KIND_RE = re.compile` |
| [obsidian](modules/obsidian.md) | `MARKDOWN_LINK_RE = re.compile`, `WIKILINK_RE = re.compile`, `LOCATION_RE = re.compile`, `PATH_RE = re.compile`, `LLM_WIKI_FRONTMATTER_RE = re.compile`, `PROJECTED_FRONTMATTER_KEY_RE = re.compile`, `PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile`, `LLM_WIKI_FRESHNESS_RE = re.compile`, `TOP_LEVEL_PROJECTED_FRONTMATTER_KEY_RE = re.compile`, `TOP_LEVEL_PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile`, `FRONTMATTER_END_BYTES_RE = re.compile` |
| [paths](modules/paths.md) | `_TEST_DIRECTORY_NAMES = frozenset`, `_TEST_FILE_STEMS = frozenset` |
| [plugins](modules/plugins.md) | `_ID_RE = re.compile`, `_MODULE_RE = re.compile`, `_ATTR_RE = re.compile`, `_PROMPT_GIT_MUTATION_RE = re.compile`, `_RUNTIME_CACHE_DIRECTORIES = frozenset`, `_ACTIVATED_PATHS = set`, `_PLUGIN_LOAD_LOCK = threading.RLock` |
| [redaction](modules/redaction.md) | `SENSITIVE_KEYS = frozenset`, `SENSITIVE_KEY_RE = re.compile`, `PRIVATE_KEY_BLOCK_RE = re.compile`, `SENSITIVE_ASSIGNMENT_RE = re.compile`, `SENSITIVE_NATURAL_LANGUAGE_RE = re.compile`, `_REDACTION_SENSITIVE_ASSIGNMENT_RE = re.compile`, `_REDACTION_SENSITIVE_NATURAL_LANGUAGE_RE = re.compile`, `URI_USERINFO_RE = re.compile`, `PROJECTION_URI_USERINFO_RE = re.compile`, `_REDACTABLE_URI_USERINFO_RE = re.compile`, `_REDACTABLE_PROJECTION_URI_USERINFO_RE = re.compile`, `LIKELY_SECRET_RE = re.compile`, `CREDENTIAL_VALUE_RE = re.compile`, `_AUTHORIZATION_VALUE_RE = re.compile` |
| [resource_diagnostics](modules/resource_diagnostics.md) | `_MISSING_ERRNO = object`, `_ENOSPC = getattr`, `_EMFILE = getattr`, `_ENFILE = getattr`, `_ENOMEM = getattr`, `_EAGAIN = getattr` |
| [services_schema](modules/services_schema.md) | `_SOURCE_READING_RECIPE_COMMANDS = frozenset` |
| [section_ownership](modules/section_ownership.md) | `_INDEX_GENERATED_HEADINGS = frozenset`, `_ENTITY_GENERATED_HEADINGS = frozenset`, `_ENTITY_MIXED_HEADINGS = frozenset`, `_MODULE_GENERATED_HEADINGS = frozenset`, `_MODULE_MIXED_HEADINGS = frozenset`, `_WORKFLOW_GENERATED_HEADINGS = frozenset`, `_FLOW_GENERATED_HEADINGS = frozenset`, `_API_GENERATED_HEADINGS = frozenset`, `_DEPENDENCIES_GENERATED_HEADINGS = frozenset`, `_LOAD_ORDER_GENERATED_HEADINGS = frozenset`, `_INFRASTRUCTURE_GENERATED_HEADINGS = frozenset`, `_HTTP_OPERATION_HEADING_RE = re.compile`, `_LOG_DATE_HEADING_RE = re.compile` |
| [site_export](modules/site_export.md) | `SUPPORTED_SITE_FORMATS = frozenset`, `SUPPORTED_SITE_PROFILES = frozenset`, `SUPPORTED_KNOWLEDGE_METADATA = frozenset`, `SITE_PUBLICATION_STATES = frozenset`, `MARKDOWN_LINK_RE = re.compile`, `_RAW_MEDIA_HTML_RE = re.compile`, `FRONT_MATTER_KEY_RE = re.compile` |
| [site_html_check](modules/site_html_check.md) | `SUPPORTED_LINK_MODES = frozenset`, `_IGNORED_SCHEMES = frozenset`, `_HREF_TAGS = frozenset`, `_MEDIA_SRC_TAGS = frozenset` |
| [source_selection](modules/source_selection.md) | `_UNSET_SELECTION_INPUTS = object`, `_SOURCE_SELECTION_ORIGINS = frozenset`, `_GLOB_CHARACTERS = frozenset`, `_SHA256_RE = re.compile` |
| [source_snapshot](modules/source_snapshot.md) | `_UNSET_EXPECTED_SELECTION_INPUTS = object` |
| [sync_manifest](modules/sync_manifest.md) | `_REASON_RE = re.compile`, `_CONCEPT_PAGE_RE = re.compile` |
| [validation](modules/validation.md) | `_WINDOWS_ABSOLUTE_RE = re.compile`, `_WINDOWS_DRIVE_PREFIX_RE = re.compile`, `_WINDOWS_RESERVED_NAMES = frozenset`, `_WINDOWS_FORBIDDEN_PATH_CHARS = frozenset`, `_UNSAFE_PAGE_COMPONENT_RE = re.compile`, `_SHA256_RE = re.compile`, `_ZERO_UTC_OFFSET = timedelta`, `_EnumValue = TypeVar` |
| [verification_contracts](modules/verification_contracts.md) | `_CHECKER_ID_RE = re.compile`, `_CHECKER_VERSION_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_ANCHOR_ID_RE = re.compile`, `_SCOPE_UID_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_DIAGNOSTIC_SUBJECT_RE = re.compile`, `_CHECKER_REGISTRY = MappingProxyType` |
| [versioning](modules/versioning.md) | `VERSION_RE = re.compile`, `_TABLE_RE = re.compile` |
| [wiki_git_policy](modules/wiki_git_policy.md) | `_GIT_REPOSITORY_REDIRECTION_ENV = frozenset` |
| [wiki_media](modules/wiki_media.md) | `IMAGE_EXTENSIONS = frozenset`, `VIDEO_EXTENSIONS = frozenset`, `_MARKDOWN_TITLE_RE = re.compile`, `_AUTHORITY_USERINFO_RE = re.compile`, `_URI_AUTHORITY_PREFIX_RE = re.compile`, `_URI_TOKEN_START_RE = re.compile`, `_REFERENCE_DEFINITION_RE = re.compile`, `_REFERENCE_IMAGE_RE = re.compile`, `_README_ASSET_RE = re.compile`, `_MERMAID_CLICK_RE = re.compile` |
| [wiki_surface](modules/wiki_surface.md) | `_PAGE_ID_RE = re.compile`, `_ASSET_SURFACE = WikiAssetSurface` |
| [wiki_surface_index](modules/wiki_surface_index.md) | `_MERMAID_CLICK_RE = re.compile`, `_MARKDOWN_PATH_RE = re.compile` |

## Factory / wiring

<!-- Heuristic, name-based detection of app-factory / wiring functions. -->

| Function | Kind | Module |
|----------|------|--------|
| `create_oci_admission_probe_environment` | factory | [broker](modules/broker.md) |
| `create_review_ledger` | factory | [documentation_review](modules/documentation_review.md) |
| `create_private_windows_directory` | factory | [filesystem_guard](modules/filesystem_guard.md) |
| `create_mcp_server` | factory | [mcp_server](modules/mcp_server.md) |

## Indeterminate (cyclic) groups

> These modules form import cycles, so their relative load order is indeterminate.

- [calibration___init__](modules/calibration___init__.md) ⇄ [broker](modules/broker.md) ⇄ [calibration_contracts](modules/calibration_contracts.md) ⇄ [controller](modules/controller.md) ⇄ [host_broker](modules/host_broker.md) ⇄ [documentation_run___init__](modules/documentation_run___init__.md) ⇄ [documentation_run_contracts](modules/documentation_run_contracts.md) ⇄ [documentation_run_dependencies](modules/documentation_run_dependencies.md) ⇄ [export](modules/export.md) ⇄ [integrity](modules/integrity.md) ⇄ [packet](modules/packet.md) ⇄ [prepare](modules/prepare.md) ⇄ [record](modules/record.md) ⇄ [refresh](modules/refresh.md) ⇄ [documentation_run_schema](modules/documentation_run_schema.md) ⇄ [verify](modules/verify.md) ⇄ [workspace](modules/workspace.md)
- [context_packet](modules/context_packet.md) ⇄ [context_service](modules/context_service.md) ⇄ [documentation_query_builder](modules/documentation_query_builder.md)
- [knowledge_consumption](modules/knowledge_consumption.md) ⇄ [knowledge_verification](modules/knowledge_verification.md)
- [knowledge_envelope](modules/knowledge_envelope.md) ⇄ [knowledge_governance](modules/knowledge_governance.md) ⇄ [knowledge_model](modules/knowledge_model.md)
- [lint_service](modules/lint_service.md) ⇄ [metrics](modules/metrics.md)

## Notes

The packaged console entry point calls `llm_wiki_cli.cli:main`; the numbered
list is dependency-first import ordering, not the order in which commands run.
Most listed import-time calls construct immutable constants, regular
expressions, compatibility aliases, or type helpers. Command work begins only
after parser dispatch.

Optional and derived integrations deliberately have different boundaries.
`mcp_cmd` delays importing the MCP service until the command is invoked, so the
base CLI does not require the optional SDK. `src_main` is the Obsidian
TypeScript source, while `llm-wiki_main` is its compiled CommonJS bundle; their
positions do not describe an application startup sequence. The
`render_summary` integration is a standalone GitHub runner script.

Relative order inside each cyclic group is indeterminate. Avoid adding
observable import-time work there; prefer explicit constructors and command
entry points. Runtime plugin discovery, conditional compatibility imports, and
lazy transports can introduce edges that this static projection cannot show.
Use [dependencies](dependencies.md) for fan-in, fan-out, package reconciliation,
and the complete cycle list.
