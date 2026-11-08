# Load order

Topological module load / startup order and import-time side effects.

## Load order

<!-- Dependency-first order: each module loads after the internal modules it imports. -->
1. [esbuild.config](modules/esbuild.config.md)
2. [llm-wiki_main](modules/llm-wiki_main.md)
3. [src_main](modules/src_main.md)
4. [provider](modules/provider.md)
5. [llm_wiki_cli___init__](modules/llm_wiki_cli___init__.md)
6. [api_types](modules/api_types.md)
7. [detectors](modules/detectors.md)
8. [styles](modules/styles.md)
9. [extractors___init__](modules/extractors___init__.md)
10. [fastapi_contracts](modules/fastapi_contracts.md)
11. [python_bindings](modules/python_bindings.md)
12. [analysis_compatibility](modules/analysis_compatibility.md)
13. [analysis_targets](modules/analysis_targets.md)
14. [bootstrap_service](modules/bootstrap_service.md)
15. [calibration___init__](modules/calibration___init__.md)
16. [canonical_json](modules/canonical_json.md)
17. [circuit_breaker](modules/circuit_breaker.md)
18. [services_contracts](modules/services_contracts.md)
19. [context_knowledge_contract](modules/context_knowledge_contract.md)
20. [current_contracts](modules/current_contracts.md)
21. [dockerfile_parser](modules/dockerfile_parser.md)
22. [extraction_jobs](modules/extraction_jobs.md)
23. [filesystem_guard](modules/filesystem_guard.md)
24. [freshness_wording](modules/freshness_wording.md)
25. [go_calls](modules/go_calls.md)
26. [health_policy](modules/health_policy.md)
27. [health_summary](modules/health_summary.md)
28. [immutable](modules/immutable.md)
29. [analysis_capture](modules/analysis_capture.md)
30. [flow_overview](modules/flow_overview.md)
31. [knowledge_storage](modules/knowledge_storage.md)
32. [knowledge_audit](modules/knowledge_audit.md)
33. [lockfile](modules/lockfile.md)
34. [normalization_diagnostics](modules/normalization_diagnostics.md)
35. [packet_field_policy](modules/packet_field_policy.md)
36. [paths](modules/paths.md)
37. [progress](modules/progress.md)
38. [knowledge_packs](modules/knowledge_packs.md)
39. [python_calls](modules/python_calls.md)
40. [python_implementation](modules/python_implementation.md)
41. [implementation_evidence](modules/implementation_evidence.md)
42. [python_observations](modules/python_observations.md)
43. [python_stdlib](modules/python_stdlib.md)
44. [python_imports](modules/python_imports.md)
45. [python_contracts](modules/python_contracts.md)
46. [redaction](modules/redaction.md)
47. [request_json](modules/request_json.md)
48. [maintenance_cmd](modules/maintenance_cmd.md)
49. [resource_diagnostics](modules/resource_diagnostics.md)
50. [runtime_output](modules/runtime_output.md)
51. [search_rank](modules/search_rank.md)
52. [secure_file](modules/secure_file.md)
53. [storage_receipts](modules/storage_receipts.md)
54. [storage_sort](modules/storage_sort.md)
55. [storage_spool](modules/storage_spool.md)
56. [task_compact_readable](modules/task_compact_readable.md)
57. [token_counting](modules/token_counting.md)
58. [validation](modules/validation.md)
59. [planner](modules/planner.md)
60. [eval_lite___init__](modules/eval_lite___init__.md)
61. [broker](modules/broker.md)
62. [host_broker](modules/host_broker.md)
63. [data_flow](modules/data_flow.md)
64. [documentation_model_policy](modules/documentation_model_policy.md)
65. [documentation_review](modules/documentation_review.md)
66. [knowledge_evidence](modules/knowledge_evidence.md)
67. [io](modules/io.md)
68. [query_cmd](modules/query_cmd.md)
69. [task_cmd](modules/task_cmd.md)
70. [config](modules/config.md)
71. [mcp_cmd](modules/mcp_cmd.md)
72. [search_cmd](modules/search_cmd.md)
73. [common](modules/common.md)
74. [native_diagnostics](modules/native_diagnostics.md)
75. [helper_runtime](modules/helper_runtime.md)
76. [imports](modules/imports.md)
77. [python_extractor](modules/python_extractor.md)
78. [knowledge_reuse](modules/knowledge_reuse.md)
79. [knowledge_storage_io](modules/knowledge_storage_io.md)
80. [reference_cmd](modules/reference_cmd.md)
81. [cli_reference](modules/cli_reference.md)
82. [legacy_hooks](modules/legacy_hooks.md)
83. [hook_cmd](modules/hook_cmd.md)
84. [maintenance_protocol](modules/maintenance_protocol.md)
85. [maintenance_recovery](modules/maintenance_recovery.md)
86. [maintenance_shapes](modules/maintenance_shapes.md)
87. [maintenance_state](modules/maintenance_state.md)
88. [maintenance_projection](modules/maintenance_projection.md)
89. [markdown_sections](modules/markdown_sections.md)
90. [packages](modules/packages.md)
91. [plugins](modules/plugins.md)
92. [diagrams](modules/diagrams.md)
93. [plugin_samples](modules/plugin_samples.md)
94. [protected_artifacts](modules/protected_artifacts.md)
95. [publication_links](modules/publication_links.md)
96. [relationships](modules/relationships.md)
97. [services_schema](modules/services_schema.md)
98. [install_cmd](modules/install_cmd.md)
99. [plugins_cmd](modules/plugins_cmd.md)
100. [skills](modules/skills.md)
101. [skills_cmd](modules/skills_cmd.md)
102. [instruction_ownership](modules/instruction_ownership.md)
103. [rendering_lifecycle](modules/rendering_lifecycle.md)
104. [source_selection](modules/source_selection.md)
105. [documentation_policy](modules/documentation_policy.md)
106. [source_snapshot](modules/source_snapshot.md)
107. [api_contracts](modules/api_contracts.md)
108. [api_diff](modules/api_diff.md)
109. [api_diff_cmd](modules/api_diff_cmd.md)
110. [dependency_versions](modules/dependency_versions.md)
111. [services_dependencies](modules/services_dependencies.md)
112. [entrypoints](modules/entrypoints.md)
113. [inventory_cache](modules/inventory_cache.md)
114. [module_coverage](modules/module_coverage.md)
115. [module_maps](modules/module_maps.md)
116. [source_path_diagnostics](modules/source_path_diagnostics.md)
117. [sync_analysis_storage](modules/sync_analysis_storage.md)
118. [sync_analysis_cache](modules/sync_analysis_cache.md)
119. [sync_manifest](modules/sync_manifest.md)
120. [manifest_storage](modules/manifest_storage.md)
121. [team](modules/team.md)
122. [typescript_helper_identity](modules/typescript_helper_identity.md)
123. [extractor_helpers](modules/extractor_helpers.md)
124. [go_extractor](modules/go_extractor.md)
125. [haskell_extractor](modules/haskell_extractor.md)
126. [rust_extractor](modules/rust_extractor.md)
127. [ts_extractor](modules/ts_extractor.md)
128. [capability_diagnostics](modules/capability_diagnostics.md)
129. [helper_cache](modules/helper_cache.md)
130. [helper_preparation](modules/helper_preparation.md)
131. [prepare_extractors_cmd](modules/prepare_extractors_cmd.md)
132. [versioning](modules/versioning.md)
133. [bump_cmd](modules/bump_cmd.md)
134. [release_cmd](modules/release_cmd.md)
135. [wiki_git_policy](modules/wiki_git_policy.md)
136. [wiki_media](modules/wiki_media.md)
137. [search_lexical](modules/search_lexical.md)
138. [site_html_check](modules/site_html_check.md)
139. [wiki_scaffold](modules/wiki_scaffold.md)
140. [wiki_surface](modules/wiki_surface.md)
141. [concept_identity](modules/concept_identity.md)
142. [knowledge_graph](modules/knowledge_graph.md)
143. [knowledge_model](modules/knowledge_model.md)
144. [knowledge_envelope](modules/knowledge_envelope.md)
145. [knowledge_freshness](modules/knowledge_freshness.md)
146. [health_contract](modules/health_contract.md)
147. [knowledge_governance](modules/knowledge_governance.md)
148. [knowledge_links](modules/knowledge_links.md)
149. [knowledge_storage_access](modules/knowledge_storage_access.md)
150. [knowledge_stream_audit](modules/knowledge_stream_audit.md)
151. [publication_config](modules/publication_config.md)
152. [publication_contracts](modules/publication_contracts.md)
153. [publication_references](modules/publication_references.md)
154. [section_ownership](modules/section_ownership.md)
155. [maintenance_evidence](modules/maintenance_evidence.md)
156. [maintenance_status](modules/maintenance_status.md)
157. [search_discovery](modules/search_discovery.md)
158. [source_retirement](modules/source_retirement.md)
159. [sync_retained_links](modules/sync_retained_links.md)
160. [task_implementation](modules/task_implementation.md)
161. [verification_contracts](modules/verification_contracts.md)
162. [wiki_lifecycle](modules/wiki_lifecycle.md)
163. [init_cmd](modules/init_cmd.md)
164. [upgrade_cmd](modules/upgrade_cmd.md)
165. [ci_installer](modules/ci_installer.md)
166. [install_ci_cmd](modules/install_ci_cmd.md)
167. [uninstall_cmd](modules/uninstall_cmd.md)
168. [wiki_surface_index](modules/wiki_surface_index.md)
169. [calibration_contracts](modules/calibration_contracts.md)
170. [documentation_worklist](modules/documentation_worklist.md)
171. [knowledge_index](modules/knowledge_index.md)
172. [wiki_write_basis](modules/wiki_write_basis.md)
173. [bootstrap_recovery](modules/bootstrap_recovery.md)
174. [sync_recovery](modules/sync_recovery.md)
175. [workflow_profile](modules/workflow_profile.md)
176. [yaml_syntax](modules/yaml_syntax.md)
177. [extraction_service](modules/extraction_service.md)
178. [yaml_formats](modules/yaml_formats.md)
179. [infrastructure_inventory](modules/infrastructure_inventory.md)
180. [team_cmd](modules/team_cmd.md)
181. [infrastructure_sync](modules/infrastructure_sync.md)
182. [canonical_pages](modules/canonical_pages.md)
183. [knowledge_artifacts](modules/knowledge_artifacts.md)
184. [knowledge_generation](modules/knowledge_generation.md)
185. [knowledge_loader](modules/knowledge_loader.md)
186. [knowledge_consumption](modules/knowledge_consumption.md)
187. [evidence_diagnostics](modules/evidence_diagnostics.md)
188. [health_details](modules/health_details.md)
189. [knowledge_coverage](modules/knowledge_coverage.md)
190. [knowledge_observability](modules/knowledge_observability.md)
191. [knowledge_cmd](modules/knowledge_cmd.md)
192. [status_cmd](modules/status_cmd.md)
193. [documentation_queries](modules/documentation_queries.md)
194. [documentation_claim_evidence](modules/documentation_claim_evidence.md)
195. [documentation_wiki_input](modules/documentation_wiki_input.md)
196. [evidence_explanation](modules/evidence_explanation.md)
197. [flow_followup](modules/flow_followup.md)
198. [knowledge_orchestration](modules/knowledge_orchestration.md)
199. [bootstrap_runtime](modules/bootstrap_runtime.md)
200. [migrate_cmd](modules/migrate_cmd.md)
201. [change_selection](modules/change_selection.md)
202. [documentation_native](modules/documentation_native.md)
203. [wiki-candidate_prepare](modules/wiki-candidate_prepare.md)
204. [knowledge_maintenance](modules/knowledge_maintenance.md)
205. [knowledge_projection](modules/knowledge_projection.md)
206. [knowledge_storage_lifecycle](modules/knowledge_storage_lifecycle.md)
207. [knowledge_storage_diagnostics](modules/knowledge_storage_diagnostics.md)
208. [knowledge_storage_cmd](modules/knowledge_storage_cmd.md)
209. [knowledge_verification](modules/knowledge_verification.md)
210. [documentation_query_builder](modules/documentation_query_builder.md)
211. [context_service](modules/context_service.md)
212. [context_packet](modules/context_packet.md)
213. [context_budget](modules/context_budget.md)
214. [documentation_run_dependencies](modules/documentation_run_dependencies.md)
215. [documentation_run_contracts](modules/documentation_run_contracts.md)
216. [documentation_run_schema](modules/documentation_run_schema.md)
217. [workspace](modules/workspace.md)
218. [integrity](modules/integrity.md)
219. [packet](modules/packet.md)
220. [refresh](modules/refresh.md)
221. [documentation_run_prepare](modules/documentation_run_prepare.md)
222. [record](modules/record.md)
223. [verify](modules/verify.md)
224. [export](modules/export.md)
225. [documentation_run___init__](modules/documentation_run___init__.md)
226. [controller](modules/controller.md)
227. [lint_service](modules/lint_service.md)
228. [doctor_service](modules/doctor_service.md)
229. [doctor_cmd](modules/doctor_cmd.md)
230. [ci_report](modules/ci_report.md)
231. [render_summary](modules/render_summary.md)
232. [maintenance_queue](modules/maintenance_queue.md)
233. [queue_cmd](modules/queue_cmd.md)
234. [maintenance_service](modules/maintenance_service.md)
235. [metrics](modules/metrics.md)
236. [ci_check_cmd](modules/ci_check_cmd.md)
237. [generate_prompt_cmd](modules/generate_prompt_cmd.md)
238. [metrics_cmd](modules/metrics_cmd.md)
239. [trigger_cmd](modules/trigger_cmd.md)
240. [native_inspection](modules/native_inspection.md)
241. [obsidian](modules/obsidian.md)
242. [obsidian_cmd](modules/obsidian_cmd.md)
243. [publication_snapshot](modules/publication_snapshot.md)
244. [publication_impact](modules/publication_impact.md)
245. [checkout](modules/checkout.md)
246. [publication_cmd](modules/publication_cmd.md)
247. [publication_candidate_cmd](modules/publication_candidate_cmd.md)
248. [docs_cmd](modules/docs_cmd.md)
249. [publication_candidate](modules/publication_candidate.md)
250. [run](modules/run.md)
251. [review_service](modules/review_service.md)
252. [review_cmd](modules/review_cmd.md)
253. [impact](modules/impact.md)
254. [scoped_sync_repair](modules/scoped_sync_repair.md)
255. [search_service](modules/search_service.md)
256. [search_source](modules/search_source.md)
257. [search_discovery_capture](modules/search_discovery_capture.md)
258. [site_export](modules/site_export.md)
259. [site_cmd](modules/site_cmd.md)
260. [sync_analysis](modules/sync_analysis.md)
261. [sync_transitions](modules/sync_transitions.md)
262. [sync_generated_sections](modules/sync_generated_sections.md)
263. [sync_transition_execution](modules/sync_transition_execution.md)
264. [sync_cmd](modules/sync_cmd.md)
265. [cli](modules/cli.md)
266. [commands___init__](modules/commands___init__.md)
267. [task_contract](modules/task_contract.md)
268. [task_evidence](modules/task_evidence.md)
269. [task_context](modules/task_context.md)
270. [task_compact](modules/task_compact.md)
271. [context_session](modules/context_session.md)
272. [api](modules/api.md)
273. [mcp_server](modules/mcp_server.md)
274. [task_compact_delivery](modules/task_compact_delivery.md)
275. [task_context_v2](modules/task_context_v2.md)
276. [wiki_git_delivery](modules/wiki_git_delivery.md)

