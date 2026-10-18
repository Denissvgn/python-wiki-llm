"""Installed recovery routes preserve bindings, read scope and writer authority."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
from types import SimpleNamespace

from markdown_it import MarkdownIt
import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import init_cmd, upgrade_cmd, query_cmd, extract_cmd, sync_cmd, lint_cmd, ci_check_cmd
from llm_wiki_cli.services import extractor_helpers, knowledge_evidence
from llm_wiki_cli.services.schema import SCHEMA_FILENAMES, pin_source_selection_command_recipes
from llm_wiki_cli.services.skills import skills_install_dir


def _instructions(agent, no_skills):
    text = Path(SCHEMA_FILENAMES[agent]).read_text(encoding='utf-8')
    if not no_skills:
        text += '\n' + (skills_install_dir(agent) / 'wiki-reference/references/maintenance.md').read_text(encoding='utf-8')
    return text


def _recipes(text):
    snippets = []
    for token in MarkdownIt().parse(text):
        if token.type == 'fence':
            snippets.extend(line.strip() for line in token.content.splitlines())
        elif token.type == 'inline':
            snippets.extend(child.content for child in token.children or () if child.type == 'code_inline')
    return [shlex.split(s) for s in snippets if s.startswith('llm-wiki ')]


def _diagnostic_recipes(text):
    commands = _recipes(text)
    query = next(c for c in commands if c[1] == 'query' and '--src-dir' in c and '--wiki-dir' in c)
    raw = next(c for c in commands if c[1] == 'extract' and '--paths' in c and '--deep' in c and '--read-only' in c)
    preview = next(c for c in commands if c[1] == 'sync' and '--dry-run' in c)
    return query, raw, preview


def _files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('agent', ['claude', 'cursor', 'copilot', 'aider', 'opencode', 'generic'])
@pytest.mark.parametrize('no_skills', [False, True], ids=['skills', 'inline'])
def test_installed_recovery_recipes_work_after_init_and_upgrade(tmp_path, monkeypatch, capsys, agent, no_skills):
    from llm_wiki_cli.commands import bootstrap_cmd
    monkeypatch.chdir(tmp_path)
    wiki = "knowledge/team's wiki"
    selection = "profiles/team's sources.json"
    helper_cache = str(tmp_path / "helper cache")
    Path('src').mkdir()
    Path('src/app.py').write_text('raise RuntimeError("do not execute target")\nclass Order:\n    value: int\n')
    Path(selection).parent.mkdir()
    Path(selection).write_text(json.dumps({'schema_version': 'llm-wiki-source-selection/v1', 'include': ['src'], 'exclude': []}))
    schema = Path(SCHEMA_FILENAMES[agent])
    schema.parent.mkdir(parents=True, exist_ok=True)
    user_text = b'# User policy: preserve this verbatim.\r\n\r\n'
    schema.write_bytes(user_text)
    parser = cli._build_parser()
    init_cmd.run(SimpleNamespace(agent=agent, wiki_dir=wiki, no_skills=no_skills, source_selection=selection))
    # Captured-evidence diagnosis applies to an established wiki, not the
    # untouched scaffold. Ordinary first use is separately authorized here.
    bootstrap_cmd.run(parser.parse_args(['bootstrap', '--src-dir', '.', '--wiki-dir', wiki,
        '--source-selection', selection, '--source-adapter', '--skip-workflows', '--skip-flows']))
    capsys.readouterr()
    for stage in ('init', 'upgrade'):
        if stage == 'upgrade':
            upgrade_cmd.run(SimpleNamespace(agent=None, wiki_dir=wiki))
            capsys.readouterr()
        assert schema.read_bytes().startswith(user_text)
        if no_skills:
            assert not (skills_install_dir(agent) / 'wiki-reference').exists()
        text = _instructions(agent, no_skills)
        query, raw, preview = _diagnostic_recipes(text)
        assert '"operation":"explain"' in text
        # Apply the documented original binding to generic reference examples;
        # generated fallback recipes already carry the configured wiki/selection.
        for argv in (query, raw, preview):
            if '--wiki-dir' in argv:
                argv[argv.index('--wiki-dir') + 1] = wiki
            if '--source-selection' not in argv:
                argv += ['--source-selection', selection]
            argv += ['--helper-cache-dir', helper_cache]
            args = parser.parse_args(argv[1:])
            assert args.src_dir == '.' and args.source_selection == selection
            assert args.helper_cache_dir == helper_cache
            if argv[1] != 'extract':
                assert args.wiki_dir == wiki
            assert '--force' not in argv and '--knowledge-format' not in argv
        # Raw extraction has no wiki argument; it retains the same source scope.
        assert '--wiki-dir' not in raw
        raw[raw.index('--paths') + 1] = 'src/app.py'
        request = Path('evidence.json')
        request.write_text(json.dumps({'operation': 'explain', 'source': 'src/app.py', 'limit': 5}))
        query[query.index('--request') + 1] = str(request)
        before = _files(tmp_path)
        query_cmd.run(parser.parse_args(query[1:]))
        explanation = json.loads(capsys.readouterr().out)
        assert not explanation['cost']['full_inventory_performed']
        assert explanation['knowledge']['availability'] == 'ready'
        assert explanation['ambiguous'] and not explanation['found']
        extract_cmd.run(parser.parse_args(raw[1:]))
        payload = json.loads(capsys.readouterr().out)
        assert set(payload['inventory']) == {'src/app.py'}
        assert _files(tmp_path) == before


def test_bootstrap_refresh_pins_new_query_recipes_without_changing_explicit_bindings():
    selection = "profiles/team's sources.json"
    original = 'Use `llm-wiki query --request evidence.json --src-dir . --wiki-dir wiki`.'
    pinned = pin_source_selection_command_recipes(original, selection)
    argv = _recipes(pinned)[0]
    assert cli._build_parser().parse_args(argv[1:]).source_selection == selection
    assert pin_source_selection_command_recipes(pinned, selection) == pinned
    explicit = original.replace('--src-dir .', '--source-selection other.json --src-dir .')
    assert pin_source_selection_command_recipes(explicit, selection) == explicit
    language = '`llm-wiki prepare-extractors --language typescript --cache-dir "helper cache"`'
    assert pin_source_selection_command_recipes(language, selection) == language
    generic = '`llm-wiki prepare-extractors --src-dir .`'
    assert cli._build_parser().parse_args(_recipes(pin_source_selection_command_recipes(generic, selection))[0][1:]).source_selection == selection
    literal_value = '`llm-wiki query --request FILE --wiki-dir "notes --source-selection archive"`'
    args = cli._build_parser().parse_args(_recipes(pin_source_selection_command_recipes(literal_value, selection))[0][1:])
    assert args.wiki_dir == 'notes --source-selection archive' and args.source_selection == selection


def test_missing_helper_preparation_plan_retains_original_cache_and_does_not_prepare(tmp_path, monkeypatch, capsys):
    from llm_wiki_cli.commands import prepare_extractors_cmd
    monkeypatch.chdir(tmp_path)
    Path('src').mkdir()
    Path('src/app.ts').write_text('export class Order {}\n')
    cache = str(tmp_path / 'helper cache')
    argv = extractor_helpers.helper_preparation_argv('typescript', 'src', cache)
    args = cli._build_parser().parse_args([*argv[1:], '--plan', '--format', 'json'])
    assert args.cache_dir == cache and args.source_selection is None
    before = _files(tmp_path)
    prepare_extractors_cmd.run(args)
    plan = json.loads(capsys.readouterr().out)
    assert plan['languages'] == ['typescript']
    assert _files(tmp_path) == before


def test_inline_recipe_reads_do_not_repair_captured_evidence_but_owning_writer_does(tmp_path, monkeypatch, capsys):
    from llm_wiki_cli.commands import bootstrap_cmd
    monkeypatch.chdir(tmp_path)
    Path('src').mkdir()
    Path('src/app.py').write_text('class Order:\n    value: int\n')
    selection = 'scope.json'
    Path(selection).write_text(json.dumps({'schema_version': 'llm-wiki-source-selection/v1', 'include': ['src'], 'exclude': []}))
    wiki = 'knowledge'
    init_cmd.run(SimpleNamespace(agent='generic', wiki_dir=wiki, no_skills=True, source_selection=selection))
    parser = cli._build_parser()
    with monkeypatch.context() as patch:
        def reject(*args):
            raise knowledge_evidence._InventoryNormalizationError('invalid-inventory-shape')
        patch.setattr(knowledge_evidence, '_normalize_module_observation', reject)
        bootstrap_cmd.run(parser.parse_args(['bootstrap', '--src-dir', '.', '--wiki-dir', wiki,
            '--source-selection', selection, '--source-adapter', '--skip-workflows', '--skip-flows']))
    capsys.readouterr()
    query, raw, preview = _diagnostic_recipes(_instructions('generic', True))
    request = Path('evidence.json')
    request.write_text(json.dumps({'operation': 'explain', 'value': 'llm-wiki://modules/app'}))
    query[query.index('--request') + 1] = str(request)
    assert '--wiki-dir' not in raw
    raw[raw.index('--paths') + 1] = 'src/app.py'
    before_read = _files(Path(wiki)), _files(Path('src'))
    query_cmd.run(parser.parse_args(query[1:]))
    captured = json.loads(capsys.readouterr().out)
    assert captured['concept']['evidence'] == 'unknown'
    extract_cmd.run(parser.parse_args(raw[1:]))
    fresh = json.loads(capsys.readouterr().out)['inventory']['src/app.py']
    assert knowledge_evidence.normalize_module_observation(fresh) is not None
    query_cmd.run(parser.parse_args(query[1:]))
    assert json.loads(capsys.readouterr().out)['concept']['evidence'] == 'unknown'
    assert (_files(Path(wiki)), _files(Path('src'))) == before_read
    sync_cmd.run(parser.parse_args(preview[1:]))
    capsys.readouterr()
    assert (_files(Path(wiki)), _files(Path('src'))) == before_read
    # The caller authorizes ordinary repair in this temporary consumer.
    apply = [arg for arg in preview if arg != '--dry-run']
    sync_cmd.run(parser.parse_args(apply[1:]))
    capsys.readouterr()
    query_cmd.run(parser.parse_args(query[1:]))
    assert json.loads(capsys.readouterr().out)['concept']['evidence'] == 'present'
    source = _files(Path('src'))
    for command, argv in ((lint_cmd, ['lint', '--strict', '--profile']),
                          (ci_check_cmd, ['ci-check', '--format', 'json', '--no-report'])):
        command.run(parser.parse_args([*argv, '--src-dir', '.', '--wiki-dir', wiki, '--source-selection', selection]))
        assert json.loads(capsys.readouterr().out)['ok']
    assert _files(Path('src')) == source
