---
name: attack-surface
description: Map a repository's attack surface with LLM Wiki — prepare extractor helpers, run `llm-wiki extract --deep --read-only`, discover the repository security model, treat data-flow gaps as unknown surface, supplement with a ranked source-level sink scan, and write a prioritized exposure report that hands suspicious paths to deeper security review. Use to prepare or scope a defensive security review of a repository you maintain; it is reconnaissance, not a SAST replacement.
---

# attack-surface

Build a prioritized, evidence-backed map of a repository's entry points and boundary effects so a deeper security review knows where to look first. The loop is: **prepare helpers → deep read-only extract → discover the security model → group entrypoints by trust boundary → walk data flows with gaps as unknowns → ranked source-level sink scan → prioritized exposure report → hand off**. The output locates and assesses surfaces; it never claims SAST-level coverage and never attempts exploitation. See [reference.md](reference.md) for the live extract schema, exposure-report artifact format, boundary/gap taxonomies, the sink-scan pattern table, and failure modes.

## Preconditions

- This is a defensive review of a repository the user owns, maintains, or is authorized to assess. The workflow reads source and writes one report; it does not exploit, patch, or harden anything by itself.
- The repository is readable and the report destination (default `reports/`) is writable. The extract itself runs `--read-only`, so no llm-wiki files are written to the target tree except the explicit `--output` payload.
- Helper toolchains for the repo's languages are available, or documented overrides are captured up front (for example `LLM_WIKI_GO=/usr/local/go/bin/go` or `LLM_WIKI_GHC=/path/to/ghc`). In sandboxes where the default cache location is read-only, choose a writable `--helper-cache-dir` before starting.
- If `--src-dir` points outside the current working directory, pass `--allow-external-src` consistently to every source-reading command in the run, including `prepare-extractors`, `extract`, `lint`, `ci-check`, and `team check`. Keep report, output, and wiki paths under the current project unless the user explicitly chooses a safe temporary path.

## Steps

1. **Prepare helpers through the CLI.**

   ```bash
   llm-wiki prepare-extractors --src-dir .
   ```

   For an external source root:

   ```bash
   llm-wiki prepare-extractors --src-dir <repo> --allow-external-src
   ```

   Deep extract fails closed when helpers for a detected language are missing — prepare first, do not skip languages to make the error go away. Use `--cache-dir` to select a writable helper cache when the default location is read-only, and the `LLM_WIKI_GO` / `LLM_WIKI_GHC` overrides when the toolchain on `PATH` is broken. Carry any unsupported-source notices forward: they are coverage gaps the final report must state, not ignorable warnings.

2. **Run the deep read-only extract.**

   ```bash
   llm-wiki extract --src-dir . --deep --read-only \
     --output /tmp/attack-surface-extract.json
   ```

   Add `--helper-cache-dir` to match step 1. Record the schema version, inventory file count, `entrypoints` count, `data_flows` count, and the counts of `data_flows[].boundaries`, `data_flows[].gaps`, and `data_flows[].truncated` rows — they head the report's evidence section.

3. **Seed the coverage worklist from the security model.** Discover the authoritative security model in this order: root `SECURITY.md`, root `security-policy.json`, `docs/security/**`, security ADRs, security scanner workflows, then explicit user selection when multiple plausible models remain. Every named high-risk area becomes a required coverage row in the final report — the run is not done while a named area has no evidence row. When no security model is documented, say so in the report and derive the worklist from entrypoint groups instead.

4. **Group entrypoints by trust boundary.** Group `entrypoints` by category — `cli`, `api`, `mcp`, `process`, plus hook and plugin surfaces — and state each group's trust boundary explicitly: who can reach it and with what input. MCP tools and plugin loading are local API/tool surfaces with their own trust story; never report them as just files.

   Compare extracted entrypoint categories against source and infrastructure evidence before trusting the queue. In mixed-language repos, verify Go `net/http` servers and Haskell Servant/Warp applications are either represented as HTTP entrypoints or recorded as uncovered surface with file, language, and suspected framework.

5. **Walk data flows with gaps as first-class unknowns.** For each flow in `data_flows`, record `data_flows[].boundaries` such as `filesystem_write`, `process`, `environment_read`, `mutation`, and `output`; record every `data_flows[].gaps` value such as `unresolved_call`, `external_call`, `step_limit`, and `truncated_flow`; and record `data_flows[].truncated` as unknown surface. Never interpret a missing sink as a safe path — a bounded flow walk underreports sinks by design.

6. **Supplement with a ranked source-level sink scan.** Exclude docs, tests, generated coverage, caches, and dependency/vendor/build-output directories unless the security model names them. Review source roots in this order: security-model named files and surfaces; entrypoints with `process`, `filesystem_write`, `network`, or `environment_read` boundaries; truncated flows; high-centrality HTTP routes; then the long tail as explicit remainder. For every entrypoint whose flow contains truncation or step-limit gaps, and for support code the security model names explicitly (helper subprocesses, extractors, hook scripts), scan reachable source for sinks: subprocess/shell execution, filesystem writes and deletes, environment reads and writes, network binds, and dynamic import/plugin loading. When source evidence and the extracted flow disagree, promote the source evidence — cite file paths and line ranges, and note the controls found next to each sink (allowlists, fixed argv, timeouts, path validation, locks).

7. **Write the prioritized exposure inventory.** Create `reports/attack_surface_<YYYY-MM-DD>.md` with one `AS-NNN` item per exposure, ordered by review value, using the artifact format in [reference.md](reference.md): extracted flow, source evidence with line ranges, existing controls, security-model alignment, and a conclusion. Capture large-run artifacts beside the report: command log, extraction JSON, review JSON when produced, generated report path, and elapsed time. Always include generated prompt/log artifacts as sensitive local artifacts even when the extract shows only `output` boundaries, and keep adjacent surfaces distinct — for example, hook prompt generation and manual agent execution are separate items, not one merged risk.

8. **Compare against the security model.** Add the coverage matrix — one row per documented high-risk area with the extract/scan evidence and an assessment: confirmed, refined (the evidence narrows or splits the stated risk), or uncovered (no documented risk matches the surface).

9. **Hand off, do not overclaim.** Close the report with follow-ups: suspicious paths queued for deeper security review, unknown surface from data-flow gaps, and unsupported-source coverage notices. State explicitly that no vulnerability is claimed or excluded unless one was actually validated. Report findings to the user; do not commit, publish, or file the report anywhere without being asked.

## Context budget

The single extract JSON payload is the primary evidence — query it rather than re-running extract per question. Reserve targeted source reads for security-model rows, flows with write/delete/process/environment boundaries, network/listener evidence, or truncation gaps. Use `rg` patterns from [reference.md](reference.md) for the sink scan instead of reading whole trees, and record skipped dependency/vendor/build-output paths as excluded remainder. Do not run `sync`, `bootstrap`, or wiki mutation in this workflow — the attack-surface pass is read-only by contract, and wiki maintenance belongs to the wiki-sync and wiki-bootstrap skills.
