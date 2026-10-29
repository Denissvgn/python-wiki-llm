"""Dockerfile source ownership and independently specified stage expectations."""

from __future__ import annotations

import json
import sys

from markdown_it import MarkdownIt

from llm_wiki_cli import cli
from llm_wiki_cli.commands.extract_cmd import _parse_dockerfile
from llm_wiki_cli.commands.bootstrap_cmd import _generate_dockerfile_md
from llm_wiki_cli.services.dockerfile_parser import DOCKERFILE_STAGES_SCHEMA
from llm_wiki_cli.services.section_ownership import SectionOwnership, observe_page_sections
from llm_wiki_cli.services.wiki_surface import PageKind


INDEPENDENT = '''FROM scratch AS build
WORKDIR /builder
ENV BUILD_ONLY=1
ENTRYPOINT ["/build-tool"]
FROM scratch AS runtime
CMD ["/application"]
'''


def _stage_sections(markdown):
    lines = markdown.split("\n")
    boundaries = []
    tokens = MarkdownIt().parse(markdown)
    for index, token in enumerate(tokens[:-1]):
        if token.type == "heading_open" and token.tag == "h3" and tokens[index + 1].content.startswith("Stage "):
            assert token.map is not None
            boundaries.append(token.map[0])
    return ["\n".join(lines[start:boundaries[index + 1] if index + 1 < len(boundaries) else len(lines)])
            for index, start in enumerate(boundaries)]


def test_independent_stages_cannot_form_a_cross_stage_container_configuration():
    parsed = _parse_dockerfile(INDEPENDENT)
    assert parsed["stage_schema_version"] == DOCKERFILE_STAGES_SCHEMA
    assert parsed["configuration_scope"] == "final-stage-declarations" and parsed["final_stage"] == 1
    build, runtime = parsed["stages"]
    assert build["workdir"] == "/builder" and build["entrypoint"] == '["/build-tool"]'
    assert build["env_vars"] == [{"name": "BUILD_ONLY", "default": "1"}]
    assert runtime["base_kind"] == "scratch" and runtime["base_stage"] is None
    assert runtime["workdir"] == runtime["entrypoint"] == "" and runtime["env_vars"] == []
    assert runtime["cmd"] == parsed["cmd"] == '["/application"]'
    assert parsed["env_vars"] == [] and parsed["entrypoint"] == parsed["workdir"] == ""
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed))
    assert "BUILD_ONLY" in first and "/build-tool" in first and "/builder" in first
    assert all(value not in second for value in ("BUILD_ONLY", "/build-tool", "/builder"))
    assert "/application" in second and "independent scratch" in second


def test_inherited_stage_is_linked_without_fabricating_an_effective_summary():
    parsed = _parse_dockerfile(INDEPENDENT.replace("FROM scratch AS runtime", "FROM build AS runtime"))
    assert parsed["stages"][1]["base_stage"] == 0 and parsed["stages"][1]["base_kind"] == "stage"
    assert parsed["entrypoint"] == "" and parsed["env_vars"] == []  # final-stage declarations
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed))
    assert "/build-tool" in first
    assert "inherits the image from stage 1" in second and "declarations authored in this stage" in second
    assert "/application" in second and "/build-tool" not in second


def test_external_defaults_and_dynamic_base_choices_remain_unknown():
    parsed = _parse_dockerfile('ARG BASE=external:one\nFROM --platform=$BUILDPLATFORM ${BASE} AS base\nARG LOCAL=1\nFROM base AS child\n')
    assert parsed["global_build_args"] == [{"name": "BASE", "default": "external:one"}]
    assert [(row["name"], row["stage"]) for row in parsed["build_args"]] == [("BASE", None), ("LOCAL", 0)]
    assert parsed["stages"][0]["image"] == "${BASE}" and parsed["stages"][0]["platform"] == "$BUILDPLATFORM"
    assert parsed["stages"][0]["base_kind"] == "unresolved" and parsed["stages"][1]["base_stage"] == 0
    page = _generate_dockerfile_md("Dockerfile", parsed)
    assert "External base-image defaults remain unknown" in page
    assert "inherited defaults are unknown" in page
    assert parsed["entrypoint"] == parsed["cmd"] == parsed["workdir"] == ""


