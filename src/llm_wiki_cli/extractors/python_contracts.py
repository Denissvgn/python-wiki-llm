"""Pure AST helpers for reconstructable Python declaration contracts.

The helpers in this module deliberately operate on syntax only.  They never
import or evaluate the inspected project, which keeps extraction deterministic
and safe for applications whose imports have startup side effects.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Mapping


PARAM_POSITIONAL_ONLY = "positional_only"
PARAM_POSITIONAL_OR_KEYWORD = "positional_or_keyword"
PARAM_VAR_POSITIONAL = "var_positional"
PARAM_KEYWORD_ONLY = "keyword_only"
PARAM_VAR_KEYWORD = "var_keyword"

_PYDANTIC_FIELD_REFS = {
    "pydantic.Field",
    "pydantic.fields.Field",
    "pydantic.v1.Field",
    "pydantic.v1.fields.Field",
}
_PYDANTIC_MODEL_REFS = {
    "pydantic.BaseModel",
    "pydantic.main.BaseModel",
    "pydantic.v1.BaseModel",
    "pydantic.v1.main.BaseModel",
    "pydantic.RootModel",
    "pydantic.root_model.RootModel",
    "pydantic_settings.BaseSettings",
    "pydantic.env_settings.BaseSettings",
}
_PYDANTIC_CONFIG_REFS = {
    "pydantic.ConfigDict",
    "pydantic.config.ConfigDict",
}
_ENUM_REFS = {
    "enum.Enum",
    "enum.IntEnum",
    "enum.StrEnum",
    "enum.Flag",
    "enum.IntFlag",
}
_TYPE_ALIAS_REFS = {"typing.TypeAlias", "typing_extensions.TypeAlias"}
_ANNOTATED_REFS = {"typing.Annotated", "typing_extensions.Annotated"}
_LITERAL_REFS = {"typing.Literal", "typing_extensions.Literal"}
_OPTIONAL_REFS = {"typing.Optional", "typing_extensions.Optional"}
_UNION_REFS = {"typing.Union", "typing_extensions.Union"}
_INFERRED_ALIAS_REFS = {
    *_ANNOTATED_REFS,
    *_LITERAL_REFS,
    *_OPTIONAL_REFS,
    *_UNION_REFS,
    "typing.Callable",
    "typing.Concatenate",
    "typing.Final",
    "typing.NotRequired",
    "typing.Required",
    "typing.Type",
    "typing_extensions.NotRequired",
    "typing_extensions.Required",
}
_FIELD_CONSTRAINTS = {
    "allow_inf_nan",
    "decimal_places",
    "discriminator",
    "ge",
    "gt",
    "le",
    "lt",
    "max_digits",
    "max_items",
    "max_length",
    "min_items",
    "min_length",
    "multiple_of",
    "pattern",
    "strict",
    "union_mode",
    "unique_items",
}
_VALIDATOR_REFS = {
    "pydantic.validator": "field",
    "pydantic.class_validators.validator": "field",
    "pydantic.v1.validator": "field",
    "pydantic.root_validator": "root",
    "pydantic.class_validators.root_validator": "root",
    "pydantic.v1.root_validator": "root",
    "pydantic.field_validator": "field",
    "pydantic.functional_validators.field_validator": "field",
    "pydantic.model_validator": "model",
    "pydantic.functional_validators.model_validator": "model",
}


def expression_to_str(node: ast.AST | None) -> str:
    """Return canonical, readable Python syntax for *node*.

    ``ast.dump`` is intentionally never exposed because it is an
    implementation representation rather than a reconstructable declaration.
    """
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except (AttributeError, TypeError, ValueError):
        return "unknown"


def reference_to_str(node: ast.AST | None) -> str:
    """Return a dotted name for a simple name/attribute expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = reference_to_str(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return ""


def normalize_reference(
    node_or_name: ast.AST | str | None, import_aliases: Mapping[str, str]
) -> str:
    """Resolve the root binding of a simple reference through imports."""
    if isinstance(node_or_name, str):
        name = node_or_name
    else:
        name = reference_to_str(node_or_name)
    if not name:
        return ""
    root, dot, rest = name.partition(".")
    mapped = import_aliases.get(root)
    if not mapped:
        return name
    return f"{mapped}.{rest}" if dot else mapped


def _argument_record(arg: ast.arg, kind: str) -> dict:
    return {
        "name": arg.arg,
        "kind": kind,
        "type": expression_to_str(arg.annotation),
    }


def extract_parameters(
    args: ast.arguments, *, omit_method_receiver: bool = False
) -> list[dict]:
    """Return all parameters in declaration order with explicit kinds."""
    records: list[dict] = []
    positional = [
        (arg, PARAM_POSITIONAL_ONLY) for arg in args.posonlyargs
    ] + [(arg, PARAM_POSITIONAL_OR_KEYWORD) for arg in args.args]
    default_offset = len(positional) - len(args.defaults)
    for index, (arg, kind) in enumerate(positional):
        record = _argument_record(arg, kind)
        default_index = index - default_offset
        if default_index >= 0:
            record["default"] = expression_to_str(args.defaults[default_index])
        records.append(record)

    if args.vararg is not None:
        records.append(_argument_record(args.vararg, PARAM_VAR_POSITIONAL))

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        record = _argument_record(arg, PARAM_KEYWORD_ONLY)
        if default is not None:
            record["default"] = expression_to_str(default)
        records.append(record)

    if args.kwarg is not None:
        records.append(_argument_record(args.kwarg, PARAM_VAR_KEYWORD))

    if omit_method_receiver and records and records[0]["name"] in {"self", "cls"}:
        records.pop(0)
    return records


def _subscript_elements(node: ast.Subscript) -> list[ast.AST]:
    if isinstance(node.slice, ast.Tuple):
        return list(node.slice.elts)
    return [node.slice]


def _unwrap_annotated(
    annotation: ast.AST, import_aliases: Mapping[str, str]
) -> tuple[ast.AST, list[ast.AST]]:
    if isinstance(annotation, ast.Subscript) and normalize_reference(
        annotation.value, import_aliases
    ) in _ANNOTATED_REFS:
        elements = _subscript_elements(annotation)
        if elements:
            return elements[0], elements[1:]
    return annotation, []


def _is_none_annotation(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _parse_forward_annotation(node: ast.AST) -> ast.AST:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return node
    try:
        return ast.parse(node.value, mode="eval").body
    except SyntaxError:
        return node


def annotation_is_nullable(
    annotation: ast.AST, import_aliases: Mapping[str, str]
) -> bool:
    """Whether an annotation explicitly permits ``None``."""
    annotation, _ = _unwrap_annotated(annotation, import_aliases)
    annotation = _parse_forward_annotation(annotation)
    if _is_none_annotation(annotation):
        return True
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return annotation_is_nullable(
            annotation.left, import_aliases
        ) or annotation_is_nullable(annotation.right, import_aliases)
    if isinstance(annotation, ast.Subscript):
        ref = normalize_reference(annotation.value, import_aliases)
        if ref in _OPTIONAL_REFS:
            return True
        if ref in _UNION_REFS:
            return any(
                annotation_is_nullable(item, import_aliases)
                for item in _subscript_elements(annotation)
            )
    return False


def literal_values(
    annotation: ast.AST, import_aliases: Mapping[str, str]
) -> list[str]:
    """Collect declared values from nested ``Literal`` annotations."""
    values: list[str] = []
    annotation = _parse_forward_annotation(annotation)

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Subscript):
            if normalize_reference(node.value, import_aliases) in _LITERAL_REFS:
                values.extend(expression_to_str(item) for item in _subscript_elements(node))
                return
            for item in _subscript_elements(node):
                visit(item)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            visit(node.left)
            visit(node.right)

    visit(annotation)
    return values


def _is_ellipsis(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is Ellipsis


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _field_call(
    node: ast.AST | None, import_aliases: Mapping[str, str]
) -> ast.Call | None:
    if isinstance(node, ast.Call) and normalize_reference(
        node.func, import_aliases
    ) in _PYDANTIC_FIELD_REFS:
        return node
    return None


def _unknown(property_name: str, node: ast.AST) -> dict[str, str]:
    return {
        "property": property_name,
        "expression": expression_to_str(node),
        "reason": "not_statically_resolvable",
    }


def _parse_examples(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [expression_to_str(item) for item in node.elts]
    return [expression_to_str(node)]


def _is_static_literal(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, bytes, int, float, complex, bool, type(None)))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_static_literal(node.operand)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_static_literal(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            key is not None
            and _is_static_literal(key)
            and _is_static_literal(value)
            for key, value in zip(node.keys, node.values)
        )
    return False


def _example_nodes(node: ast.AST) -> list[ast.AST]:
    return list(node.elts) if isinstance(node, (ast.List, ast.Tuple, ast.Set)) else [node]


def _apply_field_call(
    result: dict, call: ast.Call, import_aliases: Mapping[str, str]
) -> None:
    keywords = {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg}
    default_node = call.args[0] if call.args else keywords.get("default")
    factory_node = keywords.get("default_factory")
    if factory_node is not None:
        result.pop("default", None)
        result["default_factory"] = expression_to_str(factory_node)
        result["required"] = False
    elif default_node is not None:
        result.pop("default_factory", None)
        if _is_ellipsis(default_node):
            result.pop("default", None)
            result["required"] = True
        else:
            result["default"] = expression_to_str(default_node)
            result["required"] = False

    for name in ("alias", "validation_alias", "serialization_alias"):
        value_node = keywords.get(name)
        if value_node is None:
            continue
        literal = _literal_string(value_node)
        if literal is not None:
            result[name] = literal
        else:
            result.setdefault("unknowns", []).append(_unknown(name, value_node))

    description_node = keywords.get("description")
    if description_node is not None:
        description = _literal_string(description_node)
        if description is not None:
            result["description"] = description
        else:
            result.setdefault("unknowns", []).append(
                _unknown("description", description_node)
            )

    examples_node = keywords.get("examples")
    if examples_node is not None:
        examples = []
        for example in _example_nodes(examples_node):
            if _is_static_literal(example):
                examples.append(expression_to_str(example))
            else:
                result.setdefault("unknowns", []).append(
                    _unknown("examples", example)
                )
        if examples:
            result["examples"] = examples

    constraints = {}
    for name, value in keywords.items():
        if name not in _FIELD_CONSTRAINTS:
            continue
        if _is_static_literal(value):
            constraints[name] = expression_to_str(value)
        else:
            result.setdefault("unknowns", []).append(
                _unknown(f"constraint:{name}", value)
            )
    if constraints:
        result.setdefault("constraints", {}).update(constraints)


def extract_class_attributes(
    node: ast.ClassDef, import_aliases: Mapping[str, str]
) -> list[dict]:
    """Extract normalized annotated attributes and Pydantic field metadata."""
    attributes: list[dict] = []
    for child in node.body:
        if not isinstance(child, ast.AnnAssign) or not isinstance(
            child.target, ast.Name
        ):
            continue
        base_annotation, metadata = _unwrap_annotated(
            child.annotation, import_aliases
        )
        result = {
            "name": child.target.id,
            "line": child.lineno,
            "type": expression_to_str(child.annotation),
            "required": child.value is None,
            "nullable": annotation_is_nullable(child.annotation, import_aliases),
        }
        values = literal_values(base_annotation, import_aliases)
        if values:
            result["literal_values"] = values

        annotated_metadata = []
        for item in metadata:
            call = _field_call(item, import_aliases)
            if call is not None:
                _apply_field_call(result, call, import_aliases)
            else:
                annotated_metadata.append(expression_to_str(item))
        if annotated_metadata:
            result["annotated_metadata"] = annotated_metadata

        assigned_field = _field_call(child.value, import_aliases)
        if assigned_field is not None:
            result.pop("default", None)
            result.pop("default_factory", None)
            result["required"] = True
            _apply_field_call(result, assigned_field, import_aliases)
        elif child.value is not None:
            result["default"] = expression_to_str(child.value)
            result.pop("default_factory", None)
            result["required"] = False
        attributes.append(result)
    return attributes


def normalized_bases(
    node: ast.ClassDef, import_aliases: Mapping[str, str]
) -> list[str]:
    return [
        normalize_reference(
            base.value if isinstance(base, ast.Subscript) else base,
            import_aliases,
        )
        for base in node.bases
    ]


def class_kind(node: ast.ClassDef, import_aliases: Mapping[str, str]) -> str:
    return (
        "enum"
        if any(base in _ENUM_REFS for base in normalized_bases(node, import_aliases))
        else "class"
    )


def is_pydantic_model(
    node: ast.ClassDef, import_aliases: Mapping[str, str]
) -> bool:
    return any(
        base in _PYDANTIC_MODEL_REFS for base in normalized_bases(node, import_aliases)
    )


def finalize_model_kinds(classes: list[dict]) -> None:
    """Propagate Pydantic model classification through local subclasses."""
    model_names = {
        str(item.get("name"))
        for item in classes
        if item.get("model_kind") == "pydantic"
    }
    changed = True
    while changed:
        changed = False
        for item in classes:
            if item.get("model_kind") == "pydantic":
                continue
            bases = {
                str(base).replace("::", ".").rsplit(".", 1)[-1]
                for base in item.get("bases", [])
            }
            if bases & model_names:
                item["model_kind"] = "pydantic"
                model_names.add(str(item.get("name")))
                changed = True


def finalize_inventory_model_kinds(
    inventory: Mapping[str, dict],
    *,
    module_candidates: Callable[[str, str], set[str]] | None = None,
) -> None:
    """Propagate Pydantic model identity through imported local base classes."""
    changed = True
    while changed:
        changed = False
        model_locations: dict[str, set[str]] = {}
        for filepath, file_data in inventory.items():
            for item in file_data.get("classes", []):
                name = str(item.get("name") or "")
                if not name:
                    continue
                if item.get("model_kind") == "pydantic":
                    model_locations.setdefault(name, set()).add(filepath)

        for filepath, file_data in inventory.items():
            imported_bases: dict[str, tuple[str, str]] = {}
            for record in file_data.get("imports", []):
                if not isinstance(record, Mapping):
                    continue
                if record.get("type") == "from" and record.get("name"):
                    binding = str(record.get("alias") or record["name"])
                    imported_bases[binding] = (
                        str(record.get("module") or ""),
                        str(record["name"]),
                    )
                elif record.get("type") == "import" and record.get("module"):
                    binding = str(
                        record.get("name") or record["module"]
                    ).split(".", 1)[0]
                    imported_bases[binding] = (
                        str(record["module"]),
                        "",
                    )
            for item in file_data.get("classes", []):
                if item.get("model_kind") == "pydantic":
                    continue
                for base in item.get("bases", []):
                    base_text = str(base).split("[", 1)[0]
                    root = base_text.split(".", 1)[0]
                    leaf = base_text.rsplit(".", 1)[-1]
                    locations = model_locations.get(leaf, set())
                    local_match = filepath in locations
                    imported_match = False
                    imported = imported_bases.get(root)
                    if imported is not None and module_candidates is not None:
                        module, imported_name = imported
                        target_module = module
                        target_name = imported_name or leaf
                        if "." in base_text and imported_name:
                            separator = "" if module.endswith(".") else "."
                            target_module = f"{module}{separator}{imported_name}"
                            target_name = leaf
                        target_locations = model_locations.get(target_name, set())
                        resolved_files = module_candidates(target_module, filepath)
                        imported_match = bool(target_locations & resolved_files)
                    if local_match or imported_match:
                        item["model_kind"] = "pydantic"
                        changed = True
                        break
                if changed:
                    # Rebuild the model-name index before classifying descendants.
                    break
            if changed:
                break


def extract_enum_attributes(node: ast.ClassDef) -> list[dict]:
    """Extract declared Enum member expressions without executing them."""
    members: list[dict] = []
    for child in node.body:
        targets: list[ast.Name] = []
        value: ast.AST | None = None
        if isinstance(child, ast.Assign):
            targets = [target for target in child.targets if isinstance(target, ast.Name)]
            value = child.value
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            targets = [child.target]
            value = child.value
        if value is None:
            continue
        for target in targets:
            if target.id.startswith("_"):
                continue
            members.append(
                {
                    "name": target.id,
                    "line": child.lineno,
                    "value": expression_to_str(value),
                }
            )
    return members


def _config_entry(name: str, value: ast.AST, source: str, line: int) -> dict:
    entry = {"name": name, "line": line, "source": source}
    if _is_static_literal(value):
        entry["value"] = expression_to_str(value)
    else:
        entry["unknowns"] = [_unknown("value", value)]
    return entry


def _config_entries_from_call(call: ast.Call, source: str) -> list[dict]:
    return [
        _config_entry(
            str(keyword.arg),
            keyword.value,
            source,
            getattr(keyword.value, "lineno", call.lineno),
        )
        for keyword in call.keywords
        if keyword.arg
    ]


def _config_entries_from_dict(node: ast.Dict, source: str) -> list[dict]:
    entries = []
    for key, value in zip(node.keys, node.values):
        name = _literal_string(key)
        if name is None:
            continue
        entries.append(
            _config_entry(
                name,
                value,
                source,
                getattr(value, "lineno", node.lineno),
            )
        )
    return entries


def extract_model_config(
    node: ast.ClassDef, import_aliases: Mapping[str, str]
) -> list[dict]:
    """Extract Pydantic v1/v2 model configuration assignments."""
    entries: list[dict] = []
    for child in node.body:
        target: ast.Name | None = None
        value: ast.AST | None = None
        if isinstance(child, ast.Assign) and len(child.targets) == 1 and isinstance(
            child.targets[0], ast.Name
        ):
            target, value = child.targets[0], child.value
        elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            target, value = child.target, child.value
        if target is not None and target.id == "model_config" and value is not None:
            if isinstance(value, ast.Call) and normalize_reference(
                value.func, import_aliases
            ) in _PYDANTIC_CONFIG_REFS:
                entries.extend(_config_entries_from_call(value, "model_config"))
            elif isinstance(value, ast.Dict):
                entries.extend(_config_entries_from_dict(value, "model_config"))
        if isinstance(child, ast.ClassDef) and child.name == "Config":
            for setting in child.body:
                setting_target: ast.Name | None = None
                setting_value: ast.AST | None = None
                if (
                    isinstance(setting, ast.Assign)
                    and len(setting.targets) == 1
                    and isinstance(setting.targets[0], ast.Name)
                ):
                    setting_target, setting_value = setting.targets[0], setting.value
                elif isinstance(setting, ast.AnnAssign) and isinstance(
                    setting.target, ast.Name
                ):
                    setting_target, setting_value = setting.target, setting.value
                if setting_target is not None and setting_value is not None:
                    entries.append(
                        _config_entry(
                            setting_target.id,
                            setting_value,
                            "config_class",
                            setting.lineno,
                        )
                    )
    return entries


def extract_validator(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    import_aliases: Mapping[str, str],
) -> dict | None:
    """Return normalized Pydantic validator metadata for a method."""
    for decorator in node.decorator_list:
        call = decorator if isinstance(decorator, ast.Call) else None
        ref = normalize_reference(call.func if call else decorator, import_aliases)
        kind = _VALIDATOR_REFS.get(ref)
        if kind is None:
            continue
        fields = []
        unknowns = []
        if call is not None:
            for argument in call.args:
                field = _literal_string(argument)
                if field is None:
                    unknowns.append(_unknown("fields", argument))
                else:
                    fields.append(field)
            keywords = {
                keyword.arg: keyword.value
                for keyword in call.keywords
                if keyword.arg is not None
            }
        else:
            keywords = {}

        mode_node = keywords.get("mode")
        mode = _literal_string(mode_node)
        if mode_node is not None and mode is None:
            mode = "unknown"
            unknowns.append(_unknown("mode", mode_node))
        elif mode is None:
            pre = keywords.get("pre")
            if pre is not None and not isinstance(pre, ast.Constant):
                mode = "unknown"
                unknowns.append(_unknown("mode", pre))
            else:
                mode = (
                    "before"
                    if isinstance(pre, ast.Constant) and pre.value is True
                    else "after"
                )
        options = {
            name: expression_to_str(value)
            for name, value in keywords.items()
            if name not in {"mode", "pre"}
        }
        result: dict[str, object] = {"kind": kind, "mode": mode}
        if fields:
            result["fields"] = fields
        if options:
            result["options"] = options
        if unknowns:
            result["unknowns"] = unknowns
        return result
    return None


def type_alias_record(
    name: str,
    value: ast.AST,
    line: int,
    import_aliases: Mapping[str, str],
    *,
    deep: bool,
    inferred: bool = False,
    type_params: list[str] | None = None,
) -> dict:
    record: dict[str, object] = {
        "name": name,
        "kind": "type_alias",
        "bases": [],
        "line": line,
    }
    if deep:
        record.update(
            {
                "target": expression_to_str(value),
                "docstring": "",
                "decorators": [],
                "attributes": [],
                "methods": [],
            }
        )
        values = literal_values(value, import_aliases)
        if values:
            record["literal_values"] = values
        if type_params:
            record["type_params"] = type_params
    if inferred:
        record["inferred"] = True
    return record


def explicit_type_alias(
    node: ast.AnnAssign,
    import_aliases: Mapping[str, str],
    *,
    deep: bool,
) -> dict | None:
    if (
        not isinstance(node.target, ast.Name)
        or node.value is None
        or normalize_reference(node.annotation, import_aliases) not in _TYPE_ALIAS_REFS
    ):
        return None
    return type_alias_record(
        node.target.id,
        node.value,
        node.lineno,
        import_aliases,
        deep=deep,
    )


def inferred_type_alias(
    node: ast.Assign,
    import_aliases: Mapping[str, str],
    *,
    deep: bool,
) -> dict | None:
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        return None
    if not isinstance(node.value, ast.Subscript):
        return None
    if normalize_reference(node.value.value, import_aliases) not in _INFERRED_ALIAS_REFS:
        return None
    return type_alias_record(
        node.targets[0].id,
        node.value,
        node.lineno,
        import_aliases,
        deep=deep,
        inferred=True,
    )
