# Sibling wiki candidate example

This source-only consumer keeps public Markdown in `docs/`. Its configuration
maps the account module to an authored overview, Home page and sidebar, and
maps a downloadable text asset. `Accounts.md` is explicitly adopted from the
pinned local wiki copy. The manually edited `Wiki-Tooling.md` remains unchanged
and keeps an opt-in dependency on the installed `llm-wiki sync` reference.

Use the repository's installed provider with its `publication` extra. From the
repository root, prepare a fresh local candidate:

```bash
.venv/bin/llm-wiki docs wiki export --consumer-root examples/sibling-wiki --target-dir sibling-wiki --output-dir reports/wiki-candidate --receipt reports/wiki-candidate.json
.venv/bin/llm-wiki docs wiki check --consumer-root examples/sibling-wiki --target-dir sibling-wiki --candidate-dir reports/wiki-candidate --receipt reports/wiki-candidate.json
```

Source-only mode builds native evidence in temporary storage. The example's
local public copy is preserved. Inspect the candidate and the receipt's
`operations`, `checks` and `impact`. The first assessment leaves topics and the
complete candidate pending review; it does not establish remote delivery.

Create topic decisions against the proposed public text:

```bash
.venv/bin/llm-wiki docs impact --consumer-root examples/sibling-wiki --target-dir reports/wiki-candidate --output reports/candidate-impact.json
.venv/bin/llm-wiki docs impact resolve --consumer-root examples/sibling-wiki --target-dir reports/wiki-candidate --report reports/candidate-impact.json --finding <finding-id> --decision still-current --reviewer alice --reason "The proposed topic matches the current account" --output .llm-wiki/publication-reviews.proposed.json
.venv/bin/llm-wiki docs wiki review --consumer-root examples/sibling-wiki --candidate-dir reports/wiki-candidate --receipt reports/wiki-candidate.json --reviewer alice --reason "Reviewed the pages, navigation, asset and adoption" --output .llm-wiki/candidate-review.proposed.json
```

Resolve every topic, supplying `--reviews` to extend the proposed ledger. Submit
the records with the authored content and mapping through the project's review
process. After acceptance, supply the accepted paths:

```bash
.venv/bin/llm-wiki docs wiki check --consumer-root examples/sibling-wiki --target-dir sibling-wiki --candidate-dir reports/wiki-candidate --receipt reports/wiki-candidate.json --reviews .llm-wiki/publication-reviews.json --candidate-review .llm-wiki/candidate-review.json --output reports/wiki-candidate.checked.json --require-ready
```

Use a fresh candidate directory after source or mapping changes. The adoption
hash must continue to match the pinned target bytes. Follow the
[candidate guide](../../docs/sibling-wiki-candidates.md) for accepted baselines,
previous ownership receipts, removals and application reference freshness.
All output remains local and publication is disabled.
