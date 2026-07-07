"""Tests for GitHub Actions and Kubernetes infrastructure inventory."""

from __future__ import annotations

import textwrap

from llm_wiki_cli.services.infrastructure_inventory import (
    get_yaml_infrastructure_inventory,
    parse_envoy_config,
    parse_github_actions_workflow,
    parse_kubernetes_manifest,
    parse_prometheus_config,
    parse_promtail_config,
)


def test_parse_github_actions_workflow_summarizes_triggers_jobs_and_steps():
    text = textwrap.dedent(
        """\
        name: CI

        on:
          push:
            branches: [main, develop]
          pull_request:
            branches: [main]

        jobs:
          lint:
            name: Code Quality
            runs-on: ubuntu-latest
            steps:
              - name: Checkout code
                uses: actions/checkout@v4
              - name: Run Ruff
                run: ruff check src/ tests/
          test:
            runs-on: ubuntu-latest
            needs: lint
            steps:
              - name: Run tests
                run: pytest
        """
    )

    result = parse_github_actions_workflow(text)

    assert result["type"] == "github_actions"
    assert result["name"] == "CI"
    assert result["triggers"] == ["push", "pull_request"]
    assert result["jobs"] == [
        {
            "id": "lint",
            "name": "Code Quality",
            "runs_on": "ubuntu-latest",
            "needs": [],
            "steps": [
                {"name": "Checkout code", "uses": "actions/checkout@v4", "run": ""},
                {"name": "Run Ruff", "uses": "", "run": "ruff check src/ tests/"},
            ],
        },
        {
            "id": "test",
            "name": "",
            "runs_on": "ubuntu-latest",
            "needs": ["lint"],
            "steps": [{"name": "Run tests", "uses": "", "run": "pytest"}],
        },
    ]
    assert result["advisories"] == []


def test_parse_kubernetes_manifest_summarizes_workloads_and_services():
    text = textwrap.dedent(
        """\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: api
          namespace: production
        spec:
          replicas: 2
          template:
            spec:
              containers:
                - name: api
                  image: example/api:latest
                  ports:
                    - containerPort: 8000
                  resources:
                    requests:
                      cpu: "500m"
                      memory: "512Mi"
                    limits:
                      cpu: "1000m"
                      memory: "1Gi"
        ---
        apiVersion: v1
        kind: Service
        metadata:
          name: api
        spec:
          type: ClusterIP
          selector:
            app: api
          ports:
            - port: 80
              targetPort: 8000
              protocol: TCP
        """
    )

    result = parse_kubernetes_manifest(text)

    assert result["type"] == "kubernetes"
    assert result["resources"] == [
        {
            "api_version": "apps/v1",
            "kind": "Deployment",
            "name": "api",
            "namespace": "production",
            "replicas": "2",
            "containers": [
                {
                    "name": "api",
                    "image": "example/api:latest",
                    "ports": ["8000"],
                    "requests": {"cpu": "500m", "memory": "512Mi"},
                    "limits": {"cpu": "1000m", "memory": "1Gi"},
                }
            ],
            "service_type": "",
            "service_ports": [],
            "selector": {},
        },
        {
            "api_version": "v1",
            "kind": "Service",
            "name": "api",
            "namespace": "",
            "replicas": "",
            "containers": [],
            "service_type": "ClusterIP",
            "service_ports": [{"port": "80", "target_port": "8000", "protocol": "TCP"}],
            "selector": {"app": "api"},
        },
    ]
    assert result["advisories"] == []


