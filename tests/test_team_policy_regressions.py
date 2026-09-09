"""Team policy boundary and generator-ownership regressions."""

from __future__ import annotations

import errno
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from llm_wiki_cli.services import team
from llm_wiki_cli.commands import bootstrap_cmd, ci_check_cmd, sync_cmd, team_cmd
from llm_wiki_cli.services import lint_service
from llm_wiki_cli.services.extraction_service import ExtractorStatus


def minimal_config(wiki_dir: str = "wiki") -> dict:
    config = team.default_team_config(wiki_dir)
    conventions = config["conventions"]
    for name in (
        "required_files",
        "required_dirs",
        "required_entity_sections",
        "required_module_sections",
        "required_infrastructure_sections",
    ):
        conventions[name] = []
    conventions.update(
        require_log=False, canonical_naming=False, workflow_filename_pattern=None
    )
    return config


def check(config, wiki):
    return team.check_team_conventions(
        team.TeamConventionRequest(config, wiki, ".", {}, {})
    )


@pytest.mark.parametrize("field", ["required_files", "required_dirs"])
@pytest.mark.parametrize(
    "relative",
    [
        "../README.md",
        "/absolute",
        "",
        ".",
        "a/../b",
        "a//b",
        "./a",
        "C:/absolute",
        "C:relative",
        "\\\\host\\share",
        "a\\b",
        "a\x00b",
        "a\nb",
        "a/",
    ],
)
def test_required_path_syntax_fails_for_config_and_direct_request(
    tmp_path, field, relative
):
    config = minimal_config()
    config["conventions"][field] = [relative]
    with pytest.raises(team.TeamConfigError, match=field):
        team.validate_team_config(config)
    issues = check(config, tmp_path)
    assert len(issues) == 1
    assert issues[0]["category"] == "team_config"


def test_nested_required_paths_and_in_root_symlink_pass(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "file.md").write_text("# Page\n", encoding="utf-8")
    (tmp_path / "alias.md").symlink_to(nested / "file.md")
    config = minimal_config()
    config["conventions"].update(
        required_files=["nested/file.md", "alias.md"], required_dirs=["nested"]
    )
    assert check(config, tmp_path) == []


@pytest.mark.parametrize("kind", ["file", "directory", "implicit_log"])
def test_required_path_symlink_escape_is_one_config_error(tmp_path, kind):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    config = minimal_config()
    if kind == "directory":
        (wiki / "escape").symlink_to(tmp_path, target_is_directory=True)
        config["conventions"]["required_dirs"] = ["escape"]
    else:
        outside = tmp_path / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        name = "log.md" if kind == "implicit_log" else "escape.md"
        (wiki / name).symlink_to(outside)
        if kind == "implicit_log":
            config["conventions"]["require_log"] = True
        else:
            config["conventions"]["required_files"] = [name]
    issues = check(config, wiki)
    assert len(issues) == 1
    assert issues[0]["category"] == "team_config"
    assert "escapes" in issues[0]["message"]


def test_required_path_inspection_error_precedes_page_reads(tmp_path, monkeypatch):
    config = minimal_config()
    config["conventions"]["required_files"] = ["required.md"]
    real_stat = Path.stat

    def fail_leaf(path, *args, **kwargs):
        if path.name == "required.md":
            raise OSError(errno.EACCES, "denied")
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", fail_leaf)
    monkeypatch.setattr(team, "read_md", lambda *_: pytest.fail("read page"))
    issues = check(config, tmp_path)
    assert len(issues) == 1
    assert issues[0]["category"] == "team_config"
    assert "inspect" in issues[0]["message"]


def write_policy(config):
    team.write_default_team_config(config["wiki_dir"])
    team.team_config_path().write_text(json.dumps(config), encoding="utf-8")


