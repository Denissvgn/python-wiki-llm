# attack-surface reference

Supporting detail for [SKILL.md](SKILL.md). 

## Live extract schema contract

The attack-surface workflow consumes the current `llm-wiki-extract/v1` payload. Treat these fields as required contract terms:

- `entrypoints`: the extracted entrypoint queue. If it is empty, report that the workflow found no first-class entrypoints and continue with source and infrastructure evidence instead of claiming no attack surface exists.
- `data_flows[].boundaries`: boundary effects reached by each flow, such as `filesystem_write`, `process`, `environment_read`, `mutation`, and `output`.
- `data_flows[].gaps`: unresolved, external, step-limit, or truncation gaps. Each gap is unknown surface and should be counted in the report.
- `data_flows[].truncated`: a boolean or truncation marker that means the flow was shortened. Treat it as a review-priority signal even when boundaries look low impact.

If a payload is missing one of these fields, record the missing field in the run summary and fall back to source evidence for the affected row. Do not adapt the workflow to older names.

## Security-model discovery

Find the authoritative security model in this order:

1. root `SECURITY.md`
2. root `security-policy.json`
3. `docs/security/**`
4. security ADRs
5. security scanner workflows
6. explicit user selection when multiple plausible authoritative models remain

If none exist, state "security model not found" in the report and derive the coverage worklist from entrypoints, infrastructure, and sink evidence.

## Entry-point categories and trust boundaries

Group every extracted entry point into one of these rows and say who can reach it. A surface without a stated trust boundary is an incomplete row.

| Category | Typical members | Trust boundary |
|---|---|---|
| `cli` | Top-level commands | Local user input: arguments, paths, environment, current repo state. |
| `api` | Public Python API functions and exported exceptions | In-process callers; inputs arrive unvalidated by any CLI parsing layer. |
| `mcp` | MCP tools/resources | Local agent clients over the MCP transport; treat tool arguments as untrusted agent-controlled input. |
| `process` | Console-script entry points | Anything that can spawn the process: shells, hooks, CI. |
| hooks | Managed git hooks | Repo contributors — every commit triggers the hook path. |
| plugins | Plugin install and component loading | Local code-loading boundary; installed plugin files execute in-process. |

## Boundary effects and data-flow gaps

Boundary-effect kinds reported in `data_flows` summaries:

| Kind | Read it as |
|---|---|
| `filesystem_write` | File create/copy/delete reachable from the entry point. |
| `process` | Subprocess execution reachable from the entry point. |
| `environment_read` | Environment variables influence behavior. |
| `mutation` | Shared in-memory or persisted state changes. |
| `output` | Data leaves through stdout/stderr/returned values — the lowest-signal kind; almost every flow has it. |

Gap kinds, all of which are **unknown surface**, never evidence of safety:

| Kind | Meaning |
|---|---|
| `unresolved_call` | Call target could not be resolved; the sink behind it is invisible. |
| `external_call` | Call crosses into a dependency the walk does not enter. |
| `step_limit` | The walk stopped at its step budget before exhausting the flow. |
| `truncated_flow` | The flow summary itself was cut off. |

Rule from the dogfood run: a flow whose summary shows only `output` boundaries but contains `step_limit` or `truncated_flow` gaps must not be reported as side-effect-free. In the dogfood repository, 46 of 49 flows had gaps and the highest-value subprocess sink (`trigger-agent`) was invisible to the bounded walk. Promote source-level evidence over flow output whenever the two disagree.

## Source-level sink scan

Exclude docs, tests, generated coverage, caches, and dependency/vendor/build-output directories unless the security model names them. For large monorepos, rank source reads before opening files:

1. security-model named files and surfaces
2. entrypoints with `process`, `filesystem_write`, `network`, or
   `environment_read` boundaries
3. truncated flows
4. high-centrality HTTP routes
5. long tail recorded as explicit remainder

Run this scan for every entrypoint with truncation/step-limit gaps and for support code the security model names. Patterns for Python targets (adapt per language; the point is the sink families, not the exact regex):

| Sink family | `rg` starting pattern |
|---|---|
| Subprocess / shell execution | `subprocess\.|os\.system|os\.exec|Popen` |
| Filesystem write / delete | `\.write_text|\.write_bytes|shutil\.(copy|move|rmtree)|os\.(remove|unlink|rename)|\.mkdir|open\([^)]*["'][wax]` |
| Environment read / write | `os\.environ|getenv|putenv` |
| Network binds / listeners | `socket\.|\.bind\(|\.listen\(|HTTPServer|serve` |
| Dynamic import / code loading | `importlib|__import__|exec\(|eval\(|spec_from_file_location` |

For each hit inside reachable code, record the file path and line range, then record the controls found next to it — allowlists, fixed argument lists (no shell strings), timeouts, cwd-scoped path validation, locks, circuit breakers, private file modes. A sink with named controls is an assessed surface; a sink without them is a finding for the deeper review.

