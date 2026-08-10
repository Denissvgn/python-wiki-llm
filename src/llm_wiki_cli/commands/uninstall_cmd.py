import hashlib
import stat
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, get_agent_config_path, validate_path
from ..services.ci_installer import (
    MANAGED_WORKFLOW_PATH,
    is_unmodified_managed_workflow,
)
from ..services.filesystem_guard import (
    GuardedTreeManifest,
    atomic_write_guarded_bytes,
    guarded_tree_manifest,
    remove_guarded_tree,
    unlink_guarded_bytes,
    windows_object_identity,
)
from ..services.io import first_unsafe_path_component, read_md
from ..services.schema import (
    ALL_SCHEMA_FILES as AGENT_SCHEMA_FILES,
    CONSTRAINT_END as CONSTRAINT_END,
    CONSTRAINT_START as CONSTRAINT_START,
    ManagedSchemaBlockError,
    ManagedSchemaBlockState,
    ManagedSchemaPathError,
    classify_managed_schema_block,
    require_safe_schema_path,
    strip_wiki_block as _strip_wiki_block,
)
from ..services.skills import (
    BUNDLED_SKILLS_ROOT,
    KNOWN_INSTALL_TARGETS,
    REFERENCE_SKILL_ID,
    ReferenceSkillReason,
    ReferenceSkillState,
    verify_reference_skill,
)
from .hook_cmd import is_managed_hook_content

# Hooks that install-hook may have written
HOOK_NAMES = ["post-commit", "pre-commit", "pre-push"]

# Local runtime artifacts created by init/hooks/trigger-agent.
RUNTIME_ARTIFACTS = [
    ".git/llm-wiki-prompt.txt",
    ".git/llm-wiki.lock",
    ".git/llm-wiki-breaker.json",
    ".git/llm-wiki-sync.log",
]


class UnsafeUninstallPathError(ValueError):
    """Raised when an uninstall-owned path could escape the project tree."""


@dataclass(frozen=True)
class _HookInspection:
    """Immutable hook ownership evidence collected before mutation."""

    name: str
    path: Path
    content: str
    content_bytes: bytes
    owned: bool


@dataclass(frozen=True)
class _SchemaCleanup:
    """One verified managed-schema cleanup prepared before mutation."""

    path: Path
    content: str
    content_bytes: bytes
    stripped: str


@dataclass(frozen=True)
class _RuntimeArtifactInspection:
    """One runtime path classified without following unsafe entries."""

    path: Path
    removable: bool
    reason: str | None = None
    digest: str | None = None
    content: bytes | None = None


@dataclass(frozen=True)
class _WikiRemovalInspection:
    """Safe root-level evidence for an optional wiki-tree removal."""

    path: Path
    present: bool
    removable: bool
    page_count: int = 0
    reason: str | None = None
    root_identity: tuple[int, int, int, int] | None = None
    tree_manifest: GuardedTreeManifest = ()


@dataclass(frozen=True)
class _ReferenceSkillInspection:
    """One managed-reference tree classified for the uninstall preview."""

    target: Path
    state: ReferenceSkillState
    path: Path
    reason: str
    present: bool
    root_identity: tuple[int, int] | None = None
    tree_manifest: GuardedTreeManifest = ()


@dataclass(frozen=True)
class _CiWorkflowInspection:
    """Managed CI ownership evidence collected before confirmation."""

    path: Path
    content: bytes | None
    removable: bool
    reason: str | None = None


def _normalized_path_key(path: Path) -> tuple[str, ...]:
    """Return a case-stable absolute key without following path aliases."""

    return tuple(
        unicodedata.normalize("NFC", part).casefold() for part in path.absolute().parts
    )


def _same_path_identity(first: Path, second: Path) -> bool:
    """Return whether two spellings identify the same local path."""

    if first.absolute() == second.absolute():
        return True
    if first.name != second.name:
        return False
    if first.parent.exists() and second.parent.exists():
        try:
            return first.parent.samefile(second.parent)
        except OSError:
            return False
    return False


