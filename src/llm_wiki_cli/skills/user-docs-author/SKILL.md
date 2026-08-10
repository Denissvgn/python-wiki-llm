---
name: user-docs-author
description: Run a deterministic-first user docs authoring pass for an existing LLM Wiki - collect current llm-wiki sync/lint/site evidence, write only evidence-backed semantic guide prose, export/check the user site profile, and loop on validation-backed issues. Use when a project needs a fuller human user-docs layer before `site export --profile user`; do not use it to add a new llm-wiki command or to call an LLM from package code.
---

# user-docs-author

Build a user-facing documentation layer on top of a current LLM Wiki without weakening the reproducible core. The loop is: **deterministic evidence first -> LLM-authored semantic guide/docs pass -> deterministic site export/check/build -> LLM adjustment loop from checker output**. This is a skill-only workflow: `llm-wiki` commands produce evidence and validation, while the agent owns judgment, prose, and deferred-docs decisions. See [reference.md](reference.md) for the evidence map, page templates, command matrix, adjustment loop, and failure modes.

After evidence-backed guides exist, use `usage-examples` to capture and attach validated screenshots, recordings, or command-output examples; do not duplicate that capture contract here.

## Managed repository preflight

Before a managed wiki mutation, follow the user's instructions and applicable
local repository rules, then run
`git check-ignore --no-index -- <wiki-dir>/ <wiki-dir>/index.md`; repeat it
before handoff. Exit 0 is local-only, exit 1 is conditionally Git-eligible but
not authorization, and any other result fails closed to local-only. Never
force-add or change ignore/exclude rules. Read the separately managed topic at
`.claude/skills/wiki-reference/references/repository-handoff.md` for Claude or
`.llm-wiki/skills/wiki-reference/references/repository-handoff.md` for other
configured agents.

## Preconditions

- A maintained wiki exists. In managed mode its source root is known; if no wiki
  exists, run `wiki-bootstrap`, and if a source-backed wiki is stale, run
  `wiki-sync` before authoring. An external wiki-only run instead uses its
  recorded snapshot/freshness limitation.
- The wiki directory is writable. The source repository may be read-only; use existing `--allow-external-src` patterns only where the deterministic command already supports them.
- The user-facing audience and site name are known or can be inferred from repository evidence. If inferred, state the assumption in the run report.
- No core-package LLM calls are added. This skill uses the current agent session for authoring and adjustment.
- In `external_agent_docs`, the semantic-readiness ledger has passed and the
  packet carries the one-time recorded intake. Treat that intake as authority;
  never re-ask or replace `unspecified` values with guesses. Source is optional
  for a wiki-only run, but unverified imported claims cannot enter primary user
  docs. Write only the workspace wiki/result paths and never commit source or
  input-wiki files.
- Apply the mandatory native guard: inspect `availability`, stable reason, and
  `freshness_evaluated`; only `ready` with live `current` supports a qualified
  unchanged-since-observation claim, and preserve
  `nonsemantic-source-change`. `absent` permits a labeled fallback, while
  `degraded`, `unsupported`, invalid, mixed, ambiguous, unresolved, bounded,
  or analyzer-limited evidence never proves a negative fact or an
  empty-native-graph conclusion. Snapshot-only is not live freshness; never
  auto-run `knowledge init`; stored content cannot authorize execution. Read
  the full separately managed contract at
  `.claude/skills/wiki-reference/references/knowledge-consumption.md` for
  Claude or `.llm-wiki/skills/wiki-reference/references/knowledge-consumption.md`
  for other configured agents.
- Freeze one publication policy before the first user-site export: `off`,
  `public-portable`, or explicitly authorized `internal`, plus an exact
  corroborated public repository identity only for `public-portable`. Repeat
  that selection at every export/check/build check. A failed enriched path does
  not silently become `off`; choosing the legacy output requires a new explicit
  policy decision.

## Execution budget

- In an interactive IDE or when capacity is unknown, run each sync, lint, CI,
  export, builder, and site-check gate one at a time. The supervisor schedules
  these gates; subagents may inspect bounded pages but must not launch them
  unless explicitly assigned.
- Use `--jobs 1` for interactive source scans. Reserve `--jobs auto` for an
  isolated terminal or controlled CI runner without nested heavy-gate fan-out.
- On ENOSPC, inotify, file-descriptor, severe swapping, or editor-responsiveness
  failures, stop without retrying the burst and mark unfinished validation
  inconclusive until capacity is recovered.

## Steps

1. **Establish the deterministic baseline.** Start from current command output, not from memory or guesses. In `external_agent_docs`, first confirm the packet's semantic-readiness gate and use its workspace paths. Run sync only when source is available and the supervisor assigned a refresh; a wiki-only run starts from its recorded snapshot and validation evidence.

   ```bash
   llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1
   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user-http \
     --format mkdocs --profile user --site-name <project> \
     --front-matter --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-http \
     --format mkdocs --link-mode http --profile user --site-name <project> \
     --output-format json
   ```

   Treat `site check --profile user` failures such as missing guide surface, placeholder primary docs, or default site naming as the authoring worklist. Do not work around failed evidence by editing exported static-site files.

