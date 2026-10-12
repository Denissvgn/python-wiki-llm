"""Named YAML format recognition and deliberately narrow visible summaries."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from llm_wiki_cli.services.yaml_formats import parse_extended_yaml


def _parse(path: str, text: str) -> dict | None:
    return parse_extended_yaml(path, list(yaml.load_all(text, Loader=yaml.BaseLoader)))


@pytest.mark.parametrize(
    ("path", "text", "family", "section", "expected"),
    [
        (
            "tools/action.yml",
            "name: Package\ninputs: {token: {default: PRIVATE}}\noutputs: {artifact: {value: PRIVATE}}\n"
            "runs: {using: composite, steps: [{name: Build, uses: vendor/action@v1}, {run: 'echo PRIVATE'}]}\n",
            "github_action",
            "Action references",
            ["vendor/action@v1"],
        ),
        (
            ".gitlab-ci.yml",
            "stages: [build, deploy]\ninclude: [{local: jobs.yml}]\n"
            "build: {stage: build, script: [echo PRIVATE]}\n",
            "gitlab_ci",
            "Jobs",
            ["build"],
        ),
        (
            ".circleci/config.yaml",
            "version: 2.1\njobs: {build: {steps: [{run: echo PRIVATE}]}}\n"
            "workflows: {main: {jobs: [build]}}\norbs: {node: circleci/node@5}\n",
            "circleci",
            "Workflows",
            ["main"],
        ),
        (
            "azure-pipelines.yaml",
            "stages: [{stage: Deploy, jobs: [{deployment: Web, steps: [{template: steps.yml},"
            "{task: Publish@1}, {bash: 'echo PRIVATE', displayName: Publish}]}]}]\n",
            "azure_pipelines",
            "Jobs",
            ["Web"],
        ),
        (
            "deploy/kustomization.yaml",
            "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n"
            "resources: [deployment.yaml]\nsecretGenerator: [{name: auth, literals: [password=PRIVATE]}]\n",
            "kustomize",
            "Resources",
            ["deployment.yaml"],
        ),
        (
            "charts/api/Chart.yaml",
            "apiVersion: v2\nname: api\nversion: 1.2.3\nappVersion: '2026.01'\n"
            "dependencies: [{name: redis, version: '1.0', repository: PRIVATE}]\n",
            "helm_chart",
            "Dependencies",
            ["redis"],
        ),
        (
            "automation/playbooks/deploy.yml",
            "- name: Deploy\n  hosts: web\n  vars: {password: PRIVATE}\n"
            "  roles: [common, {role: api, password: PRIVATE}]\n"
            "  tasks: [{name: Install, block: [{name: Restart, command: echo PRIVATE}]}]\n",
            "ansible_playbook",
            "Tasks",
            ["Install", "Restart"],
        ),
    ],
)
def test_supported_families_preserve_names_and_references_without_values(
    path, text, family, section, expected
):
    result = _parse(path, text)
    assert result is not None
    assert result["type"] == "yaml_format"
    assert result["yaml_format"] == family
    assert result["sections"][section] == expected
    assert result["advisories"] == []
    assert "PRIVATE" not in repr(result)


@pytest.mark.parametrize(
    ("using", "runtime", "section", "expected"),
    [
        (
            "node20",
            "main: dist/index.js\n  pre: dist/pre.js",
            "Entry points",
            ["dist/index.js", "dist/pre.js"],
        ),
        ("node24", "main: index.js", "Entry points", ["index.js"]),
        ("docker", "image: Dockerfile\n  args: [PRIVATE]", "Image", ["Dockerfile"]),
    ],
)
def test_github_action_supports_javascript_and_docker_runtimes(
    using, runtime, section, expected
):
    result = _parse(
        "action.yaml", f"name: Build\nruns:\n  using: {using}\n  {runtime}\n"
    )
    assert result is not None
    assert result["sections"][section] == expected
    assert result["sections"]["Runtime"] == [using]
    assert "PRIVATE" not in repr(result)


def test_block_flow_indent_and_alias_syntax_yield_identical_named_summary():
    block = """name: Build
runs:
    using: composite
    steps:
        - &build
          name: Compile
          uses: vendor/compile@v2
        - *build
