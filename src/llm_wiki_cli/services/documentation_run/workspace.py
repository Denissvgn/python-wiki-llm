"""Documentation-run workspace services."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from .schema import *

def documentation_run_path(workspace: str | Path) -> Path:
    return _resolve_workspace_root_argument(workspace) / RUN_CONTROL_DIR / RUN_FILENAME


def load_documentation_run(workspace: str | Path) -> DocumentationRun:
    path = documentation_run_path(workspace)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DocumentationRunError(f"No documentation run found at {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentationPersistedStateError(
            f"Invalid documentation run at {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise DocumentationPersistedStateError(
            "Documentation run payload must be an object."
        )
    try:
        return DocumentationRun.from_dict(payload)
    except DocumentationSchemaError as exc:
        raise DocumentationPersistedStateError(str(exc)) from exc


def save_documentation_run(
    workspace: str | Path, run: DocumentationRun
) -> DocumentationRun:
    run.updated_at = _utc_now()
    _validate_run_payload(run.to_dict())
    _write_json(documentation_run_path(workspace), run.to_dict())
    return run


def transition_documentation_run(
    run: DocumentationRun,
    target_state: str,
    *,
    resume_state: str | None = None,
) -> DocumentationRun:
    if target_state not in SUPPORTED_RUN_STATES:
        raise DocumentationTransitionError(f"Unknown run state: {target_state!r}")
    if target_state == run.state:
        return run
    allowed = _ALLOWED_TRANSITIONS.get(run.state, frozenset())
    if target_state not in allowed:
        raise DocumentationTransitionError(
            f"Invalid documentation run transition: {run.state} -> {target_state}"
        )
    if run.state == "blocked" and run.resume_state and target_state != run.resume_state:
        raise DocumentationTransitionError(
            f"Blocked run must resume at its recorded state {run.resume_state!r}."
        )
    if target_state == "blocked":
        run.resume_state = resume_state or run.state
    else:
        run.resume_state = None
    run.state = target_state
    run.current_stage = _state_to_stage(target_state)
    run.updated_at = _utc_now()
    return run


def get_documentation_run_status(
    workspace: str | Path,
) -> DocumentationRunStatus:
    workspace_root = _resolve_workspace_root_argument(workspace)
    run = load_documentation_run(workspace_root)
    _load_bound_runtime_policy(workspace_root, run)
    freshness = str(run.baseline.get("freshness", "unverified"))
    return DocumentationRunStatus(
        run_id=run.run_id,
        state=run.state,
        baseline_strategy=run.baseline_strategy,
        source_available=bool(run.source.get("available")),
        freshness=freshness,
        current_stage=run.current_stage,
        next_actions=_next_actions(run),
        limitations=tuple(run.verdict_limitations),
        healthy=run.state != "blocked",
    )


def _uses_windows_guarded_path_writes() -> bool:
    return os.name == "nt"


def _archive_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _resolve_workspace_root_argument(workspace: str | Path) -> Path:
    """Resolve a workspace without accepting a redirected root argument."""

    requested = Path(os.path.abspath(os.fspath(Path(workspace).expanduser())))
    if os.path.lexists(requested):
        try:
            entry_stat = requested.lstat()
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Cannot safely inspect requested workspace root: {exc}"
            ) from exc
        is_reparse = bool(getattr(entry_stat, "st_reparse_tag", 0)) or bool(
            getattr(entry_stat, "st_file_attributes", 0) & 0x400
        )
        if stat.S_ISLNK(entry_stat.st_mode) or is_reparse:
            raise DocumentationIntegrityError(
                "Requested workspace root must not be a symlink or reparse point."
            )
        if not stat.S_ISDIR(entry_stat.st_mode):
            raise DocumentationIntegrityError(
                "Requested workspace root must be a directory."
            )
    resolved = requested.resolve()
    if os.path.lexists(resolved):
        _assert_existing_workspace_layout_safe(resolved)
    return resolved


def _create_workspace_layout(
    workspace_root: Path,
    *,
    initial_transaction: _InitialPrepareTransaction | None = None,
    existing_root_identity: tuple[int, int, int] | None = None,
) -> None:
    relative_directories = (
        RUN_CONTROL_DIR,
        f"{RUN_CONTROL_DIR}/stages",
        f"{RUN_CONTROL_DIR}/packets",
        f"{RUN_CONTROL_DIR}/results",
        f"{RUN_CONTROL_DIR}/evidence",
        f"{RUN_CONTROL_DIR}/skills",
        "wiki",
        "site",
        "_site",
    )
    _assert_existing_workspace_layout_safe(workspace_root)
    if initial_transaction is None:
        workspace_root.mkdir(parents=True, exist_ok=True)
    elif existing_root_identity is None:
        workspace_root.mkdir(parents=True, exist_ok=False)
    elif _directory_identity(workspace_root) != existing_root_identity:
        raise DocumentationIntegrityError(
            "The initially empty documentation workspace changed before layout "
            "creation."
        )

    if initial_transaction is not None:
        initial_transaction.workspace_root = workspace_root
        initial_transaction.root_identity = _directory_identity(workspace_root)
        initial_transaction.preserve_root = existing_root_identity is not None
    for relative in relative_directories:
        directory = workspace_root / relative
        directory.mkdir(parents=True, exist_ok=True)
        _assert_safe_workspace_directory(workspace_root, directory, relative)


def _assert_existing_workspace_layout_safe(workspace_root: Path) -> None:
    """Reject pre-existing redirects before the lifecycle performs any write."""

    if os.path.lexists(workspace_root):
        _assert_safe_workspace_directory(workspace_root, workspace_root, ".")
    for relative in (
        RUN_CONTROL_DIR,
        f"{RUN_CONTROL_DIR}/stages",
        f"{RUN_CONTROL_DIR}/packets",
        f"{RUN_CONTROL_DIR}/results",
        f"{RUN_CONTROL_DIR}/evidence",
        f"{RUN_CONTROL_DIR}/skills",
        "wiki",
        "site",
        "_site",
    ):
        candidate = workspace_root / relative
        if os.path.lexists(candidate):
            _assert_safe_workspace_directory(workspace_root, candidate, relative)
    _assert_workspace_control_tree_safe(workspace_root)
    for relative in ("wiki", "site", "_site"):
        _assert_workspace_output_tree_safe(workspace_root, relative)


def _assert_new_documentation_workspace_empty(
    workspace_root: Path,
) -> tuple[int, int, int] | None:
    """Require a pristine root before creating a new lifecycle trust boundary."""

    if not os.path.lexists(workspace_root):
        return None
    before = _directory_identity(workspace_root)
    try:
        entries = sorted(entry.name for entry in os.scandir(workspace_root))
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot safely inspect a new documentation workspace: {exc}"
        ) from exc
    if entries:
        raise DocumentationIntegrityError(
            "A new documentation workspace must be empty; found pre-existing "
            f"entry {entries[0]!r}. Use a new workspace path or resume a valid run."
        )
    after = _directory_identity(workspace_root)
    if after != before:
        raise DocumentationIntegrityError(
            "The new documentation workspace changed while its emptiness was "
            "being verified."
        )
    return before


def _assert_workspace_output_tree_safe(
    workspace_root: Path, relative_root: str
) -> None:
    """Reject redirects and special files anywhere in lifecycle-owned outputs."""

    root = workspace_root / relative_root
    if not os.path.lexists(root):
        return
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Cannot safely inspect documentation output {relative_root!r}: {exc}"
            ) from exc
        for entry in entries:
            try:
                entry_stat = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise DocumentationIntegrityError(
                    f"Cannot safely inspect documentation output {entry.name!r}: {exc}"
                ) from exc
            is_reparse = bool(getattr(entry_stat, "st_reparse_tag", 0)) or bool(
                getattr(entry_stat, "st_file_attributes", 0) & 0x400
            )
            relative = Path(entry.path).relative_to(workspace_root).as_posix()
            if stat.S_ISLNK(entry_stat.st_mode) or is_reparse:
                raise DocumentationIntegrityError(
                    "Documentation output artifacts must not be symlinks or reparse "
                    f"points: {relative}"
                )
            if stat.S_ISDIR(entry_stat.st_mode):
                stack.append(Path(entry.path))
            elif not stat.S_ISREG(entry_stat.st_mode):
                raise DocumentationIntegrityError(
                    f"Documentation output artifact must be a regular file: {relative}"
                )


def _assert_workspace_control_tree_safe(workspace_root: Path) -> None:
    """Reject links, reparse points, and special files in run control state."""

    control = workspace_root / RUN_CONTROL_DIR
    if not os.path.lexists(control):
        return
    stack = [control]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Cannot safely inspect documentation control state: {exc}"
            ) from exc
        for entry in entries:
            try:
                entry_stat = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise DocumentationIntegrityError(
                    f"Cannot safely inspect documentation control artifact {entry.name!r}: {exc}"
                ) from exc
            is_reparse = bool(getattr(entry_stat, "st_reparse_tag", 0)) or bool(
                getattr(entry_stat, "st_file_attributes", 0) & 0x400
            )
            relative = Path(entry.path).relative_to(workspace_root).as_posix()
            if stat.S_ISLNK(entry_stat.st_mode) or is_reparse:
                raise DocumentationIntegrityError(
                    "Documentation control artifacts must not be symlinks or reparse "
                    f"points: {relative}"
                )
            if stat.S_ISDIR(entry_stat.st_mode):
                stack.append(Path(entry.path))
            elif not stat.S_ISREG(entry_stat.st_mode):
                raise DocumentationIntegrityError(
                    f"Documentation control artifact must be a regular file: {relative}"
                )


def _assert_safe_workspace_directory(
    workspace_root: Path, directory: Path, relative: str
) -> None:
    try:
        entry_stat = directory.lstat()
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot safely inspect workspace directory {relative!r}: {exc}"
        ) from exc
    is_reparse = bool(getattr(entry_stat, "st_reparse_tag", 0)) or bool(
        getattr(entry_stat, "st_file_attributes", 0) & 0x400
    )
    if stat.S_ISLNK(entry_stat.st_mode) or is_reparse:
        raise DocumentationIntegrityError(
            f"Workspace directory {relative!r} must not be a symlink or reparse point."
        )
    if not stat.S_ISDIR(entry_stat.st_mode):
        raise DocumentationIntegrityError(
            f"Workspace path {relative!r} must be a directory."
        )
    try:
        directory.resolve(strict=True).relative_to(workspace_root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise DocumentationIntegrityError(
            f"Workspace directory {relative!r} resolves outside the workspace."
        ) from exc


def _write_runtime_policy(
    workspace_root: Path, policy: DocumentationMutationPolicy
) -> None:
    _write_json(
        workspace_root / RUN_CONTROL_DIR / POLICY_FILENAME,
        {
            "schema_version": "llm-wiki-documentation-policy/v1",
            "portable_policy": policy.to_portable_dict(),
            "runtime_paths": {
                "workspace_root": str(policy.workspace_root),
                "source_root": str(policy.source_root) if policy.source_root else None,
                "input_wiki_root": str(policy.input_wiki_root)
                if policy.input_wiki_root
                else None,
                "helper_cache_root": str(policy.helper_cache_root)
                if policy.helper_cache_root
                else None,
                "capture_root": str(policy.capture_root)
                if policy.capture_root
                else None,
            },
        },
    )


def _portable_source_selection_identity(
    portable_policy: Mapping[str, Any],
) -> dict[str, str] | None:
    """Strictly decode the documentation run's optional selection identity."""

    raw_identity = portable_policy.get("source_selection")
    try:
        identity = source_selection_identity_from_generation_inputs(
            {"source_selection": raw_identity}
            if raw_identity is not None
            else {}
        )
    except SourceSelectionError as exc:
        raise DocumentationIntegrityError(
            f"Persisted documentation source selection is malformed: {exc}"
        ) from exc
    raw_origin = portable_policy.get("source_selection_origin")
    if raw_origin not in {None, "default", "explicit"}:
        raise DocumentationIntegrityError(
            "Persisted documentation source-selection origin is unsupported."
        )
    if (identity is None) != (raw_origin is None):
        raise DocumentationIntegrityError(
            "Persisted documentation source-selection identity and origin disagree."
        )
    return identity


