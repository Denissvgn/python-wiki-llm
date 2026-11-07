# Sibling wiki impact example

The consumer configuration maps the account module and its source file to a
manually maintained public overview. Source-only mode builds native evidence
in temporary storage. The public copy remains available for exact review.

From the repository root, use its installed provider and this consumer root.

```bash
.venv/bin/llm-wiki docs impact --consumer-root examples/sibling-wiki --target-dir sibling-wiki --output reports/sibling-impact.json --format markdown
```

The initial report flags `accounts.overview` for review. Its internal navigation
and implementation pages have explicit exclusions in the configuration. Find
the topic finding ID in the JSON report and record why the overview is accurate.

```bash
.venv/bin/llm-wiki docs impact resolve --consumer-root examples/sibling-wiki --target-dir sibling-wiki --report reports/sibling-impact.json --finding <finding-id> --decision still-current --reviewer alice --reason "The overview describes the current account" --output reports/sibling-reviews.proposed.json
```

After the owner's acceptance, supply the ledger through `--reviews`. Changing
the module or public overview reopens the affected review. Follow the
[consumer guide](../../docs/sibling-wiki.md) to capture an accepted baseline and
install the read-only CI action in another project.
