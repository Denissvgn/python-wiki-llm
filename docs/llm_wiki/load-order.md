# Load order

Topological module load / startup order and import-time side effects.

## Load order

<!-- Dependency-first order: each module loads after the internal modules it imports. -->
1. [llm-wiki_main](modules/llm-wiki_main.md)
2. [src_main](modules/src_main.md)
3. [llm_wiki_cli___init__](modules/llm_wiki_cli___init__.md)
4. [api_types](modules/api_types.md)
5. [detectors](modules/detectors.md)
6. [styles](modules/styles.md)
7. [extractors___init__](modules/extractors___init__.md)
8. [fastapi_contracts](modules/fastapi_contracts.md)
9. [python_bindings](modules/python_bindings.md)
10. [python_contracts](modules/python_contracts.md)
11. [bootstrap_service](modules/bootstrap_service.md)
12. [calibration___init__](modules/calibration___init__.md)
13. [canonical_json](modules/canonical_json.md)
14. [circuit_breaker](modules/circuit_breaker.md)
15. [services_contracts](modules/services_contracts.md)
16. [context_knowledge_contract](modules/context_knowledge_contract.md)
17. [extraction_jobs](modules/extraction_jobs.md)
18. [filesystem_guard](modules/filesystem_guard.md)
19. [go_calls](modules/go_calls.md)
20. [health_summary](modules/health_summary.md)
21. [immutable](modules/immutable.md)
22. [knowledge_storage](modules/knowledge_storage.md)
23. [knowledge_audit](modules/knowledge_audit.md)
24. [knowledge_packs](modules/knowledge_packs.md)
25. [lockfile](modules/lockfile.md)
26. [packet_field_policy](modules/packet_field_policy.md)
27. [paths](modules/paths.md)
28. [progress](modules/progress.md)
29. [python_calls](modules/python_calls.md)
30. [python_observations](modules/python_observations.md)
31. [python_stdlib](modules/python_stdlib.md)
32. [python_imports](modules/python_imports.md)
33. [redaction](modules/redaction.md)
34. [request_json](modules/request_json.md)
35. [resource_diagnostics](modules/resource_diagnostics.md)
36. [runtime_output](modules/runtime_output.md)
37. [search_rank](modules/search_rank.md)
38. [secure_file](modules/secure_file.md)
39. [storage_receipts](modules/storage_receipts.md)
40. [storage_sort](modules/storage_sort.md)
41. [storage_spool](modules/storage_spool.md)
42. [token_counting](modules/token_counting.md)
43. [validation](modules/validation.md)
44. [planner](modules/planner.md)
45. [eval_lite___init__](modules/eval_lite___init__.md)
46. [broker](modules/broker.md)
47. [host_broker](modules/host_broker.md)
48. [data_flow](modules/data_flow.md)
49. [documentation_model_policy](modules/documentation_model_policy.md)
50. [documentation_review](modules/documentation_review.md)
51. [knowledge_evidence](modules/knowledge_evidence.md)
52. [io](modules/io.md)
53. [query_cmd](modules/query_cmd.md)
54. [task_cmd](modules/task_cmd.md)
55. [config](modules/config.md)
56. [mcp_cmd](modules/mcp_cmd.md)
57. [search_cmd](modules/search_cmd.md)
58. [common](modules/common.md)
59. [imports](modules/imports.md)
60. [python_extractor](modules/python_extractor.md)
61. [knowledge_reuse](modules/knowledge_reuse.md)
62. [knowledge_storage_io](modules/knowledge_storage_io.md)
63. [legacy_hooks](modules/legacy_hooks.md)
64. [hook_cmd](modules/hook_cmd.md)
65. [markdown_sections](modules/markdown_sections.md)
66. [packages](modules/packages.md)
67. [plugins](modules/plugins.md)
68. [diagrams](modules/diagrams.md)
69. [plugin_samples](modules/plugin_samples.md)
70. [protected_artifacts](modules/protected_artifacts.md)
71. [relationships](modules/relationships.md)
72. [services_schema](modules/services_schema.md)
73. [install_cmd](modules/install_cmd.md)
74. [plugins_cmd](modules/plugins_cmd.md)
75. [skills](modules/skills.md)
76. [skills_cmd](modules/skills_cmd.md)
77. [instruction_ownership](modules/instruction_ownership.md)
78. [rendering_lifecycle](modules/rendering_lifecycle.md)
79. [source_selection](modules/source_selection.md)
80. [documentation_policy](modules/documentation_policy.md)
81. [source_snapshot](modules/source_snapshot.md)
82. [api_contracts](modules/api_contracts.md)
83. [api_diff](modules/api_diff.md)
84. [api_diff_cmd](modules/api_diff_cmd.md)
85. [dependency_versions](modules/dependency_versions.md)
86. [services_dependencies](modules/services_dependencies.md)
87. [entrypoints](modules/entrypoints.md)
88. [infrastructure_inventory](modules/infrastructure_inventory.md)
89. [infrastructure_sync](modules/infrastructure_sync.md)
90. [inventory_cache](modules/inventory_cache.md)
91. [extractor_helpers](modules/extractor_helpers.md)
92. [prepare_extractors_cmd](modules/prepare_extractors_cmd.md)
93. [go_extractor](modules/go_extractor.md)
94. [haskell_extractor](modules/haskell_extractor.md)
95. [rust_extractor](modules/rust_extractor.md)
96. [ts_extractor](modules/ts_extractor.md)
97. [capability_diagnostics](modules/capability_diagnostics.md)
98. [extraction_service](modules/extraction_service.md)
99. [module_maps](modules/module_maps.md)
100. [sync_manifest](modules/sync_manifest.md)
101. [canonical_pages](modules/canonical_pages.md)
102. [manifest_storage](modules/manifest_storage.md)
103. [team](modules/team.md)
104. [team_cmd](modules/team_cmd.md)
105. [versioning](modules/versioning.md)
106. [bump_cmd](modules/bump_cmd.md)
107. [release_cmd](modules/release_cmd.md)
108. [wiki_git_policy](modules/wiki_git_policy.md)
109. [wiki_media](modules/wiki_media.md)
110. [site_html_check](modules/site_html_check.md)
111. [wiki_scaffold](modules/wiki_scaffold.md)
112. [wiki_surface](modules/wiki_surface.md)
113. [concept_identity](modules/concept_identity.md)
114. [knowledge_graph](modules/knowledge_graph.md)
115. [knowledge_model](modules/knowledge_model.md)
116. [knowledge_envelope](modules/knowledge_envelope.md)
117. [knowledge_freshness](modules/knowledge_freshness.md)
118. [health_contract](modules/health_contract.md)
119. [knowledge_governance](modules/knowledge_governance.md)
120. [knowledge_links](modules/knowledge_links.md)
121. [knowledge_storage_access](modules/knowledge_storage_access.md)
122. [knowledge_stream_audit](modules/knowledge_stream_audit.md)
123. [section_ownership](modules/section_ownership.md)
124. [verification_contracts](modules/verification_contracts.md)
125. [wiki_lifecycle](modules/wiki_lifecycle.md)
126. [init_cmd](modules/init_cmd.md)
127. [upgrade_cmd](modules/upgrade_cmd.md)
128. [ci_installer](modules/ci_installer.md)
129. [install_ci_cmd](modules/install_ci_cmd.md)
130. [uninstall_cmd](modules/uninstall_cmd.md)
131. [wiki_surface_index](modules/wiki_surface_index.md)
132. [calibration_contracts](modules/calibration_contracts.md)
133. [documentation_worklist](modules/documentation_worklist.md)
134. [knowledge_index](modules/knowledge_index.md)
135. [knowledge_artifacts](modules/knowledge_artifacts.md)
136. [knowledge_generation](modules/knowledge_generation.md)
137. [knowledge_loader](modules/knowledge_loader.md)
138. [knowledge_consumption](modules/knowledge_consumption.md)
139. [health_details](modules/health_details.md)
140. [knowledge_coverage](modules/knowledge_coverage.md)
141. [knowledge_observability](modules/knowledge_observability.md)
142. [knowledge_cmd](modules/knowledge_cmd.md)
143. [status_cmd](modules/status_cmd.md)
144. [documentation_queries](modules/documentation_queries.md)
145. [documentation_claim_evidence](modules/documentation_claim_evidence.md)
146. [documentation_wiki_input](modules/documentation_wiki_input.md)
147. [knowledge_orchestration](modules/knowledge_orchestration.md)
148. [bootstrap_runtime](modules/bootstrap_runtime.md)
149. [migrate_cmd](modules/migrate_cmd.md)
150. [change_selection](modules/change_selection.md)
151. [documentation_native](modules/documentation_native.md)
152. [knowledge_projection](modules/knowledge_projection.md)
153. [knowledge_storage_lifecycle](modules/knowledge_storage_lifecycle.md)
154. [knowledge_storage_diagnostics](modules/knowledge_storage_diagnostics.md)
155. [knowledge_storage_cmd](modules/knowledge_storage_cmd.md)
156. [knowledge_verification](modules/knowledge_verification.md)
157. [documentation_query_builder](modules/documentation_query_builder.md)
158. [context_service](modules/context_service.md)
159. [context_packet](modules/context_packet.md)
160. [context_budget](modules/context_budget.md)
161. [documentation_run_dependencies](modules/documentation_run_dependencies.md)
162. [documentation_run_contracts](modules/documentation_run_contracts.md)
163. [documentation_run_schema](modules/documentation_run_schema.md)
164. [workspace](modules/workspace.md)
165. [integrity](modules/integrity.md)
166. [packet](modules/packet.md)
167. [refresh](modules/refresh.md)
168. [prepare](modules/prepare.md)
169. [record](modules/record.md)
170. [verify](modules/verify.md)
171. [export](modules/export.md)
172. [documentation_run___init__](modules/documentation_run___init__.md)
173. [docs_cmd](modules/docs_cmd.md)
174. [controller](modules/controller.md)
175. [lint_service](modules/lint_service.md)
176. [doctor_service](modules/doctor_service.md)
177. [doctor_cmd](modules/doctor_cmd.md)
178. [ci_report](modules/ci_report.md)
179. [render_summary](modules/render_summary.md)
180. [maintenance_queue](modules/maintenance_queue.md)
181. [queue_cmd](modules/queue_cmd.md)
182. [metrics](modules/metrics.md)
183. [ci_check_cmd](modules/ci_check_cmd.md)
184. [generate_prompt_cmd](modules/generate_prompt_cmd.md)
185. [metrics_cmd](modules/metrics_cmd.md)
186. [trigger_cmd](modules/trigger_cmd.md)
187. [native_inspection](modules/native_inspection.md)
188. [obsidian](modules/obsidian.md)
189. [obsidian_cmd](modules/obsidian_cmd.md)
190. [review_service](modules/review_service.md)
191. [review_cmd](modules/review_cmd.md)
192. [impact](modules/impact.md)
193. [search_service](modules/search_service.md)
194. [site_export](modules/site_export.md)
195. [site_cmd](modules/site_cmd.md)
196. [sync_analysis](modules/sync_analysis.md)
197. [sync_cmd](modules/sync_cmd.md)
198. [cli](modules/cli.md)
199. [workflow_profile](modules/workflow_profile.md)
200. [task_contract](modules/task_contract.md)
201. [task_evidence](modules/task_evidence.md)
202. [task_context](modules/task_context.md)
203. [context_session](modules/context_session.md)
204. [api](modules/api.md)
205. [mcp_server](modules/mcp_server.md)
206. [task_context_v2](modules/task_context_v2.md)