def _resolve_bound_source_selection(
    source_root: Path,
    portable_policy: Mapping[str, Any],
) -> SourceSelectionPolicy | None:
    """Resolve the exact policy recorded by a prepared documentation run."""

    identity = _portable_source_selection_identity(portable_policy)
    origin = portable_policy.get("source_selection_origin")
    requested_path = (
        None
        if identity is None or origin == "default"
        else identity["path"]
    )
    try:
        current = resolve_source_selection(source_root, requested_path)
    except SourceSelectionError as exc:
        raise DocumentationIntegrityError(
            f"Bound documentation source selection is unavailable: {exc}"
        ) from exc
    current_identity = None if current is None else current.identity
    if current_identity != identity:
        raise DocumentationIntegrityError(
            "Bound documentation source selection changed since prepare; request "
            "an explicit refresh."
        )
    if current is not None and current.origin != origin:
        raise DocumentationIntegrityError(
            "Bound documentation source-selection origin changed since prepare."
        )
    return current


def _bound_source_selection_argument(
    portable_policy: Mapping[str, Any],
) -> str | None:
    """Return the pinned repository-relative selection path for a run."""

    identity = _portable_source_selection_identity(portable_policy)
    return None if identity is None else identity["path"]


def _build_bound_source_snapshot(
    source_root: Path,
    portable_policy: Mapping[str, Any],
    *,
    include_tests: Iterable[str] | None = None,
) -> SourceSnapshot:
    """Capture selected run inputs while rejecting policy drift and fallback."""

    selection_policy = _resolve_bound_source_selection(
        source_root,
        portable_policy,
    )
    try:
        snapshot = build_source_snapshot(
            source_root,
            include_tests=include_tests,
            selection_policy=selection_policy,
        )
    except (OSError, SourceSelectionError, TypeError, ValueError) as exc:
        raise DocumentationIntegrityError(
            f"Cannot capture the bound documentation source snapshot: {exc}"
        ) from exc
    expected_identity = _portable_source_selection_identity(portable_policy)
    if snapshot.source_selection_identity != expected_identity:
        raise DocumentationIntegrityError(
            "Documentation source selection changed while its snapshot was captured."
        )
    return snapshot


