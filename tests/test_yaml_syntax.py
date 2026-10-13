"""Structured YAML syntax and bounded infrastructure observations."""

from __future__ import annotations

import textwrap

import pytest

from llm_wiki_cli.services import yaml_syntax
from llm_wiki_cli.services.infrastructure_inventory import (
    get_yaml_infrastructure_inventory,
    parse_buf_config,
    parse_github_actions_workflow,
    parse_kubernetes_manifest,
    parse_prometheus_config,
    parse_runtime_config_yaml,
)
from llm_wiki_cli.services.yaml_syntax import load_yaml_documents


def test_quoted_helm_template_cannot_establish_resource_identity():
    result = parse_kubernetes_manifest('apiVersion: v1\nkind: Service\nmetadata: {name: "{{ .Release.Name }}"}\n')
    assert result["resources"] == []
    assert "template" in result["advisories"][0]


def test_yaml_scalar_lexemes_preserve_on_numbers_dates_and_null():
    documents, advisories = load_yaml_documents(
        "on: [push, pull_request]\nfalse: no\nport: 080\nratio: 0.10\n"
        "date: 2026-10-12\nempty:\n"
    )
    assert documents == [
        {
            "on": ["push", "pull_request"],
            "false": "no",
            "port": "080",
            "ratio": "0.10",
            "date": "2026-10-12",
            "empty": "",
        }
    ]
    assert advisories == []


def test_flow_comments_and_block_scalars_are_composed_exactly():
    documents, advisories = load_yaml_documents(
        textwrap.dedent("""\
        name: "a: b # quoted" # comment
        values: ["a,b", 'http://example/#fragment', {port: 8000}]
        script: |-
          echo first
          echo second
        folded: >-
          first
          second
        """)
    )
    assert advisories == []
    assert documents == [
        {
            "name": "a: b # quoted",
            "values": ["a,b", "http://example/#fragment", {"port": "8000"}],
            "script": "echo first\necho second",
            "folded": "first second",
        }
    ]


def test_aliases_and_merge_precedence_preserve_explicit_overrides():
    documents, advisories = load_yaml_documents(
        textwrap.dedent("""\
        base: &base {image: base:1, command: original}
        other: &other {image: other:1, port: 8000}
        service:
          <<: [*base, *other]
          command: replacement
        alias: *base
        """)
    )
    assert advisories == []
    assert documents == [
        {
            "base": {"image": "base:1", "command": "original"},
            "other": {"image": "other:1", "port": "8000"},
            "service": {"image": "base:1", "port": "8000", "command": "replacement"},
            "alias": {"image": "base:1", "command": "original"},
        }
    ]


@pytest.mark.parametrize(
    "text, reason",
    [
        ("name: [broken", "Malformed YAML"),
        ("name: first\nname: second\n", "duplicate mapping key"),
        ("root: &root {child: *root}", "recursive alias"),
        ("name: !custom value", "unsupported YAML tag"),
        (
            "payload: !!python/object/apply:os.system [echo unsafe]",
            "unsupported YAML tag",
        ),
        ("? [one, two]\n: value\n", "complex mapping key"),
        ("root: {<<: scalar}", "mapping merge requires mappings"),
        ("root: {<<: {}, <<: {}}", "duplicate merge key"),
    ],
)
def test_invalid_yaml_rejects_entire_stream_without_source_echo(text, reason):
    documents, advisories = load_yaml_documents(f"safe: SECRET_SENTINEL\n---\n{text}")
    assert documents == []
    assert len(advisories) == 1
    assert reason in advisories[0]
    assert "SECRET_SENTINEL" not in advisories[0]
    assert "echo unsafe" not in advisories[0]


def test_real_byte_budget_is_bounded():
    documents, advisories = load_yaml_documents(
        "x: " + "x" * yaml_syntax.MAX_YAML_BYTES
    )
    assert documents == []
    assert "byte budget" in advisories[0]


