// Independent compiler-AST observer. Never load target modules or tsconfig plugins.
const fs = require("node:fs");
const ts = require(process.argv[2]).ts;

function source(text, filename = "probe.ts") {
  const file = ts.createSourceFile(filename, text, ts.ScriptTarget.Latest, true,
    filename.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
  if (file.parseDiagnostics.length) throw Error(ts.flattenDiagnosticMessageText(file.parseDiagnostics[0].messageText, " "));
  return file;
}
function shape(node, file) {
  if (!node) return null;
  if (ts.isParenthesizedTypeNode(node) || ts.isParenthesizedExpression(node)) return shape(node.type || node.expression, file);
  const children = [];
  ts.forEachChild(node, child => { children.push(shape(child, file)); });
  if (children.length) return [ts.SyntaxKind[node.kind], children];
  return [ts.SyntaxKind[node.kind], node.text === undefined ? node.getText(file) : node.text];
}
function normalize(mode, text) {
  if (mode === "type" && /^(?:asserts\s+|[\w$]+\s+is\s+)/.test(text.trim())) {
    const file = source(`declare function probe(): ${text};`);
    return shape(file.statements[0].type, file);
  }
  const file = source(mode === "type" ? `type Probe = ${text};` : `const probe = (${text});`);
  const node = mode === "type" ? file.statements[0].type : file.statements[0].declarationList.declarations[0].initializer;
  return shape(node, file);
}
function observe(text, filename) {
  const file = source(text, filename), declarations = [], imports = [];
  const raw = node => node ? node.getText(file) : "";
  const line = node => file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1;
  const name = node => node.name ? raw(node.name).replace(/^['"]|['"]$/g, "") : "";
  const params = node => (node.parameters || []).map(p => {
    const result = {name: name(p), type: raw(p.type), optional: !!p.questionToken, rest: !!p.dotDotDotToken};
    if (p.initializer) result.default = raw(p.initializer);
    return result;
  });
  function addCallable(node, symbol, owner, position = node) {
    declarations.push({kind: owner ? "method" : "function", owner, name: symbol,
      line: line(position), params: params(node), return_type: raw(node.type),
      type_parameters: (node.typeParameters || []).map(raw),
      is_async: !!node.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword)});
  }
  for (const node of file.statements) {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
      imports.push({module: node.moduleSpecifier.text, line: line(node)});
    } else if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node)) {
      const owner = name(node);
      if (!owner) continue;
      declarations.push({kind: "class", name: owner, owner: "", line: line(node),
        declaration_kind: ts.isInterfaceDeclaration(node) ? "interface" : "class",
        bases: (node.heritageClauses || []).flatMap(c => c.types.map(raw)),
        type_parameters: (node.typeParameters || []).map(raw)});
      for (const member of node.members) {
        if (ts.isPropertyDeclaration(member) || ts.isPropertySignature(member)) {
          const record = {kind: "attribute", name: name(member), owner, line: line(member),
            type: raw(member.type), optional: !!member.questionToken,
            readonly: !!member.modifiers?.some(m => m.kind === ts.SyntaxKind.ReadonlyKeyword)};
          if (member.initializer) record.default = raw(member.initializer);
          declarations.push(record);
        } else if (ts.isMethodDeclaration(member) || ts.isMethodSignature(member)) {
          addCallable(member, name(member), owner);
        } else if (ts.isConstructorDeclaration(member)) {
          addCallable(member, "constructor", owner);
        }
      }
    } else if (ts.isTypeAliasDeclaration(node)) {
      declarations.push({kind: "class", declaration_kind: "type_alias", name: name(node), owner: "", line: line(node), type: raw(node.type), type_parameters: (node.typeParameters || []).map(raw)});
    } else if (ts.isEnumDeclaration(node)) {
      declarations.push({kind: "class", declaration_kind: "enum", name: name(node), owner: "", line: line(node)});
    } else if (ts.isFunctionDeclaration(node) && node.name) {
      addCallable(node, name(node), "");
    } else if (ts.isVariableStatement(node)) {
      for (const variable of node.declarationList.declarations) {
        if (variable.initializer && (ts.isArrowFunction(variable.initializer) || ts.isFunctionExpression(variable.initializer))) {
          addCallable(variable.initializer, name(variable), "", node);
        }
      }
    }
  }
  return {declarations, imports};
}
try {
  const jobs = JSON.parse(fs.readFileSync(0, "utf8"));
  process.stdout.write(JSON.stringify(jobs.map(j => j.mode === "source" ? observe(j.text, j.filename || "probe.ts") : normalize(j.mode, j.text))));
} catch (error) {
  process.stderr.write(String(error) + "\n"); process.exitCode = 2;
}
