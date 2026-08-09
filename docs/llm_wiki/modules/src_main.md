# main Module

**Path:** `integrations/obsidian/llm-wiki/src/main.ts`

## Description

Authoring source for the Obsidian plugin. It registers commands for exporting,
syncing, validating, and inspecting the wiki, copies bounded context for the
active note, opens referenced source locations, and exposes persistent plugin
settings. CLI processes are launched with argument arrays through `execFile`,
and their output is shown in Obsidian notices or a modal.

## Imports

| Source | Symbols |
|--------|---------|
| `child_process` | `execFile` |
| `obsidian` | `App`, `MarkdownView`, `Modal`, `Notice`, `Plugin`, `PluginSettingTab`, `Setting` |

## Module Signals

| Signal | Values |
|--------|--------|
| Exports | `buildCommandArgs`, `default` |
| Constants | `DEFAULT_SETTINGS` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
*No internal module dependencies detected.*

### External packages

| Language | Used packages | Undeclared packages |
|---|---:|---:|
| typescript | 1 | 0 |

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [OutputModal](../entities/OutputModal.md) | Class | 116 | `Modal` | — |
| [LlmWikiPlugin](../entities/LlmWikiPlugin.md) | Class | 129 | `Plugin` | — |
| [LlmWikiSettingTab](../entities/LlmWikiSettingTab.md) | Class | 219 | `PluginSettingTab` | — |
| [LlmWikiSettings](../entities/LlmWikiSettings.md) | Class | 12 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `buildCommandArgs` | `(command: "export" \| "sync" \| "lint" \| "context" \| "status", settings: LlmWikiSettings, vaultPath: string) -> string[]` | — | — |
