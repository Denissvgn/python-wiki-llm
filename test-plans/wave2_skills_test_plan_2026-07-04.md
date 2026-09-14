# Test Plan: impact-analysis, infra-review, publish-docs

Date: 2026-07-04

Scope: the three wave-2 skills implemented and committed on 2026-07-04 (`5f0019a feat: bundle doc-hub, impact-analysis, infra-review, publish-docs skills`) but not yet dogfooded against a real project. Unlike `dep-vuln-triage` and `onboarding-guide` (both already run end-to-end, both already found real bugs — see [`entrypoint_root_propagation_bugfix_2026-07-04.md`](../reports/entrypoint_root_propagation_bugfix_2026-07-04.md)), these three are currently spec-verified only: their skill text quotes live field names and CLI flags I confirmed by reading source, but no agent has actually followed the SKILL.md steps against a real repository yet. This plan exists to close that gap and should produce dogfood reports in the same style as the existing two once executed.

## Why a plan before execution

Both prior dogfoods changed the skill text and fixed real product code after running, not before. The expectation for this plan is the same: at least one of these three scenarios should surface something the spec-only pass missed. Executing this plan and finding nothing wrong is a valid outcome, but it should be treated as a weaker signal than it looks — verify each "pass" against the concrete expected finding listed per scenario, not just against "the command didn't error."

## Available targets (reuse before regenerating)

| Target | Path | Status as of 2026-07-04 |
|---|---|---|
| TeamCrush bootstrapped wiki | `/tmp/llm-wiki-skills-p1p2-20260704-5v8Tq5/teamcrush/wiki-external` | 539 pages, current as of commit `e05bff1` |
| Traid Platform bootstrapped wiki | `/tmp/llm-wiki-skills-p1p2-20260704-5v8Tq5/traid/wiki-external` | 10,980 pages, current as of the state described in `p1_p2_skill_gap_closure_confirmation_2026-07-04.md` |
| Prepared helper cache (Go+Haskell) | `/tmp/llm-wiki-p1p2-confirm-XTnFgk/helpers` | Prepared with `LLM_WIKI_GO=/usr/local/go/bin/go`, `LLM_WIKI_GHC=/home/mike/.ghcup/bin/ghc` |
| TeamCrush source | `/mnt/data/projects/project_team_crush` | Read-only; use `--allow-external-src` |
| Traid Platform source | `/mnt/data/projects/traid-platform` | Read-only; use `--allow-external-src`; has an unrelated dirty working tree from other work — do not touch |

These `/tmp` paths may not survive a machine restart or `/tmp` cleanup. If missing, regenerate with the `wiki-bootstrap` skill exactly as documented in `skills_p1_p2_real_project_run_2026-07-04.md` before starting this plan — do not substitute a synthetic fixture for the real thing, since the whole point of this plan is to exercise the skills against real, messy data.

Environment facts confirmed for this plan (re-check if the runner differs): `mkdocs` 1.6.1 and `npm`/`npx` 11.11.1 are both installed, so `publish-docs` scenarios can exercise the real-builder path, not just the not-installed path.

## Skill 1: `impact-analysis`

### Scenario IA-1: Symbol query, found, single match

Target: TeamCrush, symbol `check_health` (used by the `http-health` flow, confirmed present in `rlm-gateway/server.py` during the onboarding-guide dogfood).

```bash
echo '{"protocol":"llm-wiki-context/v1","budget_tokens":16000,"filters":{"symbol":"check_health"}}' \
  | LLM_WIKI_GO=/usr/local/go/bin/go LLM_WIKI_GHC=/home/mike/.ghcup/bin/ghc \
    llm-wiki context --src-dir /mnt/data/projects/project_team_crush \
    --wiki-dir <teamcrush wiki path> --allow-external-src --request -
```

Expected: `graphs.symbol.callers.found: true`, `ambiguous: false`; `pages` lists at least the module page for `rlm-gateway/server.py`. Verify the blast-radius summary the skill produces actually names the `http-health` flow as a caller-adjacent entrypoint, not just the raw symbol list.

### Scenario IA-2: Symbol query, ambiguous

