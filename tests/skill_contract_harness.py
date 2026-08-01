"""Executable validators for bundled skill command and payload examples."""

from __future__ import annotations

from dataclasses import dataclass
import contextlib
import io
import json
from pathlib import Path
import re
import shlex
from typing import Iterable, Mapping, Sequence

from llm_wiki_cli import cli
from llm_wiki_cli.commands import context_cmd
from llm_wiki_cli.services import mcp_server, skills


_SAFE_PLACEHOLDERS = {
    "<repo>": "contract-repo",
    "<project>": "contract-project",
    "<identity>": "configured-public:contract-project",
    "<file>": "src/contract.py",
    "<symbol>": "contract_symbol",
    "<name>": "contract_symbol",
    "<entrypoint>": "contract-entrypoint",
    "<helper-cache>": ".cache/contract-helpers",
}
_PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
_JSON_OBJECT_RE = re.compile(r"\{[^{}\n]+\}")
_SHELL_QUOTED_JSON_RE = re.compile(r"'(\{.*\})'")
_MCP_TOOL_MARKER_RE = re.compile(r"^MCP tool `([a-z][a-z0-9_]*)`:$")
_INLINE_COMMAND_RE = re.compile(r"^`(llm-wiki\s+[^`]+)`$")
_BULLET_COMMAND_RE = re.compile(r"^[-*+]\s+`(llm-wiki\s+[^`]+)`[.]?$")
_TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
_EXPLICIT_FRAGMENT_RE = re.compile(r"(?:^|\s)(?:\.\.\.|…)(?=\s|$)")

WORKFLOW_MARKER_EDIT = "edit"
WORKFLOW_MARKER_REANCHOR = "reanchor"
WORKFLOW_MARKER_STRICT = "strict"

_WORKFLOW_SECTION_HEADINGS = ("## Steps", "## Workflow")
_FRONTMATTER_DELIMITER = "---"
# A canonical-Markdown edit is claimed when an authoring verb and a wiki
# surface object appear on the same instruction line.
_CANONICAL_EDIT_VERB_RE = re.compile(
    r"(?i)\b(?:edit|edits|edited|editing|write|writes|writing|wrote|author"
    r"|authors|authoring|append|appends|appending|attach|attaches|attaching"
    r"|rewrite|rewrites|rewriting|update|updates|updating|add|adds|adding)\b"
)
_CANONICAL_EDIT_OBJECT_RE = re.compile(
    r"(?i)(?:canonical|markdown|semantic|wiki prose|guide page|log line"
    r"|asset path|deferred-docs row)"
)
_REANCHOR_COMMAND_RE = re.compile(r"^llm-wiki (?:sync|bootstrap|migrate)\b")
_STRICT_VALIDATION_COMMAND_RE = re.compile(
    r"^llm-wiki (?:ci-check\b|lint\b.*?\s--strict\b)"
)


class SkillContractError(AssertionError):
    """A documented skill contract does not match a real public adapter."""


@dataclass(frozen=True)
class ExampleLocation:
    skill_id: str
    path: Path
    line: int

    @property
    def label(self) -> str:
        return f"{self.skill_id} ({self.path.as_posix()}:{self.line})"


@dataclass(frozen=True)
class CliExample:
    location: ExampleLocation
    command: str


@dataclass(frozen=True)
class JsonExample:
    location: ExampleLocation
    payload: Mapping[str, object]


@dataclass(frozen=True)
class McpToolExample:
    location: ExampleLocation
    tool_name: str
    payload: Mapping[str, object]


@dataclass(frozen=True)
class WorkflowMarker:
    location: ExampleLocation
    kind: str
    text: str


def _is_explicit_command_fragment(command: str) -> bool:
    return _EXPLICIT_FRAGMENT_RE.search(command) is not None