def _capture_bound_source_baseline(
    source_root: Path,
    portable_policy: Mapping[str, Any],
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> TreeBaseline:
    """Preserve the broad legacy baseline when no selection is configured."""

    if _portable_source_selection_identity(portable_policy) is None:
        return source_tree_baseline(source_root)
    snapshot = source_snapshot or _build_bound_source_snapshot(
        source_root,
        portable_policy,
    )
    return source_snapshot_tree_baseline(snapshot)


def _compare_bound_source_baseline(
    baseline: TreeBaseline,
    source_root: Path,
    portable_policy: Mapping[str, Any],
) -> IntegrityDifference:
    """Compare with the capture mode bound into the documentation run."""

    if _portable_source_selection_identity(portable_policy) is None:
        return compare_tree_baseline(baseline, source_root)
    selection_policy = _resolve_bound_source_selection(
        source_root,
        portable_policy,
    )
    if selection_policy is None:
        raise DocumentationIntegrityError(
            "Configured documentation source selection is unavailable."
        )
    current_inputs = capture_source_selection_inputs(
        source_root,
        selection_policy=selection_policy,
    )
    assert current_inputs is not None
    expected_control_hashes = {
        path: digest
        for path, digest in baseline.file_hashes.items()
        if path == selection_policy.path or Path(path).name == ".gitignore"
    }
    raw_inputs = current_inputs.get("inputs")
    if not isinstance(raw_inputs, list):
        raise DocumentationIntegrityError(
            "Captured documentation source-selection inputs are invalid."
        )
    current_control_hashes: dict[str, str] = {}
    for item in raw_inputs:
        if not isinstance(item, Mapping):
            raise DocumentationIntegrityError(
                "Captured documentation source-selection inputs are invalid."
            )
        path = item.get("path")
        content_hash = item.get("content_hash")
        if not isinstance(path, str) or not isinstance(content_hash, str):
            raise DocumentationIntegrityError(
                "Captured documentation source-selection inputs are invalid."
            )
        current_control_hashes[path] = content_hash
    if expected_control_hashes != current_control_hashes:
        return IntegrityDifference(
            root_display=baseline.root_display,
            added=tuple(
                sorted(set(current_control_hashes) - set(expected_control_hashes))
            ),
            removed=tuple(
                sorted(set(expected_control_hashes) - set(current_control_hashes))
            ),
            changed=tuple(
                sorted(
                    path
                    for path in set(expected_control_hashes)
                    & set(current_control_hashes)
                    if expected_control_hashes[path] != current_control_hashes[path]
                )
            ),
        )
    return compare_source_snapshot_baseline(
        baseline,
        build_source_snapshot(
            source_root,
            selection_policy=selection_policy,
            expected_selection_inputs=current_inputs,
        ),
    )


def _capture_bound_source_plugin_baseline(source_root: Path) -> TreeBaseline:
    try:
        return source_plugin_tree_baseline(source_root)
    except (OSError, DocumentationPolicyError) as exc:
        raise DocumentationIntegrityError(
            f"Cannot capture trusted source-plugin integrity: {exc}"
        ) from exc


def _compare_bound_source_plugin_baseline(
    baseline: TreeBaseline,
    source_root: Path,
) -> IntegrityDifference:
    try:
        return compare_source_plugin_tree_baseline(baseline, source_root)
    except (OSError, DocumentationPolicyError) as exc:
        raise DocumentationIntegrityError(
            f"Cannot compare trusted source-plugin integrity: {exc}"
        ) from exc


def _portable_bootstrap_summary(
    summary: Mapping[str, Any], *, workspace_root: Path
) -> dict[str, Any]:
    payload = _json_round_trip(summary)
    payload["src_dir"] = "source"
    payload["generated_wiki_path"] = "wiki"
    for field_name in ("created_files", "updated_files", "skipped_files"):
        values = []
        for value in payload.get(field_name, []):
            path = Path(str(value))
            try:
                values.append(path.resolve().relative_to(workspace_root).as_posix())
            except (OSError, ValueError):
                values.append(path.name)
        payload[field_name] = values
    for field_name, fallback in (
        ("manifest_path", "wiki/.llm-wiki-manifest.json"),
        ("knowledge_path", f"wiki/{KNOWLEDGE_INDEX_FILENAME}"),
    ):
        artifact_path = payload.get(field_name)
        if artifact_path:
            try:
                payload[field_name] = (
                    Path(str(artifact_path))
                    .resolve()
                    .relative_to(workspace_root)
                    .as_posix()
                )
            except (OSError, ValueError):
                payload[field_name] = fallback
    return payload


def _workspace_path(workspace_root: Path, relative: str) -> Path:
    portable = _portable_path(relative)
    return resolve_workspace_path(
        workspace_root,
        portable,
        escape_error=DocumentationSchemaError(
            f"Workspace artifact path escapes the workspace: {relative!r}"
        ),
    )


def _stage_event_path(
    workspace_root: Path,
    stage: str,
    *,
    attempt: int,
    event: str,
) -> Path:
    sequence = {
        "wiki-enrichment": 2,
        "user-docs": 3,
        "review": 4,
    }[stage]
    return (
        workspace_root
        / RUN_CONTROL_DIR
        / "stages"
        / f"{sequence:02d}-{stage}-{attempt:02d}-{event}.json"
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentationSchemaError(f"Invalid JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DocumentationSchemaError(f"JSON artifact must be an object: {path}")
    return payload


def _load_bound_runtime_policy(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    verify_source_selection: bool = True,
) -> dict[str, Path | None]:
    """Bind machine-local roots back to the validated portable run policy."""

    policy_path = _workspace_path(
        workspace_root, f"{RUN_CONTROL_DIR}/{POLICY_FILENAME}"
    )
    payload = _read_json(policy_path)
    _require_exact_fields(
        payload,
        allowed={"schema_version", "portable_policy", "runtime_paths"},
        required={"schema_version", "portable_policy", "runtime_paths"},
        label="runtime documentation policy",
    )
    if payload.get("schema_version") != "llm-wiki-documentation-policy/v1":
        raise DocumentationIntegrityError(
            "Runtime documentation policy schema is unsupported or was changed."
        )
    portable = payload.get("portable_policy")
    if not isinstance(portable, Mapping) or dict(portable) != run.policy:
        raise DocumentationIntegrityError(
            "Runtime documentation policy no longer matches the persisted run policy."
        )
    raw_paths = payload.get("runtime_paths")
    if not isinstance(raw_paths, Mapping):
        raise DocumentationIntegrityError(
            "Runtime documentation policy paths are missing or malformed."
        )
    expected_keys = {
        "workspace_root",
        "source_root",
        "input_wiki_root",
        "helper_cache_root",
        "capture_root",
    }
    if set(raw_paths) != expected_keys:
        raise DocumentationIntegrityError(
            "Runtime documentation policy paths contain missing or unknown fields."
        )
    if raw_paths.get("workspace_root") != str(workspace_root):
        raise DocumentationIntegrityError(
            "Runtime documentation policy points at a different workspace root."
        )

    resolved: dict[str, Path | None] = {"workspace_root": workspace_root}
    for name in (
        "source_root",
        "input_wiki_root",
        "helper_cache_root",
        "capture_root",
    ):
        value = raw_paths.get(name)
        if value is None:
            resolved[name] = None
            continue
        if not isinstance(value, str) or not value:
            raise DocumentationIntegrityError(
                f"Runtime documentation policy {name} must be an absolute path or null."
            )
        candidate = Path(value).expanduser()
        if not candidate.is_absolute() or str(candidate.resolve()) != value:
            raise DocumentationIntegrityError(
                f"Runtime documentation policy {name} is not canonical."
            )
        resolved[name] = candidate

    expected_allowed = ["workspace"]
    if resolved["helper_cache_root"] is not None:
        expected_allowed.append("helper_cache")
    if resolved["capture_root"] is not None:
        expected_allowed.append("capture")
    if run.policy.get("allowed_write_roots") != expected_allowed:
        raise DocumentationIntegrityError(
            "Runtime writable roots no longer match the portable run policy."
        )
    expected_forbidden = []
    if resolved["source_root"] is not None:
        expected_forbidden.append("source")
    if resolved["input_wiki_root"] is not None:
        expected_forbidden.append("input_wiki")
    if run.policy.get("forbidden_write_roots") != expected_forbidden:
        raise DocumentationIntegrityError(
            "Runtime read-only roots no longer match the portable run policy."
        )

    source_root = resolved["source_root"]
    if bool(run.source.get("available")) != (source_root is not None):
        raise DocumentationIntegrityError(
            "Runtime source root availability no longer matches the run contract."
        )
    if source_root is not None:
        if verify_source_selection:
            _resolve_bound_source_selection(source_root, run.policy)
    elif _portable_source_selection_identity(run.policy) is not None:
        raise DocumentationIntegrityError(
            "Source-unavailable documentation run retained a source selection."
        )
    input_root = resolved["input_wiki_root"]
    expected_input = isinstance(run.baseline.get("input_wiki"), Mapping)
    if expected_input != (input_root is not None):
        raise DocumentationIntegrityError(
            "Runtime input-wiki root availability no longer matches the run contract."
        )
    return resolved


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    workspace_root = _control_workspace_root(path)
    _write_workspace_text(
        workspace_root,
        path,
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )


def _control_workspace_root(path: Path) -> Path:
    absolute = Path(os.path.abspath(os.fspath(path)))
    indexes = [
        index
        for index, component in enumerate(absolute.parts)
        if component == RUN_CONTROL_DIR
    ]
    if not indexes:
        raise DocumentationIntegrityError(
            "Lifecycle JSON writes must remain under the documentation control directory."
        )
    return Path(*absolute.parts[: indexes[-1]])


def _write_workspace_text(
    workspace_root: Path,
    path: Path,
    text: str,
) -> None:
    """Write after validating the workspace allowlist and every existing parent."""

    root = Path(os.path.abspath(os.fspath(workspace_root)))
    target = Path(os.path.abspath(os.fspath(path)))
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise DocumentationIntegrityError(
            f"Lifecycle write target escapes the workspace: {target}"
        ) from exc
    _assert_existing_workspace_layout_safe(root)
    if not os.path.lexists(target.parent):
        raise DocumentationIntegrityError(
            f"Lifecycle write parent does not exist: {target.parent}"
        )
    parent_relative = target.parent.relative_to(root).as_posix() or "."
    _assert_safe_workspace_directory(root, target.parent, parent_relative)
    if os.path.lexists(target):
        try:
            target_stat = target.lstat()
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Cannot safely inspect lifecycle write target {target}: {exc}"
            ) from exc
        is_reparse = bool(getattr(target_stat, "st_reparse_tag", 0)) or bool(
            getattr(target_stat, "st_file_attributes", 0) & 0x400
        )
        if not stat.S_ISREG(target_stat.st_mode) or is_reparse:
            raise DocumentationIntegrityError(
                f"Lifecycle write target must be a regular file: {target}"
            )
    resolve_documentation_policy(root).assert_write_allowed(target)
    if _supports_descriptor_bound_workspace_writes():
        _write_descriptor_bound_workspace_text(root, target, text)
    elif _uses_windows_guarded_path_writes():
        # Windows has no stdlib openat. Pin the complete directory chain with
        # native handles that omit FILE_SHARE_DELETE before the pathname writer
        # can create a temporary file or replace the destination.
        try:
            relative_parent = target.parent.relative_to(root)
            with guard_windows_directory_chain(root, relative_parent.parts):
                parent_before = _directory_identity(target.parent)
                write_text_output(target, text)
                if _directory_identity(target.parent) != parent_before:
                    raise DocumentationIntegrityError(
                        "Lifecycle write parent changed during the write."
                    )
        except WindowsDirectoryGuardError as exc:
            raise DocumentationIntegrityError(
                f"Cannot pin the Windows lifecycle write path: {exc}"
            ) from exc
    else:
        raise DocumentationIntegrityError(
            "This platform lacks descriptor-relative no-follow writes and a "
            "qualified safe fallback."
        )
    _assert_existing_workspace_layout_safe(root)


def _supports_descriptor_bound_workspace_writes() -> bool:
    return (
        os.name != "nt"
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
        and os.rename in os.supports_dir_fd
        and os.unlink in os.supports_dir_fd
    )


def _directory_identity(path: Path) -> tuple[int, int, int]:
    try:
        payload = path.lstat()
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot inspect lifecycle write parent {path}: {exc}"
        ) from exc
    is_reparse = bool(getattr(payload, "st_reparse_tag", 0)) or bool(
        getattr(payload, "st_file_attributes", 0) & 0x400
    )
    if not stat.S_ISDIR(payload.st_mode) or stat.S_ISLNK(payload.st_mode) or is_reparse:
        raise DocumentationIntegrityError(
            f"Lifecycle write parent must remain a regular directory: {path}"
        )
    return (payload.st_dev, payload.st_ino, payload.st_mode)


def _write_descriptor_bound_workspace_text(
    workspace_root: Path,
    target: Path,
    text: str,
) -> None:
    """Atomically replace a file relative to a pinned, no-follow parent fd."""

    parent_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        parent_fd = os.open(target.parent, parent_flags)
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot safely open lifecycle write parent {target.parent}: {exc}"
        ) from exc
    temp_name = f".{target.name}.{uuid.uuid4().hex}.tmp"
    temp_created = False
    try:
        opened_identity = os.fstat(parent_fd)
        expected_identity = _directory_identity(target.parent)
        if (
            opened_identity.st_dev,
            opened_identity.st_ino,
            opened_identity.st_mode,
        ) != expected_identity:
            raise DocumentationIntegrityError(
                "Lifecycle write parent changed while it was opened."
            )
        _assert_open_parent_within_workspace(
            workspace_root,
            target.parent,
            opened_identity,
        )
        _assert_relative_write_target_regular(parent_fd, target.name)

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        temp_fd = os.open(temp_name, flags, 0o600, dir_fd=parent_fd)
        temp_created = True
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        with os.fdopen(temp_fd, "wb") as stream:
            stream.write(normalized.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())

        current_identity = _directory_identity(target.parent)
        if current_identity != expected_identity:
            raise DocumentationIntegrityError(
                "Lifecycle write parent changed before atomic replacement."
            )
        _assert_relative_write_target_regular(parent_fd, target.name)
        os.rename(
            temp_name,
            target.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temp_created = False
        _fsync_directory_after_replace(parent_fd)
        if _directory_identity(target.parent) != expected_identity:
            raise DocumentationIntegrityError(
                "Lifecycle write parent changed during atomic replacement."
            )
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Descriptor-bound lifecycle write failed for {target}: {exc}"
        ) from exc
    finally:
        if temp_created:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except OSError:
                pass
        os.close(parent_fd)


