"""Executable contracts for publishing, hub, and attack-surface skills."""

from __future__ import annotations

import json
import re
import shlex
import textwrap
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.services.data_flow import analyze_data_flow
from llm_wiki_cli.services.plugins import PluginError
from llm_wiki_cli.services.site_export import (
    SITE_PUBLICATION_MARKER,
    check_site_hub,
    check_site_mirror,
    export_site_hub,
    export_site_mirror,
)
from llm_wiki_cli.services.skills import BUNDLED_SKILLS_ROOT


PUBLISH_SKILL = BUNDLED_SKILLS_ROOT / "publish-docs" / "SKILL.md"
PUBLISH_REFERENCE = BUNDLED_SKILLS_ROOT / "publish-docs" / "reference.md"
HUB_SKILL = BUNDLED_SKILLS_ROOT / "doc-hub" / "SKILL.md"
HUB_REFERENCE = BUNDLED_SKILLS_ROOT / "doc-hub" / "reference.md"
ATTACK_SKILL = BUNDLED_SKILLS_ROOT / "attack-surface" / "SKILL.md"
ATTACK_REFERENCE = BUNDLED_SKILLS_ROOT / "attack-surface" / "reference.md"

BOUNDARY_KINDS = {
    "filesystem_read",
    "filesystem_write",
    "environment_read",
    "environment_write",
    "network",
    "process",
    "mutation",
    "output",
    "logging",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _bash_commands(markdown: str) -> list[str]:
    commands: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", markdown, flags=re.DOTALL):
        pending = ""
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            pending = f"{pending} {line}".strip()
            if pending.endswith("\\"):
                pending = pending[:-1].rstrip()
                continue
            if pending.startswith("llm-wiki "):
                commands.append(pending)
            pending = ""
    return commands


def _yaml_run_commands(markdown: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(
            r"^\s*run:\s*(llm-wiki .+)$",
            markdown,
            flags=re.MULTILINE,
        )
    ]


def _parse(command: str):
    replacements = {
        "<project>": "ProjectDocs",
        "<identity>": "configured-public:ProjectDocs",
        "<helper-cache>": ".cache/attack-surface",
        "<repo>": "source-repository",
    }
    for marker, value in replacements.items():
        command = command.replace(marker, value)
    argv = shlex.split(command)
    assert argv[0] == "llm-wiki"
    return cli._build_parser().parse_args(argv[1:])


def _projection_selection(args) -> tuple[object, ...]:
    return (
        args.profile,
        args.site_name,
        args.knowledge_metadata,
        args.knowledge_profile,
        args.public_repository_identity,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _wiki(root: Path, name: str = "wiki") -> Path:
    wiki = root / name
    _write(wiki / "index.md", "# Index\n\n[Service](modules/service.md)\n")
    _write(wiki / "log.md", "# Log\n\n")
    _write(wiki / "modules" / "service.md", "# Service\n\n")
    return wiki


def test_publish_user_hosted_and_file_commands_preserve_selection():
    parsed = [_parse(command) for command in _bash_commands(_read(PUBLISH_SKILL))]
    user = [
        args
        for args in parsed
        if args.command == "site" and args.profile == "user"
    ]

    assert len(user) == 6
    assert {_projection_selection(args) for args in user} == {
        (
            "user",
            "ProjectDocs",
            "summary",
            "public-portable",
            "configured-public:ProjectDocs",
        )
    }

    hosted = [args for args in user if args.out_dir == "site"]
    direct_file = [args for args in user if args.out_dir == "site-file"]
    assert [args.site_action for args in hosted] == ["export", "check", "check"]
    assert [args.site_action for args in direct_file] == ["export", "check", "check"]

    hosted_export = hosted[0]
    hosted_built = hosted[-1]
    file_export = direct_file[0]
    file_built = direct_file[-1]
    assert hosted_export.format == file_export.format == "mkdocs"
    assert hosted_export.file_friendly is False
    assert file_export.file_friendly is True
    assert hosted_built.link_mode == "http"
    assert file_built.link_mode == "file"
    assert hosted_built.built_site_dir == "_site-http"
    assert file_built.built_site_dir == "_site-file"
    assert hosted_built.built_site_dir != file_built.built_site_dir
    assert hosted_built.format == file_built.format == "mkdocs"


def test_publish_reference_and_ci_built_checks_keep_explicit_contract():
    reference = _read(PUBLISH_REFERENCE)
    commands = [
        *_bash_commands(reference),
        *_yaml_run_commands(reference),
    ]
    parsed = [_parse(command) for command in commands]

    reference_site = [
        args
        for args in parsed
        if args.command == "site"
        and args.profile == "reference"
        and args.wiki_dir == "docs/llm_wiki"
    ]
    built = [
        args
        for args in reference_site
        if args.site_action == "check" and args.built_site_dir
    ]
    assert built
    assert all(args.link_mode == "http" for args in built)
    assert all(args.profile == "reference" for args in built)
    assert all(args.site_name is None for args in built)

    ci = [_parse(command) for command in _yaml_run_commands(reference)]
    assert [args.site_action for args in ci] == ["export", "check", "check"]
    assert all(args.profile == "reference" for args in ci)
    assert ci[-1].built_site_dir == "_site-http"
    assert ci[-1].link_mode == "http"


def test_final_user_check_applies_user_only_gate(tmp_path):
    wiki = _wiki(tmp_path)
    out = tmp_path / "site"
    built = tmp_path / "_site-http"
    export_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        format="mkdocs",
        profile="reference",
    )
    _write(built / "index.html", "<html><body>Reference build</body></html>\n")
    _write(
        built / SITE_PUBLICATION_MARKER,
        (out / SITE_PUBLICATION_MARKER).read_text(encoding="utf-8"),
    )

    reference = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
        profile="reference",
    )
    user = check_site_mirror(
        wiki_dir=wiki,
        out_dir=out,
        built_site_dir=built,
        link_mode="http",
        profile="user",
        site_name="ProjectDocs",
    )

    assert reference.ok is True
    assert user.ok is False
    assert any(issue["category"] == "missing_user_guides" for issue in user.issues)


