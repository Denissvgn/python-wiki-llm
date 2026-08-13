"""Contract tests for the bounded infrastructure-review skill."""

from __future__ import annotations

import textwrap

from llm_wiki_cli.commands.bootstrap_cmd import _generate_infrastructure_md
from llm_wiki_cli.commands.extract_cmd import (
    _parse_compose,
    _parse_dockerfile,
    get_docker_inventory,
)
from llm_wiki_cli.services import skills
from llm_wiki_cli.services.infrastructure_inventory import (
    get_yaml_infrastructure_inventory,
    parse_github_actions_workflow,
    parse_kubernetes_manifest,
)


def _skill_text() -> str:
    skill_dir = skills.BUNDLED_SKILLS_ROOT / "infra-review"
    return "\n".join(
        (skill_dir / filename).read_text(encoding="utf-8")
        for filename in ("SKILL.md", "reference.md")
    )


def test_infra_review_contract_bounds_incremental_freshness_and_outcomes():
    text = _skill_text()
    normalized = " ".join(text.split())

    assert "incremental observation" in text.lower()
    assert "Ordinary `llm-wiki sync` incrementally regenerates" in normalized
    assert "generation_inputs.infrastructure" in text
    assert "source-content hash" in text
    assert "observation hash" in text
    assert "unsupported YAML" in text
    assert "removal/move tombstones" in text
    assert "current raw source" in text.lower()
    assert "fresh dedicated infrastructure extractor" in text

    assert "zero findings" in text.lower()
    assert "zero discovered artifacts" in text.lower()
    assert "page-screened only" in text
    assert "unsupported discovery" in text
    assert "Zero `infrastructure/` pages alone proves none of them" in normalized

    assert "`## Notes` is the one supported semantic section" in normalized
    assert "unsupported custom headings" in normalized
    assert "A report-only review makes no wiki change and needs no sync" in normalized
    assert "strict lint correctly fails until the owning sync re-anchors it" in normalized
    assert "llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki" in text
    assert "PAYMENTS_TOKEN=<redacted>" in text
    assert "<private-endpoint>" in text


def test_infra_review_routes_native_policy_and_keeps_trusted_plugin_kernel():
    text = _skill_text()
    normalized = " ".join(text.split())

    for expected in (
        "`availability`",
        "reason",
        "`freshness_evaluated`",
        "`nonsemantic-source-change`",
        "`ready` with live `current`",
        "bounded `found: false`",
        "trusted, unsandboxed code",
    ):
        assert expected in normalized
    assert skills.SKILL_DEPENDENCIES["infra-review"] == (
        skills.REFERENCE_SKILL_ID,
    )
    for root in (".claude/skills", ".llm-wiki/skills"):
        assert (
            f"{root}/wiki-reference/references/knowledge-consumption.md" in text
        )

    common = (
        skills.BUNDLED_SKILLS_ROOT
        / skills.REFERENCE_SKILL_ID
        / "references/knowledge-consumption.md"
    ).read_text(encoding="utf-8")
    normalized_common = " ".join(common.split())
    assert "snapshot-only" in normalized_common
    assert (
        "Do not upgrade them to truth, approval, security, or runtime behavior"
        in normalized_common
    )
    assert "Neither mode initializes, repairs, or persists governance" in normalized_common