def _safe_substitute(value: str, location: ExampleLocation) -> str:
    substituted = value
    for placeholder, replacement in _SAFE_PLACEHOLDERS.items():
        substituted = substituted.replace(placeholder, replacement)
    remaining = sorted(set(_PLACEHOLDER_RE.findall(substituted)))
    if remaining:
        raise SkillContractError(
            f"{location.label}: no deterministic substitution for "
            f"{remaining[0]}"
        )
    return substituted


def extract_fenced_cli_examples(skills_root: Path) -> tuple[CliExample, ...]:
    """Extract complete ``llm-wiki`` argv examples from Markdown fences."""
    examples: list[CliExample] = []
    for path in sorted(skills_root.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        in_fence = False
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                index += 1
                continue
            command_start = stripped
            if command_start.startswith("| llm-wiki "):
                command_start = command_start[2:].lstrip()
            if not in_fence or not command_start.startswith("llm-wiki "):
                index += 1
                continue

            start_line = index + 1
            parts: list[str] = []
            while index < len(lines):
                part = (
                    command_start
                    if not parts
                    else lines[index].strip()
                )
                continued = part.endswith("\\")
                parts.append(part[:-1].rstrip() if continued else part)
                index += 1
                if not continued:
                    break
            command = " ".join(parts)
            if not _is_explicit_command_fragment(command):
                examples.append(
                    CliExample(
                        ExampleLocation(path.parent.name, path, start_line),
                        command,
                    )
                )
    return tuple(examples)


def _markdown_table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def extract_inline_cli_examples(skills_root: Path) -> tuple[CliExample, ...]:
    """Extract complete standalone bullet and ``Command`` table examples."""

    examples: list[CliExample] = []
    for path in sorted(skills_root.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            bullet = _BULLET_COMMAND_RE.fullmatch(stripped)
            if bullet is not None:
                command = bullet.group(1)
                if not _is_explicit_command_fragment(command):
                    examples.append(
                        CliExample(
                            ExampleLocation(path.parent.name, path, index + 1),
                            command,
                        )
                    )
                index += 1
                continue

            header = _markdown_table_cells(lines[index])
            separator = (
                _markdown_table_cells(lines[index + 1])
                if index + 1 < len(lines)
                else None
            )
            if (
                header is None
                or separator is None
                or len(header) != len(separator)
                or "Command" not in header
                or any(
                    _TABLE_SEPARATOR_RE.fullmatch(cell) is None
                    for cell in separator
                )
            ):
                index += 1
                continue

            command_column = header.index("Command")
            index += 2
            while index < len(lines):
                row = _markdown_table_cells(lines[index])
                if row is None or len(row) != len(header):
                    break
                inline = _INLINE_COMMAND_RE.fullmatch(row[command_column])
                if inline is not None:
                    command = inline.group(1)
                    if not _is_explicit_command_fragment(command):
                        examples.append(
                            CliExample(
                                ExampleLocation(path.parent.name, path, index + 1),
                                command,
                            )
                        )
                index += 1
    return tuple(examples)


def extract_cli_examples(skills_root: Path) -> tuple[CliExample, ...]:
    """Return every complete documented CLI argv example in stable order."""

    examples = {
        (
            example.location.path,
            example.location.line,
            example.command,
        ): example
        for example in (
            *extract_fenced_cli_examples(skills_root),
            *extract_inline_cli_examples(skills_root),
        )
    }
    return tuple(
        examples[key]
        for key in sorted(
            examples,
            key=lambda value: (value[0].as_posix(), value[1], value[2]),
        )
    )


def parse_cli_example(example: CliExample):
    """Parse one documented command with the real CLI parser, without running it."""
    command = _safe_substitute(example.command, example.location)
    try:
        argv = shlex.split(command, comments=True, posix=True)
    except ValueError as exc:
        raise SkillContractError(
            f"{example.location.label}: invalid shell argv: {exc}"
        ) from exc
    if not argv or argv[0] != "llm-wiki":
        raise SkillContractError(
            f"{example.location.label}: example must start with llm-wiki"
        )

    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            return cli._build_parser().parse_args(argv[1:])
    except SystemExit as exc:
        detail = stderr.getvalue().strip().splitlines()
        message = detail[-1] if detail else f"argparse exited with {exc.code}"
        raise SkillContractError(f"{example.location.label}: {message}") from exc


def extract_query_graph_examples(path: Path) -> tuple[JsonExample, ...]:
    """Extract inline JSON objects presented as MCP ``query_graph`` requests.

    A documented request may wrap onto the line after the ``query_graph``
    mention, so each mention scans its own line plus the next one.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[tuple[int, int]] = set()
    examples: list[JsonExample] = []
    for line_number, line in enumerate(lines, 1):
        if "query_graph" not in line:
            continue
        window = [(line_number, line)]
        if line_number < len(lines):
            window.append((line_number + 1, lines[line_number]))
        for json_line_number, json_line in window:
            for match in _JSON_OBJECT_RE.finditer(json_line):
                key = (json_line_number, match.start())
                if key in seen:
                    continue
                seen.add(key)
                location = ExampleLocation(
                    path.parent.name, path, json_line_number
                )
                raw = _safe_substitute(match.group(0), location)
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise SkillContractError(
                        f"{location.label}: invalid query_graph JSON: {exc.msg}"
                    ) from exc
                if isinstance(payload, dict):
                    examples.append(JsonExample(location, payload))
    return tuple(examples)


def validate_query_graph_example(example: JsonExample) -> tuple[str, str, int]:
    """Validate one MCP request through the production request validator."""
    try:
        return mcp_server._graph_query_args(example.payload)
    except (mcp_server.McpWikiError, TypeError, ValueError) as exc:
        raise SkillContractError(f"{example.location.label}: {exc}") from exc


def extract_mcp_tool_examples(path: Path) -> tuple[McpToolExample, ...]:
    """Extract named fenced JSON argument objects for MCP knowledge tools."""
    lines = path.read_text(encoding="utf-8").splitlines()
    examples: list[McpToolExample] = []
    index = 0
    while index < len(lines):
        marker = _MCP_TOOL_MARKER_RE.fullmatch(lines[index].strip())
        if marker is None:
            index += 1
            continue

        tool_name = marker.group(1)
        marker_line = index + 1
        index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines) or lines[index].strip() != "```json":
            raise SkillContractError(
                f"{path.parent.name} ({path.as_posix()}:{marker_line}): "
                "MCP tool marker must be followed by a fenced JSON object"
            )
        start_line = index + 2
        index += 1
        block: list[str] = []
        while index < len(lines) and lines[index].strip() != "```":
            block.append(lines[index])
            index += 1
        if index >= len(lines):
            raise SkillContractError(
                f"{path.parent.name} ({path.as_posix()}:{start_line}): "
                "unterminated MCP tool JSON fence"
            )

        location = ExampleLocation(path.parent.name, path, start_line)
        raw = _safe_substitute("\n".join(block), location)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SkillContractError(
                f"{location.label}: invalid MCP tool JSON: {exc.msg}"
            ) from exc
        if not isinstance(payload, dict):
            raise SkillContractError(
                f"{location.label}: MCP tool arguments must be an object"
            )
        examples.append(McpToolExample(location, tool_name, payload))
        index += 1
    return tuple(examples)


class _ValidationOnlyMcpWikiService(mcp_server.McpWikiService):
    """Run public MCP argument validation without building a live service."""

    def _run_documentation_query(
        self,
        method_name: str,
        value: str,
        *,
        limit: int,
        **query_options,
    ) -> dict:
        return {
            "method": method_name,
            "value": value,
            "limit": limit,
            "options": query_options,
        }


def validate_mcp_tool_example(example: McpToolExample) -> dict:
    """Validate one named MCP example through its production public method."""
    supported = {
        "get_concept",
        "list_concept_sections",
        "related_concepts",
        "traverse_typed_graph",
        "explain_evidence",
    }
    if example.tool_name not in supported:
        raise SkillContractError(
            f"{example.location.label}: unsupported MCP tool "
            f"{example.tool_name!r}"
        )
    service = _ValidationOnlyMcpWikiService()
    method = getattr(service, example.tool_name)
    try:
        result = method(**dict(example.payload))
    except (mcp_server.McpWikiError, TypeError, ValueError) as exc:
        raise SkillContractError(f"{example.location.label}: {exc}") from exc
    if not isinstance(result, dict):
        raise SkillContractError(
            f"{example.location.label}: MCP validator returned no object"
        )
    return result


def extract_context_request_examples(skills_root: Path) -> tuple[JsonExample, ...]:
    """Extract fenced and shell-quoted context-protocol JSON requests."""
    examples: list[JsonExample] = []
    for path in sorted(skills_root.rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            if not stripped.startswith("```json"):
                inline = _SHELL_QUOTED_JSON_RE.search(lines[index])
                if (
                    inline is not None
                    and context_cmd.PROTOCOL_VERSION in inline.group(1)
                ):
                    location = ExampleLocation(
                        path.parent.name, path, index + 1
                    )
                    raw = _safe_substitute(inline.group(1), location)
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise SkillContractError(
                            f"{location.label}: invalid context JSON: "
                            f"{exc.msg}"
                        ) from exc
                    if not isinstance(payload, dict):
                        raise SkillContractError(
                            f"{location.label}: context request must be "
                            "an object"
                        )
                    examples.append(JsonExample(location, payload))
                index += 1
                continue
            start_line = index + 2
            index += 1
            block: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            raw = "\n".join(block)
            if context_cmd.PROTOCOL_VERSION not in raw:
                index += 1
                continue
            location = ExampleLocation(path.parent.name, path, start_line)
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SkillContractError(
                    f"{location.label}: invalid context JSON: {exc.msg}"
                ) from exc
            if not isinstance(payload, dict):
                raise SkillContractError(
                    f"{location.label}: context request must be an object"
                )
            examples.append(JsonExample(location, payload))
            index += 1
    return tuple(examples)


def validate_context_example(example: JsonExample) -> dict:
    """Validate one context request through the production protocol parser."""
    try:
        return context_cmd._validate_protocol_request(dict(example.payload))
    except context_cmd.ProtocolRequestError as exc:
        raise SkillContractError(f"{example.location.label}: {exc}") from exc


def output_value(
    payload: Mapping[str, object],
    dotted_path: str,
    location: ExampleLocation,
) -> object:
    """Resolve a documented response path against a real fixture payload."""
    current: object = payload
    for component in dotted_path.split("."):
        if not isinstance(current, Mapping) or component not in current:
            raise SkillContractError(
                f"{location.label}: output has no field {dotted_path!r}"
            )
        current = current[component]
    return current


def assert_markers_in_order(
    text: str,
    markers: Sequence[str],
    location: ExampleLocation,
) -> None:
    """Assert critical workflow markers appear once in the documented order."""
    cursor = 0
    for marker in markers:
        position = text.find(marker, cursor)
        if position < 0:
            raise SkillContractError(
                f"{location.label}: missing or out-of-order marker {marker!r}"
            )
        cursor = position + len(marker)


def assert_cli_selections_equal(
    examples: Iterable[CliExample],
    fields: Sequence[str],
) -> None:
    """Require immutable argparse selections to match across workflow stages."""
    parsed = [(example, parse_cli_example(example)) for example in examples]
    if not parsed:
        raise SkillContractError("selection comparison requires an example")
    first_example, first_args = parsed[0]
    expected = tuple(getattr(first_args, field, None) for field in fields)
    for example, args in parsed[1:]:
        actual = tuple(getattr(args, field, None) for field in fields)
        if actual != expected:
            raise SkillContractError(
                f"{example.location.label}: selections {actual!r} do not match "
                f"{first_example.location.label} selections {expected!r}"
            )


def _workflow_section(path: Path) -> tuple[int, list[str]]:
    """Return the workflow body of a manifest with its 0-based line offset."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() in _WORKFLOW_SECTION_HEADINGS:
            return index + 1, lines[index + 1 :]
    offset = 0
    if lines and lines[0].strip() == _FRONTMATTER_DELIMITER:
        for index in range(1, len(lines)):
            if lines[index].strip() == _FRONTMATTER_DELIMITER:
                offset = index + 1
                break
    return offset, lines[offset:]


def extract_workflow_markers(path: Path) -> tuple[WorkflowMarker, ...]:
    """Extract ordered edit, re-anchor, and strict-validation workflow markers.

    A ``--dry-run`` sync previews without re-committing the native snapshot, so
    it never counts as a re-anchor.
    """
    offset, lines = _workflow_section(path)
    markers: list[WorkflowMarker] = []
    for index, line in enumerate(lines):
        command = line.strip()
        location = ExampleLocation(path.parent.name, path, offset + index + 1)
        if _REANCHOR_COMMAND_RE.match(command):
            if "--dry-run" in command:
                continue
            markers.append(
                WorkflowMarker(location, WORKFLOW_MARKER_REANCHOR, command)
            )
        elif _STRICT_VALIDATION_COMMAND_RE.match(command):
            markers.append(
                WorkflowMarker(location, WORKFLOW_MARKER_STRICT, command)
            )
        elif _CANONICAL_EDIT_VERB_RE.search(line) and _CANONICAL_EDIT_OBJECT_RE.search(
            line
        ):
            markers.append(WorkflowMarker(location, WORKFLOW_MARKER_EDIT, command))
    return tuple(markers)


def validate_workflow_ordering(path: Path) -> None:
    """Require a re-anchor between any canonical edit and strict validation."""
    pending: WorkflowMarker | None = None
    for marker in extract_workflow_markers(path):
        if marker.kind == WORKFLOW_MARKER_EDIT:
            pending = pending or marker
        elif marker.kind == WORKFLOW_MARKER_REANCHOR:
            pending = None
        elif pending is not None:
            raise SkillContractError(
                f"{marker.location.label}: strict validation "
                f"{marker.text!r} follows the canonical edit documented at "
                f"line {pending.location.line} with no intervening re-anchor "
                "sync"
            )


def bundled_skill_dirs(skills_root: Path) -> tuple[Path, ...]:
    """Every bundled skill directory that ships a manifest, in stable order."""
    return tuple(
        path
        for path in sorted(skills_root.iterdir())
        if (path / skills.SKILL_MANIFEST_NAME).is_file()
    )


def collect_skill_contract_errors(skill_dir: Path) -> tuple[str, ...]:
    """Every documented-contract violation in one bundled skill directory."""
    errors: list[str] = []

    for extract_all, validate_all in (
        (extract_cli_examples, parse_cli_example),
        (extract_context_request_examples, validate_context_example),
    ):
        try:
            extracted = extract_all(skill_dir)
        except SkillContractError as exc:
            errors.append(str(exc))
            continue
        for example in extracted:
            try:
                validate_all(example)
            except SkillContractError as exc:
                errors.append(str(exc))

    for path in sorted(skill_dir.rglob("*.md")):
        for extract_one, validate_one in (
            (extract_query_graph_examples, validate_query_graph_example),
            (extract_mcp_tool_examples, validate_mcp_tool_example),
        ):
            try:
                extracted = extract_one(path)
            except SkillContractError as exc:
                errors.append(str(exc))
                continue
            for example in extracted:
                try:
                    validate_one(example)
                except SkillContractError as exc:
                    errors.append(str(exc))

    try:
        validate_workflow_ordering(skill_dir / skills.SKILL_MANIFEST_NAME)
    except SkillContractError as exc:
        errors.append(str(exc))

    return tuple(errors)
