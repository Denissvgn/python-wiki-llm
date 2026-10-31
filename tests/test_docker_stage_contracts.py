"""Dockerfile source ownership and independently specified stage expectations."""

from __future__ import annotations

import json
import sys

from markdown_it import MarkdownIt
import pytest

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


@pytest.mark.parametrize("escape", ["\\", "`"])
def test_continued_words_and_quoted_whitespace_keep_their_source_meaning(escape):
    source = (f"# escape={escape}\nFROM scr{escape}\natch AS build\n"
              f'ENV JOINED=hello{escape}\nworld SPACED="hello{escape}\n  world"\n'
              f"FROM bu{escape}\n# ignored continuation comment\nild AS runtime\n")
    parsed = _parse_dockerfile(source)
    build, runtime = parsed["stages"]
    assert build["image"] == "scratch" and build["alias"] == "build"
    assert build["env_vars"] == [{"name": "JOINED", "default": "helloworld"},
                                 {"name": "SPACED", "default": "hello  world"}]
    assert runtime["base_kind"] == "stage" and runtime["base_stage"] == 0
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed))
    assert "helloworld" in first and "inherits the image from stage 1" in second


@pytest.mark.parametrize("escape", ["\\", "`"])
def test_doubled_escape_does_not_consume_the_next_stage(escape):
    source = (f"# escape={escape}\nFROM scratch AS build\nENV BUILD_ONLY=tail{escape}{escape}\n"
              'FROM scratch AS runtime\nCMD ["/application"]\n')
    parsed = _parse_dockerfile(source)
    assert [stage["alias"] for stage in parsed["stages"]] == ["build", "runtime"]
    assert parsed["env_vars"] == [] and parsed["cmd"] == '["/application"]'
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed))
    assert "BUILD_ONLY" in first and "BUILD_ONLY" not in second


@pytest.mark.parametrize("prefix", ["# ordinary comment\n", "\n", "# unknown=value\n"])
def test_escape_directives_after_the_directive_block_are_only_comments(prefix):
    source = prefix + '# escape=`\nFROM scratch AS build\nENV BUILD_ONLY=one`\nFROM scratch AS runtime\n'
    parsed = _parse_dockerfile(source)
    assert [stage["alias"] for stage in parsed["stages"]] == ["build", "runtime"]
    assert parsed["stages"][0]["env_vars"] == [{"name": "BUILD_ONLY", "default": "one`"}]


@pytest.mark.parametrize(("instruction", "marker", "terminator"), [("COPY", "E\"OF\"", "EOF"),
    ("RUN", "'END OF FILE'", "END OF FILE"), ("COPY", "EOF!", "EOF!"), ("COPY", "\\EOF", "EOF")])
def test_quoted_and_escaped_heredoc_delimiters_keep_bodies_out_of_the_inventory(instruction, marker, terminator):
    source = (f"FROM scratch AS build\n{instruction} <<{marker}" + (" /notice" if instruction == "COPY" else "") + "\n"
              f"FROM bogus AS invented\nENV WRONG=1\n{terminator}\n"
              'FROM scratch AS runtime\nCOPY --from=build /notice /notice\n')
    parsed = _parse_dockerfile(source)
    assert [stage["alias"] for stage in parsed["stages"]] == ["build", "runtime"]
    assert all(stage["env_vars"] == [] for stage in parsed["stages"])
    if instruction == "COPY":
        assert parsed["stages"][0]["copies"][0]["inline"] is True
    assert "ENV WRONG=1" in parsed["stages"][0]["instructions"][1]["value"]


def test_onbuild_heredoc_bodies_are_owned_by_the_trigger_instruction():
    parsed = _parse_dockerfile('FROM scratch AS build\nONBUILD COPY <<EOF /notice\n'
                              'FROM bogus AS invented\nENV WRONG=1\nEOF\nFROM scratch AS runtime\n')
    assert [stage["alias"] for stage in parsed["stages"]] == ["build", "runtime"]
    assert parsed["stages"][0]["env_vars"] == []
    assert parsed["stages"][0]["instructions"][1]["instruction"] == "ONBUILD"
    assert "ENV WRONG=1" in parsed["stages"][0]["instructions"][1]["value"]