"""
    flow = "name: Build\nruns: {using: composite, steps: [{name: Compile, uses: vendor/compile@v2}]}\n"
    assert _parse("action.yml", block) == _parse("action.yml", flow)


@pytest.mark.parametrize(
    ("path", "text"),
    [
        ("arbitrary.yml", "name: Build\nruns: {using: composite, steps: []}\n"),
        ("action.yml", "name: Build\nruns: {using: unknown, main: index.js}\n"),
        ("action.yml", "name: Build\nruns: {using: node20}\n"),
        ("action.yml", "name: Build\nruns: {using: composite, steps: malformed}\n"),
        ("action.yml", "name: Build\nruns: {using: docker}\n"),
        (".gitlab-ci.yml", "variables: {password: PRIVATE}\n"),
        ("config.yml", "build: {script: echo hello}\n"),
        ("not.gitlab/citrus/jobs.yml", "build: {script: echo hello}\n"),
        (".circleci/config.yml", "version: 1\njobs: {build: {}}\n"),
        (".circleci/config.yml", "version: 2.1\npassword: PRIVATE\n"),
        ("azure-pipelines.yml", "steps: [unrelated]\n"),
        ("azure-pipelines.yml", "database: {host: localhost}\n"),
        ("kustomization.yaml", "name: app\nvariables: {password: PRIVATE}\n"),
        ("Chart.yaml", "name: app\nversion: 1.0\n"),
        ("charts/api/values.yaml", "apiVersion: v2\nname: api\nversion: 1.0\n"),
        (
            "charts/api/templates/deployment.yaml",
            "apiVersion: apps/v1\nkind: Deployment\n",
        ),
        ("playbooks/deploy.yml", "- name: hello\n  command: echo hi\n"),
        ("playbook.yml", "- hosts: {invalid: host}\n"),
        ("settings.yml", "- hosts: web\n  roles: [api]\n"),
    ],
)
def test_unrelated_paths_and_invalid_format_shapes_remain_unrecognized(path, text):
    assert _parse(path, text) is None


def test_mixed_documents_are_not_silently_collapsed_into_one_format():
    document = {"name": "Build", "runs": {"using": "composite", "steps": []}}
    assert parse_extended_yaml("action.yml", [document, {"database": {}}]) is None
    assert parse_extended_yaml("action.yml", [document, deepcopy(document)]) is None
    assert parse_extended_yaml("action.yml", [None, document, None]) is not None
    assert parse_extended_yaml("action.yml", []) is None


def test_parsing_does_not_mutate_loaded_documents_and_is_deterministic():
    documents = [
        {
            "name": "Build",
            "inputs": {"token": {"default": "PRIVATE"}},
            "runs": {"using": "composite", "steps": []},
        }
    ]
    before = deepcopy(documents)
    first = parse_extended_yaml("tools\\action.yml", documents)
    assert first == parse_extended_yaml("tools/action.yml", documents)
    assert documents == before


@pytest.mark.parametrize(
    "relative",
    ["integrations/github-action/action.yml", "integrations/wiki-integrity/action.yml"],
)
def test_current_project_composite_actions_are_recognized(relative):
    text = (Path(__file__).resolve().parents[1] / relative).read_text(encoding="utf-8")
    result = _parse(relative, text)
    assert result is not None
    assert result["yaml_format"] == "github_action"
    assert result["sections"]["Runtime"] == ["composite"]
    assert result["sections"]["Steps"]
    assert "src-dir" in result["sections"]["Inputs"]


def test_secondary_named_paths_and_sections_are_preserved():
    gitlab = _parse(
        ".gitlab/ci/deploy.yaml", "deploy: {extends: [.common], trigger: child.yml}\n"
    )
    assert gitlab is not None
    assert gitlab["sections"]["Job dependencies"] == [".common"]
    azure = _parse(
        "azure-pipelines-build.yml",
        "jobs: [{job: Build, steps: [{task: Compile@2}, {template: reuse.yml}]}]\n",
    )
    assert azure is not None
    assert azure["sections"]["Templates"] == ["reuse.yml"]
    assert azure["sections"]["Tasks"] == ["Compile@2"]
    kustomize = _parse(
        "kustomization.yaml",
        "resources: [base]\nconfigMapGenerator: [{name: app, literals: [value=PRIVATE]}]\npatches: [{path: patch.yml}]\n",
    )
    assert kustomize is not None
    assert kustomize["sections"]["configMapGenerator"] == ["app"]
    assert kustomize["sections"]["Patch files"] == ["patch.yml"]


def test_include_only_ci_and_import_only_playbooks_keep_file_references():
    gitlab = _parse(".gitlab-ci.yml", "include: [{template: Python.gitlab-ci.yml}]\n")
    assert gitlab is not None
    assert gitlab["sections"] == {"Includes": ["Python.gitlab-ci.yml"]}
    ansible = _parse(
        "site.yml", "- import_playbook: web.yml\n- import_playbook: workers.yml\n"
    )
    assert ansible is not None
    assert ansible["sections"] == {"Imported playbooks": ["web.yml", "workers.yml"]}
