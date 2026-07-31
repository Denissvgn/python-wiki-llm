"""Import-layer guards for command adapters and reusable services."""

from __future__ import annotations

import ast
import re
from copy import deepcopy
from pathlib import Path


SERVICES_ROOT = (
    Path(__file__).resolve().parents[1] / "src" / "llm_wiki_cli" / "services"
)
VALIDATION_PATH = SERVICES_ROOT / "validation.py"
VALIDATION_MODULE = "llm_wiki_cli.services.validation"
NON_ADAPTER_VALIDATION_HELPERS = frozenset(
    {
        # These utilities are intentionally used inside substantive domain
        # functions; calling either one does not make a function an adapter.
        "format_field_differences",
        "portable_path_key",
        "require_no_control_characters",
    }
)
_VALIDATION_LIKE_NAME_RE = re.compile(
    r"^_(?:"
    r"array|bool|bounded|canonical|contains|ensure_safe|enum|hash|is_safe|mapping|"
    r"non_negative|nonnegative|normalise|normalize|object|only_fields|optional|"
    r"portable|positive|reject|relative|required|require|safe|scope|sequence|"
    r"sha256|string|text|uuid|validate"
    r")(?:_|$)"
)
_VALIDATION_DUPLICATE_EXEMPT_NAMES = frozenset(
    {
        # Digest computation is not input validation even though its helper
        # name starts with the same algorithm token as digest validators.
        "_sha256_bytes",
    }
)
REQUIRED_SHARED_VALIDATION_ADAPTERS_BY_FAMILY = {
    "bootstrap_runtime": frozenset({"_path_text", "_safe_page_component"}),
    "context_service": frozenset({"_nonnegative_count"}),
    "data_flow": frozenset({"_positive_source_line"}),
    "dependencies": frozenset(
        {"_path_under", "_path_under_scope", "_positive_line"}
    ),
    "diagrams": frozenset({"_roots_equal"}),
    "documentation_calibration": frozenset(
        {
            "_bool_or_none",
            "_non_negative_int_or_none",
            "_optional_text",
            "_portable_relative_path",
            "_safe_non_negative_int",
            "_text_list",
        }
    ),
    "documentation_calibration_broker": frozenset(
        {
            "_bounded_int",
            "_bounded_text",
            "_is_relative_to",
            "_is_canonical_uuid",
            "_required_int",
            "_required_mapping",
            "_required_text",
            "_text_tuple",
            "_validate_hash",
            "_validate_object",
            "_validate_uuid",
        }
    ),
    "documentation_calibration_controller": frozenset(
        {
            "_require_bool",
            "_require_choice",
            "_require_exact_fields",
            "_require_nonnegative_int",
            "_require_positive_int",
            "_require_sha256",
            "_require_text",
            "_require_text_list",
            "_require_timestamp",
            "_require_uuid",
            "_required_mapping",
            "_paths_overlap",
        }
    ),
    "documentation_calibration_host_broker": frozenset(
        {"_require_bounded_text", "_require_hash"}
    ),
    "documentation_claim_evidence": frozenset(
        {
            "_enum",
            "_exact_fields",
            "_mapping",
            "_nonnegative_int",
            "_object_array",
            "_portable_path",
            "_string_list",
            "_text",
        }
    ),
    "documentation_model_policy": frozenset(
        {
            "_object_sequence",
            "_optional_text",
            "_required_text",
            "_text_sequence",
            "_validate_object",
        }
    ),
    "documentation_native": frozenset({"_is_safe_relative_posix_path"}),
    "documentation_queries": frozenset(
        {"_normalise_source_path", "_require_query"}
    ),
    "documentation_review": frozenset(
        {
            "_non_negative_int",
            "_optional_text",
            "_positive_int",
            "_require_exact_fields",
            "_require_mapping",
            "_required_bool",
            "_required_enum",
            "_required_json_string",
            "_required_json_text",
            "_required_non_negative_int",
            "_required_positive_int",
            "_required_string_list",
            "_required_text",
            "_normalise_paths",
            "_validate_text_items",
        }
    ),
    "documentation_run": frozenset(
        {
            "_portable_path",
            "_require_exact_fields",
            "_require_sha256",
            "_require_utc_timestamp",
            "_required_agent_result_text",
            "_strict_string_tuple",
            "_workspace_path",
        }
    ),
    "documentation_wiki_input": frozenset(
        {
            "_is_relative_to",
            "_is_safe_posix_relative",
            "_paths_overlap",
            "_validate_portable_relative_path",
        }
    ),
    "documentation_worklist": frozenset(
        {
            "_normalise_relative_path",
            "_require_non_negative_int",
            "_require_positive_int",
            "_safe_non_negative_int",
        }
    ),
    "entrypoints": frozenset({"_roots_equal", "_source_line"}),
    "knowledge_artifacts": frozenset(
        {
            "_is_safe_relative_path",
            "_nonnegative_integer",
            "_validate_surface_keys",
        }
    ),
    "knowledge_envelope": frozenset({"_repository_relative_path"}),
    "knowledge_evidence": frozenset(
        {
            "_optional_record_array",
            "_record_name",
            "_validate_entity_coordinate",
            "_validate_extractor_ref",
            "_validate_hash",
            "_validate_inventory_complete",
            "_validate_optional_booleans",
            "_validate_optional_json_array",
            "_validate_optional_mapping",
            "_validate_optional_string_array",
            "_validate_optional_strings",
            "_validate_scope",
            "_validate_source_path",
            "_validate_string_array",
        }
    ),
    "knowledge_freshness": frozenset({"_validate_source_path"}),
    "knowledge_governance": frozenset(
        {
            "_array",
            "_exact_fields",
            "_hash",
            "_nonnegative_int",
            "_object",
            "_relative_path",
        }
    ),
    "knowledge_graph": frozenset(
        {
            "_array",
            "_enum",
            "_hash",
            "_name",
            "_nonnegative_int",
            "_object",
            "_only_fields",
            "_positive_int",
            "_relative_path",
        }
    ),
    "knowledge_index": frozenset(
        {
            "_contains_control_character",
            "_relative_path",
            "_require_exact_keys",
        }
    ),
    "knowledge_links": frozenset(
        {"_canonical_relative_path", "_contains_control_character"}
    ),
    "knowledge_model": frozenset(
        {
            "_array",
            "_enum_value",
            "_hash",
            "_nonempty_string",
            "_nonnegative_integer",
            "_object",
            "_positive_integer",
            "_relative_path",
            "_string",
        }
    ),
    "knowledge_projection": frozenset(
        {
            "_require_bool",
            "_require_enum",
            "_require_exact_fields",
            "_require_mapping",
            "_require_nonnegative_int",
            "_require_positive_int",
            "_require_relative_path",
            "_require_sequence",
            "_require_sha256",
        }
    ),
    "lint_service": frozenset({"_is_legacy_page"}),
    "protected_artifacts": frozenset(
        {"_validate_portable_component", "validate_portable_relative_path"}
    ),
    "relationships": frozenset({"_detail_line"}),
    "infrastructure_sync": frozenset({"_valid_repository_path"}),
    "imports": frozenset({"_path_under", "_path_under_scope"}),
    "mcp_server": frozenset({"_normalise_source_path", "_posix_string"}),
    "obsidian": frozenset(
        {
            "_ensure_safe_base",
            "_path_is_within",
            "_paths_overlap",
            "_safe_join",
            "_validate_existing_dir",
            "_validate_mirror_scan_relative_path",
        }
    ),
    "plugins": frozenset({"_is_relative_to", "_safe_component_path"}),
    "site_export": frozenset(
        {
            "_require_digest",
            "_require_string",
            "_is_relative_to",
            "_paths_overlap",
            "_safe_join",
            "_validate_existing_dir",
        }
    ),
    "skills": frozenset({"_ensure_safe_base"}),
    "source_snapshot": frozenset({"_validate_repository_path"}),
    "sync_manifest": frozenset(
        {
            "_mapping_value",
            "_safe_page_component",
            "_validate_exact_keys",
            "_validate_repository_path",
        }
    ),
    "verification_contracts": frozenset(
        {
            "_array",
            "_exact_fields",
            "_nonnegative_int",
            "_object",
            "_portable_text",
            "_sha256",
            "_string",
        }
    ),
    "section_ownership": frozenset(
        {
            "_section_array",
            "_section_fields",
            "_section_hash",
            "_section_int",
            "_section_object",
            "_section_string",
        }
    ),
    "team": frozenset({"_ensure_string_list", "_reject_unknown_keys"}),
    "wiki_surface": frozenset({"_is_legacy_path", "is_safe_page_id"}),
    "wiki_surface_index": frozenset({"_safe_source_path"}),
}


