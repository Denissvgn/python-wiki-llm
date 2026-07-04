#!/usr/bin/env node
// TypeScript AST extractor for agent-wiki-cli.
// Usage: node extract.js --src-dir <path> [--only-files <f1,f2,...>]
//                        [--deep] [--extensions <.ts,.tsx>]
//
// Outputs a JSON inventory to stdout (same canonical schema as PythonExtractor).
// The "language" field is intentionally absent — TypeScriptExtractor stamps it.
// Errors/warnings go to stderr.  Exit 0 on success.

"use strict";

const path = require("path");
const fs = require("fs");
const { Project, SyntaxKind } = require("ts-morph");

// ── Argument parsing ──────────────────────────────────────────────────────────

const args = process.argv.slice(2);

function getArg(flag, defaultValue = null) {
  const idx = args.indexOf(flag);
  if (idx === -1) return defaultValue;
  return args[idx + 1] ?? defaultValue;
}

const srcDir = path.resolve(getArg("--src-dir", "."));
// ts-morph normalises all paths to forward slashes, even on Windows.
// We keep a forward-slash version of srcDir for path comparisons against
// ts-morph's getFilePath() output so that startsWith() works on Windows.
const srcDirPosix = srcDir.split(path.sep).join("/");
const onlyFilesArg = getArg("--only-files", null);
const deep = args.includes("--deep");
const extensionsArg = getArg("--extensions", ".ts,.tsx");
const extensions = extensionsArg.split(",").map((e) => e.trim());

const EXCLUDED_DIRS = new Set([
  ".cache",
  ".direnv",
  ".eggs",
  ".env",
  ".git",
  ".mypy_cache",
  ".next",
  ".nox",
  ".npm",
  ".nuxt",
  ".parcel-cache",
  ".pnpm-store",
  ".pyre",
  ".pytest_cache",
  ".ruff_cache",
  ".svelte-kit",
  ".tox",
  ".venv",
  ".virtualenv",
  ".vite",
  ".yarn",
  "__pycache__",
  "__pypackages__",
  "bower_components",
  "build",
  "coverage",
  "dist",
  "env",
  "htmlcov",
  "jspm_packages",
  "node_modules",
  "out",
  "site-packages",
  "target",
  "venv",
  "virtualenv",
]);

// ── ts-morph Project setup ─────────────────────────────────────────────────

// Walk up from srcDir to find tsconfig.json (supports src/ subdirectories).
function findTsConfig(startDir) {
  let dir = startDir;
  while (true) {
    const candidate = path.join(dir, "tsconfig.json");
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) return null; // filesystem root
    dir = parent;
  }
}

const projectOptions = { skipAddingFilesFromTsConfig: true };
// When only specific files are requested, skip loading all tsconfig files to
// avoid scanning the entire project for an incremental extraction.
if (!onlyFilesArg) {
  const tsconfigPath = findTsConfig(srcDir);
  if (tsconfigPath) {
    projectOptions.tsConfigFilePath = tsconfigPath;
    projectOptions.skipAddingFilesFromTsConfig = false;
  }
}

const project = new Project(projectOptions);

// ── File discovery ────────────────────────────────────────────────────────────

function isExcluded(filePath) {
  // Exclude only the directory segments, not the filename itself.
  // Without .slice(0,-1) a file named "dist.ts" would be incorrectly excluded.
  // Split on both / and \ to handle ts-morph (forward-slash) and native paths.
  const parts = filePath.split(/[/\\]/).slice(0, -1);
  return parts.some((part) => EXCLUDED_DIRS.has(part));
}

function collectFiles(dir) {
  const results = [];
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return results;
  }
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!EXCLUDED_DIRS.has(entry.name)) {
        results.push(...collectFiles(full));
      }
    } else if (
      entry.isFile() &&
      extensions.includes(path.extname(entry.name))
    ) {
      results.push(full);
    }
  }
  return results;
}

let filesToProcess;
if (onlyFilesArg) {
  filesToProcess = onlyFilesArg
    .split(",")
    .map((f) => path.resolve(srcDir, f.trim()))
    .filter((f) => fs.existsSync(f) && extensions.includes(path.extname(f)));
} else {
  filesToProcess = collectFiles(srcDir).filter((f) => !isExcluded(f));
}