## Module-level side effects

| Module | Import-time calls |
|--------|-------------------|
| [render_summary](modules/render_summary.md) | `FRESHNESS_STATES = frozenset`, `AVAILABILITY_STATES = frozenset`, `SNAPSHOT_STATES = frozenset`, `GOVERNANCE_STATES = frozenset`, `GOVERNANCE_LEDGER_STATES = frozenset`, `GOVERNANCE_PROJECTION_STATES = frozenset`, `DRIFT_STATES = frozenset`, `VERIFICATION_STATES = frozenset`, `RECORDED_RESULTS = frozenset`, `REPORT_FIELDS = frozenset`, `AVAILABILITY_FIELDS = frozenset`, `FRESHNESS_FIELDS = frozenset`, `SNAPSHOT_FIELDS = frozenset`, `GOVERNANCE_FIELDS = frozenset`, `DRIFT_FIELDS = frozenset`, `VERIFICATION_FIELDS = frozenset` |
| [llm-wiki_main](modules/llm-wiki_main.md) | `__export`, `module.exports = __toCommonJS`, `import_obsidian = require`, `import_child_process = require` |
| [llm_wiki_cli___init__](modules/llm_wiki_cli___init__.md) | `__version__ = version` |
| [api](modules/api.md) | `_CALIBRATION_CONTROLLER_TYPE_EXPORTS = frozenset`, `_CALIBRATION_HOST_TYPE_EXPORTS = frozenset`, `_CALIBRATION_CONTROLLER_MODULES = frozenset`, `_CALIBRATION_HOST_MODULES = frozenset`, `_WIKI_INPUT_ARTIFACT_CATEGORIES = frozenset`, `_WIKI_INPUT_WORKSPACE_CATEGORIES = frozenset`, `_P = ParamSpec`, `_R = TypeVar`, `_NATIVE_QUERY_ERROR_FIELDS = frozenset`, `_QUALIFIED_GRAPH_KIND_RE = re.compile`, `adopt_documentation_wiki_snapshot = _api_boundary`, `fingerprint_documentation_wiki_input = _api_boundary`, `prepare_documentation_run = _api_boundary`, `get_documentation_run_status = _api_boundary`, `build_documentation_agent_packet = _api_boundary`, `record_documentation_agent_result = _api_boundary`, `verify_documentation_run = _api_boundary`, `select_documentation_model = _api_boundary`, `validate_documentation_model_selection = _api_boundary`, `setattr`, `prepare_p0_calibration_run = _deprecated_api_alias`, `admit_p0_calibration_run = _deprecated_api_alias`, `get_p0_calibration_run_status = _deprecated_api_alias`, `build_p0_calibration_agent_packet = _deprecated_api_alias`, `dispatch_p0_calibration_agent = _deprecated_api_alias`, `record_p0_calibration_agent_result = _deprecated_api_alias`, `verify_p0_calibration_run = _deprecated_api_alias`, `use_p0_calibration_host_broker_authenticator = _deprecated_api_alias` |
| [docs_cmd](modules/docs_cmd.md) | `KNOWLEDGE_MODE_CHOICES = tuple` |
| [knowledge_cmd](modules/knowledge_cmd.md) | `_RECOVERABLE_PROJECTION_CODES = frozenset` |
| [mcp_cmd](modules/mcp_cmd.md) | `_MCP_SERVICE_EXPORTS = frozenset`, `_MISSING = object` |
| [migrate_cmd](modules/migrate_cmd.md) | `_LINK_RE = re.compile`, `_HEADING_RE = re.compile`, `_LOCATION_RE = re.compile`, `_PATH_RE = re.compile` |
| [release_cmd](modules/release_cmd.md) | `_UNRELEASED_RE = re.compile`, `_REF_LINK_RE = re.compile`, `_GITHUB_REPO_RE = re.compile`, `_UNRELEASED_BODY_RE = re.compile` |
| [site_cmd](modules/site_cmd.md) | `SITE_FORMAT_CHOICES = sorted`, `SITE_PROFILE_CHOICES = sorted`, `LINK_MODE_CHOICES = sorted`, `KNOWLEDGE_METADATA_CHOICES = sorted`, `KNOWLEDGE_PROFILE_CHOICES = sorted` |
| [sync_cmd](modules/sync_cmd.md) | `_FLOW_CATEGORY_RE = re.compile`, `_NEUTRAL_FLOW_BEHAVIOR_RE = re.compile`, `_NEUTRAL_WORKFLOW_BEHAVIOR_RE = re.compile`, `_GENERATED_ENTRY_POINT_RE = re.compile` |
| [trigger_cmd](modules/trigger_cmd.md) | `GIT_DIR = Path` |
| [config](modules/config.md) | `_CONFIG_EXPECTATION_UNSET = object`, `_RENDER_STATE_FIELDS = frozenset`, `_PENDING_CLEANUP_FIELDS = frozenset`, `_RENDER_PROFILES = frozenset`, `_RENDER_REASONS = frozenset`, `_OPAQUE_CONFIG_REASONS = frozenset` |
| [planner](modules/planner.md) | `_CONTENT_ADDRESS_RE = re.compile`, `_CAPABILITY_RE = re.compile`, `_MISSING = object`, `_TASK_FIELDS = frozenset`, `_ORACLE_FIELDS = frozenset` |
| [common](modules/common.md) | `_HASH_TOKEN_SPLIT_RE = re.compile`, `INCLUDE_TEST_LANGUAGES = frozenset`, `NON_IMPORT_TIME_SCOPES = frozenset`, `_BUNDLED_HELPER_IMPLEMENTATIONS = frozenset`, `_WINDOWS_BUNDLED_HELPER_IMPLEMENTATIONS = frozenset`, `BUNDLED_HELPER_IMPLEMENTATION_PATHS = frozenset` |
| [python_bindings](modules/python_bindings.md) | `BUILTIN_NAMES = frozenset` |
| [python_extractor](modules/python_extractor.md) | `_TYPE_CHECKING_MODULES = frozenset` |
| [api_contracts](modules/api_contracts.md) | `_STATUS_REF_RE = re.compile`, `_PATH_PARAMETER_RE = re.compile`, `_SAFE_ID_RE = re.compile`, `_NONE_ANNOTATION_RE = re.compile`, `_UNKNOWN = object` |
| [bootstrap_runtime](modules/bootstrap_runtime.md) | `_SOURCE_DOC_LINK_RE = re.compile`, `_FLOWCHART_NODE_LINE = re.compile` |
| [broker](modules/broker.md) | `SUPPORTED_OCI_RUNTIMES = frozenset`, `SUPPORTED_AGENT_ROLES = frozenset`, `_SLUG_RE = re.compile`, `_IDEMPOTENCY_RE = re.compile`, `_PUBLIC_RECIPIENT_RE = re.compile`, `_CONTAINER_NAME_RE = re.compile`, `_IMAGE_RE = re.compile`, `_NUMERIC_USER_RE = re.compile`, `_HEX_32_RE = re.compile`, `_CONTROL_RE = re.compile`, `_RECEIPT_STATUSES = frozenset`, `_CLEANUP_STATUSES = frozenset`, `_restore_legacy_definition_modules` |
| [calibration_contracts](modules/calibration_contracts.md) | `_CALIBRATION_PRIORITIES = frozenset`, `_SOURCE_PROVENANCE = frozenset`, `_CONFIDENCE_VALUES = frozenset`, `_MUTATION_HTTP_METHODS = frozenset`, `_restore_legacy_definition_modules` |
| [controller](modules/controller.md) | `CALIBRATION_TERMINAL_STATES = frozenset`, `ADMISSION_PROFILES = frozenset`, `_PORTABLE_ID_RE = re.compile`, `_EXTERNAL_DISPATCH_FAILURE_REASONS = frozenset`, `_DOCUMENT_SUFFIXES = frozenset`, `_ROOT_DOCUMENT_NAMES = frozenset`, `_PROJECT_MANIFEST_NAMES = frozenset`, `_ALLOWED_ROOT_FILES = frozenset`, `_ALLOWED_ROOT_DIRS = frozenset`, `_FILE_URI_RE = re.compile`, `_WINDOWS_ABSOLUTE_PATH_RE = re.compile`, `_POSIX_ABSOLUTE_PATH_RE = re.compile`, `admit_p0_calibration_run = _deprecated_calibration_alias`, `build_p0_calibration_agent_packet = _deprecated_calibration_alias`, `dispatch_p0_calibration_agent = _deprecated_calibration_alias`, `get_p0_calibration_run_status = _deprecated_calibration_alias`, `prepare_p0_calibration_run = _deprecated_calibration_alias`, `record_p0_calibration_agent_result = _deprecated_calibration_alias`, `verify_p0_calibration_run = _deprecated_calibration_alias`, `_restore_legacy_definition_modules` |
| [host_broker](modules/host_broker.md) | `_HOST_BROKER_AUTHENTICATOR = ContextVar`, `use_p0_calibration_host_broker_authenticator.__name__ = 'use_p0_calibration_host_broker_authenticator'`, `use_p0_calibration_host_broker_authenticator.__qualname__ = 'use_p0_calibration_host_broker_authenticator'`, `_restore_legacy_definition_modules` |
| [canonical_json](modules/canonical_json.md) | `_ESCAPED = re.compile`, `_SHORT = frozenset` |
| [ci_installer](modules/ci_installer.md) | `MANAGED_WORKFLOW_PATH = Path`, `_ACTION_REF_RE = re.compile`, `_MANAGED_HEADER_RE = re.compile` |
| [ci_report](modules/ci_report.md) | `_CI_REQUIRED_FIELDS = frozenset`, `_CI_OPTIONAL_FIELDS = frozenset`, `_KNOWLEDGE_SUMMARY_FIELDS = frozenset`, `_LINT_ISSUE_REQUIRED_FIELDS = frozenset`, `_LINT_ISSUE_OPTIONAL_FIELDS = frozenset`, `_EXTRACTOR_JOB_FIELDS = frozenset`, `_DOCTOR_FIELDS = frozenset`, `_AVAILABILITY_FIELDS = frozenset`, `_FRESHNESS_FIELDS = frozenset`, `_SNAPSHOT_FIELDS = frozenset`, `_GOVERNANCE_FIELDS = frozenset`, `_DRIFT_FIELDS = frozenset`, `_VERIFICATION_FIELDS = frozenset`, `_FRESHNESS_STATES = frozenset`, `_AVAILABILITY_STATES = frozenset`, `_SNAPSHOT_STATES = frozenset`, `_GOVERNANCE_STATES = frozenset`, `_GOVERNANCE_LEDGER_STATES = frozenset`, `_GOVERNANCE_PROJECTION_STATES = frozenset`, `_DRIFT_STATES = frozenset`, `_VERIFICATION_STATES = frozenset`, `_RECORDED_RESULTS = frozenset`, `_JSON_EVIDENCE_STATES = frozenset`, `_REASON_RE = re.compile` |
| [concept_identity](modules/concept_identity.md) | `_BUNDLE_ID_RE = re.compile`, `_QUALIFIED_KIND_RE = re.compile`, `_NATURAL_KEY_PREFIX_RE = re.compile`, `_NATURAL_KEY_PAYLOAD_RE = re.compile`, `_PERCENT_ESCAPE_RE = re.compile`, `_INVALID_PERCENT_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_URI_SCHEME_RE = re.compile`, `_COLLISION_CODE_RE = re.compile`, `_COLLISION_COORDINATE_TYPE_RE = re.compile`, `_UID_RE = re.compile`, `_RecordT = TypeVar` |
| [context_knowledge_contract](modules/context_knowledge_contract.md) | `_LIFECYCLE_FIELDS = frozenset`, `_EVIDENCE_FIELDS = frozenset`, `_LIFECYCLE_EVIDENCE_FIELDS = frozenset`, `_CONTRACT_FIELDS = frozenset`, `_CONTRACT['lifecycle_evidence_matrix'] = [{'lifecycle_state': lifecycle['state'], 'evidence_state': evidence['state'], 'rendered_profile': lifecycle['rendered_profile'], 'read_only_knowledge': evidence['read_only_knowledge'], 'fallback_evidence': list(evidence['fallback_evidence']), 'mutation_permission': 'none', 'signals': _combined_signals(lifecycle, evidence), 'recovery_routes': _combined_recovery_routes(lifecycle, evidence)} for lifecycle in _CONTRACT['lifecycle_matrix'] for evidence in _CONTRACT['evidence_matrix']]`, `_CANONICAL_CONTRACT = deepcopy`, `_CANONICAL_CONTRACT_JSON = json.dumps`, `validate_context_knowledge_contract` |
| [context_packet](modules/context_packet.md) | `_LIMITATION_RE = re.compile`, `_COVERAGE_LIMITATION_RE = re.compile`, `_PORTABLE_URI_RE = re.compile`, `_RFC3986_URI_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_RECONCILIATION_FACETS = frozenset`, `_RECONCILIATION_FACET_FIELDS = frozenset`, `_PACKET_TOP_LEVEL_FIELDS = frozenset`, `_LEGACY_PACKET_CONTRACT = _PacketWireContract`, `_KNOWLEDGE_PACKET_CONTRACT = _PacketWireContract`, `_PACKET_CONTRACT_BY_SCHEMA = MappingProxyType`, `_CAPTURE_GUARDS = ContextVar` |
| [context_service](modules/context_service.md) | `_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile` |
| [data_flow](modules/data_flow.md) | `_COMMON_STATIC_CALLS = frozenset` |
| [services_dependencies](modules/services_dependencies.md) | `_DEPENDENCY_MODULE_LANGUAGES = frozenset`, `_WIRING_NAMES = frozenset`, `_PYTHON_MANIFEST_EXCLUDED_DIRS = frozenset`, `_NODE_BUILTINS = frozenset`, `_TS_MANIFEST_EXCLUDED_DIRS = frozenset`, `_GO_MANIFEST_EXCLUDED_DIRS = frozenset`, `_RUST_INTERNAL_ROOTS = frozenset`, `_HASKELL_MANIFEST_EXCLUDED_DIRS = frozenset`, `_CABAL_FIELD_RE = re.compile`, `_CABAL_STANZA_RE = re.compile`, `_STACK_FIELD_RE = re.compile`, `_NIX_HASKELL_PACKAGE_SKIP_NAMES = frozenset`, `_REQUIREMENTS_PIN_RE = re.compile` |
| [dependency_versions](modules/dependency_versions.md) | `_EXCLUDED_DIRS = frozenset`, `_SOURCE_NAMES = frozenset`, `_PYTHON_NAME_RE = re.compile` |
| [diagrams](modules/diagrams.md) | `_CLASS_SAFE = re.compile`, `_COLOR_SAFE = re.compile` |
| [doctor_service](modules/doctor_service.md) | `_REASON_RE = re.compile`, `_FRESHNESS_STATES = tuple`, `_CONFIRMED_STALE_STATES = frozenset`, `_INDETERMINATE_STATES = frozenset`, `_VERIFICATION_UNHEALTHY_STATES = frozenset` |
| [documentation_claim_evidence](modules/documentation_claim_evidence.md) | `_CLAIM_FIELDS = frozenset`, `_CLAIM_REQUIRED = frozenset`, `_CAPTURE_FIELDS = frozenset`, `_CAPTURE_REQUIRED = frozenset`, `_RESOLUTIONS = frozenset`, `_EVIDENCE_STATES = frozenset`, `_FRESHNESS_STATES = frozenset`, `_EVALUATED_FRESHNESS_DISCLOSURE_RE = re.compile`, `_AVAILABILITY_STATES = frozenset`, `_OWNERSHIP_STATES = frozenset`, `_CAPTURE_STATES = frozenset`, `_REDACTION_STATES = frozenset`, `_ENVIRONMENT_MODES = frozenset`, `_RUNTIME_CAPTURE_SUFFIXES = frozenset`, `_UNINSPECTED_MEDIA_SUFFIXES = frozenset`, `_UNINSPECTED_MEDIA_LIMITATIONS = frozenset`, `_SAFE_ID_RE = re.compile`, `_MACHINE_REASON_RE = re.compile`, `_WINDOWS_DRIVE_RE = re.compile`, `_CREDENTIAL_VALUE_RE = re.compile`, `_MACHINE_ABSOLUTE_PATH_RE = re.compile` |
| [documentation_model_policy](modules/documentation_model_policy.md) | `SUPPORTED_PROVIDER_FAMILIES = frozenset`, `SUPPORTED_MODEL_TIERS = frozenset`, `SUPPORTED_INVOCATION_MODES = frozenset`, `SUPPORTED_SELECTION_BASES = frozenset`, `_SLUG_RE = re.compile`, `_HEX_DIGEST_RE = re.compile`, `_CONTROL_RE = re.compile`, `_PUBLIC_IDENTIFIER_RE = re.compile`, `_CREDENTIAL_VALUE_RE = re.compile`, `_SENSITIVE_KEYS = frozenset` |
| [documentation_policy](modules/documentation_policy.md) | `AGENT_POLICY_FILENAMES = frozenset`, `SOURCE_BASELINE_EXCLUDED_DIRS = frozenset` |
| [documentation_queries](modules/documentation_queries.md) | `_QUALIFIED_NAME_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_CONTEXT_COVERAGE_LIMITATION_RE = re.compile`, `_QUERY_PRESENTATION_TEXT_FIELDS = frozenset`, `_KNOWLEDGE_SELECTION_REJECTING_FINDINGS = frozenset`, `_QueryParameters = ParamSpec` |
| [documentation_query_builder](modules/documentation_query_builder.md) | `_UNSET_LIVE_SELECTION_INPUTS = object`, `_UNSET_DIFF_HEADER = object` |
| [documentation_review](modules/documentation_review.md) | `SUPPORTED_REVIEW_SOURCES = frozenset`, `SUPPORTED_FINDING_SEVERITIES = frozenset`, `SUPPORTED_FINDING_STATUSES = frozenset`, `TERMINAL_FINDING_STATUSES = frozenset`, `SUPPORTED_PACKET_ROLES = frozenset`, `SUPPORTED_LEDGER_STATES = frozenset`, `_CATEGORY_RE = re.compile`, `_FINDING_FIELDS = frozenset`, `_PACKET_FIELDS = frozenset`, `_RECONCILIATION_FIELDS = frozenset`, `_LEDGER_FIELDS = frozenset`, `_PACKET_COLLECTION_FIELDS = frozenset` |
| [documentation_run___init__](modules/documentation_run___init__.md) | `__annotations__ = dict`, `_conditional_annotations = getattr`, `__conditional_annotations__ = set`, `_MISSING = object`, `_HISTORICAL_CLASS_FIRSTLINENO = dict`, `_COMPATIBILITY_NAMES = tuple`, `_COMPATIBILITY_OWNERS = dict`, `_DELETED_COMPATIBILITY_OWNERS = dict`, `_sys.modules[__name__].__class__ = _CompatibilityModule` |
| [documentation_run_contracts](modules/documentation_run_contracts.md) | `SUPPORTED_RUN_STATES = frozenset`, `SUPPORTED_BASELINE_STRATEGIES = frozenset`, `SUPPORTED_AGENT_STAGES = frozenset`, `SUPPORTED_AGENT_RESULT_STATUSES = frozenset`, `_AGENT_RESULT_FIELDS = frozenset`, `_IMPORTED_PAGE_EDIT_FIELDS = frozenset`, `_AGENT_FINDING_FIELDS = frozenset`, `_AGENT_FINDING_STATUSES = frozenset`, `_AGENT_FINDING_SEVERITIES = frozenset`, `SUPPORTED_FRESHNESS_POLICIES = frozenset`, `SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES = frozenset`, `_NATIVE_ARTIFACT_PATHS = frozenset`, `_PACKET_FORBIDDEN_FIELDS = frozenset`, `_PACKET_FORBIDDEN_KEY_SUFFIXES = frozenset` |
| [documentation_wiki_input](modules/documentation_wiki_input.md) | `SUPPORTED_MANIFEST_VERSIONS = frozenset`, `FRESHNESS_POLICIES = frozenset`, `_HASH_RE = re.compile`, `_OPENAPI_GENERATION_INPUT_FIELDS = frozenset`, `_SUPPORTED_GENERATION_INPUTS = frozenset`, `_GENERATED_MARKER_RE = re.compile`, `_WINDOWS_RESERVED_NAMES = frozenset`, `_WINDOWS_FORBIDDEN_CHARS = frozenset`, `_CANONICAL_ROOT_FILES = frozenset`, `_CANONICAL_MARKDOWN_DIRS = frozenset`, `_REJECTED_DIRECTORY_NAMES = frozenset`, `_REJECTED_FILE_NAMES = frozenset` |
| [documentation_worklist](modules/documentation_worklist.md) | `IMPORTED_PAGE_CLASSIFICATIONS = frozenset`, `GROUNDING_STATUSES = frozenset`, `WORK_ITEM_STATUSES = frozenset`, `_USER_PROFILE_DEFERRED_CATEGORIES = frozenset`, `_USER_PROFILE_INDEX_CATEGORIES = frozenset`, `_PRIMARY_FLOW_CATEGORIES = frozenset`, `_MARKDOWN_COMMENT_RE = re.compile`, `_MARKDOWN_LINK_RE = re.compile`, `_HEADING_RE = re.compile`, `_SOURCE_PATH_RE = re.compile` |
| [entrypoints](modules/entrypoints.md) | `_CLI_DECORATORS = frozenset`, `_HTTP_DECORATORS = frozenset`, `_MCP_DECORATORS = frozenset`, `_PLUGIN_CATEGORY_RE = re.compile`, `_NODE_HTTP_MODULES = frozenset`, `_GO_HTTP_MODULES = frozenset`, `_GO_HANDLE_FUNC_RE = re.compile`, `_GO_LISTEN_AND_SERVE_RE = re.compile`, `_GO_HTTP_SERVER_RE = re.compile`, `_HASKELL_SERVE_RE = re.compile`, `_HASKELL_WARP_RUN_RE = re.compile` |
| [extraction_service](modules/extraction_service.md) | `_MISSING_INVENTORY_REQUEST = object`, `_INVALID_DIFF_PATH = object`, `_DOCKERFILE_ENV_PATTERN = re.compile`, `_DOCKERFILE_VOLUME_LIST_PATTERN = re.compile`, `_DOCKERFILE_LABEL_PATTERN = re.compile` |
| [filesystem_guard](modules/filesystem_guard.md) | `_EXPECTED_EXISTING_UNSET = object` |
| [health_contract](modules/health_contract.md) | `FRESHNESS_STATES = frozenset`, `COMPARABLE_STATES = frozenset`, `_HASH = re.compile`, `_ID = re.compile` |
| [immutable](modules/immutable.md) | `_T = TypeVar` |
| [imports](modules/imports.md) | `_GO_MODULE_EXCLUDED_DIRS = frozenset`, `_TS_CONFIG_EXCLUDED_DIRS = frozenset` |
| [instruction_ownership](modules/instruction_ownership.md) | `_ALL_PROFILES = tuple`, `_MAINTENANCE = _topic`, `_SURFACES_NAMING = _topic`, `_PUBLISHING = _topic`, `_EXTRACTORS = _topic`, `_ROUTER_TOPICS = tuple`, `_INSTALLED_REFERENCE_PATH = re.compile`, `_REFERENCE_ROOT_TOPIC_PATH = re.compile` |
| [knowledge_artifacts](modules/knowledge_artifacts.md) | `_KNOWLEDGE_SCHEMA_VERSION_RE = re.compile`, `_SURFACE_SCHEMA_VERSION_RE = re.compile` |
| [knowledge_consumption](modules/knowledge_consumption.md) | `_MACHINE_SCOPE_KINDS = frozenset`, `_MACHINE_INVALIDATION_REASONS = frozenset`, `_MACHINE_RESULT_VALUES = frozenset`, `_MACHINE_CHECKER_ID_RE = re.compile`, `_MACHINE_CHECKER_VERSION_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_MACHINE_SCOPE_UID_RE = re.compile`, `_MACHINE_SUBJECT_RE = re.compile` |
| [knowledge_coverage](modules/knowledge_coverage.md) | `_KINDS = frozenset` |
| [knowledge_envelope](modules/knowledge_envelope.md) | `_REPOSITORY_IDENTITY_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_INPUT_KIND_RE = re.compile`, `_WINDOWS_DRIVE_PREFIX_RE = re.compile`, `_MALFORMED_PERCENT_RE = re.compile`, `_SCP_REMOTE_RE = re.compile`, `_EFFECTIVE_LINE_ENDING_CONFIG_KEYS = frozenset`, `_CORE_EOL_VALUES = frozenset` |
| [knowledge_evidence](modules/knowledge_evidence.md) | `_SHA256_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_UNKNOWN_REASON_RE = re.compile`, `_SUPPORTED_OBSERVATION_LANGUAGES = frozenset`, `_LOCATION_ONLY_KEYS = frozenset` |
| [knowledge_freshness](modules/knowledge_freshness.md) | `_STRUCTURAL_PAGE_KINDS = frozenset`, `_REASON_DESCRIPTIONS = MappingProxyType`, `KNOWN_FRESHNESS_REASON_CODES = frozenset`, `FRESHNESS_REASON_STATES = MappingProxyType` |
| [knowledge_governance](modules/knowledge_governance.md) | `ALIAS_TYPES = frozenset`, `ACTOR_KINDS = frozenset`, `REVIEW_EVIDENCE_MODES = frozenset`, `REVIEW_EXPIRY_REASONS = frozenset`, `_SAFE_ID_RE = re.compile`, `_EVENT_ID_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_CONTROL_RE = re.compile`, `_SENSITIVE_RE = re.compile`, `_MISSING = object` |
| [knowledge_graph](modules/knowledge_graph.md) | `_QUALIFIED_NAME_RE = re.compile`, `_LIMITATION_RE = re.compile`, `_CONTROL_RE = re.compile`, `_URI_RE = re.compile` |
| [knowledge_index](modules/knowledge_index.md) | `_WINDOWS_ABSOLUTE_RE = re.compile`, `_MALFORMED_PERCENT_RE = re.compile`, `_MANIFEST_STRUCTURAL_PAGE_KINDS = frozenset`, `_STRUCTURAL_PAGE_KINDS = frozenset`, `_LINK_SYNTAX_VALUES = frozenset` |
| [knowledge_links](modules/knowledge_links.md) | `_MALFORMED_PERCENT_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_URI_CHARS_RE = re.compile` |
| [knowledge_model](modules/knowledge_model.md) | `_QUALIFIED_NAME_RE = re.compile`, `_REPOSITORY_IDENTITY_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_PERCENT_ESCAPE_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_URI_CHAR_RE = re.compile`, `_MISSING = object`, `PAGE_KIND_TO_CONCEPT_KIND = MappingProxyType`, `_SURFACE_KIND_BY_PAGE_KIND = MappingProxyType`, `_EnumT = TypeVar` |
| [knowledge_observability](modules/knowledge_observability.md) | `_FRESHNESS_COUNT_KEYS = frozenset`, `_EVIDENCE_ISSUE_KEYS = frozenset`, `_PHASE_DURATION_KEYS = frozenset`, `_REASON_VALUES = frozenset`, `_DEGRADED_REASON_VALUES = frozenset`, `_UNSUPPORTED_REASON_VALUES = frozenset`, `BASIS_INCOMPATIBLE_HINTS = MappingProxyType`, `BASIS_INCOMPATIBLE_REASON_CODES = frozenset` |
| [knowledge_orchestration](modules/knowledge_orchestration.md) | `_COMPONENT_PART_RE = re.compile`, `_RUNTIME_POLICY_KEYS = frozenset`, `_DEPENDENCY_GRAPH_DETAILS = frozenset`, `_COMMITTED_STATE_TOKEN = object` |
| [knowledge_packs](modules/knowledge_packs.md) | `INDEX_PAGE_NAME = re.compile`, `PACKED_FORMATS = frozenset`, `INDEX_NAME = re.compile`, `PACK_NAME = re.compile`, `_BITS = re.compile`, `_HEX = re.compile`, `_MEMBER = re.compile`, `_LOCAL_HEADER = struct.Struct`, `_END = struct.Struct` |
| [knowledge_projection](modules/knowledge_projection.md) | `_EVALUATED_FRESHNESS_DISCLOSURE_RE = re.compile`, `_RESERVED_EXTENSION_KEYS = frozenset`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_TRAVERSAL_RE = re.compile`, `_EMBEDDED_ABSOLUTE_RE = re.compile`, `_RAW_VCS_REMOTE_RE = re.compile`, `_CONTROL_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile`, `_SAFE_TOKEN_RE = re.compile`, `_REVIEW_EXPIRY_REASONS = frozenset`, `_REVIEW_STATES = frozenset`, `_MACHINE_INVALIDATION_REASONS = frozenset`, `_OMISSION_FIELDS = frozenset`, `_BASE_WARNING_VALUES = frozenset` |
| [knowledge_reuse](modules/knowledge_reuse.md) | `_HASH_FIELDS = frozenset` |
| [knowledge_storage](modules/knowledge_storage.md) | `_HASH = re.compile`, `_PREFIX = re.compile`, `_RESERVED = frozenset`, `_INTERN_FIELDS = frozenset` |
| [knowledge_storage_lifecycle](modules/knowledge_storage_lifecycle.md) | `_OBJECT_NAME = re.compile` |
| [lint_service](modules/lint_service.md) | `MERMAID_CLICK_RE = re.compile`, `MERMAID_NODE_RE = re.compile`, `_CountKey = TypeVar` |
| [lockfile](modules/lockfile.md) | `_CONTENTION_ERRNOS = frozenset`, `_WINDOWS_CONTENTION_ERRORS = frozenset` |
| [manifest_storage](modules/manifest_storage.md) | `OBJECT_NAME = re.compile` |
| [markdown_sections](modules/markdown_sections.md) | `GENERATED_INDEX_INTROS = frozenset`, `_ATX_HEADING_RE = re.compile`, `_FENCE_OPEN_RE = re.compile`, `_LEGACY_HEADING_RE = re.compile`, `_AUTO_GENERATED_RE = re.compile`, `_INDEX_GENERATED_HEADINGS = frozenset` |
| [mcp_server](modules/mcp_server.md) | `_SEARCH_KINDS = set`, `_QUALIFIED_GRAPH_KIND_RE = re.compile` |
| [obsidian](modules/obsidian.md) | `MARKDOWN_LINK_RE = re.compile`, `WIKILINK_RE = re.compile`, `LOCATION_RE = re.compile`, `PATH_RE = re.compile`, `LLM_WIKI_FRONTMATTER_RE = re.compile`, `PROJECTED_FRONTMATTER_KEY_RE = re.compile`, `PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile`, `LLM_WIKI_FRESHNESS_RE = re.compile`, `TOP_LEVEL_PROJECTED_FRONTMATTER_KEY_RE = re.compile`, `TOP_LEVEL_PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile`, `FRONTMATTER_END_BYTES_RE = re.compile` |
| [packet_field_policy](modules/packet_field_policy.md) | `SCALAR = FieldPolicy`, `STRUCTURAL_PATH_FIELDS = frozenset`, `PUBLIC_URI_FIELDS = frozenset`, `REPOSITORY_KEY_SPACES = frozenset`, `REPOSITORY_LIST_SPACES = frozenset`, `FILTERS = _record`, `BOUND = _record`, `SOURCE_BOUNDS = _record`, `FRESHNESS = _record`, `ENDPOINT = _record`, `COVERAGE = _record`, `CONCEPT = _record`, `PAGE = _record`, `RELATIONSHIP = _record`, `KNOWLEDGE = _record`, `BASIS = _record`, `RECEIPT = _record`, `POLICIES = MappingProxyType` |
| [paths](modules/paths.md) | `_TEST_DIRECTORY_NAMES = frozenset`, `_TEST_FILE_STEMS = frozenset` |
| [plugins](modules/plugins.md) | `_ID_RE = re.compile`, `_MODULE_RE = re.compile`, `_ATTR_RE = re.compile`, `_PROMPT_GIT_MUTATION_RE = re.compile`, `_RUNTIME_CACHE_DIRECTORIES = frozenset`, `_ACTIVATED_PATHS = set`, `_PLUGIN_LOAD_LOCK = threading.RLock` |
| [progress](modules/progress.md) | `_CURRENT = contextvars.ContextVar`, `_LABEL = re.compile`, `_COUNTERS = frozenset`, `_F = TypeVar` |
| [python_stdlib](modules/python_stdlib.md) | `_PYTHON_STDLIB_FALLBACK = frozenset` |
| [redaction](modules/redaction.md) | `SENSITIVE_KEYS = frozenset`, `SENSITIVE_KEY_RE = re.compile`, `PRIVATE_KEY_BLOCK_RE = re.compile`, `SENSITIVE_ASSIGNMENT_RE = re.compile`, `SENSITIVE_NATURAL_LANGUAGE_RE = re.compile`, `_REDACTION_SENSITIVE_ASSIGNMENT_RE = re.compile`, `_REDACTION_SENSITIVE_NATURAL_LANGUAGE_RE = re.compile`, `URI_USERINFO_RE = re.compile`, `PROJECTION_URI_USERINFO_RE = re.compile`, `_REDACTABLE_URI_USERINFO_RE = re.compile`, `_REDACTABLE_PROJECTION_URI_USERINFO_RE = re.compile`, `LIKELY_SECRET_RE = re.compile`, `CREDENTIAL_VALUE_RE = re.compile`, `_AUTHORIZATION_VALUE_RE = re.compile` |
| [resource_diagnostics](modules/resource_diagnostics.md) | `_MISSING_ERRNO = object`, `_ENOSPC = getattr`, `_EMFILE = getattr`, `_ENFILE = getattr`, `_ENOMEM = getattr`, `_EAGAIN = getattr` |
| [review_service](modules/review_service.md) | `_SOURCE_EXTS = tuple` |
| [services_schema](modules/services_schema.md) | `_SCHEMA_PROFILE_MARKER_RE = re.compile`, `_SOURCE_READING_RECIPE_COMMANDS = frozenset` |
| [search_rank](modules/search_rank.md) | `_STOP_WORDS = frozenset`, `_WORDS = re.compile`, `_SYMBOL = re.compile`, `_LINK = re.compile` |
| [search_service](modules/search_service.md) | `SEARCH_KINDS = frozenset` |
| [section_ownership](modules/section_ownership.md) | `_INDEX_GENERATED_HEADINGS = frozenset`, `_ENTITY_GENERATED_HEADINGS = frozenset`, `_ENTITY_MIXED_HEADINGS = frozenset`, `_MODULE_GENERATED_HEADINGS = frozenset`, `_MODULE_MIXED_HEADINGS = frozenset`, `_WORKFLOW_GENERATED_HEADINGS = frozenset`, `_FLOW_GENERATED_HEADINGS = frozenset`, `_API_GENERATED_HEADINGS = frozenset`, `_DEPENDENCIES_GENERATED_HEADINGS = frozenset`, `_LOAD_ORDER_GENERATED_HEADINGS = frozenset`, `_INFRASTRUCTURE_GENERATED_HEADINGS = frozenset`, `_HTTP_OPERATION_HEADING_RE = re.compile`, `_LOG_DATE_HEADING_RE = re.compile` |
| [site_export](modules/site_export.md) | `SUPPORTED_SITE_FORMATS = frozenset`, `SUPPORTED_SITE_PROFILES = frozenset`, `SUPPORTED_KNOWLEDGE_METADATA = frozenset`, `SITE_PUBLICATION_STATES = frozenset`, `MARKDOWN_LINK_RE = re.compile`, `_RAW_MEDIA_HTML_RE = re.compile`, `FRONT_MATTER_KEY_RE = re.compile` |
| [site_html_check](modules/site_html_check.md) | `SUPPORTED_LINK_MODES = frozenset`, `_IGNORED_SCHEMES = frozenset`, `_HREF_TAGS = frozenset`, `_MEDIA_SRC_TAGS = frozenset` |
| [skills](modules/skills.md) | `REFERENCE_DEPENDENT_SKILLS = frozenset` |
| [source_selection](modules/source_selection.md) | `_UNSET_SELECTION_INPUTS = object`, `_SOURCE_SELECTION_ORIGINS = frozenset`, `_GLOB_CHARACTERS = frozenset`, `_SHA256_RE = re.compile` |
| [source_snapshot](modules/source_snapshot.md) | `_UNSET_EXPECTED_SELECTION_INPUTS = object` |
| [storage_receipts](modules/storage_receipts.md) | `_HEX = re.compile` |
| [sync_manifest](modules/sync_manifest.md) | `_REASON_RE = re.compile`, `_CONCEPT_PAGE_RE = re.compile` |
| [task_context](modules/task_context.md) | `_LIVE_FACETS = frozenset`, `_NATIVE_FACETS = frozenset` |
| [task_contract](modules/task_contract.md) | `FACETS = frozenset`, `ANCHOR_KINDS = frozenset`, `TASK_KINDS = frozenset` |
| [validation](modules/validation.md) | `_WINDOWS_ABSOLUTE_RE = re.compile`, `_WINDOWS_DRIVE_PREFIX_RE = re.compile`, `_WINDOWS_RESERVED_NAMES = frozenset`, `_WINDOWS_FORBIDDEN_PATH_CHARS = frozenset`, `_UNSAFE_PAGE_COMPONENT_RE = re.compile`, `_SHA256_RE = re.compile`, `_ZERO_UTC_OFFSET = timedelta`, `_PATH_SYNTAX = OrderedDict`, `_PATH_SYNTAX_LOCK = RLock`, `_ASCII_CONTROL = re.compile`, `_ASCII_CONTROL_DELETE = re.compile`, `_EnumValue = TypeVar` |
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

Every module has a determinate position: no group imports itself into a cycle
while loading, so this order is complete rather than partial. The ordering
counts only imports that execute on load — imports written inside a function or
under `TYPE_CHECKING` constrain nothing, which is why the calibration and
documentation-run packages sort normally despite referring to each other. Avoid
adding observable import-time work; prefer explicit constructors and command
entry points. Runtime plugin discovery and lazy transports can still introduce
edges that this static projection cannot show. Use
[dependencies](dependencies.md) for fan-in, fan-out, package reconciliation, and
the groups that are cyclic only through deferred imports.
