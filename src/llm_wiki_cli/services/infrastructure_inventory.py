"""Structured observations for recognized infrastructure YAML formats."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

from .source_snapshot import SourceSnapshot, build_source_snapshot
from .yaml_formats import parse_extended_yaml
from .yaml_syntax import load_yaml_documents, yaml_mapping as _mapping, yaml_scalar as _string


_GITHUB_WORKFLOW_PREFIX = ".github/workflows/"
_KUBERNETES_PREFIX = "k8s/"
_YAML_SUFFIXES = (".yml", ".yaml")
RUNTIME_CONFIG_TYPES = {
    "buf",
    "envoy",
    "grafana_provisioning",
    "loki",
    "model_service_config",
    "prometheus",
    "prometheus_rules",
    "promtail",
}


def infrastructure_page_name(source_path: str) -> str:
    """Return the canonical infrastructure page stem for *source_path*."""
    return source_path.replace("\\", "/").replace("/", "_").replace(".", "_")


def infrastructure_display_label(source_path: str, info: dict) -> str:
    """Return a human-friendly index label for an infrastructure entry."""
    entry_type = info.get("type")
    if entry_type == "yaml_format":
        family = str(info.get("yaml_format", "YAML")).replace("_", " ")
        return f"{family}: {Path(source_path).name}"
    if entry_type == "github_actions":
        name = str(info.get("name") or Path(source_path).stem)
        return f"GitHub Actions: {name}"
    if entry_type == "kubernetes":
        resources = info.get("resources") or []
        if resources:
            first = resources[0]
            kind = first.get("kind") or "Manifest"
            name = first.get("name") or Path(source_path).stem
            return f"Kubernetes: {kind} {name}"
        return f"Kubernetes: {Path(source_path).stem}"
    labels = {
        "prometheus": "Prometheus",
        "prometheus_rules": "Prometheus rules",
        "grafana_provisioning": "Grafana provisioning",
        "promtail": "Promtail",
        "loki": "Loki",
        "envoy": "Envoy",
        "buf": "Buf",
    }
    if entry_type in labels:
        return f"{labels[entry_type]}: {Path(source_path).name}"
    if entry_type == "model_service_config":
        service = str(info.get("service") or Path(source_path).parent.name)
        return f"Model service config: {service}"
    return infrastructure_page_name(source_path)


def get_yaml_infrastructure_inventory(
    src_dir: str | Path, *, source_snapshot: SourceSnapshot | None = None
) -> dict[str, dict]:
    """Discover recognized infrastructure and runtime/config YAML files."""
    source_snapshot = source_snapshot or build_source_snapshot(src_dir)
    inventory: dict[str, dict] = {}
    for source_file in source_snapshot.yaml_candidates:
        rel = source_file.rel_path
        text = source_file.abs_path.read_text(errors="replace")
        documents, _advisories = load_yaml_documents(text)
        extended = parse_extended_yaml(rel, documents)
        if _is_github_actions_path(rel):
            inventory[rel] = parse_github_actions_workflow(text)
        elif extended is not None:
            inventory[rel] = extended
        elif _is_kubernetes_path(rel) or any(
            _is_kubernetes_document(doc) for doc in documents
        ):
            inventory[rel] = parse_kubernetes_manifest(text)
        else:
            runtime_config = parse_runtime_config_yaml(rel, text)
            if runtime_config is not None:
                inventory[rel] = runtime_config
    return inventory


def parse_runtime_config_yaml(rel_path: str, text: str) -> dict | None:
    """Parse recognized runtime/config YAML families into documentation models."""
    normalized = rel_path.replace("\\", "/")
    name = Path(normalized).name
    root, _advisories = _single_mapping(text)
    if name.startswith("prometheus") and "scrape_configs" in root:
        return parse_prometheus_config(text)
    if "rules" in name and "groups" in root:
        return parse_prometheus_rules(text)
    if "/grafana/provisioning/" in f"/{normalized}":
        return parse_grafana_provisioning(text, normalized)
    if (
        "/promtail/" in f"/{normalized}"
        and name in {"config.yml", "config.yaml"}
        and "scrape_configs" in root
    ):
        return parse_promtail_config(text)
    if (
        "/loki/" in f"/{normalized}"
        and name in {"config.yml", "config.yaml"}
        and {"schema_config", "auth_enabled"}.intersection(root)
    ):
        return parse_loki_config(text)
    if name.startswith("envoy.") and "static_resources" in root:
        return parse_envoy_config(text)
    if name in {"buf.yaml", "buf.gen.yaml"}:
        return parse_buf_config(text, normalized)
    parts = normalized.split("/")
    if (
        len(parts) == 3
        and parts[0] == "services"
        and parts[1].startswith("llm_")
        and name in {"config.yml", "config.yaml"}
        and "model" in root
    ):
        return parse_model_service_config(text, normalized)
    return None


def parse_prometheus_config(text: str) -> dict:
    """Observe Prometheus scrape configuration without evaluating it."""
    root, advisories = _single_mapping(text)
    rules = _strings(root.get("rule_files"))
    jobs = _named_items(root.get("scrape_configs"), "job_name")
    if not rules and not jobs and not advisories:
        advisories.append("No Prometheus rule files or scrape jobs were observed.")
    return {
        "type": "prometheus",
        "rule_files": rules,
        "scrape_jobs": jobs,
        "advisories": advisories,
    }


def parse_prometheus_rules(text: str) -> dict:
    """Observe Prometheus recording/alerting rule groups."""
    root, advisories = _single_mapping(text)
    groups = [
        {
            "name": _string(group.get("name")),
            "interval": _string(group.get("interval")),
            "rules": len(_list(group.get("rules"))),
        }
        for group in _mappings(root.get("groups"))
    ]
    if not groups and not advisories:
        advisories.append("No Prometheus rule groups were observed.")
    return {"type": "prometheus_rules", "groups": groups, "advisories": advisories}


def parse_grafana_provisioning(text: str, rel_path: str) -> dict:
    """Observe Grafana provisioning datasource or dashboard files."""
    root, advisories = _single_mapping(text)
    kind = "dashboard" if "dashboards" in rel_path else "datasource"
    entries = _named_items(
        root.get("providers" if kind == "dashboard" else "datasources")
    )
    if not entries and not advisories:
        advisories.append("No Grafana provisioning entries were observed.")
    return {
        "type": "grafana_provisioning",
        "provisioning_kind": kind,
        "entries": entries,
        "advisories": advisories,
    }


def parse_promtail_config(text: str) -> dict:
    """Observe Promtail client and scrape configuration."""
    root, advisories = _single_mapping(text)
    return {
        "type": "promtail",
        "clients": _named_items(root.get("clients"), "url"),
        "scrape_jobs": _named_items(root.get("scrape_configs"), "job_name"),
        "listen_port": _string(_mapping(root.get("server")).get("http_listen_port")),
        "advisories": advisories,
    }


def parse_loki_config(text: str) -> dict:
    """Observe Loki server and schema settings."""
    root, advisories = _single_mapping(text)
    listen_port = _string(_mapping(root.get("server")).get("http_listen_port"))
    stores = _named_items(_mapping(root.get("schema_config")).get("configs"), "store")
    if not listen_port and not stores and not advisories:
        advisories.append("No Loki server or schema settings were observed.")
    return {
        "type": "loki",
        "auth_enabled": _string(root.get("auth_enabled")),
        "listen_port": listen_port,
        "schema_stores": stores,
        "retention_period": _first_scalar(root, "retention_period"),
        "advisories": advisories,
    }


def parse_envoy_config(text: str) -> dict:
    """Observe Envoy listener, cluster, and admin port summaries."""
    root, advisories = _single_mapping(text)
    static = _mapping(root.get("static_resources"))
    listeners = _named_items(static.get("listeners"))
    clusters = _named_items(static.get("clusters"))
    ports = _recursive_scalars(_mapping(root.get("admin")), "port_value")
    if not listeners and not clusters and not advisories:
        advisories.append("No Envoy listeners or clusters were observed.")
    return {
        "type": "envoy",
        "listeners": listeners,
        "clusters": clusters,
        "admin_ports": ports,
        "advisories": advisories,
    }


def parse_buf_config(text: str, rel_path: str) -> dict:
    """Observe Buf module or generation configuration."""
    root, advisories = _single_mapping(text)
    plugins = _mappings(root.get("plugins"))
    return {
        "type": "buf",
        "config_kind": "generation" if rel_path.endswith("buf.gen.yaml") else "module",
        "version": _string(root.get("version")),
        "modules": _named_items(root.get("modules")),
        "deps": _strings(root.get("deps")),
        "plugins": _unique_values(
            _string(plugin.get("remote") or plugin.get("local") or plugin.get("plugin"))
            for plugin in plugins
        ),
        "outputs": _named_items(root.get("plugins"), "out"),
        "advisories": advisories,
    }


def parse_model_service_config(text: str, rel_path: str) -> dict:
    """Observe service-local model runtime settings."""
    root, advisories = _single_mapping(text)
    settings = {
        key.replace("-", "_"): _string(root.get(key))
        for key in (
            "model",
            "quantization",
            "max-model-len",
            "gpu-memory-utilization",
            "dtype",
        )
    }
    if not settings["model"] and not advisories:
        advisories.append("No model setting was observed.")
    return {
        "type": "model_service_config",
        "service": Path(rel_path).parent.name,
        "settings": settings,
        "advisories": advisories,
    }


def parse_github_actions_workflow(text: str) -> dict:
    """Observe GitHub Actions workflow triggers, jobs, and direct steps."""
    root, advisories = _single_mapping(text)
    on = root.get("on")
    triggers = list(on) if isinstance(on, dict) else _strings(on)
    jobs = []
    for job_id, raw_job in _mapping(root.get("jobs")).items():
        job = _mapping(raw_job)
        jobs.append(
            {
                "id": job_id,
                "name": _string(job.get("name")),
                "runs_on": ", ".join(_strings(job.get("runs-on"))),
                "needs": _strings(job.get("needs")),
                "steps": [
                    {key: _string(step.get(key)) for key in ("name", "uses", "run")}
                    for step in _mappings(job.get("steps"))
                ],
            }
        )
    if not jobs and not advisories:
        advisories.append("No GitHub Actions jobs were observed.")
    return {
        "type": "github_actions",
        "name": _string(root.get("name")),
        "triggers": triggers,
        "jobs": jobs,
        "advisories": advisories,
    }


def parse_kubernetes_manifest(text: str) -> dict:
    """Observe an entirely Kubernetes stream, including Lists and CronJobs.

    A mixed stream retains no resource observations rather than silently
    omitting unrecognized documents or List items.
    """
    if "{{" in text or "{%" in text:
        return {
            "type": "kubernetes", "resources": [],
            "advisories": ["Unrendered template syntax; no concrete Kubernetes resources were retained."],
        }
    documents, advisories = load_yaml_documents(text)
    resources = []
    if not advisories:
        for document in documents:
            leaves = _kubernetes_leaves(document)
            if leaves is None:
                advisories.append(
                    "The YAML stream includes a non-Kubernetes document or List item; no resources were retained."
                )
                resources = []
                break
            resources.extend(_kubernetes_resource(resource) for resource in leaves)
    if not resources and not advisories:
        advisories.append("No Kubernetes resources were observed.")
    return {"type": "kubernetes", "resources": resources, "advisories": advisories}


def _is_github_actions_path(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    return normalized.startswith(_GITHUB_WORKFLOW_PREFIX) and normalized.endswith(
        _YAML_SUFFIXES
    )


def _is_kubernetes_path(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    return normalized.startswith(_KUBERNETES_PREFIX) and normalized.endswith(
        _YAML_SUFFIXES
    )


def _is_kubernetes_document(document: object) -> bool:
    if not isinstance(document, dict):
        return False
    version = _string(document.get("apiVersion"))
    kind = _string(document.get("kind"))
    if (
        re.fullmatch(r"(?:[a-zA-Z0-9.-]+/)?v\d+(?:(?:alpha|beta)\d+)?", version) is None
        or not kind
        or version.startswith("kustomize.config.k8s.io/")
    ):
        return False
    return isinstance(document.get("metadata"), dict) or (
        kind == "List" and isinstance(document.get("items"), list)
    )


def _kubernetes_leaves(document: object) -> list[dict] | None:
    if not _is_kubernetes_document(document):
        return None
    document = _mapping(document)
    if document.get("kind") != "List":
        return [document]
    leaves = []
    for item in _list(document.get("items")):
        nested = _kubernetes_leaves(item)
        if nested is None:
            return None
        leaves.extend(nested)
    return leaves


def _kubernetes_resource(document: dict) -> dict:
    metadata = _mapping(document.get("metadata"))
    spec = _mapping(document.get("spec"))
    kind = _string(document.get("kind"))
    pod = {}
    if kind == "Pod":
        pod = spec
    elif kind == "CronJob":
        job = _mapping(_mapping(spec.get("jobTemplate")).get("spec"))
        pod = _mapping(_mapping(job.get("template")).get("spec"))
    elif kind in {
        "Deployment",
        "StatefulSet",
        "DaemonSet",
        "ReplicaSet",
        "ReplicationController",
        "Job",
    }:
        pod = _mapping(_mapping(spec.get("template")).get("spec"))
    selector = _mapping(spec.get("selector"))
    selector = (
        _mapping(selector.get("matchLabels")) if "matchLabels" in selector else selector
    )
    containers = []
    for container in _mappings(pod.get("containers")):
        resources = _mapping(container.get("resources"))
        containers.append(
            {
                "name": _string(container.get("name")),
                "image": _string(container.get("image")),
                "ports": _named_items(container.get("ports"), "containerPort"),
                "requests": _scalar_mapping(resources.get("requests")),
                "limits": _scalar_mapping(resources.get("limits")),
            }
        )
    service_ports = (
        [
            {
                "port": _string(port.get("port")),
                "target_port": _string(port.get("targetPort")),
                "protocol": _string(port.get("protocol")),
            }
            for port in _mappings(spec.get("ports"))
        ]
        if kind == "Service"
        else []
    )
    return {
        "api_version": _string(document.get("apiVersion")),
        "kind": kind,
        "name": _string(metadata.get("name")),
        "namespace": _string(metadata.get("namespace")),
        "replicas": _string(spec.get("replicas")),
        "containers": containers,
        "service_type": _string(spec.get("type")) if kind == "Service" else "",
        "service_ports": service_ports,
        "selector": _scalar_mapping(selector),
    }


def _single_mapping(text: str) -> tuple[dict, list[str]]:
    documents, advisories = load_yaml_documents(text)
    if advisories:
        return {}, advisories
    if len(documents) != 1 or not isinstance(documents[0], dict):
        return {}, [
            "Expected one YAML mapping document; no observations were retained."
        ]
    return documents[0], []


def _list(value: object) -> list:
    return value if isinstance(value, list) else []


def _mappings(value: object) -> list[dict]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    return _unique_values(
        _string(item) for item in (value if isinstance(value, list) else [value])
    )


def _named_items(value: object, key: str = "name") -> list[str]:
    return _unique_values(_string(item.get(key)) for item in _mappings(value))


def _scalar_mapping(value: object) -> dict[str, str]:
    return {key: item for key, item in _mapping(value).items() if isinstance(item, str)}


def _recursive_scalars(value: object, key: str) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        if key in value:
            values.append(_string(value[key]))
        for child in value.values():
            values.extend(_recursive_scalars(child, key))
    elif isinstance(value, list):
        for child in value:
            values.extend(_recursive_scalars(child, key))
    return _unique_values(values)


def _first_scalar(value: object, key: str) -> str:
    return next(iter(_recursive_scalars(value, key)), "")


def _unique_values(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