def test_nested_onbuild_fragments_remain_opaque_without_recursive_interpretation():
    source = "ONBUILD " * 1500 + "RUN true"
    parsed = _parse_dockerfile("FROM scratch\n" + source + "\nFROM scratch AS runtime\n")
    assert parsed["stages"][0]["instructions"][1]["value"] == source.removeprefix("ONBUILD ")
    assert parsed["stages"][1]["alias"] == "runtime"


@pytest.mark.parametrize("source", ['COPY prefix"<<EOF" /notice', 'RUN echo prefix"<<EOF"',
                                    'RUN ["echo", "<<EOF"]', 'COPY ["<<EOF", "/notice"]'])
def test_literal_heredoc_text_does_not_consume_following_stages(source):
    parsed = _parse_dockerfile(f'FROM scratch AS build\n{source}\nFROM scratch AS runtime\nCMD ["/application"]\n')
    assert [stage["alias"] for stage in parsed["stages"]] == ["build", "runtime"]
    assert parsed["stages"][0]["instructions"][1]["value"].count("\n") == 0
    assert parsed["cmd"] == '["/application"]'


def test_scoped_rendering_preserves_literal_values_that_resemble_its_labels():
    marker = "**Working Directory:**"
    entrypoint = json.dumps(["echo", marker])
    command = json.dumps([marker])
    source = (f'FROM scratch AS build\nENV MESSAGE="{marker}"\nLABEL message="{marker}"\n'
              f'WORKDIR /{marker}\nENTRYPOINT {entrypoint}\nCMD {command}\nFROM scratch AS runtime\n')
    parsed = _parse_dockerfile(source)
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed))
    values = [child.content for block in MarkdownIt().parse(first) for child in block.children or []
              if child.type == "code_inline"]
    assert values.count(marker) == 2  # Independent ENV and LABEL declarations.
    assert "/" + marker in values and entrypoint in values and command in values
    assert first.count("**Declared WORKDIR:**") == 1
    assert marker not in second
    assert parsed["stages"][0]["workdir"] == "/" + marker


@pytest.mark.parametrize(("flags", "escape"), [
    ('--exclude="not needed" --from="build"', "\\"),
    ("--exclude='not needed' --from='build'", "\\"),
    ("--exclude=not\\ needed --from=build", "\\"),
    ('--exclude=not` needed --from="build"', "`"),
])
@pytest.mark.parametrize("syntax", ["shell", "json"])
def test_copy_flags_preserve_image_origin_without_inventing_host_sources(flags, escape, syntax):
    paths = ["builder.py", "startup.sh", "/app/"]
    arguments = json.dumps(paths) if syntax == "json" else " ".join(paths)
    source = (f"# escape={escape}\nFROM scratch AS build\nENV BUILD_ONLY=1\n"
              f"FROM scratch AS runtime\nCOPY {flags} {arguments}\n")
    parsed = _parse_dockerfile(source)
    copy = parsed["stages"][1]["copies"][0]
    assert copy == {"src": "builder.py startup.sh", "dest": "/app/", "from_stage": "build", "instruction": "COPY"}
    assert parsed["copies"] == [{**copy, "stage": 1, "line": 5}]
    assert not parsed["env_vars"] and parsed["stages"][1]["base_stage"] is None
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed,
        {"builder.py": "builder"}, {"shell": {"paths": ["startup.sh"]}}))
    assert "BUILD_ONLY" in first and "BUILD_ONLY" not in second
    assert "../modules/builder.md" not in second and "Unsupported Copied Sources" not in second
    assert "| `build` |" in second


@pytest.mark.parametrize("syntax", ["shell", "json"])
def test_copy_flag_terminator_keeps_flag_looking_context_paths(syntax):
    arguments = '["--from=build", "/app.py"]' if syntax == "json" else "--from=build /app.py"
    parsed = _parse_dockerfile(f"FROM scratch AS build\nFROM scratch AS runtime\nCOPY -- {arguments}\n")
    copy = parsed["stages"][1]["copies"][0]
    assert copy == {"src": "--from=build", "dest": "/app.py", "from_stage": "", "instruction": "COPY"}
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed, {"--from=build": "context"}))
    assert "../modules/context.md" in second and "../modules/context.md" not in first