def _path_contains(ancestor: Path, descendant: Path) -> bool:
    """Return whether ``descendant`` is lexically inside ``ancestor``."""

    ancestor_key = _normalized_path_key(ancestor)
    descendant_key = _normalized_path_key(descendant)
    return descendant_key[: len(ancestor_key)] == ancestor_key


def _confirm(prompt: str) -> bool:
    """Ask for y/n confirmation."""
    try:
        answer = input(f"  {prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("y", "yes")


def _require_safe_hook_path(path: Path) -> Path:
    """Reject a hook path containing a symlink, reparse, or traversal."""

    unsafe = first_unsafe_path_component(path)
    if unsafe is not None:
        raise UnsafeUninstallPathError(f"hook path contains unsafe component: {unsafe}")
    return path


def _preflight_hooks() -> tuple[_HookInspection, ...]:
    """Inspect every known hook without following an unsafe path."""

    hooks_dir = Path(".git/hooks")
    _require_safe_hook_path(hooks_dir)

    if not hooks_dir.exists():
        return ()
    if not hooks_dir.is_dir():
        raise UnsafeUninstallPathError(
            f"hook directory is not a regular directory: {hooks_dir}"
        )

    inspections: list[_HookInspection] = []
    for name in HOOK_NAMES:
        hook_path = _require_safe_hook_path(hooks_dir / name)
        if not hook_path.exists() and not hook_path.is_symlink():
            continue
        if not hook_path.is_file():
            raise UnsafeUninstallPathError(
                f"hook path is not a regular file: {hook_path}"
            )
        try:
            content_bytes = hook_path.read_bytes()
            content = content_bytes.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise UnsafeUninstallPathError(
                f"hook path cannot be verified safely: {hook_path}"
            ) from exc
        inspections.append(
            _HookInspection(
                name=name,
                path=hook_path,
                content=content,
                content_bytes=content_bytes,
                owned=is_managed_hook_content(name, content),
            )
        )
    return tuple(inspections)


def _validate_hook_plan(plan: tuple[_HookInspection, ...]) -> None:
    """Ensure hook ownership evidence is still current before unlinking."""

    if _preflight_hooks() != plan:
        raise UnsafeUninstallPathError(
            "managed hook candidates changed after uninstall preflight"
        )


def _remove_hooks(
    dry_run: bool = False,
    *,
    plan: tuple[_HookInspection, ...] | None = None,
) -> int:
    """Remove llm-wiki hooks, but only from one safe ownership snapshot."""

    inspections = _preflight_hooks() if plan is None else plan
    removed = 0
    if not dry_run:
        _validate_hook_plan(inspections)

    for inspection in inspections:
        if not inspection.owned:
            print(
                f"  SKIP hook {inspection.name} "
                "(not ours — contains custom user content)"
            )
            continue

        if dry_run:
            print(f"  WOULD REMOVE hook: {inspection.path}")
        else:
            absolute = (
                inspection.path
                if inspection.path.is_absolute()
                else Path.cwd().resolve() / inspection.path
            )
            try:
                unlink_guarded_bytes(absolute, expected=inspection.content_bytes)
            except OSError as exc:
                raise UnsafeUninstallPathError(
                    f"managed hook changed during guarded removal: {inspection.path}"
                ) from exc
            print(f"  REMOVED hook: {inspection.path}")
        removed += 1

    return removed


def _preflight_agent_schemas() -> tuple[_SchemaCleanup, ...]:
    """Validate every possible managed schema and stage safe removals."""

    cleanup: list[_SchemaCleanup] = []
    for filename in AGENT_SCHEMA_FILES:
        schema_path = require_safe_schema_path(filename)
        if not schema_path.exists():
            continue
        if not schema_path.is_file():
            raise ManagedSchemaPathError(
                f"managed schema path is not a regular file: {schema_path}"
            )
        try:
            content_bytes = schema_path.read_bytes()
            content = read_md(schema_path)
        except (OSError, UnicodeError) as exc:
            raise ManagedSchemaPathError(
                f"managed schema path cannot be read safely: {schema_path}"
            ) from exc
        block = classify_managed_schema_block(content)
        if block.state is ManagedSchemaBlockState.MALFORMED:
            raise ManagedSchemaBlockError(
                f"managed schema block is malformed: {schema_path}"
            )
        if block.state is ManagedSchemaBlockState.ABSENT:
            continue

        stripped = _strip_wiki_block(content)
        if (
            classify_managed_schema_block(stripped).state
            is not ManagedSchemaBlockState.ABSENT
        ):
            raise ManagedSchemaBlockError(
                f"managed schema block could not be removed safely: {schema_path}"
            )
        cleanup.append(_SchemaCleanup(schema_path, content, content_bytes, stripped))
    return tuple(cleanup)


def _validate_schema_plan(plan: tuple[_SchemaCleanup, ...]) -> None:
    """Ensure schema cleanup evidence is still current before writing."""

    if _preflight_agent_schemas() != plan:
        raise ManagedSchemaBlockError(
            "managed schema candidates changed after uninstall preflight"
        )
    for item in plan:
        if (
            classify_managed_schema_block(item.stripped).state
            is not ManagedSchemaBlockState.ABSENT
        ):
            raise ManagedSchemaBlockError(
                f"managed schema block could not be removed safely: {item.path}"
            )


def _clean_agent_schemas(
    dry_run: bool = False,
    *,
    plan: tuple[_SchemaCleanup, ...] | None = None,
) -> int:
    """Remove the LLM Wiki constraint block from agent schema files.

    If the file becomes empty after block removal, delete it entirely.
    If user content remains, preserve it.
    """
    cleanup = _preflight_agent_schemas() if plan is None else plan
    if not dry_run:
        _validate_schema_plan(cleanup)

    for item in cleanup:
        if dry_run:
            if item.stripped:
                print(f"  WOULD CLEAN block from: {item.path} (user content preserved)")
            else:
                print(f"  WOULD DELETE: {item.path} (only contained wiki constraints)")
        else:
            absolute = (
                item.path
                if item.path.is_absolute()
                else Path.cwd().resolve() / item.path
            )
            try:
                require_safe_schema_path(item.path)
                if item.stripped:
                    atomic_write_guarded_bytes(
                        absolute,
                        item.stripped.encode("utf-8"),
                        mode=0o644,
                        require_single_link=False,
                        expected_existing=item.content_bytes,
                    )
                    print(f"  CLEANED block from: {item.path} (user content preserved)")
                else:
                    unlink_guarded_bytes(absolute, expected=item.content_bytes)
                    print(f"  DELETED: {item.path} (only contained wiki constraints)")
            except OSError as exc:
                raise ManagedSchemaPathError(
                    f"managed schema changed during guarded cleanup: {item.path}"
                ) from exc

    return len(cleanup)


def _wiki_tree_manifest(
    wiki_dir: Path,
) -> GuardedTreeManifest:
    """Capture every removable tree entry without following nested links."""

    absolute = wiki_dir if wiki_dir.is_absolute() else Path.cwd().resolve() / wiki_dir
    return guarded_tree_manifest(absolute)


def _preflight_wiki_removal(
    wiki_dir: Path,
    *,
    requested: bool,
) -> _WikiRemovalInspection:
    """Classify the optional wiki root without opening redirected targets."""

    present = wiki_dir.exists() or wiki_dir.is_symlink()
    if not requested or not present:
        return _WikiRemovalInspection(wiki_dir, present, False)
    unsafe = first_unsafe_path_component(wiki_dir)
    if unsafe is not None:
        return _WikiRemovalInspection(
            wiki_dir,
            True,
            False,
            reason=f"unsafe path component: {unsafe}",
        )
    if not wiki_dir.is_dir():
        return _WikiRemovalInspection(
            wiki_dir,
            True,
            False,
            reason="wiki root is not a regular directory",
        )
    wiki_absolute = wiki_dir.absolute()
    protected_roots = {
        Path(".git").absolute(),
        *(Path(target).absolute() for target in KNOWN_INSTALL_TARGETS),
        (BUNDLED_SKILLS_ROOT / REFERENCE_SKILL_ID).absolute(),
    }
    protected_paths = {
        *protected_roots,
        Path(MANAGED_WORKFLOW_PATH).absolute(),
        *(Path(filename).absolute() for filename in AGENT_SCHEMA_FILES),
    }

    def contains(ancestor: Path, descendant: Path) -> bool:
        ancestor_key = _normalized_path_key(ancestor)
        descendant_key = _normalized_path_key(descendant)
        if descendant_key[: len(ancestor_key)] == ancestor_key:
            return True
        if ancestor.exists():
            for candidate in (descendant, *descendant.parents):
                if not candidate.exists():
                    continue
                try:
                    if ancestor.samefile(candidate):
                        return True
                except OSError:
                    continue
        return False

    if (
        contains(wiki_absolute, Path.cwd().absolute())
        or any(contains(wiki_absolute, protected) for protected in protected_paths)
        or any(
            contains(protected_root, wiki_absolute)
            for protected_root in protected_roots
        )
    ):
        return _WikiRemovalInspection(
            wiki_dir,
            True,
            False,
            reason="wiki root overlaps protected project or lifecycle paths",
        )
    try:
        stat_result = wiki_dir.stat()
        root_object_identity = windows_object_identity(
            stat_result,
            context=str(wiki_dir),
        )
        manifest = _wiki_tree_manifest(wiki_dir)
    except OSError:
        return _WikiRemovalInspection(
            wiki_dir,
            True,
            False,
            reason="wiki root cannot be inspected safely",
        )
    page_count = sum(
        1
        for relative, mode, *_rest in manifest
        if stat.S_ISREG(mode) and relative.endswith(".md")
    )
    return _WikiRemovalInspection(
        wiki_dir,
        True,
        True,
        page_count,
        root_identity=(
            root_object_identity.device,
            root_object_identity.file_id,
            stat_result.st_mtime_ns,
            stat_result.st_size,
        ),
        tree_manifest=manifest,
    )


def _remove_wiki_dir(
    wiki_dir: Path,
    dry_run: bool = False,
    *,
    plan: _WikiRemovalInspection | None = None,
) -> bool:
    """Remove the wiki directory tree."""
    inspection = (
        _preflight_wiki_removal(wiki_dir, requested=True) if plan is None else plan
    )
    if not inspection.removable:
        return False

    if not dry_run:
        current = _preflight_wiki_removal(wiki_dir, requested=True)
        if current != inspection:
            raise UnsafeUninstallPathError(
                f"wiki root changed after uninstall preflight: {wiki_dir}"
            )

    if dry_run:
        print(f"  WOULD REMOVE: {wiki_dir}/ ({inspection.page_count} markdown files)")
    else:
        if inspection.root_identity is None:
            raise UnsafeUninstallPathError(
                f"wiki root has no confirmed identity: {wiki_dir}"
            )
        absolute = (
            wiki_dir if wiki_dir.is_absolute() else Path.cwd().resolve() / wiki_dir
        )
        try:
            remove_guarded_tree(
                absolute,
                expected_identity=inspection.root_identity[:2],
                expected_manifest=inspection.tree_manifest,
            )
        except OSError as exc:
            raise UnsafeUninstallPathError(
                f"wiki root changed during guarded removal: {wiki_dir}"
            ) from exc
        print(f"  REMOVED: {wiki_dir}/")
    return True


def _preflight_reference_skills() -> tuple[_ReferenceSkillInspection, ...]:
    """Capture exact managed-reference states for the uninstall preview."""

    inspections: list[_ReferenceSkillInspection] = []
    for target in KNOWN_INSTALL_TARGETS:
        verification = verify_reference_skill(target=target)
        inspection_state = verification.state
        inspection_reason = verification.reason.value
        present = verification.path.exists() or verification.path.is_symlink()
        root_identity: tuple[int, int] | None = None
        tree_manifest: GuardedTreeManifest = ()
        if present and not verification.path.is_symlink():
            try:
                metadata = verification.path.lstat()
                identity = windows_object_identity(
                    metadata,
                    context=str(verification.path),
                )
                root_identity = (identity.device, identity.file_id)
                absolute = (
                    verification.path
                    if verification.path.is_absolute()
                    else Path.cwd().resolve() / verification.path
                )
                tree_manifest = guarded_tree_manifest(absolute)
                confirmed = verify_reference_skill(target=target)
                if confirmed.state is not ReferenceSkillState.CURRENT:
                    inspection_state = confirmed.state
                    inspection_reason = confirmed.reason.value
                    root_identity = None
                    tree_manifest = ()
            except (OSError, ValueError):
                inspection_state = ReferenceSkillState.INSTALL_ERROR
                inspection_reason = ReferenceSkillReason.INSTALL_ERROR.value
                root_identity = None
                tree_manifest = ()
        inspections.append(
            _ReferenceSkillInspection(
                target=Path(target),
                state=inspection_state,
                path=verification.path,
                reason=inspection_reason,
                present=present,
                root_identity=root_identity,
                tree_manifest=tree_manifest,
            )
        )
    return tuple(inspections)


def _validate_reference_plan(plan: tuple[_ReferenceSkillInspection, ...]) -> None:
    """Reject any managed-reference state change after confirmation."""

    if _preflight_reference_skills() != plan:
        raise UnsafeUninstallPathError(
            "managed-reference state changed after uninstall preflight"
        )


def _remove_reference_skill(
    dry_run: bool = False,
    *,
    plan: tuple[_ReferenceSkillInspection, ...] | None = None,
) -> int:
    """Remove installed wiki-reference skill copies, but only exact-current ones.

    Sweeps every directory provisioning may have used across agents.
    """
    removed = 0
    inspections = _preflight_reference_skills() if plan is None else plan
    if not dry_run:
        _validate_reference_plan(inspections)
    for inspection in inspections:
        skill_dir = inspection.path
        if inspection.state is ReferenceSkillState.ABSENT and not inspection.present:
            continue

        if inspection.state is not ReferenceSkillState.CURRENT:
            if not inspection.present:
                continue
            print(
                f"  SKIP {skill_dir}/ (locally modified, incomplete, or unverifiable: "
                f"{inspection.reason}; remove manually if intended)"
            )
            continue

        if dry_run:
            print(f"  WOULD REMOVE: {skill_dir}/")
        else:
            if inspection.root_identity is None:
                raise UnsafeUninstallPathError(
                    f"managed-reference has no confirmed identity: {skill_dir}"
                )
            absolute = (
                skill_dir
                if skill_dir.is_absolute()
                else Path.cwd().resolve() / skill_dir
            )
            try:
                remove_guarded_tree(
                    absolute,
                    expected_identity=inspection.root_identity,
                    expected_manifest=inspection.tree_manifest,
                )
            except OSError as exc:
                raise UnsafeUninstallPathError(
                    f"managed-reference changed during guarded removal: {skill_dir}"
                ) from exc
            print(f"  REMOVED: {skill_dir}/")
        removed += 1
    return removed


def _runtime_artifact_paths(wiki_dir: Path) -> tuple[Path, ...]:
    """Return unique runtime paths, including the resolved local config path."""

    paths = [
        get_agent_config_path(wiki_dir),
        Path(".git/.llm-wiki-agent"),
        wiki_dir / ".llm-wiki-agent",
    ]
    paths.extend(Path(filepath) for filepath in RUNTIME_ARTIFACTS)
    unique: list[Path] = []
    for path in paths:
        if any(_same_path_identity(path, existing) for existing in unique):
            continue
        unique.append(path)
    return tuple(unique)


def _preflight_runtime_artifacts(
    wiki_dir: Path,
    *,
    wiki_removal: bool = False,
    preserved_reference_roots: tuple[Path, ...] = (),
) -> tuple[_RuntimeArtifactInspection, ...]:
    """Classify present runtime paths before any uninstall mutation."""

    inspections: list[_RuntimeArtifactInspection] = []
    for path in _runtime_artifact_paths(wiki_dir):
        if wiki_removal:
            try:
                path.relative_to(wiki_dir)
            except ValueError:
                pass
            else:
                # The confirmed tree removal owns this nested runtime path.
                continue
        if not (path.exists() or path.is_symlink()):
            continue
        if any(_path_contains(root, path) for root in preserved_reference_roots):
            inspections.append(
                _RuntimeArtifactInspection(
                    path,
                    False,
                    "inside a preserved managed-reference tree",
                )
            )
            continue
        unsafe = first_unsafe_path_component(path)
        if unsafe is not None:
            inspections.append(
                _RuntimeArtifactInspection(
                    path,
                    False,
                    f"unsafe path component: {unsafe}",
                )
            )
            continue
        if not path.is_file():
            inspections.append(
                _RuntimeArtifactInspection(path, False, "not a regular file")
            )
            continue
        try:
            content = path.read_bytes()
            digest = hashlib.sha256(content)
        except OSError:
            inspections.append(_RuntimeArtifactInspection(path, False, "unreadable"))
            continue
        inspections.append(
            _RuntimeArtifactInspection(
                path,
                True,
                digest=digest.hexdigest(),
                content=content,
            )
        )
    return tuple(inspections)


def _validate_runtime_plan(
    plan: tuple[_RuntimeArtifactInspection, ...],
    wiki_dir: Path,
    *,
    wiki_removal: bool = False,
    preserved_reference_roots: tuple[Path, ...] = (),
) -> None:
    """Reject runtime path changes after the uninstall preview."""

    if (
        _preflight_runtime_artifacts(
            wiki_dir,
            wiki_removal=wiki_removal,
            preserved_reference_roots=preserved_reference_roots,
        )
        != plan
    ):
        raise UnsafeUninstallPathError(
            "runtime artifacts changed after uninstall preflight"
        )


def _remove_runtime_artifacts(
    wiki_dir: Path,
    dry_run: bool = False,
    *,
    plan: tuple[_RuntimeArtifactInspection, ...] | None = None,
    wiki_removal: bool = False,
    preserved_reference_roots: tuple[Path, ...] = (),
) -> int:
    """Remove local runtime artifacts created by llm-wiki."""
    removed = 0
    inspections = (
        _preflight_runtime_artifacts(
            wiki_dir,
            wiki_removal=wiki_removal,
            preserved_reference_roots=preserved_reference_roots,
        )
        if plan is None
        else plan
    )
    if not dry_run:
        _validate_runtime_plan(
            inspections,
            wiki_dir,
            wiki_removal=wiki_removal,
            preserved_reference_roots=preserved_reference_roots,
        )
    for inspection in inspections:
        if not inspection.removable:
            print(f"  SKIP {inspection.path} ({inspection.reason})")
            continue
        if dry_run:
            print(f"  WOULD REMOVE: {inspection.path}")
        else:
            if inspection.content is None:
                raise UnsafeUninstallPathError(
                    f"runtime artifact has no confirmed content: {inspection.path}"
                )
            absolute = (
                inspection.path
                if inspection.path.is_absolute()
                else Path.cwd().resolve() / inspection.path
            )
            try:
                unlink_guarded_bytes(absolute, expected=inspection.content)
            except OSError as exc:
                raise UnsafeUninstallPathError(
                    "runtime artifact changed during guarded removal: "
                    f"{inspection.path}"
                ) from exc
            print(f"  REMOVED: {inspection.path}")
        removed += 1
    return removed


def _preflight_ci_workflow() -> _CiWorkflowInspection:
    """Capture dedicated CI workflow ownership for the uninstall preview."""

    path = Path(MANAGED_WORKFLOW_PATH)
    unsafe = first_unsafe_path_component(path)
    if unsafe is not None:
        return _CiWorkflowInspection(
            path, None, False, "unsafe or not a regular managed workflow"
        )
    if not path.exists() and not path.is_symlink():
        return _CiWorkflowInspection(path, None, False, "absent")
    if not path.is_file():
        return _CiWorkflowInspection(
            path, None, False, "unsafe or not a regular managed workflow"
        )
    try:
        content = path.read_bytes()
    except OSError:
        return _CiWorkflowInspection(
            path, None, False, "cannot verify managed ownership"
        )
    if not is_unmodified_managed_workflow(content):
        return _CiWorkflowInspection(
            path, content, False, "locally modified or not managed by llm-wiki"
        )
    return _CiWorkflowInspection(path, content, True)


def _remove_ci_workflow(
    dry_run: bool = False,
    *,
    plan: _CiWorkflowInspection | None = None,
) -> int:
    """Remove the dedicated CI workflow only from its previewed checksum."""

    inspection = _preflight_ci_workflow() if plan is None else plan
    path = inspection.path
    if not inspection.removable:
        if inspection.reason != "absent":
            print(f"  SKIP {path} ({inspection.reason})")
        return 0
    if not dry_run and _preflight_ci_workflow() != inspection:
        raise UnsafeUninstallPathError(
            f"managed CI workflow changed after uninstall preflight: {path}"
        )

    if dry_run:
        print(f"  WOULD REMOVE: {path}")
    else:
        try:
            if inspection.content is None:
                raise OSError("managed workflow has no confirmed content")
            absolute = path if path.is_absolute() else Path.cwd().resolve() / path
            unlink_guarded_bytes(absolute, expected=inspection.content)
        except OSError as exc:
            print(f"  SKIP {path} (cannot remove managed workflow: {exc})")
            return 0
        print(f"  REMOVED: {path}")
    return 1


def run(args):
    wiki_dir_arg = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(str(wiki_dir_arg), "--wiki-dir")
    wiki_dir = Path(wiki_dir_arg)
    remove_wiki = getattr(args, "remove_wiki", False)
    dry_run = getattr(args, "dry_run", False)

    try:
        hook_plan = _preflight_hooks()
        schema_plan = _preflight_agent_schemas()
        reference_plan = _preflight_reference_skills()
        preserved_reference_roots = tuple(
            inspection.path
            for inspection in reference_plan
            if inspection.present
            and inspection.state is not ReferenceSkillState.CURRENT
        ) + ((BUNDLED_SKILLS_ROOT / REFERENCE_SKILL_ID),)
        wiki_plan = _preflight_wiki_removal(wiki_dir, requested=remove_wiki)
        runtime_plan = _preflight_runtime_artifacts(
            wiki_dir,
            wiki_removal=wiki_plan.removable,
            preserved_reference_roots=preserved_reference_roots,
        )
        ci_plan = _preflight_ci_workflow()
    except (
        ManagedSchemaBlockError,
        ManagedSchemaPathError,
        UnsafeUninstallPathError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    if dry_run:
        print("DRY RUN — no files will be modified:\n")

    # ── 1. Preview what will be removed ──────────────────────────────
    print("LLM Wiki Uninstall")
    print("=" * 40)

    # Hooks
    print("\n1. Git Hooks:")
    hooks_count = _remove_hooks(dry_run=True, plan=hook_plan)
    if hooks_count == 0:
        print("  Nothing to remove.")

    # Agent schemas
    print("\n2. Agent Constraint Blocks:")
    schema_count = _clean_agent_schemas(dry_run=True, plan=schema_plan)
    if schema_count == 0:
        print("  Nothing to remove.")

    # Wiki dir
    print("\n3. Wiki Directory:")
    if wiki_plan.removable:
        print(f"  {wiki_dir}/ — {wiki_plan.page_count} markdown file(s)")
    elif remove_wiki and wiki_plan.present:
        print(f"  {wiki_dir}/ — KEPT ({wiki_plan.reason})")
    elif wiki_plan.present:
        print(f"  {wiki_dir}/ — KEPT (use --remove-wiki to delete)")
    else:
        print("  Not found.")

    # Runtime artifacts
    print("\n4. Runtime Artifacts:")
    artifact_count = sum(item.removable for item in runtime_plan)
    present_runtime_artifacts = [item.path for item in runtime_plan]
    if present_runtime_artifacts:
        for item in runtime_plan:
            if item.removable:
                print(f"  {item.path}")
            else:
                print(f"  {item.path} — KEPT ({item.reason})")
    else:
        print("  Nothing to remove.")

    # Installed wiki-reference skill copies (any agent's location)
    print("\n5. Bundled Reference Skill:")
    skill_count = 0
    skill_found = False
    for inspection in reference_plan:
        skill_dir = inspection.path
        if inspection.state is ReferenceSkillState.ABSENT and not inspection.present:
            continue
        if not inspection.present:
            continue
        skill_found = True
        if inspection.state is ReferenceSkillState.CURRENT:
            print(f"  {skill_dir}/")
            skill_count += 1
        else:
            print(
                f"  {skill_dir}/ — KEPT (locally modified, incomplete, or "
                f"unverifiable: {inspection.reason})"
            )
    if not skill_found:
        print("  Not found.")

    # Dedicated CI workflow installed by `llm-wiki install-ci`.
    print("\n6. Managed CI Workflow:")
    ci_workflow_count = _remove_ci_workflow(dry_run=True, plan=ci_plan)
    if ci_workflow_count == 0:
        print("  Nothing removable.")

    wiki_targeted = wiki_plan.removable
    total = (
        hooks_count
        + schema_count
        + (1 if wiki_targeted else 0)
        + artifact_count
        + skill_count
        + ci_workflow_count
    )
    if total == 0:
        if (
            skill_found
            or present_runtime_artifacts
            or (remove_wiki and wiki_plan.present)
        ):
            print("\nNothing safely removable; preserved managed items remain.")
        else:
            print("\nNothing to uninstall. Project is clean.")
        return

    if dry_run:
        print(f"\nDry run complete. {total} item(s) would be affected.")
        return

    # ── 2. Confirm and execute ────────────────────────────────────────
    print(f"\n{total} item(s) will be affected.")
    if not _confirm("Proceed with uninstall?"):
        print("Aborted.")
        return

    # Revalidate every previewed ownership snapshot after confirmation. Never
    # replace the user's confirmed plan with a newly authoritative one.
    try:
        _validate_hook_plan(hook_plan)
        _validate_schema_plan(schema_plan)
        _validate_runtime_plan(
            runtime_plan,
            wiki_dir,
            wiki_removal=wiki_plan.removable,
            preserved_reference_roots=preserved_reference_roots,
        )
        if _preflight_wiki_removal(wiki_dir, requested=remove_wiki) != wiki_plan:
            raise UnsafeUninstallPathError(
                f"wiki root changed after uninstall preflight: {wiki_dir}"
            )
        _validate_reference_plan(reference_plan)
        if _preflight_ci_workflow() != ci_plan:
            raise UnsafeUninstallPathError(
                "managed CI workflow changed after uninstall preflight"
            )
    except (
        ManagedSchemaBlockError,
        ManagedSchemaPathError,
        UnsafeUninstallPathError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print()
    removed_total = 0

    # Execute removals
    r = _remove_hooks(plan=hook_plan)
    removed_total += r

    # Let every schema cleanup failure propagate. Reference copies are removed
    # only after all managed blocks have been cleaned successfully.
    r = _clean_agent_schemas(plan=schema_plan)
    removed_total += r

    r = _remove_runtime_artifacts(
        wiki_dir,
        plan=runtime_plan,
        wiki_removal=wiki_plan.removable,
        preserved_reference_roots=preserved_reference_roots,
    )
    removed_total += r

    if wiki_plan.removable:
        _remove_wiki_dir(wiki_dir, plan=wiki_plan)
        removed_total += 1

    r = _remove_reference_skill(plan=reference_plan)
    removed_total += r

    r = _remove_ci_workflow(plan=ci_plan)
    removed_total += r

    print(f"\nUninstall complete. {removed_total} item(s) removed.")
    print("To uninstall the CLI itself: pip uninstall agent-wiki-cli")
