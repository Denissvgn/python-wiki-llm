"""CLI compatibility adapter for the upgrade runtime service."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from ..services import upgrade_runtime as _service

if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from ..services.upgrade_runtime import (
        UpgradeAborted as UpgradeAborted,
        _clean_old_schema as _clean_old_schema,
        _cleanup_recorded_source as _cleanup_recorded_source,
        _legacy_seed_sync_request as _legacy_seed_sync_request,
        _migrate_reference_skill as _migrate_reference_skill,
        _seed_legacy_for_current_defaults as _seed_legacy_for_current_defaults,
        _target_cleanup_is_ready as _target_cleanup_is_ready,
        _upgrade_schema as _upgrade_schema,
        atomic_write_guarded_bytes as atomic_write_guarded_bytes,
        execute_upgrade as execute_upgrade,
        guarded_tree_manifest as guarded_tree_manifest,
        installed_skill_block_contents as installed_skill_block_contents,
        provision_reference_skill as provision_reference_skill,
        remove_guarded_tree as remove_guarded_tree,
        remove_legacy_hooks as remove_legacy_hooks,
        run as run,
        run_request as run_request,
        shutil as shutil,
        strip_wiki_block as strip_wiki_block,
        unlink_guarded_bytes as unlink_guarded_bytes,
        upgrade_request_from_args as upgrade_request_from_args,
        verify_reference_skill as verify_reference_skill,
        write_config as write_config,
    )

_sys.modules[__name__] = _service
