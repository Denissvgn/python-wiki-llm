# Dependencies

Internal module dependency graph and external package reconciliation.

## Module graph

<!-- Collapsed to top-level packages; the full module list is in the Fan-in / Fan-out table below. -->
```mermaid
flowchart TD
    n0["integrations"]
    n1["src"]
    n0 --> n1
```

## Cycles

> Import cycles are legal but complicate load order — review the modules below.

- [calibration___init__](modules/calibration___init__.md) ⇄ [broker](modules/broker.md) ⇄ [calibration_contracts](modules/calibration_contracts.md) ⇄ [controller](modules/controller.md) ⇄ [host_broker](modules/host_broker.md) ⇄ [documentation_run___init__](modules/documentation_run___init__.md) ⇄ [documentation_run_contracts](modules/documentation_run_contracts.md) ⇄ [documentation_run_dependencies](modules/documentation_run_dependencies.md) ⇄ [export](modules/export.md) ⇄ [integrity](modules/integrity.md) ⇄ [packet](modules/packet.md) ⇄ [prepare](modules/prepare.md) ⇄ [record](modules/record.md) ⇄ [refresh](modules/refresh.md) ⇄ [documentation_run_schema](modules/documentation_run_schema.md) ⇄ [verify](modules/verify.md) ⇄ [workspace](modules/workspace.md)
- [context_packet](modules/context_packet.md) ⇄ [context_service](modules/context_service.md) ⇄ [documentation_query_builder](modules/documentation_query_builder.md)
- [knowledge_consumption](modules/knowledge_consumption.md) ⇄ [knowledge_verification](modules/knowledge_verification.md)
- [knowledge_envelope](modules/knowledge_envelope.md) ⇄ [knowledge_governance](modules/knowledge_governance.md) ⇄ [knowledge_model](modules/knowledge_model.md)
- [lint_service](modules/lint_service.md) ⇄ [metrics](modules/metrics.md)

## Fan-in / Fan-out

