"""Library-owned current formats for authorized project setup and upgrade."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile

CURRENT_KNOWLEDGE_FORMAT = "packed-v4-deflate"
CURRENT_MANIFEST_FORMAT = "indexed-v8"


def current_contract_defaults() -> dict:
    """Return detached installation policy; callers do not elect wire versions."""
    return {"policy": "current", "task_request": "llm-wiki-task-request/v2",
            "compact_view": "llm-wiki-task-view-request/v2",
            "knowledge_format": CURRENT_KNOWLEDGE_FORMAT,
            "manifest_format": CURRENT_MANIFEST_FORMAT,
            "storage_selection": "required-facets-v1", "storage_receipt": "compact-v1"}


def upgrade_current_knowledge(src_dir, wiki_dir, *, helper_cache_dir=None, source_selection=None,
                              allow_external_src=False, _captured=None, _seed_legacy=None) -> dict:
    """Use existing guarded writers and recovery copies; never repair bad authority."""
    from .knowledge_artifacts import current_knowledge_format
    from .knowledge_storage_lifecycle import _committed_inputs, migrate_knowledge_storage
    from .maintenance_protocol import load_adoption_marker, guard_maintenance_owner
    from .maintenance_service import adopt_maintenance_authority
    from .manifest_storage import current_manifest_format
    from .knowledge_storage_lifecycle import _absolute_path
    from .filesystem_guard import ensure_guarded_directory

    wiki = _absolute_path(Path(wiki_dir))
    root = wiki / ".llm-wiki-knowledge.json"
    manifest = wiki / ".llm-wiki-manifest.json"
    surface = wiki / ".llm-wiki-surface.json"
    adopted = load_adoption_marker(wiki) is not None
    if adopted:
        guard_maintenance_owner(wiki)
    if not root.exists() and (wiki / ".llm-wiki-governance.json").exists():
        raise ValueError("Missing governed native authority requires recovery")
    if not root.exists() and not manifest.exists() and not surface.exists():
        from .wiki_lifecycle import is_pristine_wiki_target
        if not (wiki / "index.md").is_file() or is_pristine_wiki_target(wiki):
            # init provisions a scaffold; an established canonical wiki instead
            # enters the guarded legacy owning-seed route below.
            return {"changed": False, "state": "awaiting-bootstrap"}
    if (adopted and current_knowledge_format(wiki) == CURRENT_KNOWLEDGE_FORMAT
            and current_manifest_format(wiki) == CURRENT_MANIFEST_FORMAT):
        _committed_inputs(wiki)
        return {"changed": False, "state": "current"}
    identity = hashlib.sha256(str(wiki).encode()).hexdigest()[:20]
    recovery_base = Path(tempfile.gettempdir()).resolve() / "llm-wiki-upgrade-recovery"
    ensure_guarded_directory(recovery_base, mode=0o700)
    recovery = Path(tempfile.mkdtemp(prefix=identity + "-", dir=recovery_base))
    _absolute_path(recovery)
    if not root.exists() and not adopted:
        from .knowledge_consumption import load_knowledge_read_view
        from .maintenance_protocol import snapshot_wiki, save_recovery_snapshot

        # Only an independently valid uncommitted legacy surface can be seeded.
        # A newer commitment to missing native data is corruption, not legacy.
        if manifest.exists():
            payload = json.loads(manifest.read_bytes())
            if payload.get("version") not in (1, 2, 3, 4) or payload.get("artifact_hashes"):
                raise ValueError("Missing committed native authority requires recovery")
        if surface.exists() or surface.is_symlink():
            view = load_knowledge_read_view(wiki, snapshot_only=True)
            if view.availability != "absent":
                raise ValueError("Missing committed native authority requires recovery")
        save_recovery_snapshot(recovery / "legacy", snapshot_wiki(wiki), marker=None, kind="legacy-preimage")
        if _seed_legacy is None:
            raise ValueError("Legacy native setup requires owning project init or upgrade")
        _seed_legacy(src_dir, wiki, helper_cache_dir=helper_cache_dir, source_selection=source_selection)

    _committed_inputs(wiki)
    # Ownership adoption captures source/helper bases before publishing. It
    # creates pending ordinary maintenance, never synthetic human approval.
    if not adopted:
        adopt_maintenance_authority(src_dir, wiki, recovery_dir=recovery / "adoption",
            manifest_format=CURRENT_MANIFEST_FORMAT, helper_cache_dir=helper_cache_dir,
            source_selection=source_selection, allow_external_src=allow_external_src, _captured=_captured)
    if current_knowledge_format(wiki) != CURRENT_KNOWLEDGE_FORMAT:
        migrate_knowledge_storage(wiki, to=CURRENT_KNOWLEDGE_FORMAT, recovery_dir=recovery / "knowledge")
    if current_manifest_format(wiki) != CURRENT_MANIFEST_FORMAT:
        migrate_knowledge_storage(wiki, to=CURRENT_MANIFEST_FORMAT, recovery_dir=recovery / "manifest")
    _committed_inputs(wiki)
    return {"changed": True, "state": "current", "recovery_dir": str(recovery)}