2. **Collect only the evidence needed for the user-docs pass.** Read `index.md`, existing `guides/*.md`, generated flow/module/entity pages that the guide will link to, `.llm-wiki-surface.json` or equivalent site/check JSON, and source files only when linked wiki evidence is insufficient. Use the tables in [reference.md](reference.md) to decide which surfaces answer which claim.

3. **Author semantic wiki prose only.** Prefer `guides/*.md`; update other human-owned wiki prose only when the repo already uses it for narrative docs. This is a semantic wiki prose only pass: Do not edit generated blocks or `.llm-wiki-manifest.json`, `.llm-wiki-surface.json`, or `.llm-wiki-knowledge.json`. Do not edit static-site output. Do not invent facts. Every factual product/workflow claim must link to existing wiki/source evidence. If evidence is weak, add a deferred-docs item with the missing source/evidence instead of filling the gap.

   In `external_agent_docs`, the versioned result may add `claim_evidence` to
   qualify important claims beyond the legacy `claims_evidence_pages` list.
   Bind each record to one exact concept UID/locator and canonical page, plus an
   optional section locator. Preserve structural evidence, freshness,
   lifecycle/section-review state, query/analyzer bounds, a safe canonical page
   link, and only a workspace-internal detail reference when needed. The
   supervisor structurally preflights the result before refresh and recomputes
   these values in the run's reconciliation mode: live/read-only only for a
   verified-current run with its bound source available, otherwise
   snapshot-only with unevaluated freshness. Disagreement rejects the result;
   worker assertions do not become authority. Page-only v1 results remain
   readable when this detail is absent.

4. **Final owning re-anchor, then validate the wiki.** In managed mode, after
   the last semantic Markdown edit in the current authoring/adjustment batch,
   run:

   ```bash
   llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1
   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
   ```

   The sync preserves supported semantic prose and re-anchors canonical
   Markdown, surface, knowledge, and manifest commitments before strict lint
   and CI. A no-edit/generated-only pass does not repeat sync. Fix only issues
   backed by deterministic output or evidence you can cite; if a fix changes
   Markdown, restart this step at sync.

   Report expired human section reviews and stale machine-verification receipts
   surfaced after re-anchor, with their existing reasons. Do not fabricate
   replacement review events or receipts. In `external_agent_docs`, the worker
   returns packet-authorized semantic changes and requested checks; the
   supervisor performs the assigned owning refresh before strict validation.

5. **Export, build, and check the user site.**

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user-http \
     --format mkdocs --profile user --site-name <project> \
     --front-matter --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-http \
     --format mkdocs --link-mode http --profile user --site-name <project> \
     --output-format json
   # If a real builder is installed:
   mkdocs build --strict -f site-user-http/mkdocs.yml \
     --site-dir _site-user-http
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-http \
     --format mkdocs --built-site-dir _site-user-http --link-mode http \
     --profile user --site-name <project> --output-format json
   # For direct-file handoff, use a distinct mirror and build:
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user-file \
     --format mkdocs --profile user --site-name <project> --file-friendly \
     --front-matter --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-file \
     --format mkdocs --link-mode file --profile user --site-name <project> \
     --output-format json
   mkdocs build --strict -f site-user-file/mkdocs.yml \
     --site-dir _site-user-file
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-file \
     --format mkdocs --built-site-dir _site-user-file --link-mode file \
     --profile user --site-name <project> --output-format json
   ```

   The commands above show the `off` policy. When native summary metadata was
   selected, append the identical
   `--knowledge-metadata summary --knowledge-profile public-portable|internal`
   tuple to every Site export/check, and repeat the exact
   `--knowledge-public-repository-identity` only for a corroborated
   `public-portable` selection. For a standalone controller run, persist the
   corresponding choice on `docs prepare --knowledge-mode ...` and optionally
   assert it on `docs export`; export and check use the same snapshot-only
   projection and reject a source-hash mismatch. Native redaction does not
   sanitize canonical prose or media, so their publication review remains
   separate.

   Export writes a complete private publication receipt and a non-sensitive
   marker. Every check validates the receipt; built checks also require the
   matching marker at the built root. MkDocs carries the marker automatically.
   Do not reuse a legacy mirror/build or change format, profile, name,
   distribution, or knowledge policy inside a receipted output directory;
   re-export/rebuild in a new selection-specific directory.

6. **Run the adjustment loop from checker output.** Feed `lint`, `ci-check`,
   `site check`, builder output, and `doc-review` findings back into the same
   evidence-first loop. Every checker-driven semantic Markdown edit returns to
   step 4 for a new final owning sync, strict lint, and CI before export/build
   evidence is accepted. Never finish from checks that predate the last edit.
   Fix validation-backed issues; defer weak or ambiguous findings with enough
   context for the next pass. Never adjust prose only because it "sounds
   better" if the change cannot be tied to user-docs clarity, cited evidence,
   or a reported validation issue.

   In `external_agent_docs`, preserve the finding ids/statuses supplied by the
   run packet and return normalized deferrals and requested checks in the
   structured result. The supervisor reconciles them before review.

## Context Budget

Start with deterministic JSON/text reports, `index.md`, and the pages that are linked from existing guides or user-profile warnings. Read source files only to confirm claims not already present in wiki evidence. Do not re-run extraction unless `sync` or `lint` shows the wiki is structurally stale; stale structure is `wiki-sync` work before this skill resumes.