@pytest.mark.parametrize(
    "constant, limit, text, reason",
    [
        ("MAX_YAML_EVENTS", 8, "values: [a,b,c,d,e,f,g]", "event budget"),
        ("MAX_YAML_DOCUMENTS", 2, "a\n---\nb\n---\nc", "document budget"),
        ("MAX_YAML_DEPTH", 3, "x: [[[[leaf]]]]", "depth budget"),
        (
            "MAX_YAML_EXPANDED_NODES",
            20,
            "base: &a [a,b,c,d]\nrepeated: [*a,*a,*a,*a,*a]",
            "expanded-node budget",
        ),
    ],
)
def test_workload_limits_fail_closed(monkeypatch, constant, limit, text, reason):
    monkeypatch.setattr(yaml_syntax, constant, limit)
    documents, advisories = load_yaml_documents(text)
    assert documents == []
    assert reason in advisories[0]


def test_github_flow_aliases_block_run_and_runner_lists():
    result = parse_github_actions_workflow(
        textwrap.dedent("""\
        name: "CI: wide"
        on: {push: {}, pull_request: {}}
        common: &step {name: Checkout, uses: actions/checkout@v4}
        jobs:
          build:
            runs-on: [self-hosted, linux]
            needs: [lint, "checks,extra"]
            steps:
            - *step
            - run: |-
                echo first
                echo second
        """)
    )
    assert result["advisories"] == []
    assert result["triggers"] == ["push", "pull_request"]
    assert result["jobs"][0]["runs_on"] == "self-hosted, linux"
    assert result["jobs"][0]["needs"] == ["lint", "checks,extra"]
    assert result["jobs"][0]["steps"] == [
        {"name": "Checkout", "uses": "actions/checkout@v4", "run": ""},
        {"name": "", "uses": "", "run": "echo first\necho second"},
    ]


def test_runtime_flow_syntax_preserves_nested_scope():
    parsed = parse_runtime_config_yaml(
        "prometheus.yml",
        "{rule_files: [alerts.yml], scrape_configs: [{job_name: api, static_configs: [{name: nested}]}]}",
    )
    assert parsed is not None
    assert parsed["scrape_jobs"] == ["api"]
    assert parsed["rule_files"] == ["alerts.yml"]
    assert parsed["advisories"] == []
    buf = parse_buf_config(
        "{version: v2, plugins: [{local: protoc-gen-go, out: gen}]}", "buf.gen.yaml"
    )
    assert buf["plugins"] == ["protoc-gen-go"]
    assert buf["outputs"] == ["gen"]


@pytest.mark.parametrize(
    "path,text,expected",
    [
        ("prometheus.yml", "{rule_files: [rules.yml], scrape_configs: [{job_name: api}]}", {"type": "prometheus", "scrape_jobs": ["api"], "rule_files": ["rules.yml"]}),
        ("alerts.rules.yaml", "{groups: [{name: alerts, interval: 30s, rules: [{alert: Down, expr: up}]}]}", {"type": "prometheus_rules", "groups": [{"name": "alerts", "interval": "30s", "rules": 1}]}),
        ("grafana/provisioning/datasources/config.yaml", "{apiVersion: 1, datasources: [{name: Metrics, type: prometheus}]}", {"type": "grafana_provisioning", "entries": ["Metrics"]}),
        ("promtail/config.yaml", "{server: {http_listen_port: 9080}, clients: [{url: http://loki:3100}], scrape_configs: [{job_name: logs}]}", {"type": "promtail", "clients": ["http://loki:3100"], "scrape_jobs": ["logs"]}),
        ("loki/config.yaml", "{auth_enabled: false, server: {http_listen_port: 3100}, schema_config: {configs: [{store: tsdb}]}}", {"type": "loki", "auth_enabled": "false", "schema_stores": ["tsdb"]}),
        ("envoy.yaml", "{static_resources: {listeners: [{name: ingress}], clusters: [{name: api}]}, admin: {address: {socket_address: {port_value: 9901}}}}", {"type": "envoy", "listeners": ["ingress"], "admin_ports": ["9901"]}),
        ("buf.gen.yaml", "{version: v2, plugins: [{remote: buf.build/protocolbuffers/python, out: gen}]}", {"type": "buf", "config_kind": "generation", "outputs": ["gen"]}),
        ("services/llm_api/config.yaml", "{model: example/model, gpu-memory-utilization: 0.10}", {"type": "model_service_config", "settings": {"model": "example/model", "quantization": "", "max_model_len": "", "gpu_memory_utilization": "0.10", "dtype": ""}}),
    ],
)
def test_each_existing_runtime_family_accepts_flow_collections(path, text, expected):
    parsed = parse_runtime_config_yaml(path, text)
    assert parsed is not None and parsed["advisories"] == []
    for field, value in expected.items():
        assert parsed[field] == value