def _service_package(path: Path, services_root: Path) -> tuple[str, ...]:
    relative = path.relative_to(services_root)
    return ("llm_wiki_cli", "services", *relative.parent.parts)


def _resolve_relative_module(
    path: Path,
    *,
    services_root: Path,
    level: int,
    module: str,
) -> str:
    if level == 0:
        return module
    package = _service_package(path, services_root)
    parent_count = level - 1
    base = (
        package[: len(package) - parent_count]
        if parent_count <= len(package)
        else ()
    )
    return ".".join((*base, *(module.split(".") if module else ())))


def _is_command_module(module: str) -> bool:
    return (
        module == "commands"
        or module == "llm_wiki_cli.commands"
        or module.startswith("llm_wiki_cli.commands.")
    )


def _literal_dynamic_import(node: ast.Call) -> str | None:
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    value = node.args[0].value
    if not isinstance(value, str):
        return None
    function = node.func
    if isinstance(function, ast.Name):
        callable_name = function.id
    elif isinstance(function, ast.Attribute):
        callable_name = function.attr
    else:
        return None
    return value if callable_name in {"__import__", "import_module"} else None


def _resolve_dynamic_module(
    path: Path,
    *,
    services_root: Path,
    module: str,
) -> str:
    if not module.startswith("."):
        return module
    level = len(module) - len(module.lstrip("."))
    return _resolve_relative_module(
        path,
        services_root=services_root,
        level=level,
        module=module[level:],
    )


