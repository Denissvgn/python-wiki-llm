"""Tests for the TypeScript extractor (ts_extractor.py + ts_scripts/extract.js)."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.extractors import common as extractor_common
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.extractor_helpers import (
    resolve_helper_cache_root,
    typescript_dependencies_ready,
)

# ---------------------------------------------------------------------------
# Skip all tests when Node.js is not available on this machine.
# ---------------------------------------------------------------------------


def _command_available(*cmd: str) -> bool:
    if shutil.which(cmd[0]) is None:
        return False
    try:
        subprocess.run(
            list(cmd),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return True
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return False


PROJECT_ROOT = Path(__file__).parents[1]
BUNDLED_TS_SCRIPTS = (
    PROJECT_ROOT / "src" / "llm_wiki_cli" / "extractors" / "ts_scripts"
)
NODE_AVAILABLE = (
    _command_available("node", "--version")
    and typescript_dependencies_ready(PROJECT_ROOT)
)
skip_no_node = pytest.mark.skipif(
    not NODE_AVAILABLE,
    reason="Node.js/ts-morph dependencies not installed — TypeScript extractor tests skipped",
)


@skip_no_node
@pytest.mark.parametrize("extension", ["js", "jsx", "mjs", "cjs", "ts", "tsx"])
def test_unresolved_import_producer_consumer_contract(tmp_path, extension):
    from llm_wiki_cli.services.bootstrap_runtime import _generate_module_md
    from llm_wiki_cli.services.dependencies import build_dependency_graph
    from llm_wiki_cli.services.knowledge_evidence import normalize_module_observation

    filename = f"dynamic.{extension}"
    _make_ts(tmp_path, filename, """\
        async function load(name) { return await import(name); }
        function read(name) { return require(name); }
        module.exports = { load, read };
        const eager = import(process.env.NAME);
        const literal = import('./known.js');
        const required = require('known-package');
        import { known } from './known.js';
    """)
    _make_ts(tmp_path, "known.js", "export function known() { return 1; }\n")
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    # Readiness is checked against PROJECT_ROOT, not the temporary caller or
    # pytest's working directory. Use that same native cache base for execution.
    helper_root = resolve_helper_cache_root(PROJECT_ROOT)
    assert helper_root is not None
    inventory = TypeScriptExtractor().extract(
        str(tmp_path), deep=True, helper_cache_dir=str(helper_root.parent)
    )
    data = inventory[filename]
    normalized = normalize_module_observation(data)
    assert normalized is not None
    gaps = [record for record in data["imports"] if record.get("resolution") == "unresolved"]
    assert len(gaps) == 4
    assert {gap["reason"] for gap in gaps} == {"dynamic-import", "dynamic-require"}
    assert sum(gap.get("scope") == "deferred" for gap in gaps) == 2
    assert sum(record.get("resolution") == "unresolved" for record in normalized["imports"]) == 4
    graph = build_dependency_graph(inventory)
    assert graph["edges"] == [(filename, "known.js")]
    assert sum(item.get("reason") in {"dynamic-import", "dynamic-require"} for item in graph["unresolved"]) == 4
    gap_only = deepcopy(inventory)
    gap_only[filename]['imports'] = deepcopy(gaps)
    assert build_dependency_graph(gap_only)['edges'] == []
    page = _generate_module_md(filename, data)
    assert "| `` |" not in page
    assert "Unresolved `dynamic-import`" in page
    assert "Unresolved `dynamic-require`" in page
    assert "(line 1; deferred)" in page
    assert "| `known-package` | — |" in page
    for field, wrong in (("reason", "not-a-gap"), ("resolution", "resolved"),
                         ("line", False), ("scope", "eager")):
        malformed = deepcopy(data)
        index = next(i for i, row in enumerate(malformed["imports"]) if row.get("resolution") == "unresolved")
        malformed["imports"][index][field] = wrong
        from llm_wiki_cli.services.knowledge_evidence import build_module_observation_basis, sha256_bytes
        rejected = build_module_observation_basis(source_path=filename, file_data=malformed,
            source_content_hash=sha256_bytes(b"source"), extractor_ref="llm-wiki/extractor/typescript", inventory_complete=True)
        assert rejected.unknown_reason == "invalid-inventory-shape"
        assert rejected.normalization_diagnostic is not None
        assert rejected.normalization_diagnostic.pointer == f"/imports/{index}/{field}"
        assert "concept_observation_hash" not in rejected.to_evidence_payload()
    assert {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before


@skip_no_node
def test_released_unknown_evidence_guarded_upgrade_and_refresh(tmp_path, monkeypatch, capsys, request):
    """Released unknown evidence remains qualified until reviewed owning work."""
    from llm_wiki_cli.commands import sync_cmd, upgrade_cmd, extract_cmd, lint_cmd, ci_check_cmd
    from llm_wiki_cli.services.knowledge_evidence import normalize_module_observation
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.knowledge_artifacts import current_knowledge_format
    from llm_wiki_cli.services.manifest_storage import current_manifest_format

    fixture = PROJECT_ROOT / "tests/fixtures/knowledge-evidence/released-2.5.0-large-files.json"
    provenance = json.loads((fixture.parent / 'released-2.5.0-large.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == provenance['bundle_sha256']
    assert provenance['producer_version'] == '2.5.0' and provenance['source_count'] == 261
    bundle = json.loads(fixture.read_text(encoding='utf-8'))
    assert set(bundle) == set(provenance['files'])
    for name, text in bundle.items():
        assert not name.startswith('/') and '..' not in name.split('/') and '\\' not in name
        data = text.encode('utf-8')
        assert hashlib.sha256(data).hexdigest() == provenance['files'][name]
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    monkeypatch.chdir(tmp_path)
    helper = resolve_helper_cache_root(PROJECT_ROOT)
    assert helper is not None
    from llm_wiki_cli.services.maintenance_protocol import governance_writer_lock, storage_writer_lock

    # Persistent operational locks are setup state, not canonical prose or
    # provenance. Capture the refusal baseline after provisioning both locks.
    with governance_writer_lock(tmp_path / 'wiki'), storage_writer_lock(tmp_path / 'wiki'):
        pass
    common = ['--src-dir', '.', '--wiki-dir', 'wiki', '--source-selection', '.llm-wiki/source-selection.json',
              '--helper-cache-dir', str(helper.parent), '--jobs', '1', '--no-cache']
    sync = ['sync', *common, '--no-plugins']
    parser = cli._build_parser()

    def files(root):
        return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns, p.stat().st_size)
                for p in root.rglob('*') if p.is_file()}

    def state():
        result = load_knowledge_state(tmp_path / 'wiki')
        assert result.knowledge is not None and result.manifest_basis is not None
        return result

    source_before = files(tmp_path / 'src')
    old = state()
    assert old.knowledge is not None and old.manifest_basis is not None
    assert old.knowledge.bundle.producer.tool.version == '2.5.0'
    assert len(old.manifest_basis.sources) == 261
    assert old.manifest_basis.evidence_baselines['modules/dyn.md'].unknown_reason == 'invalid-inventory-shape'
    before_read = files(tmp_path)
    raw = extract_cmd.build_extract_payload('.', paths=['src/dyn.mjs'], deep=True, read_only=True,
        helper_cache_dir=str(helper.parent), source_selection='.llm-wiki/source-selection.json').payload
    assert set(raw['inventory']) == {'src/dyn.mjs'}
    assert normalize_module_observation(raw['inventory']['src/dyn.mjs']) is not None
    assert files(tmp_path) == before_read

    def only_recovery_created(before, after):
        assert not set(before) - set(after)
        assert not [p for p in set(before) & set(after) if before[p] != after[p]]
        created = sorted(set(after) - set(before))
        assert all(p.startswith('.llm-wiki-maintenance-recovery/maintenance-preimages/') for p in created)
        return len(created), sum(after[p][2] for p in created)

    refusal_recovery = []
    def guarded():
        before = files(tmp_path)
        with pytest.raises(SystemExit) as stopped:
            sync_cmd.run(parser.parse_args(sync))
        assert stopped.value.code == 1
        error = capsys.readouterr().err
        assert 'Affected source inputs: 261 (deduplicated; source files are not rewritten)' in error
        assert 'new=0, changed=0, metadata-only=0, removed=0' in error
        # The recoverable JavaScript source has its own disjoint category even
        # during a producer transition: 260 + 1 still requires full 261-source
        # review. Storage upgrade does not approve either category.
        assert 'generator-refresh-additional=260' in error
        assert 'evidence-refresh-additional=1' in error
        assert '8 shown, 253 omitted' in error and '--dry-run' in error
        refusal_recovery.append(only_recovery_created(before, files(tmp_path)))

    guarded()
    upgrade_cmd.run(parser.parse_args(['upgrade', '--wiki-dir', 'wiki', '--src-dir', '.',
        '--source-selection', '.llm-wiki/source-selection.json', '--helper-cache-dir', str(helper.parent)]))
    capsys.readouterr()
    upgraded = state()
    assert current_knowledge_format('wiki') == 'packed-v4-deflate'
    assert current_manifest_format('wiki') == 'indexed-v8'
    assert upgraded.manifest_basis is not None
    assert upgraded.manifest_basis.evidence_baselines['modules/dyn.md'].unknown_reason == 'invalid-inventory-shape'
    assert files(tmp_path / 'src') == source_before
    guarded()  # Adoption/storage upgrade does not approve a generator refresh.
    before = files(tmp_path)
    sync_cmd.run(parser.parse_args([*sync, '--dry-run']))
    preview = capsys.readouterr().out
    assert 'generator refresh sources: 260' in preview
    assert 'evidence-refresh-additional=1' in preview
    assert 'Affected source inputs: 261 (deduplicated; source files are not rewritten)' in preview
    assert 'complete source paths: 261 shown, 0 omitted' in preview
    assert 'requires --force: yes' in preview and 'this preview is not an approval token' in preview
    assert files(tmp_path) == before
    # Explicit authority is confined to this synthetic caller's reviewed plan.
    sync_cmd.run(parser.parse_args([*sync, '--force']))
    capsys.readouterr()
    refreshed = state()
    assert refreshed.manifest_basis is not None
    assert refreshed.manifest_basis.evidence_baselines['modules/dyn.md'].is_known
    assert files(tmp_path / 'src') == source_before
    assert 'Historical authored explanation' in (tmp_path / 'wiki/modules/dyn.md').read_text(encoding='utf-8')
    strict_results = []
    for command, options in ((lint_cmd, ['lint', '--strict', '--profile']),
                             (ci_check_cmd, ['ci-check', '--no-plugins', '--format', 'json', '--no-report'])):
        command.run(parser.parse_args([*options, *common]))
        report = json.loads(capsys.readouterr().out)
        assert report['ok'] and not [i for i in report['issues'] if i['category'] == 'knowledge_evidence']
        strict_results.append(report['ok'])
    before_noop = files(tmp_path)
    sync_cmd.run(parser.parse_args(sync))
    capsys.readouterr()
    noop_recovery = only_recovery_created(before_noop, files(tmp_path))
    measurement = {'sources': 261, 'raw_source_changes': 0, 'generator_inputs': 261,
                   'read_changed_files': 0, 'refusals_preserved_state': 2,
                   'preview_changed_files': 0, 'repaired_modules': 1,
                   'strict_passes': sum(strict_results), 'noop_active_byte_or_mtime_changes': 0,
                   'refusal_recovery_created_files_bytes': refusal_recovery,
                   'noop_recovery_created_files_bytes': noop_recovery,
                   'fixture_sha256': provenance['bundle_sha256']}
    request.node.user_properties.append(('transition_measurement', json.dumps(measurement, sort_keys=True)))


@skip_no_node
def test_dynamic_import_gap_survives_bootstrap_sync_and_strict_gates(tmp_path, monkeypatch, capsys):
    helper_root = resolve_helper_cache_root(PROJECT_ROOT)
    assert helper_root is not None
    _make_ts(tmp_path, "dyn.mjs", "export async function load(name) { return await import(name); }\n")
    monkeypatch.chdir(tmp_path)

    def run(command, *options):
        monkeypatch.setattr(sys, "argv", [
            "llm-wiki", command, "--src-dir", ".", "--wiki-dir", "wiki",
            "--helper-cache-dir", str(helper_root.parent), *options,
            *([] if command == "bootstrap" else ["--jobs", "1"]),
        ])
        cli.main()
        return capsys.readouterr().out

    run("bootstrap", "--source-adapter")
    page = tmp_path / "wiki/modules/dyn.md"
    assert "Unresolved `dynamic-import`" in page.read_text(encoding="utf-8")
    run("sync", "--no-plugins")
    lint = json.loads(run("lint", "--strict", "--profile"))
    assert lint["ok"]
    assert not [issue for issue in lint["issues"] if issue["category"] == "knowledge_evidence"]
    ci = json.loads(run("ci-check", "--format", "json", "--no-report", "--no-plugins"))
    assert ci["ok"]
    manifest = SyncManifest.load(tmp_path / "wiki")
    assert manifest is not None
    basis = manifest.evidence_baselines["modules/dyn.md"].basis
    assert basis is not None
    assert basis.is_known

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ts(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def _write_owned_package_sentinels(root: Path) -> None:
    for rel_path in (
        "src/llm_wiki_cli/__init__.py",
        "src/llm_wiki_cli/cli.py",
        "src/llm_wiki_cli/extractors/__init__.py",
        "src/llm_wiki_cli/extractors/common.py",
    ):
        _make_ts(root, rel_path, "# package source\n")


class TestTypeScriptWrapperFiltering:
    def test_full_scan_passes_gitignore_filtered_files_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        _make_ts(tmp_path, "real.ts", "export class Real {}")
        _make_ts(tmp_path, "ignored.ts", "export class Ignored {}")
        (tmp_path / ".gitignore").write_text("ignored.ts\n", encoding="utf-8")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"real.ts":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(str(tmp_path))

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "real.ts"

    def test_full_scan_skips_generated_javascript_bundles(self, tmp_path, monkeypatch):
        _make_ts(
            tmp_path,
            "services/dashboard/frontend/src/main.js",
            "export const app = 1;",
        )
        _make_ts(
            tmp_path,
            "services/dashboard/static/assets/index-D0zaI3XT.js",
            "function a(){};export{a as Ko};",
        )
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"services/dashboard/frontend/src/main.js":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(str(tmp_path))

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "services/dashboard/frontend/src/main.js"

    def test_only_files_passes_gitignored_explicit_files_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        _make_ts(tmp_path, "frontend/src/lib/api.ts", "export const api = 1;")
        (tmp_path / ".gitignore").write_text("lib/\n", encoding="utf-8")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"frontend/src/lib/api.ts":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(
            str(tmp_path),
            only_files=["frontend/src/lib/api.ts"],
        )

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "frontend/src/lib/api.ts"

    def test_only_files_passes_exact_generated_javascript_bundle_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        generated = "services/dashboard/static/assets/index-D0zaI3XT.js"
        _make_ts(tmp_path, generated, "function a(){};export{a as Ko};")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"services/dashboard/static/assets/index-D0zaI3XT.js":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(str(tmp_path), only_files=[generated])

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == generated

    def test_large_file_selection_is_split_across_subprocess_calls(
        self, tmp_path, monkeypatch
    ):
        paths = ["src/a.ts", "src/b.ts", "src/c.ts"]
        for rel in paths:
            _make_ts(tmp_path, rel, "export class Item {}\n")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            only_files = cmd[cmd.index("--only-files") + 1].split(",")
            payload = {rel: {"classes": [], "functions": []} for rel in only_files}
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps(payload),
                stderr="",
            )

        monkeypatch.setattr(extractor_common, "MAX_ONLY_FILES_ARG_CHARS", 15)
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        inv = TypeScriptExtractor().extract(str(tmp_path))

        assert set(inv) == set(paths)
        assert len(commands) > 1
        for cmd in commands:
            only_arg = cmd[cmd.index("--only-files") + 1]
            assert len(only_arg) <= extractor_common.MAX_ONLY_FILES_ARG_CHARS

    def test_js_and_jsx_files_are_extracted_with_javascript_language(
        self, tmp_path, monkeypatch
    ):
        _make_ts(tmp_path, "script.js", "export function run() {}\n")
        _make_ts(tmp_path, "view.jsx", "export function View() { return null; }\n")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps(
                    {
                        "script.js": {
                            "classes": [],
                            "functions": [{"name": "run"}],
                        },
                        "view.jsx": {
                            "classes": [],
                            "functions": [{"name": "View"}],
                        },
                    }
                ),
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert set(inv) == {"script.js", "view.jsx"}
        assert {entry["language"] for entry in inv.values()} == {"javascript"}
        cmd = commands[0]
        assert cmd[cmd.index("--extensions") + 1] == ".ts,.tsx,.js,.jsx,.mjs,.cjs"
        only_files = cmd[cmd.index("--only-files") + 1].split(",")
        assert only_files == ["script.js", "view.jsx"]


# ===========================================================================
# Unit-level tests (require Node.js)
# ===========================================================================


@skip_no_node
class TestTypeScriptExtractor:
    def test_empty_dir(self, tmp_path):
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_single_file_with_class(self, tmp_path):
        _make_ts(
            tmp_path,
            "models.ts",
            """
            export class User {
                name: string;
                age: number;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        data = list(inv.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "User"
        assert data["classes"][0]["kind"] == "class"

    def test_language_field_stamped(self, tmp_path):
        _make_ts(tmp_path, "a.ts", "export class A {}")
        inv = TypeScriptExtractor().extract(str(tmp_path))
        for entry in inv.values():
            assert entry["language"] == "typescript"

    def test_single_file_with_function(self, tmp_path):
        _make_ts(
            tmp_path,
            "utils.ts",
            """
            export function greet(name: string): string {
                return `Hello ${name}`;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        data = list(inv.values())[0]
        assert data["functions"][0]["name"] == "greet"

    def test_arrow_function_export(self, tmp_path):
        _make_ts(
            tmp_path,
            "utils.ts",
            """
            export const add = (a: number, b: number): number => a + b;
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        fns = list(inv.values())[0]["functions"]
        assert any(f["name"] == "add" for f in fns)

    def test_interface_extraction(self, tmp_path):
        _make_ts(
            tmp_path,
            "types.ts",
            """
            export interface Config {
                host: string;
                port: number;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        assert len(classes) == 1
        assert classes[0]["name"] == "Config"
        assert classes[0]["kind"] == "interface"

    def test_enum_extraction(self, tmp_path):
        _make_ts(
            tmp_path,
            "status.ts",
            """
            export enum Status {
                Active = "active",
                Inactive = "inactive",
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        assert classes[0]["name"] == "Status"
        assert classes[0]["kind"] == "enum"

    def test_type_alias_extraction(self, tmp_path):
        _make_ts(
            tmp_path,
            "aliases.ts",
            """
            export type UserId = string;
            export type Handler = (event: Event) => void;
            export type Mode = "fast" | "safe";
            export type Shape<T extends string = "ready"> = { value: T; enabled?: boolean };
            export type Fence = "```";
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        kinds = {c["kind"] for c in classes}
        assert "type_alias" in kinds
        names = {c["name"] for c in classes}
        assert "UserId" in names
        assert "Handler" in names
        assert all("target" not in record for record in classes)
        deep = TypeScriptExtractor().extract(str(tmp_path), deep=True)["aliases.ts"]
        aliases = {record["name"]: record for record in deep["classes"]}
        assert aliases["Handler"]["target"] == "(event: Event) => void"
        assert aliases["Mode"]["target"] == '"fast" | "safe"'
        assert aliases["Shape"]["target"] == "{ value: T; enabled?: boolean }"
        assert aliases["Shape"]["type_params"] == ['T extends string = "ready"']
        from llm_wiki_cli.services.bootstrap_runtime import _generate_entity_md
        page = _generate_entity_md(aliases["Mode"], "aliases.ts", {})
        assert '```typescript\n"fast" | "safe"\n```' in page
        assert "Inherits" not in page and "Kind:** Type alias" in page
        page = _generate_entity_md(aliases["Fence"], "aliases.ts", {})
        assert '````typescript\n"```"\n````' in page
        target = '"' + "雪" * 4096 + '"'
        (tmp_path / "aliases.ts").write_text("export type Bounded = " + target + ";\n")
        bounded = TypeScriptExtractor().extract(str(tmp_path), deep=True)["aliases.ts"]["classes"][0]
        assert bounded["target"] == target[:4096] and bounded["target_truncated"] is True
        assert bounded["target_sha256"] == "sha256:" + hashlib.sha256(target.encode()).hexdigest()
        assert "Definition truncated" in _generate_entity_md(bounded, "aliases.ts", {})

    def test_tsx_support(self, tmp_path):
        _make_ts(
            tmp_path,
            "Button.tsx",
            """
            export function Button(props: { label: string }) {
                return null;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        assert list(inv.values())[0]["functions"][0]["name"] == "Button"

    def test_jsx_support(self, tmp_path):
        _make_ts(
            tmp_path,
            "Button.jsx",
            """
            export function Button(props) {
                return null;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        data = inv["Button.jsx"]
        assert data["language"] == "javascript"
        assert data["functions"][0]["name"] == "Button"

    def test_skips_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules" / "somelib"
        nm.mkdir(parents=True)
        _make_ts(nm, "index.ts", "export class Hidden {}")
        _make_ts(tmp_path, "real.ts", "export class Visible {}")

        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        assert list(inv.values())[0]["classes"][0]["name"] == "Visible"

    def test_only_files_respects_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules" / "somelib"
        nm.mkdir(parents=True)
        _make_ts(nm, "index.ts", "export class Hidden {}")

        inv = TypeScriptExtractor().extract(
            str(tmp_path),
            only_files=["node_modules/somelib/index.ts"],
        )
        assert inv == {}

    def test_skips_syntax_errors(self, tmp_path):
        (tmp_path / "bad.ts").write_text("export class {{{{", encoding="utf-8")
        _make_ts(tmp_path, "good.ts", "export class OK {}")

        # Should not raise — bad file is skipped gracefully
        inv = TypeScriptExtractor().extract(str(tmp_path))
        names = [c["name"] for entry in inv.values() for c in entry["classes"]]
        assert "OK" in names

    def test_only_files_filter(self, tmp_path):
        _make_ts(tmp_path, "a.ts", "export class A {}")
        _make_ts(tmp_path, "b.ts", "export class B {}")

        inv = TypeScriptExtractor().extract(str(tmp_path), only_files=["a.ts"])
        class_names = [c["name"] for entry in inv.values() for c in entry["classes"]]
        assert "A" in class_names
        assert "B" not in class_names

    def test_bases_extracted(self, tmp_path):
        _make_ts(
            tmp_path,
            "animal.ts",
            """
            export class Animal {}
            export class Dog extends Animal {}
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        dog = next(c for c in classes if c["name"] == "Dog")
        assert "Animal" in dog["bases"]

    # ── Deep mode tests ─────────────────────────────────────────────────────

    def test_deep_mode_includes_jsdoc(self, tmp_path):
        _make_ts(
            tmp_path,
            "service.ts",
            """
            /**
             * A service that does things.
             */
            export class MyService {
                /**
                 * Run the service.
                 */
                run(): void {}
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert "service" in cls["docstring"].lower() or "things" in cls["docstring"]
        method = cls["methods"][0]
        assert (
            "run" in method["docstring"].lower()
            or "service" in method["docstring"].lower()
        )

    def test_deep_mode_includes_imports(self, tmp_path):
        _make_ts(
            tmp_path,
            "app.ts",
            """
            import { Router } from 'express';
            import path from 'path';

            export class App {
                private router: Router;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        assert "imports" in data
        module_names = {imp["module"] for imp in data["imports"]}
        assert "express" in module_names
        assert "path" in module_names

    def test_deep_mode_includes_methods(self, tmp_path):
        _make_ts(
            tmp_path,
            "calc.ts",
            """
            export class Calculator {
                add(a: number, b: number): number {
                    return a + b;
                }
                async fetchResult(id: string): Promise<number> {
                    return 0;
                }
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert len(cls["methods"]) == 2
        add = next(m for m in cls["methods"] if m["name"] == "add")
        assert add["params"][0]["name"] == "a"
        assert add["params"][0]["type"] == "number"
        assert add["return_type"] == "number"
        assert add["is_async"] is False

        fetch = next(m for m in cls["methods"] if m["name"] == "fetchResult")
        assert fetch["is_async"] is True

    def test_deep_mode_includes_attributes(self, tmp_path):
        _make_ts(
            tmp_path,
            "user.ts",
            """
            export class User {
                name: string;
                age: number = 0;
                nickname?: string;
                initialized_optional?: number = 1;
            }
            export interface EvidenceSignals {
                required_count: number;
                events_incomplete?: boolean;
                questions_awaiting_review?: number;
                required_undefined: number | undefined;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        attrs = list(inv.values())[0]["classes"][0]["attributes"]
        names = {a["name"] for a in attrs}
        assert "name" in names
        assert "age" in names
        age_attr = next(a for a in attrs if a["name"] == "age")
        assert age_attr.get("default") == "0"
        by_name = {a["name"]: a for a in attrs}
        assert by_name["name"]["optional"] is False
        assert by_name["age"]["optional"] is False
        assert by_name["nickname"] == {
            "name": "nickname",
            "type": "string",
            "default": "",
            "optional": True,
        }
        assert by_name["initialized_optional"]["optional"] is True
        assert by_name["initialized_optional"]["default"] == "1"
        interface = next(
            cls for cls in inv["user.ts"]["classes"] if cls["name"] == "EvidenceSignals"
        )
        properties = {a["name"]: a for a in interface["attributes"]}
        assert properties["required_count"]["optional"] is False
        assert properties["required_undefined"]["optional"] is False
        assert properties["required_undefined"]["type"] == "number | undefined"
        for name in ("events_incomplete", "questions_awaiting_review"):
            assert properties[name]["optional"] is True
            assert properties[name]["default"] == ""

    def test_optional_properties_bootstrap_and_incremental_sync(
        self, tmp_path, monkeypatch, capsys
    ):
        helper_root = resolve_helper_cache_root(PROJECT_ROOT)
        assert helper_root is not None
        source = _make_ts(
            tmp_path,
            "types.ts",
            """\
            export interface EvidenceSignals {
                events_incomplete?: boolean;
                change_me: number;
                required_undefined: number | undefined;
            }
            export class EvidenceState {
                initialized: number = 0;
                optional_count?: number;
            }
            export type Mode = "fast" | "safe";
            export type Handler = (value: number) => string;
            export function collect(prefix?: string, ...items: string[]): string { return ""; }
            export function identity<T extends string = "ready">(value: T): T { return value; }
            export const arrow = <T,>(first?: T, ...rest: T[]): T[] => rest;
            export class Client<T> {
                constructor(timeout?: number, ...labels: string[]) {}
                run<U extends T>(value?: U, ...items: U[]): void {}
            }
            """,
        )
        monkeypatch.chdir(tmp_path)

        def run(command):
            args = [
                "llm-wiki",
                command,
                "--src-dir",
                ".",
                "--wiki-dir",
                "wiki",
                "--helper-cache-dir",
                str(helper_root.parent),
            ]
            if command == "bootstrap":
                args.append("--source-adapter")
            else:
                args.extend(["--jobs", "1", "--cache-dir", str(tmp_path / "cache")])
            monkeypatch.setattr(sys, "argv", args)
            cli.main()

        run("bootstrap")
        page = tmp_path / "wiki/entities/EvidenceSignals.md"
        content = page.read_text(encoding="utf-8")
        assert "| `events_incomplete` | `boolean` | No | — |" in content
        assert "| `change_me` | `number` | Yes | — |" in content
        assert r"| `required_undefined` | `number \| undefined` | Yes | — |" in content
        state = (tmp_path / "wiki/entities/EvidenceState.md").read_text(encoding="utf-8")
        assert "| `initialized` | `number` | Yes | `0` |" in state
        assert "| `optional_count` | `number` | No | — |" in state
        module = (tmp_path / "wiki/modules/types.md").read_text()
        assert "(prefix?: string, ...items: string[]) -> string" in module
        assert '<T extends string = "ready">(value: T) -> T' in module
        assert "<T>(first?: T, ...rest: T[]) -> T[]" in module
        assert "| [EvidenceSignals](../entities/EvidenceSignals.md) | Interface |" in module
        assert "**Kind:** Interface" in content and "Inherits" not in content
        client = (tmp_path / "wiki/entities/Client.md").read_text()
        assert "**Type parameters:** `T`" in client
        assert "(timeout?: number, ...labels: string[])" in client
        assert "<U extends T>(value?: U, ...items: U[]) -> void" in client
        assert '```typescript\n"fast" | "safe"\n```' in (tmp_path / "wiki/entities/Mode.md").read_text()
        assert "(value: number) => string" in (tmp_path / "wiki/entities/Handler.md").read_text()
        content = content.replace(
            "_Auto-generated from `EvidenceSignals` in `types.ts`._",
            "Human-curated evidence contract.",
        ).replace(
            "| `events_incomplete` | `boolean` | No | — | — |",
            "| `events_incomplete` | `boolean` | No | — | Omission means unavailable. |",
        )
        page.write_text(content, encoding="utf-8")
        before = SyncManifest.load(tmp_path / "wiki").sources
        source.write_text(
            source.read_text(encoding="utf-8").replace("change_me:", "change_me?:").replace('"safe"', '"careful"').replace("prefix?:", "prefix:"),
            encoding="utf-8",
        )
        capsys.readouterr()
        run("sync")
        assert "UPDATE entity: EvidenceSignals" in capsys.readouterr().out
        after = SyncManifest.load(tmp_path / "wiki").sources
        assert (
            before["types.ts"]["semantic_hash"]
            != after["types.ts"]["semantic_hash"]
        )
        content = page.read_text(encoding="utf-8")
        assert "| `change_me` | `number` | No | — |" in content
        assert "Human-curated evidence contract." in content
        assert "Omission means unavailable." in content
        assert '"careful"' in (tmp_path / "wiki/entities/Mode.md").read_text()
        assert "(prefix: string, ...items: string[]) -> string" in (tmp_path / "wiki/modules/types.md").read_text()
        run("sync")
        assert page.read_text(encoding="utf-8") == content

    def test_deep_mode_decorators(self, tmp_path):
        _make_ts(
            tmp_path,
            "component.ts",
            """
            function Component(target: any) {}

            @Component
            export class MyComponent {
                @Component
                value: string = "";
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert "Component" in cls["decorators"]

    def test_enum_deep_members(self, tmp_path):
        _make_ts(
            tmp_path,
            "status.ts",
            """
            export enum Direction {
                Up = "UP",
                Down = "DOWN",
                Left = "LEFT",
                Right = "RIGHT",
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert cls["kind"] == "enum"
        member_names = {a["name"] for a in cls["attributes"]}
        assert {"Up", "Down", "Left", "Right"} == member_names

    def test_interface_deep_methods(self, tmp_path):
        _make_ts(
            tmp_path,
            "repo.ts",
            """
            export interface Repository<T> {
                findById(id: string): Promise<T>;
                save(entity: T): Promise<void>;
                select<U extends T = T>(value?: U, ...rest: U[]): U;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert cls["kind"] == "interface"
        method_names = {m["name"] for m in cls["methods"]}
        assert "findById" in method_names
        assert "save" in method_names
        method = next(m for m in cls["methods"] if m["name"] == "select")
        assert cls["type_params"] == ["T"]
        assert method["type_params"] == ["U extends T = T"]
        assert method["params"][0]["optional"] is True
        assert method["params"][1]["rest"] is True


# ===========================================================================
# Graceful-degradation tests (Node.js mocked away, no Node.js required)
# ===========================================================================


class TestTypeScriptExtractorWithoutNode:
    def test_node_not_available_returns_empty(self, tmp_path):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        with patch("shutil.which", return_value=None):
            inv = TypeScriptExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_node_not_available_warns_to_stderr(self, tmp_path, capsys):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        with patch("shutil.which", return_value=None):
            TypeScriptExtractor().extract(str(tmp_path))
        err = capsys.readouterr().err
        assert (
            "node" in err.lower() or "nodejs" in err.lower() or "node.js" in err.lower()
        )

    def test_no_ts_files_skips_toolchain_probe(self, tmp_path):
        with patch("llm_wiki_cli.extractors.ts_extractor.shutil.which") as mock_which:
            inv = TypeScriptExtractor().extract(str(tmp_path))
        assert inv == {}
        mock_which.assert_not_called()


class TestTypeScriptExtractorWrapper:
    def test_extract_remains_short_orchestrator(self):
        source = textwrap.dedent(inspect.getsource(TypeScriptExtractor.extract))
        function_node = ast.parse(source).body[0]
        assert isinstance(function_node, ast.FunctionDef)
        body = list(function_node.body)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]

        first_body_line = min(stmt.lineno for stmt in body)
        last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
        body_lines = last_body_line - first_body_line + 1

        assert body_lines <= 35

    def test_missing_dependencies_do_not_invoke_npm_install(self, tmp_path):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=None,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run"
                ) as mock_run:
                    inv = TypeScriptExtractor().extract(str(tmp_path))

        assert inv == {}
        mock_run.assert_not_called()

    def test_explicit_helper_cache_dir_is_forwarded(self, tmp_path):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        helper_cache = str(tmp_path / "helpers")
        seen = {}

        def fake_root(src_dir, cache_dir=None):
            seen["src_dir"] = src_dir
            seen["cache_dir"] = cache_dir
            return BUNDLED_TS_SCRIPTS

        result = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout='{"app.ts": {"classes": [], "functions": []}}',
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                side_effect=fake_root,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run",
                    return_value=result,
                ):
                    inv = TypeScriptExtractor().extract(
                        str(tmp_path),
                        helper_cache_dir=helper_cache,
                    )

        assert inv["app.ts"]["language"] == "typescript"
        assert seen["src_dir"] == str(tmp_path)
        assert seen["cache_dir"] == helper_cache

    def test_normalization_filters_checkout_helper_but_not_unrelated_suffix(
        self, tmp_path
    ):
        _write_owned_package_sentinels(tmp_path)
        bundled = "src/llm_wiki_cli/extractors/ts_scripts/extract.js"
        unrelated = "vendor/llm_wiki_cli/extractors/ts_scripts/extract.js"
        _make_ts(tmp_path, bundled, "export function extract() {}\n")
        _make_ts(tmp_path, unrelated, "export function consumer() {}\n")
        inventory = {
            bundled: {"classes": [], "functions": []},
            unrelated: {"classes": [], "functions": []},
        }

        normalized = TypeScriptExtractor()._normalize_inventory(
            str(tmp_path),
            inventory,
            BUNDLED_TS_SCRIPTS,
        )

        assert list(normalized) == [unrelated]

    def test_relative_external_helper_suffix_fails_open_across_both_filter_stages(
        self, tmp_path, monkeypatch
    ):
        external_root = tmp_path / "external-consumer"
        relative_path = "src/llm_wiki_cli/extractors/ts_scripts/extract.js"
        _make_ts(external_root, relative_path, "export function consumer() {}\n")
        monkeypatch.chdir(Path(__file__).parents[1])
        result = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout=json.dumps(
                {relative_path: {"classes": [], "functions": []}}
            ),
            stderr="",
        )
        extractor = TypeScriptExtractor()

        loaded = extractor._load_inventory(result)
        normalized = extractor._normalize_inventory(
            str(external_root), loaded, BUNDLED_TS_SCRIPTS
        )

        assert list(loaded) == [relative_path]
        assert list(normalized) == [relative_path]

    def test_windows_style_inventory_keys_are_normalized(self, tmp_path):
        _make_ts(tmp_path, "web/src/app.ts", "export class App {}")
        result = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout='{"web\\\\src\\\\app.ts": {"classes": [], "functions": []}}',
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=BUNDLED_TS_SCRIPTS,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run",
                    return_value=result,
                ):
                    inv = TypeScriptExtractor().extract(str(tmp_path))

        assert "web/src/app.ts" in inv
        assert "web\\src\\app.ts" not in inv
        assert inv["web/src/app.ts"]["language"] == "typescript"

    def test_malformed_json_returns_empty(self, tmp_path, capsys):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        result = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout="{not-json",
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=BUNDLED_TS_SCRIPTS,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run",
                    return_value=result,
                ):
                    inv = TypeScriptExtractor().extract(str(tmp_path))

        assert inv == {}
        assert "malformed JSON" in capsys.readouterr().err

    def test_timeout_returns_empty_and_names_configuration(
        self, tmp_path, capsys, monkeypatch
    ):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        monkeypatch.setenv("LLM_WIKI_EXTRACTOR_TIMEOUT", "37")
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=BUNDLED_TS_SCRIPTS,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(["node"], 37),
                ) as mock_run:
                    extractor = TypeScriptExtractor()
                    inv = extractor.extract(str(tmp_path))

        assert inv == {}
        assert mock_run.call_args.kwargs["timeout"] == 37
        assert extractor.last_error is not None
        assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in extractor.last_error
        assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in capsys.readouterr().err


# ===========================================================================
# Integration: both .py and .ts files in same directory
# ===========================================================================


@skip_no_node
class TestExtractorRegistryIntegration:
    def test_extract_command_merges_both_languages(self, tmp_path):
        """Running all registered extractors on a mixed dir returns both languages."""
        from llm_wiki_cli.commands.extract_cmd import _load_extractor
        from llm_wiki_cli.config import EXTRACTOR_REGISTRY

        (tmp_path / "models.py").write_text(
            textwrap.dedent("class PythonModel:\n    pass\n"), encoding="utf-8"
        )
        _make_ts(tmp_path, "models.ts", "export class TypeScriptModel {}")

        inventory: dict = {}
        for _lang, entry_point in EXTRACTOR_REGISTRY.items():
            extractor = _load_extractor(entry_point)
            inventory.update(extractor.extract(str(tmp_path)))

        languages = {entry["language"] for entry in inventory.values()}
        assert "python" in languages
        assert "typescript" in languages

    def test_typescript_entry_in_registry(self):
        from llm_wiki_cli.config import EXTRACTOR_REGISTRY

        assert "typescript" in EXTRACTOR_REGISTRY
        assert "TypeScriptExtractor" in EXTRACTOR_REGISTRY["typescript"]


# ===========================================================================
# Tests for gap/bug fixes
# ===========================================================================


@skip_no_node
class TestTypeScriptExtractorFixes:
    """Tests specifically validating the gap-analysis bug fixes."""

    def test_interface_bases_external_type(self, tmp_path):
        """getExtends() must report bases even when the type is from an unresolved
        external module (getBaseDeclarations() would silently return [] here)."""
        _make_ts(
            tmp_path,
            "emitter.ts",
            """
            import { EventEmitter } from 'events';
            export interface MyEmitter extends EventEmitter {
                onData: () => void;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        iface = next((c for c in classes if c["name"] == "MyEmitter"), None)
        assert iface is not None
        assert "EventEmitter" in iface["bases"]

    def test_module_docstring_captured(self, tmp_path):
        """deep mode must capture a module-level /** ... */ comment."""
        _make_ts(
            tmp_path,
            "utils.ts",
            """
            /** @module utils - Utility helpers for the project. */
            export function add(a: number, b: number): number {
                return a + b;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        assert "module_docstring" in data
        assert (
            "utils" in data["module_docstring"].lower()
            or "utility" in data["module_docstring"].lower()
        )

    def test_anonymous_class_disambiguated(self, tmp_path):
        """An anonymous class (export default class {}) gets a line-disambiguated name
        instead of the bare '<anonymous>' that would collide across files."""
        _make_ts(
            tmp_path,
            "handler.ts",
            """
            /** Default handler */
            export default class {
                run() {}
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        assert len(classes) == 1
        name = classes[0]["name"]
        # Must not be the bare '<anonymous>' that caused collisions;
        # must contain the line number for disambiguation.
        assert name.startswith("<anonymous_L"), (
            f"Expected disambiguated name, got: {name!r}"
        )

    def test_dts_files_included(self, tmp_path):
        """First-party declaration files (.d.ts) appear in the inventory."""
        (tmp_path / "types.d.ts").write_text(
            "export declare class Phantom {}\n", encoding="utf-8"
        )
        _make_ts(tmp_path, "real.ts", "export class Real {}")
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert "types.d.ts" in inv
        assert "real.ts" in inv
        dts_classes = [c["name"] for c in inv["types.d.ts"]["classes"]]
        assert "Phantom" in dts_classes

    def test_shallow_module_only_javascript_file_is_retained(self, tmp_path):
        _make_ts(
            tmp_path,
            "docker/proxy.js",
            """
            const http = require("node:http");
            const listenPort = Number.parseInt(process.env.PORT || "3000", 10);
            const server = http.createServer((req, res) => {
              res.end("ok");
            });
            server.listen(listenPort);
            """,
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=False)

        assert sorted(inv) == ["docker/proxy.js"]
        data = inv["docker/proxy.js"]
        assert data["language"] == "javascript"
        assert data["classes"] == []
        assert data["functions"] == []
        assert [constant["name"] for constant in data["constants"]] == [
            "http",
            "listenPort",
            "server",
        ]
        assert [call["name"] for call in data["module_calls"]] == [
            "require",
            "parseInt",
            "createServer",
            "listen",
        ]

    def test_tsconfig_walk_up(self, tmp_path):
        """tsconfig.json one level above srcDir must be discovered automatically."""
        # Write a minimal tsconfig at the parent level.
        tsconfig = {"compilerOptions": {"strict": True}}
        import json as _json

        (tmp_path / "tsconfig.json").write_bytes(_json.dumps(tsconfig).encode("utf-8"))
        src = tmp_path / "src"
        src.mkdir()
        _make_ts(src, "app.ts", "export class App {}")
        # Extract from src/ — tsconfig is at tmp_path/tsconfig.json (one level up).
        inv = TypeScriptExtractor().extract(str(src))
        assert len(inv) == 1
        assert list(inv.values())[0]["classes"][0]["name"] == "App"

    def test_inventory_keys_are_relative(self, tmp_path):
        """Inventory keys must match Python/Go/Rust by being srcDir-relative."""
        nested = tmp_path / "web" / "src"
        nested.mkdir(parents=True)
        _make_ts(nested, "app.ts", "export class App {}")

        inv = TypeScriptExtractor().extract(str(tmp_path))

        assert "web/src/app.ts" in inv
        assert all(not Path(key).is_absolute() for key in inv)

    def test_stderr_forwarded_on_success(self, tmp_path, capsys):
        """Warnings written to Node.js stderr must reach Python sys.stderr."""
        from unittest.mock import patch, MagicMock

        _make_ts(tmp_path, "file.ts", "export class File {}")

        # Simulate a successful Node.js run that also emits a warning on stderr.
        fake_result = MagicMock()
        fake_result.stdout = '{"file.ts": {"classes": [], "functions": []}}'
        fake_result.stderr = "Warning: could not resolve some types\n"

        with patch("subprocess.run", return_value=fake_result):
            TypeScriptExtractor().extract(str(tmp_path))

        err = capsys.readouterr().err
        assert "Warning" in err

    def test_file_named_like_excluded_dir(self, tmp_path):
        """A file named dist.ts inside a valid directory must NOT be excluded."""
        _make_ts(tmp_path, "dist.ts", "export class Dist {}")
        _make_ts(tmp_path, "build.ts", "export class Build {}")
        inv = TypeScriptExtractor().extract(str(tmp_path))
        all_names = [c["name"] for entry in inv.values() for c in entry["classes"]]
        assert "Dist" in all_names
        assert "Build" in all_names

    def test_deep_includes_entrypoint_setup_module(self, tmp_path):
        _make_ts(
            tmp_path,
            "main.tsx",
            """
            import React from 'react';
            import ReactDOM from 'react-dom/client';
            import App from './App';

            const queryClient = new QueryClient();
            ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
            """,
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        data = inv["main.tsx"]
        assert data["classes"] == []
        assert data["functions"] == []
        assert {imp["module"] for imp in data["imports"]} >= {
            "react",
            "react-dom/client",
            "./App",
        }
        assert data["constants"] == [
            {"name": "queryClient", "line": 6, "exported": False}
        ]
        assert [call["name"] for call in data["module_calls"]] == [
            "QueryClient",
            "render",
        ]

    def test_deep_includes_service_client_setup_module(self, tmp_path):
        _make_ts(
            tmp_path,
            "api.ts",
            """
            import axios, { AxiosInstance } from 'axios';

            const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const api: AxiosInstance = axios.create({ baseURL: `${BASE_URL}/api/v1` });

            api.interceptors.request.use((config) => config);

            export default api;
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)["api.ts"]

        assert data["exports"] == ["default"]
        constants = {constant["name"]: constant for constant in data["constants"]}
        assert constants["BASE_URL"]["exported"] is False
        assert constants["api"]["line"] == 5
        assert [call["name"] for call in data["module_calls"]] == ["create", "use"]

    def test_deep_includes_exported_query_client_constant(self, tmp_path):
        _make_ts(
            tmp_path,
            "queryClient.ts",
            """
            import { QueryClient } from '@tanstack/react-query';

            export const queryClient = new QueryClient({
              defaultOptions: { queries: { retry: 1 } },
            });
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)["queryClient.ts"]

        assert data["exports"] == ["queryClient"]
        assert data["constants"] == [
            {"name": "queryClient", "line": 4, "exported": True}
        ]
        assert data["module_calls"] == [
            {"name": "QueryClient", "target": "queryClient", "line": 4}
        ]

    def test_commonjs_default_assignment_surfaces_top_level_function(self, tmp_path):
        _make_ts(
            tmp_path,
            "SimpleRegister.tsx",
            """
            Object.defineProperty(exports, "__esModule", { value: true });
            exports.default = SimpleRegister;

            function SimpleRegister() {
              return null;
            }
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)[
            "SimpleRegister.tsx"
        ]

        assert data["exports"] == ["default"]
        assert [fn["name"] for fn in data["functions"]] == ["SimpleRegister"]

    def test_plain_js_commonjs_service_surfaces_top_level_functions(self, tmp_path):
        _make_ts(
            tmp_path,
            "docker/web-auth-proxy.js",
            """\
            const http = require("node:http");

            function isTruthy(value) {
              return Boolean(value);
            }

            function withAuthHeaders(headers = {}) {
              return { ...headers, authorization: "Bearer token" };
            }

            function rewriteJsonPayload(req, payload) {
              return payload;
            }

            const server = http.createServer((req, res) => {
              res.end(rewriteJsonPayload(req, {}));
            });
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)[
            "docker/web-auth-proxy.js"
        ]

        assert data["language"] == "javascript"
        assert [fn["name"] for fn in data["functions"]] == [
            "isTruthy",
            "withAuthHeaders",
            "rewriteJsonPayload",
        ]
        by_name = {fn["name"]: fn for fn in data["functions"]}
        assert by_name["isTruthy"]["line"] == 3
        assert by_name["isTruthy"]["kind"] == "function"
        assert by_name["isTruthy"]["end_line"] == 5
        assert by_name["withAuthHeaders"]["params"] == [
            {"name": "headers", "type": "", "default": "{}"}
        ]
        assert {"name": "createServer", "target": "server", "line": 15} in data[
            "module_calls"
        ]

    def test_plain_js_create_server_named_handler_records_argument(self, tmp_path):
        _make_ts(
            tmp_path,
            "server.js",
            """\
            const http = require("node:http");

            function handleRequest(req, res) {
              res.end("ok");
            }

            const server = http.createServer(handleRequest);
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)["server.js"]

        assert {
            "name": "createServer",
            "target": "server",
            "line": 7,
            "args": ["handleRequest"],
        } in data["module_calls"]

    def test_non_exported_typescript_family_functions_stay_private(self, tmp_path):
        _make_ts(
            tmp_path,
            "hidden.ts",
            """\
            export const visible = 1;
            function privateTs() {
              return visible;
            }
            """,
        )
        _make_ts(
            tmp_path,
            "Hidden.tsx",
            """\
            export function PublicTsx() {
              return null;
            }
            function privateTsx() {
              return null;
            }
            """,
        )
        _make_ts(
            tmp_path,
            "Hidden.jsx",
            """\
            export default function PublicJsx() {
              return null;
            }
            function privateJsx() {
              return null;
            }
            """,
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert [fn["name"] for fn in inv["hidden.ts"]["functions"]] == []
        assert [fn["name"] for fn in inv["Hidden.tsx"]["functions"]] == ["PublicTsx"]
        assert [fn["name"] for fn in inv["Hidden.jsx"]["functions"]] == ["PublicJsx"]

    def test_empty_typescript_file_reports_deep_skip_diagnostic(self, tmp_path, capsys):
        _make_ts(tmp_path, "empty.ts", "// comments only\n")

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert inv == {}
        err = capsys.readouterr().err
        assert "skipped empty.ts" in err
        assert "no documentable TypeScript declarations" in err
