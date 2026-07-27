# Native knowledge M1 operations

## Experimental status

The `.llm-wiki-knowledge.json` projection is an experimental, generated
observation artifact. It is not an editable authority, a public export, a
freshness verdict, or an authorization record. Canonical Markdown remains the
human/agent editing surface, and `.llm-wiki-surface.json` remains on the
unchanged `llm-wiki-surface-index/v1` contract.

One valid M1 state consists of three files produced from the same evaluated
inputs:

- `.llm-wiki-surface.json`;
- `.llm-wiki-knowledge.json`; and
- `.llm-wiki-manifest.json`, written last with exact hashes of both
  projections and the evaluated envelope.

Consumers must use the validated loader. A file that merely exists is not
trusted: malformed data, stale commit markers, hash mismatches, and mixed
snapshots are rejected or exposed only through an explicitly selected degraded
surface-only policy.

The internal projection may include repository-relative source paths, current
revision evidence, producer identifiers, and lossless non-credential link
targets. It must not include machine-local absolute paths, raw VCS remotes,
environment dumps, authority userinfo, or raw producer configuration.
Configuration and generation options enter the artifact only through
commitment hashes. The M1 artifact is not safe to publish merely because it
passes its schema: public projection allowlists and heuristic scanning of query
strings and arbitrary extension values remain deferred to KNOW-501.

## Accepted M1 performance budget

The deterministic harness in
`tests/knowledge_m1_benchmark.py` constructs already-evaluated Python inventory,
canonical pages, surface-v1 payloads, source commitments, and producer metadata
without discovery or extractor execution. Timing covers the production planner
through evidence, envelope, links, knowledge validation/serialization, and the
commit plan. Fixture construction and artifact writes are excluded.

The following CI-safe ceilings are accepted for M1:

| Scale | Sources | Entities/source | Active pages | Maximum knowledge bytes | Maximum planner time |
|---|---:|---:|---:|---:|---:|
| Small | 2 | 2 | 7 | 128 KiB | 2 seconds |
| Medium | 20 | 4 | 101 | 2 MiB | 8 seconds |
| Large | 75 | 6 | 526 | 12 MiB | 30 seconds |

These are regression ceilings, not size targets. M1 performs no implicit
truncation. A budget breach requires an explicit contract/performance review
before changing the ceiling or adding a documented truncation policy.

A reference run on 2026-07-26 using Python 3.14.5 on arm64 macOS produced:

| Scale | Knowledge bytes | Surface bytes | Manifest bytes | Median planner time |
|---|---:|---:|---:|---:|
| Small | 15,045 | 3,179 | 6,928 | 0.006 seconds |
| Medium | 226,525 | 36,133 | 105,507 | 0.070 seconds |
| Large | 1,201,865 | 186,139 | 548,101 | 0.378 seconds |

Run the enforced privacy and performance gates with:

```bash
PYTHONPATH=src .venv/bin/pytest -q tests/test_knowledge_m1_hardening.py
```

Print a fresh machine-readable benchmark observation with:

```bash
PYTHONPATH=src .venv/bin/python -m tests.knowledge_m1_benchmark
```

Timing varies by machine; deterministic artifact bytes and the accepted
ceilings are the gates.

## Privacy verification

The KNOW-111 privacy gate drives the production planner with canaries placed in
source bytes, Markdown prose, an environment variable, generation options,
producer configuration, absolute page object paths, a credential-bearing link,
and a raw credentialed VCS remote. It recursively scans the generated surface,
knowledge, and manifest JSON payloads and fails on:

- any canary or private remote value;
- Unix or Windows absolute paths;
- URI authority userinfo; or
- common secret-bearing JSON key names.

This verifies default generation boundaries. It does not authorize callers to
put private data in arbitrary extensions, and it does not replace a future
public-export redaction profile.

## Rollback

Canonical Markdown and assets do not need conversion when rolling back M1.
Use this procedure:

1. Stop bootstrap/sync writers and preserve the three hidden JSON artifacts if
   they are needed for diagnosis.
2. Pin the last pre-M1 CLI version.
3. Remove `.llm-wiki-knowledge.json` and the M1
   `.llm-wiki-manifest.json`. Do not leave a manifest that still commits to a
   missing knowledge projection. If rollback interrupts chunked migration,
   also remove the temporary `.llm-wiki-migration-progress.json` receipt after
   preserving it for diagnosis.
4. Keep `.llm-wiki-surface.json` when its unchanged v1 bytes are useful, or let
   the pinned CLI regenerate it.
5. Run the pinned CLI's normal sync path to reconstruct its manifest from the
   existing canonical Markdown and source tree. Do not bootstrap over that
   preserved wiki.
6. Run lint before restoring automated writers.

Deleting only `.llm-wiki-knowledge.json` while its hash remains in the manifest
is an integrity failure, not a clean rollback; the validated loader correctly
reports that state as invalid. A clean surface-only state has no knowledge
projection and no manifest commitment declaring one.

Re-enabling an M1-capable writer rebuilds all three artifacts from one evaluated
snapshot. Do not hand-edit hashes or copy a projection from a different run.