def test_doc_hub_conservative_surface_is_overwritten_and_not_navigated(tmp_path):
    root = tmp_path / "sources"
    _wiki(root, "alpha")
    _wiki(root, "beta")
    out = tmp_path / "site"

    export_site_hub(wiki_root=root, out_dir=out, format="mkdocs")
    _write(out / "overview.md", "# Overview\n\n[Broken](missing.md)\n")
    with (out / "index.md").open("a", encoding="utf-8") as stream:
        stream.write("\n[Overview](overview.md)\n")

    export_site_hub(wiki_root=root, out_dir=out, format="mkdocs")

    assert "overview.md" not in (out / "index.md").read_text(encoding="utf-8")
    assert "overview.md" not in (out / "mkdocs.yml").read_text(encoding="utf-8")
    assert (out / "overview.md").is_file()
    assert check_site_hub(wiki_root=root, out_dir=out).ok is True

    docusaurus_out = tmp_path / "site-docusaurus"
    export_site_hub(
        wiki_root=root,
        out_dir=docusaurus_out,
        format="docusaurus",
    )
    sidebar = json.loads(
        (docusaurus_out / "sidebars.json").read_text(encoding="utf-8")
    )
    assert "overview" not in json.dumps(sidebar)

    combined = f"{_read(HUB_SKILL)}\n{_read(HUB_REFERENCE)}".lower()
    assert "no canonical hub-overview input" in combined
    assert "do not write an overview page" in combined
    assert "do not fabricate" in combined


def test_deep_extract_http_only_fixture_enters_worklist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(
        tmp_path / "app.py",
        textwrap.dedent(
            """\
            @app.get("/health")
            def health():
                return {"ok": True}
            """
        ),
    )

    payload = extract_cmd.build_extract_payload(
        ".",
        deep=True,
        read_only=True,
    ).payload

    assert [(item["category"], item["symbol"]) for item in payload["entrypoints"]] == [
        ("http", "health")
    ]
    assert [flow["id"] for flow in payload["data_flows"]] == ["http-health"]
    assert "| `http` |" in _read(ATTACK_REFERENCE)