def test_docker_and_compose_page_screen_matches_parser_renderer_boundary():
    text = _skill_text()
    docker_source = textwrap.dedent(
        """\
        FROM python:3.12-slim
        USER 10001
        RUN install-runtime
        EXPOSE 8080
        ENV API_TOKEN=placeholder-sensitive-value
        VOLUME /data
        """
    )
    docker_page = _generate_infrastructure_md(
        "Dockerfile", _parse_dockerfile(docker_source)
    )

    assert "`python:3.12-slim`" in docker_page
    assert "`8080`" in docker_page
    assert "`API_TOKEN`" in docker_page
    assert "`/data`" in docker_page
    assert "USER 10001" not in docker_page
    assert "install-runtime" not in docker_page
    assert "`USER`" in text
    assert "`RUN`" in text

    compose_source = textwrap.dedent(
        """\
        services:
          api:
            image: example/api:latest
            privileged: true
            ports:
              - "8080:8080"
            volumes:
              - "/var/run/docker.sock:/var/run/docker.sock"
            environment:
              - "API_TOKEN=placeholder-sensitive-value"
        """
    )
    compose_page = _generate_infrastructure_md(
        "compose.yml", _parse_compose(compose_source)
    )

    assert "`example/api:latest`" in compose_page
    assert "`8080:8080`" in compose_page
    assert "`/var/run/docker.sock:/var/run/docker.sock`" in compose_page
    assert "`API_TOKEN=placeholder-sensitive-value`" in compose_page
    assert "privileged" not in compose_page
    assert "`privileged`" in text


def test_kubernetes_resources_and_actions_uses_are_page_visible_but_controls_are_not():
    text = _skill_text()
    kubernetes_source = textwrap.dedent(
        """\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: api
        spec:
          template:
            spec:
              hostNetwork: true
              containers:
                - name: api
                  image: example/api:latest
                  securityContext:
                    privileged: true
                  resources:
                    requests:
                      cpu: 250m
                    limits:
                      memory: 512Mi
        """
    )
    kubernetes_page = _generate_infrastructure_md(
        "k8s/deployment.yaml",
        parse_kubernetes_manifest(kubernetes_source),
    )

    assert "`cpu=250m`" in kubernetes_page
    assert "`memory=512Mi`" in kubernetes_page
    assert "securityContext" not in kubernetes_page
    assert "hostNetwork" not in kubernetes_page
    assert "container resource `requests` and `limits`" in text
    assert "`securityContext`" in text

    actions_source = textwrap.dedent(
        """\
        name: CI
        on: push
        permissions:
          contents: write
        jobs:
          test:
            runs-on: ubuntu-latest
            permissions:
              packages: write
            steps:
              - name: Checkout
                uses: actions/checkout@v4
        """
    )
    actions_page = _generate_infrastructure_md(
        ".github/workflows/ci.yml",
        parse_github_actions_workflow(actions_source),
    )

    assert "uses `actions/checkout@v4`" in actions_page
    assert "permissions" not in actions_page
    assert "Because `uses` is rendered" in " ".join(text.split())
    assert "workflow- and job-level `permissions:`" in text


def test_discovery_fixtures_distinguish_supported_alternate_and_empty_roots(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "name: CI\non: push\njobs:\n  test:\n", encoding="utf-8"
    )
    k8s = tmp_path / "k8s"
    k8s.mkdir()
    (k8s / "deployment.yaml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api\n",
        encoding="utf-8",
    )
    deploy = tmp_path / "deploy"
    deploy.mkdir()
    (deploy / "alternate.yaml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: alternate\n",
        encoding="utf-8",
    )
    nested = tmp_path / "ops"
    nested.mkdir()
    (nested / "Dockerfile.worker").write_text("FROM alpine:3.20\n", encoding="utf-8")
    (nested / "stack.yaml").write_text(
        "services:\n  api:\n    image: example/api:latest\n", encoding="utf-8"
    )

    docker_inventory = get_docker_inventory(str(tmp_path))
    yaml_inventory = get_yaml_infrastructure_inventory(tmp_path)

    assert sorted(docker_inventory) == [
        "ops/Dockerfile.worker",
        "ops/stack.yaml",
    ]
    assert sorted(yaml_inventory) == [
        ".github/workflows/ci.yml",
        "k8s/deployment.yaml",
    ]
    assert "deploy/alternate.yaml" not in yaml_inventory
    assert "alternate roots such as `deploy/`" in _skill_text()

    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "README.md").write_text("# Empty\n", encoding="utf-8")
    assert get_docker_inventory(str(empty)) == {}
    assert get_yaml_infrastructure_inventory(empty) == {}
