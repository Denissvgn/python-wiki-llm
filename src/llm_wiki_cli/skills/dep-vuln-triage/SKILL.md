---
name: dep-vuln-triage
description: Triage vulnerable-dependency exposure with LLM Wiki — run `llm-wiki extract --deep --read-only`, build a per-language dependency inventory with lockfile-resolved versions, look up security advisories per package, rank hits by import-site reachability, and write a severity-times-reachability triage report with proposed version bumps or mitigations. Use for a defensive review of dependencies in a repository you maintain; packages without resolved versions are unknowns to report, never safe paths.
---

# dep-vuln-triage

Answer the question dependency scanners cannot: *is the vulnerable code path reachable from our usage?* The loop is: **prepare helpers → deep read-only extract → dependency inventory with versions → advisory lookup → reachability triage → severity × reachability table → smallest safe action → verify → report**. This skill extends the `dep-audit` triage contract with advisory data and reachability ranking; it locates and assesses exposure, proposes mitigations, and hands exploitability questions to deeper security review. It never attempts exploitation. See [reference.md](reference.md) for the extract payload shapes, ecosystem mapping, triage statuses, report format, and edge cases.

## Preconditions

- This is a defensive review of a repository the user owns, maintains, or is authorized to assess.
- Advisory lookup needs either network access (OSV, GitHub advisories) or a user-provided offline advisory dataset. If neither exists, stop after the inventory step and report the boundary instead of guessing.
- Helper toolchains for the repo's languages are available or overridden (`LLM_WIKI_GO`, `LLM_WIKI_GHC`); deep extract fails closed on missing helpers.
- If `--src-dir` points outside the current working directory, pass `--allow-external-src` consistently to every source-reading command, including `prepare-extractors --src-dir <repo> --allow-external-src` and `team check --src-dir <repo> --allow-external-src` when team policy is checked. Keep report and output paths under the current project.

## Steps

1. **Prepare helpers and run the deep read-only extract.**

   ```bash
   llm-wiki prepare-extractors --src-dir .
   llm-wiki extract --src-dir . --deep --read-only \
     --output /tmp/dep-vuln-extract.json
   ```

   Save the extraction JSON; it is the primary evidence and the reachability source for the whole run.

2. **Build the dependency inventory.** For each language under `dependencies.external.<language>`, collect:

   - `used` — package → importing files (the reachability seed);
   - `unused` — declared but not imported;
   - `undeclared` — imported but not declared;
   - `versions` — package → `{version, resolved_from}` captured from lockfiles.

   Version capture is additive and fail-open: a used or declared package with **no `versions` record is an unknown-version package**. List it in the report's unknowns section exactly like `attack-surface` reports data-flow gaps — unknown surface, never evidence of safety. Read the manifest yourself only to record the declared range next to the missing resolved version; do not substitute a range for a resolved version in advisory queries without saying so.

3. **Look up advisories per package.** Query OSV (or GitHub advisories) with the ecosystem-mapped package name and the resolved version from `versions`. Record for every hit: advisory ID, severity, affected range, fixed version, and the lookup date. Record clean results too — the report must show which packages were checked, not only which matched.

4. **Rank hits by reachability.** For each package with an advisory hit, classify using extract evidence before reading any source:

   - **reachable-from-entrypoint** — an importing file from `used` appears in an entrypoint's flow (`data_flows`), or graph queries (`callers`, `dependency_neighborhood`) connect it to one;
   - **test-only (not production-reachable)** — importing files are traced, but every hit is on a test path; exclude test paths from the reachable bucket before classifying, or a large test suite will manufacture false "reachable" CVEs for test-only dependencies;
   - **imported-not-traced** — imported somewhere, but no extracted flow reaches the import site (data-flow gaps count as *unknown*, not unreachable);
   - **declared-only** — in `unused` with zero importing files: before accepting this, grep the source for the package's actual *import* name, which can differ from its *declared* name (`pyjwt`→`jwt`, `python-multipart`→`multipart`, `pyyaml`→`yaml`, and others in [reference.md](reference.md)) — zero matches under the declared name is not proof of zero usage;
   - **unknown** — undeclared imports, unknown-version packages, or gap-heavy flows.

   Then read the importing files for the top-ranked hits to confirm which APIs of the package are actually called, and whether they match the advisory's affected functions when the advisory names them.

5. **Build the severity × reachability table.** One `DVT-NNN` row per package/advisory pair, ordered by severity and reachability class, using the format in [reference.md](reference.md).

6. **Choose the smallest safe action per row.** Version bump when the fixed version is compatible (edit the manifest, then regenerate the lockfile with the package manager — never hand-edit lockfiles); mitigation note when a bump is blocked; removal proposal for `declared-only` hits (route through the `dep-audit` no-manifest-edits-without-source-evidence rule); explicit deferral with rationale otherwise. Do not apply source or manifest edits the user did not ask for — default output is the triage report.

7. **Verify.** If manifests changed, re-run the extract or `llm-wiki lint --strict` / `llm-wiki ci-check` so dependency reconciliation confirms the new state; cite the passing command in the report.

8. **Report and hand off.** Write `reports/dep_vuln_triage_<YYYY-MM-DD>.md`: inventory counts per language, the triage table, the unknown-version and unresolved-import sections, the advisory source and lookup date, and follow-ups. Hand paths needing exploitability analysis to deeper security review (`attack-surfa ce` output, then `/security-review`); state explicitly that no vulnerability is claimed or excluded unless validated.

## Context budget

Query the saved extract JSON instead of re-running extract per package. Read source only for top-ranked advisory hits (the importing files from `used`), not for the whole dependency list. Advisory lookups are per unique package+version, batched where the API allows. On monorepos, triage by severity class first and record the long tail as explicit remainder rather than exhausting the session on low-severity hits.
