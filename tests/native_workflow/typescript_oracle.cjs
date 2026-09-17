// Deliberately owned fixture control. This is not a general execution sandbox.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { Project, ts } = require(process.argv[2]);
const root = process.argv[3];
const project = new Project({useInMemoryFileSystem: true, compilerOptions: {
  strict: true, target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS
}});
for (const name of ['options.ts', 'client.ts']) {
  project.createSourceFile('/' + name, fs.readFileSync(path.join(root, name), 'utf8'));
}
const diagnostics = project.getPreEmitDiagnostics();
if (diagnostics.length) {
  console.log(JSON.stringify({compiled: false, oracle_passed: false,
    diagnostics: project.formatDiagnosticsWithColorAndContext(diagnostics)}));
} else {
  const source = project.getSourceFileOrThrow('/options.ts');
  const text = source.getEmitOutput().getOutputFiles().find(f => f.getFilePath().endsWith('.js')).getText();
  const context = {exports: {}};
  vm.runInNewContext(text + '\nglobalThis.__result = [exports.timeout({}), exports.timeout({timeout: 0}), exports.timeout({timeout: 7})];',
    context, {timeout: 3000, contextCodeGeneration: {strings: false, wasm: false}});
  console.log(JSON.stringify({compiled: true, process_exit: 0,
    oracle_passed: JSON.stringify(context.__result) === '[30,0,7]', observed: context.__result}));
}