Target: Traid Platform, a common short symbol name likely to exist in multiple services (e.g., `run` or `main` — Traid's scale makes collisions likely; confirm the actual name by grepping first). Expected: `ambiguous: true` with multiple `matches`. Verify the skill's output lists every match and asks the user to disambiguate rather than silently picking the first one — this is an explicit SKILL.md requirement (step 1), and it's the kind of thing easy to get wrong under time pressure during a live run.

### Scenario IA-3: Symbol query, not found

Target: either project, a deliberately misspelled or nonexistent symbol name. Expected: `found: false`, empty `callers`/`callees`/`pages`. Verify the skill's report says "not found," not "found with zero callers" — these are different claims and the wording matters for a real blast-radius answer.

### Scenario IA-4: Truncated result on a high fan-in target

Target: Traid Platform. Use a package or module known to have very broad usage — the `dep_vuln_triage_dogfood_traid_2026-07-04.md` run already established `pytest` has 1,066 importing files and several production modules have wide fan-in; pick a real Traid symbol with a large caller set (check via `dependency_neighborhood` on a high fan-in file from that report first, then pick a symbol defined in it). Expected: `truncated: true` on the callers query. Verify the skill's report states the blast radius is partial and does not claim completeness — this is the single most safety-relevant behavior in the whole skill.

### Scenario IA-5: File-path query via `dependency_neighborhood` (MCP)

Target: TeamCrush, file `rlm-gateway/server.py` (the file with the most generated flow pages pointing at it). Requires the MCP server, not just `context --request` (the SKILL.md explicitly documents that `dependency_neighborhood` is MCP-only through this protocol — this scenario exists specifically to confirm that claim is still true and that an agent following the skill without an MCP connection correctly falls back rather than getting stuck).

```bash
# via mcp query_graph tool, query_type=dependency_neighborhood, path=rlm-gateway/server.py
```

Expected: `metrics.fan_in`/`fan_out`, `cycle_groups` (compare against `dependencies.md`'s fan-in/fan-out table from the onboarding-guide dogfood — `agent` module was 22/10; a different file here is fine, the point is the numbers must match the generated page, not just be internally consistent).

### Scenario IA-6: Entrypoint query

Target: TeamCrush, entrypoint id `http-chat_completions` (confirmed to exist as a real generated flow page). Expected: `graphs.entrypoint.flow`/`data_flow` populated; cross-reference against the actual `flows/http-chat_completions.md` page content from the earlier dogfood to confirm the query's data matches the generated page rather than diverging.

### IA pass/fail criteria

- All six scenarios return the documented envelope fields   (`found`/`ambiguous`/`matches`/`truncated`) — if any is missing, that's a contract-text bug in the skill, not just a data issue.
- The docs-to-update checklist the skill produces uses only the three `doc-review`-shared statuses (`valid documentation defect`, `stale generated content`, `needs human confirmation`) — any other status is a vocabulary-drift finding.
- IA-2 and IA-4 specifically must not be reported as clean/complete results — false confidence here is the highest-severity possible finding for this skill.

## Skill 2: `infra-review`

Traid Platform is the primary target — it is the only one of the two with real Kubernetes manifests and GitHub Actions workflows, so it's the only target that can exercise the full checklist. Use TeamCrush as the secondary target specifically to test the "coverage vs. clean" distinction (step 7 of the SKILL), since TeamCrush's infrastructure surface is Dockerfile/Compose-only.

### Scenario IR-1: Compose page-visible finding (no raw-source read needed)

Target: TeamCrush, `docker-compose.yml`, `rlm-gateway` service. Already confirmed present during this session: `Volumes: /var/run/docker.sock:/var/run/docker.sock, ...`. Expected: the skill flags this from the generated page alone (step 3), without needing a raw-source read — this is the reference.md's own worked example; confirm a live run actually produces it rather than only existing in the doc.

### Scenario IR-2: Kubernetes findings requiring a raw-source read

Target: Traid Platform, `infra/k8s/order-router/deployment.yaml`.
Confirmed by direct inspection for this plan:

- No `resources:` (limits/requests) block at all in the container spec — a genuine missing-resource-limits finding.
- `image: traid-platform-order-router:latest` — a mutable tag, the same pinning concern the SKILL.md raises for Dockerfiles, here on a K8s image reference instead.
- No `securityContext`, `hostPath`, `hostNetwork`, or `privileged` fields present in this particular manifest (a true negative — good for confirming the skill doesn't hallucinate findings that aren't there).

Expected: the skill's generated-page read alone (kind/name/containers) will not show any of this — confirm the agent actually performs the raw YAML read the SKILL.md mandates in step 4, and doesn't stop at the generated page. This is the single highest-value scenario in this plan: if an agent skips the raw-source read here, the skill's core promise is broken in the most common real case.

Also check `infra/k8s/order-router/secret.example.yaml` as a deliberate **negative** case: it uses empty-string `stringData` placeholders (`EXMO_API_KEY: ""`, etc.), not real secret values. Confirm the skill does not flag this as a plaintext-secret finding — a false positive here would undermine trust in every other finding in the report.

### Scenario IR-3: GitHub Actions missing-permissions findings

Target: Traid Platform, `.github/workflows/`. Confirmed by direct inspection (`grep -L`/`-l "permissions:" .github/workflows/*.yml`): of 22 total workflow files, exactly **17 have no `permissions:` block at all** (default token scope) and exactly **5 do** — the `*-multiarch.yml` workflows (`autotrade-service-multiarch.yml`, `data-ingest-multiarch.yml`, `inference-service-multiarch.yml`, `order-router-multiarch.yml`, `feature-service-multiarch.yml`), each scoped to `contents: read`.

Expected: the skill correctly distinguishes these two groups (missing permissions block vs. minimally-scoped) rather than treating the whole workflow directory as one bucket. The finding count should match 17/22 missing, 5/22 present — a different count either direction is a concrete, checkable signal that the raw-source-read step was not actually performed comprehensively across the workflow directory (this is an exact ground truth, not an estimate).

### Scenario IR-4: Coverage vs. clean distinction

Target: TeamCrush. It has zero Kubernetes and zero GitHub Actions files.
Expected: the report explicitly states these artifact types have no coverage in this repo (not applicable), distinct from "reviewed, found clean." A report that silently omits K8s/Actions rows entirely, or one that claims them "clean," both fail this scenario — the SKILL.md's step 7 requires stating this distinction explicitly.

### IR pass/fail criteria

- IR-2's missing-resource-limits and mutable-tag findings must actually appear in the report — these are the plan's ground-truth expected findings, independently confirmed by direct file inspection above.
- IR-2's `secret.example.yaml` must **not** appear as a plaintext-secret finding (false-positive check).
- IR-3's finding count is a real, checkable number (17/22 missing, 5/22 present) — treat a different count as a signal the raw-source-read step was skipped or only partially performed.
- IR-4 is answered explicitly, not by omission.

## Skill 3: `publish-docs`

### Scenario PD-1: Single-wiki mkdocs export → check → real build

Target: TeamCrush wiki. `mkdocs` 1.6.1 is installed in this environment, so this scenario should exercise the real builder, not just detection.

```bash
llm-wiki site export --wiki-dir <teamcrush wiki path> --out-dir /tmp/pd-test-mkdocs/site \
  --format mkdocs --front-matter --output-format json
llm-wiki site check --wiki-dir <teamcrush wiki path> --out-dir /tmp/pd-test-mkdocs/site --output-format json
mkdocs build --strict -f /tmp/pd-test-mkdocs/site/mkdocs.yml
```

Expected: export/check both `ok: true`; `mkdocs build --strict` either succeeds or fails with a real MkDocs-level error (missing plugin, etc.) — confirm the skill's guidance to "surface the real builder's error verbatim" actually produces something legible, not a swallowed/summarized error.

### Scenario PD-2: Docusaurus export without an existing app (expected non-buildable)

Target: TeamCrush wiki, `--format docusaurus`. Confirmed via `reference.md`: export only writes `sidebars.json`, not `docusaurus.config.js`/`package.json`, so a bare `npm run build` in the export output directory should fail with a missing-app error.

```bash
llm-wiki site export --wiki-dir <teamcrush wiki path> --out-dir /tmp/pd-test-docusaurus/site \
  --format docusaurus --front-matter --output-format json
cd /tmp/pd-test-docusaurus/site && npm run build   # expected to fail — no package.json here
```

Expected: this is a **negative test** — the point is confirming the skill's documented limitation ("Docusaurus needs an existing app; export alone isn't buildable") is accurate, and that the skill's failure-mode table entry for this exact case ("Docusaurus build fails with 'docs not found'") matches what actually happens rather than being a guess.

### Scenario PD-3: Builder-not-installed path (simulated)

Simulate the absent-toolchain case even though this environment has both builders installed, since a real user's environment may not:

```bash
PATH=/usr/bin:/bin llm-wiki site export --wiki-dir <teamcrush wiki path> --out-dir /tmp/pd-test-noPATH/site --format mkdocs --output-format json
command -v mkdocs || echo "mkdocs not found (expected under stripped PATH, if mkdocs isn't in /usr/bin)"
```

Adjust the stripped `PATH` to genuinely exclude wherever `mkdocs`/`npm` actually resolve from in this environment (confirm with `command -v mkdocs` `command -v npm` first, since `mkdocs` was found at `/usr/bin/mkdocs` here, which may already survive a naive strip — pick a `PATH` value that actually excludes it). Expected: the skill detects the absence and stops after `site check`, explicitly stating no build was attempted — it must not error out trying to run a missing command, and it must not silently skip mentioning that a build step was expected.

### Scenario PD-4: Deploy guardrail

No deploy target is configured for either test project. Expected: even if asked to "publish the docs," the skill hands off the deploy step and asks for confirmation before doing anything that pushes to a hosting target — confirm this by explicitly checking that a run of this skill against either test wiki does not attempt to touch any real hosting target (GitHub Pages branch, external host) without being separately, explicitly asked. This is a guardrail-presence check, not a functional check — the pass condition is "the skill asked" or "the skill didn't have a deploy target to attempt," not any generated artifact.

### PD pass/fail criteria

- PD-1's real `mkdocs build` actually runs (not just detected as   available) and its result (success or a real builder error) is   surfaced verbatim.
- PD-2 confirms the documented Docusaurus limitation is accurate — if a bare export somehow builds successfully, the reference.md's claim is wrong and needs correcting.
- PD-3 confirms fail-closed behavior with an accurate PATH strip, not a strip that happens to leave the tool reachable anyway.
- PD-4 is the only scenario in this plan whose "pass" is entirely about absence of a destructive action, not presence of a correct artifact.

## Evidence to capture per skill (mirrors the two completed dogfood reports)

For each skill, produce a report at `reports/<skill>_dogfood_<target>_<date>.md` following the structure already established by [`dep_vuln_triage_dogfood_traid_2026-07-04.md`](../reports/dep_vuln_triage_dogfood_traid_2026-07-04.md) and [`onboarding_guide_dogfood_teamcrush_2026-07-04.md`](../reports/onboarding_guide_dogfood_teamcrush_2026-07-04.md): runner path, exact commands run with exit codes, the scenario-by-scenario result against this plan's expected findings, any skill-text or product code fix applied as a result (with before/after verification the same way the entrypoint-root-propagation and sync-relink fixes were verified — a failing regression test before the fix, passing after), and full test suite + ruff confirmation if any code changed.

## Run Order

1. `infra-review` IR-2 and IR-3 first — these have the most concretely pre-verified expected findings (missing K8s resource limits, mutable tag, 17/22 vs 5/22 Actions permissions split) and the highest chance of surfacing a real gap, matching the pattern from both prior dogfoods.
2. `impact-analysis` IA-2 and IA-4 next — the ambiguity and truncation paths are the parts most likely to be wrong in a way that produces false confidence rather than an obvious error.
3. `publish-docs` last — lowest LLM judgment budget by design, most likely to just work, but PD-4's guardrail must still be explicitly confirmed rather than assumed.