@pytest.mark.parametrize("instruction", ["ENV", "LABEL"])
@pytest.mark.parametrize(("value", "expected"), [
    ("one   two", "one   two"),
    ('" leading  value "  tail', " leading  value   tail"),
    ("one=two   three", "one=two   three"),
    ("one\ttwo", "one\ttwo"),
])
def test_legacy_declaration_values_keep_significant_whitespace(instruction, value, expected):
    parsed = _parse_dockerfile(f"FROM scratch AS build\n{instruction} MESSAGE {value}\nFROM scratch AS runtime\n")
    build, runtime = parsed["stages"]
    if instruction == "ENV":
        assert build["env_vars"] == [{"name": "MESSAGE", "default": expected}]
        assert parsed["env_vars"] == runtime["env_vars"] == []
    else:
        assert build["labels"] == {"MESSAGE": expected}
        assert parsed["labels"] == runtime["labels"] == {}
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed))
    assert "MESSAGE" not in second
    if "\t" in expected:
        assert "one&#9;two" in first
    else:
        values = [child.content for block in MarkdownIt().parse(first) for child in block.children or []
                  if child.type == "code_inline"]
        assert expected in values


@pytest.mark.parametrize("escape", ["\\", "`"])
@pytest.mark.parametrize("parent", ["scratch", "build"])
def test_multiple_arg_declarations_retain_every_owner_line_and_raw_default(escape, parent):
    source = (f'# escape={escape}\nARG FIRST=one SECOND="two words"\nFROM scratch AS build\n'
              f'ARG LOCAL=left OTHER=right{escape} words QUOTED="quoted words" EMPTY="" NO_DEFAULT\n'
              f'FROM {parent} AS runtime\nARG LAST=final UNKNOWN\n')
    parsed = _parse_dockerfile(source)
    global_args = [{"name": "FIRST", "default": "one"}, {"name": "SECOND", "default": '"two words"'}]
    build_args = [{"name": "LOCAL", "default": "left"}, {"name": "OTHER", "default": f"right{escape} words"},
                  {"name": "QUOTED", "default": '"quoted words"'}, {"name": "EMPTY", "default": '""'},
                  {"name": "NO_DEFAULT", "default": ""}]
    runtime_args = [{"name": "LAST", "default": "final"}, {"name": "UNKNOWN", "default": ""}]
    assert parsed["global_build_args"] == global_args
    assert parsed["stages"][0]["build_args"] == build_args
    assert parsed["stages"][1]["build_args"] == runtime_args
    assert parsed["build_args"] == ([{**arg, "stage": None, "line": 2} for arg in global_args]
        + [{**arg, "stage": 0, "line": 4} for arg in build_args]
        + [{**arg, "stage": 1, "line": 6} for arg in runtime_args])
    first, second = _stage_sections(_generate_dockerfile_md("Dockerfile", parsed))
    assert all(f"`{name}`" in first and f"`{name}`" not in second for name in ("LOCAL", "OTHER", "QUOTED", "EMPTY", "NO_DEFAULT"))
    assert "`LAST`" in second and "`UNKNOWN`" in second


@pytest.mark.parametrize("name", ["memo\n\n### Stage 999\n.txt", "tick`name.py", "pipe|name.py"])
def test_context_copy_literals_cannot_change_stage_or_table_structure(name):
    source = ('FROM scratch AS build\nCOPY ' + json.dumps([name, "/memo"])
              + '\nFROM scratch AS runtime\nCMD ["/application"]\n')
    info = _parse_dockerfile(source)
    page = _generate_dockerfile_md("Dockerfile", info, {name: "literal"})
    first, second = _stage_sections(page)
    assert len(info["stages"]) == 2 and "literal.md" not in second
    if "\n" in name:
        assert "&#10;" in first and "<pre><code>" in first
        assert "../modules/literal.md" not in first
    else:
        tokens = MarkdownIt().enable("table").parse(first)
        values = [child.content for token in tokens for child in token.children or [] if child.type == "code_inline"]
        assert name in values
        assert "../modules/literal.md" in first