// Add source files to the project
for (const f of filesToProcess) {
  try {
    project.addSourceFileAtPath(f);
  } catch (err) {
    process.stderr.write(`Warning: could not add ${f}: ${err.message}\n`);
  }
}

// ── AST extraction helpers ────────────────────────────────────────────────────

function getJsDoc(node) {
  try {
    const docs = node.getJsDocs?.() ?? [];
    if (docs.length === 0) return "";
    return docs[docs.length - 1].getDescription().trim();
  } catch {
    return "";
  }
}

function getDecoratorNames(node) {
  try {
    return node.getDecorators?.().map((d) => d.getName()) ?? [];
  } catch {
    return [];
  }
}

function typeToStr(typeNode) {
  if (!typeNode) return "";
  try {
    return typeNode.getText();
  } catch {
    return "";
  }
}

function extractMethodParam(param) {
  const info = { name: param.getName() };
  const typeNode = param.getTypeNode();
  info.type = typeToStr(typeNode);
  const initializer = param.getInitializer();
  if (initializer) info.default = initializer.getText();
  return info;
}

function extractMethodInfo(method) {
  const isAsync =
    method.isAsync?.() ??
    method.getModifiers?.().some((m) => m.getText() === "async") ??
    false;

  const info = {
    name: method.getName(),
    line: method.getStartLineNumber(),
    is_async: isAsync,
  };

  if (deep) {
    info.docstring = getJsDoc(method);
    info.decorators = getDecoratorNames(method);
    info.params = (method.getParameters?.() ?? []).map(extractMethodParam);
    const returnTypeNode = method.getReturnTypeNode?.();
    info.return_type = typeToStr(returnTypeNode);
  }

  return info;
}

function nodeEndLine(node) {
  try {
    return node.getEndLineNumber?.();
  } catch {
    return undefined;
  }
}

function functionBaseInfo(node, name, line = null) {
  const startLine = line ?? node.getStartLineNumber();
  const info = {
    name,
    kind: "function",
    line: startLine,
  };
  const endLine = nodeEndLine(node);
  if (Number.isInteger(endLine) && endLine >= startLine) {
    info.end_line = endLine;
  }
  return info;
}

function extractFunctionInfo(fn, name, docNode = null, line = null) {
  const info = functionBaseInfo(fn, name, line);
  const isAsync = fn.isAsync?.() ?? false;

  if (deep) {
    info.is_async = isAsync;
    info.docstring = getJsDoc(docNode ?? fn);
    info.decorators = getDecoratorNames(fn);
    info.params = (fn.getParameters?.() ?? []).map(extractMethodParam);
    info.return_type = typeToStr(fn.getReturnTypeNode?.());
  } else if (isAsync) {
    info.async = true;
  }

  return info;
}

function extractProperty(prop) {
  const info = { name: prop.getName(), type: "" };
  const typeNode = prop.getTypeNode?.();
  if (typeNode) info.type = typeToStr(typeNode);
  const initializer = prop.getInitializer?.();
  if (initializer) info.default = initializer.getText();
  else info.default = "";
  return info;
}

function relativePathFromSrc(filePath) {
  const normalized = filePath.split("\\").join("/");
  if (normalized === srcDirPosix) return path.basename(normalized);
  if (normalized.startsWith(srcDirPosix + "/")) {
    return normalized.slice(srcDirPosix.length + 1);
  }
  return normalized;
}

function commonJsExports(sourceFile) {
  const exports = new Set();
  const functionNames = new Set();

  for (const assignment of sourceFile.getDescendantsOfKind(SyntaxKind.BinaryExpression)) {
    if (assignment.getOperatorToken().getText() !== "=") continue;

    const left = assignment.getLeft().getText();
    const right = assignment.getRight();
    let exportedName = "";
    if (left === "module.exports") {
      exportedName = "default";
    } else if (left.startsWith("exports.")) {
      exportedName = left.slice("exports.".length);
    } else if (left.startsWith("module.exports.")) {
      exportedName = left.slice("module.exports.".length);
    }

    if (!exportedName) continue;
    exports.add(exportedName === "default" ? "default" : exportedName);
    if (right.getKind() === SyntaxKind.Identifier) {
      functionNames.add(right.getText());
    }
  }

  return { exports, functionNames };
}