## Module-level side effects

| Module | Import-time calls |
|--------|-------------------|
| [render_summary](modules/render_summary.md) | `FRESHNESS_STATES = frozenset`, `AVAILABILITY_STATES = frozenset`, `SNAPSHOT_STATES = frozenset`, `GOVERNANCE_STATES = frozenset`, `GOVERNANCE_LEDGER_STATES = frozenset`, `GOVERNANCE_PROJECTION_STATES = frozenset`, `DRIFT_STATES = frozenset`, `VERIFICATION_STATES = frozenset`, `RECORDED_RESULTS = frozenset`, `REPORT_FIELDS = frozenset`, `AVAILABILITY_FIELDS = frozenset`, `FRESHNESS_FIELDS = frozenset`, `SNAPSHOT_FIELDS = frozenset`, `GOVERNANCE_FIELDS = frozenset`, `DRIFT_FIELDS = frozenset`, `VERIFICATION_FIELDS = frozenset` |
| [llm-wiki_main](modules/llm-wiki_main.md) | `__export`, `module.exports = __toCommonJS`, `import_obsidian = require`, `import_child_process = require` |
| [provider](modules/provider.md) | `FULL_SHA = re.compile` |
| [llm_wiki_cli___init__](modules/llm_wiki_cli___init__.md) | `__version__ = version` |
| [api](modules/api.md) | `_CALIBRATION_CONTROLLER_TYPE_EXPORTS = frozenset`, `_CALIBRATION_HOST_TYPE_EXPORTS = frozenset`, `_CALIBRATION_CONTROLLER_MODULES = frozenset`, `_CALIBRATION_HOST_MODULES = frozenset`, `_WIKI_INPUT_ARTIFACT_CATEGORIES = frozenset`, `_WIKI_INPUT_WORKSPACE_CATEGORIES = frozenset`, `_P = ParamSpec`, `_R = TypeVar`, `setattr`, `_NATIVE_QUERY_ERROR_FIELDS = frozenset`, `_QUALIFIED_GRAPH_KIND_RE = re.compile`, `install_documentation_ci_workflow = _api_boundary`, `adopt_documentation_wiki_snapshot = _api_boundary`, `fingerprint_documentation_wiki_input = _api_boundary`, `prepare_documentation_run = _api_boundary`, `get_documentation_run_status = _api_boundary`, `build_documentation_agent_packet = _api_boundary`, `record_documentation_agent_result = _api_boundary`, `verify_documentation_run = _api_boundary`, `select_documentation_model = _api_boundary`, `validate_documentation_model_selection = _api_boundary`, `setattr`, `prepare_p0_calibration_run = _deprecated_api_alias`, `admit_p0_calibration_run = _deprecated_api_alias`, `get_p0_calibration_run_status = _deprecated_api_alias`, `build_p0_calibration_agent_packet = _deprecated_api_alias`, `dispatch_p0_calibration_agent = _deprecated_api_alias`, `record_p0_calibration_agent_result = _deprecated_api_alias`, `verify_p0_calibration_run = _deprecated_api_alias`, `use_p0_calibration_host_broker_authenticator = _deprecated_api_alias` |
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
| [python_bindings](modules/python_bindings.md) | `BUILTIN_NAMES = frozenset`, `_NAMESPACE_MUTATORS = frozenset`, `_DISPATCH_SLOTS = frozenset` |
| [python_extractor](modules/python_extractor.md) | `_TYPE_CHECKING_MODULES = frozenset` |
| [analysis_capture](modules/analysis_capture.md) | `_ISSUER = object`, `_CAPTURE = ContextVar`, `REGISTRY_PATH = Path(__file__).with_name` |
| [analysis_compatibility](modules/analysis_compatibility.md) | `POLICIES = frozenset`, `_ACTIVE = ContextVar`, `_HASH = re.compile`, `_FIELDS = frozenset`, `_P = ParamSpec`, `_R = TypeVar` |
| [api_contracts](modules/api_contracts.md) | `_STATUS_REF_RE = re.compile`, `_PATH_PARAMETER_RE = re.compile`, `_SAFE_ID_RE = re.compile`, `_NONE_ANNOTATION_RE = re.compile`, `_UNKNOWN = object` |
| [bootstrap_runtime](modules/bootstrap_runtime.md) | `_SOURCE_DOC_LINK_RE = re.compile`, `_FLOWCHART_NODE_LINE = re.compile` |
| [broker](modules/broker.md) | `SUPPORTED_OCI_RUNTIMES = frozenset`, `SUPPORTED_AGENT_ROLES = frozenset`, `_SLUG_RE = re.compile`, `_IDEMPOTENCY_RE = re.compile`, `_PUBLIC_RECIPIENT_RE = re.compile`, `_CONTAINER_NAME_RE = re.compile`, `_IMAGE_RE = re.compile`, `_NUMERIC_USER_RE = re.compile`, `_HEX_32_RE = re.compile`, `_CONTROL_RE = re.compile`, `_RECEIPT_STATUSES = frozenset`, `_CLEANUP_STATUSES = frozenset`, `_restore_legacy_definition_modules` |
| [calibration_contracts](modules/calibration_contracts.md) | `_CALIBRATION_PRIORITIES = frozenset`, `_SOURCE_PROVENANCE = frozenset`, `_CONFIDENCE_VALUES = frozenset`, `_MUTATION_HTTP_METHODS = frozenset`, `_restore_legacy_definition_modules` |
| [controller](modules/controller.md) | `CALIBRATION_TERMINAL_STATES = frozenset`, `ADMISSION_PROFILES = frozenset`, `_PORTABLE_ID_RE = re.compile`, `_EXTERNAL_DISPATCH_FAILURE_REASONS = frozenset`, `_DOCUMENT_SUFFIXES = frozenset`, `_ROOT_DOCUMENT_NAMES = frozenset`, `_PROJECT_MANIFEST_NAMES = frozenset`, `_ALLOWED_ROOT_FILES = frozenset`, `_ALLOWED_ROOT_DIRS = frozenset`, `_FILE_URI_RE = re.compile`, `_WINDOWS_ABSOLUTE_PATH_RE = re.compile`, `_POSIX_ABSOLUTE_PATH_RE = re.compile`, `admit_p0_calibration_run = _deprecated_calibration_alias`, `build_p0_calibration_agent_packet = _deprecated_calibration_alias`, `dispatch_p0_calibration_agent = _deprecated_calibration_alias`, `get_p0_calibration_run_status = _deprecated_calibration_alias`, `prepare_p0_calibration_run = _deprecated_calibration_alias`, `record_p0_calibration_agent_result = _deprecated_calibration_alias`, `verify_p0_calibration_run = _deprecated_calibration_alias`, `_restore_legacy_definition_modules` |
| [host_broker](modules/host_broker.md) | `_HOST_BROKER_AUTHENTICATOR = ContextVar`, `use_p0_calibration_host_broker_authenticator.__name__ = 'use_p0_calibration_host_broker_authenticator'`, `use_p0_calibration_host_broker_authenticator.__qualname__ = 'use_p0_calibration_host_broker_authenticator'`, `_restore_legacy_definition_modules` |
| [canonical_json](modules/canonical_json.md) | `_ESCAPED = re.compile`, `_SHORT = frozenset` |
| [ci_installer](modules/ci_installer.md) | `MANAGED_WORKFLOW_PATH = Path`, `DOCUMENTATION_WORKFLOW_PATH = Path`, `_ACTION_REF_RE = re.compile`, `_MANAGED_HEADER_RE = re.compile` |
| [ci_report](modules/ci_report.md) | `_CI_REQUIRED_FIELDS = frozenset`, `_CI_OPTIONAL_FIELDS = frozenset`, `_KNOWLEDGE_SUMMARY_FIELDS = frozenset`, `_LINT_ISSUE_REQUIRED_FIELDS = frozenset`, `_LINT_ISSUE_OPTIONAL_FIELDS = frozenset`, `_EXTRACTOR_JOB_FIELDS = frozenset`, `_DOCTOR_FIELDS = frozenset`, `_AVAILABILITY_FIELDS = frozenset`, `_FRESHNESS_FIELDS = frozenset`, `_SNAPSHOT_FIELDS = frozenset`, `_GOVERNANCE_FIELDS = frozenset`, `_DRIFT_FIELDS = frozenset`, `_VERIFICATION_FIELDS = frozenset`, `_FRESHNESS_STATES = frozenset`, `_AVAILABILITY_STATES = frozenset`, `_SNAPSHOT_STATES = frozenset`, `_GOVERNANCE_STATES = frozenset`, `_GOVERNANCE_LEDGER_STATES = frozenset`, `_GOVERNANCE_PROJECTION_STATES = frozenset`, `_DRIFT_STATES = frozenset`, `_VERIFICATION_STATES = frozenset`, `_RECORDED_RESULTS = frozenset`, `_JSON_EVIDENCE_STATES = frozenset`, `_REASON_RE = re.compile` |
| [cli_reference](modules/cli_reference.md) | `_MODULE = re.compile`, `_QUALNAME = re.compile` |
| [concept_identity](modules/concept_identity.md) | `_BUNDLE_ID_RE = re.compile`, `_QUALIFIED_KIND_RE = re.compile`, `_NATURAL_KEY_PREFIX_RE = re.compile`, `_NATURAL_KEY_PAYLOAD_RE = re.compile`, `_PERCENT_ESCAPE_RE = re.compile`, `_INVALID_PERCENT_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_URI_SCHEME_RE = re.compile`, `_COLLISION_CODE_RE = re.compile`, `_COLLISION_COORDINATE_TYPE_RE = re.compile`, `_UID_RE = re.compile`, `_RecordT = TypeVar` |
| [context_knowledge_contract](modules/context_knowledge_contract.md) | `_LIFECYCLE_FIELDS = frozenset`, `_EVIDENCE_FIELDS = frozenset`, `_LIFECYCLE_EVIDENCE_FIELDS = frozenset`, `_CONTRACT_FIELDS = frozenset`, `_CONTRACT['lifecycle_evidence_matrix'] = [{'lifecycle_state': lifecycle['state'], 'evidence_state': evidence['state'], 'rendered_profile': lifecycle['rendered_profile'], 'read_only_knowledge': evidence['read_only_knowledge'], 'fallback_evidence': list(evidence['fallback_evidence']), 'mutation_permission': 'none', 'signals': _combined_signals(lifecycle, evidence), 'recovery_routes': _combined_recovery_routes(lifecycle, evidence)} for lifecycle in _CONTRACT['lifecycle_matrix'] for evidence in _CONTRACT['evidence_matrix']]`, `_CANONICAL_CONTRACT = deepcopy`, `_CANONICAL_CONTRACT_JSON = json.dumps`, `_CURRENT_CANONICAL_CONTRACT = deepcopy`, `_CURRENT_CANONICAL_CONTRACT['schema_version'] = CONTEXT_KNOWLEDGE_CONTRACT_SCHEMA_VERSION`, `_CURRENT_CANONICAL_CONTRACT['runtime_state']['default_packet_schema'] = QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION`, `_CURRENT_CANONICAL_CONTRACT['versioning']['packet_default'] = {**_PACKET_DEFAULTS, 'introduced_in': '3.0.0', 'legacy_interfaces': ['cli', 'python-api']}`, `_CURRENT_CANONICAL_CONTRACT['request']['omitted_behavior'] = 'interface-specific'`, `_CURRENT_CANONICAL_CONTRACT['request']['normalization']['omitted'] = 'interface-specific-default'`, `_CURRENT_CANONICAL_CONTRACT['interfaces']['packet']['default'] = 'auto'`, `_CURRENT_CANONICAL_CONTRACT['interfaces']['packet']['omission'] = 'use-current-v2-packet'`, `_CURRENT_CANONICAL_CONTRACT_JSON = json.dumps`, `validate_context_knowledge_contract`, `validate_context_knowledge_contract` |
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
| [extraction_service](modules/extraction_service.md) | `_MISSING_INVENTORY_REQUEST = object`, `_INVALID_DIFF_PATH = object` |
| [extractor_helpers](modules/extractor_helpers.md) | `GO_BUILD_RECIPE = ' '.join` |
| [filesystem_guard](modules/filesystem_guard.md) | `_EXPECTED_EXISTING_UNSET = object` |
| [flow_followup](modules/flow_followup.md) | `_BASIS_RE = re.compile` |
| [flow_overview](modules/flow_overview.md) | `_CALL_KINDS = frozenset` |
| [health_contract](modules/health_contract.md) | `FRESHNESS_STATES = frozenset`, `COMPARABLE_STATES = frozenset`, `_HASH = re.compile`, `_ID = re.compile` |
| [health_policy](modules/health_policy.md) | `_spec = importlib.util.spec_from_file_location`, `ac = importlib.util.module_from_spec`, `_spec.loader.exec_module`, `_HASH = re.compile`, `_SHA = re.compile` |
| [helper_runtime](modules/helper_runtime.md) | `_CONFIGURATION = ContextVar`, `_OPERATION = ContextVar` |
| [immutable](modules/immutable.md) | `_T = TypeVar` |
| [implementation_evidence](modules/implementation_evidence.md) | `SCOPES = frozenset`, `ANALYSIS_SCOPES = frozenset`, `UNAVAILABLE_REASONS = frozenset`, `SUMMARY_FIELDS = frozenset`, `_HASH = re.compile` |
| [imports](modules/imports.md) | `_GO_MODULE_EXCLUDED_DIRS = frozenset`, `_TS_CONFIG_EXCLUDED_DIRS = frozenset` |
| [instruction_ownership](modules/instruction_ownership.md) | `_ALL_PROFILES = tuple`, `_MAINTENANCE = _topic`, `_SURFACES_NAMING = _topic`, `_PUBLISHING = _topic`, `_EXTRACTORS = _topic`, `_ROUTER_TOPICS = tuple`, `_INSTALLED_REFERENCE_PATH = re.compile`, `_REFERENCE_ROOT_TOPIC_PATH = re.compile` |
| [knowledge_artifacts](modules/knowledge_artifacts.md) | `_KNOWLEDGE_SCHEMA_VERSION_RE = re.compile`, `_SURFACE_SCHEMA_VERSION_RE = re.compile` |
| [knowledge_consumption](modules/knowledge_consumption.md) | `_MACHINE_SCOPE_KINDS = frozenset`, `_MACHINE_INVALIDATION_REASONS = frozenset`, `_MACHINE_RESULT_VALUES = frozenset`, `_MACHINE_CHECKER_ID_RE = re.compile`, `_MACHINE_CHECKER_VERSION_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_MACHINE_SCOPE_UID_RE = re.compile`, `_MACHINE_SUBJECT_RE = re.compile` |
| [knowledge_coverage](modules/knowledge_coverage.md) | `_KINDS = frozenset` |
| [knowledge_envelope](modules/knowledge_envelope.md) | `_REPOSITORY_IDENTITY_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_INPUT_KIND_RE = re.compile`, `_WINDOWS_DRIVE_PREFIX_RE = re.compile`, `_MALFORMED_PERCENT_RE = re.compile`, `_SCP_REMOTE_RE = re.compile`, `_EFFECTIVE_LINE_ENDING_CONFIG_KEYS = frozenset`, `_CORE_EOL_VALUES = frozenset` |
| [knowledge_evidence](modules/knowledge_evidence.md) | `_SHA256_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_UNKNOWN_REASON_RE = re.compile`, `_SUPPORTED_OBSERVATION_LANGUAGES = frozenset`, `_LOCATION_ONLY_KEYS = frozenset`, `_POINTER_FIELDS = frozenset` |
| [knowledge_freshness](modules/knowledge_freshness.md) | `_STRUCTURAL_PAGE_KINDS = frozenset`, `_REASON_DESCRIPTIONS = MappingProxyType`, `KNOWN_FRESHNESS_REASON_CODES = frozenset`, `FRESHNESS_REASON_STATES = MappingProxyType` |
| [knowledge_governance](modules/knowledge_governance.md) | `ALIAS_TYPES = frozenset`, `ACTOR_KINDS = frozenset`, `REVIEW_EVIDENCE_MODES = frozenset`, `REVIEW_EXPIRY_REASONS = frozenset`, `_SAFE_ID_RE = re.compile`, `_EVENT_ID_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_CONTROL_RE = re.compile`, `_SENSITIVE_RE = re.compile`, `_MISSING = object` |
| [knowledge_graph](modules/knowledge_graph.md) | `_QUALIFIED_NAME_RE = re.compile`, `_LIMITATION_RE = re.compile`, `_CONTROL_RE = re.compile`, `_URI_RE = re.compile`, `_OBJECT_ERROR = partial`, `_OBJECT_KEYS_ERROR = partial`, `_ARRAY_ERROR = partial`, `_NAME_ERROR = partial`, `_HASH_ERROR = partial`, `_NONNEGATIVE_ERROR = partial`, `_POSITIVE_ERROR = partial` |
| [knowledge_index](modules/knowledge_index.md) | `_WINDOWS_ABSOLUTE_RE = re.compile`, `_MALFORMED_PERCENT_RE = re.compile`, `_MANIFEST_STRUCTURAL_PAGE_KINDS = frozenset`, `_STRUCTURAL_PAGE_KINDS = frozenset`, `_LINK_SYNTAX_VALUES = frozenset`, `_INDEX_VALIDATION_OPERATION = ContextVar`, `_INDEX_RECEIPT_ISSUER = object` |
| [knowledge_links](modules/knowledge_links.md) | `_MALFORMED_PERCENT_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_URI_CHARS_RE = re.compile` |
| [knowledge_model](modules/knowledge_model.md) | `_QUALIFIED_NAME_RE = re.compile`, `_REPOSITORY_IDENTITY_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_PERCENT_ESCAPE_RE = re.compile`, `_COMPONENT_ID_RE = re.compile`, `_URI_CHAR_RE = re.compile`, `_MISSING = object`, `_OBJECT_ERROR = partial`, `_OBJECT_KEYS_ERROR = partial`, `_UTF8_ERROR = partial`, `_ARRAY_ERROR = partial`, `_STRING_ERROR = partial`, `_NONEMPTY_ERROR = partial`, `_NONNEGATIVE_ERROR = partial`, `_LOCATION_BOUNDS_ERROR = partial`, `_POSITIVE_ERROR = partial`, `_HASH_ERROR = partial`, `PAGE_KIND_TO_CONCEPT_KIND = MappingProxyType`, `_SURFACE_KIND_BY_PAGE_KIND = MappingProxyType`, `_EnumT = TypeVar` |
| [knowledge_observability](modules/knowledge_observability.md) | `_FRESHNESS_COUNT_KEYS = frozenset`, `_EVIDENCE_ISSUE_KEYS = frozenset`, `_PHASE_DURATION_KEYS = frozenset`, `_REASON_VALUES = frozenset`, `_DEGRADED_REASON_VALUES = frozenset`, `_UNSUPPORTED_REASON_VALUES = frozenset`, `BASIS_INCOMPATIBLE_HINTS = MappingProxyType`, `BASIS_INCOMPATIBLE_REASON_CODES = frozenset` |
| [knowledge_orchestration](modules/knowledge_orchestration.md) | `_COMPONENT_PART_RE = re.compile`, `_RUNTIME_POLICY_KEYS = frozenset`, `_DEPENDENCY_GRAPH_DETAILS = frozenset`, `_COMMITTED_STATE_TOKEN = object` |
| [knowledge_packs](modules/knowledge_packs.md) | `INDEX_PAGE_NAME = re.compile`, `PACKED_FORMATS = frozenset`, `INDEX_NAME = re.compile`, `PACK_NAME = re.compile`, `_BITS = re.compile`, `_HEX = re.compile`, `_MEMBER = re.compile`, `_LOCAL_HEADER = struct.Struct`, `_END = struct.Struct` |
| [knowledge_projection](modules/knowledge_projection.md) | `_EVALUATED_FRESHNESS_DISCLOSURE_RE = re.compile`, `_RESERVED_EXTENSION_KEYS = frozenset`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_TRAVERSAL_RE = re.compile`, `_EMBEDDED_ABSOLUTE_RE = re.compile`, `_RAW_VCS_REMOTE_RE = re.compile`, `_CONTROL_RE = re.compile`, `_EVALUATED_REVISION_RE = re.compile`, `_LIMITATION_CODE_RE = re.compile`, `_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile`, `_SAFE_TOKEN_RE = re.compile`, `_REVIEW_EXPIRY_REASONS = frozenset`, `_REVIEW_STATES = frozenset`, `_MACHINE_INVALIDATION_REASONS = frozenset`, `_OMISSION_FIELDS = frozenset`, `_BASE_WARNING_VALUES = frozenset` |
| [knowledge_reuse](modules/knowledge_reuse.md) | `_HASH_FIELDS = frozenset`, `_STABLE_IMPLEMENTATION_GAPS = frozenset` |
| [knowledge_storage](modules/knowledge_storage.md) | `_HASH = re.compile`, `_PREFIX = re.compile`, `_RESERVED = frozenset`, `_INTERN_FIELDS = frozenset` |
| [knowledge_storage_lifecycle](modules/knowledge_storage_lifecycle.md) | `_OBJECT_NAME = re.compile` |
| [lint_service](modules/lint_service.md) | `MERMAID_CLICK_RE = re.compile`, `MERMAID_NODE_RE = re.compile`, `_CountKey = TypeVar` |
| [lockfile](modules/lockfile.md) | `_CONTENTION_ERRNOS = frozenset`, `_WINDOWS_CONTENTION_ERRORS = frozenset` |
| [maintenance_projection](modules/maintenance_projection.md) | `_HASH = re.compile` |
| [maintenance_protocol](modules/maintenance_protocol.md) | `_OWNED_STORAGE = ContextVar`, `_OWNED_GOVERNANCE = ContextVar`, `_STORAGE_STAGING_ISSUER = object` |
| [maintenance_queue](modules/maintenance_queue.md) | `_AUTHORING_HINTS = frozenset` |
| [maintenance_recovery](modules/maintenance_recovery.md) | `_HEX = re.compile` |
| [maintenance_state](modules/maintenance_state.md) | `_RECONCILIATION_OWNER = ContextVar` |
| [maintenance_status](modules/maintenance_status.md) | `_HASH = re.compile`, `ANALYSIS_SCOPES = frozenset`, `SUMMARY_FIELDS = frozenset` |
| [manifest_storage](modules/manifest_storage.md) | `OBJECT_NAME = re.compile` |
| [markdown_sections](modules/markdown_sections.md) | `GENERATED_INDEX_INTROS = frozenset`, `_ATX_HEADING_RE = re.compile`, `_FENCE_OPEN_RE = re.compile`, `_LEGACY_HEADING_RE = re.compile`, `_AUTO_GENERATED_RE = re.compile`, `_INDEX_GENERATED_HEADINGS = frozenset` |
| [mcp_server](modules/mcp_server.md) | `_SEARCH_KINDS = set`, `_QUALIFIED_GRAPH_KIND_RE = re.compile` |
| [normalization_diagnostics](modules/normalization_diagnostics.md) | `MISSING_VALUE = object` |
| [obsidian](modules/obsidian.md) | `MARKDOWN_LINK_RE = re.compile`, `WIKILINK_RE = re.compile`, `LOCATION_RE = re.compile`, `PATH_RE = re.compile`, `LLM_WIKI_FRONTMATTER_RE = re.compile`, `PROJECTED_FRONTMATTER_KEY_RE = re.compile`, `PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile`, `LLM_WIKI_FRESHNESS_RE = re.compile`, `TOP_LEVEL_PROJECTED_FRONTMATTER_KEY_RE = re.compile`, `TOP_LEVEL_PROJECTED_KNOWLEDGE_FRONTMATTER_KEY_RE = re.compile`, `FRONTMATTER_END_BYTES_RE = re.compile` |
| [packet_field_policy](modules/packet_field_policy.md) | `SCALAR = FieldPolicy`, `STRUCTURAL_PATH_FIELDS = frozenset`, `PUBLIC_URI_FIELDS = frozenset`, `REPOSITORY_KEY_SPACES = frozenset`, `REPOSITORY_LIST_SPACES = frozenset`, `FILTERS = _record`, `BOUND = _record`, `SOURCE_BOUNDS = _record`, `FRESHNESS = _record`, `IMPLEMENTATION = _record`, `MAINTENANCE = _record`, `ENDPOINT = _record`, `COVERAGE = _record`, `CONCEPT = _record`, `PAGE = _record`, `RELATIONSHIP = _record`, `KNOWLEDGE = _record`, `BASIS = _record`, `RECEIPT = _record`, `POLICIES = MappingProxyType` |
| [paths](modules/paths.md) | `_TEST_DIRECTORY_NAMES = frozenset`, `_TEST_FILE_STEMS = frozenset` |
| [plugins](modules/plugins.md) | `_ID_RE = re.compile`, `_MODULE_RE = re.compile`, `_ATTR_RE = re.compile`, `_PROMPT_GIT_MUTATION_RE = re.compile`, `_RUNTIME_CACHE_DIRECTORIES = frozenset`, `_ACTIVATED_PATHS = set`, `_PLUGIN_LOAD_LOCK = threading.RLock` |
| [progress](modules/progress.md) | `_CURRENT = contextvars.ContextVar`, `_LABEL = re.compile`, `_COUNTERS = frozenset`, `_F = TypeVar` |
| [publication_candidate](modules/publication_candidate.md) | `_HASH = re.compile`, `_REVISION = re.compile` |
| [publication_config](modules/publication_config.md) | `_METADATA_DIRECTORIES = frozenset`, `_IDENTIFIER = re.compile`, `_REPOSITORY = re.compile`, `_ANCHOR = re.compile`, `_GLOB = re.compile` |
| [publication_contracts](modules/publication_contracts.md) | `_TOPIC_ID = re.compile` |
| [publication_links](modules/publication_links.md) | `_PRIVATE_COMPONENTS = frozenset`, `_WIKI_LINK = re.compile`, `_REFERENCE = re.compile`, `_ESCAPE = re.compile`, `_FORMAT_TAGS = frozenset` |
| [python_implementation](modules/python_implementation.md) | `_HASH = re.compile`, `_LOCATIONS = frozenset` |
| [python_stdlib](modules/python_stdlib.md) | `_PYTHON_STDLIB_FALLBACK = frozenset` |
| [redaction](modules/redaction.md) | `SENSITIVE_KEYS = frozenset`, `SENSITIVE_KEY_RE = re.compile`, `PRIVATE_KEY_BLOCK_RE = re.compile`, `SENSITIVE_ASSIGNMENT_RE = re.compile`, `SENSITIVE_NATURAL_LANGUAGE_RE = re.compile`, `_REDACTION_SENSITIVE_ASSIGNMENT_RE = re.compile`, `_REDACTION_SENSITIVE_NATURAL_LANGUAGE_RE = re.compile`, `URI_USERINFO_RE = re.compile`, `PROJECTION_URI_USERINFO_RE = re.compile`, `_REDACTABLE_URI_USERINFO_RE = re.compile`, `_REDACTABLE_PROJECTION_URI_USERINFO_RE = re.compile`, `LIKELY_SECRET_RE = re.compile`, `CREDENTIAL_VALUE_RE = re.compile`, `_AUTHORIZATION_VALUE_RE = re.compile` |
| [resource_diagnostics](modules/resource_diagnostics.md) | `_MISSING_ERRNO = object`, `_ENOSPC = getattr`, `_EMFILE = getattr`, `_ENFILE = getattr`, `_ENOMEM = getattr`, `_EAGAIN = getattr` |
| [review_service](modules/review_service.md) | `_SOURCE_EXTS = tuple` |
| [services_schema](modules/services_schema.md) | `_SCHEMA_PROFILE_MARKER_RE = re.compile`, `_SOURCE_READING_RECIPE_COMMANDS = frozenset` |
| [search_discovery](modules/search_discovery.md) | `_SHA = re.compile`, `_REVIEW_FIELDS = frozenset`, `_REVIEW_REQUIRED = frozenset`, `_BOUND_FIELDS = frozenset` |
| [search_lexical](modules/search_lexical.md) | `_SEMANTIC = frozenset`, `_DEFINITIONS = frozenset`, `_INVENTORY = frozenset`, `_FLOW_INVENTORY = frozenset`, `_FLOW_PLACEHOLDER = re.compile`, `_LINK = re.compile`, `_SYMBOL = re.compile`, `_ENTRY_POINT = re.compile`, `_ENTRY_SOURCE = re.compile` |
| [search_rank](modules/search_rank.md) | `_STOP_WORDS = frozenset`, `_WORDS = re.compile`, `_SYMBOL = re.compile`, `_LINK = re.compile` |
| [search_service](modules/search_service.md) | `SEARCH_KINDS = frozenset` |
| [section_ownership](modules/section_ownership.md) | `_INDEX_GENERATED_HEADINGS = frozenset`, `_ENTITY_GENERATED_HEADINGS = frozenset`, `_ENTITY_MIXED_HEADINGS = frozenset`, `_MODULE_GENERATED_HEADINGS = frozenset`, `_MODULE_MIXED_HEADINGS = frozenset`, `_WORKFLOW_GENERATED_HEADINGS = frozenset`, `_FLOW_GENERATED_HEADINGS = frozenset`, `_API_GENERATED_HEADINGS = frozenset`, `_DEPENDENCIES_GENERATED_HEADINGS = frozenset`, `_LOAD_ORDER_GENERATED_HEADINGS = frozenset`, `_INFRASTRUCTURE_GENERATED_HEADINGS = frozenset`, `_HTTP_OPERATION_HEADING_RE = re.compile`, `_LOG_DATE_HEADING_RE = re.compile` |
| [site_export](modules/site_export.md) | `SUPPORTED_SITE_FORMATS = frozenset`, `SUPPORTED_SITE_PROFILES = frozenset`, `SUPPORTED_KNOWLEDGE_METADATA = frozenset`, `SITE_PUBLICATION_STATES = frozenset`, `MARKDOWN_LINK_RE = re.compile`, `_RAW_MEDIA_HTML_RE = re.compile`, `FRONT_MATTER_KEY_RE = re.compile` |
| [site_html_check](modules/site_html_check.md) | `SUPPORTED_LINK_MODES = frozenset`, `_IGNORED_SCHEMES = frozenset`, `_HREF_TAGS = frozenset`, `_MEDIA_SRC_TAGS = frozenset` |
| [skills](modules/skills.md) | `REFERENCE_DEPENDENT_SKILLS = frozenset` |
| [source_selection](modules/source_selection.md) | `_UNSET_SELECTION_INPUTS = object`, `_SOURCE_SELECTION_ORIGINS = frozenset`, `_GLOB_CHARACTERS = frozenset`, `_SHA256_RE = re.compile` |
| [source_snapshot](modules/source_snapshot.md) | `_UNSET_EXPECTED_SELECTION_INPUTS = object` |
| [storage_receipts](modules/storage_receipts.md) | `_HEX = re.compile` |
| [sync_analysis_storage](modules/sync_analysis_storage.md) | `_CATALOG_SCHEMAS = frozenset`, `_HASH = re.compile` |
| [sync_manifest](modules/sync_manifest.md) | `_REASON_RE = re.compile`, `_CONCEPT_PAGE_RE = re.compile` |
| [task_context](modules/task_context.md) | `_LIVE_FACETS = frozenset`, `_NATIVE_FACETS = frozenset` |
| [task_contract](modules/task_contract.md) | `FACETS = frozenset`, `ANCHOR_KINDS = frozenset`, `TASK_KINDS = frozenset` |
| [validation](modules/validation.md) | `_WINDOWS_ABSOLUTE_RE = re.compile`, `_WINDOWS_DRIVE_PREFIX_RE = re.compile`, `_WINDOWS_RESERVED_NAMES = frozenset`, `_WINDOWS_FORBIDDEN_PATH_CHARS = frozenset`, `_UNSAFE_PAGE_COMPONENT_RE = re.compile`, `_SHA256_RE = re.compile`, `_ZERO_UTC_OFFSET = timedelta`, `_PATH_SYNTAX = OrderedDict`, `_PATH_SYNTAX_LOCK = RLock`, `_ASCII_CONTROL = re.compile`, `_ASCII_CONTROL_DELETE = re.compile`, `_EnumValue = TypeVar` |
| [verification_contracts](modules/verification_contracts.md) | `_CHECKER_ID_RE = re.compile`, `_CHECKER_VERSION_RE = re.compile`, `_MACHINE_CODE_RE = re.compile`, `_ANCHOR_ID_RE = re.compile`, `_SCOPE_UID_RE = re.compile`, `_WINDOWS_ABSOLUTE_RE = re.compile`, `_DIAGNOSTIC_SUBJECT_RE = re.compile`, `_CHECKER_REGISTRY = MappingProxyType` |
| [versioning](modules/versioning.md) | `VERSION_RE = re.compile`, `_TABLE_RE = re.compile` |
| [wiki_git_delivery](modules/wiki_git_delivery.md) | `_OID = re.compile` |
| [wiki_git_policy](modules/wiki_git_policy.md) | `_GIT_REPOSITORY_REDIRECTION_ENV = frozenset` |
| [wiki_media](modules/wiki_media.md) | `IMAGE_EXTENSIONS = frozenset`, `VIDEO_EXTENSIONS = frozenset`, `_MARKDOWN_TITLE_RE = re.compile`, `_AUTHORITY_USERINFO_RE = re.compile`, `_URI_AUTHORITY_PREFIX_RE = re.compile`, `_URI_TOKEN_START_RE = re.compile`, `_REFERENCE_DEFINITION_RE = re.compile`, `_REFERENCE_IMAGE_RE = re.compile`, `_README_ASSET_RE = re.compile`, `_MERMAID_CLICK_RE = re.compile` |
| [wiki_surface](modules/wiki_surface.md) | `_PAGE_ID_RE = re.compile`, `_ASSET_SURFACE = WikiAssetSurface` |
| [wiki_surface_index](modules/wiki_surface_index.md) | `_MERMAID_CLICK_RE = re.compile`, `_MARKDOWN_PATH_RE = re.compile` |
| [wiki_write_basis](modules/wiki_write_basis.md) | `ACTIVE_WRITE_BASIS = ContextVar`, `ACTIVE_SYNC_JOURNAL = ContextVar`, `ACTIVE_BOOTSTRAP_JOURNAL = ContextVar` |

## Factory / wiring

<!-- Heuristic, name-based detection of app-factory / wiring functions. -->

| Function | Kind | Module |
|----------|------|--------|
| `setup` | wiring | [provider](modules/provider.md) |
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

Class-body imports join eager ordering only when the class definition is outside a function and a recognized type-only guard. A class constructed inside a function retains deferred scope; imports under TYPE_CHECKING remain outside eager ordering.