def _command_imports(
    path: Path, *, services_root: Path = SERVICES_ROOT
) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_command_module(alias.name):
                    violations.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = _resolve_relative_module(
                path,
                services_root=services_root,
                level=node.level,
                module=node.module or "",
            )
            imported = (
                module,
                *(
                    f"{module}.{alias.name}" if module else alias.name
                    for alias in node.names
                ),
            )
            if any(_is_command_module(candidate) for candidate in imported):
                violations.append((node.lineno, module or "<relative>"))
        elif isinstance(node, ast.Call):
            literal = _literal_dynamic_import(node)
            if literal is None:
                continue
            module = _resolve_dynamic_module(
                path,
                services_root=services_root,
                module=literal,
            )
            if _is_command_module(module):
                violations.append((node.lineno, f"dynamic:{literal}"))
    return violations


def _is_docstring_statement(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _shared_validation_helpers(
    validation_path: Path = VALIDATION_PATH,
) -> frozenset[str]:
    """Discover public shared validators without importing service code."""

    tree = ast.parse(
        validation_path.read_text(encoding="utf-8"),
        filename=str(validation_path),
    )
    return frozenset(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
        and node.name not in NON_ADAPTER_VALIDATION_HELPERS
    )


def _validation_imports(
    path: Path,
    tree: ast.Module,
    *,
    services_root: Path,
    helper_names: frozenset[str],
) -> tuple[dict[str, str], frozenset[str]]:
    """Return direct helper aliases and imported validation-module aliases."""

    direct_aliases: dict[str, str] = {}
    module_aliases: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module = _resolve_relative_module(
                path,
                services_root=services_root,
                level=node.level,
                module=node.module or "",
            )
            if module == VALIDATION_MODULE:
                for alias in node.names:
                    if alias.name in helper_names:
                        direct_aliases[alias.asname or alias.name] = alias.name
                continue
            if module == "llm_wiki_cli.services":
                for alias in node.names:
                    if alias.name == "validation":
                        module_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == VALIDATION_MODULE and alias.asname:
                    module_aliases.add(alias.asname)
    changed = True
    while changed:
        changed = False
        for node in tree.body:
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            else:
                continue
            if value is None:
                continue
            helper: str | None = None
            module_alias = False
            if isinstance(value, ast.Name):
                helper = direct_aliases.get(value.id)
                module_alias = value.id in module_aliases
            elif (
                isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name)
                and value.value.id in module_aliases
                and value.attr in helper_names
            ):
                helper = value.attr
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                if helper is not None and direct_aliases.get(target.id) != helper:
                    direct_aliases[target.id] = helper
                    changed = True
                if module_alias and target.id not in module_aliases:
                    module_aliases.add(target.id)
                    changed = True
    return direct_aliases, frozenset(module_aliases)


def _service_module_path(module: str, *, services_root: Path) -> Path | None:
    prefix = "llm_wiki_cli.services"
    if module == prefix:
        candidate = services_root / "__init__.py"
        return candidate if candidate.is_file() else None
    if not module.startswith(f"{prefix}."):
        return None
    relative = module.removeprefix(f"{prefix}.").split(".")
    module_path = services_root.joinpath(*relative).with_suffix(".py")
    if module_path.is_file():
        return module_path
    package_path = services_root.joinpath(*relative) / "__init__.py"
    return package_path if package_path.is_file() else None


def _literal_exports(tree: ast.Module) -> frozenset[str] | None:
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in targets
        ):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (TypeError, ValueError):
            return None
        if isinstance(value, (list, tuple, set)) and all(
            isinstance(item, str) for item in value
        ):
            return frozenset(value)
        return None
    return None


