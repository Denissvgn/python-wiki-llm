"""Focused regressions for sync runtime provenance and deferred changes."""

from __future__ import annotations

import subprocess
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import bootstrap_runtime, knowledge_orchestration
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME


def _bootstrap_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _sync_args(**kwargs):
    defaults = {"src_dir": ".", "wiki_dir": "docs/llm_wiki"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _wiki_bytes(wiki_dir: Path) -> dict[str, bytes]:
    return {
        path.relative_to(wiki_dir).as_posix(): path.read_bytes()
        for path in sorted(wiki_dir.rglob("*"))
        if path.is_file()
    }


def _new_project(tmp_path: Path, *, name: str = "project") -> tuple[Path, Path]:
    project = tmp_path / name
    project.mkdir()
    subprocess.run(
        ["git", "init", str(project)],
        check=True,
        capture_output=True,
    )
    return project, project / "docs" / "llm_wiki"


def _bootstrap_rich_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    project, wiki_dir = _new_project(tmp_path, name="rich-project")
    (project / "pyproject.toml").write_text(
        textwrap.dedent(
            """\
            [project]
            name = "rich-project"
            version = "0.1.0"

            [project.scripts]
            rich-project = "app:publish"
            """
        ),
        encoding="utf-8",
    )
    for module, class_name in (
        ("alpha", "Alpha"),
        ("beta", "Beta"),
        ("gamma", "Gamma"),
    ):
        (project / f"{module}.py").write_text(
            f"class {class_name}:\n    pass\n",
            encoding="utf-8",
        )
    (project / "app.py").write_text(
        textwrap.dedent(
            """\
            from alpha import Alpha
            from beta import Beta
            from gamma import Gamma

            __all__ = ["publish"]


            def publish(alpha: Alpha, beta: Beta, gamma: Gamma) -> Gamma:
                return gamma
            """
        ),
        encoding="utf-8",
    )
    (project / "Dockerfile").write_text(
        'FROM alpine:3.19\nENTRYPOINT ["python", "-m", "app"]\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    bootstrap_cmd.run(
        _bootstrap_args(
            src_dir=str(project),
            wiki_dir=str(wiki_dir),
            skip_workflows=False,
        )
    )
    return project, wiki_dir


def test_generator_version_upgrade_regenerates_managed_modules_and_converges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project, wiki_dir = _new_project(tmp_path)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "project"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (project / "worker.py").write_text(
        "def value():\n    return 1\n",
        encoding="utf-8",
    )
    (project / "service.py").write_text(
        "from worker import value\n\n\ndef run():\n    return value()\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    bootstrap_cmd.run(
        _bootstrap_args(src_dir=str(project), wiki_dir=str(wiki_dir))
    )

    managed_module_paths = {
        wiki_dir / "modules" / f"{source['module_page']}.md"
        for source in SyncManifest.load(wiki_dir).sources.values()
    }
    assert len(managed_module_paths) == 2
    semantic_prose = "Explains the reviewed service boundary for operators."
    service_module = wiki_dir / "modules" / "service.md"
    service_module.write_text(
        sync_cmd._replace_section_body(
            service_module.read_text(encoding="utf-8"),
            "Description",
            semantic_prose,
        ),
        encoding="utf-8",
    )

    marker = "<!-- generated-imports-template-9.8.7 -->"
    original_renderer = sync_cmd._generate_module_md
    rendered_sources: set[str] = set()

    def upgraded_renderer(*args, **kwargs):
        rendered_sources.add(str(args[0]))
        rendered = original_renderer(*args, **kwargs)
        return rendered.replace(
            "## Imports\n\n",
            f"## Imports\n\n{marker}\n\n",
            1,
        )

    monkeypatch.setattr(sync_cmd, "_generate_module_md", upgraded_renderer)
    monkeypatch.setattr(sync_cmd, "__version__", "9.8.7")
    monkeypatch.setattr(bootstrap_cmd, "__version__", "9.8.7")
    monkeypatch.setattr(bootstrap_runtime, "__version__", "9.8.7")
    monkeypatch.setattr(knowledge_orchestration, "__version__", "9.8.7")
    capsys.readouterr()

    sync_cmd.run(_sync_args(src_dir=str(project), wiki_dir=str(wiki_dir)))

    assert rendered_sources == {"service.py", "worker.py"}
    assert marker in service_module.read_text(encoding="utf-8")
    assert marker not in (wiki_dir / "modules" / "worker.md").read_text(
        encoding="utf-8"
    )
    assert semantic_prose in service_module.read_text(encoding="utf-8")
    knowledge = load_knowledge_state(wiki_dir).knowledge
    assert knowledge is not None
    assert knowledge.bundle.producer.tool.version == "9.8.7"
    first_tree = _wiki_bytes(wiki_dir)

    sync_cmd.run(_sync_args(src_dir=str(project), wiki_dir=str(wiki_dir)))

    assert _wiki_bytes(wiki_dir) == first_tree
    assert "Wiki is up to date." in capsys.readouterr().out


def test_surface_initialization_and_normal_sync_share_canonical_graph_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project, wiki_dir = _new_project(tmp_path)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "project"\nversion = "0.1.0"\n'
        'dependencies = ["requests"]\n',
        encoding="utf-8",
    )
    (project / "app.py").write_text(
        "import requests\n\n\ndef fetch():\n"
        "    return requests.get('https://example.invalid')\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    bootstrap_cmd.run(
        _bootstrap_args(src_dir=str(project), wiki_dir=str(wiki_dir))
    )
    initialize_args = _sync_args(
        src_dir=str(project),
        wiki_dir=str(wiki_dir),
        initialize_surfaces=[("flows",)],
        no_cache=True,
    )
    capsys.readouterr()

    sync_cmd.run(initialize_args)
    sync_cmd.run(initialize_args)
    initialized_tree = _wiki_bytes(wiki_dir)

    sync_cmd.run(
        _sync_args(
            src_dir=str(project),
            wiki_dir=str(wiki_dir),
            no_cache=True,
        )
    )

    assert _wiki_bytes(wiki_dir) == initialized_tree
    assert "Wiki is up to date." in capsys.readouterr().out