function extractExports(sourceFile, commonJs) {
  const names = new Set(commonJs.exports);
  const exportedDeclarations = sourceFile.getExportedDeclarations?.() ?? new Map();
  for (const name of exportedDeclarations.keys()) {
    names.add(name);
  }

  for (const exp of sourceFile.getExportDeclarations()) {
    const namedExports = exp.getNamedExports();
    if (namedExports.length === 0) {
      names.add("*");
      continue;
    }
    for (const named of namedExports) {
      names.add(named.getName());
    }
  }

  for (const assignment of sourceFile.getExportAssignments?.() ?? []) {
    names.add(assignment.isExportEquals?.() ? "=" : "default");
  }

  return [...names].filter(Boolean).sort();
}

function extractTopLevelConstants(sourceFile) {
  const constants = [];
  for (const stmt of sourceFile.getStatements()) {
    if (stmt.getKind() !== SyntaxKind.VariableStatement) continue;
    if (stmt.getDeclarationKind?.() !== "const") continue;

    for (const decl of stmt.getDeclarations()) {
      const init = decl.getInitializer();
      const initKind = init?.getKind();
      if (
        initKind === SyntaxKind.ArrowFunction ||
        initKind === SyntaxKind.FunctionExpression
      )
        continue;
      constants.push({
        name: decl.getName(),
        line: decl.getStartLineNumber(),
        exported: stmt.isExported?.() ?? false,
      });
    }
  }
  return constants;
}

function expressionCallName(expr) {
  const kind = expr.getKind();
  if (kind === SyntaxKind.CallExpression) {
    const callee = expr.getExpression();
    if (callee.getKind() === SyntaxKind.PropertyAccessExpression) {
      return callee.getName();
    }
    return callee.getText();
  }
  if (kind === SyntaxKind.NewExpression) {
    return expr.getExpression().getText().split(".").pop();
  }
  return "";
}

function moduleCallFromExpression(expr, target = null, line = null) {
  if (!expr) return null;
  const kind = expr.getKind();
  if (kind !== SyntaxKind.CallExpression && kind !== SyntaxKind.NewExpression) {
    return null;
  }
  const name = expressionCallName(expr);
  if (!name) return null;

  const call = { name, line: line ?? expr.getStartLineNumber() };
  if (target) call.target = target;
  if (name === "createServer" && typeof expr.getArguments === "function") {
    const firstArg = expr.getArguments()[0];
    if (firstArg && firstArg.getKind() === SyntaxKind.Identifier) {
      call.args = [firstArg.getText()];
    }
  }
  return call;
}

function extractModuleCalls(sourceFile) {
  const calls = [];
  for (const stmt of sourceFile.getStatements()) {
    if (stmt.getKind() === SyntaxKind.VariableStatement) {
      for (const decl of stmt.getDeclarations()) {
        const call = moduleCallFromExpression(
          decl.getInitializer(),
          decl.getName(),
          decl.getStartLineNumber()
        );
        if (call) calls.push(call);
      }
      continue;
    }

    if (stmt.getKind() !== SyntaxKind.ExpressionStatement) continue;
    const expr = stmt.getExpression();
    if (expr.getKind() === SyntaxKind.BinaryExpression) {
      const call = moduleCallFromExpression(
        expr.getRight(),
        expr.getLeft().getText(),
        expr.getStartLineNumber()
      );
      if (call) calls.push(call);
      continue;
    }

    const call = moduleCallFromExpression(expr, null, expr.getStartLineNumber());
    if (call) calls.push(call);
  }
  return calls;
}

function extractImportRecords(sourceFile) {
  const imports = [];
  for (const imp of sourceFile.getImportDeclarations()) {
    const moduleSpecifier = imp.getModuleSpecifierValue();
    const defaultImport = imp.getDefaultImport();
    if (defaultImport) {
      imports.push({
        module: moduleSpecifier,
        name: defaultImport.getText(),
        alias: null,
        type: "default",
      });
    }

    for (const named of imp.getNamedImports()) {
      imports.push({
        module: moduleSpecifier,
        name: named.getName(),
        alias: named.getAliasNode()?.getText() ?? null,
        type: "named",
      });
    }

    const ns = imp.getNamespaceImport();
    if (ns) {
      imports.push({
        module: moduleSpecifier,
        name: ns.getText(),
        alias: null,
        type: "namespace",
      });
    }
  }
  return imports;
}

