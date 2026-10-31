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
const crypto = require("crypto");
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
const diagnostics = args.includes("--diagnostics-v1");
const includeEmpty = diagnostics && args.includes("--include-empty-v1");
const retainedEmptyFiles = new Set(diagnostics ? JSON.parse(getArg("--retain-empty-files-v1", "[]")) : []);
const outcomes = {};
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
    outcomes[relativePathFromSrc(f)] = { extraction_state: "failed", reason: "source-load-failed", failure_scope: "file" };
    process.stderr.write(`Warning: could not add ${f}: ${err.message}\n`);
  }
}

// ── AST extraction helpers ────────────────────────────────────────────────────

function nodeLine(node, position = node.getStart()) {
  // ts-morph's line helpers count only LF. Use the compiler's line map so CR
  // and Unicode line separators agree with TypeScript diagnostics and tooling.
  return node.getSourceFile().compilerNode.getLineAndCharacterOfPosition(position).line + 1;
}

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
  if (param.hasQuestionToken?.()) info.optional = true;
  if (param.isRestParameter?.()) info.rest = true;
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
    line: nodeLine(method),
    is_async: isAsync,
  };

  if (deep) {
    info.docstring = getJsDoc(method);
    info.decorators = getDecoratorNames(method);
    info.params = (method.getParameters?.() ?? []).map(extractMethodParam);
    const typeParams = (method.getTypeParameters?.() ?? []).map(typeToStr);
    if (typeParams.length) info.type_params = typeParams;
    const returnTypeNode = method.getReturnTypeNode?.();
    info.return_type = typeToStr(returnTypeNode);
    if (method.isImplementation?.()) {
      const overloads = method.getOverloads?.() ?? [];
      if (overloads.length) info.overloads = overloads.map(extractMethodInfo);
    }
  }

  return info;
}

function nodeEndLine(node) {
  try {
    return nodeLine(node, Math.max(node.getStart(), node.getEnd() - 1));
  } catch {
    return undefined;
  }
}

function functionBaseInfo(node, name, line = null) {
  const startLine = line ?? nodeLine(node);
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
    const typeParams = (fn.getTypeParameters?.() ?? []).map(typeToStr);
    if (typeParams.length) info.type_params = typeParams;
    info.return_type = typeToStr(fn.getReturnTypeNode?.());
    if (fn.isImplementation?.()) {
      const overloads = fn.getOverloads?.() ?? [];
      if (overloads.length) info.overloads = overloads.map(node => extractFunctionInfo(node, name));
    }
  } else if (isAsync) {
    info.async = true;
  }

  return info;
}

function extractConstructorInfo(ctor) {
  const info = {
    name: "constructor",
    line: nodeLine(ctor),
    is_async: false,
    docstring: getJsDoc(ctor),
    decorators: [],
    params: ctor.getParameters().map(extractMethodParam),
    return_type: "",
  };
  if (ctor.isImplementation()) {
    const overloads = ctor.getOverloads();
    if (overloads.length) info.overloads = overloads.map(extractConstructorInfo);
  }
  return info;
}

function extractProperty(prop) {
  const info = {
    name: prop.getName(),
    type: "",
    // A union with undefined does not make a property optional.
    optional: prop.hasQuestionToken?.() ?? false,
  };
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
        line: nodeLine(decl),
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

  const call = { name, line: line ?? nodeLine(expr) };
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
          nodeLine(decl)
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
        nodeLine(expr)
      );
      if (call) calls.push(call);
      continue;
    }

    const call = moduleCallFromExpression(expr, null, nodeLine(expr));
    if (call) calls.push(call);
  }
  return calls;
}

