# run_request

**Entry point:** `upgrade_runtime.run_request`
**Modules involved:** [config](../modules/config.md), [current_contracts](../modules/current_contracts.md), [filesystem_guard](../modules/filesystem_guard.md), [host](../modules/host.md), [knowledge_evidence](../modules/knowledge_evidence.md), [legacy_hooks](../modules/legacy_hooks.md), [path_policy](../modules/path_policy.md), [rendering_lifecycle](../modules/rendering_lifecycle.md), [skills](../modules/skills.md), [source_selection](../modules/source_selection.md), [upgrade_runtime](../modules/upgrade_runtime.md), [upgrade_service](../modules/upgrade_service.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

> Run one upgrade for a command: output goes to the host, stops raise UpgradeAborted.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `path_policy.validate_path`
2. `wiki_lifecycle.require_safe_wiki_scaffold`
3. `config.require_safe_config_path`
4. `host.emit`
5. `host.emit`
6. `legacy_hooks.remove_legacy_hooks`
7. `legacy_hooks.inspect_legacy_hooks`
8. `host.emit`
9. `host.emit`
10. `config.inspect_config`
11. `config.get_agent_config_path`
12. `host.emit`
13. `host.emit`
14. `config.config_requires_manual_recovery`
15. `host.emit`
16. `host.emit`
17. `host.emit`
18. `host.emit`
19. `source_selection.resolve_source_selection`
20. `host.emit`
21. `host.emit`
22. `host.emit`
23. `host.emit`
24. `host.emit`
25. `host.emit`
26. `host.emit`
27. `host.emit`
28. `host.emit`
29. `skills.verify_reference_skill`
30. `skills.skills_install_dir`
31. `skills.skills_install_dir`
32. `host.emit`
33. `host.emit`
34. `host.emit`
35. `host.emit`
36. `host.emit`
37. `host.emit`
38. `host.emit`
39. `current_contracts.upgrade_current_knowledge`
40. `host.emit`
41. `host.emit`
42. `host.emit`
43. `config.require_config_inspection_unchanged`
44. `skills._provision_reference_skill_guarded`
45. `host.emit`
46. `host.emit`
47. `rendering_lifecycle.reference_recovery_command`
48. `skills.skills_install_dir`
49. `host.emit`
50. `skills.verify_reference_skill`
51. `host.emit`
52. `rendering_lifecycle.select_render_profile`
53. `host.emit`
54. `host.emit`
55. `host.emit`
56. `host.emit`
57. `host.emit`
58. `host.emit`
59. `host.emit`
60. `host.emit`
61. `host.emit`
62. `current_contracts.current_contract_defaults`
63. `knowledge_evidence.formatted_json_bytes`
64. `config.write_config`
65. `host.current_host`
66. `filesystem_guard.unlink_guarded_bytes`
67. `host.emit`
68. `host.emit`
69. `config.require_committed_config`
70. `host.emit`
71. `host.emit`
72. `config.write_config`
73. `config.require_committed_config`
74. `host.emit`
75. `host.emit`
76. `host.emit`
77. `config.require_committed_config`
78. `host.emit`
79. `host.emit`
80. `host.emit`
81. `host.emit`
82. `host.emit`
83. `host.emit`
84. `upgrade_service.UpgradeOutcome`

## Touches

- [config](../modules/config.md)
- [current_contracts](../modules/current_contracts.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [host](../modules/host.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [legacy_hooks](../modules/legacy_hooks.md)
- [path_policy](../modules/path_policy.md)
- [rendering_lifecycle](../modules/rendering_lifecycle.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [upgrade_runtime](../modules/upgrade_runtime.md)
- [upgrade_service](../modules/upgrade_service.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `upgrade_runtime.run_request`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
