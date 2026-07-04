# dep-vuln-triage reference

Supporting detail for [SKILL.md](SKILL.md).

## Input contract: the deep extract dependency block

`llm-wiki extract --deep --read-only` writes the `llm-wiki-extract/v1` payload with a `dependencies.external.<language>` mapping per detected language:

```json
{
  "dependencies": {
    "external": {
      "python": {
        "used": {"requests": ["app.py"]},
        "undeclared": [],
        "unused": ["flask"],
        "versions": {
          "flask": {"resolved_from": "poetry.lock", "version": "3.0.1"},
          "requests": {"resolved_from": "poetry.lock", "version": "2.31.0"}
        }
      }
    }
  }
}
```

- `used` maps package → importing files; it is the reachability seed.
- `versions` is additive and fail-open: entries exist only when a lockfile resolved the package. Missing or malformed lockfiles produce silent absence of version metadata, never an error.
- `versions.<package>.resolved_from` names the lockfile so the report can cite it.

Lockfile sources captured per language:

| Language | `resolved_from` values |
|---|---|
| python | `poetry.lock`, pinned `requirements*.txt` (`==` pins only) |
| typescript | `package-lock.json`, `pnpm-lock.yaml` |
| go | `go.sum` |
| rust | `Cargo.lock` |
| haskell | none — Cabal `build-depends` versions are not captured |

Haskell packages are therefore **always unknown-version**: triage them from the manifest range, mark the resolved version as unknown, and say so in the report. The same applies to Python packages declared only with ranges and to any ecosystem where the repo has no lockfile.

## Advisory lookup

Map extract language keys to advisory ecosystems:

| Extract language | OSV ecosystem |
|---|---|
| python | `PyPI` |
| typescript | `npm` |
| go | `Go` |
| rust | `crates.io` |
| haskell | `Hackage` |

Query with the resolved version when one exists. For unknown-version packages, query by package name, report all potentially-affected advisories, and mark the rows `unknown-version` — do not pick an optimistic version from a range to make advisories disappear. Record the advisory source (OSV, GitHub advisories) and the lookup date in the report header; advisory data is a moving target and the report must be datable.

## Reachability classes

Ordered strongest to weakest evidence of exposure:

| Class | Evidence | Interpretation |
|---|---|---|
| reachable-from-entrypoint | Importing file appears in an entrypoint flow (`data_flows`) or `callers`/`dependency_neighborhood` connects it to one | Treat as live exposure; read the import sites. |
| test-only (not production-reachable) | Importing files are traced, but every hit is on a test path | Note the CVE class but do not treat it as production exposure. |
| imported-not-traced | Package in `used` but no extracted flow reaches the import site | Unknown, not unreachable — bounded flow walks underreport by design. |
| declared-only | Package in `unused` | Not imported by analyzed source; still triage (build tools and plugins execute too), then route removal proposals through `dep-audit`. |
| unknown | Undeclared imports, unknown-version packages, gap-heavy flows | Report explicitly in the unknowns section. |

Data-flow `gaps` values (`unresolved_call`, `external_call`, `step_limit`, `truncated_flow`) weaken reachability evidence; a package "not reachable" only because the flow truncated is `imported-not-traced`, never safe.

**Test-path exclusion is mandatory, not optional.** Computing reachability by intersecting a package's importing files against the set of all `data_flows[].steps[].file` values will flag test-only dependencies (test runners, fixture/mocking libraries) as "reachable" whenever the extracted flow graph happens to trace through `tests/test_*.py` files — the extractor does not distinguish a production HTTP handler from a test-shaped entrypoint.
Confirmed on a real monorepo: a naive intersection classified `pytest` (1066 importing files) as `reachable-from-entrypoint` purely because 219 of its importers were traced test files. Exclude paths matching `/test`, `tests/`, or a `test_`/`test` prefix from the "reachable" bucket before drawing a conclusion; route them to `test-only (not production-reachable)` instead.

**Zero import evidence requires a spot-check before `declared-only`.**
Dependency reconciliation matches on the *declared package name*, but a package's *import name* can differ — `pyjwt` imports as `jwt`, `python-multipart` imports as `multipart`, `pyyaml` imports as `yaml`, `pillow` imports as `PIL`, `beautifulsoup4` imports as `bs4`, `scikit-learn` imports as `sklearn`, `opencv-python` imports as `cv2`, `protobuf` imports as `google.protobuf`. A package with zero entries in `used` can still be genuinely and heavily imported under its real module name. Confirmed on a real monorepo: `pyjwt` showed 0 importing files in the extract and was about to be reported `declared-only` for a live SSRF/token- forgery advisory; a source grep for `import jwt` found 45 importers, including a production authentication-flow file. Before accepting `declared-only` for any package with a known name/import mismatch — or any package whose advisory hit looks high-value enough to matter — grep the source for the actual import name once. This is a single targeted read, not a full-repo scan.

## Triage statuses

| Status | Meaning | Typical action |
|---|---|---|
| bump now | Fixed version exists and is compatible | Edit manifest, regenerate lockfile via the package manager, re-verify. |
| bump blocked | Fixed version conflicts with peers or needs migration | Record blocker + mitigation; file follow-up. |
| mitigate | No fix released or bump impossible now | Document the compensating control next to the evidence. |
| remove | `declared-only` and evidence shows it is genuinely dead | Propose removal via the `dep-audit` contract — no manifest edits without source evidence. |
| defer | Severity × reachability too low for this budget | Record rationale and the row stays in the report. |
| needs human confirmation | Policy-sensitive or ambiguous evidence | Record the exact question and stop before edits. |

## Report format

`reports/dep_vuln_triage_<YYYY-MM-DD>.md`, resumable rows:

```markdown
| ID | Package (lang) | Version (source) | Advisory | Severity | Reachability | Status | Evidence | Action |
|---|---|---|---|---|---|---|---|---|
| DVT-001 | requests (python) | 2.31.0 (poetry.lock) | GHSA-xxxx / CVE-yyyy | high | reachable-from-entrypoint | bump now | app.py imports requests; flow api_handler → fetch | bump to 2.32.4 |
```

Required sections beyond the table:

1. inventory counts per language (used / unused / undeclared / with-version / unknown-version);
2. advisory source and lookup date, and the list of packages checked clean;
3. unknowns: unknown-version packages, undeclared imports, gap-limited reachability calls;
4. verification commands run and their results;
5. follow-ups and hand-offs (deeper security review, `dep-audit` items).

## Edge cases

- **Monorepos with scoped manifests**: `used` paths tell you which service/package imports the hit; triage per owning scope, not per repo.
- **Multiple lockfiles resolving the same package**: version capture keeps the highest version. Say so when the repo may run older duplicates.
- **Indirect/transitive dependencies**: reconciliation tracks direct declarations and imports. Advisories on transitive packages surface only via lockfile entries; check the lockfile-backed `versions` mapping, and state that transitive reachability is out of scope for the flow evidence.
- **Vendored code**: dependency reconciliation does not cover vendored trees; note vendored directories as uncovered surface.
- **No network**: stop after the inventory and unknowns sections; a triage report without advisory data must say it contains no advisory conclusions.

## Scope guardrails

- Defensive locate-and-mitigate only: no exploit development, no proof-of-concept payloads, no testing of live systems.
- Never hand-edit lockfiles; manifests change first, the package manager regenerates the lock.
- The default deliverable is the report; apply manifest edits only when the user asked for fixes.