def _module_validation_bindings(
    path: Path,
    *,
    services_root: Path,
    validation_path: Path,
    helper_names: frozenset[str],
    cache: dict[Path, tuple[dict[str, str], frozenset[str]]],
) -> tuple[dict[str, str], frozenset[str]]:
    """Resolve shared-validator aliases through local service re-exports."""

    cached = cache.get(path)
    if cached is not None:
        return cached
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    direct_aliases, module_aliases = _validation_imports(
        path,
        tree,
        services_root=services_root,
        helper_names=helper_names,
    )
    # Seed the cache before following imports so benign service import cycles
    # cannot recurse indefinitely. Direct bindings remain authoritative.
    cache[path] = (direct_aliases, module_aliases)
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        module = _resolve_relative_module(
            path,
            services_root=services_root,
            level=node.level,
            module=node.module or "",
        )
        target = _service_module_path(module, services_root=services_root)
        if target is None or target == validation_path:
            continue
        target_aliases, _ = _module_validation_bindings(
            target,
            services_root=services_root,
            validation_path=validation_path,
            helper_names=helper_names,
            cache=cache,
        )
        if not target_aliases:
            continue
        exports = _literal_exports(
            ast.parse(
                target.read_text(encoding="utf-8"),
                filename=str(target),
            )
        )
        for alias in node.names:
            if alias.name == "*":
                for imported_name, helper_name in target_aliases.items():
                    if exports is None:
                        if imported_name.startswith("_"):
                            continue
                    elif imported_name not in exports:
                        continue
                    direct_aliases.setdefault(imported_name, helper_name)
            elif alias.name in target_aliases:
                direct_aliases.setdefault(
                    alias.asname or alias.name,
                    target_aliases[alias.name],
                )
    return direct_aliases, module_aliases


def _function_scope_nodes(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.AST]:
    """Walk one function body without attributing nested scopes to its owner."""

    nodes: list[ast.AST] = []
    pending: list[ast.AST] = list(reversed(function.body))
    while pending:
        node = pending.pop()
        nodes.append(node)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
        ):
            continue
        pending.extend(reversed(list(ast.iter_child_nodes(node))))
    return nodes


def _assigned_helper_aliases(
    nodes: list[ast.AST],
    *,
    direct_aliases: dict[str, str],
    module_aliases: frozenset[str],
    helper_names: frozenset[str],
) -> dict[str, str]:
    aliases = dict(direct_aliases)
    changed = True
    while changed:
        changed = False
        for node in nodes:
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            else:
                continue
            if value is None:
                continue
            helper: str | None = None
            if isinstance(value, ast.Name):
                helper = aliases.get(value.id)
            elif (
                isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name)
                and value.value.id in module_aliases
                and value.attr in helper_names
            ):
                helper = value.attr
            if helper is None:
                continue
            for target in targets:
                if (
                    isinstance(target, ast.Name)
                    and aliases.get(target.id) != helper
                ):
                    aliases[target.id] = helper
                    changed = True
    return aliases


def _called_shared_helpers(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    direct_aliases: dict[str, str],
    module_aliases: frozenset[str],
    helper_names: frozenset[str],
) -> frozenset[str]:
    nodes = _function_scope_nodes(function)
    aliases = _assigned_helper_aliases(
        nodes,
        direct_aliases=direct_aliases,
        module_aliases=module_aliases,
        helper_names=helper_names,
    )

    def helper_from_default(value: ast.expr | None) -> str | None:
        if isinstance(value, ast.Name):
            return aliases.get(value.id)
        if (
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id in module_aliases
            and value.attr in helper_names
        ):
            return value.attr
        return None

    positional = [*function.args.posonlyargs, *function.args.args]
    for argument, default in zip(
        positional[-len(function.args.defaults) :],
        function.args.defaults,
    ):
        helper = helper_from_default(default)
        if helper is not None:
            aliases[argument.arg] = helper
    for argument, default in zip(
        function.args.kwonlyargs,
        function.args.kw_defaults,
    ):
        helper = helper_from_default(default)
        if helper is not None:
            aliases[argument.arg] = helper

    called: set[str] = set()
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            helper = aliases.get(node.func.id)
            if helper is not None:
                called.add(helper)
        elif (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in module_aliases
            and node.func.attr in helper_names
        ):
            called.add(node.func.attr)
    return frozenset(called)