def test_yaml_infrastructure_inventory_targets_actions_and_k8s_only(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n")
    k8s = tmp_path / "k8s"
    k8s.mkdir()
    (k8s / "service.yaml").write_text(
        "apiVersion: v1\nkind: Service\nmetadata:\n  name: api\n"
    )
    (tmp_path / "config.yml").write_text("database:\n  host: localhost\n")

    inventory = get_yaml_infrastructure_inventory(tmp_path)

    assert sorted(inventory) == [".github/workflows/ci.yml", "k8s/service.yaml"]
    assert inventory[".github/workflows/ci.yml"]["type"] == "github_actions"
    assert inventory["k8s/service.yaml"]["type"] == "kubernetes"


def test_yaml_infrastructure_inventory_targets_runtime_config_families(tmp_path):
    (tmp_path / "prometheus.yml").write_text(
        textwrap.dedent(
            """\
            global:
              scrape_interval: 15s
            rule_files:
              - recording_rules.yml
            scrape_configs:
              - job_name: api
                static_configs:
                  - targets: ["api:8000"]
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "recording_rules.yml").write_text(
        textwrap.dedent(
            """\
            groups:
              - name: latency
                interval: 30s
                rules:
                  - record: job:request_seconds:p95
                    expr: histogram_quantile(0.95, rate(request_seconds_bucket[5m]))
            """
        ),
        encoding="utf-8",
    )
    grafana = tmp_path / "services" / "grafana" / "provisioning" / "datasources"
    grafana.mkdir(parents=True)
    (grafana / "datasources.yml").write_text(
        textwrap.dedent(
            """\
            apiVersion: 1
            datasources:
              - name: Prometheus
                type: prometheus
                url: http://prometheus:9090
            """
        ),
        encoding="utf-8",
    )
    promtail = tmp_path / "services" / "promtail"
    promtail.mkdir(parents=True)
    (promtail / "config.yml").write_text(
        textwrap.dedent(
            """\
            server:
              http_listen_port: 9080
            clients:
              - url: http://loki:3100/loki/api/v1/push
            scrape_configs:
              - job_name: docker
            """
        ),
        encoding="utf-8",
    )
    loki = tmp_path / "services" / "loki"
    loki.mkdir(parents=True)
    (loki / "config.yml").write_text(
        textwrap.dedent(
            """\
            auth_enabled: false
            server:
              http_listen_port: 3100
            schema_config:
              configs:
                - store: tsdb
            """
        ),
        encoding="utf-8",
    )
    envoy = tmp_path / "host" / "bridge"
    envoy.mkdir(parents=True)
    (envoy / "envoy.yaml").write_text(
        textwrap.dedent(
            """\
            static_resources:
              listeners:
                - name: grpc_web_listener
              clusters:
                - name: bridge_grpc
            admin:
              address:
                socket_address:
                  port_value: 9901
            """
        ),
        encoding="utf-8",
    )
    proto = tmp_path / "proto"
    proto.mkdir()
    (proto / "buf.yaml").write_text(
        textwrap.dedent(
            """\
            version: v2
            modules:
              - path: .
                name: buf.build/example/proto
            deps:
              - buf.build/googleapis/googleapis
            """
        ),
        encoding="utf-8",
    )
    model = tmp_path / "services" / "llm_dialogue"
    model.mkdir(parents=True)
    (model / "config.yaml").write_text(
        textwrap.dedent(
            """\
            model: microsoft/Phi-4-mini-instruct
            quantization: bitsandbytes
            max-model-len: 4096
            gpu-memory-utilization: 0.10
            """
        ),
        encoding="utf-8",
    )
    prompt = tmp_path / "services" / "dialogue" / "src" / "dialogue" / "prompts"
    prompt.mkdir(parents=True)
    (prompt / "policy.yaml").write_text("rules:\n  - be concise\n", encoding="utf-8")

    inventory = get_yaml_infrastructure_inventory(tmp_path)

    assert inventory["prometheus.yml"]["type"] == "prometheus"
    assert inventory["prometheus.yml"]["scrape_jobs"] == ["api"]
    assert inventory["recording_rules.yml"]["type"] == "prometheus_rules"
    assert inventory["recording_rules.yml"]["groups"] == [
        {"name": "latency", "interval": "30s", "rules": 1}
    ]
    assert (
        inventory["services/grafana/provisioning/datasources/datasources.yml"]["type"]
        == "grafana_provisioning"
    )
    assert inventory["services/promtail/config.yml"]["type"] == "promtail"
    assert inventory["services/loki/config.yml"]["type"] == "loki"
    assert inventory["host/bridge/envoy.yaml"]["type"] == "envoy"
    assert inventory["proto/buf.yaml"]["type"] == "buf"
    assert inventory["services/llm_dialogue/config.yaml"]["type"] == (
        "model_service_config"
    )
    assert "services/dialogue/src/dialogue/prompts/policy.yaml" not in inventory


def test_runtime_config_parsers_ignore_inline_comments_and_nested_names():
    prometheus = parse_prometheus_config(
        textwrap.dedent(
            """\
            rule_files:
              - "llm_unified_rules.yml"  # acceptance alerts
            scrape_configs:
              - job_name: api
            """
        )
    )
    promtail = parse_promtail_config(
        textwrap.dedent(
            """\
            scrape_configs:
              - job_name: docker
                docker_sd_configs:
                  - filters:
                      - name: label
                        values: ["com.docker.compose.project"]
            """
        )
    )
    envoy = parse_envoy_config(
        textwrap.dedent(
            """\
            static_resources:
              listeners:
                - name: grpc_web_listener
                  filter_chains:
                    - filters:
                        - name: envoy.filters.http.router
              clusters:
                - name: bridge_grpc
            """
        )
    )

    assert prometheus["rule_files"] == ["llm_unified_rules.yml"]
    assert promtail["scrape_jobs"] == ["docker"]
    assert envoy["listeners"] == ["grpc_web_listener"]
    assert envoy["clusters"] == ["bridge_grpc"]


def test_kubernetes_container_fields_ignore_nested_env_and_probe_names():
    text = textwrap.dedent(
        """\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: pto-api
        spec:
          template:
            spec:
              containers:
                - name: api
                  image: projectteamopen/api:latest
                  envFrom:
                    - secretRef:
                        name: pto-secrets
                  resources:
                    requests:
                      memory: "512Mi"
                      cpu: "500m"
                    limits:
                      memory: "2Gi"
                      cpu: "2000m"
                  livenessProbe:
                    httpGet:
                      path: /api/v1/health
                      port: http
        """
    )

    result = parse_kubernetes_manifest(text)
    container = result["resources"][0]["containers"][0]

    assert container["name"] == "api"
    assert container["image"] == "projectteamopen/api:latest"
    assert container["requests"] == {"memory": "512Mi", "cpu": "500m"}
    assert container["limits"] == {"memory": "2Gi", "cpu": "2000m"}
