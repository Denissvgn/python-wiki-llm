"""Rejection coordinates are fresh, bounded and independent of semantic hashes."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import jsonschema
import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.normalization_diagnostics import (
    DIAGNOSTIC_PREFIX, DIAGNOSTIC_SCHEMA, MAX_DIAGNOSTIC_BYTES, NormalizationDiagnostic,
)
from tests.test_captured_evidence_diagnostics import _view
from tests.test_knowledge_evidence import _inventory, _module_basis, _entity_basis
from tests.test_knowledge_freshness import MODULE_LOCATOR
from tests.test_knowledge_lint import _report_for_view


SCHEMA = json.loads((Path(__file__).parents[1] / 'src/llm_wiki_cli/schemas/llm-wiki-normalization-diagnostic-v1.schema.json').read_text())


def detail(basis):
    assert not basis.is_known
    assert basis.normalization_diagnostic is not None
    payload = basis.normalization_diagnostic.to_payload()
    jsonschema.Draft202012Validator(SCHEMA).validate(payload)
    assert len(basis.normalization_diagnostic.render().encode()) <= MAX_DIAGNOSTIC_BYTES
    assert payload['basis'] == 'fresh-normalization'
    assert payload['source_path'] == 'src/accounts.py'
    assert payload['extractor_ref'] == 'python-ast'
    return payload


@pytest.mark.parametrize(('mutate', 'pointer', 'rule', 'actual'), [
    (lambda d: d.update(imports=[{'module': ''}]), '/imports/0/module', 'import-module', 'string'),
    (lambda d: d.update(imports=[{'module': 'valid'}, {'module': 0}]), '/imports/1/module', 'import-module', 'integer'),
    (lambda d: d.update(imports=[[{'module': 'nested'}]]), '/imports/0', 'object-required', 'array'),
    (lambda d: d.update(imports={'module': 'wrong'}), '/imports', 'array-required', 'object'),
    (lambda d: d.pop('classes'), '/classes', 'required-field', 'missing'),
    (lambda d: d.update(module=' '), '/module', 'nonempty-text', 'string'),
    (lambda d: d.update(language='sql'), '/language', 'supported-language', 'string'),
    (lambda d: d['functions'][0].update(is_async=0), '/functions/0/is_async', 'boolean-required', 'integer'),
    (lambda d: d['classes'][0].update(bases=[True]), '/classes/0/bases/0', 'string-required', 'boolean'),
])
def test_malformed_module_identifies_record_and_rule(mutate, pointer, rule, actual):
    data = _inventory('python')
    mutate(data)
    result = detail(_module_basis(data))
    assert result['pointer'] == pointer and result['pointer_exact']
    assert result['rule'] == rule and result['actual']['type'] == actual
    assert result['scope'] == 'module'
    assert result['reason'] == ('unsupported-language' if rule == 'supported-language' else 'invalid-inventory-shape')


def test_second_same_name_occurrence_keeps_actual_inventory_index():
    data = _inventory('python')
    data['classes'] = [data['classes'][0], deepcopy(data['classes'][0])]
    data['classes'][1]['methods'][0]['params'] = [{'name': None}]
    assert _entity_basis(data, 'User', 1).is_known
    result = detail(_entity_basis(data, 'User', 2))
    assert result['pointer'] == '/classes/1/methods/0/params/0/name'
    assert result['entity_name'] == 'User' and result['occurrence'] == 2
    assert result['rule'] == 'string-required' and result['actual']['type'] == 'null'


def test_missing_occurrence_does_not_invent_a_class_index():
    result = detail(_entity_basis(_inventory('python'), 'User', 3))
    assert result['pointer'] == '/classes' and result['rule'] == 'entity-occurrence'
    assert result['reason'] == 'entity-occurrence-not-found' and result['occurrence'] == 3


@pytest.mark.parametrize('kind', ['dynamic-import', 'require'])
def test_explicit_unresolved_gaps_stay_valid_but_near_misses_locate_the_failure(kind):
    data = {'language': 'javascript', 'classes': [], 'functions': [], 'imports': [{
        'module': '', 'name': '', 'type': kind, 'resolution': 'unresolved',
        'reason': 'dynamic-import' if kind == 'dynamic-import' else 'dynamic-require', 'line': 1,
    }]}
    valid = _module_basis(data)
    assert valid.is_known and valid.normalization_diagnostic is None
    del data['imports'][0]['reason']
    result = detail(_module_basis(data))
    assert result['pointer'] == '/imports/0/reason' and result['rule'] == 'explicit-import-gap'
    assert result['actual']['type'] == 'missing'
    data['imports'][0]['reason'] = 'dynamic-import' if kind == 'dynamic-import' else 'dynamic-require'
    data['imports'][0]['line'] = True
    assert detail(_module_basis(data))['pointer'] == '/imports/0/line'


@pytest.mark.parametrize('value', [float('nan'), float('inf'), object()])
def test_nested_json_values_have_a_bounded_pointer(value):
    data = _inventory('python')
    data['classes'][0]['attributes'][0]['examples'] = [[value]]
    result = detail(_entity_basis(data, 'User'))
    assert result['pointer'] == '/classes/0/attributes/0/examples/0/0'
    assert result['rule'] == 'finite-json-value'


def test_secret_values_and_arbitrary_keys_are_not_rendered_or_represented():
    class Secret:
        def __repr__(self):
            pytest.fail('arbitrary repr must never execute')
    data = _inventory('python')
    data['classes'][0]['attributes'][0]['constraints'] = {'API_TOKEN_SECRET': Secret()}
    basis = _entity_basis(data, 'User')
    result = detail(basis)
    assert result['pointer'] == '/classes/0/attributes/0/constraints'
    assert not result['pointer_exact']
    assert basis.normalization_diagnostic is not None
    assert 'API_TOKEN_SECRET' not in basis.normalization_diagnostic.render()
    data['classes'][0]['methods'][0]['is_async'] = 'HOST_PASSWORD_SECRET' * 100000
    result = detail(_entity_basis(data, 'User'))
    assert result['actual']['summary'] == '2000000 characters; value redacted'
    assert 'HOST_PASSWORD_SECRET' not in json.dumps(result)


def test_cycles_and_depth_overflow_never_fabricate_exact_details():
    data = _inventory('python')
    cycle = []
    cycle.append(cycle)
    data['classes'][0]['attributes'][0]['examples'] = cycle
    result = detail(_entity_basis(data, 'User'))
    assert result['rule'] == 'acyclic-json'
    nested = []
    current = nested
    for _ in range(2000):
        child = []
        current.append(child)
        current = child
    data['classes'][0]['attributes'][0]['examples'] = nested
    result = detail(_entity_basis(data, 'User'))
    assert result['pointer'] is None and not result['pointer_exact']
    assert result['rule'] == 'structural-json-encoding' and result['actual']['type'] == 'unavailable'


def test_multibyte_coordinate_bounds_are_explicit_and_valid_json():
    d = NormalizationDiagnostic.rejection('invalid-inventory-shape', '/' + '😃' * 1000, 'string-required', 'string', None)
    d = d.at_source('😃' * 1000, 'entity', '😃' * 1000, '😃' * 1000, 10 ** 10000)
    payload = d.to_payload()
    jsonschema.Draft202012Validator(SCHEMA).validate(payload)
    assert len(d.render().encode()) <= MAX_DIAGNOSTIC_BYTES
    assert not payload['pointer_exact'] and payload['occurrence'] is None
    assert {'pointer', 'source_path', 'extractor_ref', 'entity_name', 'occurrence'} <= set(payload['truncated_fields'])
    assert d.render() == d.render()


@pytest.mark.parametrize('surface', ['service', 'api', 'mcp', 'lint', 'cli-text', 'cli-json', 'ci-v1', 'ci-v2', 'ci-v3', 'ci-v4'])
def test_fresh_detail_survives_existing_outer_contracts_without_persisting(tmp_path, monkeypatch, capsys, surface):
    view, concept = _view(tmp_path, 'invalid-inventory-shape')
    assert view.freshness is not None
    bad = _inventory('python')
    bad['imports'] = [{'module': ''}]
    fresh = _module_basis(bad)
    diagnostic = fresh.normalization_diagnostic
    assert diagnostic is not None
    original = view.freshness.by_locator[concept.locator]
    assert original.live_basis is not None
    diagnostic = diagnostic.at_source(original.live_basis.source_path, original.live_basis.scope.value, original.live_basis.extractor_ref)
    current = replace(original, live_basis=replace(original.live_basis, normalization_diagnostic=diagnostic))
    view = replace(view, freshness=replace(view.freshness, by_locator={
        **view.freshness.by_locator, concept.locator: current,
    }))
    if surface in {'lint', 'cli-text', 'cli-json', 'ci-v1', 'ci-v2', 'ci-v3', 'ci-v4'}:
        report = _report_for_view(view)
        report.knowledge_enabled = True
        report.knowledge_view = view
        issue = next(i for i in report.issues if i.target == MODULE_LOCATOR)
        assert not report.passed and issue.reason_code == 'promised-evidence-unknown' and issue.severity == 'error'
        text = issue.message
        if surface != 'lint':
            from llm_wiki_cli import cli
            from llm_wiki_cli.commands import lint_cmd, ci_check_cmd
            from llm_wiki_cli.services import ci_report, metrics
            monkeypatch.chdir(tmp_path)
            (tmp_path / 'src').mkdir()
            (tmp_path / 'wiki').mkdir()
            monkeypatch.setattr(metrics, 'record_validation_event', lambda **kw: None)
            if surface in {'ci-v3', 'ci-v4'}:
                from llm_wiki_cli.services import health_details
                if surface == 'ci-v3':
                    # Explicit historical exact-comparison fixture; the native
                    # current default is independently exercised by ci-v4.
                    monkeypatch.setattr(health_details.ac, 'selected_policy', lambda *args, **kwargs: 'exact-v1')
                report.health_details = health_details.capture_health_details(
                    view, wiki_dir='wiki', src_dir='src',
                )
            command = ci_check_cmd if surface.startswith('ci-') else lint_cmd
            monkeypatch.setattr(command, 'build_report', lambda *a, **kw: report)
            monkeypatch.setattr(ci_check_cmd, 'record_validation_event', lambda **kw: None)
            before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
            args = ['ci-check' if surface.startswith('ci-') else 'lint', '--src-dir', 'src', '--wiki-dir', 'wiki', '--no-cache']
            if surface.startswith('ci-'):
                args += ['--no-report', '--format', 'json', '--report-schema', surface[3:]]
            else:
                args += ['--strict', *(['--profile'] if surface == 'cli-json' else [])]
            with pytest.raises(SystemExit) as stopped:
                command.run(cli._build_parser().parse_args(args))
            assert stopped.value.code == 1
            output = capsys.readouterr().out
            if surface == 'cli-text':
                text = output
            else:
                payload = json.loads(output)
                if surface.startswith('ci-'):
                    ci_report.validate_ci_check_payload(payload, cli_exit=1)
                    assert payload['schema_version'] == 'llm-wiki-ci-check/' + surface[3:]
                text = next(i['message'] for i in payload['issues'] if i['target'] == MODULE_LOCATOR)
                # Existing report decoders also accept historical text with no marker.
                if surface.startswith('ci-'):
                    legacy = deepcopy(payload)
                    for record in legacy['issues']:
                        record['message'] = 'Historical reason-only rejection'
                    ci_report.validate_ci_check_payload(legacy, cli_exit=1)
            assert before == {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    else:
        service = DocumentationGraphQueryService({}, knowledge_view=view)
        if surface == 'api':
            result = api.explain_evidence(MODULE_LOCATOR, service=service)
        elif surface == 'mcp':
            from llm_wiki_cli.services import mcp_server
            monkeypatch.chdir(tmp_path)
            monkeypatch.setattr(mcp_server, 'build_documentation_query_service', lambda *a, **kw: service)
            result = mcp_server.McpWikiService(src_dir='.', wiki_dir='.').explain_evidence(MODULE_LOCATOR)
        else:
            result = service.explain_evidence(MODULE_LOCATOR)
        assert result['evidence'] is not None
        freshness = result['evidence']['freshness']
        assert set(freshness) == {'state', 'reason', 'description', 'live_comparison_performed', 'recorded_basis', 'live_basis', 'hint'}
        assert 'normalization_diagnostic' not in freshness['live_basis']
        assert freshness['state'] == 'unknown'
        text = freshness['description']
        assert result['bounds']['raw_evidence_bytes']['returned'] == len(json.dumps(result['evidence'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
    payload, _ = json.JSONDecoder().raw_decode(text.split(DIAGNOSTIC_PREFIX, 1)[1])
    assert payload['schema_version'] == DIAGNOSTIC_SCHEMA and payload['pointer'] == '/imports/0/module'
    assert 'Historical rejected-record details were not captured' in text
    assert 'normalization_diagnostic' not in fresh.to_evidence_payload()


def test_old_reason_only_failure_does_not_gain_a_synthetic_pointer(tmp_path):
    from llm_wiki_cli.services.evidence_diagnostics import captured_evidence_diagnostic
    view, concept = _view(tmp_path, 'invalid-inventory-shape')
    diagnosis = captured_evidence_diagnostic(view, concept)
    assert diagnosis is not None
    text, _ = diagnosis
    assert DIAGNOSTIC_PREFIX not in text
    assert 'Fresh rejected-record details were not captured' in text


def test_runtime_basis_and_freshness_transport_detail_without_persisting_it(tmp_path):
    from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
    from llm_wiki_cli.services.knowledge_orchestration import _runtime_live_concept_bases
    from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
    from llm_wiki_cli.services.sync_manifest import ManifestEvidenceBaseline
    from tests.test_knowledge_lint import _loaded_knowledge
    from tests.test_knowledge_freshness import _live_evaluation

    loaded, knowledge = _loaded_knowledge(tmp_path)
    assert loaded.manifest_basis is not None
    live = _live_evaluation(knowledge)
    previous = live.concept_bases[MODULE_LOCATOR]
    data = _inventory('python')
    data['imports'] = [{'module': ''}]
    bases = _runtime_live_concept_bases(
        knowledge, loaded.manifest_basis, {previous.source_path: data},
        {previous.source_path: previous.source_content_hash},
        {previous.source_path: previous.extractor_ref},
        infrastructure_bases_by_source={}, inventory_complete=True,
    )
    fresh = bases[MODULE_LOCATOR]
    assert fresh.normalization_diagnostic is not None
    view = build_knowledge_read_view(loaded, live_evaluation=replace(live, concept_bases={**live.concept_bases, **bases}))
    assert view.freshness is not None
    result = view.freshness.by_locator[MODULE_LOCATOR]
    assert result.live_basis is not None
    assert result.live_basis.normalization_diagnostic == fresh.normalization_diagnostic
    assert result.recorded_basis is not None and result.recorded_basis.normalization_diagnostic is None
    payload = ManifestEvidenceBaseline.from_basis(fresh).to_payload()
    assert set(payload) == {'state', 'basis', 'unknown_reason'}
    assert DIAGNOSTIC_SCHEMA not in json.dumps(payload)
    restored = ManifestEvidenceBaseline.from_payload(payload, 'baseline')
    assert restored.basis is not None and restored.basis.normalization_diagnostic is None
    # Diagnostics never affect equality or evidence/hash payloads.
    assert replace(fresh, normalization_diagnostic=None) == fresh
    assert sha256_bytes(json.dumps(payload, sort_keys=True).encode()) == sha256_bytes(json.dumps(ManifestEvidenceBaseline.from_basis(replace(fresh, normalization_diagnostic=None)).to_payload(), sort_keys=True).encode())


def test_false_and_zero_keep_distinct_valid_structural_meanings():
    data = _inventory('python')
    attribute = data['classes'][0]['attributes'][0]
    attribute['constraints'] = {'minimum': 0}
    attribute['required'] = False
    first = _entity_basis(data, 'User')
    assert first.is_known and first.normalization_diagnostic is None
    attribute['constraints']['minimum'] = False
    second = _entity_basis(data, 'User')
    assert second.is_known and first.concept_observation_hash != second.concept_observation_hash


def test_redacted_mapping_keys_keep_a_resolvable_ancestor_through_nested_arrays():
    data = _inventory('python')
    data['classes'][0]['attributes'][0]['constraints'] = {'SECRET_KEY': [{'value': float('nan')}]}
    result = detail(_entity_basis(data, 'User'))
    assert result['pointer'] == '/classes/0/attributes/0/constraints'
    assert not result['pointer_exact']
    assert 'SECRET_KEY' not in json.dumps(result)


def test_missing_value_sentinel_is_bound_to_shared_producer_identity(tmp_path, monkeypatch):
    from llm_wiki_cli.services import analysis_capture as capture, knowledge_evidence as ke

    data = {'classes': [], 'functions': []}
    assert not _module_basis(data).is_known
    # A future changed sentinel can alter acceptance; it is not presentation-only.
    monkeypatch.setattr(ke, 'MISSING_VALUE', 'python')
    assert _module_basis(data).is_known
    rules = capture.registry()
    name = 'services/normalization_diagnostics.py'
    assert name in rules['shared']
    package = Path(ke.__file__).parents[1]
    copied = tmp_path / 'package'
    for relative in rules['shared']:
        target = copied / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((package / relative).read_bytes())
    before = capture.implementation_hash(copied, rules['shared'])
    old_inputs = [p for p in rules['shared'] if p != name]
    unbound_before = capture.implementation_hash(copied, old_inputs)
    target = copied / name
    target.write_bytes(target.read_bytes().replace(b'MISSING_VALUE = object()', b'MISSING_VALUE = "python"'))
    after = capture.implementation_hash(copied, rules['shared'])
    assert before != after
    assert capture.implementation_hash(copied, old_inputs) == unbound_before
