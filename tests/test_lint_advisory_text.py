"""Default lint disclosure preserves full findings and integrity behavior."""

import json
import sys

import pytest

from llm_wiki_cli.cli import main
from llm_wiki_cli.services.lint_service import LintIssue, LintReport, render_text, render_markdown, report_to_dict


@pytest.mark.parametrize('kind', ['external_call', 'unresolved_call', 'step_limit', 'truncated_flow'])
def test_advisory_flow_gap_is_visible_without_global_consistency_claim(kind):
    finding = LintIssue('data_flow_gaps', f'Data-flow gap in checkout: {kind} entry -> target line 7',
                        severity='warning', target='checkout')
    report = LintReport('wiki', 'src', diagnostics=[finding])
    raw = report_to_dict(report)
    markdown = render_markdown(report)
    text = render_text(report)
    assert finding.message in text
    assert 'Next action: Inspect the affected flow and source' in text
    assert 'upstream analysis can remain bounded or incomplete' in text
    assert 'no blocking issues' in text and 'fully consistent' not in text
    assert report.passed and report.issue_count == 0
    assert report_to_dict(report) == raw and render_markdown(report) == markdown


def test_preview_is_bounded_but_all_raw_records_and_severities_remain():
    findings = [LintIssue('data_flow_gaps', f'Unique missing observation {i}', severity='warning', target='flow')
                for i in range(20)]
    report = LintReport('wiki', 'src', diagnostics=findings)
    before = report_to_dict(report)
    text = render_text(report)
    assert 'Showing 5 of 20 record(s); 15 omitted' in text
    assert 'lint --profile JSON or CI JSON/Markdown with the same roots and options' in text
    assert findings[4].message in text and findings[5].message not in text
    assert report_to_dict(report) == before
    assert len(before['diagnostics']) == 20
    assert all(f.message in render_markdown(report) for f in findings)


def test_unfamiliar_advisories_keep_info_warning_path_and_hint():
    report = LintReport('wiki', 'src', diagnostics=[
        LintIssue('consumer-info', 'A limited consumer observation', 'info', path='modules/demo.md', hint='Inspect source.'),
        LintIssue('consumer-warning', 'Check caller scope', 'warning'),
        LintIssue('unscanned_manifest_scopes', 'Unused analysis was not performed', 'warning'),
    ])
    text = render_text(report)
    assert 'INFO: A limited consumer observation (modules/demo.md)' in text
    assert 'WARNING: Check caller scope' in text
    assert 'Hint: Inspect source.' in text
    assert 'Unused analysis was not performed' in text
    assert 'fully consistent' not in text
    assert report.passed


def test_long_control_characters_only_affect_bounded_escaped_preview():
    message = 'unresolved\n\r\x1b' + 'x' * 2_000
    report = LintReport('wiki', 'src', diagnostics=[LintIssue('data_flow_gaps', message, 'warning')])
    before = report_to_dict(report)
    text = render_text(report)
    assert '\\n\\r\\u001b' in text and '\x1b' not in text
    preview = next(line for line in text.splitlines() if line.startswith('    WARNING: '))
    assert len(preview.removeprefix('    WARNING: ')) == 400
    assert preview.endswith('...')
    assert report_to_dict(report) == before
    assert before['diagnostics'][0]['message'] == message


def test_blocking_issue_stays_failed_and_clean_report_does_not_invent_advisories():
    failed = LintReport('wiki', 'src', issues=[LintIssue('broken_links', 'Missing page', path='index.md')],
                        diagnostics=[LintIssue('data_flow_gaps', 'Missing static effect', 'warning')])
    text = render_text(failed)
    assert 'Missing page' in text and 'Missing static effect' in text
    assert 'Lint found 1 issue(s)' in text and not failed.passed
    clean = LintReport('wiki', 'src')
    assert 'no blocking issues' in render_text(clean)
    assert 'Advisory diagnostics:' not in render_text(clean)
    assert 'fully consistent' not in render_text(clean)


def test_real_cli_static_external_call_disclosure_has_unchanged_success_exit(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'app.py').write_text('from external_package import remote\n\ndef main():\n    return remote()\n')
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="advisory-consumer"\nversion="0.1.0"\n[project.scripts]\nprobe="app:main"\n')
    monkeypatch.setattr(sys, 'argv', ['llm-wiki', 'bootstrap', '--src-dir', '.', '--wiki-dir', 'wiki',
                                    '--skip-workflows', '--skip-dependencies', '--source-adapter'])
    main()
    capsys.readouterr()
    monkeypatch.setattr(sys, 'argv', ['llm-wiki', 'lint', '--src-dir', '.', '--wiki-dir', 'wiki', '--strict'])
    main()
    text = capsys.readouterr().out
    assert 'Data-flow gap in process-probe' in text and 'remote' in text
    assert 'fully consistent' not in text
    monkeypatch.setattr(sys, 'argv', ['llm-wiki', 'lint', '--src-dir', '.', '--wiki-dir', 'wiki', '--strict', '--profile'])
    main()
    raw = json.loads(capsys.readouterr().out)
    gaps = [r for r in raw['diagnostics'] if r['category'] == 'data_flow_gaps']
    assert gaps and raw['ok'] and raw['issue_count'] == 0
    assert all(r['severity'] == 'warning' for r in gaps)
