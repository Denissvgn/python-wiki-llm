"""Compiler and CLI import checks run by the existing TypeScript owner nodes."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

from llm_wiki_cli import cli
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services.dependencies import analyze_dependencies, detect_cycles
from llm_wiki_cli.services.extractor_helpers import get_prepared_typescript_root, resolve_helper_cache_root
from llm_wiki_cli.services.sync_manifest import SyncManifest
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# The compiler observer uses compiler nodes and emitted JS; it neither calls
# the extractor nor executes the fixture's imports or its module bodies.
_COMPILER_PROBE = r"""
const ts = require(process.argv[1]).ts;
const fs = require('node:fs');
const jobs = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = jobs.map(job => {
  const file = ts.createSourceFile(job.filename, job.text, ts.ScriptTarget.Latest, true);
  if (file.parseDiagnostics.length) throw Error('invalid fixture syntax');
  const imports = [];
  for (const node of file.statements) {
    if (ts.isImportDeclaration(node)) {
      const clause = node.importClause;
      const declaration = !!clause?.isTypeOnly;
      const bindings = [];
      if (clause?.name) bindings.push([clause.name.text, false]);
      if (clause?.namedBindings) {
        if (ts.isNamespaceImport(clause.namedBindings)) bindings.push([clause.namedBindings.name.text, false]);
        else for (const binding of clause.namedBindings.elements)
          bindings.push([(binding.propertyName || binding.name).text, !!binding.isTypeOnly]);
      }
      if (!bindings.length) bindings.push(['', false]);
      for (const [name, marker] of bindings) imports.push({module: node.moduleSpecifier.text, name,
        type_only: declaration || marker, type_only_declaration: declaration});
    } else if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) {
      imports.push({module: node.moduleReference.expression.text, name: node.name.text,
        type_only: !!node.isTypeOnly, type_only_declaration: !!node.isTypeOnly});
    }
  }
  const emitted = [false, true].map(verbatimModuleSyntax => {
    const options = {module: job.commonjs ? ts.ModuleKind.CommonJS : ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2022, verbatimModuleSyntax, noLib: true};
    let text;
    if (file.isDeclarationFile) {
      const output = [];
      const host = ts.createCompilerHost(options);
      host.getSourceFile = name => name === job.filename ? file : undefined;
      host.fileExists = name => name === job.filename;
      host.readFile = name => name === job.filename ? job.text : undefined;
      host.writeFile = (_name, contents) => output.push(contents);
      ts.createProgram([job.filename], options, host).emit();
      text = output.join('\n');
    } else text = ts.transpileModule(job.text, {fileName: job.filename, compilerOptions: options}).outputText;
    const javascript = ts.createSourceFile('emitted.js', text, ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
    const modules = [];
    function visit(node) {
      if (ts.isImportDeclaration(node)) modules.push(node.moduleSpecifier.text);
      if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === 'require'
          && node.arguments.length === 1 && ts.isStringLiteral(node.arguments[0])) modules.push(node.arguments[0].text);
      ts.forEachChild(node, visit);
    }
    visit(javascript);
    return modules;
  });
  return {imports, emitted};
});
process.stdout.write(JSON.stringify(results));
"""


def _compiler_observe(paths: list[Path], *, commonjs: bool = False) -> list[dict]:
    prepared = get_prepared_typescript_root(PROJECT_ROOT)
    node = shutil.which("node")
    assert prepared is not None and node is not None
    result = subprocess.run(
        [node, "-e", _COMPILER_PROBE, str(prepared / "node_modules/ts-morph")],
        input=json.dumps([{"filename": str(path), "text": path.read_text(), "commonjs": commonjs} for path in paths]),
        capture_output=True, text=True, check=True, timeout=30,
    )
    return json.loads(result.stdout)


IMPORT_PHASE_CASES = [
    ('import type { T as Local } from "./dep"; export type Result = Local;', "erased", [[], []], "input.ts", False),
    ('import type T from "./dep"; export type Result = T;', "erased", [[], []], "input.ts", False),
    ('import type * as Types from "./dep"; export type Result = Types.T;', "erased", [[], []], "input.ts", False),
    ('import type {} from "./dep";', "erased", [[], []], "input.ts", False),
    ('import { type T as Local } from "./dep"; export type Result = Local;', "conditional", [[], ["./dep"]], "input.ts", False),
    ('import { value, type T } from "./dep"; export const result = value;', "conditional", [["./dep"], ["./dep"]], "input.ts", False),
    ('import Default, { type T } from "./dep"; export const result = Default;', "conditional", [["./dep"], ["./dep"]], "input.ts", False),
    ('import { T } from "./dep"; export type Result = T;', "conditional", [[], ["./dep"]], "input.ts", False),
    ('import { type as Local } from "./dep"; export const result = Local;', "conditional", [["./dep"], ["./dep"]], "input.ts", False),
    ('import "./dep";', "present", [["./dep"], ["./dep"]], "input.ts", False),
    ('import {} from "./dep";', "conditional", [[], ["./dep"]], "input.ts", False),
    ('import type T = require("./dep"); export type Result = T;', "erased", [[], []], "input.ts", True),
    ('import T = require("./dep"); export const result = T;', "conditional", [["./dep"], ["./dep"]], "input.ts", True),
    ('import { T } from "./dep"; export type Result = T;', "erased", [[], []], "input.d.ts", False),
]


def check_import_markers_and_runtime_qualification_match_compiler_emission(
    tmp_path, declaration, runtime, emitted, filename, commonjs,
):
    source = tmp_path / filename
    source.write_text(declaration)
    helper = resolve_helper_cache_root(PROJECT_ROOT)
    assert helper is not None
    inventory = TypeScriptExtractor().extract(str(tmp_path), deep=True, helper_cache_dir=str(helper.parent))
    records = inventory[filename]["imports"]
    observed = _compiler_observe([source], commonjs=commonjs)[0]
    assert observed["emitted"] == emitted
    assert [{"module": record["module"], "name": record["name"],
             "type_only": record.get("type_only", False),
             "type_only_declaration": record.get("type_only_declaration", False)}
            for record in records] == observed["imports"]
    assert all(record["runtime"] == runtime for record in records)


def check_erased_cycle_bootstrap_sync_lint_and_extract_follow_source_emission(tmp_path, monkeypatch, capsys):
    a, b = tmp_path / "a.ts", tmp_path / "b.ts"
    a.write_text('import type { B } from "./b"; export interface A { b?: B; }')
    b.write_text('import type { A } from "./a"; export interface B { a?: A; }')
    helper = resolve_helper_cache_root(PROJECT_ROOT)
    assert helper is not None
    monkeypatch.chdir(tmp_path)

    def run(command, *options):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", command, "--src-dir", ".",
            *([] if command == "extract" else ["--wiki-dir", "wiki"]),
            "--helper-cache-dir", str(helper.parent), *options,
            *([] if command in {"bootstrap", "extract"} else ["--jobs", "1", "--no-cache"])])
        cli.main()
        return capsys.readouterr().out

    def extracted():
        return TypeScriptExtractor().extract(str(tmp_path), deep=True, helper_cache_dir=str(helper.parent))

    def cycle_diagnostics():
        result = json.loads(run("lint", "--strict", "--profile"))
        assert result["ok"], result["issues"]
        return [row for row in result["diagnostics"] if row["category"] == "dependency_cycles"]

    run("bootstrap", "--source-adapter")
    wiki = tmp_path / "wiki"
    load = wiki / "load-order.md"
    dependencies = wiki / "dependencies.md"
    assert "Indeterminate (cyclic) groups" not in load.read_text()
    assert "#### Type dependency cycles" in dependencies.read_text()
    assert "No runtime import cycles detected" in dependencies.read_text()
    assert "Declaration | erased" in (wiki / "modules/a.md").read_text()
    payload = json.loads(run("extract", "--deep", "--read-only"))
    assert payload["inventory"]["a.ts"]["imports"][0]["type_only_declaration"] is True
    assert payload["dependencies"]["cycles"] == []
    assert payload["dependencies"]["import_time_edges"] == []
    assert payload["dependencies"]["type_cycles"] == [["a.ts", "b.ts"]]
    assert payload["dependencies"]["type_only_edges"] == [["a.ts", "b.ts"], ["b.ts", "a.ts"]]
    assert cycle_diagnostics() == []
    before = SyncManifest.load(wiki).sources["a.ts"]["semantic_hash"]
    dependencies.write_text(dependencies.read_text() + "\nAuthored initialization guidance.\n")

    # Identical symbols and paths, different markers: one possible edge cannot
    # close a runtime cycle while the other statement is guaranteed erased.
    a.write_text(a.read_text().replace("import type { B }", "import { type B }"))
    run("sync", "--no-plugins")
    assert SyncManifest.load(wiki).sources["a.ts"]["semantic_hash"] != before
    assert "Indeterminate (cyclic) groups" not in load.read_text()
    assert "Specifier | compiler-dependent" in (wiki / "modules/a.md").read_text()
    assert cycle_diagnostics() == []

    b.write_text(b.read_text().replace("import type { A }", "import { type A }"))
    run("sync", "--no-plugins")
    observed = _compiler_observe([a, b])
    assert [item["emitted"] for item in observed] == [[[], ["./b"]], [[], ["./a"]]]
    analysis = analyze_dependencies(extracted(), tmp_path)
    assert analysis["cycles"] == analysis["conditional_cycles"] == [["a.ts", "b.ts"]]
    assert "compiler-dependent TypeScript emission" in load.read_text()
    assert "compiler-dependent startup cycle candidate" in (wiki / "modules/a.md").read_text()
    payload = json.loads(run("extract", "--deep", "--read-only"))
    assert payload["dependencies"]["conditional_cycles"] == [["a.ts", "b.ts"]]
    assert payload["dependencies"]["import_time_edges"] == [["a.ts", "b.ts"], ["b.ts", "a.ts"]]
    diagnostics = cycle_diagnostics()
    assert len(diagnostics) == 1 and "Potential import cycle" in diagnostics[0]["message"]

    a.write_text(a.read_text().replace("import { type B }", "import type { B }"))
    b.write_text(b.read_text().replace("import { type A }", "import type { A }"))
    run("sync", "--no-plugins")
    assert "Indeterminate (cyclic) groups" not in load.read_text()
    assert "Authored initialization guidance." in dependencies.read_text()
    assert cycle_diagnostics() == []
    before_repeat = load.read_bytes(), dependencies.read_bytes()
    run("sync", "--no-plugins")
    assert before_repeat == (load.read_bytes(), dependencies.read_bytes())


def check_emitted_runtime_cycle_control_survives_type_partition(tmp_path, bare):
    a, b = tmp_path / "a.ts", tmp_path / "b.ts"
    if bare:
        a.write_text('import "./b"; export interface A {}')
        b.write_text('import "./a"; export interface B {}')
    else:
        a.write_text('import { valueB, type B } from "./b"; export interface A { b?: B; } export const valueA = () => valueB;')
        b.write_text('import { valueA, type A } from "./a"; export interface B { a?: A; } export const valueB = () => valueA;')
    helper = resolve_helper_cache_root(PROJECT_ROOT)
    assert helper is not None
    inventory = TypeScriptExtractor().extract(str(tmp_path), deep=True, helper_cache_dir=str(helper.parent))
    analysis = analyze_dependencies(inventory, tmp_path)
    emitted = _compiler_observe([a, b])
    for configuration in (0, 1):
        graph = {"nodes": ["a.ts", "b.ts"], "edges": [(path.name, module[2:] + ".ts")
            for path, observation in zip((a, b), emitted) for module in observation["emitted"][configuration]]}
        assert detect_cycles(graph) == [["a.ts", "b.ts"]]
    assert analysis["cycles"] == analysis["load_order"]["cycle_groups"] == [["a.ts", "b.ts"]]
    assert analysis.get("conditional_cycles", []) == ([] if bare else [["a.ts", "b.ts"]])


def check_preserved_subcycle_and_cached_sync_keep_both_compiler_projections(tmp_path, monkeypatch, capsys):
    a, b, c = (tmp_path / name for name in ("a.ts", "b.ts", "c.ts"))
    a.write_text('import "./b"; export interface A {}')
    b.write_text('import "./a"; import { type C } from "./c"; export interface B { c?: C; }')
    c.write_text('import { type B } from "./b"; export interface C { b?: B; }')
    emitted = _compiler_observe([a, b, c])
    expected = [[["a.ts", "b.ts"]], [["a.ts", "b.ts", "c.ts"]]]
    for configuration in (0, 1):
        graph = {"nodes": ["a.ts", "b.ts", "c.ts"], "edges": [(path.name, module[2:] + ".ts")
            for path, observation in zip((a, b, c), emitted) for module in observation["emitted"][configuration]]}
        assert detect_cycles(graph) == expected[configuration]
    helper = resolve_helper_cache_root(PROJECT_ROOT)
    assert helper is not None
    monkeypatch.chdir(tmp_path)

    def run(command, *options):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", command, "--src-dir", ".",
            *([] if command == "extract" else ["--wiki-dir", "wiki"]),
            "--helper-cache-dir", str(helper.parent), *options,
            *([] if command in {"bootstrap", "extract"} else ["--jobs", "1", "--cache-dir", str(tmp_path / "cache")])])
        cli.main()
        return capsys.readouterr().out

    run("bootstrap", "--source-adapter")
    wiki = tmp_path / "wiki"
    preserved = "- [a](modules/a.md) ⇄ [b](modules/b.md)"
    candidate = preserved + " ⇄ [c](modules/c.md) *(compiler-dependent TypeScript emission)*"

    def check_views():
        for page in ("dependencies.md", "load-order.md"):
            lines = (wiki / page).read_text().split("\n")
            assert preserved in lines and candidate in lines
        for name in ("a", "b"):
            assert "### Preserved startup cycles" in (wiki / f"modules/{name}.md").read_text()
        assert "### Preserved startup cycles" not in (wiki / "modules/c.md").read_text()
        payload = json.loads(run("extract", "--deep", "--read-only"))["dependencies"]
        assert payload["preserved_cycles"] == [["a.ts", "b.ts"]]
        assert payload["cycles"] == payload["conditional_cycles"] == [["a.ts", "b.ts", "c.ts"]]
        lint = json.loads(run("lint", "--strict", "--profile"))
        assert lint["ok"], lint["issues"]
        messages = [row["message"] for row in lint["diagnostics"] if row["category"] == "dependency_cycles"]
        assert "Import cycle: a.ts ⇄ b.ts" in messages
        assert any(message.startswith("Potential import cycle") and message.endswith("a.ts ⇄ b.ts ⇄ c.ts") for message in messages)

    check_views()
    run("sync", "--no-plugins")
    before = {page: (wiki / page).read_bytes() for page in ("dependencies.md", "load-order.md")}
    warm = run("sync", "--no-plugins")
    assert "Sync analysis reuse: hit" in warm
    assert before == {page: (wiki / page).read_bytes() for page in before}
    check_views()


def check_import_phase_corpus(root: Path) -> None:
    root.mkdir()
    for index, case in enumerate(IMPORT_PHASE_CASES):
        fixture = root / f"declaration-{index}"
        fixture.mkdir()
        check_import_markers_and_runtime_qualification_match_compiler_emission(fixture, *case)
    for bare in (False, True):
        fixture = root / f"runtime-{bare}"
        fixture.mkdir()
        check_emitted_runtime_cycle_control_survives_type_partition(fixture, bare)