def test_all_observations_keep_source_owners_and_copy_does_not_inherit_configuration():
    text = '''ARG GLOBAL=1
FROM scratch AS build
ENV ONLY=build
EXPOSE 8000
VOLUME ["/build-data"]
LABEL phase=build
COPY builder.py /builder.py
ARG LOCAL=build
RUN echo build
FROM scratch AS runtime
COPY --from=build /builder.py /app.py
USER app
SHELL ["/bin/sh", "-c"]
STOPSIGNAL SIGTERM
HEALTHCHECK NONE
'''
    parsed = _parse_dockerfile(text)
    build, runtime = parsed["stages"]
    assert build["ports"] == ["8000"] and build["volumes"] == ["/build-data"] and build["labels"] == {"phase": "build"}
    assert any(row["instruction"] == "RUN" and row["line"] == 9 for row in build["instructions"])
    assert runtime["base_stage"] is None and not runtime["env_vars"] and not runtime["ports"] and not runtime["volumes"] and not runtime["labels"]
    assert runtime["user"] == "app" and runtime["stop_signal"] == "SIGTERM" and runtime["healthcheck"] == "NONE"
    assert [row["stage"] for row in parsed["copies"]] == [0, 1]
    assert [row["stage"] for row in parsed["build_args"]] == [None, 0]
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed, {"builder.py": "builder"}))
    assert "../modules/builder.md" in first and "../modules/builder.md" not in second
    assert "Declared USER" in second and "SIGTERM" in second and "NONE" in second


def test_heredoc_content_never_becomes_a_new_stage_or_configuration():
    parsed = _parse_dockerfile('''FROM scratch AS build
COPY <<'CONTENT' /notice
FROM bogus AS invented
ENV WRONG=1
CONTENT
RUN echo "<<NOT_A_HEREDOC"
FROM scratch AS runtime
CMD ["/run"]
''')
    assert [stage["alias"] for stage in parsed["stages"]] == ["build", "runtime"]
    assert parsed["stages"][0]["env_vars"] == []
    copy = parsed["stages"][0]["copies"][0]
    assert copy["inline"] and copy["dest"] == "/notice"
    assert "ENV WRONG=1" in parsed["stages"][0]["instructions"][1]["value"]


def test_escape_directive_and_continuation_comments_keep_stage_boundaries():
    parsed = _parse_dockerfile('# escape=`\nFROM scratch AS build\nENV ONE=1 `\n# comment\n TWO="two words"\nWORKDIR C:\\builder\nFROM scratch\n')
    assert parsed["stages"][0]["env_vars"] == [{"name": "ONE", "default": "1"}, {"name": "TWO", "default": "two words"}]
    assert parsed["stages"][0]["workdir"] == "C:\\builder"
    assert parsed["workdir"] == "" and parsed["stages"][1]["base_stage"] is None


def test_legacy_multistage_records_do_not_render_an_unsafe_command_pair():
    legacy = {"type": "dockerfile", "stages": [{"image": "scratch", "alias": "build"}, {"image": "scratch", "alias": "runtime"}],
              "entrypoint": '["/build-tool"]', "cmd": '["/application"]', "env_vars": [{"name": "BUILD_ONLY", "default": "1"}]}
    page = _generate_dockerfile_md("Dockerfile", legacy)
    assert "Stage ownership is unavailable" in page
    assert all(value not in page for value in ("/build-tool", "/application", "BUILD_ONLY"))


def test_stage_sections_inherit_generated_ownership():
    page = _generate_dockerfile_md("Dockerfile", _parse_dockerfile(INDEPENDENT))
    observations = observe_page_sections(page, "llm-wiki://infrastructure/Dockerfile", PageKind.INFRASTRUCTURE)
    selected = [item for item in observations.sections if "Build Stages" in item.heading_path]
    assert selected and all(item.ownership is SectionOwnership.GENERATED for item in selected)


def test_stage_only_edits_flow_through_extract_bootstrap_sync_and_strict_lint(tmp_path, monkeypatch, capsys):
    (tmp_path / "demo.py").write_text("def marker():\n    pass\n")
    source = tmp_path / "Dockerfile"
    source.write_text(INDEPENDENT)
    monkeypatch.chdir(tmp_path)

    def run(command, *options):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", command, "--src-dir", ".",
            *([] if command == "extract" else ["--wiki-dir", "wiki"]), *options,
            *([] if command in {"bootstrap", "extract"} else ["--jobs", "1", "--no-cache"])])
        cli.main()
        return capsys.readouterr().out

    run("bootstrap", "--source-adapter")
    page = tmp_path / "wiki/infrastructure/Dockerfile.md"
    first, second = _stage_sections(page.read_text())
    assert "BUILD_ONLY" in first and "BUILD_ONLY" not in second
    payload = json.loads(run("extract", "--deep", "--read-only"))
    assert payload["docker"]["Dockerfile"]["stages"][1]["entrypoint"] == ""
    report = json.loads(run("lint", "--strict", "--profile"))
    assert report["ok"], report["issues"]
    source.write_text(INDEPENDENT.replace("BUILD_ONLY=1", "BUILD_ONLY=2"))
    run("sync", "--no-plugins")
    first, second = _stage_sections(page.read_text())
    assert "`2`" in first and "BUILD_ONLY" not in second
    before = page.read_bytes()
    run("sync", "--no-plugins")
    assert page.read_bytes() == before
    report = json.loads(run("ci-check", "--format", "json", "--no-report", "--no-plugins"))
    assert report["ok"], report["issues"]