def test_legacy_manifest_refreshes_package_facts_before_adopting_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project, wiki_dir = _new_project(tmp_path)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "project"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (project / "app.py").write_text(
        "import requests\n\n\ndef fetch():\n"
        "    return requests.get('https://example.invalid')\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    bootstrap_cmd.run(
        _bootstrap_args(src_dir=str(project), wiki_dir=str(wiki_dir))
    )
    module_path = wiki_dir / "modules" / "app.md"
    assert "| python | 1 | 1 |" in module_path.read_text(encoding="utf-8")

    SyncManifest.load(wiki_dir).without_artifact_hashes().save(wiki_dir)
    for filename in (SURFACE_INDEX_FILENAME, KNOWLEDGE_INDEX_FILENAME):
        (wiki_dir / filename).unlink()
    assert SyncManifest.load(wiki_dir).artifact_hashes is None
    (project / "pyproject.toml").write_text(
        '[project]\nname = "project"\nversion = "0.1.0"\n'
        'dependencies = ["requests"]\n',
        encoding="utf-8",
    )

    real_finalize = sync_cmd.finalize_runtime_knowledge
    finalized_after_refresh: list[bool] = []

    def finalize_after_module_refresh(*args, **kwargs):
        refreshed = "| python | 1 | 0 |" in module_path.read_text(encoding="utf-8")
        finalized_after_refresh.append(refreshed)
        assert refreshed
        return real_finalize(*args, **kwargs)

    monkeypatch.setattr(
        sync_cmd,
        "finalize_runtime_knowledge",
        finalize_after_module_refresh,
    )
    capsys.readouterr()

    sync_cmd.run(_sync_args(src_dir=str(project), wiki_dir=str(wiki_dir)))

    assert finalized_after_refresh == [True]
    assert "| python | 1 | 0 |" in module_path.read_text(encoding="utf-8")
    adopted = SyncManifest.load(wiki_dir)
    assert adopted.artifact_hashes is not None
    assert (wiki_dir / SURFACE_INDEX_FILENAME).is_file()
    assert (wiki_dir / KNOWLEDGE_INDEX_FILENAME).is_file()
    first_tree = _wiki_bytes(wiki_dir)

    sync_cmd.run(_sync_args(src_dir=str(project), wiki_dir=str(wiki_dir)))

    assert finalized_after_refresh == [True, True]
    assert _wiki_bytes(wiki_dir) == first_tree
    assert "Wiki is up to date." in capsys.readouterr().out


