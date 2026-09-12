# Automation

[Back to README](../README.md) · [Command reference](cli-reference.md)

Keep wiki maintenance explicit and use CI to check the committed result.
Choose the [full integrity gate](#install-the-full-integrity-gate) for blocking
validation or the [doctor dashboard](#strict-doctor-dashboard) for knowledge
health diagnostics. [Manual agent triggers](#manual-agent-triggers) and
[cleanup of retired hooks](#git-hook-retirement) are described separately.

## Install the full integrity gate

After `bootstrap` has created a managed wiki, install its dedicated workflow:

```bash
llm-wiki install-ci --action-ref "$RELEASE_COMMIT_SHA" --dry-run
llm-wiki install-ci --action-ref "$RELEASE_COMMIT_SHA"
```

The command writes only
`.github/workflows/llm-wiki-integrity.yml`. Rerunning it with the same inputs is
an exact no-op, while an older unmodified workflow installed by this command is
updated safely. An unmanaged or locally modified workflow is preserved and
reported as a conflict unless `--force` is supplied; unrelated workflow files
are never modified.

The installed workflow checks out the project without persisted credentials
and calls the release's reusable full-integrity action with read-only
permissions. That action installs the CLI from its immutable action checkout,
discovers helper languages through default source-selection discovery (using
`.llm-wiki/source-selection.json` when present), installs their
checksum-verified toolchains in runner-temporary storage, and prepares detected
TypeScript/JavaScript, Go, Rust, and Haskell helpers. Python extraction is built
in and needs no external helper. A pinned GitHub cache action restores only an
exact helper-cache key covering the runner platform, release toolchain lock,
selected helper sources and dependency locks, helper-cache contract, CLI
version, and immutable action ref. Helper preparation still runs after every
restore, so a miss or unusable entry rebuilds instead of reducing language
coverage. Pull requests may restore the cache but only a successful push to the
default branch may save a new entry.

The action then runs the strict `ci-check` gate with advisory native-drift
diagnostics, verifies that the project worktree stayed clean, and uploads a
fixed, allowlisted set of validation, cache-measurement, and toolchain evidence
even when validation fails.

Installed pull-request workflows fetch full history and supply the fetched
base and head commits to the same action for advisory change impact. The action
adds a bounded job summary, up to 50 warning/notice annotations, and
`llm-wiki-impact.json` / `llm-wiki-impact.md` artifacts. Reporting failures do
not replace the integrity result. Callers of the action can opt in by setting
both `impact-base` and `impact-head`.

The portable gate disables project-local Python plugins so pull-request content
is never imported or executed. A project that intentionally depends on trusted
extractor, generation, or lint plugins must use a separately reviewed trusted
workflow instead of this pull-request gate.

Installation does not bootstrap or synchronize the wiki, change branch
protection, install hooks, push commits, or add repository secrets. Those
remain explicit maintainer actions.

## Git hook retirement

Git hook installation has been removed. After updating the package, run the
workspace upgrade from each repository that used LLM Wiki:

```bash
pip install --upgrade agent-wiki-cli
llm-wiki upgrade
```

`upgrade` automatically removes recognized, unmodified LLM Wiki `post-commit`,
`pre-commit`, and `pre-push` hooks, including older background-agent and version
bump hooks. Cleanup runs before agent instruction refresh and does not require
an agent preference. If instruction refresh then needs configuration repair,
the hook cleanup remains complete. Repeating the upgrade is safe.

Cleanup covers the repository's Git hooks directory, the shared Git directory
of a linked worktree, and a repository-local `core.hooksPath`. Customized hooks,
unrelated hooks, and external/global hook directories remain user-managed.
Unsafe or unreadable hook paths stop cleanup with an error; changed files are
rechecked before removal. Package installation itself does not discover or
modify arbitrary repositories. Read-only commands do not remove hooks.

For a reviewed prompt, run `llm-wiki generate-prompt` explicitly. The retired
`install-hook` command is no longer available.

## Manual agent triggers

For advanced trusted workflows, `trigger-agent` remains available as an explicit
manual command:

```bash
llm-wiki trigger-agent --agent <agent>
```

The trigger command:

- takes `git diff HEAD~1..HEAD`;
- skips empty diffs and oversized diffs unless `--force` is used;
- uses a lock file to prevent concurrent syncs;
- opens a circuit breaker after repeated failures;
- builds deep source inventory and call-graph context;
- filters credential-like values from the generated prompt on a best-effort
  basis, then writes `.git/llm-wiki-prompt.txt` with owner-only permissions
  where supported;
- invokes the selected agent with a prompt that asks it to update, lint, and
  follow a repository-aware handoff. A Git-ignored or indeterminate wiki stays
  local and is never force-added or committed.

Useful trigger options:

```bash
llm-wiki trigger-agent --agent claude --timeout 600 --max-diff-lines 2000
llm-wiki trigger-agent --agent claude --max-prompt-bytes 2000000
llm-wiki trigger-agent --agent claude --force
llm-wiki trigger-agent --reset-breaker
```

Failed trigger runs exit nonzero, including preparation and runner launch failures.
Runner timeouts exit `124`; other positive child exit codes are preserved.
Empty or oversized inputs, an occupied lock, and an open breaker remain successful
skips. Each attempted run records its outcome for the circuit breaker and metrics.

Set `LLM_WIKI_LOCK_WAIT` to a non-negative number of seconds when a trusted
automation runner should wait briefly for another sync to release the lock.
The circuit breaker permits one automatic recovery attempt after 3600 seconds
by default; set `LLM_WIKI_BREAKER_TTL_SECONDS` to another non-negative duration,
or to `0` to require `--reset-breaker`.

## Strict doctor dashboard

The context-health composite action publishes a diagnostic knowledge-health
dashboard and applies a configurable failure threshold. It is intentionally
separate from the blocking full-integrity gate: it does not replace general
wiki checks, trusted plugin validation, or team-owned review policy.

```yaml
- uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
- uses: Denissvgn/python-wiki-llm/integrations/github-action@<FULL_RELEASE_COMMIT_SHA>
  with:
    wiki-dir: docs/llm_wiki
    src-dir: .
    source-selection: .llm-wiki/source-selection.json
    strict: "true"
    fail-on: unhealthy
    evidence-id: default
```

Use `fail-on: unhealthy` to allow degraded-but-usable knowledge while blocking
mixed snapshots, invalid governance, confirmed stale concepts, and invalid
verification receipts. Use `fail-on: degraded` when any degraded result must
block the job. `strict: "true"` also classifies indeterminate or nonsemantic
source drift as unhealthy. Replace `<FULL_RELEASE_COMMIT_SHA>` with the full
40-character SHA of the immutable released commit; never use a branch or tag
for a protected workflow.

The action installs `agent-wiki-cli` from the same action checkout, so pinning
the action reference also binds the CLI implementation. Through the same
default source-selection discovery used by the CLI, it plans and prepares any
detected TypeScript/JavaScript, Go, Rust, or Haskell extractor helper with the
release's checksum-verified toolchains; Python extraction needs no helper. It
then invokes `llm-wiki doctor --format json` and reads only the complete,
versioned `llm-wiki-doctor/v1` object. The renderer rejects a report when its
strictness or declared exit code does not match the captured request and
process status, and it never scrapes human output. Within that schema major,
required fields and documented state values remain strict while additive
object fields are ignored. A wiki that has not been initialized is reported as
`absent` and fails either threshold.

The action reserves isolated runner-temporary cache, toolchain, and evidence
paths and uploads only the JSON
report, a hash-bound dashboard receipt, the extractor plan, and the preparation
log. Human disclosure text is escaped and the job summary has fixed size and
line bounds. This repository also provides a separately named, manually
dispatched dashboard workflow; it has read-only permissions and no scheduled,
pull-request, or push trigger. Branch protection should continue to require the
exact `LLM Wiki integrity` context produced by the full gate, not this
diagnostic dashboard.

Omit `source-selection` to use default discovery. Set it to the same
source-root-relative non-default profile used by local maintenance commands
when a repository does not use `.llm-wiki/source-selection.json`.
The default `evidence-id` is sufficient for one invocation in a job. Give each
invocation a unique lowercase identifier when the same action is used more
than once; unsafe identifiers and occupied runner paths fail closed before any
artifact upload.