def _substantive_statement_count(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> int:
    """Count statements recursively so a nested branch cannot hide logic."""

    docstring = (
        function.body[0]
        if function.body and _is_docstring_statement(function.body[0])
        else None
    )
    return sum(
        1
        for node in _function_scope_nodes(function)
        if isinstance(node, ast.stmt) and node is not docstring
    )


def _shared_validation_adapters(
    path: Path,
    *,
    validation_path: Path = VALIDATION_PATH,
    binding_cache: dict[
        Path, tuple[dict[str, str], frozenset[str]]
    ] | None = None,
) -> dict[tuple[str, int], tuple[int, frozenset[str]]]:
    """Discover adapters from their dependency on shared validation helpers."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    helper_names = _shared_validation_helpers(validation_path)
    services_root = validation_path.parent
    direct_aliases, module_aliases = _module_validation_bindings(
        path,
        services_root=services_root,
        validation_path=validation_path,
        helper_names=helper_names,
        cache=binding_cache if binding_cache is not None else {},
    )
    adapters: dict[tuple[str, int], tuple[int, frozenset[str]]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        called = _called_shared_helpers(
            node,
            direct_aliases=direct_aliases,
            module_aliases=module_aliases,
            helper_names=helper_names,
        )
        if not called:
            continue
        adapters[(node.name, node.lineno)] = (
            _substantive_statement_count(node),
            called,
        )
    return adapters


def _service_family(path: Path, *, services_root: Path = SERVICES_ROOT) -> str:
    first_part = path.relative_to(services_root).parts[0]
    return first_part.removesuffix(".py")


def _unshared_required_adapter_definitions(
    path: Path,
    *,
    adapters: dict[tuple[str, int], tuple[int, frozenset[str]]],
    required: frozenset[str],
) -> list[tuple[int, str]]:
    """Return required-name definitions that do not themselves delegate."""

    discovered = set(adapters)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        (node.lineno, node.name)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in required
        and (node.name, node.lineno) not in discovered
    ]


def _validation_body_fingerprint(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    body = deepcopy(
        function.body[1:]
        if function.body and _is_docstring_statement(function.body[0])
        else function.body
    )
    module = ast.Module(body=body, type_ignores=[])
    excluded = {
        name
        for node in ast.walk(module)
        if isinstance(node, (ast.Global, ast.Nonlocal))
        for name in node.names
    }
    local_names: list[str] = []

    def add_local(name: str | None) -> None:
        if name and name not in excluded and name not in local_names:
            local_names.append(name)

    arguments = function.args
    for argument in (
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
    ):
        add_local(argument.arg)
    if arguments.vararg is not None:
        add_local(arguments.vararg.arg)
    if arguments.kwarg is not None:
        add_local(arguments.kwarg.arg)
    for node in ast.walk(module):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            add_local(node.id)
        elif isinstance(node, ast.arg):
            add_local(node.arg)
        elif isinstance(node, ast.ExceptHandler):
            add_local(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            add_local(node.name)
        elif isinstance(node, ast.alias):
            add_local(node.asname or node.name.split(".", 1)[0])

    replacements = {
        name: f"__local_{index}" for index, name in enumerate(local_names)
    }

    class LocalNameNormalizer(ast.NodeTransformer):
        def visit_Name(self, node: ast.Name) -> ast.Name:
            node.id = replacements.get(node.id, node.id)
            return node

        def visit_arg(self, node: ast.arg) -> ast.arg:
            node.arg = replacements.get(node.arg, node.arg)
            return node

        def visit_ExceptHandler(
            self, node: ast.ExceptHandler
        ) -> ast.ExceptHandler:
            if node.name is not None:
                node.name = replacements.get(node.name, node.name)
            return self.generic_visit(node)

        def _visit_named_scope(
            self,
            node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        ) -> ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef:
            node.name = replacements.get(node.name, node.name)
            return self.generic_visit(node)

        visit_FunctionDef = _visit_named_scope
        visit_AsyncFunctionDef = _visit_named_scope
        visit_ClassDef = _visit_named_scope

        def visit_alias(self, node: ast.alias) -> ast.alias:
            bound = node.asname or node.name.split(".", 1)[0]
            replacement = replacements.get(bound)
            if replacement is not None:
                node.asname = replacement
            return node

    normalized = LocalNameNormalizer().visit(module)
    ast.fix_missing_locations(normalized)
    return ast.dump(
        normalized,
        annotate_fields=False,
        include_attributes=False,
    )


def _duplicated_unshared_validation_helpers(
    *,
    services_root: Path = SERVICES_ROOT,
    validation_path: Path = VALIDATION_PATH,
) -> list[list[tuple[str, int, str, bool]]]:
    """Find repeated validator bodies not fully backed by shared validation."""

    groups: dict[str, list[tuple[str, int, str, bool]]] = {}
    binding_cache: dict[
        Path, tuple[dict[str, str], frozenset[str]]
    ] = {}
    for path in sorted(services_root.rglob("*.py")):
        if path == validation_path:
            continue
        adapters = _shared_validation_adapters(
            path,
            validation_path=validation_path,
            binding_cache=binding_cache,
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(services_root).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name in _VALIDATION_DUPLICATE_EXEMPT_NAMES:
                continue
            if _VALIDATION_LIKE_NAME_RE.search(node.name) is None:
                continue
            fingerprint = _validation_body_fingerprint(node)
            groups.setdefault(fingerprint, []).append(
                (
                    relative,
                    node.lineno,
                    node.name,
                    (node.name, node.lineno) in adapters,
                )
            )
    return sorted(
        (
            sorted(records)
            for records in groups.values()
            if len({relative for relative, _line, _name, _shared in records})
            >= 2
            and not all(shared for _relative, _line, _name, shared in records)
        ),
        key=lambda records: records[0],
    )


def test_services_do_not_import_command_modules() -> None:
    violations = {
        path.relative_to(SERVICES_ROOT).as_posix(): imports
        for path in sorted(SERVICES_ROOT.rglob("*.py"))
        if (imports := _command_imports(path))
    }

    assert violations == {}


def test_command_import_guard_covers_relative_depth_and_dynamic_literals(
    tmp_path: Path,
) -> None:
    services_root = tmp_path / "llm_wiki_cli" / "services"
    cases = {
        "direct.py": "from ..commands import docs\n",
        "from_parent.py": "from .. import commands\n",
        "nested/direct.py": "from ...commands.docs import run\n",
        "nested/from_parent.py": "from ... import commands\n",
        "absolute_parent.py": "from llm_wiki_cli import commands\n",
        "dynamic.py": (
            "import importlib\n"
            "importlib.import_module('llm_wiki_cli.commands.docs')\n"
        ),
        "nested/dynamic.py": (
            "from importlib import import_module\n"
            "import_module('...commands.docs', __package__)\n"
        ),
        "builtin_dynamic.py": "__import__('llm_wiki_cli.commands')\n",
    }
    for relative, source in cases.items():
        path = services_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        assert _command_imports(path, services_root=services_root), relative


def test_command_import_guard_allows_service_relative_imports(tmp_path: Path) -> None:
    services_root = tmp_path / "llm_wiki_cli" / "services"
    path = services_root / "nested" / "service.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        "from .. import validation\n"
        "from ... import api\n"
        "importlib.import_module('llm_wiki_cli.services.validation')\n",
        encoding="utf-8",
    )

    assert _command_imports(path, services_root=services_root) == []


def test_shared_validation_adapters_remain_thin() -> None:
    violations: dict[str, dict[str, dict[str, object]]] = {}
    unshared_required: dict[str, list[tuple[int, str]]] = {}
    covered_adapters: dict[str, set[str]] = {}
    binding_cache: dict[
        Path, tuple[dict[str, str], frozenset[str]]
    ] = {}
    for path in sorted(SERVICES_ROOT.rglob("*.py")):
        relative = path.relative_to(SERVICES_ROOT).as_posix()
        adapters = _shared_validation_adapters(
            path,
            binding_cache=binding_cache,
        )
        family = _service_family(path)
        if adapters:
            covered_adapters.setdefault(family, set()).update(
                name for name, _line in adapters
            )
        required = REQUIRED_SHARED_VALIDATION_ADAPTERS_BY_FAMILY.get(
            family, frozenset()
        )
        missing_delegations = _unshared_required_adapter_definitions(
            path,
            adapters=adapters,
            required=required,
        )
        if missing_delegations:
            unshared_required[relative] = missing_delegations
        for (name, line), (statement_count, helpers) in adapters.items():
            if statement_count > 3:
                violations.setdefault(relative, {})[name] = {
                    "line": line,
                    "statements": statement_count,
                    "helpers": sorted(helpers),
                }
    assert violations == {}
    assert unshared_required == {}
    missing = {
        family: sorted(required - covered_adapters.get(family, set()))
        for family, required in REQUIRED_SHARED_VALIDATION_ADAPTERS_BY_FAMILY.items()
        if required - covered_adapters.get(family, set())
    }
    assert missing == {}


def test_duplicated_validation_bodies_delegate_to_shared_module() -> None:
    assert _duplicated_unshared_validation_helpers() == []


def test_duplicate_validation_body_guard_catches_differently_named_helpers(
    tmp_path: Path,
) -> None:
    services_root = tmp_path / "services"
    validation_path = services_root / "validation.py"
    validation_path.parent.mkdir()
    validation_path.write_text(
        "def positive_int_or_none(value):\n"
        "    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:\n"
        "        return None\n"
        "    return value\n",
        encoding="utf-8",
    )
    body = (
        "(value):\n"
        "    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:\n"
        "        return None\n"
        "    return value\n"
    )
    (services_root / "data_flow.py").write_text(
        "def _positive_source_line" + body,
        encoding="utf-8",
    )
    (services_root / "dependencies.py").write_text(
        "def _positive_line" + body,
        encoding="utf-8",
    )

    groups = _duplicated_unshared_validation_helpers(
        services_root=services_root,
        validation_path=validation_path,
    )

    assert groups == [
        [
            ("data_flow.py", 1, "_positive_source_line", False),
            ("dependencies.py", 1, "_positive_line", False),
        ]
    ]


def test_duplicate_guard_covers_common_validation_prefix_families(
    tmp_path: Path,
) -> None:
    for prefix in ("bool", "non_negative", "optional"):
        services_root = tmp_path / prefix / "services"
        validation_path = services_root / "validation.py"
        validation_path.parent.mkdir(parents=True)
        validation_path.write_text("", encoding="utf-8")
        body = (
            "(value):\n"
            "    if value is None:\n"
            "        return None\n"
            "    return str(value)\n"
        )
        (services_root / "first.py").write_text(
            f"def _{prefix}_first" + body,
            encoding="utf-8",
        )
        (services_root / "second.py").write_text(
            f"def _{prefix}_second" + body,
            encoding="utf-8",
        )

        groups = _duplicated_unshared_validation_helpers(
            services_root=services_root,
            validation_path=validation_path,
        )

        assert groups == [
            [
                ("first.py", 1, f"_{prefix}_first", False),
                ("second.py", 1, f"_{prefix}_second", False),
            ]
        ]


def test_duplicate_guard_normalizes_parameter_and_local_names(
    tmp_path: Path,
) -> None:
    services_root = tmp_path / "services"
    validation_path = services_root / "validation.py"
    validation_path.parent.mkdir()
    validation_path.write_text("", encoding="utf-8")
    (services_root / "counts.py").write_text(
        "def _safe_count(value):\n"
        "    if isinstance(value, bool):\n"
        "        raise ValueError()\n"
        "    parsed = int(value)\n"
        "    return parsed\n",
        encoding="utf-8",
    )
    (services_root / "totals.py").write_text(
        "def _safe_total(raw):\n"
        "    if isinstance(raw, bool):\n"
        "        raise ValueError()\n"
        "    total = int(raw)\n"
        "    return total\n",
        encoding="utf-8",
    )

    groups = _duplicated_unshared_validation_helpers(
        services_root=services_root,
        validation_path=validation_path,
    )

    assert groups == [
        [
            ("counts.py", 1, "_safe_count", False),
            ("totals.py", 1, "_safe_total", False),
        ]
    ]


def test_duplicate_guard_ignores_digest_computation_helpers(
    tmp_path: Path,
) -> None:
    services_root = tmp_path / "services"
    validation_path = services_root / "validation.py"
    validation_path.parent.mkdir()
    validation_path.write_text("", encoding="utf-8")
    body = (
        "(content):\n"
        "    return 'sha256:' + hashlib.sha256(content).hexdigest()\n"
    )
    for module_name in ("cache", "snapshot"):
        (services_root / f"{module_name}.py").write_text(
            "import hashlib\n\n"
            "def _sha256_bytes" + body,
            encoding="utf-8",
        )

    assert _duplicated_unshared_validation_helpers(
        services_root=services_root,
        validation_path=validation_path,
    ) == []


def test_shared_validation_guard_rejects_same_name_unshared_split_duplicate(
    tmp_path: Path,
) -> None:
    validation_path = tmp_path / "services" / "validation.py"
    validation_path.parent.mkdir()
    validation_path.write_text(
        "def require_value(value, *, error):\n"
        "    return value\n",
        encoding="utf-8",
    )
    shared_path = validation_path.parent / "documentation_run" / "shared.py"
    shared_path.parent.mkdir()
    shared_path.write_text(
        "from ..validation import require_value\n"
        "\n"
        "def _portable_path(value):\n"
        "    return require_value(value, error=ValueError())\n",
        encoding="utf-8",
    )
    duplicate_path = shared_path.parent / "duplicate.py"
    duplicate_path.write_text(
        "def _portable_path(value):\n"
        "    if not isinstance(value, str):\n"
        "        raise ValueError()\n"
        "    return value\n",
        encoding="utf-8",
    )
    adapters = _shared_validation_adapters(
        shared_path,
        validation_path=validation_path,
    )

    assert ("_portable_path", 3) in adapters
    assert _unshared_required_adapter_definitions(
        duplicate_path,
        adapters={},
        required=frozenset({"_portable_path"}),
    ) == [(1, "_portable_path")]


def test_shared_validation_guard_rejects_unshared_required_method(
    tmp_path: Path,
) -> None:
    path = tmp_path / "domain.py"
    path.write_text(
        "class Contract:\n"
        "    def _required_text(self, value):\n"
        "        return value\n",
        encoding="utf-8",
    )

    assert _unshared_required_adapter_definitions(
        path,
        adapters={},
        required=frozenset({"_required_text"}),
    ) == [(2, "_required_text")]


def test_shared_validation_guard_tracks_split_modules_and_aliases(
    tmp_path: Path,
) -> None:
    services_root = tmp_path / "llm_wiki_cli" / "services"
    validation_path = services_root / "validation.py"
    validation_path.parent.mkdir(parents=True)
    validation_path.write_text(
        "def require_value(value, *, error):\n"
        "    if value is None:\n"
        "        raise error\n"
        "    return value\n",
        encoding="utf-8",
    )
    dependencies_path = services_root / "documentation_run" / "dependencies.py"
    dependencies_path.parent.mkdir()
    dependencies_path.write_text(
        "from ..validation import require_value as shared_value\n"
        "\n"
        "__all__ = ('shared_value',)\n",
        encoding="utf-8",
    )
    path = services_root / "documentation_run" / "contracts.py"
    path.write_text(
        "from .dependencies import *\n"
        "\n"
        "def adapter(value):\n"
        "    prepared = value\n"
        "    checked = shared_value(prepared, error=ValueError())\n"
        "    observed = checked\n"
        "    return observed\n",
        encoding="utf-8",
    )

    assert _service_family(path, services_root=services_root) == "documentation_run"
    assert _shared_validation_adapters(
        path,
        validation_path=validation_path,
    ) == {
        ("adapter", 3): (4, frozenset({"require_value"})),
    }


def test_shared_validation_guard_tracks_assigned_nested_and_method_adapters(
    tmp_path: Path,
) -> None:
    validation_path = tmp_path / "services" / "validation.py"
    validation_path.parent.mkdir()
    validation_path.write_text(
        "def require_value(value, *, error):\n"
        "    return value\n",
        encoding="utf-8",
    )
    path = validation_path.parent / "domain.py"
    path.write_text(
        "from .validation import require_value\n"
        "\n"
        "assigned = require_value\n"
        "\n"
        "class Validator:\n"
        "    def method(self, value):\n"
        "        return assigned(value, error=ValueError())\n"
        "\n"
        "def owner():\n"
        "    def nested(value):\n"
        "        return assigned(value, error=ValueError())\n"
        "    return nested\n"
        "\n"
        "def branch(value):\n"
        "    checked = assigned(value, error=ValueError())\n"
        "    if checked:\n"
        "        first = 1\n"
        "        second = 2\n"
        "        third = 3\n"
        "        fourth = 4\n"
        "    return checked\n",
        encoding="utf-8",
    )

    adapters = _shared_validation_adapters(
        path,
        validation_path=validation_path,
    )

    assert adapters[("method", 6)] == (
        1,
        frozenset({"require_value"}),
    )
    assert adapters[("nested", 10)] == (
        1,
        frozenset({"require_value"}),
    )
    assert adapters[("branch", 14)] == (
        7,
        frozenset({"require_value"}),
    )
    assert ("owner", 9) not in adapters


def test_shared_validation_guard_ignores_specialized_domain_invariants(
    tmp_path: Path,
) -> None:
    validation_path = tmp_path / "validation.py"
    validation_path.write_text(
        "def require_value(value, *, error):\n"
        "    return value\n"
        "\n"
        "def portable_path_key(value):\n"
        "    return value.casefold()\n",
        encoding="utf-8",
    )
    path = tmp_path / "domain.py"
    path.write_text(
        "from .validation import portable_path_key, require_value\n"
        "\n"
        "def thin_adapter(value):\n"
        "    return require_value(value, error=ValueError())\n"
        "\n"
        "def specialized_invariant(value):\n"
        "    key = portable_path_key(value)\n"
        "    if not key:\n"
        "        raise ValueError()\n"
        "    if key != value:\n"
        "        raise ValueError()\n"
        "    return key\n",
        encoding="utf-8",
    )

    assert _shared_validation_adapters(
        path,
        validation_path=validation_path,
    ) == {
        ("thin_adapter", 3): (1, frozenset({"require_value"})),
    }
