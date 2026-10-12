"""Conservative summaries for named CI, packaging, and automation YAML formats.

The caller supplies safely loaded documents. Recognition requires both an
expected repository path and the format's structural fields. Summaries contain
names and references, rather than arbitrary settings, defaults, or scripts.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from collections.abc import Sequence
from typing import Callable

from .yaml_syntax import yaml_mapping as _mapping, yaml_scalar as _text


def _items(value: object) -> list:
    return value if isinstance(value, list) else []


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    return [item for item in _items(value) if isinstance(item, str) and item]


def _names(value: object) -> list[str]:
    return [key for key in _mapping(value) if isinstance(key, str) and key]


def _result(family: str, title: str, sections: dict[str, list[str]]) -> dict:
    return {
        "type": "yaml_format",
        "yaml_format": family,
        "title": title,
        "sections": {
            name: list(dict.fromkeys(values))
            for name, values in sections.items()
            if values
        },
        "advisories": [],
    }


def _github_action(path: PurePosixPath, document: object) -> dict | None:
    if path.name not in {"action.yml", "action.yaml"}:
        return None
    data = _mapping(document)
    runs = _mapping(data.get("runs"))
    using = _text(runs.get("using"))
    if not _text(data.get("name")):
        return None
    sections = {
        "Inputs": _names(data.get("inputs")),
        "Outputs": _names(data.get("outputs")),
    }
    sections["Runtime"] = [using] if using else []
    if using == "composite" and isinstance(runs.get("steps"), list):
        steps = [_mapping(step) for step in _items(runs.get("steps"))]
        sections["Steps"] = [
            _text(step.get("name")) for step in steps if _text(step.get("name"))
        ]
        sections["Action references"] = [
            _text(step.get("uses")) for step in steps if _text(step.get("uses"))
        ]
    elif using.startswith("node") and using[4:].isdigit() and _text(runs.get("main")):
        sections["Entry points"] = [
            _text(runs.get(key))
            for key in ("main", "pre", "post")
            if _text(runs.get(key))
        ]
    elif using == "docker" and _text(runs.get("image")):
        sections["Image"] = [_text(runs.get("image"))]
    else:
        return None
    return _result("github_action", _text(data.get("name")), sections)


_GITLAB_RESERVED = {
    "stages",
    "include",
    "default",
    "variables",
    "workflow",
    "image",
    "services",
    "before_script",
    "after_script",
    "cache",
    "spec",
    "types",
}


def _gitlab_ci(path: PurePosixPath, document: object) -> dict | None:
    if path.name not in {".gitlab-ci.yml", ".gitlab-ci.yaml"} and path.parts[:2] != (
        ".gitlab",
        "ci",
    ):
        return None
    data = _mapping(document)
    jobs = {
        key: value
        for key, value in data.items()
        if isinstance(key, str)
        and key not in _GITLAB_RESERVED
        and isinstance(value, dict)
        and (
            _strings(value.get("script"))
            or _strings(value.get("extends"))
            or isinstance(value.get("trigger"), (str, dict))
        )
    }
    includes = data.get("include")
    includes = includes if isinstance(includes, list) else [includes]
    references: list[str] = []
    for entry in includes:
        if isinstance(entry, str):
            references.append(entry)
        else:
            mapping = _mapping(entry)
            for key in ("local", "project", "file", "template", "component"):
                references.extend(_strings(mapping.get(key)))
    if not jobs and not references:
        return None
    return _result(
        "gitlab_ci",
        "GitLab CI",
        {
            "Stages": _strings(data.get("stages")),
            "Jobs": list(jobs),
            "Includes": references,
            "Job dependencies": [
                item for job in jobs.values() for item in _strings(job.get("extends"))
            ],
        },
    )


def _circle_ci(path: PurePosixPath, document: object) -> dict | None:
    if (
        path.as_posix() != ".circleci/config.yml"
        and path.as_posix() != ".circleci/config.yaml"
    ):
        return None
    data = _mapping(document)
    if _text(data.get("version")) not in {"2", "2.0", "2.1"}:
        return None
    if not isinstance(data.get("jobs"), dict) and not isinstance(
        data.get("workflows"), dict
    ):
        return None
    workflows = _mapping(data.get("workflows"))
    return _result(
        "circleci",
        "CircleCI",
        {
            "Jobs": _names(data.get("jobs")),
            "Workflows": [name for name in _names(workflows) if name != "version"],
            "Orbs": _names(data.get("orbs")),
            "Executors": _names(data.get("executors")),
            "Commands": _names(data.get("commands")),
        },
    )


def _pipeline_fields(data: dict, field: str, depth: int = 0) -> list[str]:
    if depth >= 16:
        return []
    values = _strings(data.get(field))
    for section in ("stages", "jobs", "steps"):
        for item in _items(data.get(section)):
            values.extend(_pipeline_fields(_mapping(item), field, depth + 1))
    return values


def _azure_pipeline(path: PurePosixPath, document: object) -> dict | None:
    if not path.name.startswith("azure-pipelines") or path.suffix not in {
        ".yml",
        ".yaml",
    }:
        return None
    data = _mapping(document)
    fields = (
        "stage",
        "job",
        "deployment",
        "template",
        "task",
        "script",
        "bash",
        "pwsh",
        "powershell",
        "checkout",
        "download",
        "publish",
    )
    if not any(
        isinstance(item, dict) and any(field in item for field in fields)
        for key in ("stages", "jobs", "steps")
        for item in _items(data.get(key))
    ):
        return None
    return _result(
        "azure_pipelines",
        "Azure Pipelines",
        {
            "Stages": _pipeline_fields(data, "stage"),
            "Jobs": _pipeline_fields(data, "job")
            + _pipeline_fields(data, "deployment"),
            "Templates": _pipeline_fields(data, "template"),
            "Tasks": _pipeline_fields(data, "task"),
            "Step names": _pipeline_fields(data, "displayName"),
        },
    )


def _kustomize(path: PurePosixPath, document: object) -> dict | None:
    if path.name not in {"kustomization.yaml", "kustomization.yml", "Kustomization"}:
        return None
    data = _mapping(document)
    typed = data.get("kind") == "Kustomization" and _text(
        data.get("apiVersion")
    ).startswith("kustomize.config.k8s.io/")
    fields = (
        "resources",
        "bases",
        "components",
        "generators",
        "transformers",
        "configMapGenerator",
        "secretGenerator",
        "patches",
        "patchesStrategicMerge",
        "helmCharts",
    )
    if not typed and not any(isinstance(data.get(key), list) for key in fields):
        return None
    sections = {
        key.title(): _strings(data.get(key))
        for key in (
            "resources",
            "bases",
            "components",
            "generators",
            "transformers",
            "patchesStrategicMerge",
        )
    }
    for key in ("configMapGenerator", "secretGenerator", "helmCharts"):
        sections[key] = [
            _text(_mapping(item).get("name"))
            for item in _items(data.get(key))
            if _text(_mapping(item).get("name"))
        ]
    sections["Patch files"] = [
        _text(_mapping(item).get("path"))
        for item in _items(data.get("patches"))
        if _text(_mapping(item).get("path"))
    ]
    return _result("kustomize", "Kustomize", sections)


def _helm_chart(path: PurePosixPath, document: object) -> dict | None:
    if path.name not in {"Chart.yaml", "Chart.yml"}:
        return None
    data = _mapping(document)
    if (
        data.get("apiVersion") not in {"v1", "v2"}
        or not _text(data.get("name"))
        or not _text(data.get("version"))
    ):
        return None
    dependencies = [_mapping(item) for item in _items(data.get("dependencies"))]
    return _result(
        "helm_chart",
        _text(data.get("name")),
        {
            "Version": [_text(data.get("version"))],
            "Application version": _strings(data.get("appVersion")),
            "Type": _strings(data.get("type")),
            "Dependencies": [
                _text(item.get("name"))
                for item in dependencies
                if _text(item.get("name"))
            ],
        },
    )


def _task_names(tasks: object, depth: int = 0) -> list[str]:
    if depth >= 16:
        return []
    names: list[str] = []
    for task in _items(tasks):
        mapping = _mapping(task)
        names.extend(_strings(mapping.get("name")))
        for key in ("block", "rescue", "always"):
            names.extend(_task_names(mapping.get(key), depth + 1))
    return names


def _ansible_playbook(path: PurePosixPath, document: object) -> dict | None:
    if (
        path.name not in {"playbook.yml", "playbook.yaml", "site.yml", "site.yaml"}
        and "playbooks" not in path.parts
    ):
        return None
    plays = _items(document)
    if not plays or not all(
        isinstance(play, dict)
        and (_strings(play.get("hosts")) or _text(play.get("import_playbook")))
        for play in plays
    ):
        return None
    sections: dict[str, list[str]] = {
        "Plays": [],
        "Hosts": [],
        "Tasks": [],
        "Roles": [],
        "Imported playbooks": [],
    }
    for play in plays:
        sections["Plays"].extend(_strings(play.get("name")))
        sections["Hosts"].extend(_strings(play.get("hosts")))
        sections["Imported playbooks"].extend(_strings(play.get("import_playbook")))
        for key in ("tasks", "pre_tasks", "post_tasks", "handlers"):
            sections["Tasks"].extend(_task_names(play.get(key)))
        for role in _items(play.get("roles")):
            sections["Roles"].extend(
                _strings(role)
                if isinstance(role, str)
                else _strings(_mapping(role).get("role"))
            )
    return _result("ansible_playbook", "Ansible playbook", sections)


_PARSERS: tuple[Callable[[PurePosixPath, object], dict | None], ...] = (
    _github_action,
    _gitlab_ci,
    _circle_ci,
    _azure_pipeline,
    _kustomize,
    _helm_chart,
    _ansible_playbook,
)


def parse_extended_yaml(rel_path: str, documents: Sequence[object]) -> dict | None:
    """Recognize a single named YAML format without claiming mixed documents."""
    populated = [document for document in documents if document is not None]
    if len(populated) != 1:
        return None
    path = PurePosixPath(rel_path.replace("\\", "/"))
    if path.suffix not in {".yaml", ".yml"} and path.name != "Kustomization":
        return None
    for parser in _PARSERS:
        result = parser(path, populated[0])
        if result is not None:
            return result
    return None