def test_unsupported_copy_notices_quote_literal_source_paths():
    name = "startup`note.sh"
    source = "FROM scratch\nCOPY " + json.dumps([name, "/entrypoint.sh"]) + "\n"
    page = _generate_dockerfile_md("Dockerfile", _parse_dockerfile(source), {}, {"shell": {"paths": [name]}})
    tokens = MarkdownIt().enable("table").parse(page)
    values = [child.content for token in tokens for child in token.children or [] if child.type == "code_inline"]
    assert values.count(name) == 3  # Copy source, notice source, and resolved path.


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


@pytest.mark.parametrize("syntax", ["plain", "continued-from", "heredoc", "quoted-copy", "declarations", "copy-literal"])
def test_stage_only_edits_flow_through_extract_bootstrap_sync_and_strict_lint(tmp_path, monkeypatch, capsys, syntax):
    (tmp_path / "demo.py").write_text("def marker():\n    pass\n")
    source = tmp_path / "Dockerfile"
    text = INDEPENDENT
    if syntax == "continued-from":
        text = text.replace("FROM scratch AS build", "FROM scr\\\natch AS build")
    elif syntax == "heredoc":
        text = text.replace("ENV BUILD_ONLY=1\n", 'ENV BUILD_ONLY=1\nCOPY <<E"OF" /notice\nFROM scratch AS invented\nENV WRONG=1\nEOF\n')
    elif syntax == "quoted-copy":
        text = text.replace('CMD ["/application"]', 'COPY --exclude="not needed" --from="build" demo.py /app.py\nCMD ["/application"]')
    elif syntax == "declarations":
        text = 'ARG GLOBAL_ONE=1 GLOBAL_TWO="two words"\n' + text.replace("ENV BUILD_ONLY=1\n",
            "ENV BUILD_ONLY=1\nENV NOTE one   two\nLABEL note one   two\nARG BUILD_ONE=1 BUILD_TWO=2\n")
    elif syntax == "copy-literal":
        text = text.replace("ENV BUILD_ONLY=1\n", "ENV BUILD_ONLY=1\nCOPY "
            + json.dumps(["memo\n\n### Stage 999\n.txt", "/memo"]) + "\n")
    source.write_text(text)
    monkeypatch.chdir(tmp_path)

    def run(command, *options):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", command, "--src-dir", ".",
            *([] if command == "extract" else ["--wiki-dir", "wiki"]), *options,
            *([] if command in {"bootstrap", "extract"} else ["--jobs", "1"])])
        cli.main()
        return capsys.readouterr().out

    run("bootstrap", "--source-adapter")
    page = tmp_path / "wiki/infrastructure/Dockerfile.md"
    first, second = _stage_sections(page.read_text())
    assert "BUILD_ONLY" in first and "BUILD_ONLY" not in second
    assert "../modules/demo.md" not in second
    payload = json.loads(run("extract", "--deep", "--read-only"))
    assert payload["docker"]["Dockerfile"]["stages"][1]["entrypoint"] == ""
    if syntax == "declarations":
        info = payload["docker"]["Dockerfile"]
        assert info["stages"][0]["env_vars"][-1] == {"name": "NOTE", "default": "one   two"}
        assert [row["name"] for row in info["stages"][0]["build_args"]] == ["BUILD_ONE", "BUILD_TWO"]
        assert [row["name"] for row in info["global_build_args"]] == ["GLOBAL_ONE", "GLOBAL_TWO"]
    report = json.loads(run("lint", "--strict", "--profile"))
    assert report["ok"], report["issues"]
    source.write_text(text.replace("BUILD_ONLY=1", "BUILD_ONLY=2"))
    run("sync", "--no-plugins")
    first, second = _stage_sections(page.read_text())
    assert "`2`" in first and "BUILD_ONLY" not in second
    before = page.read_bytes()
    run("sync", "--no-plugins")
    assert page.read_bytes() == before
    report = json.loads(run("ci-check", "--format", "json", "--no-report", "--no-plugins"))
    assert report["ok"], report["issues"]
