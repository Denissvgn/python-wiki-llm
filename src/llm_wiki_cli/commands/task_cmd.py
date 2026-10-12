"""CLI for explicit task-context requests and canonical counted output."""

import json
from pathlib import Path
import stat
import sys

from ..services.io import write_text_output, write_utf8_stdout
from ..services.request_json import load_request


def _safe_absolute(value):
    from ..services.io import first_unsafe_path_component

    raw = Path(value).expanduser()
    if first_unsafe_path_component(raw) is not None:
        raise ValueError("Compact artifact paths cannot traverse redirected components")
    return raw.resolve(strict=False)


def _parent_stamps(path):
    result = {}
    for parent in (path.parent, *path.parent.parents):
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError("Compact artifact parent is not a directory")
        result[parent] = (info.st_dev, info.st_ino)
    return result


def _compact_outputs(args):
    """Pin explicit artifact destinations before any workspace capture."""
    from ..services.knowledge_storage_io import read_guarded

    if not getattr(args, "canonical_output", None):
        raise ValueError("Compact delivery requires --canonical-output")
    budget = getattr(args, "view_budget_tokens", None)
    if type(budget) is not int or budget < 1:
        raise ValueError("Compact delivery requires a positive --view-budget-tokens")
    source = _safe_absolute(args.src_dir)
    wiki = _safe_absolute(args.wiki_dir)
    protected = {
        _safe_absolute(value)
        for name in ("request", "profile", "tokenizer", "source_selection")
        if (value := getattr(args, name, None)) and value != "-"
    }
    paths = [_safe_absolute(args.canonical_output)]
    if getattr(args, "output", None):
        paths.append(_safe_absolute(args.output))
    if len(paths) == 2 and (
        paths[0].is_relative_to(paths[1]) or paths[1].is_relative_to(paths[0])
    ):
        raise ValueError("Canonical receipt and compact output must be different files")
    result = []
    for path in paths:
        if (
            any(path.is_relative_to(p) or p.is_relative_to(path) for p in protected)
            or path.is_relative_to(source) or source.is_relative_to(path)
            or path.is_relative_to(wiki) or wiki.is_relative_to(path)
        ):
            raise ValueError("Compact artifacts must be outside inputs and source/wiki trees")
        existing = None
        if path.exists():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("Compact artifact must be an independent regular file")
            existing = read_guarded(path, 16_777_216).content
        result.append((path, existing, _parent_stamps(path)))
    return result


def _publish_compact_outputs(outputs, result):
    from ..services.filesystem_guard import atomic_write_guarded_bytes, ensure_guarded_directory

    for path, _, stamps in outputs:
        if _safe_absolute(path) != path or any(
            not parent.exists() or (parent.stat().st_dev, parent.stat().st_ino) != expected
            for parent, expected in stamps.items()
        ):
            raise ValueError("Compact artifact destination changed during capture")
    values = [result.canonical_text.encode("utf-8")]
    if result.ok:
        values.append(result.rendered.encode("utf-8"))
    for (path, expected, _), value in zip(outputs, values):
        ensure_guarded_directory(path.parent, mode=0o700)
        atomic_write_guarded_bytes(path, value, expected_existing=expected)


def run(args):
    from .. import api
    from ..services.token_counting import LocalTokenizerCounter

    try:
        view = getattr(args, "view", "canonical")
        compact = view in ("compact-v1", "compact-v2")
        outputs = _compact_outputs(args) if compact else None
        if not compact and (
            getattr(args, "view_budget_tokens", None) is not None
            or getattr(args, "canonical_output", None) is not None
        ):
            raise ValueError("Compact artifact options require a compact --view")
        request = load_request(args.request)
        policy = api.WorkflowPolicy(read_scope="full-inventory" if args.allow_full_inventory else "selected")
        profile = api.load_workflow_profile(args.profile, policy=policy) if args.profile else None
        counter = LocalTokenizerCounter(args.tokenizer) if args.tokenizer else None
        options = {"src_dir": args.src_dir, "wiki_dir": args.wiki_dir,
            "profile": profile, "policy": policy, "counter": counter,
            "allow_external_src": args.allow_external_src, "source_selection": args.source_selection,
            "helper_cache_dir": args.helper_cache_dir}
        result = (
            api.build_compact_task_context(request,
                view_options={"schema_version": "llm-wiki-task-view-request/v2" if view == "compact-v2" else "llm-wiki-task-view-request/v1",
                              "budget_tokens": args.view_budget_tokens}, **options)
            if compact else api.build_task_context(request, **options)
        )
        if compact:
            assert isinstance(result, api.CompactTaskContext)
        if not result.ok:
            if compact:
                assert isinstance(result, api.CompactTaskContext)
                assert outputs is not None
                if result.canonical_text:
                    _publish_compact_outputs(outputs, result)
                sys.stderr.write(result.diagnostic_rendered)
            else:
                print(json.dumps(result.to_payload(), sort_keys=True), file=sys.stderr)
            raise SystemExit(3)
        if compact:
            assert outputs is not None
            _publish_compact_outputs(outputs, result)
            if not args.output:
                write_utf8_stdout(result.rendered)
        elif args.output:
            write_text_output(args.output, result.rendered)
        else:
            write_utf8_stdout(result.rendered)
    except (ValueError, api.LlmWikiApiError) as exc:
        invalid = isinstance(exc, (ValueError, api.InvalidRequestError))
        details = getattr(exc, "details", None) or {}
        from ..services.knowledge_storage import KnowledgeStorageError

        cause: BaseException | None = exc
        seen = set()
        while cause is not None and id(cause) not in seen:
            seen.add(id(cause))
            if isinstance(cause, KnowledgeStorageError) and cause.code == "flat-native-adoption-required":
                details = {
                    "reason": "flat-native-adoption-required",
                    "next_action": (
                        "Keep native requirements. With storage migration authorized, "
                        "preview knowledge migrate --wiki-dir WIKI --to sharded-v2 "
                        "--dry-run --recovery-dir RECOVERY. Use an empty recovery directory "
                        "outside source/wiki, inspect the result before applying, and run "
                        "knowledge storage-check --wiki-dir WIKI --full. "
                        "Migration validates the complete snapshot; recover damaged authority."
                    ),
                }
                break
            cause = cause.__cause__
        print(json.dumps({"ok": False, "error": {"code": getattr(exc, "code", None) or
            ("invalid-request" if invalid else "workspace-state-error"),
            "message": "Task context unavailable", "details": details}},
            sort_keys=True), file=sys.stderr)
        raise SystemExit(2 if invalid else 1) from exc