def test_deep_extract_without_entrypoints_is_valid_zero_emitted_case(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "constants.py", "VALUE = 1\n")

    payload = extract_cmd.build_extract_payload(
        ".",
        deep=True,
        read_only=True,
    ).payload

    assert payload["schema_version"] == "llm-wiki-extract/v1"
    assert "entrypoints" not in payload
    assert payload["data_flows"] == []
    combined = f"{_read(ATTACK_SKILL)}\n{_read(ATTACK_REFERENCE)}"
    assert "zero emitted entry-point rows" in combined
    assert "Entrypoint/analyzer completeness is unknown" in combined


def test_attack_surface_documents_every_emitted_boundary_kind(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    _write(
        tmp_path / "effects.py",
        textwrap.dedent(
            """\
            import logging
            import os
            import requests
            import subprocess

            def filesystem_read(path):
                return path.read_text()

            def filesystem_write(path):
                path.write_text("value")

            def environment_read():
                return os.getenv("TOKEN")

            def environment_write():
                os.environ["TOKEN"] = "value"

            def network():
                return requests.get("https://example.invalid")

            def process():
                return subprocess.run(["true"])

            def mutation(items):
                items.append("value")

            def output():
                print("value")

            def logging_effect():
                logging.info("value")
            """
        ),
    )

    inventory = extract_cmd.get_inventory(".", deep=True)
    emitted = {
        effect["kind"]
        for function in inventory["effects.py"]["functions"]
        for effect in function.get("data_effects", {}).get("boundary_effects", [])
    }
    documented = set(
        re.findall(r"^\| `([^`]+)` \|", _read(ATTACK_REFERENCE), flags=re.MULTILINE)
    )

    assert emitted == BOUNDARY_KINDS
    assert BOUNDARY_KINDS <= documented


def test_legacy_bounded_flow_counts_are_emitted_rows_not_coverage():
    flow = {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "service.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {
                "depth": 0 if index == 0 else 1,
                "file": "service.py",
                "symbol": "run" if index == 0 else f"step_{index}",
                "kind": "entry" if index == 0 else "internal",
            }
            for index in range(13)
        ],
        "modules_touched": ["service.py"],
        "truncated": True,
    }

    emitted = analyze_data_flow({}, flow, [])

    assert len(emitted["steps"]) == 12
    assert {gap["kind"] for gap in emitted["gaps"]} == {
        "step_limit",
        "truncated_flow",
    }
    assert emitted["truncated"] is True
    assert "coverage" not in emitted
    combined = f"{_read(ATTACK_SKILL)}\n{_read(ATTACK_REFERENCE)}"
    assert "emitted rows" in combined
    assert "Only report observed/emitted/omitted totals" in combined
    assert "complete analyzer coverage" in combined


def test_plugin_limitation_remains_unknown_and_helper_flags_parse(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "api.py", '__all__ = ["run"]\n\ndef run():\n    return 1\n')
    _write(tmp_path / ".llm-wiki" / "plugins.lock.json", "{not-json\n")

    with pytest.raises(PluginError, match="Invalid plugin lockfile"):
        extract_cmd.build_extract_payload(
            ".",
            deep=True,
            read_only=True,
        )

    combined = f"{_read(ATTACK_SKILL)}\n{_read(ATTACK_REFERENCE)}"
    assert "Missing/failed plugins" in combined
    assert "coverage limitations" in combined
    assert "inert evidence" in combined

    parser = cli._build_parser()
    prepared = parser.parse_args(
        [
            "prepare-extractors",
            "--src-dir",
            ".",
            "--cache-dir",
            ".cache/attack-surface",
        ]
    )
    extracted = parser.parse_args(
        [
            "extract",
            "--src-dir",
            ".",
            "--deep",
            "--read-only",
            "--helper-cache-dir",
            ".cache/attack-surface",
        ]
    )
    assert prepared.cache_dir == extracted.helper_cache_dir


@pytest.mark.parametrize("path", [PUBLISH_SKILL, PUBLISH_REFERENCE, HUB_SKILL])
def test_documented_site_commands_parse_against_real_cli(path):
    commands = _bash_commands(_read(path))
    site_commands = [
        command for command in commands if command.startswith("llm-wiki site ")
    ]

    assert site_commands
    assert all(_parse(command).command == "site" for command in site_commands)
