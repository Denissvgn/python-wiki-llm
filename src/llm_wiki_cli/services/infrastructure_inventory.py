"""Inventory helpers for non-Docker infrastructure YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .source_snapshot import SourceSnapshot, build_source_snapshot


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
    if entry_type == "prometheus":
        return f"Prometheus: {Path(source_path).name}"
    if entry_type == "prometheus_rules":
        return f"Prometheus rules: {Path(source_path).name}"
    if entry_type == "grafana_provisioning":
        return f"Grafana provisioning: {Path(source_path).name}"
    if entry_type == "promtail":
        return f"Promtail: {Path(source_path).name}"
    if entry_type == "loki":
        return f"Loki: {Path(source_path).name}"
    if entry_type == "envoy":
        return f"Envoy: {Path(source_path).name}"
    if entry_type == "buf":
        return f"Buf: {Path(source_path).name}"
    if entry_type == "model_service_config":
        service = str(info.get("service") or Path(source_path).parent.name)
        return f"Model service config: {service}"
    return infrastructure_page_name(source_path)


def get_yaml_infrastructure_inventory(
    src_dir: str | Path, *, source_snapshot: SourceSnapshot | None = None
) -> dict[str, dict]:
    """Discover targeted infrastructure and runtime/config YAML files."""
    source_snapshot = source_snapshot or build_source_snapshot(src_dir)
    inventory: dict[str, dict] = {}
    for source_file in source_snapshot.yaml_candidates:
        rel = source_file.rel_path
        text = source_file.abs_path.read_text(errors="replace")
        if _is_github_actions_path(rel):
            inventory[rel] = parse_github_actions_workflow(text)
        elif _is_kubernetes_path(rel):
            inventory[rel] = parse_kubernetes_manifest(text)
        else:
            runtime_config = parse_runtime_config_yaml(rel, text)
            if runtime_config is not None:
                inventory[rel] = runtime_config
    return inventory


def parse_runtime_config_yaml(rel_path: str, text: str) -> dict | None:
    """Parse recognized runtime/config YAML families into documentation models."""
    normalized = rel_path.replace("\\", "/")
    lines = _yaml_lines(text)
    if _is_prometheus_config(normalized, lines):
        return parse_prometheus_config(text)
    if _is_prometheus_rules(normalized, lines):
        return parse_prometheus_rules(text)
    if _is_grafana_provisioning(normalized):
        return parse_grafana_provisioning(text, normalized)
    if _is_promtail_config(normalized, lines):
        return parse_promtail_config(text)
    if _is_loki_config(normalized, lines):
        return parse_loki_config(text)
    if _is_envoy_config(normalized, lines):
        return parse_envoy_config(text)
    if _is_buf_config(normalized):
        return parse_buf_config(text, normalized)
    if _is_model_service_config(normalized, lines):
        return parse_model_service_config(text, normalized)
    return None


def parse_prometheus_config(text: str) -> dict:
    """Parse Prometheus scrape configuration into a compact model."""
    lines = _yaml_lines(text)
    rule_files = _collect_list_values(lines, "rule_files")
    scrape_jobs = _collect_named_items(lines, "scrape_configs")
    advisories = []
    if not rule_files and not scrape_jobs:
        advisories.append(
            "No Prometheus rule files or scrape jobs were parsed; the file may "
            "use unsupported YAML features."
        )
    return {
        "type": "prometheus",
        "rule_files": rule_files,
        "scrape_jobs": scrape_jobs,
        "advisories": advisories,
    }


def parse_prometheus_rules(text: str) -> dict:
    """Parse Prometheus recording/alerting rule groups."""
    lines = _yaml_lines(text)
    groups: list[dict[str, object]] = []
    in_groups = False
    group_indent = -1
    current: dict[str, object] | None = None
    in_rules = False
    rules_indent = -1

    for indent, stripped in lines:
        if indent == 0:
            in_groups = stripped == "groups:"
            group_indent = indent if in_groups else -1
            current = None
            in_rules = False
            continue
        if not in_groups:
            continue
        if indent <= group_indent:
            in_groups = False
            current = None
            in_rules = False
            continue
        if stripped.startswith("- ") and indent == group_indent + 2:
            current = {"name": "", "interval": "", "rules": 0}
            groups.append(current)
            in_rules = False
            tail = stripped[2:].strip()
            if _mapping_key(tail):
                key, value = _split_key_value(tail)
                if key == "name":
                    current["name"] = _parse_scalar(value)
            continue
        if current is None:
            continue
        if indent == group_indent + 4 and _mapping_key(stripped):
            key, value = _split_key_value(stripped)
            if key in {"name", "interval"}:
                current[key] = _parse_scalar(value)
            elif key == "rules":
                in_rules = True
                rules_indent = indent
            else:
                in_rules = False
            continue
        if in_rules and indent > rules_indent and stripped.startswith("- "):
            current_rules = current.get("rules", 0)
            current["rules"] = (
                current_rules if isinstance(current_rules, int) else 0
            ) + 1

    advisories = []
    if not groups:
        advisories.append(
            "No Prometheus rule groups were parsed; the file may use "
            "unsupported YAML features."
        )
    return {"type": "prometheus_rules", "groups": groups, "advisories": advisories}


def parse_grafana_provisioning(text: str, rel_path: str) -> dict:
    """Parse Grafana provisioning datasource or dashboard files."""
    lines = _yaml_lines(text)
    provisioning_kind = "dashboard" if "dashboards" in rel_path else "datasource"
    section = "providers" if provisioning_kind == "dashboard" else "datasources"
    entries = _collect_named_items(lines, section)
    advisories = []
    if not entries:
        advisories.append(
            "No Grafana provisioning entries were parsed; the file may use "
            "unsupported YAML features."
        )
    return {
        "type": "grafana_provisioning",
        "provisioning_kind": provisioning_kind,
        "entries": entries,
        "advisories": advisories,
    }


def parse_promtail_config(text: str) -> dict:
    """Parse Promtail client and scrape configuration."""
    lines = _yaml_lines(text)
    return {
        "type": "promtail",
        "clients": _collect_field_values(lines, "clients", "url"),
        "scrape_jobs": _collect_named_items(lines, "scrape_configs"),
        "listen_port": _first_value_for_key(lines, "http_listen_port"),
        "advisories": [],
    }


def parse_loki_config(text: str) -> dict:
    """Parse Loki local runtime configuration."""
    lines = _yaml_lines(text)
    advisories = []
    listen_port = _first_value_for_key(lines, "http_listen_port")
    stores = _collect_field_values(lines, "configs", "store")
    if not listen_port and not stores:
        advisories.append(
            "No Loki server or schema settings were parsed; the file may use "
            "unsupported YAML features."
        )
    return {
        "type": "loki",
        "auth_enabled": _top_level_value(lines, "auth_enabled"),
        "listen_port": listen_port,
        "schema_stores": stores,
        "retention_period": _first_value_for_key(lines, "retention_period"),
        "advisories": advisories,
    }


def parse_envoy_config(text: str) -> dict:
    """Parse Envoy listener, cluster, and admin port summaries."""
    lines = _yaml_lines(text)
    listeners = _collect_named_items(lines, "listeners")
    clusters = _collect_named_items(lines, "clusters")
    admin_ports = _collect_values_after_key(lines, "admin", "port_value")
    advisories = []
    if not listeners and not clusters:
        advisories.append(
            "No Envoy listeners or clusters were parsed; the file may use "
            "unsupported YAML features."
        )
    return {
        "type": "envoy",
        "listeners": listeners,
        "clusters": clusters,
        "admin_ports": admin_ports,
        "advisories": advisories,
    }


def parse_buf_config(text: str, rel_path: str) -> dict:
    """Parse Buf module or generation configuration."""
    lines = _yaml_lines(text)
    plugins = _collect_field_values(lines, "plugins", "remote")
    return {
        "type": "buf",
        "config_kind": "generation" if rel_path.endswith("buf.gen.yaml") else "module",
        "version": _top_level_value(lines, "version"),
        "modules": _collect_field_values(lines, "modules", "name"),
        "deps": _collect_list_values(lines, "deps"),
        "plugins": plugins,
        "outputs": _collect_field_values(lines, "plugins", "out"),
        "advisories": [],
    }


def parse_model_service_config(text: str, rel_path: str) -> dict:
    """Parse service-local model runtime settings."""
    lines = _yaml_lines(text)
    service = Path(rel_path).parent.name
    settings = {
        "model": _top_level_value(lines, "model"),
        "quantization": _top_level_value(lines, "quantization"),
        "max_model_len": _top_level_value(lines, "max-model-len"),
        "gpu_memory_utilization": _top_level_value(lines, "gpu-memory-utilization"),
        "dtype": _top_level_value(lines, "dtype"),
    }
    advisories = []
    if not settings["model"]:
        advisories.append(
            "No model setting was parsed; the config may use unsupported YAML features."
        )
    return {
        "type": "model_service_config",
        "service": service,
        "settings": settings,
        "advisories": advisories,
    }


def parse_github_actions_workflow(text: str) -> dict:
    """Parse a GitHub Actions workflow into a compact documentation model."""
    lines = _yaml_lines(text)
    name = ""
    triggers: list[str] = []
    jobs: list[dict] = []
    current_job: dict | None = None
    current_step: dict | None = None
    in_jobs = False
    in_steps = False
    pending_job_list: str | None = None
    pending_job_list_indent = -1
    index = 0

    while index < len(lines):
        indent, stripped = lines[index]
        if indent == 0:
            in_steps = False
            current_step = None
            pending_job_list = None
            if stripped.startswith("name:"):
                name = _scalar_after_colon(stripped)
            elif stripped.startswith("on:"):
                triggers = _parse_github_triggers(lines, index)
            in_jobs = stripped == "jobs:"
            index += 1
            continue

        if (
            in_jobs
            and indent == 2
            and _mapping_key(stripped)
            and not stripped.startswith("-")
        ):
            job_id = stripped.split(":", 1)[0].strip()
            current_job = {
                "id": job_id,
                "name": "",
                "runs_on": "",
                "needs": [],
                "steps": [],
            }
            jobs.append(current_job)
            in_steps = False
            current_step = None
            pending_job_list = None
            index += 1
            continue

        if in_jobs and current_job is not None and indent == 4:
            key, value = _split_key_value(stripped)
            if key == "steps":
                in_steps = True
                current_step = None
                pending_job_list = None
            elif key in {"name", "runs-on"}:
                field = "name" if key == "name" else "runs_on"
                current_job[field] = _parse_scalar(value)
            elif key == "needs":
                needs = _parse_string_list(value)
                current_job["needs"] = needs
                pending_job_list = "needs" if not value else None
                pending_job_list_indent = indent
            else:
                pending_job_list = None
            index += 1
            continue

        if (
            in_jobs
            and current_job is not None
            and pending_job_list == "needs"
            and indent > pending_job_list_indent
            and stripped.startswith("- ")
        ):
            current_job["needs"].append(_parse_scalar(stripped[2:].strip()))
            index += 1
            continue

        if in_jobs and in_steps and current_job is not None and indent >= 6:
            step_result = _parse_actions_step_line(
                lines, index, current_job, current_step
            )
            current_step = step_result[0]
            index = step_result[1]
            continue

        index += 1

    advisories = []
    if not jobs:
        advisories.append(
            "No GitHub Actions jobs were parsed; the workflow may use "
            "unsupported YAML features."
        )
    return {
        "type": "github_actions",
        "name": name,
        "triggers": triggers,
        "jobs": jobs,
        "advisories": advisories,
    }


def parse_kubernetes_manifest(text: str) -> dict:
    """Parse one Kubernetes YAML file into resource summaries."""
    resources = [
        _parse_kubernetes_document(document)
        for document in _split_yaml_documents(text)
        if document.strip()
    ]
    resources = [resource for resource in resources if resource is not None]
    advisories = []
    if not resources:
        advisories.append(
            "No Kubernetes resources were parsed; the manifest may use "
            "unsupported YAML features."
        )
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


def _is_prometheus_config(rel_path: str, lines: list[tuple[int, str]]) -> bool:
    name = Path(rel_path).name
    return name.startswith("prometheus") and _has_key(lines, "scrape_configs")


def _is_prometheus_rules(rel_path: str, lines: list[tuple[int, str]]) -> bool:
    name = Path(rel_path).name
    return "rules" in name and _has_top_level_key(lines, "groups")


def _is_grafana_provisioning(rel_path: str) -> bool:
    normalized = f"/{rel_path}"
    return "/grafana/provisioning/" in normalized


def _is_promtail_config(rel_path: str, lines: list[tuple[int, str]]) -> bool:
    normalized = f"/{rel_path}"
    return (
        "/promtail/" in normalized
        and Path(rel_path).name in {"config.yml", "config.yaml"}
        and _has_key(lines, "scrape_configs")
    )


def _is_loki_config(rel_path: str, lines: list[tuple[int, str]]) -> bool:
    normalized = f"/{rel_path}"
    return (
        "/loki/" in normalized
        and Path(rel_path).name in {"config.yml", "config.yaml"}
        and (_has_key(lines, "schema_config") or _has_key(lines, "auth_enabled"))
    )


def _is_envoy_config(rel_path: str, lines: list[tuple[int, str]]) -> bool:
    name = Path(rel_path).name
    return name.startswith("envoy.") and _has_key(lines, "static_resources")


def _is_buf_config(rel_path: str) -> bool:
    return Path(rel_path).name in {"buf.yaml", "buf.gen.yaml"}


def _is_model_service_config(rel_path: str, lines: list[tuple[int, str]]) -> bool:
    parts = rel_path.split("/")
    return (
        len(parts) == 3
        and parts[0] == "services"
        and parts[1].startswith("llm_")
        and parts[2] in {"config.yml", "config.yaml"}
        and _has_top_level_key(lines, "model")
    )


def _has_key(lines: Iterable[tuple[int, str]], key: str) -> bool:
    prefix = f"{key}:"
    return any(stripped.startswith(prefix) for _indent, stripped in lines)


def _has_top_level_key(lines: Iterable[tuple[int, str]], key: str) -> bool:
    prefix = f"{key}:"
    return any(
        indent == 0 and stripped.startswith(prefix) for indent, stripped in lines
    )


def _section_ranges(
    lines: list[tuple[int, str]], section_key: str
) -> Iterable[tuple[int, int, int]]:
    section = f"{section_key}:"
    for index, (indent, stripped) in enumerate(lines):
        if stripped != section:
            continue
        end = len(lines)
        for next_index in range(index + 1, len(lines)):
            next_indent, _next_stripped = lines[next_index]
            if next_indent <= indent:
                end = next_index
                break
        yield index, indent, end


def _unique_values(values: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _collect_list_values(lines: list[tuple[int, str]], section_key: str) -> list[str]:
    values: list[str] = []
    for _index, base_indent, end in _section_ranges(lines, section_key):
        for indent, stripped in lines[_index + 1 : end]:
            if indent <= base_indent:
                break
            if stripped.startswith("- "):
                tail = stripped[2:].strip()
                if tail and not _mapping_key(tail):
                    values.append(_parse_scalar(tail))
    return _unique_values(values)


def _collect_named_items(lines: list[tuple[int, str]], section_key: str) -> list[str]:
    names: list[str] = []
    for index, base_indent, end in _section_ranges(lines, section_key):
        direct_item_indent = base_indent + 2
        current_indent = -1
        for indent, stripped in lines[index + 1 : end]:
            if indent <= base_indent:
                break
            item_started = stripped.startswith("- ")
            tail = stripped[2:].strip() if item_started else stripped
            if item_started:
                current_indent = indent if indent == direct_item_indent else -1
            if not _mapping_key(tail):
                continue
            key, value = _split_key_value(tail)
            if key not in {"name", "job_name"}:
                continue
            if item_started and current_indent == direct_item_indent:
                names.append(_parse_scalar(value))
            elif current_indent == direct_item_indent and indent == current_indent + 2:
                names.append(_parse_scalar(value))
    return _unique_values(names)


def _collect_field_values(
    lines: list[tuple[int, str]], section_key: str, field_key: str
) -> list[str]:
    values: list[str] = []
    for index, base_indent, end in _section_ranges(lines, section_key):
        for indent, stripped in lines[index + 1 : end]:
            if indent <= base_indent:
                break
            tail = stripped[2:].strip() if stripped.startswith("- ") else stripped
            if not _mapping_key(tail):
                continue
            key, value = _split_key_value(tail)
            if key == field_key:
                values.append(_parse_scalar(value))
    return _unique_values(values)


def _collect_values_after_key(
    lines: list[tuple[int, str]], section_key: str, field_key: str
) -> list[str]:
    values: list[str] = []
    for index, base_indent, end in _section_ranges(lines, section_key):
        for indent, stripped in lines[index + 1 : end]:
            if indent <= base_indent:
                break
            if not _mapping_key(stripped):
                continue
            key, value = _split_key_value(stripped)
            if key == field_key:
                values.append(_parse_scalar(value))
    return _unique_values(values)


def _first_value_for_key(lines: Iterable[tuple[int, str]], key: str) -> str:
    prefix = f"{key}:"
    for _indent, stripped in lines:
        if stripped.startswith(prefix):
            return _scalar_after_colon(stripped)
    return ""


def _yaml_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, stripped))
    return lines


def _mapping_key(stripped: str) -> bool:
    return ":" in stripped and stripped.split(":", 1)[0].strip() != ""


def _split_key_value(stripped: str) -> tuple[str, str]:
    key, _, value = stripped.partition(":")
    return key.strip(), value.strip()


def _scalar_after_colon(stripped: str) -> str:
    return _parse_scalar(stripped.split(":", 1)[1].strip())


def _parse_scalar(value: str) -> str:
    value = _strip_inline_comment(value.strip())
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _strip_inline_comment(value: str) -> str:
    quote = ""
    for index, char in enumerate(value):
        if char in {'"', "'"}:
            if not quote:
                quote = char
            elif quote == char:
                quote = ""
            continue
        if char == "#" and not quote and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value


def _parse_string_list(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [
            _parse_scalar(item.strip()) for item in inner.split(",") if item.strip()
        ]
    return [_parse_scalar(value)]


def _parse_github_triggers(lines: list[tuple[int, str]], start_index: int) -> list[str]:
    _indent, stripped = lines[start_index]
    value = stripped.split(":", 1)[1].strip()
    if value:
        return _parse_string_list(value)

    triggers: list[str] = []
    index = start_index + 1
    while index < len(lines):
        indent, child = lines[index]
        if indent == 0:
            break
        if indent == 2:
            if child.startswith("- "):
                triggers.append(_parse_scalar(child[2:].strip()))
            elif _mapping_key(child):
                triggers.append(child.split(":", 1)[0].strip())
        index += 1
    return triggers


def _new_actions_step() -> dict[str, str]:
    return {"name": "", "uses": "", "run": ""}


def _parse_actions_step_line(
    lines: list[tuple[int, str]],
    index: int,
    current_job: dict,
    current_step: dict | None,
) -> tuple[dict | None, int]:
    indent, stripped = lines[index]
    if indent == 6 and stripped.startswith("- "):
        current_step = _new_actions_step()
        current_job["steps"].append(current_step)
        tail = stripped[2:].strip()
        if _mapping_key(tail):
            key, value = _split_key_value(tail)
            _assign_step_value(current_step, key, value, lines, index)
        return current_step, index + 1

    if current_step is not None and indent >= 8 and _mapping_key(stripped):
        key, value = _split_key_value(stripped)
        next_index = _assign_step_value(current_step, key, value, lines, index)
        return current_step, next_index
    return current_step, index + 1


def _assign_step_value(
    step: dict[str, str],
    key: str,
    value: str,
    lines: list[tuple[int, str]],
    index: int,
) -> int:
    if key not in {"name", "uses", "run"}:
        return index + 1
    if key == "run" and value in {"|", ">"}:
        block, next_index = _collect_block_scalar(lines, index)
        step[key] = block
        return next_index
    step[key] = _parse_scalar(value)
    return index + 1


def _collect_block_scalar(
    lines: list[tuple[int, str]], start_index: int
) -> tuple[str, int]:
    start_indent, _stripped = lines[start_index]
    collected: list[str] = []
    index = start_index + 1
    while index < len(lines):
        indent, stripped = lines[index]
        if indent <= start_indent:
            break
        collected.append(stripped)
        index += 1
    return " ".join(collected), index


def _split_yaml_documents(text: str) -> list[str]:
    documents: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip() == "---":
            documents.append("\n".join(current))
            current = []
        else:
            current.append(line)
    documents.append("\n".join(current))
    return documents


def _parse_kubernetes_document(text: str) -> dict | None:
    lines = _yaml_lines(text)
    if not lines:
        return None

    resource = {
        "api_version": _top_level_value(lines, "apiVersion"),
        "kind": _top_level_value(lines, "kind"),
        "name": "",
        "namespace": "",
        "replicas": "",
        "containers": [],
        "service_type": "",
        "service_ports": [],
        "selector": {},
    }
    if not resource["kind"]:
        return None

    _fill_kubernetes_metadata(lines, resource)
    _fill_kubernetes_spec(lines, resource)
    return resource


def _top_level_value(lines: Iterable[tuple[int, str]], key: str) -> str:
    prefix = f"{key}:"
    for indent, stripped in lines:
        if indent == 0 and stripped.startswith(prefix):
            return _scalar_after_colon(stripped)
    return ""


def _fill_kubernetes_metadata(lines: list[tuple[int, str]], resource: dict) -> None:
    in_metadata = False
    for indent, stripped in lines:
        if indent == 0:
            in_metadata = stripped == "metadata:"
            continue
        if in_metadata and indent == 2:
            key, value = _split_key_value(stripped)
            if key in {"name", "namespace"}:
                resource[key] = _parse_scalar(value)


def _fill_kubernetes_spec(lines: list[tuple[int, str]], resource: dict) -> None:
    kind = str(resource.get("kind", ""))
    for index, (indent, stripped) in enumerate(lines):
        if indent == 2 and stripped.startswith("replicas:"):
            resource["replicas"] = _scalar_after_colon(stripped)
        if kind == "Service" and indent == 2 and stripped.startswith("type:"):
            resource["service_type"] = _scalar_after_colon(stripped)
        if stripped == "selector:":
            resource["selector"].update(_collect_mapping(lines, index))
        if stripped == "containers:":
            resource["containers"].extend(_collect_containers(lines, index))
        if kind == "Service" and stripped == "ports:":
            resource["service_ports"].extend(_collect_service_ports(lines, index))


def _collect_mapping(lines: list[tuple[int, str]], start_index: int) -> dict[str, str]:
    base_indent = lines[start_index][0]
    values: dict[str, str] = {}
    for indent, stripped in lines[start_index + 1 :]:
        if indent <= base_indent:
            break
        if indent == base_indent + 2 and _mapping_key(stripped):
            key, value = _split_key_value(stripped)
            values[key] = _parse_scalar(value)
    return values


def _collect_containers(lines: list[tuple[int, str]], start_index: int) -> list[dict]:
    base_indent = lines[start_index][0]
    containers: list[dict] = []
    current: dict | None = None
    current_section = ""
    section_indent = -1
    field_indent = base_indent + 4
    for indent, stripped in lines[start_index + 1 :]:
        if indent <= base_indent:
            break
        if stripped.startswith("- "):
            if indent == base_indent + 2:
                current = {
                    "name": "",
                    "image": "",
                    "ports": [],
                    "requests": {},
                    "limits": {},
                }
                containers.append(current)
                key, value = _split_key_value(stripped[2:].strip())
                if key in {"name", "image"}:
                    current[key] = _parse_scalar(value)
                current_section = ""
                section_indent = -1
            elif current is not None and current_section == "ports":
                key, value = _split_key_value(stripped[2:].strip())
                if key == "containerPort":
                    current["ports"].append(_parse_scalar(value))
            continue
        if current is None or not _mapping_key(stripped):
            continue
        key, value = _split_key_value(stripped)
        if indent == field_indent and key in {"name", "image"}:
            current[key] = _parse_scalar(value)
            current_section = ""
            section_indent = -1
        elif indent == field_indent and key == "ports":
            current_section = "ports"
            section_indent = indent
        elif key in {"requests", "limits"}:
            current_section = key
            section_indent = indent
        elif (
            current_section in {"requests", "limits"}
            and indent == section_indent + 2
            and value
        ):
            current[current_section][key] = _parse_scalar(value)
        elif indent <= section_indent:
            current_section = ""
            section_indent = -1
    return containers


def _collect_service_ports(
    lines: list[tuple[int, str]], start_index: int
) -> list[dict]:
    base_indent = lines[start_index][0]
    ports: list[dict] = []
    current: dict | None = None
    for indent, stripped in lines[start_index + 1 :]:
        if indent <= base_indent:
            break
        if stripped.startswith("- "):
            current = {"port": "", "target_port": "", "protocol": ""}
            ports.append(current)
            key, value = _split_key_value(stripped[2:].strip())
            _assign_service_port_value(current, key, value)
            continue
        if current is not None and _mapping_key(stripped):
            key, value = _split_key_value(stripped)
            _assign_service_port_value(current, key, value)
    return ports


def _assign_service_port_value(port: dict[str, str], key: str, value: str) -> None:
    if key == "targetPort":
        port["target_port"] = _parse_scalar(value)
    elif key in {"port", "protocol"}:
        port[key] = _parse_scalar(value)
