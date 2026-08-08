"""Shared team policy and conservative wiki conflict resolution."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..config import DEFAULT_WIKI_DIR
from .io import read_md, write_json_atomic, write_md
from .plugins import PluginError, iter_components
from .validation import require_exact_fields, require_string_list

if TYPE_CHECKING:
    from .source_snapshot import SourceSnapshot
    from .sync_manifest import SyncManifest

TEAM_CONFIG_PATH = Path(".llm-wiki") / "team.json"
TEAM_CONFIG_VERSION = 1
CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")

DEFAULT_TEAM_CONFIG: dict[str, Any] = {
    "version": TEAM_CONFIG_VERSION,
    "wiki_dir": DEFAULT_WIKI_DIR,
    "conventions": {
        "required_files": ["index.md", "log.md"],
        "required_dirs": ["entities", "modules", "workflows", "infrastructure"],
        "require_log": True,
        "canonical_naming": True,
        "required_entity_sections": [
            "Description",
            "Attributes",
            "Methods",
            "Relationships",
        ],
        "required_module_sections": ["Description"],
        "required_infrastructure_sections": [],
        "workflow_filename_pattern": r"^[A-Za-z0-9_.-]+$",
    },
    "agent": {
        "prompt_template": None,
        "required_lint_rules": [],
        "required_skills": [],
    },
}

_TOP_LEVEL_KEYS = {"version", "wiki_dir", "conventions", "agent"}
_CONVENTION_KEYS = {
    "required_files",
    "required_dirs",
    "require_log",
    "canonical_naming",
    "required_entity_sections",
    "required_module_sections",
    "required_infrastructure_sections",
    "workflow_filename_pattern",
}
_AGENT_KEYS = {"prompt_template", "required_lint_rules", "required_skills"}


class TeamConfigError(ValueError):
    """Raised when `.llm-wiki/team.json` is invalid."""


@dataclass(frozen=True)
class TeamConventionRequest:
    """Inputs needed to check wiki files against team conventions."""

    config: dict[str, Any]
    wiki_dir: str | Path
    src_dir: str
    inventory: dict[str, Any]
    docker_inventory: dict[str, Any] | None = None

    @property
    def wiki_path(self) -> Path:
        return Path(self.wiki_dir)


def default_team_config(wiki_dir: str = DEFAULT_WIKI_DIR) -> dict[str, Any]:
    config = deepcopy(DEFAULT_TEAM_CONFIG)
    config["wiki_dir"] = wiki_dir
    return config


def team_config_path(root: str | Path = ".") -> Path:
    return Path(root) / TEAM_CONFIG_PATH


def write_default_team_config(
    wiki_dir: str = DEFAULT_WIKI_DIR, *, root: str | Path = "."
) -> Path:
    path = team_config_path(root)
    return write_json_atomic(path, default_team_config(wiki_dir))


def _reject_unknown_keys(data: dict[str, Any], allowed: set[str], scope: str) -> None:
    return require_exact_fields(
        data,
        allowed=allowed,
        required=(),
        mapping_error=TeamConfigError(f"{scope} must be a mapping"),
        missing_error=lambda _fields: AssertionError("no required fields"),
        unknown_error=lambda fields: TeamConfigError(
            f"{scope} contains unknown key(s): {', '.join(fields)}"
        ),
    )


def _ensure_string_list(value: Any, field: str) -> list[str]:
    return require_string_list(
        value,
        error=TeamConfigError(f"{field} must be a list of strings."),
    )


def validate_team_config(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise TeamConfigError("team config must be a JSON object.")
    _reject_unknown_keys(data, _TOP_LEVEL_KEYS, "team config")

    if data.get("version") != TEAM_CONFIG_VERSION:
        raise TeamConfigError(f"version must be {TEAM_CONFIG_VERSION}.")
    if not isinstance(data.get("wiki_dir"), str) or not data["wiki_dir"]:
        raise TeamConfigError("wiki_dir must be a non-empty string.")

    conventions = data.get("conventions")
    if not isinstance(conventions, dict):
        raise TeamConfigError("conventions must be an object.")
    _reject_unknown_keys(conventions, _CONVENTION_KEYS, "conventions")
    for key in (
        "required_files",
        "required_dirs",
        "required_entity_sections",
        "required_module_sections",
        "required_infrastructure_sections",
    ):
        _ensure_string_list(conventions.get(key), f"conventions.{key}")
    if not isinstance(conventions.get("require_log"), bool):
        raise TeamConfigError("conventions.require_log must be a boolean.")
    if not isinstance(conventions.get("canonical_naming"), bool):
        raise TeamConfigError("conventions.canonical_naming must be a boolean.")
    pattern = conventions.get("workflow_filename_pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            raise TeamConfigError(
                "conventions.workflow_filename_pattern must be a string or null."
            )
        try:
            re.compile(pattern)
        except re.error as exc:
            raise TeamConfigError(
                f"conventions.workflow_filename_pattern is invalid: {exc}"
            ) from exc

    agent = data.get("agent")
    if not isinstance(agent, dict):
        raise TeamConfigError("agent must be an object.")
    _reject_unknown_keys(agent, _AGENT_KEYS, "agent")
    prompt_template = agent.get("prompt_template")
    if prompt_template is not None and not isinstance(prompt_template, str):
        raise TeamConfigError("agent.prompt_template must be a string or null.")
    _ensure_string_list(agent.get("required_lint_rules"), "agent.required_lint_rules")
    _ensure_string_list(agent.get("required_skills"), "agent.required_skills")
    return data


def load_team_config(
    *, required: bool = False, root: str | Path = "."
) -> dict[str, Any] | None:
    path = team_config_path(root)
    if not path.exists():
        if required:
            raise TeamConfigError(f"Missing team config: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TeamConfigError(f"Invalid JSON in {path}: {exc}") from exc
    return validate_team_config(data)


def team_prompt_template_default(root: str | Path = ".") -> str | None:
    config = load_team_config(required=False, root=root)
    if not config:
        return None
    return config["agent"].get("prompt_template")


def _issue(
    category: str, message: str, *, path: str | None = None, target: str | None = None
) -> dict[str, str | None]:
    return {
        "category": category,
        "message": message,
        "severity": "error",
        "path": path,
        "target": target,
    }


@lru_cache(maxsize=None)
def _section_pattern(section: str) -> re.Pattern[str]:
    return re.compile(rf"^##\s+{re.escape(section)}\s*$", re.MULTILINE)


def _has_section(content: str, section: str) -> bool:
    return _section_pattern(section).search(content) is not None


def _plugin_refs_by_type(root: str | Path = ".") -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {
        "lint_rule": set(),
        "skill": set(),
        "prompt_template": set(),
    }
    for component_type in refs:
        for component in iter_components(component_type, root=root):
            refs[component_type].add(component["ref"])
            refs[component_type].add(component["id"])
    return refs


def check_plugin_requirements(
    config: dict[str, Any], *, root: str | Path = "."
) -> list[dict[str, str | None]]:
    issues: list[dict[str, str | None]] = []
    try:
        refs = _plugin_refs_by_type(root)
    except PluginError as exc:
        return [
            _issue(
                "team_plugin_requirement",
                f"Could not read installed plugin lockfile: {exc}",
            )
        ]

    agent = config["agent"]
    prompt_template = agent.get("prompt_template")
    if prompt_template and prompt_template not in refs["prompt_template"]:
        issues.append(
            _issue(
                "team_plugin_requirement",
                f"Required prompt template is not installed: {prompt_template}",
                target=prompt_template,
            )
        )
    for rule in agent.get("required_lint_rules", []):
        if rule not in refs["lint_rule"]:
            issues.append(
                _issue(
                    "team_plugin_requirement",
                    f"Required lint rule is not installed: {rule}",
                    target=rule,
                )
            )
    for skill in agent.get("required_skills", []):
        if skill not in refs["skill"]:
            issues.append(
                _issue(
                    "team_plugin_requirement",
                    f"Required skill is not installed: {skill}",
                    target=skill,
                )
            )
    return issues


def check_team_conventions(
    request: TeamConventionRequest,
) -> list[dict[str, str | None]]:
    from .bootstrap_runtime import (
        build_entity_occurrence_page_map,
        build_module_page_map,
    )
    from .extraction_service import get_docker_inventory

    wiki_path = request.wiki_path
    conventions = request.config["conventions"]
    issues: list[dict[str, str | None]] = []

    for rel in conventions["required_files"]:
        if not (wiki_path / rel).is_file():
            issues.append(
                _issue(
                    "team_conventions",
                    f"Missing required team wiki file: {rel}",
                    path=rel,
                )
            )
    for rel in conventions["required_dirs"]:
        if not (wiki_path / rel).is_dir():
            issues.append(
                _issue(
                    "team_conventions",
                    f"Missing required team wiki directory: {rel}/",
                    path=rel,
                )
            )
    if conventions["require_log"] and not (wiki_path / "log.md").is_file():
        issues.append(
            _issue(
                "team_conventions",
                "Missing required architectural log: log.md",
                path="log.md",
            )
        )

    section_checks = [
        ("entities", "required_entity_sections"),
        ("modules", "required_module_sections"),
        ("infrastructure", "required_infrastructure_sections"),
    ]
    for dirname, key in section_checks:
        for page in (
            sorted((wiki_path / dirname).glob("*.md"))
            if (wiki_path / dirname).exists()
            else []
        ):
            rel = page.relative_to(wiki_path).as_posix()
            content = read_md(page)
            for section in conventions[key]:
                if not _has_section(content, section):
                    issues.append(
                        _issue(
                            "team_conventions",
                            f"{rel} is missing required section: {section}",
                            path=rel,
                            target=section,
                        )
                    )

    pattern = conventions.get("workflow_filename_pattern")
    if pattern and (wiki_path / "workflows").exists():
        workflow_re = re.compile(pattern)
        for page in sorted((wiki_path / "workflows").glob("*.md")):
            if not workflow_re.match(page.stem):
                rel = page.relative_to(wiki_path).as_posix()
                issues.append(
                    _issue(
                        "team_conventions",
                        f"Workflow page name does not match team pattern {pattern}: {page.name}",
                        path=rel,
                    )
                )

    if conventions["canonical_naming"]:
        expected_entities = set(
            build_entity_occurrence_page_map(request.inventory).values()
        )
        documented_entities = (
            {p.stem for p in (wiki_path / "entities").glob("*.md")}
            if (wiki_path / "entities").exists()
            else set()
        )
        for name in sorted(documented_entities - expected_entities):
            issues.append(
                _issue(
                    "team_canonical_naming",
                    f"Entity page does not match canonical generated naming: {name}.md",
                    path=f"entities/{name}.md",
                    target=name,
                )
            )

        expected_modules = set(build_module_page_map(request.inventory).values())
        documented_modules = (
            {p.stem for p in (wiki_path / "modules").glob("*.md")}
            if (wiki_path / "modules").exists()
            else set()
        )
        for name in sorted(documented_modules - expected_modules):
            issues.append(
                _issue(
                    "team_canonical_naming",
                    f"Module page does not match canonical generated naming: {name}.md",
                    path=f"modules/{name}.md",
                    target=name,
                )
            )

        docker_inventory = request.docker_inventory
        if docker_inventory is None:
            docker_inventory = get_docker_inventory(request.src_dir)
        expected_infra = {
            f.replace("\\", "/").replace("/", "_").replace(".", "_")
            for f in docker_inventory
        }
        documented_infra = (
            {p.stem for p in (wiki_path / "infrastructure").glob("*.md")}
            if (wiki_path / "infrastructure").exists()
            else set()
        )
        for name in sorted(documented_infra - expected_infra):
            issues.append(
                _issue(
                    "team_canonical_naming",
                    f"Infrastructure page does not match canonical generated naming: {name}.md",
                    path=f"infrastructure/{name}.md",
                    target=name,
                )
            )

    return issues


def build_team_issues(
    wiki_dir: str | Path,
    src_dir: str,
    inventory: dict,
    pages: list[Path],
    *,
    require_config: bool = False,
    root: str | Path = ".",
    docker_inventory: dict | None = None,
) -> list[dict[str, str | None]]:
    try:
        config = load_team_config(required=require_config, root=root)
    except TeamConfigError as exc:
        return [_issue("team_config", str(exc), path=str(team_config_path(root)))]
    if not config:
        return []
    return check_plugin_requirements(config, root=root) + check_team_conventions(
        TeamConventionRequest(
            config=config,
            wiki_dir=wiki_dir,
            src_dir=src_dir,
            inventory=inventory,
            docker_inventory=docker_inventory,
        )
    )


def has_conflict_markers(text: str) -> bool:
    return all(marker in text for marker in CONFLICT_MARKERS)


def _existing_page_entries(directory: Path, extra_key: str) -> list[dict[str, str]]:
    if not directory.exists():
        return []
    return [{"name": p.stem, extra_key: ""} for p in sorted(directory.glob("*.md"))]


def _index_content(wiki_dir: Path, inventory: dict) -> str:
    from .bootstrap_runtime import (
        _generate_index_md,
        build_entity_occurrence_page_map,
        build_module_page_map,
    )

    module_page_map = build_module_page_map(inventory)
    entity_page_map = build_entity_occurrence_page_map(inventory, module_page_map)
    entity_names: list[str] = []
    seen: set[str] = set()
    module_entries: list[dict[str, str]] = []
    for filepath, file_data in inventory.items():
        module_entries.append(
            {
                "name": module_page_map[filepath],
                "path": filepath,
                "docstring": file_data.get("module_docstring", ""),
            }
        )
        seen_names: dict[str, int] = {}
        for cls in file_data.get("classes", []):
            cls_name = cls["name"]
            seen_names[cls_name] = seen_names.get(cls_name, 0) + 1
            name = entity_page_map[(cls_name, filepath, seen_names[cls_name])]
            if name not in seen:
                entity_names.append(name)
                seen.add(name)
    return _generate_index_md(
        entity_names,
        module_entries,
        workflow_entries=(
            _existing_page_entries(wiki_dir / "workflows", "entry") or None
        ),
        guide_entries=_existing_page_entries(wiki_dir / "guides", "topic") or None,
        infra_entries=(
            _existing_page_entries(wiki_dir / "infrastructure", "type") or None
        ),
        flow_entries=[
            {"id": path.stem, "category": path.stem.split("-", 1)[0]}
            for path in sorted((wiki_dir / "flows").glob("*.md"))
        ]
        or None,
        architecture_entries=[
            {"name": label, "page": stem}
            for stem, label in (
                ("dependencies", "Dependencies"),
                ("load-order", "Load order"),
            )
            if (wiki_dir / f"{stem}.md").is_file()
        ]
        or None,
        api_contracts_present=(wiki_dir / "api-contracts.md").is_file(),
    )


def _manifest_content(
    inventory: dict,
    src_dir: str,
    *,
    wiki_dir: Path | None = None,
    surfaces: dict[str, dict] | None = None,
    generation_inputs: dict[str, object] | None = None,
    previous_manifest: SyncManifest | None = None,
    source_snapshot: SourceSnapshot | None = None,
) -> str:
    from .bootstrap_runtime import (
        build_entity_occurrence_page_map,
        build_entity_page_map,
        build_module_page_map,
    )
    from .sync_manifest import (
        MANIFEST_STATE_UNAVAILABLE,
        SyncManifest,
        prune_manifest_for_source_selection,
        retained_concept_page_paths,
    )
    from .source_selection import with_source_selection_generation_input

    module_page_map = build_module_page_map(inventory)
    effective_generation_inputs = generation_inputs
    if source_snapshot is not None:
        effective_generation_inputs = with_source_selection_generation_input(
            generation_inputs,
            source_snapshot.source_selection_identity,
            source_snapshot.source_selection_inputs,
        )
    retained_page_paths = (
        retained_concept_page_paths(wiki_dir) if wiki_dir is not None else None
    )
    if (
        source_snapshot is not None
        and source_snapshot.source_selection_policy is not None
        and previous_manifest is not None
    ):
        prune_result = prune_manifest_for_source_selection(
            previous_manifest,
            source_snapshot.source_selection_policy,
            source_snapshot=source_snapshot,
        )
        previous_manifest = prune_result.manifest
        if retained_page_paths is not None:
            retained_page_paths = tuple(
                sorted(
                    set(retained_page_paths)
                    - set(prune_result.deselected_page_paths)
                )
            )
    manifest = SyncManifest.build_from_inventory(
        inventory,
        src_dir,
        build_entity_page_map(inventory),
        module_page_map,
        entity_occurrence_page_cache=build_entity_occurrence_page_map(
            inventory, module_page_map
        ),
        surfaces=surfaces,
        generation_inputs=effective_generation_inputs,
        previous_manifest=previous_manifest,
        retained_page_paths=retained_page_paths,
        unknown_evidence_reason=MANIFEST_STATE_UNAVAILABLE,
        source_content_hashes=(
            source_snapshot.hashes_for(inventory)
            if source_snapshot is not None
            else None
        ),
    )
    return manifest.to_json()


def _conflict_variants(text: str) -> tuple[str, str]:
    ours: list[str] = []
    theirs: list[str] = []
    side = "both"
    for line in text.splitlines():
        if line.startswith("<<<<<<<"):
            side = "ours"
            continue
        if side == "ours" and line.startswith("======="):
            side = "theirs"
            continue
        if side == "theirs" and line.startswith(">>>>>>>"):
            side = "both"
            continue
        if side in {"both", "ours"}:
            ours.append(line)
        if side in {"both", "theirs"}:
            theirs.append(line)
    return "\n".join(ours), "\n".join(theirs)


def _manifest_resolution_state_from_conflict(
    text: str,
) -> tuple[
    dict[str, dict] | None,
    dict[str, object] | None,
    SyncManifest | None,
    str,
]:
    from .sync_manifest import MANIFEST_VERSION, SyncManifest, SyncManifestError

    variants = _conflict_variants(text)
    parsed: list[dict] = []
    v5_manifests: list[SyncManifest] = []
    v5_advertised = False
    invalid_v5 = False
    for variant in variants:
        try:
            payload = json.loads(variant)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(payload, dict):
            parsed.append(payload)
            if payload.get("version") == MANIFEST_VERSION:
                v5_advertised = True
                try:
                    v5_manifests.append(SyncManifest.from_payload(payload))
                except (SyncManifestError, TypeError, ValueError):
                    invalid_v5 = True
    if not parsed:
        return {}, {}, None, ""

    if v5_advertised:
        if invalid_v5 or len(v5_manifests) != len(variants):
            return (
                None,
                None,
                None,
                "manifest v5 state cannot be validated on both sides and "
                "requires manual resolution",
            )
        operational_fields = (
            "surfaces",
            "generation_inputs",
            "page_source_mappings",
            "evidence_baselines",
            "tombstones",
        )
        manifest_payloads = [manifest.to_payload() for manifest in v5_manifests]
        operational_payloads = [
            {field: payload[field] for field in operational_fields}
            for payload in manifest_payloads
        ]
        if operational_payloads[0] != operational_payloads[1]:
            return (
                None,
                None,
                None,
                "manifest v5 operational state differs and requires manual resolution",
            )
        agreed = v5_manifests[0].without_artifact_hashes()
        return agreed.surfaces, agreed.generation_inputs, agreed, ""

    preserved: dict[str, dict] = {}
    for key in ("surfaces", "generation_inputs"):
        explicit_values = [
            payload[key]
            for payload in parsed
            if key in payload and isinstance(payload[key], dict)
        ]
        values = explicit_values or [{}]
        unique = {json.dumps(value, sort_keys=True) for value in values}
        if len(unique) > 1:
            label = key.replace("_", " ")
            return (
                None,
                None,
                None,
                f"manifest {label} differ and require manual resolution",
            )
        preserved[key] = values[0]
    return preserved["surfaces"], preserved["generation_inputs"], None, ""


def _manifest_state_from_conflict(
    text: str,
) -> tuple[dict[str, dict] | None, dict[str, object] | None, str]:
    """Return the legacy three-field view used by callers and tests."""

    surfaces, generation_inputs, _manifest, error = (
        _manifest_resolution_state_from_conflict(text)
    )
    return surfaces, generation_inputs, error


def _module_content(page_stem: str, inventory: dict) -> tuple[str | None, str]:
    from .bootstrap_runtime import (
        _generate_module_md,
        build_entity_occurrence_page_map,
        build_module_page_map,
    )

    module_page_map = build_module_page_map(inventory)
    matches = [
        filepath for filepath, stem in module_page_map.items() if stem == page_stem
    ]
    if len(matches) != 1:
        return None, "module page does not map unambiguously to a live source file"
    filepath = matches[0]
    entity_occurrence_map = build_entity_occurrence_page_map(inventory, module_page_map)
    file_entity_page_map: dict[str, str] = {}
    seen_names: dict[str, int] = {}
    for cls in inventory[filepath].get("classes", []):
        cls_name = cls["name"]
        seen_names[cls_name] = seen_names.get(cls_name, 0) + 1
        file_entity_page_map.setdefault(
            cls_name,
            entity_occurrence_map[(cls_name, filepath, seen_names[cls_name])],
        )
    return _generate_module_md(
        filepath,
        inventory[filepath],
        file_entity_page_map,
        entity_occurrence_page_map=entity_occurrence_map,
    ), "regenerated module page"


def _entity_content(page_stem: str, inventory: dict) -> tuple[str | None, str]:
    from .bootstrap_runtime import (
        _build_relationships,
        _generate_entity_md,
        build_entity_occurrence_page_map,
        build_module_page_map,
    )

    module_page_map = build_module_page_map(inventory)
    entity_page_map = build_entity_occurrence_page_map(inventory, module_page_map)
    matches = [
        (cls_name, filepath, occurrence)
        for (cls_name, filepath, occurrence), stem in entity_page_map.items()
        if stem == page_stem
    ]
    if len(matches) != 1:
        return None, "entity page does not map unambiguously to a live source entity"
    cls_name, filepath, occurrence = matches[0]
    class_info = None
    seen = 0
    for cls in inventory[filepath].get("classes", []):
        if cls["name"] != cls_name:
            continue
        seen += 1
        if seen == occurrence:
            class_info = cls
            break
    if class_info is None:
        return None, "entity page maps to a missing class"
    relationships = _build_relationships(inventory, module_page_map)
    return _generate_entity_md(
        class_info, filepath, relationships, module_page_map[filepath]
    ), "regenerated entity page"


def _infrastructure_content(
    page_stem: str,
    inventory: dict,
    src_dir: str,
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> tuple[str | None, str]:
    from .bootstrap_runtime import _generate_docker_md, build_module_page_map
    from .extraction_service import get_docker_inventory

    docker_inventory = get_docker_inventory(
        src_dir,
        source_snapshot=source_snapshot,
    )
    matches = [
        (docker_file, docker_info)
        for docker_file, docker_info in docker_inventory.items()
        if docker_file.replace("\\", "/").replace("/", "_").replace(".", "_")
        == page_stem
    ]
    if len(matches) != 1:
        return (
            None,
            "infrastructure page does not map unambiguously to a live Docker/Compose file",
        )
    docker_file, docker_info = matches[0]
    return _generate_docker_md(
        docker_file, docker_info, build_module_page_map(inventory)
    ), "regenerated infrastructure page"


def _merge_conflicted_log(text: str) -> str:
    output: list[str] = []
    seen: set[str] = set()
    in_conflict = False
    side = "base"
    ours: list[str] = []
    theirs: list[str] = []

    def append_unique(lines: list[str]) -> None:
        for line in lines:
            key = line.rstrip()
            if key and key in seen:
                continue
            output.append(line)
            if key:
                seen.add(key)

    for raw_line in text.splitlines():
        if raw_line.startswith("<<<<<<<"):
            in_conflict = True
            side = "ours"
            ours = []
            theirs = []
            continue
        if in_conflict and raw_line.startswith("======="):
            side = "theirs"
            continue
        if in_conflict and raw_line.startswith(">>>>>>>"):
            append_unique(ours)
            append_unique(theirs)
            in_conflict = False
            side = "base"
            continue
        if not in_conflict:
            append_unique([raw_line])
        elif side == "ours":
            ours.append(raw_line)
        else:
            theirs.append(raw_line)
    if in_conflict:
        append_unique(ours)
        append_unique(theirs)
    return "\n".join(output).rstrip() + "\n"


def _resolution_for_path(
    rel_path: str,
    path: Path,
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> tuple[str | None, str]:
    if rel_path == "index.md":
        return _index_content(
            wiki_dir, inventory
        ), "rebuilt index from current inventory"
    if rel_path == ".llm-wiki-manifest.json":
        (
            surfaces,
            generation_inputs,
            previous_manifest,
            error,
        ) = _manifest_resolution_state_from_conflict(read_md(path))
        if surfaces is None:
            return None, error
        return _manifest_content(
            inventory,
            src_dir,
            wiki_dir=wiki_dir,
            surfaces=surfaces,
            generation_inputs=generation_inputs,
            previous_manifest=previous_manifest,
            source_snapshot=source_snapshot,
        ), (
            "reconciled agreed v5 manifest state with current inventory"
            if previous_manifest is not None
            else "rebuilt sync manifest from current inventory"
        )
    if rel_path == "log.md":
        return _merge_conflicted_log(
            read_md(path)
        ), "merged unique log lines from both sides"
    if rel_path.startswith("modules/") and path.suffix == ".md":
        return _module_content(path.stem, inventory)
    if rel_path.startswith("entities/") and path.suffix == ".md":
        return _entity_content(path.stem, inventory)
    if rel_path.startswith("infrastructure/") and path.suffix == ".md":
        return _infrastructure_content(
            path.stem,
            inventory,
            src_dir,
            source_snapshot=source_snapshot,
        )
    if rel_path.startswith("workflows/"):
        return None, "workflow conflicts require manual resolution"
    return None, "file is not a supported safe wiki conflict target"


def resolve_conflicts(
    wiki_dir: str | Path,
    src_dir: str,
    *,
    write: bool = False,
    source_selection: str | Path | None = None,
) -> dict[str, Any]:
    from .extraction_service import get_inventory_result
    from .source_selection import (
        SourceSelectionError,
        resolve_source_selection,
        validate_persisted_source_selection_identity,
    )
    from .source_snapshot import (
        build_source_snapshot,
        capture_source_selection_inputs,
    )
    from .sync_manifest import SyncManifest

    wiki_path = Path(wiki_dir)
    policy = resolve_source_selection(src_dir, source_selection)
    try:
        previous_manifest = SyncManifest.load(wiki_path)
    except FileNotFoundError:
        generation_inputs = (
            {}
            if wiki_path.is_dir() and next(wiki_path.iterdir(), None) is not None
            else None
        )
    except (OSError, TypeError, UnicodeError, ValueError):
        manifest_path = wiki_path / ".llm-wiki-manifest.json"
        try:
            manifest_text = read_md(manifest_path)
        except OSError:
            manifest_text = ""
        if has_conflict_markers(manifest_text):
            _surfaces, conflict_inputs, _manifest, _error = (
                _manifest_resolution_state_from_conflict(manifest_text)
            )
        else:
            conflict_inputs = None
        if conflict_inputs is not None:
            generation_inputs = conflict_inputs
        else:
            raise SourceSelectionError(
                "source_selection",
                "team resolve-conflicts cannot validate the managed wiki "
                "boundary from its conflicted manifest; restore it or run sync",
            )
    else:
        generation_inputs = previous_manifest.generation_inputs
    validate_persisted_source_selection_identity(
        generation_inputs,
        None if policy is None else policy.identity,
        operation="team resolve-conflicts",
    )
    selection_inputs = capture_source_selection_inputs(
        src_dir,
        source_selection=source_selection,
        selection_policy=policy,
    )
    validate_persisted_source_selection_identity(
        generation_inputs,
        None if policy is None else policy.identity,
        operation="team resolve-conflicts",
        live_selection_inputs=selection_inputs,
    )
    source_snapshot = build_source_snapshot(
        src_dir,
        source_selection=source_selection,
        selection_policy=policy,
        expected_selection_inputs=selection_inputs,
    )
    validate_persisted_source_selection_identity(
        generation_inputs,
        source_snapshot.source_selection_identity,
        operation="team resolve-conflicts",
        live_selection_inputs=source_snapshot.source_selection_inputs,
    )
    inventory_result = get_inventory_result(
        src_dir,
        deep=True,
        source_snapshot=source_snapshot,
    )
    inventory = inventory_result.inventory
    source_snapshot = inventory_result.source_snapshot or source_snapshot
    resolved: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []

    for path in sorted(p for p in wiki_path.rglob("*") if p.is_file()):
        try:
            text = read_md(path)
        except OSError:
            continue
        if not has_conflict_markers(text):
            continue
        rel_path = path.relative_to(wiki_path).as_posix()
        new_content, reason = _resolution_for_path(
            rel_path,
            path,
            wiki_path,
            inventory,
            src_dir,
            source_snapshot=source_snapshot,
        )
        if new_content is None:
            unresolved.append({"path": rel_path, "reason": reason})
            continue
        if write:
            write_md(path, new_content)
        resolved.append({"path": rel_path, "action": reason})

    return {
        "wiki_dir": str(wiki_path),
        "src_dir": src_dir,
        "write": write,
        "ok": not unresolved,
        "resolved": resolved,
        "unresolved": unresolved,
        "conflict_count": len(resolved) + len(unresolved),
    }
