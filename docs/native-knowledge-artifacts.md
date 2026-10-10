# Native knowledge artifact operations

## Experimental status

The `.llm-wiki-knowledge.json` projection is an experimental, generated
observation artifact. It is not an editable authority, a public export, a
freshness verdict, or an authorization record. Canonical Markdown remains the
human/agent editing surface, and `.llm-wiki-surface.json` remains on the
unchanged `llm-wiki-surface-index/v1` contract.

A valid projection commit includes three generated roots produced from the
same evaluated inputs:

- `.llm-wiki-surface.json`;
- `.llm-wiki-knowledge.json`; and
- `.llm-wiki-manifest.json`, written last with exact hashes of both
  projections and the evaluated envelope.

When governance is enabled, the committed set must also include the
authoritative `.llm-wiki-governance.json` ledger. The validated loader rejects
a governed projection whose ledger is missing or invalid.

For sharded or packed storage, commit every referenced object, pack and routing
container alongside those roots. An adopted indexed manifest also needs its
referenced catalogs. Existing storage formats remain compatible; bounded task
reads select supported storage explicitly. See [knowledge storage](knowledge-storage.md).

Optional ordinary review adds the immutable
`.llm-wiki-maintenance-adoption.json` marker and matching manifest-owned
maintenance state. Keep that complete authority and its projected bindings
intact. An agent acknowledgment records operational review, not human governance
approval. Review tracking and storage adoption are separate choices.

Consumers must use the validated loader. A file that merely exists is not
trusted: malformed data, stale commit markers, hash mismatches, and mixed
snapshots are rejected or exposed only through an explicitly selected degraded
surface-only policy.

The internal projection may include repository-relative source paths, current
revision evidence, producer identifiers, and lossless non-credential link
targets. It must not include machine-local absolute paths, raw VCS remotes,
environment dumps, authority userinfo, or raw producer configuration.
Configuration and generation options enter the artifact only through
commitment hashes. The raw knowledge artifact is not safe to publish merely
because it passes its schema. For publication, use the implemented
[`public-portable` projection profile](native-knowledge.md#safe-derived-projections),
which applies an explicit allowlist and omits private evidence, identities,
producer details, unknown extensions, credential-like values, environment
details, and machine-local paths. These default generation boundaries do not
authorize callers to place private data in arbitrary extensions, and they do
not make the raw knowledge artifact suitable for publication.

## Compatibility and recovery

Legacy wikis that never declared a knowledge projection remain readable in
surface-only mode. The current CLI does not provide an in-place switch that
converts a committed knowledge-capable artifact set into that legacy shape.
Deleting only `.llm-wiki-knowledge.json` or editing its manifest commitment
creates an invalid or mixed snapshot; it is not a supported rollback.

If only the generated projections are damaged while the manifest is readable
and any required governance and maintenance authority remains valid, preserve
the damaged files
when diagnostics are needed, then run `llm-wiki sync` to regenerate one
evaluated snapshot. Restore a missing or invalid manifest or governance ledger
from version control or backup before syncing. A missing/corrupt adopted
maintenance owner or mismatched marker needs its verified complete
[maintenance recovery snapshot](maintenance.md#recover-complete-authority);
manifestless seeding and single-file knowledge export cannot recreate its
history. Preserve newer work when recovery eligibility rejects a replacement.
When the selected release
requires migration, follow its `llm-wiki migrate` and release-specific
migration guidance. Do not hand-edit hashes or copy a projection from a
different run.

Moving a repository to a CLI release that predates native knowledge requires
that release's own migration guidance and a version-controlled restoration of
the complete artifact set. Perform such a downgrade on an isolated branch and
validate the resulting wiki with the selected release before restoring
automated writers.