def _fsync_directory_after_replace(directory_fd: int) -> bool:
    """Flush renamed directory metadata when the mounted filesystem supports it.

    macOS and POSIX network/virtual filesystems may reject directory ``fsync``
    with ``EINVAL`` or ``ENOTSUP`` even though the atomic rename succeeded.  Do
    not turn that already-committed rename into a false lifecycle failure; keep
    other I/O errors fatal.  The return value lets focused tests and future
    receipts distinguish the degraded durability case.
    """

    try:
        os.fsync(directory_fd)
    except OSError as exc:
        unsupported = {
            errno.EINVAL,
            getattr(errno, "ENOTSUP", errno.EINVAL),
            getattr(errno, "EOPNOTSUPP", errno.EINVAL),
        }
        if exc.errno in unsupported:
            return False
        raise
    return True


def _assert_open_parent_within_workspace(
    workspace_root: Path,
    parent: Path,
    opened_identity: os.stat_result,
) -> None:
    try:
        resolved_parent = parent.resolve(strict=True)
        resolved_parent.relative_to(workspace_root.resolve(strict=True))
        resolved_identity = resolved_parent.stat()
    except (OSError, ValueError) as exc:
        raise DocumentationIntegrityError(
            "Lifecycle write parent no longer resolves inside the workspace."
        ) from exc
    if (resolved_identity.st_dev, resolved_identity.st_ino) != (
        opened_identity.st_dev,
        opened_identity.st_ino,
    ):
        raise DocumentationIntegrityError(
            "Lifecycle write parent identity changed during resolution."
        )


