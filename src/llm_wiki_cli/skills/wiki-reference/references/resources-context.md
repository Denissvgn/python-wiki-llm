# Resource-aware execution

Read this topic before scheduling a broad context scan, extraction, build,
coverage run, browser suite, sync, lint, CI check, or another resource-heavy
gate. It owns scheduling and capacity fallback only. It never authorizes a
command, install, network operation, repository mutation, or wider source
selection.

## Environment matrix

| Environment | Extractor jobs | Scheduling rule |
| --- | --- | --- |
| Interactive IDE or unknown capacity | `--jobs 1` | Run one heavy gate at a time. The supervisor owns the schedule; subagents may inspect bounded files and diffs but must not launch a heavy gate unless explicitly assigned. |
| Isolated terminal | `--jobs auto` is allowed | Use it only when that terminal owns the sole heavy gate and host capacity is available. Do not nest another build, context, or validation fan-out. |
| Controlled CI | `--jobs auto` is allowed with reserved capacity | Run one top-level gate per reserved runner allocation. Use `--jobs 1` whenever capacity is shared or unknown. |

Treat context, full verification suites, coverage, builds, browser suites,
sync, lint, and CI checks as heavy gates. A task request and applicable
repository policy still decide whether any gate may run.

## Extractor-plan disclosures

Keep these values distinct when reading a plan:

- `requested_jobs` is the caller's raw choice, such as `1` or `auto`.
- `resolved_jobs` is the integer concurrency ceiling. `auto` resolves to the
  visible logical CPU count, with a minimum of one.
- `effective_workers` is the maximum number of extraction plans that can run
  simultaneously after absent languages, cache-elided work, sequential-only
  plugins, and eligible-plan caps are applied. It is zero when no extraction
  remains and one for sequential-only work.

Eligible-parallel, parallel-plan, sequential-plan, and cache-elided-plan fields
explain why effective concurrency can be lower than the requested or resolved
value. `auto` is not a global host-resource cap and does not make nested
parallelism safe.

## Capacity failure

On ENOSPC, inotify, file-descriptor, severe swapping, or editor-responsiveness
failure, stop launching work and do not retry the same parallel burst. Mark
unfinished gates inconclusive until capacity is recovered. One later manual
retry may use `--jobs 1` after the underlying condition changes. Watcher-limit
symptoms are host or IDE resource evidence, not proof that `llm-wiki` leaked a
watcher.

For choosing broad versus targeted evidence after scheduling is safe, read
[Context and query selection](context-query.md).