function extractImportRecords(sourceFile) {
  const imports = [];
  const typescript = ![".js", ".jsx", ".mjs", ".cjs"].includes(path.extname(sourceFile.getFilePath()));
  const qualification = (typeOnly, hasClause) => typescript ? {
    ...(typeOnly ? { type_only: true, type_only_declaration: true } : {}),
    runtime: sourceFile.isDeclarationFile() || typeOnly ? "erased" : hasClause ? "conditional" : "present",
  } : {};
  for (const imp of sourceFile.getImportDeclarations()) {
    const moduleSpecifier = imp.getModuleSpecifierValue();
    const defaultImport = imp.getDefaultImport();
    const namedImports = imp.getNamedImports();
    const ns = imp.getNamespaceImport();
    const phase = qualification(imp.isTypeOnly(), !!imp.getImportClause());
    if (defaultImport) {
      imports.push({
        module: moduleSpecifier,
        name: defaultImport.getText(),
        alias: null,
        type: "default",
        ...phase,
      });
    }

    for (const named of namedImports) {
      imports.push({
        module: moduleSpecifier,
        name: named.getName(),
        alias: named.getAliasNode()?.getText() ?? null,
        type: "named",
        ...phase,
        ...(named.isTypeOnly() ? { type_only: true } : {}),
      });
    }

    if (ns) {
      imports.push({
        module: moduleSpecifier,
        name: ns.getText(),
        alias: null,
        type: "namespace",
        ...phase,
      });
    }
    if (!defaultImport && namedImports.length === 0 && !ns) {
      imports.push({ module: moduleSpecifier, name: "", alias: null, type: "side-effect", ...phase });
    }
  }
  for (const imp of sourceFile.getStatements().filter(node => node.getKind() === SyntaxKind.ImportEqualsDeclaration)) {
    const reference = imp.getModuleReference();
    if (reference.getKind() !== SyntaxKind.ExternalModuleReference) continue;
    const expression = reference.getExpression();
    if (expression?.getKind() !== SyntaxKind.StringLiteral) continue;
    imports.push({ module: expression.getLiteralValue(), name: imp.getName(), alias: null,
      type: "namespace", ...qualification(imp.isTypeOnly(), true) });
  }
  const gaps = [];
  for (const call of sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression)) {
    const expression = call.getExpression();
    const isDynamicImport = expression.getKind() === SyntaxKind.ImportKeyword;
    const isRequire = expression.getKind() === SyntaxKind.Identifier && expression.getText() === "require";
    if (!isRequire && !isDynamicImport) continue;
    const line = nodeLine(call);
    if (isRequire && requireIsShadowed(call)) {
      gaps.push({ line, reason: "shadowed-call-not-module-import" });
      continue;
    }
    const argument = call.getArguments()[0];
    const literal = call.getArguments().length === 1 && argument?.getKind() === SyntaxKind.StringLiteral;
    const deferred = call.getAncestors().some((node) => [
      SyntaxKind.FunctionDeclaration, SyntaxKind.FunctionExpression, SyntaxKind.ArrowFunction,
      SyntaxKind.MethodDeclaration, SyntaxKind.Constructor, SyntaxKind.GetAccessor, SyntaxKind.SetAccessor,
    ].includes(node.getKind()));
    if (isRequire && literal) {
      imports.push({ module: argument.getLiteralValue(), name: "", alias: null, type: "require", line,
        ...(deferred ? { scope: "deferred" } : {}) });
    } else {
      imports.push({ module: "", name: "", type: isDynamicImport ? "dynamic-import" : "require",
        line, resolution: "unresolved", reason: isDynamicImport ? "dynamic-import" : "dynamic-require",
        ...(deferred ? { scope: "deferred" } : {}) });
    }
  }
  for (const declaration of sourceFile.getDescendantsOfKind(SyntaxKind.VariableDeclaration)) {
    if (declaration.getInitializer()?.getText() === "require") {
      gaps.push({ line: nodeLine(declaration), reason: "indirect-require-unsupported" });
    }
  }
  return { imports, gaps };
}

function bindingNames(node) {
  if (!node) return [];
  if (node.getKind() === SyntaxKind.Identifier) return [node.getText()];
  return (node.getElements?.() ?? []).flatMap((element) => bindingNames(element.getNameNode?.()));
}

function enclosingFunction(node) {
  return node.getFirstAncestor((ancestor) => [SyntaxKind.FunctionDeclaration, SyntaxKind.FunctionExpression,
    SyntaxKind.ArrowFunction, SyntaxKind.MethodDeclaration, SyntaxKind.Constructor,
    SyntaxKind.GetAccessor, SyntaxKind.SetAccessor].includes(ancestor.getKind()));
}

