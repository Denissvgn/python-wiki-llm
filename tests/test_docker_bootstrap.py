"""Tests for Docker infrastructure page generation in bootstrap_cmd."""

from __future__ import annotations

import ast
import inspect
import os
import textwrap


from llm_wiki_cli.commands.bootstrap_cmd import (
    _generate_docker_md,
    _generate_dockerfile_md,
)
from llm_wiki_cli.commands.extract_cmd import _parse_dockerfile, _parse_compose


class TestGenerateDockerfileMd:
    def test_dockerfile_renderer_stays_decomposed(self):
        source = textwrap.dedent(inspect.getsource(_generate_dockerfile_md))
        function_node = ast.parse(source).body[0]
        assert isinstance(function_node, ast.FunctionDef)
        body = list(function_node.body)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]

        first_body_line = min(stmt.lineno for stmt in body)
        last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
        body_lines = last_body_line - first_body_line + 1

        assert body_lines <= 25

    def test_single_stage(self):
        info = _parse_dockerfile(
            "FROM python:3.12-slim\nEXPOSE 8000\nCMD python main.py\n"
        )
        md = _generate_docker_md("Dockerfile", info)
        assert "# Dockerfile" in md
        assert "`python:3.12-slim`" in md
        assert "`8000`" in md
        assert "python main.py" in md

    def test_multi_stage_has_table(self):
        text = "FROM python:3.12 AS builder\nFROM python:3.12-slim AS runtime\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Build Stages" in md
        assert "`builder`" in md
        assert "`runtime`" in md

    def test_env_vars_section(self):
        text = "FROM alpine\nENV APP_ENV=production\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Environment Variables" in md
        assert "`APP_ENV`" in md
        assert "`production`" in md

    def test_volumes_section(self):
        text = 'FROM alpine\nVOLUME ["/data"]\n'
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Volumes" in md
        assert "`/data`" in md

    def test_build_args_section(self):
        text = "FROM alpine\nARG VERSION=1.0\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Build Arguments" in md
        assert "`VERSION`" in md

    def test_copy_cross_reference(self):
        text = "FROM alpine\nCOPY main.py /app/\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info, module_stems={"main"})
        assert "[`main.py`](../modules/main.md)" in md

    def test_copy_cross_reference_uses_module_page_map(self):
        """COPY links must use collision-aware module page names, not file stems."""
        text = "FROM alpine\nCOPY sidecars/workspace_server.py /app/\n"
        info = _parse_dockerfile(text)
        module_links = {
            "sidecars/workspace_server.py": "sidecars_workspace_server",
            "sidecars/typescript/src/server.ts": "sidecars_typescript_src_server",
        }

        md = _generate_docker_md(
            "docker/Dockerfile.workspace", info, module_links=module_links
        )

        assert (
            "[`sidecars/workspace_server.py`](../modules/sidecars_workspace_server.md)"
            in md
        )
        assert "../modules/server.md" not in md

    def test_copy_cross_reference_prefers_nested_docker_context(self):
        """A Dockerfile under a nested docker/ dir should link within that worktree."""
        text = "FROM alpine\nCOPY sidecars/workspace_server.py /app/\n"
        info = _parse_dockerfile(text)
        module_links = {
            "sidecars/workspace_server.py": "sidecars_workspace_server",
            ".claude/worktrees/agent-strict-instructions/sidecars/workspace_server.py": "agent-strict-instructions_sidecars_workspace_server",
        }

        md = _generate_docker_md(
            ".claude/worktrees/agent-strict-instructions/docker/Dockerfile.workspace",
            info,
            module_links=module_links,
        )

        assert (
            "[`sidecars/workspace_server.py`]"
            "(../modules/agent-strict-instructions_sidecars_workspace_server.md)"
        ) in md

    def test_copy_cross_reference_leaves_ambiguous_suffix_unlinked(self):
        """Suffix-only matches should not create a link when multiple pages match."""
        text = "FROM alpine\nCOPY workspace_server.py /app/\n"
        info = _parse_dockerfile(text)
        module_links = {
            "sidecars/workspace_server.py": "sidecars_workspace_server",
            "other/workspace_server.py": "other_workspace_server",
        }

        md = _generate_docker_md("Dockerfile", info, module_links=module_links)

        assert "`workspace_server.py`" in md
        assert "../modules/" not in md

    def test_copy_no_cross_reference(self):
        text = "FROM alpine\nCOPY config.txt /app/\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info, module_stems={"main"})
        assert "`config.txt`" in md
        assert "../modules/" not in md

    def test_healthcheck_section(self):
        text = "FROM alpine\nHEALTHCHECK CMD curl -f http://localhost/\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "Healthcheck" in md


