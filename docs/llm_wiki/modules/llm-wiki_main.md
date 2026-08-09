# main Module

**Path:** `integrations/obsidian/llm-wiki/main.js`

## Description

Compiled CommonJS distribution of the Obsidian plugin from `src/main.ts`.
Obsidian loads this file to register the plugin and its command helpers. It is
a generated bundle rather than an independent implementation; behavior changes
belong in the TypeScript source and are carried here by the integration build.

## Module Signals

| Signal | Values |
|--------|--------|
| Exports | `default` |
| Module calls | `__export`, `module.exports = __toCommonJS`, `import_obsidian = require`, `import_child_process = require` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
*No internal module dependencies detected.*

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `buildCommandArgs` | `(command, settings, vaultPath)` | — | — |
| `resolveProjectRoot` | `(settings, vaultPath)` | — | — |
| `getVaultPath` | `(app)` | — | — |
| `runCommand` | `(settings, args, vaultPath)` | — | — |
| `sourceUri` | `(settings, vaultPath, sourcePath, line)` | — | — |