| Module | Fan-in | Fan-out |
|--------|--------|---------|
| [validation](modules/validation.md) | 50 | 0 |
| [config](modules/config.md) | 46 | 2 |
| [source_snapshot](modules/source_snapshot.md) | 33 | 5 |
| [wiki_surface](modules/wiki_surface.md) | 30 | 1 |
| [services_contracts](modules/services_contracts.md) | 29 | 0 |
| [source_selection](modules/source_selection.md) | 29 | 2 |
| [io](modules/io.md) | 26 | 1 |
| [sync_manifest](modules/sync_manifest.md) | 24 | 6 |
| [knowledge_evidence](modules/knowledge_evidence.md) | 23 | 1 |
| [knowledge_model](modules/knowledge_model.md) | 22 | 8 |
| [wiki_surface_index](modules/wiki_surface_index.md) | 21 | 5 |
| [extraction_service](modules/extraction_service.md) | 18 | 20 |
| [knowledge_consumption](modules/knowledge_consumption.md) | 17 | 5 |
| [knowledge_governance](modules/knowledge_governance.md) | 16 | 9 |
| [plugins](modules/plugins.md) | 16 | 2 |
| [knowledge_artifacts](modules/knowledge_artifacts.md) | 15 | 14 |
| [knowledge_observability](modules/knowledge_observability.md) | 14 | 9 |
| [bootstrap_runtime](modules/bootstrap_runtime.md) | 13 | 28 |
| [knowledge_envelope](modules/knowledge_envelope.md) | 13 | 4 |
| [common](modules/common.md) | 11 | 1 |
| [documentation_run_dependencies](modules/documentation_run_dependencies.md) | 11 | 23 |
| [wiki_media](modules/wiki_media.md) | 11 | 0 |
| [services_dependencies](modules/services_dependencies.md) | 10 | 5 |
| [documentation_run_contracts](modules/documentation_run_contracts.md) | 10 | 3 |
| [documentation_run_schema](modules/documentation_run_schema.md) | 10 | 2 |
| [extraction_jobs](modules/extraction_jobs.md) | 10 | 0 |
| [filesystem_guard](modules/filesystem_guard.md) | 10 | 0 |
| [knowledge_graph](modules/knowledge_graph.md) | 9 | 5 |
| [paths](modules/paths.md) | 9 | 0 |
| [documentation_queries](modules/documentation_queries.md) | 8 | 9 |
| [documentation_query_builder](modules/documentation_query_builder.md) | 8 | 11 |
| [workspace](modules/workspace.md) | 8 | 3 |
| [entrypoints](modules/entrypoints.md) | 8 | 4 |
| [integrity](modules/integrity.md) | 7 | 7 |
| [imports](modules/imports.md) | 7 | 3 |
| [inventory_cache](modules/inventory_cache.md) | 7 | 4 |
| [lint_service](modules/lint_service.md) | 7 | 34 |
| [skills](modules/skills.md) | 7 | 2 |
| [context_service](modules/context_service.md) | 6 | 25 |
| [infrastructure_inventory](modules/infrastructure_inventory.md) | 6 | 1 |
| [infrastructure_sync](modules/infrastructure_sync.md) | 6 | 4 |
| [knowledge_loader](modules/knowledge_loader.md) | 6 | 8 |
| [knowledge_orchestration](modules/knowledge_orchestration.md) | 6 | 15 |
| [knowledge_verification](modules/knowledge_verification.md) | 6 | 4 |
| [markdown_sections](modules/markdown_sections.md) | 6 | 1 |
| [services_schema](modules/services_schema.md) | 6 | 4 |
| [data_flow](modules/data_flow.md) | 5 | 1 |
| [refresh](modules/refresh.md) | 5 | 8 |
| [extractor_helpers](modules/extractor_helpers.md) | 5 | 1 |
| [knowledge_freshness](modules/knowledge_freshness.md) | 5 | 5 |
| [knowledge_projection](modules/knowledge_projection.md) | 5 | 14 |
| [metrics](modules/metrics.md) | 5 | 9 |
| [verification_contracts](modules/verification_contracts.md) | 5 | 5 |
| [api_contracts](modules/api_contracts.md) | 4 | 4 |
| [calibration___init__](modules/calibration___init__.md) | 4 | 4 |
| [concept_identity](modules/concept_identity.md) | 4 | 1 |
| [documentation_wiki_input](modules/documentation_wiki_input.md) | 4 | 13 |
| [redaction](modules/redaction.md) | 4 | 0 |
| [section_ownership](modules/section_ownership.md) | 4 | 5 |
| [team](modules/team.md) | 4 | 9 |
| [wiki_lifecycle](modules/wiki_lifecycle.md) | 4 | 4 |
| [bootstrap_service](modules/bootstrap_service.md) | 3 | 0 |
| [calibration_contracts](modules/calibration_contracts.md) | 3 | 5 |
| [controller](modules/controller.md) | 3 | 12 |
| [host_broker](modules/host_broker.md) | 3 | 2 |
| [circuit_breaker](modules/circuit_breaker.md) | 3 | 0 |
| [context_packet](modules/context_packet.md) | 3 | 18 |
| [doctor_service](modules/doctor_service.md) | 3 | 12 |
| [documentation_policy](modules/documentation_policy.md) | 3 | 3 |
| [documentation_run___init__](modules/documentation_run___init__.md) | 3 | 11 |
| [record](modules/record.md) | 3 | 7 |
| [knowledge_index](modules/knowledge_index.md) | 3 | 11 |
| [wiki_scaffold](modules/wiki_scaffold.md) | 3 | 0 |
| [generate_prompt_cmd](modules/generate_prompt_cmd.md) | 2 | 12 |
| [hook_cmd](modules/hook_cmd.md) | 2 | 3 |
| [broker](modules/broker.md) | 2 | 5 |
| [ci_installer](modules/ci_installer.md) | 2 | 5 |
| [ci_report](modules/ci_report.md) | 2 | 4 |
| [diagrams](modules/diagrams.md) | 2 | 2 |
| [documentation_native](modules/documentation_native.md) | 2 | 23 |
| [packet](modules/packet.md) | 2 | 5 |
| [verify](modules/verify.md) | 2 | 9 |
| [documentation_worklist](modules/documentation_worklist.md) | 2 | 5 |
| [knowledge_links](modules/knowledge_links.md) | 2 | 4 |
| [module_maps](modules/module_maps.md) | 2 | 1 |
| [relationships](modules/relationships.md) | 2 | 2 |
| [resource_diagnostics](modules/resource_diagnostics.md) | 2 | 0 |
| [secure_file](modules/secure_file.md) | 2 | 0 |
| [site_export](modules/site_export.md) | 2 | 8 |
| [site_html_check](modules/site_html_check.md) | 2 | 1 |
| [sync_analysis](modules/sync_analysis.md) | 2 | 3 |
| [versioning](modules/versioning.md) | 2 | 0 |
| [api](modules/api.md) | 1 | 22 |
| [api_types](modules/api_types.md) | 1 | 0 |
| [bump_cmd](modules/bump_cmd.md) | 1 | 1 |
| [ci_check_cmd](modules/ci_check_cmd.md) | 1 | 6 |
| [docs_cmd](modules/docs_cmd.md) | 1 | 5 |
| [doctor_cmd](modules/doctor_cmd.md) | 1 | 3 |
| [init_cmd](modules/init_cmd.md) | 1 | 7 |
| [install_ci_cmd](modules/install_ci_cmd.md) | 1 | 2 |
| [install_cmd](modules/install_cmd.md) | 1 | 3 |
| [knowledge_cmd](modules/knowledge_cmd.md) | 1 | 11 |
| [mcp_cmd](modules/mcp_cmd.md) | 1 | 2 |
| [metrics_cmd](modules/metrics_cmd.md) | 1 | 2 |
| [migrate_cmd](modules/migrate_cmd.md) | 1 | 18 |
| [obsidian_cmd](modules/obsidian_cmd.md) | 1 | 4 |
| [plugins_cmd](modules/plugins_cmd.md) | 1 | 4 |
| [prepare_extractors_cmd](modules/prepare_extractors_cmd.md) | 1 | 4 |
| [release_cmd](modules/release_cmd.md) | 1 | 1 |
| [review_cmd](modules/review_cmd.md) | 1 | 10 |
| [site_cmd](modules/site_cmd.md) | 1 | 6 |
| [skills_cmd](modules/skills_cmd.md) | 1 | 2 |
| [status_cmd](modules/status_cmd.md) | 1 | 5 |
| [sync_cmd](modules/sync_cmd.md) | 1 | 29 |
| [team_cmd](modules/team_cmd.md) | 1 | 6 |
| [trigger_cmd](modules/trigger_cmd.md) | 1 | 12 |
| [uninstall_cmd](modules/uninstall_cmd.md) | 1 | 5 |
| [upgrade_cmd](modules/upgrade_cmd.md) | 1 | 8 |
| [planner](modules/planner.md) | 1 | 3 |
| [fastapi_contracts](modules/fastapi_contracts.md) | 1 | 0 |
| [go_extractor](modules/go_extractor.md) | 1 | 2 |
| [haskell_extractor](modules/haskell_extractor.md) | 1 | 2 |
| [python_contracts](modules/python_contracts.md) | 1 | 0 |
| [python_extractor](modules/python_extractor.md) | 1 | 5 |
| [rust_extractor](modules/rust_extractor.md) | 1 | 2 |
| [dependency_versions](modules/dependency_versions.md) | 1 | 3 |
| [documentation_claim_evidence](modules/documentation_claim_evidence.md) | 1 | 4 |
| [documentation_model_policy](modules/documentation_model_policy.md) | 1 | 2 |
| [documentation_review](modules/documentation_review.md) | 1 | 1 |
| [export](modules/export.md) | 1 | 9 |
| [prepare](modules/prepare.md) | 1 | 8 |
| [knowledge_generation](modules/knowledge_generation.md) | 1 | 13 |
| [lockfile](modules/lockfile.md) | 1 | 0 |
| [mcp_server](modules/mcp_server.md) | 1 | 17 |
| [obsidian](modules/obsidian.md) | 1 | 11 |
| [packages](modules/packages.md) | 1 | 2 |
| [plugin_samples](modules/plugin_samples.md) | 1 | 1 |
| [protected_artifacts](modules/protected_artifacts.md) | 1 | 2 |
| [wiki_git_policy](modules/wiki_git_policy.md) | 1 | 0 |
| [render_summary](modules/render_summary.md) | 0 | 1 |
| [llm-wiki_main](modules/llm-wiki_main.md) | 0 | 0 |
| [src_main](modules/src_main.md) | 0 | 0 |
| [cli](modules/cli.md) | 0 | 34 |
| [eval_lite___init__](modules/eval_lite___init__.md) | 0 | 1 |
| [detectors](modules/detectors.md) | 0 | 0 |
| [styles](modules/styles.md) | 0 | 0 |
| [extractors___init__](modules/extractors___init__.md) | 0 | 0 |
| [ts_extractor](modules/ts_extractor.md) | 0 | 2 |

