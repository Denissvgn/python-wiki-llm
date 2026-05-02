# LLM Wiki Obsidian Plugin

Desktop-only companion plugin for `llm-wiki`.

It runs local `llm-wiki` CLI commands from Obsidian:

- `LLM Wiki: Export mirror`
- `LLM Wiki: Sync wiki`
- `LLM Wiki: Lint wiki`
- `LLM Wiki: Copy context`
- `LLM Wiki: Open source location`
- `LLM Wiki: Show status`

## Local Install

From the Python project:

```bash
llm-wiki obsidian install-plugin --vault-dir /path/to/vault
```

Then enable **LLM Wiki** from Obsidian's Community plugins settings.

## Development

```bash
cd integrations/obsidian/llm-wiki
npm install
npm run dev
```

`main.js` is committed so local installs work before rebuilding. Source lives in
`src/main.ts`.

## Settings

- **CLI path**: executable path for `llm-wiki`.
- **Project root**: repository root. Blank uses the current vault path.
- **Wiki dir**: canonical wiki directory, usually `docs/llm_wiki`.
- **Vault dir**: mirror destination. Blank uses the current vault.
- **Notes dir**: sidecar notes path, relative to vault dir unless absolute.
- **Context budget**: token budget for `Copy context`.
- **Source URI template**: uses `{projectRoot}`, `{sourcePath}`, and `{line}`.

The default source URI template opens VS Code:

```text
vscode://file/{projectRoot}/{sourcePath}:{line}
```