def test_single_mapping_parser_rejects_multidocument_partial_observations():
    result = parse_prometheus_config(
        "scrape_configs: [{job_name: first}]\n---\nother: second\n"
    )
    assert result["scrape_jobs"] == []
    assert result["advisories"]


def test_empty_yaml_documents_are_ignored_but_explicit_null_is_retained():
    documents, advisories = load_yaml_documents(
        "---\n# empty\n---\nname: api\n---\n# trailing empty\n"
    )
    assert documents == [{"name": "api"}]
    assert advisories == []
    documents, advisories = load_yaml_documents("null\n")
    assert documents == ["null"]
    assert advisories == []
    kubernetes = parse_kubernetes_manifest(
        "---\napiVersion: v1\nkind: Service\nmetadata: {name: api}\n---\n# empty\n"
    )
    assert kubernetes["advisories"] == []
    assert kubernetes["resources"][0]["name"] == "api"


def test_kubernetes_list_cronjob_service_and_custom_metadata():
    result = parse_kubernetes_manifest(
        textwrap.dedent("""\
        apiVersion: v1
        kind: List
        items:
        - apiVersion: batch/v1
          kind: CronJob
          metadata: {name: refresh, namespace: jobs}
          spec:
            jobTemplate:
              spec:
                template:
                  spec:
                    containers:
                    - {name: job, image: example/worker:1, ports: [{containerPort: 8080}], resources: {limits: {cpu: "1"}}}
        - apiVersion: v1
          kind: Service
          metadata: {name: worker}
          spec: {selector: {app: worker}, ports: [{port: 80, targetPort: http, protocol: TCP}]}
        - apiVersion: example.io/v1
          kind: Application
          metadata: {name: custom}
          spec: {secret: never-observed}
        """)
    )
    assert result["advisories"] == []
    assert [resource["kind"] for resource in result["resources"]] == [
        "CronJob",
        "Service",
        "Application",
    ]
    assert result["resources"][0]["containers"] == [
        {
            "name": "job",
            "image": "example/worker:1",
            "ports": ["8080"],
            "requests": {},
            "limits": {"cpu": "1"},
        }
    ]
    assert result["resources"][1]["selector"] == {"app": "worker"}
    assert result["resources"][1]["service_ports"] == [
        {"port": "80", "target_port": "http", "protocol": "TCP"}
    ]
    assert "never-observed" not in str(result)


@pytest.mark.parametrize(
    "tail",
    [
        "---\nother: unrelated\n",
        "---\napiVersion: v1\nkind: List\nitems: [{other: unrelated}]\n",
    ],
)
def test_mixed_kubernetes_stream_has_no_partial_resource_authority(tail):
    result = parse_kubernetes_manifest(
        "apiVersion: v1\nkind: Service\nmetadata: {name: api}\n" + tail
    )
    assert result["resources"] == []
    assert "non-Kubernetes" in result["advisories"][0]


def test_inventory_discovers_kubernetes_outside_convention_and_keeps_unknown_yaml(
    tmp_path,
):
    (tmp_path / "deployment.yml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: api}\n"
    )
    (tmp_path / "unknown.yml").write_text("database: {host: localhost}\n")
    result = get_yaml_infrastructure_inventory(tmp_path)
    assert result["deployment.yml"]["type"] == "kubernetes"
    assert "unknown.yml" not in result
