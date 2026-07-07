---
name: usage-examples
description: Capture evidence-linked usage examples for user docs - run documented flows, attach screenshots or recordings under the wiki assets surface, validate media links, and defer honestly when capture tooling or runtime access is unavailable. Use after authored guides exist; do not use it to invent product behavior, install capture tools, or edit generated site output.
---

# usage-examples

Add worked examples to user-facing docs without weakening the deterministic
wiki contract. The core rule: examples are evidence, not decoration. A capture
is valid only when it demonstrates a flow already documented by a guide and
backed by wiki/source evidence. This skill uses the current agent session for
judgment and capture; package code never calls an LLM or installs tooling.
See [reference.md](reference.md) for capture tooling checks, media policy,
redaction rules, command matrix, deferred rows, and failure modes.

## Preconditions

- A maintained wiki exists and strict lint is clean. If not, run `wiki-sync`
  or `wiki-bootstrap` first.
- Authored guide pages exist under `guides/*.md`. If guides are missing or
  mostly placeholders, run `user-docs-author` before this skill.
- Capture tooling is checked, never installed. The agent platform may provide
  screenshots, browser automation, terminal recording, or video recording; this
  package only validates the files that result.
- Use a read-only source target unless the user explicitly asks for source
  edits. Run flows in a disposable working directory or scratch path.

## Steps

1. **Build the worklist from evidence.** Read `guides/*.md`,
   `.llm-wiki-surface.json`, and the linked wiki pages that support each guide
   section. Each candidate example must name the guide section, the exact flow
   or command, and the evidence page that already documents it.

2. **Choose the lightest capture.** Prefer real command output in fenced
   blocks when text communicates the behavior. Use screenshots or recordings
   only for state, layout, motion, or UI steps that text cannot show well.

3. **Run the flow in isolation.** Use a disposable directory and a read-only
   source target. Do not use real credentials, real user data, machine-specific
   absolute paths, or secrets. Re-run or redact any capture that exposes them.

4. **Attach under the mirrored asset path.** Store media under
   `assets/<surface>/<page-stem>/<name>.<ext>` next to the owning wiki page's
   logical path when practical. Page-local media outside `assets/` is mirrored
   by export but should be treated as convention drift and cleaned up when the
   page is being edited. Embed images with descriptive alt text. Add a one-line
   caption naming the exact command or flow and linking the evidence page.

5. **Validate and adjust.**

   ```bash
   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user \
     --format mkdocs --profile user --site-name <project> --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
     --profile user --site-name <project> --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
     --built-site-dir _site --link-mode http --profile user \
     --site-name <project> --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
     --built-site-dir _site --link-mode file --profile user \
     --site-name <project> --output-format json
   ```

   Treat `media_link_broken`, `media_missing_alt_text`, `media_oversize`,
   `media_orphan`, `media_outside_assets`, `asset_unrecognized_type`,
   `media_symlink_escape`, `missing_built_media_target`, and
   `user_docs_missing_examples` as the adjustment worklist.

6. **Defer honestly.** If a flow cannot be exercised because credentials,
   runtime services, browser support, or capture tooling are missing, add a
   deferred-docs row with a `capture blocker` value. Never stage a screenshot
   of behavior the runner cannot actually exercise.

7. **Write the run report.** Record captured examples, tool versions or agent
   platform capabilities used, deferred flows, media paths, validation results,
   and any follow-up defaults or policy changes.

## Context Budget

Start with guides, `.llm-wiki-surface.json`, and deterministic validation
reports. Read only the linked wiki/source evidence for flows selected for
capture. Do not scan the whole repository for examples, and do not re-run
extraction unless sync or lint says the wiki is stale.