## Exposure-report artifact format

Default path: `reports/attack_surface_<YYYY-MM-DD>.md`. The artifact is agent-owned Markdown; keep it stable and updatable by hand. Required sections: run summary (commands, schema version, counts), prioritized exposure inventory, security-model coverage matrix, and follow-ups.

For large runs, capture and name the companion artifacts in the run summary: command log, extraction JSON, review JSON if a review command is used, generated report path, and elapsed time. These names make reruns comparable without rereading long console output.

Each exposure item uses a stable sequential `AS-NNN` ID:

```markdown
### AS-001: Manual CLI agent execution

- Extracted flow: `cli-trigger-agent`
- Source path: `src/llm_wiki_cli/commands/trigger_cmd.py`
- Extract result: output boundary only, with unresolved/truncated flow gaps.
- Source evidence:
  - Executes the selected agent with `subprocess.run` and a timeout at lines 259-272.
- Existing controls:
  - CLI-agent allowlist; lock and circuit breaker; prompt byte guard.
- Security-model alignment: matches "Headless agent execution from post-commit hooks".
- Conclusion: highest-value manual review surface; the bounded flow walk underreports the subprocess sink, so source evidence is authoritative.
```

Required fields for every item: extracted flow (or "not surfaced" with the reason), source path(s), extract result including gaps, source evidence with line ranges, existing controls, security-model alignment, and a conclusion that says what a deeper review should do with the item.

Two classification rules are mandatory:

- **Prompt/log artifacts are always sensitive.** Generated prompt files and background logs built from diffs and source inventory go in the report as sensitive local artifacts even when the extract shows only `output` boundaries.
- **Adjacent surfaces stay distinct.** Do not merge surfaces that share a feature but differ in effect — for example, a hook that only generates a prompt file versus a manual command that executes an agent subprocess. Merging them overstates one path and understates the other.

## Security-model coverage matrix

One row per high-risk area named in `SECURITY.md` (or equivalent):

```markdown
| Documented high-risk area | Extract/scan evidence | Assessment |
|---|---|---|
| Subprocess execution for extractors | Helper preparation exercised; fixed-argv `subprocess.run` with timeouts at <paths>. | Confirmed; extract underreports internal helper subprocesses. |
```

Assessment values: **confirmed** (evidence matches the stated risk), **refined** (evidence narrows or splits it — record the refinement), **uncovered** (a surface with no matching documented risk — a documentation finding in itself). A named area with no row means the run is incomplete, not that the area is safe.

## Validation expectations

A successful run has:

- Helpers prepared (or unsupported sources recorded as coverage notices). 
- `extract --deep --read-only` completed with the payload saved and its counts cited in the report.
- Source-adapter runs used `llm-wiki prepare-extractors --src-dir <repo> --allow-external-src` before extraction, and used `llm-wiki team check --src-dir <repo> --allow-external-src --wiki-dir docs/llm_wiki` only when a guarded copied/project wiki exists.
- Every security-model high-risk area covered by a matrix row.
- Every exposure item carrying source evidence with line ranges, not only extracted flow names.
- All data-flow gap counts reported as unknown surface.
- A sink scan performed for every truncated/step-limited entry point.
- An explicit closing statement that no vulnerability is claimed or excluded unless one was actually validated in this run.
- No writes to the target tree other than the report and the explicit `--output` payload.

## Failure modes and edge cases

- **Missing helpers.** Deep extract fails closed. Prepare helpers through the CLI; do not drop `--deep` to make the run pass, because the shallow payload has no data flows.
- **Read-only cache locations.** Sandboxes may mount `.git/` or the default cache read-only. Select a writable `--helper-cache-dir`/ `--cache-dir` and keep it consistent between prepare and extract.
- **No SECURITY.md.** Derive the worklist from entry-point groups, and report the missing security model as a documentation finding.
- **Gap-dominated payloads.** When most flows have gaps (the common case), the extract is a review queue, not a verdict. Budget the sink scan toward the highest-value entry points instead of chasing every gap.
- **Large monorepos.** Do not attempt full coverage. Cover the security model rows and the highest-value entry-point groups, then record the remainder explicitly as unassessed surface.
- **MCP/plugin surfaces.** Both are easy to underreport as "local files". Group them as API/tool and code-loading boundaries with their own rows.
- **Temptation to validate findings.** Proof-of-concept exploitation, fuzzing, or attacking the code is out of scope. Suspicious paths are handed to a deeper, explicitly authorized security review.

## Related workflows

- Wiki creation and refresh belong to the wiki-bootstrap and wiki-sync skills; this workflow never mutates the wiki.
- Dependency-hygiene warnings surfaced along the way belong to the dep-audit workflow.
- Fixing or hardening anything the report surfaces is follow-up work the user directs — this skill's deliverable is the exposure report.