function requireIsShadowed(call) {
  // JavaScript files may not participate in the TypeScript type checker. Use
  // conservative lexical bindings rather than assuming an absent symbol is global.
  const scopeKinds = [SyntaxKind.SourceFile, SyntaxKind.Block, SyntaxKind.CatchClause,
    SyntaxKind.ForStatement, SyntaxKind.ForInStatement, SyntaxKind.ForOfStatement];
  const source = call.getSourceFile();
  for (const declaration of source.getDescendantsOfKind(SyntaxKind.VariableDeclaration)) {
    if (declaration.getFirstAncestorByKind(SyntaxKind.VariableDeclarationList)?.getDeclarationKind() === "var"
      && enclosingFunction(declaration) === enclosingFunction(call)
      && bindingNames(declaration.getNameNode()).includes("require")) return true;
  }
  if (source.getDescendantsOfKind(SyntaxKind.BinaryExpression).some((assignment) =>
    assignment.getLeft().getText() === "require" && ["=", "||=", "&&=", "??="].includes(assignment.getOperatorToken().getText()))) return true;
  for (const scope of call.getAncestors()) {
    if (scope.getParameters?.().some((parameter) => bindingNames(parameter.getNameNode()).includes("require"))) return true;
    if (scope.getKind() === SyntaxKind.FunctionExpression && scope.getName?.() === "require") return true;
    if (scope.getKind() === SyntaxKind.CatchClause && bindingNames(scope.getVariableDeclaration()?.getNameNode()).includes("require")) return true;
    if (!scopeKinds.includes(scope.getKind())) continue;
    const bindings = scope.getDescendantsOfKind(SyntaxKind.VariableDeclaration).concat(
      scope.getDescendantsOfKind(SyntaxKind.FunctionDeclaration), scope.getDescendantsOfKind(SyntaxKind.ClassDeclaration),
      scope.getDescendantsOfKind(SyntaxKind.ImportSpecifier), scope.getDescendantsOfKind(SyntaxKind.ImportClause),
      scope.getDescendantsOfKind(SyntaxKind.NamespaceImport),
    );
    for (const binding of bindings) {
      const owner = binding.getFirstAncestor((node) => scopeKinds.includes(node.getKind()));
      if (owner !== scope) continue;
      const name = binding.getAliasNode?.() ?? binding.getNameNode?.() ?? binding.getDefaultImport?.();
      if (bindingNames(name).includes("require")) return true;
    }
  }
  return false;
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
  return [".js", ".mjs", ".cjs"].includes(path.extname(filePath));
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
    const bases = baseExpr ? [baseExpr.getText()] : [];
    const implementsExprs = cls.getImplements().map((i) => i.getText());

    const clsLine = nodeLine(cls);
    const clsName = cls.getName() ?? `<anonymous_L${clsLine}>`;
    if (deep) {
      fileEntry.classes.push({
        name: clsName,
        kind: "class",
        bases: [...bases, ...implementsExprs],
        line: clsLine,
        docstring: getJsDoc(cls),
        decorators: getDecoratorNames(cls),
        type_params: cls.getTypeParameters().map(typeToStr),
        attributes: cls.getProperties().map(extractProperty),
        methods: [
          ...cls.getMethods().map(extractMethodInfo),
          ...cls.getConstructors().map(extractConstructorInfo),
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
    const bases = iface.getExtends().map((n) => n.getText());

    if (deep) {
      fileEntry.classes.push({
        name: iface.getName(),
        kind: "interface",
        bases,
        line: nodeLine(iface),
        docstring: getJsDoc(iface),
        decorators: [],
        type_params: iface.getTypeParameters().map(typeToStr),
        attributes: iface.getProperties().map(extractProperty),
        methods: iface.getMethods().map(extractMethodInfo),
      });
    } else {
      fileEntry.classes.push({
        name: iface.getName(),
        kind: "interface",
        bases,
        line: nodeLine(iface),
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
        line: nodeLine(en),
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
        line: nodeLine(en),
      });
    }
  }

  // ── Type aliases ───────────────────────────────────────────────────────────
  for (const ta of sourceFile.getTypeAliases()) {
    const target = deep ? typeToStr(ta.getTypeNode()) : "";
    const definition = Array.from(target);
    fileEntry.classes.push({
      name: ta.getName(),
      kind: "type_alias",
      bases: [],
      line: nodeLine(ta),
      ...(deep ? {
        docstring: getJsDoc(ta), decorators: [], attributes: [], methods: [],
        type_params: ta.getTypeParameters().map(typeToStr),
        target: definition.slice(0, 4096).join(""),
        ...(definition.length > 4096 ? {
          target_truncated: true,
          target_sha256: "sha256:" + crypto.createHash("sha256").update(target, "utf8").digest("hex"),
        } : {}),
      } : {}),
    });
  }

  // ── Functions ──────────────────────────────────────────────────────────────
  for (const fn of sourceFile.getFunctions()) {
    const fnName = fn.getName() ?? "";
    if (!shouldIncludeTopLevelFunction(fn, filePath, cjs)) continue;

    fileEntry.functions.push(
      extractFunctionInfo(
        fn,
        fnName || `<anonymous_L${nodeLine(fn)}>`
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
      nodeLine(varDecl)
    );
    if (deep) info.decorators = [];
    fileEntry.functions.push(info);
  }

  // ── Module-level signals ───────────────────────────────────────────────────
  const { imports, gaps } = extractImportRecords(sourceFile);
  if (imports.length > 0) fileEntry.imports = imports;
  if (gaps.length > 0) fileEntry.import_gaps = gaps;

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
  const documentable = (
    fileEntry.classes.length > 0 ||
    fileEntry.functions.length > 0 ||
    hasDocumentableModuleSignals(fileEntry, moduleDocstring) || fileEntry.import_gaps?.length
  );
  if (documentable || includeEmpty || retainedEmptyFiles.has(relativePathFromSrc(filePath))) {
    if (!documentable) fileEntry.empty_module = true;
    return [filePath, fileEntry, Boolean(documentable)];
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
const requestedFiles = new Set(filesToProcess.map((f) => f.split(path.sep).join("/")));

for (const sourceFile of project.getSourceFiles()) {
  // Skip files outside srcDir (e.g. from lib.d.ts loaded via tsconfig).
  // Use separator-aware prefix to avoid false matches on sibling dirs like src-gen/.
  // ts-morph always returns forward-slash paths, so compare against srcDirPosix.
  const fp = sourceFile.getFilePath();
  if (!fp.startsWith(srcDirPosix + "/") && fp !== srcDirPosix) continue;
  if (onlyFilesArg && !requestedFiles.has(fp)) continue;
  if (isExcluded(fp)) continue;

  try {
    if (diagnostics && sourceFile.compilerNode.parseDiagnostics?.length) {
      outcomes[relativePathFromSrc(fp)] = { extraction_state: "failed", reason: "syntax-error", failure_scope: "file" };
      continue;
    }
    const result = extractFile(sourceFile);
    if (result) {
      const [filePath, fileEntry, documentable] = result;
      inventory[filePath] = fileEntry;
      outcomes[relativePathFromSrc(fp)] = documentable
        ? { extraction_state: "extracted", reason: "inventory-entry" }
        : { extraction_state: "extracted", reason: "inventory-entry", retained_empty: true };
    } else {
      outcomes[relativePathFromSrc(fp)] = { extraction_state: "no-documentable-content", reason: "no-documentable-content" };
    }
  } catch (err) {
    outcomes[relativePathFromSrc(fp)] = { extraction_state: "failed", reason: "extraction-error", failure_scope: "file" };
    process.stderr.write(`Warning: failed to extract ${fp}: ${err.message}\n`);
  }
}

process.stdout.write(JSON.stringify(diagnostics
  ? { schema_version: "llm-wiki-typescript-diagnostics/v1", inventory, outcomes }
  : inventory));