def test_team_check_omitted_wiki_uses_policy(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("docs/intended").mkdir(parents=True)
    write_policy(minimal_config("docs/intended"))
    team_cmd.run(SimpleNamespace(team_action="check", src_dir=".", format="json"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["wiki_dir"] == "docs/intended"


@pytest.mark.parametrize("consumer", ["team", "lint", "ci", "service"])
def test_wiki_identity_rejected_before_extraction_and_page_reads(
    tmp_path, monkeypatch, capsys, consumer
):
    monkeypatch.chdir(tmp_path)
    Path("other").mkdir()
    write_policy(minimal_config("intended"))

    def unexpected(*args, **kwargs):
        pytest.fail("invalid team identity reached extraction or page reads")

    monkeypatch.setattr(team_cmd, "get_inventory_result", unexpected)
    monkeypatch.setattr(lint_service, "_collect_lint_inputs", unexpected)
    monkeypatch.setattr(team, "read_md", unexpected)
    if consumer == "team":
        with pytest.raises(SystemExit) as error:
            team_cmd.run(
                SimpleNamespace(
                    team_action="check", src_dir=".", wiki_dir="other", format="json"
                )
            )
        assert error.value.code == 1
        issues = json.loads(capsys.readouterr().out)["issues"]
    elif consumer == "ci":
        with pytest.raises(SystemExit) as error:
            ci_check_cmd.run(
                SimpleNamespace(
                    src_dir=".", wiki_dir="other", format="json", report="report.md"
                )
            )
        assert error.value.code == 1
        issues = json.loads(capsys.readouterr().out)["issues"]
    elif consumer == "lint":
        report = lint_service.build_report("other", ".", strict=True)
        issues = [vars(issue) for issue in report.issues]
    else:
        issues = team.build_team_issues("other", ".", {}, [])
    assert len(issues) == 1
    assert issues[0]["category"] == "team_config"
    assert "identity mismatch" in issues[0]["message"]


def test_equivalent_wiki_identity_and_project_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    team.write_default_team_config("docs/wiki", root=project)
    policy = team.resolve_team_policy("./docs/wiki/", root=project)
    assert policy.root == project
    assert policy.config["wiki_dir"] == "docs/wiki"
    assert (
        team.resolve_team_policy(project / "docs/wiki", root=project).config
        == policy.config
    )


def test_policy_load_is_reused_by_integrated_lint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("wiki").mkdir()
    write_policy(minimal_config())
    calls = []
    original = team.load_team_config

    def counted(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(team, "load_team_config", counted)
    lint_service.build_report("wiki", ".")
    assert len(calls) == 1


def test_configured_external_wiki_is_rejected_before_required_path_probes(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    write_policy(minimal_config("../outside"))
    monkeypatch.setattr(
        team, "_required_path_states", lambda *_: pytest.fail("probed an external wiki")
    )
    with pytest.raises(team.TeamConfigError, match="inside the project root"):
        team.resolve_team_policy(None, required=True)


def test_resolved_policy_is_immutable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_policy(minimal_config())
    policy = team.resolve_team_policy("wiki")
    with pytest.raises(TypeError, match="immutable"):
        policy.config["wiki_dir"] = "other"


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize("require_log", [False, True])
@pytest.mark.parametrize("present", [False, True])
def test_one_log_obligation(tmp_path, explicit, require_log, present):
    config = minimal_config()
    config["conventions"].update(
        required_files=["log.md", "log.md"] if explicit else [],
        require_log=require_log,
    )
    if present:
        (tmp_path / "log.md").write_text("# Log\n", encoding="utf-8")
    issues = check(config, tmp_path)
    expected = int(not present and (explicit or require_log))
    assert len(issues) == expected
    if issues:
        assert issues[0]["path"] == "log.md"
        assert ("architectural log" in issues[0]["message"]) is require_log


def test_duplicate_required_entries_do_not_hide_independent_sections(tmp_path):
    config = minimal_config()
    config["conventions"].update(
        required_files=["absent.md", "absent.md"],
        required_dirs=["absent", "absent"],
        required_module_sections=["Description", "Examples"],
    )
    (tmp_path / "modules").mkdir()
    (tmp_path / "modules/app.md").write_text("# App\n", encoding="utf-8")
    issues = check(config, tmp_path)
    assert len(issues) == 4
    assert [
        issue["target"] for issue in issues if issue["path"] == "modules/app.md"
    ] == ["Description", "Examples"]


def team_payload(capsys):
    capsys.readouterr()
    try:
        team_cmd.run(
            SimpleNamespace(
                team_action="check", src_dir="src", wiki_dir="wiki", format="json"
            )
        )
    except SystemExit as exc:
        assert exc.code == 1
    return json.loads(capsys.readouterr().out)


def assert_team_parity(capsys, expected_paths):
    payload = team_payload(capsys)
    standalone = payload["issues"]
    lint = lint_service.build_report("wiki", "src", strict=True)
    capsys.readouterr()
    try:
        ci_check_cmd.run(
            SimpleNamespace(
                src_dir="src", wiki_dir="wiki", format="json", report="ci-report.md"
            )
        )
    except SystemExit as exc:
        assert exc.code == 1
    ci = json.loads(capsys.readouterr().out)
    for issues in (standalone, [vars(issue) for issue in lint.issues], ci["issues"]):
        assert {
            issue["path"]
            for issue in issues
            if issue["category"] == "team_canonical_naming"
        } == expected_paths
        assert not any(issue["category"] == "team_config" for issue in issues)


def test_generated_deep_collision_yaml_and_removed_pages_agree_across_commands(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/private_only.py").write_text(
        "def _helper():\n    return 1\n", encoding="utf-8"
    )
    Path("src/removed.py").write_text("class Removed:\n    pass\n", encoding="utf-8")
    for folder in ("a.b", "a_b"):
        (Path("src") / folder).mkdir()
        (Path("src") / folder / "Dockerfile").write_text(
            "FROM scratch\n", encoding="utf-8"
        )
    Path("src/Dockerfile.legacy").write_text("FROM alpine\n", encoding="utf-8")
    Path("src/k8s").mkdir()
    Path("src/k8s/deployment.yml").write_text(
        "apiVersion: v1\nkind: Pod\nmetadata:\n  name: example\n", encoding="utf-8"
    )
    bootstrap_cmd.run(
        SimpleNamespace(
            src_dir="src",
            wiki_dir="wiki",
            depth="full",
            overwrite=False,
            skip_workflows=True,
            source_adapter=True,
        )
    )
    team.write_default_team_config("wiki")
    assert len(list(Path("wiki/infrastructure").glob("*__*.md"))) == 2
    assert Path("wiki/infrastructure/k8s_deployment_yml.md").exists()
    assert_team_parity(capsys, set())

    Path("src/removed.py").unlink()
    Path("src/Dockerfile.legacy").unlink()
    sync_cmd.run(SimpleNamespace(src_dir="src", wiki_dir="wiki", no_cache=True))
    assert Path("wiki/modules/removed.md").exists()
    assert Path("wiki/entities/Removed.md").exists()
    assert Path("wiki/infrastructure/Dockerfile_legacy.md").exists()
    assert_team_parity(capsys, set())

    rogue_paths = {
        f"{directory}/rogue.md"
        for directory in ("entities", "modules", "infrastructure")
    }
    for relative in rogue_paths:
        (Path("wiki") / relative).write_text("# Rogue\n", encoding="utf-8")
    assert_team_parity(capsys, rogue_paths)


def test_extractor_failure_is_reported_before_naming(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("wiki/modules").mkdir(parents=True)
    Path("wiki/modules/rogue.md").write_text("# Rogue\n", encoding="utf-8")
    team.write_default_team_config("wiki")

    def fail_inventory(*args, **kwargs):
        assert kwargs["deep"] is True
        return SimpleNamespace(
            failed=[ExtractorStatus("python", "failed", 1, "broken extractor")]
        )

    monkeypatch.setattr(team_cmd, "get_inventory_result", fail_inventory)
    issues = team_payload(capsys)["issues"]
    assert len(issues) == 1
    assert issues[0]["category"] == "extractor_failure"
    assert "broken extractor" in issues[0]["message"]


def test_invalid_managed_authority_stops_before_extraction(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("wiki").mkdir()
    Path("wiki/.llm-wiki-manifest.json").write_text("{broken", encoding="utf-8")
    write_policy(minimal_config())
    monkeypatch.setattr(
        team_cmd, "get_inventory_result", lambda *a, **kw: pytest.fail("extracted")
    )
    issues = team_payload(capsys)["issues"]
    assert len(issues) == 1
    assert issues[0]["category"] == "team_config"
