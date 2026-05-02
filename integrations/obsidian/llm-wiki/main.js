/* THIS FILE IS GENERATED FROM src/main.ts */
"use strict";
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/main.ts
var main_exports = {};
__export(main_exports, {
  buildCommandArgs: () => buildCommandArgs,
  default: () => LlmWikiPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian = require("obsidian");
var import_child_process = require("child_process");
var DEFAULT_SETTINGS = {
  cliPath: "llm-wiki",
  projectRoot: "",
  wikiDir: "docs/llm_wiki",
  vaultDir: "",
  notesDir: ".llm-wiki/obsidian-notes",
  contextBudget: 32e3,
  sourceUriTemplate: "vscode://file/{projectRoot}/{sourcePath}:{line}"
};
function buildCommandArgs(command, settings, vaultPath) {
  const projectRoot = resolveProjectRoot(settings, vaultPath);
  const vaultDir = settings.vaultDir || vaultPath;
  if (command === "export") {
    return [
      "obsidian",
      "export",
      "--src-dir",
      projectRoot,
      "--wiki-dir",
      settings.wikiDir,
      "--vault-dir",
      vaultDir,
      "--notes-dir",
      settings.notesDir
    ];
  }
  if (command === "sync") {
    return ["sync", "--src-dir", projectRoot, "--wiki-dir", settings.wikiDir];
  }
  if (command === "lint") {
    return ["lint", "--src-dir", projectRoot, "--wiki-dir", settings.wikiDir];
  }
  if (command === "context") {
    return [
      "context",
      "--src-dir",
      projectRoot,
      "--budget",
      String(settings.contextBudget),
      "--format",
      "markdown",
      "--focus",
      "changed"
    ];
  }
  return ["status", "--wiki-dir", settings.wikiDir];
}
function resolveProjectRoot(settings, vaultPath) {
  return settings.projectRoot || vaultPath;
}
function getVaultPath(app) {
  const adapter = app.vault.adapter;
  return adapter.getBasePath ? adapter.getBasePath() : "";
}
function runCommand(settings, args, vaultPath) {
  const cwd = resolveProjectRoot(settings, vaultPath);
  return new Promise((resolve, reject) => {
    (0, import_child_process.execFile)(
      settings.cliPath,
      args,
      { cwd, timeout: 12e4, maxBuffer: 1024 * 1024 * 8 },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`${stderr || error.message}`));
          return;
        }
        resolve({ stdout, stderr });
      }
    );
  });
}
function sourceUri(settings, vaultPath, sourcePath, line) {
  const projectRoot = resolveProjectRoot(settings, vaultPath);
  const replacements = {
    projectRoot,
    sourcePath,
    line: String(line || 1)
  };
  return encodeURI(settings.sourceUriTemplate.replace(/\{(projectRoot|sourcePath|line)\}/g, (_, key) => replacements[key]));
}
var OutputModal = class extends import_obsidian.Modal {
  constructor(app, title, body) {
    super(app);
    this.title = title;
    this.body = body;
  }
  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.createEl("h2", { text: this.title });
    contentEl.createEl("pre", { text: this.body || "No output." });
  }
};
var LlmWikiPlugin = class extends import_obsidian.Plugin {
  constructor() {
    super(...arguments);
    this.settings = DEFAULT_SETTINGS;
  }
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.addCommand({
      id: "export-mirror",
      name: "Export mirror",
      callback: () => this.runAndShow("Export mirror", "export")
    });
    this.addCommand({
      id: "sync-wiki",
      name: "Sync wiki",
      callback: () => this.runAndShow("Sync wiki", "sync")
    });
    this.addCommand({
      id: "lint-wiki",
      name: "Lint wiki",
      callback: () => this.runAndShow("Lint wiki", "lint")
    });
    this.addCommand({
      id: "copy-context",
      name: "Copy context",
      callback: () => this.copyContext()
    });
    this.addCommand({
      id: "open-source-location",
      name: "Open source location",
      callback: () => this.openSourceLocation()
    });
    this.addCommand({
      id: "show-status",
      name: "Show status",
      callback: () => this.runAndShow("Status", "status")
    });
    this.addSettingTab(new LlmWikiSettingTab(this.app, this));
  }
  async saveSettings() {
    await this.saveData(this.settings);
  }
  async runAndShow(title, command) {
    const vaultPath = getVaultPath(this.app);
    try {
      const args = buildCommandArgs(command, this.settings, vaultPath);
      const result = await runCommand(this.settings, args, vaultPath);
      new import_obsidian.Notice(`LLM Wiki: ${title} complete`);
      new OutputModal(this.app, `LLM Wiki: ${title}`, result.stdout || result.stderr).open();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      new import_obsidian.Notice(`LLM Wiki: ${title} failed`);
      new OutputModal(this.app, `LLM Wiki: ${title} failed`, message).open();
    }
  }
  async copyContext() {
    const vaultPath = getVaultPath(this.app);
    try {
      const args = buildCommandArgs("context", this.settings, vaultPath);
      const result = await runCommand(this.settings, args, vaultPath);
      await navigator.clipboard.writeText(result.stdout);
      new import_obsidian.Notice("LLM Wiki context copied");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      new OutputModal(this.app, "LLM Wiki: Copy context failed", message).open();
    }
  }
  openSourceLocation() {
    const view = this.app.workspace.getActiveViewOfType(import_obsidian.MarkdownView);
    const file = view?.file;
    if (!file) {
      new import_obsidian.Notice("Open an LLM Wiki mirror note first.");
      return;
    }
    const frontmatter = this.app.metadataCache.getFileCache(file)?.frontmatter;
    const metadata = frontmatter?.llm_wiki;
    const sourcePath = metadata?.source_path;
    const line = Number(metadata?.source_line || 1);
    if (!sourcePath) {
      new import_obsidian.Notice("This note does not include an llm_wiki.source_path.");
      return;
    }
    window.open(sourceUri(this.settings, getVaultPath(this.app), sourcePath, line));
  }
};
var LlmWikiSettingTab = class extends import_obsidian.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "LLM Wiki" });
    this.textSetting("CLI path", "Executable path for llm-wiki.", "cliPath");
    this.textSetting("Project root", "Repository root. Leave blank to use the current vault path.", "projectRoot");
    this.textSetting("Wiki dir", "Canonical wiki directory relative to the project root.", "wikiDir");
    this.textSetting("Vault dir", "Vault directory passed to obsidian export. Leave blank to use current vault.", "vaultDir");
    this.textSetting("Notes dir", "Sidecar notes directory, relative to vault dir unless absolute.", "notesDir");
    new import_obsidian.Setting(containerEl).setName("Context budget").setDesc("Token budget for the Copy context command.").addText((text) => text.setValue(String(this.plugin.settings.contextBudget)).onChange(async (value) => {
      const parsed = Number(value);
      if (Number.isFinite(parsed) && parsed > 0) {
        this.plugin.settings.contextBudget = Math.floor(parsed);
        await this.plugin.saveSettings();
      }
    }));
    this.textSetting("Source URI template", "Use {projectRoot}, {sourcePath}, and {line}.", "sourceUriTemplate");
  }
  textSetting(name, desc, key) {
    new import_obsidian.Setting(this.containerEl).setName(name).setDesc(desc).addText((text) => text.setValue(String(this.plugin.settings[key])).onChange(async (value) => {
      this.plugin.settings[key] = value;
      await this.plugin.saveSettings();
    }));
  }
};