function extractModuleDocstring(sourceFile) {
  const firstStmt = sourceFile.getStatements()[0];
  if (!firstStmt) return "";
  const leading = firstStmt
    .getLeadingCommentRanges()
    .find((r) => r.getText().startsWith("/**"));
  return leading ? leading.getText() : "";
}

function hasDocumentableModuleSignals(fileEntry, moduleDocstring = "") {
  return Boolean(
    fileEntry.imports?.length ||
      moduleDocstring ||
      fileEntry.exports?.length ||
      fileEntry.constants?.length ||
      fileEntry.module_calls?.length
  );
}

function isPlainJavaScriptFile(filePath) {
  return path.extname(filePath) === ".js";
}

function shouldIncludeTopLevelFunction(fn, filePath, commonJs) {
  const fnName = fn.getName() ?? "";
  if (isPlainJavaScriptFile(filePath) && fnName) return true;
  return (
    fn.isExported() ||
    fn.isDefaultExport() ||
    (deep && fnName && commonJs.functionNames.has(fnName))
  );
}

// ── Per-file extraction ───────────────────────────────────────────────────────

function extractFile(sourceFile) {
  const filePath = sourceFile.getFilePath();
  const fileEntry = { classes: [], functions: [] };
  const cjs = commonJsExports(sourceFile);

  // ── Classes ────────────────────────────────────────────────────────────────
  for (const cls of sourceFile.getClasses()) {
    const baseExpr = cls.getExtends();
    const bases = baseExpr ? [baseExpr.getExpression().getText()] : [];
    const implementsExprs = cls.getImplements().map((i) => i.getExpression().getText());

    const clsLine = cls.getStartLineNumber();
    const clsName = cls.getName() ?? `<anonymous_L${clsLine}>`;
    if (deep) {
      fileEntry.classes.push({
        name: clsName,
        kind: "class",
        bases: [...bases, ...implementsExprs],
        line: clsLine,
        docstring: getJsDoc(cls),
        decorators: getDecoratorNames(cls),
        attributes: cls.getProperties().map(extractProperty),
        methods: [
          ...cls.getMethods().map(extractMethodInfo),
          ...cls.getConstructors().map((c) => ({
            name: "constructor",
            line: c.getStartLineNumber(),
            is_async: false,
            docstring: getJsDoc(c),
            decorators: [],
            params: c.getParameters().map(extractMethodParam),
            return_type: "",
          })),
        ],
      });
    } else {
      fileEntry.classes.push({
        name: clsName,
        kind: "class",
        bases: [...bases, ...implementsExprs],
        line: clsLine,
      });
    }
  }

  // ── Interfaces ─────────────────────────────────────────────────────────────
  for (const iface of sourceFile.getInterfaces()) {
    // Use getExtends() instead of getBaseDeclarations() — the latter returns []
    // for unresolved external types (e.g. interfaces extending EventEmitter).
    const bases = iface.getExtends().map((n) => n.getExpression().getText());

    if (deep) {
      fileEntry.classes.push({
        name: iface.getName(),
        kind: "interface",
        bases,
        line: iface.getStartLineNumber(),
        docstring: getJsDoc(iface),
        decorators: [],
        attributes: iface.getProperties().map(extractProperty),
        methods: iface.getMethods().map((m) => ({
          name: m.getName(),
          line: m.getStartLineNumber(),
          is_async: false,
          docstring: getJsDoc(m),
          decorators: [],
          params: m.getParameters().map(extractMethodParam),
          return_type: typeToStr(m.getReturnTypeNode()),
        })),
      });
    } else {
      fileEntry.classes.push({
        name: iface.getName(),
        kind: "interface",
        bases,
        line: iface.getStartLineNumber(),
      });
    }
  }

  // ── Enums ──────────────────────────────────────────────────────────────────
  for (const en of sourceFile.getEnums()) {
    if (deep) {
      fileEntry.classes.push({
        name: en.getName(),
        kind: "enum",
        bases: [],
        line: en.getStartLineNumber(),
        docstring: getJsDoc(en),
        decorators: getDecoratorNames(en),
        attributes: en.getMembers().map((m) => ({
          name: m.getName(),
          type: "",
          default: m.getValue()?.toString() ?? "",
        })),
        methods: [],
      });
    } else {
      fileEntry.classes.push({
        name: en.getName(),
        kind: "enum",
        bases: [],
        line: en.getStartLineNumber(),
      });
    }
  }

  // ── Type aliases ───────────────────────────────────────────────────────────
  for (const ta of sourceFile.getTypeAliases()) {
    fileEntry.classes.push({
      name: ta.getName(),
      kind: "type_alias",
      bases: [],
      line: ta.getStartLineNumber(),
      ...(deep ? { docstring: getJsDoc(ta), decorators: [], attributes: [], methods: [] } : {}),
    });
  }

  // ── Functions ──────────────────────────────────────────────────────────────
  for (const fn of sourceFile.getFunctions()) {
    const fnName = fn.getName() ?? "";
    if (!shouldIncludeTopLevelFunction(fn, filePath, cjs)) continue;

    fileEntry.functions.push(
      extractFunctionInfo(
        fn,
        fnName || `<anonymous_L${fn.getStartLineNumber()}>`
      )
    );
  }

  // ── Arrow-function exports (const foo = () => ...) ─────────────────────────
  for (const varDecl of sourceFile.getVariableDeclarations()) {
    const stmt = varDecl.getVariableStatement();
    if (!stmt) continue;
    if (!stmt.isExported()) continue;
    const init = varDecl.getInitializer();
    if (!init) continue;
    const kind = init.getKind();
    if (
      kind !== SyntaxKind.ArrowFunction &&
      kind !== SyntaxKind.FunctionExpression
    )
      continue;

    const arrowFn = init;
    const info = extractFunctionInfo(
      arrowFn,
      varDecl.getName(),
      stmt,
      varDecl.getStartLineNumber()
    );
    if (deep) info.decorators = [];
    fileEntry.functions.push(info);
  }

  // ── Module-level signals ───────────────────────────────────────────────────
  const imports = extractImportRecords(sourceFile);
  if (imports.length > 0) fileEntry.imports = imports;

  const moduleDocstring = extractModuleDocstring(sourceFile);

  const exports = extractExports(sourceFile, cjs);
  if (exports.length > 0) fileEntry.exports = exports;

  const constants = extractTopLevelConstants(sourceFile);
  if (constants.length > 0) fileEntry.constants = constants;

  const moduleCalls = extractModuleCalls(sourceFile);
  if (moduleCalls.length > 0) fileEntry.module_calls = moduleCalls;

  if (deep) {
    fileEntry.module_docstring = moduleDocstring;
  }

  // Only include files that have something worth tracking
  if (
    fileEntry.classes.length > 0 ||
    fileEntry.functions.length > 0 ||
    hasDocumentableModuleSignals(fileEntry, moduleDocstring)
  ) {
    return [filePath, fileEntry];
  }
  if (deep) {
    process.stderr.write(
      `llm-wiki TypeScript extractor: skipped ${relativePathFromSrc(
        filePath
      )}: no documentable TypeScript declarations, imports, exports, constants, or module statements.\n`
    );
  }
  return null;
}

// ── Main ──────────────────────────────────────────────────────────────────────

const inventory = {};

for (const sourceFile of project.getSourceFiles()) {
  // Skip files outside srcDir (e.g. from lib.d.ts loaded via tsconfig).
  // Use separator-aware prefix to avoid false matches on sibling dirs like src-gen/.
  // ts-morph always returns forward-slash paths, so compare against srcDirPosix.
  const fp = sourceFile.getFilePath();
  if (!fp.startsWith(srcDirPosix + "/") && fp !== srcDirPosix) continue;
  if (isExcluded(fp)) continue;

  try {
    const result = extractFile(sourceFile);
    if (result) {
      const [filePath, fileEntry] = result;
      inventory[filePath] = fileEntry;
    }
  } catch (err) {
    process.stderr.write(`Warning: failed to extract ${fp}: ${err.message}\n`);
  }
}

process.stdout.write(JSON.stringify(inventory));
