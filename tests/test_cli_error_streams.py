"""Real CLI failure streams and mutation boundaries for write-oriented commands."""

import io
import subprocess
import sys
import types

import pytest

from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.services.bootstrap_service import (
    BootstrapRequest,
    BootstrapExtractionError,
)
from llm_wiki_cli.services.bootstrap_runtime import execute_bootstrap
from llm_wiki_cli.services.extraction_service import InventoryResult, ExtractorStatus


@pytest.mark.parametrize(
    "argv,files,code",
    [
        (["bootstrap", "--overwrite"], {}, 2),
        (["bootstrap", "--overwrite", "--format", "json"], {}, 2),
        (["bootstrap"], {"docs/llm_wiki/custom.md": "User prose\n"}, 2),
        (
            ["bootstrap", "--format", "json"],
            {"docs/llm_wiki/custom.md": "User prose\n"},
            2,
        ),
        (["bump", "--patch"], {}, 1),
        (["bump", "--minor"], {"pyproject.toml": '[project]\nname="example"\n'}, 1),
        (["release", "--changelog", "absent.md"], {"VERSION": "1.2.3\n"}, 1),
        (["release"], {"CHANGELOG.md": "## [Unreleased]\n\nChange\n"}, 1),
        (
            ["release"],
            {"CHANGELOG.md": "## [Unreleased]\n", "VERSION": "unparseable\n"},
            1,
        ),
        (["release"], {"CHANGELOG.md": "# Changes\n", "VERSION": "1.2.3\n"}, 1),
    ],
    ids=[
        "overwrite-text",
        "overwrite-json",
        "existing-text",
        "existing-json",
        "bump-missing",
        "bump-invalid",
        "release-missing-changelog",
        "release-missing-version",
        "release-invalid-version",
        "release-invalid-changelog",
    ],
)
def test_cli_validation_errors_use_stderr_without_writes(tmp_path, argv, files, code):
    for relative, content in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def snapshot():
        return {
            p.relative_to(tmp_path): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in tmp_path.rglob("*")
            if p.is_file()
        }

    before = snapshot()
    result = subprocess.run(
        [sys.executable, "-c", "from llm_wiki_cli.cli import main; main()", *argv],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == code
    assert result.stdout == ""
    assert result.stderr.startswith("Error:")
    assert snapshot() == before


def test_bootstrap_extraction_diagnostic_respects_cli_and_api_sinks(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.chdir(source)
    monkeypatch.setattr(
        bootstrap_cmd,
        "get_inventory_result",
        lambda *a, **kw: InventoryResult(
            {},
            {"python": ExtractorStatus("python", "failed", 1, "synthetic failure")},
        ),
    )
    args = types.SimpleNamespace(
        src_dir=str(source), wiki_dir=str(source / "cli-wiki"), overwrite=False
    )
    with pytest.raises(SystemExit) as exc:
        bootstrap_cmd.run(args)
    assert exc.value.code == 1
    output = capsys.readouterr()
    assert "Error:" not in output.out
    assert "synthetic failure" in output.err
    stream = io.StringIO()
    with pytest.raises(BootstrapExtractionError):
        execute_bootstrap(
            BootstrapRequest(source_root=source, wiki_root=tmp_path / "api-wiki"),
            progress_stream=stream,
        )
    assert "synthetic failure" in stream.getvalue()
    assert capsys.readouterr() == ("", "")