## External dependencies

### python

- **Used:** `mcp`, `pyyaml`, `tomli`, `uvicorn`
- ⚠️ **Undeclared:** `uvicorn`

### rust

- **Used:** —
- **Unused (declared, not imported):** `proc_macro2`, `quote`, `serde`, `serde_json`, `syn`

### typescript

- **Used:** `obsidian`
- **Unused (declared, not imported):** `ts-morph`

## Notes

The command-line dispatcher is the composition root: it imports command and
service modules so one parser can route the complete product surface. The high
fan-out on `cli` is therefore expected. `validation`, `config`,
`source_snapshot`, `wiki_surface`, and the service contracts have high fan-in
because they centralize boundary rules and shared records rather than product
orchestration.

The large cyclic groups deserve care when changing import-time behavior. The
calibration and documentation-run group includes compatibility re-export
wiring; the context group joins packet construction, context assembly, and
query building; the knowledge groups join loading, verification, governance,
and model contracts. Keep new work behind functions or lazy boundaries where
possible, and do not rely on relative order within a reported cycle.

The optional MCP stack is loaded only when the `mcp` command runs. The direct
`uvicorn` import belongs to HTTP transport and is supplied transitively by the
optional MCP dependency set through the SDK's runtime coupling; project
metadata declares the `mcp` extra rather than `uvicorn` directly, which explains
the static undeclared-package warning. The Rust crates and TypeScript
`ts-morph` entries come from packaged extractor-helper manifests; they are tool
implementation dependencies, not imports by the application modules being
documented. Extractor plugins are discovered dynamically and may not appear as
ordinary import edges.

This page is a static projection. Conditional imports, runtime plugin loading,
and generated JavaScript bundle wiring can change effective dependencies. For
startup implications, continue with [load order](load-order.md).
