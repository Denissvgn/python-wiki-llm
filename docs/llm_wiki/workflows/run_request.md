# run_request

**Entry point:** `upgrade_runtime.run_request`
**Modules involved:** [config](../modules/config.md), [current_contracts](../modules/current_contracts.md), [filesystem_guard](../modules/filesystem_guard.md), [historical_sources](../modules/historical_sources.md), [host](../modules/host.md), [knowledge_evidence](../modules/knowledge_evidence.md), [legacy_hooks](../modules/legacy_hooks.md), [path_policy](../modules/path_policy.md), [rendering_lifecycle](../modules/rendering_lifecycle.md), [skills](../modules/skills.md), [source_selection](../modules/source_selection.md), [sync_manifest](../modules/sync_manifest.md), [upgrade_runtime](../modules/upgrade_runtime.md), [upgrade_service](../modules/upgrade_service.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

> Run one upgrade for a command: output goes to the host, stops raise UpgradeAborted.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `path_policy.validate_path`
2. `wiki_lifecycle.require_safe_wiki_scaffold`
3. `config.require_safe_config_path`
4. `host.emit`
5. `historical_sources.bound_records`
6. `sync_manifest.SyncManifest.load`
7. `host.emit`
8. `host.emit`
9. `host.emit`
10. `legacy_hooks.remove_legacy_hooks`
11. `legacy_hooks.inspect_legacy_hooks`
12. `host.emit`
13. `host.emit`
14. `config.inspect_config`
15. `config.get_agent_config_path`
16. `host.emit`
17. `host.emit`
18. `config.config_requires_manual_recovery`
19. `host.emit`
20. `host.emit`
21. `host.emit`
22. `host.emit`
23. `source_selection.resolve_source_selection`
24. `host.emit`
25. `host.emit`
26. `host.emit`
27. `host.emit`
28. `host.emit`
29. `host.emit`
30. `host.emit`
31. `host.emit`
32. `host.emit`
33. `skills.verify_reference_skill`
34. `skills.skills_install_dir`
35. `skills.skills_install_dir`
36. `host.emit`
37. `host.emit`
38. `host.emit`
39. `host.emit`
40. `host.emit`
41. `host.emit`
42. `host.emit`
43. `current_contracts.upgrade_current_knowledge`
44. `host.emit`
45. `host.emit`
46. `host.emit`
47. `config.require_config_inspection_unchanged`
48. `skills._provision_reference_skill_guarded`
49. `host.emit`
50. `host.emit`
51. `rendering_lifecycle.reference_recovery_command`
52. `skills.skills_install_dir`
53. `host.emit`
54. `skills.verify_reference_skill`
55. `host.emit`
56. `rendering_lifecycle.select_render_profile`
57. `host.emit`
58. `host.emit`
59. `host.emit`
60. `host.emit`
61. `host.emit`
62. `host.emit`
63. `host.emit`
64. `host.emit`
65. `host.emit`
66. `current_contracts.current_contract_defaults`
67. `knowledge_evidence.formatted_json_bytes`
68. `config.write_config`
69. `host.current_host`
70. `filesystem_guard.unlink_guarded_bytes`
71. `host.emit`
72. `host.emit`
73. `config.require_committed_config`
74. `host.emit`
75. `host.emit`
76. `config.write_config`
77. `config.require_committed_config`
78. `host.emit`
79. `host.emit`
80. `host.emit`
81. `config.require_committed_config`
82. `host.emit`
83. `host.emit`
84. `host.emit`
85. `host.emit`
86. `host.emit`
87. `host.emit`
88. `upgrade_service.UpgradeOutcome`

## Touches

- [config](../modules/config.md)
- [current_contracts](../modules/current_contracts.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [historical_sources](../modules/historical_sources.md)
- [host](../modules/host.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [legacy_hooks](../modules/legacy_hooks.md)
- [path_policy](../modules/path_policy.md)
- [rendering_lifecycle](../modules/rendering_lifecycle.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)
- [upgrade_runtime](../modules/upgrade_runtime.md)
- [upgrade_service](../modules/upgrade_service.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `upgrade_runtime.run_request`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