@pytest.mark.parametrize("deferred_change", ("source", "infrastructure"))
def test_repeated_surface_initialization_preserves_deferred_state_and_converges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    deferred_change: str,
) -> None:
    project, wiki_dir = _bootstrap_rich_project(tmp_path, monkeypatch)
    index_metadata = (
        "- [publish](workflows/publish.md) - entry: `app.publish`",
        "- [api-publish](flows/api-publish.md) - entry: `publish`",
        "- [Dockerfile](infrastructure/Dockerfile.md) - dockerfile",
    )
    initial_index = (wiki_dir / "index.md").read_text(encoding="utf-8")
    for line in index_metadata:
        assert line in initial_index

    app_module = wiki_dir / "modules" / "app.md"
    flow_page = wiki_dir / "flows" / "api-publish.md"
    workflow_page = wiki_dir / "workflows" / "publish.md"
    manifest = SyncManifest.load(wiki_dir)
    infrastructure_record = manifest.generation_inputs["infrastructure"]["sources"][
        "Dockerfile"
    ]
    infrastructure_page = wiki_dir / infrastructure_record["page_path"]
    deferred_page = (
        app_module if deferred_change == "source" else infrastructure_page
    )
    deferred_page_before = deferred_page.read_bytes()

    if deferred_change == "source":
        (project / "app.py").write_text(
            "__all__ = [\"replacement\"]\n\n\ndef replacement():\n    return 1\n",
            encoding="utf-8",
        )
    else:
        (project / "Dockerfile").write_text(
            'FROM alpine:3.20\nENTRYPOINT ["python", "-m", "app"]\n',
            encoding="utf-8",
        )

    initialize_args = _sync_args(
        src_dir=str(project),
        wiki_dir=str(wiki_dir),
        initialize_surfaces=[("dependencies",)],
        no_cache=True,
    )
    capsys.readouterr()

    sync_cmd.run(initialize_args)

    assert deferred_page.read_bytes() == deferred_page_before
    initialized_index = (wiki_dir / "index.md").read_text(encoding="utf-8")
    for line in index_metadata:
        assert line in initialized_index
    assert flow_page.is_file()
    assert workflow_page.is_file()
    first_initialized_tree = _wiki_bytes(wiki_dir)

    sync_cmd.run(initialize_args)

    assert _wiki_bytes(wiki_dir) == first_initialized_tree
    repeated_output = capsys.readouterr().out
    if deferred_change == "source":
        assert "Deferred source changes: 1 file(s)." in repeated_output
    else:
        assert "Requested optional surfaces are up to date." in repeated_output

    sync_cmd.run(
        _sync_args(
            src_dir=str(project),
            wiki_dir=str(wiki_dir),
            no_cache=True,
        )
    )

    assert deferred_page.read_bytes() != deferred_page_before
    if deferred_change == "source":
        assert "`replacement`" in app_module.read_text(encoding="utf-8")
        assert not flow_page.exists()
        assert not workflow_page.exists()
    else:
        assert "alpine:3.20" in infrastructure_page.read_text(encoding="utf-8")
    first_normal_tree = _wiki_bytes(wiki_dir)

    sync_cmd.run(
        _sync_args(
            src_dir=str(project),
            wiki_dir=str(wiki_dir),
            no_cache=True,
        )
    )

    assert _wiki_bytes(wiki_dir) == first_normal_tree
    assert "Wiki is up to date." in capsys.readouterr().out
