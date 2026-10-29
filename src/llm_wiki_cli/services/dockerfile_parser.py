"""Stage-owned Dockerfile source observations without image evaluation."""

from __future__ import annotations

from copy import deepcopy
import json
import re
import shlex


DOCKERFILE_STAGES_SCHEMA = "llm-wiki-dockerfile-stages/v1"
_LIST_FIELDS = ("ports", "env_vars", "volumes", "copies", "build_args")
_TEXT_FIELDS = ("entrypoint", "cmd", "workdir", "healthcheck", "user", "shell", "stop_signal")


def _empty_declarations() -> dict:
    return {**{field: [] for field in _LIST_FIELDS},
            **{field: "" for field in _TEXT_FIELDS}, "labels": {}}


def _words(value: str, escape: str = "\\") -> list[str]:
    lexer = shlex.shlex(value, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.escape = escape
    try:
        return list(lexer)
    except ValueError:
        # Raw instructions remain available when a fragment is not understood.
        return value.split()


def _heredocs(instruction: str, value: str) -> list[tuple[str, bool]]:
    if instruction not in {"RUN", "COPY", "ADD"}:
        return []
    lexer = shlex.shlex(value, posix=False, punctuation_chars="<>")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    result = []
    for index, token in enumerate(tokens[:-1]):
        if token == "<<":
            delimiter = tokens[index + 1]
            tabs = delimiter.startswith("-")
            delimiter = delimiter.removeprefix("-").strip("\"'")
            if re.fullmatch(r"[\w.-]+", delimiter):
                result.append((delimiter, tabs))
    return result


def _instructions(text: str):
    """Keep continuation and heredoc bodies attached to their source owner."""
    lines = text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    escape = "\\"
    index = 0
    started = False
    while index < len(lines):
        raw = lines[index]
        start = index + 1
        index += 1
        if not started:
            directive = re.fullmatch(r"\s*#\s*escape\s*=\s*([\\`])\s*", raw, re.IGNORECASE)
            if directive:
                escape = directive[1]
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        started = True
        value = raw.rstrip()
        while value.endswith(escape) and index < len(lines):
            value = value[:-1] + " "
            following = lines[index]
            index += 1
            while (not following.strip() or following.lstrip().startswith("#")) and index < len(lines):
                following = lines[index]
                index += 1
            value += following.strip()
        parts = value.strip().split(None, 1)
        instruction, argument = parts[0].upper(), parts[1] if len(parts) > 1 else ""
        for delimiter, strip_tabs in _heredocs(instruction, argument):
            while index < len(lines):
                body = lines[index]
                index += 1
                argument += "\n" + body
                if (body.lstrip("\t") if strip_tabs else body) == delimiter:
                    break
        yield {"instruction": instruction, "value": argument, "line": start}, escape


def _stage(argument: str, line: int, stages: list[dict], escape: str) -> dict:
    tokens = _words(argument, escape)
    flags = []
    while tokens and tokens[0].startswith("--"):
        flags.append(tokens.pop(0))
    image = tokens[0] if tokens else "unknown"
    alias = tokens[2] if len(tokens) >= 3 and tokens[1].upper() == "AS" else ""
    parent = next((stage["index"] for stage in reversed(stages)
                   if stage["alias"] and stage["alias"].casefold() == image.casefold()), None)
    base_kind = "stage" if parent is not None else "scratch" if image == "scratch" else "external"
    if "$" in image or image == "unknown":
        base_kind = "unresolved"
    platform = next((flag.split("=", 1)[1] for flag in flags if flag.startswith("--platform=")), "")
    return {"index": len(stages), "image": image, "alias": alias, "line": line,
            "platform": platform, "base_stage": parent, "base_kind": base_kind,
            "instructions": [], **_empty_declarations()}


def _pairs(argument: str, escape: str) -> list[tuple[str, str]]:
    tokens = _words(argument, escape)
    if not tokens:
        return []
    if "=" not in tokens[0]:
        return [(tokens[0], " ".join(tokens[1:]))]
    result = []
    for token in tokens:
        if "=" in token:
            name, value = token.split("=", 1)
            result.append((name, value))
    return result


def _copy(argument: str, instruction: str, escape: str) -> dict:
    rest = argument.split("\n", 1)[0]
    inline = bool(_heredocs(instruction, rest))
    flags = []
    while rest.lstrip().startswith("--"):
        parts = rest.lstrip().split(None, 1)
        flags.append(parts[0])
        rest = parts[1] if len(parts) > 1 else ""
    try:
        paths = json.loads(rest) if rest.startswith("[") else _words(rest, escape)
    except (ValueError, TypeError):
        paths = _words(rest, escape)
    if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
        paths = []
    sources = paths[:-1]
    source = " ".join(shlex.quote(path) for path in sources)
    return {"src": source, "dest": paths[-1] if paths else "",
            "from_stage": next((flag.split("=", 1)[1] for flag in flags if flag.startswith("--from=")), ""),
            "instruction": instruction, **({"inline": True} if inline else {})}


def _observe(stage: dict, record: dict, escape: str) -> None:
    instruction, value = record["instruction"], record["value"]
    text_field = {"WORKDIR": "workdir", "ENTRYPOINT": "entrypoint", "CMD": "cmd",
                  "HEALTHCHECK": "healthcheck", "USER": "user", "SHELL": "shell", "STOPSIGNAL": "stop_signal"}.get(instruction)
    if text_field:
        stage[text_field] = value
    elif instruction == "EXPOSE":
        stage["ports"].extend(_words(value, escape))
    elif instruction == "ENV":
        stage["env_vars"].extend({"name": name, "default": default} for name, default in _pairs(value, escape))
    elif instruction == "LABEL":
        stage["labels"].update(_pairs(value, escape))
    elif instruction == "ARG":
        name, separator, default = value.partition("=")
        stage["build_args"].append({"name": name.strip(), "default": default.strip() if separator else ""})
    elif instruction in {"COPY", "ADD"}:
        stage["copies"].append(_copy(value, instruction, escape))
    elif instruction == "VOLUME":
        try:
            volumes = json.loads(value) if value.startswith("[") else _words(value, escape)
        except ValueError:
            volumes = _words(value, escape)
        if isinstance(volumes, list) and all(isinstance(volume, str) for volume in volumes):
            stage["volumes"].extend(volumes)


def parse_dockerfile(text: str) -> dict:
    """Parse source declarations with stage ownership, without resolving defaults.

    Flat configuration fields project declarations in the final source stage.
    COPY and ARG lists retain all observed operations with explicit owners.
    FROM links identify earlier named stages; COPY --from is only a file source.
    """
    stages: list[dict] = []
    unscoped: list[dict] = []
    global_args: list[dict] = []
    all_args: list[dict] = []
    all_copies: list[dict] = []
    for record, escape in _instructions(text):
        instruction = record["instruction"]
        if instruction == "FROM":
            stages.append(_stage(record["value"], record["line"], stages, escape))
        if not stages:
            unscoped.append(record)
            if instruction == "ARG":
                declarations = _empty_declarations()
                _observe(declarations, record, escape)
                global_args.extend(declarations["build_args"])
                all_args.extend({**arg, "stage": None, "line": record["line"]} for arg in declarations["build_args"])
            continue
        stage = stages[-1]
        stage["instructions"].append(record)
        _observe(stage, record, escape)
        if instruction == "ARG" and stage["build_args"]:
            all_args.append({**stage["build_args"][-1], "stage": stage["index"], "line": record["line"]})
        if instruction in {"COPY", "ADD"}:
            all_copies.append({**stage["copies"][-1], "stage": stage["index"], "line": record["line"]})
    projection = {key: deepcopy(stages[-1][key]) for key in _empty_declarations()} if stages else _empty_declarations()
    return {"type": "dockerfile", "stage_schema_version": DOCKERFILE_STAGES_SCHEMA,
            "configuration_scope": "final-stage-declarations", "final_stage": len(stages) - 1 if stages else None,
            "stages": stages, "global_build_args": global_args, "unscoped_instructions": unscoped,
            **projection, "copies": all_copies, "build_args": all_args}