class TestGenerateComposeMd:
    def test_basic_services(self):
        text = textwrap.dedent("""\
            services:
              web:
                build: .
                ports:
                  - "8000:8000"
              db:
                image: postgres:16
        """)
        info = _parse_compose(text)
        md = _generate_docker_md("docker-compose.yml", info)
        assert "# docker-compose.yml" in md
        assert "## Services" in md
        assert "`web`" in md
        assert "`db`" in md

    def test_per_service_detail(self):
        text = textwrap.dedent("""\
            services:
              app:
                image: myapp:latest
                command: python run.py
        """)
        info = _parse_compose(text)
        md = _generate_docker_md("docker-compose.yml", info)
        assert "### app" in md
        assert "`myapp:latest`" in md
        assert "python run.py" in md

    def test_networks_and_volumes(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
            networks:
              frontend:
            volumes:
              pgdata:
        """)
        info = _parse_compose(text)
        md = _generate_docker_md("docker-compose.yml", info)
        assert "## Networks" in md
        assert "`frontend`" in md
        assert "## Named Volumes" in md
        assert "`pgdata`" in md


class TestBootstrapInfrastructureIntegration:
    """Integration test: bootstrap generates infrastructure pages from Docker files."""

    def test_bootstrap_creates_infra_pages(self, tmp_path):
        """Run bootstrap on a project with Docker files and verify pages."""
        proj = tmp_path / "proj"
        proj.mkdir()

        # Create a Python file so bootstrap has something
        (proj / "app.py").write_text("class App:\n    pass\n")

        # Create Docker files
        (proj / "Dockerfile").write_text("FROM python:3.12\nEXPOSE 8000\n")
        (proj / "docker-compose.yml").write_text(
            'services:\n  web:\n    build: .\n    ports:\n      - "8000:8000"\n'
        )

        # Bootstrap creates the wiki dir inside the current project root.
        wiki = proj / "docs" / "llm_wiki"

        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            from llm_wiki_cli.commands import bootstrap_cmd
            import argparse

            args = argparse.Namespace(
                src_dir=".",
                wiki_dir=str(wiki),
                overwrite=False,
                depth="full",
                skip_workflows=True,
            )
            bootstrap_cmd.run(args)

            # Check infrastructure pages created
            infra_dir = wiki / "infrastructure"
            infra_pages = list(infra_dir.glob("*.md"))
            page_names = {p.stem for p in infra_pages}
            assert "Dockerfile" in page_names
            assert "docker-compose_yml" in page_names

            # Check index.md has Infrastructure section
            index_content = (wiki / "index.md").read_text(encoding="utf-8")
            assert "## Infrastructure" in index_content
            assert "Dockerfile" in index_content
            assert "docker-compose_yml" in index_content
        finally:
            os.chdir(old_cwd)

    def test_bootstrap_lint_passes_with_collision_aware_copy_links(
        self, tmp_path, capsys
    ):
        """A freshly bootstrapped wiki must not emit broken Docker COPY links."""
        proj = tmp_path / "proj"
        proj.mkdir()

        (proj / "sidecars").mkdir()
        (proj / "other").mkdir()
        (proj / "docker").mkdir()
        (proj / "sidecars" / "workspace_server.py").write_text(
            "class WorkspaceServer:\n    pass\n"
        )
        (proj / "sidecars" / "server.py").write_text("class Server:\n    pass\n")
        (proj / "other" / "workspace_server.py").write_text(
            "class OtherWorkspaceServer:\n    pass\n"
        )
        (proj / "docker" / "Dockerfile.workspace").write_text(
            "FROM alpine\nCOPY sidecars/workspace_server.py /app/workspace_server.py\n"
        )

        wiki = proj / "docs" / "llm_wiki"

        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd
            import argparse

            args = argparse.Namespace(
                src_dir=".",
                wiki_dir=str(wiki),
                overwrite=False,
                depth="shallow",
                skip_workflows=True,
            )
            bootstrap_cmd.run(args)

            infra = (
                wiki / "infrastructure" / "docker_Dockerfile_workspace.md"
            ).read_text(encoding="utf-8")
            assert "../modules/sidecars_workspace_server.md" in infra
            assert "../modules/server.md" not in infra

            lint_cmd.run(argparse.Namespace(wiki_dir=str(wiki), src_dir="."))
            output = capsys.readouterr().out
            assert "Lint passed" in output
        finally:
            os.chdir(old_cwd)

    def test_bootstrap_marks_copied_shell_scripts_as_unsupported_sources(
        self, tmp_path
    ):
        """Docker pages should make copied unsupported deployment scripts visible."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "app.py").write_text("class App:\n    pass\n", encoding="utf-8")
        docker = proj / "docker"
        docker.mkdir()
        (docker / "entrypoint.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (docker / "generate-config.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (docker / "Dockerfile").write_text(
            textwrap.dedent("""\
                FROM alpine
                COPY entrypoint.sh /usr/local/bin/entrypoint.sh
                COPY generate-config.sh /usr/local/bin/generate-config.sh
                ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
            """),
            encoding="utf-8",
        )

        wiki = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            from llm_wiki_cli.commands import bootstrap_cmd
            import argparse

            bootstrap_cmd.run(
                argparse.Namespace(
                    src_dir=".",
                    wiki_dir=str(wiki),
                    overwrite=False,
                    depth="shallow",
                    skip_workflows=True,
                )
            )

            infra = (wiki / "infrastructure" / "docker_Dockerfile.md").read_text(
                encoding="utf-8"
            )
            assert "## Unsupported Copied Sources" in infra
            assert "`entrypoint.sh`" in infra
            assert "`docker/entrypoint.sh`" in infra
            assert "`generate-config.sh`" in infra
            assert "`docker/generate-config.sh`" in infra
            assert "Shell extraction is not yet supported" in infra
        finally:
            os.chdir(old_cwd)

    def test_bootstrap_creates_actions_and_kubernetes_infrastructure_pages(
        self, tmp_path, capsys
    ):
        """Bootstrap documents deployment YAML without mixing it into app workflows."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "app.py").write_text("class App:\n    pass\n")
        workflows = proj / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text(
            textwrap.dedent("""\
                name: CI
                on: push
                jobs:
                  test:
                    runs-on: ubuntu-latest
                    steps:
                      - name: Run tests
                        run: pytest
            """)
        )
        k8s = proj / "k8s"
        k8s.mkdir()
        (k8s / "deployment.yaml").write_text(
            textwrap.dedent("""\
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: api
                spec:
                  replicas: 2
                  template:
                    spec:
                      containers:
                        - name: api
                          image: example/api:latest
            """)
        )
        (k8s / "service.yaml").write_text(
            textwrap.dedent("""\
                apiVersion: v1
                kind: Service
                metadata:
                  name: api
                spec:
                  type: ClusterIP
                  ports:
                    - port: 80
                      targetPort: 8000
            """)
        )

        wiki = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd
            import argparse

            bootstrap_cmd.run(
                argparse.Namespace(
                    src_dir=".",
                    wiki_dir=str(wiki),
                    overwrite=False,
                    depth="full",
                    skip_workflows=True,
                )
            )

            assert (wiki / "infrastructure" / "_github_workflows_ci_yml.md").exists()
            assert (wiki / "infrastructure" / "k8s_deployment_yaml.md").exists()
            assert (wiki / "infrastructure" / "k8s_service_yaml.md").exists()

            actions_md = (
                wiki / "infrastructure" / "_github_workflows_ci_yml.md"
            ).read_text(encoding="utf-8")
            assert "# GitHub Actions: CI" in actions_md
            assert "`test`" in actions_md
            assert "Run tests" in actions_md

            deployment_md = (
                wiki / "infrastructure" / "k8s_deployment_yaml.md"
            ).read_text(encoding="utf-8")
            assert "# Kubernetes: Deployment api" in deployment_md
            assert "`example/api:latest`" in deployment_md

            index_content = (wiki / "index.md").read_text(encoding="utf-8")
            assert "GitHub Actions: CI" in index_content
            assert "Kubernetes: Deployment api" in index_content
            assert "## Workflows" not in index_content

            lint_cmd.run(argparse.Namespace(wiki_dir=str(wiki), src_dir="."))
            assert "Lint passed" in capsys.readouterr().out
        finally:
            os.chdir(old_cwd)

    def test_bootstrap_creates_runtime_config_yaml_infrastructure_pages(
        self, tmp_path, capsys
    ):
        """Bootstrap documents recognized runtime/config YAML but ignores generic YAML."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "app.py").write_text("class App:\n    pass\n", encoding="utf-8")
        (proj / "prometheus.yml").write_text(
            textwrap.dedent("""\
                global:
                  scrape_interval: 15s
                rule_files:
                  - recording_rules.yml
                scrape_configs:
                  - job_name: api
                    static_configs:
                      - targets: ["api:8000"]
            """),
            encoding="utf-8",
        )
        (proj / "recording_rules.yml").write_text(
            textwrap.dedent("""\
                groups:
                  - name: latency
                    interval: 30s
                    rules:
                      - record: job:request_seconds:p95
                        expr: histogram_quantile(0.95, rate(request_seconds_bucket[5m]))
            """),
            encoding="utf-8",
        )
        promtail = proj / "services" / "promtail"
        promtail.mkdir(parents=True)
        (promtail / "config.yml").write_text(
            "server:\n  http_listen_port: 9080\nclients:\n  - url: http://loki:3100/loki/api/v1/push\nscrape_configs:\n  - job_name: docker\n",
            encoding="utf-8",
        )
        loki = proj / "services" / "loki"
        loki.mkdir(parents=True)
        (loki / "config.yml").write_text(
            "auth_enabled: false\nserver:\n  http_listen_port: 3100\nschema_config:\n  configs:\n    - store: tsdb\n",
            encoding="utf-8",
        )
        envoy = proj / "host" / "bridge"
        envoy.mkdir(parents=True)
        (envoy / "envoy.yaml").write_text(
            "static_resources:\n  listeners:\n    - name: grpc_web_listener\n  clusters:\n    - name: bridge_grpc\nadmin:\n  address:\n    socket_address:\n      port_value: 9901\n",
            encoding="utf-8",
        )
        proto = proj / "proto"
        proto.mkdir()
        (proto / "buf.yaml").write_text(
            "version: v2\nmodules:\n  - path: .\n    name: buf.build/example/proto\ndeps:\n  - buf.build/googleapis/googleapis\n",
            encoding="utf-8",
        )
        grafana = proj / "services" / "grafana" / "provisioning" / "datasources"
        grafana.mkdir(parents=True)
        (grafana / "datasources.yml").write_text(
            "apiVersion: 1\ndatasources:\n  - name: Prometheus\n    type: prometheus\n    url: http://prometheus:9090\n",
            encoding="utf-8",
        )
        model = proj / "services" / "llm_dialogue"
        model.mkdir(parents=True)
        (model / "config.yaml").write_text(
            "model: microsoft/Phi-4-mini-instruct\nquantization: bitsandbytes\nmax-model-len: 4096\ngpu-memory-utilization: 0.10\n",
            encoding="utf-8",
        )
        prompts = proj / "services" / "dialogue" / "src" / "dialogue" / "prompts"
        prompts.mkdir(parents=True)
        (prompts / "policy.yaml").write_text(
            "rules:\n  - be concise\n", encoding="utf-8"
        )

        wiki = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            from llm_wiki_cli.commands import bootstrap_cmd
            import argparse
            import json

            bootstrap_cmd.run(
                argparse.Namespace(
                    src_dir=".",
                    wiki_dir=str(wiki),
                    overwrite=False,
                    depth="full",
                    skip_workflows=True,
                    format="json",
                    source_adapter=True,
                )
            )

            summary = json.loads(capsys.readouterr().out)
            assert summary["runtime_config_files"] == 8
            assert summary["runtime_config_by_type"] == {
                "buf": 1,
                "envoy": 1,
                "grafana_provisioning": 1,
                "loki": 1,
                "model_service_config": 1,
                "prometheus": 1,
                "prometheus_rules": 1,
                "promtail": 1,
            }
            assert summary["infrastructure_files"] == 8

            expected_pages = [
                "prometheus_yml.md",
                "recording_rules_yml.md",
                "services_promtail_config_yml.md",
                "services_loki_config_yml.md",
                "host_bridge_envoy_yaml.md",
                "proto_buf_yaml.md",
                "services_grafana_provisioning_datasources_datasources_yml.md",
                "services_llm_dialogue_config_yaml.md",
            ]
            for page in expected_pages:
                assert (wiki / "infrastructure" / page).exists()
            assert not (
                wiki
                / "infrastructure"
                / "services_dialogue_src_dialogue_prompts_policy_yaml.md"
            ).exists()

            prometheus_md = (wiki / "infrastructure" / "prometheus_yml.md").read_text(
                encoding="utf-8"
            )
            assert "# Prometheus: prometheus.yml" in prometheus_md
            assert "**Type:** `prometheus`" in prometheus_md
            assert "`api`" in prometheus_md
            assert "`recording_rules.yml`" in prometheus_md
            assert "Prometheus rules: recording_rules.yml" in (
                wiki / "infrastructure" / "recording_rules_yml.md"
            ).read_text(encoding="utf-8")
            assert "Envoy: envoy.yaml" in (
                wiki / "infrastructure" / "host_bridge_envoy_yaml.md"
            ).read_text(encoding="utf-8")
            assert "microsoft/Phi-4-mini-instruct" in (
                wiki / "infrastructure" / "services_llm_dialogue_config_yaml.md"
            ).read_text(encoding="utf-8")

            index_content = (wiki / "index.md").read_text(encoding="utf-8")
            assert "Prometheus: prometheus.yml" in index_content
            assert "Model service config: llm_dialogue" in index_content
            assert "policy.yaml" not in index_content
        finally:
            os.chdir(old_cwd)