def _assert_relative_write_target_regular(parent_fd: int, name: str) -> None:
    try:
        payload = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot inspect descriptor-relative lifecycle target {name!r}: {exc}"
        ) from exc
    is_reparse = bool(getattr(payload, "st_reparse_tag", 0)) or bool(
        getattr(payload, "st_file_attributes", 0) & 0x400
    )
    if not stat.S_ISREG(payload.st_mode) or stat.S_ISLNK(payload.st_mode) or is_reparse:
        raise DocumentationIntegrityError(
            f"Descriptor-relative lifecycle target must be a regular file: {name}"
        )

__all__ = (
    'documentation_run_path',
    'load_documentation_run',
    'save_documentation_run',
    'transition_documentation_run',
    'get_documentation_run_status',
    '_uses_windows_guarded_path_writes',
    '_archive_timestamp',
    '_resolve_workspace_root_argument',
    '_create_workspace_layout',
    '_assert_existing_workspace_layout_safe',
    '_assert_new_documentation_workspace_empty',
    '_assert_workspace_output_tree_safe',
    '_assert_workspace_control_tree_safe',
    '_assert_safe_workspace_directory',
    '_write_runtime_policy',
    '_portable_source_selection_identity',
    '_resolve_bound_source_selection',
    '_bound_source_selection_argument',
    '_build_bound_source_snapshot',
    '_capture_bound_source_baseline',
    '_capture_bound_source_plugin_baseline',
    '_compare_bound_source_baseline',
    '_compare_bound_source_plugin_baseline',
    '_portable_bootstrap_summary',
    '_workspace_path',
    '_stage_event_path',
    '_read_json',
    '_load_bound_runtime_policy',
    '_write_json',
    '_control_workspace_root',
    '_write_workspace_text',
    '_supports_descriptor_bound_workspace_writes',
    '_directory_identity',
    '_write_descriptor_bound_workspace_text',
    '_fsync_directory_after_replace',
    '_assert_open_parent_within_workspace',
    '_assert_relative_write_target_regular',
)
