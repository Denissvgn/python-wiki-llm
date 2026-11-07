# Maintaining a sibling wiki

Use `llm-wiki docs impact` to find public topics that need review when their
architecture evidence changes. The command compares local snapshots and a
consumer-owned mapping. It produces JSON and Markdown reports for maintainers
and CI. Public pages can stay manually edited on GitHub.

Add [CLI reference dependencies](cli-reference-data.md) when a public topic
describes commands or options. The provider captures versioned declarations
from the selected library or a saved application contract, alongside native
architecture evidence in the same review workflow.

Use [GitHub wiki candidates](sibling-wiki-candidates.md) to render explicitly
repository-authored public pages, preserve manual content and review the exact
proposed tree before any separate delivery process.

## Configure a project

Create `.llm-wiki/publication.json` in the consumer project. Paths are relative
to that project, with architecture page paths relative to `architecture.root`.
Give each topic a stable ID, an owner and its public destination. A topic can
depend on several native pages or source files. Several topics can use the same
evidence.

For a new source-only project, select `architecture.baseline: bootstrap-source`
and set `architecture.root` to its source directory, or `.` for the consumer
root. The command builds evidence in temporary storage using the existing
source selection. Prepare any required language helpers before running it.
The [runnable consumer example](../examples/sibling-wiki/README.md) includes a
complete configuration and public page.

```json
{
  "schema_version": "llm-wiki-publication/v1",
  "source_policy": "default-branch",
  "architecture": {"baseline": "existing-wiki", "root": "docs/llm_wiki"},
  "target": {"kind": "github-wiki", "repository": "self"},
  "enforcement": "advisory",
  "publish": false,
  "topics": [{
    "id": "accounts.overview",
    "owner": "account-maintainers",
    "wiki_page": "Accounts.md",
    "edit_at": "wiki",
    "depends_on": [{"architecture_page": "modules/accounts.md"}]
  }],
  "exclusions": [
    {"pattern": "index.md", "reason": "Native navigation is maintained locally"},
    {"pattern": "log.md", "reason": "Operational native history stays local"}
  ]
}
```

Replace the example module with a page in your native wiki. An optional `anchor`
selects a unique plain ATX heading in the public page. Whole-page mappings also
work for legacy Markdown. Native section dependencies use a native `section`
locator and optionally `facets: ["semantic"]` or `["structural"]`. Find native
section locators through `list_concept_sections`. The public anchor and native
locator have separate formats. Without a section selection, the dependency
covers the whole native page and its captured source basis.

Native `#section/@preamble` dependencies cover text before the first heading.
Public section anchors support unique plain headings and inline code labels.
For headings containing links, emphasis or HTML, map the whole public page.

Use `{"source_file": "config/accounts.toml"}` for a value owned by configuration
or another input outside native page coverage. For repository-authored public
content, set `edit_at` to `repository` and provide its `source_document` path.
The report identifies its edit location. Keep titles, page filenames and local
links portable across operating systems.

Use narrow, reasoned exclusions for internal material. Every remaining native
page without a mapping appears as an uncovered topic candidate. A glob excludes
future matches too, so its stated scope should describe that intent. Review
mapping and exclusion changes alongside the source change.

## Inspect impact

Keep a local checkout or pinned copy of the public wiki under the consumer
project, such as `sibling-wiki/`. It can be excluded from the consumer's Git
tracking. Populate or refresh the native wiki through its owning workflow
before reading impact. Native capture validates committed page and storage
consistency and discloses that live source freshness requires native integrity
validation.

```bash
.venv/bin/llm-wiki docs impact --target-dir sibling-wiki --output reports/wiki-impact.json --format markdown
```

The first assessment highlights the configured topics and unmapped native
pages. Open the public topic and inspect each contributing dependency. Add
missing bindings or scope exclusions, then rerun the report. A retired mapping
still reaches its former public readers when compared against the previous
accepted basis.

An accepted basis is a durable checkpoint chosen by the project's maintainers.
Capture it only after reviewing the initial mapping and public content.

```bash
.venv/bin/llm-wiki docs impact snapshot --target-dir sibling-wiki --output .llm-wiki/publication-baseline.json
.venv/bin/llm-wiki docs impact --target-dir sibling-wiki --baseline .llm-wiki/publication-baseline.json --output reports/wiki-impact.json
```

Commit accepted configuration, baselines and review records through the
consumer's normal review process. Keep generated reports in ignored storage
or CI artifacts. PR runs propose changes without advancing shared checkpoints.
An omitted local target copy still allows evidence comparison. The report
retains target verification as pending and cannot establish a ready review.

Replacing an existing checkpoint requires `snapshot --replace` after review.
Evidence inputs and outputs resolve relative to `--consumer-root`, which
defaults to the current directory. Explicit absolute artifact paths are also
accepted. Keep checkpoint replacement separate from routine report generation.

## Resolve a finding

Edit manual topics in the sibling wiki. Edit repository-authored topics in their
declared source document. Rerun against the updated local public copy and source
inputs. When a public section remains accurate, prepare an exact-basis review
decision with the topic finding ID from the JSON report.

```bash
.venv/bin/llm-wiki docs impact resolve --target-dir sibling-wiki --baseline .llm-wiki/publication-baseline.json --report reports/wiki-impact.json --finding <finding-id> --decision still-current --reviewer alice --reason "The public contract remains accurate" --output .llm-wiki/publication-reviews.proposed.json
```

Include `--reviews` when adding to an existing accepted ledger. The command
verifies current inputs and target text against the saved report and produces
a proposal. Submit it for the owner's review. After acceptance, keep the ledger
at the chosen accepted path and supply it on subsequent comparisons.

```bash
.venv/bin/llm-wiki docs impact --target-dir sibling-wiki --baseline .llm-wiki/publication-baseline.json --reviews .llm-wiki/publication-reviews.json --output reports/wiki-impact.json
```

An accepted decision clears the matching finding while its evidence and target
text remain the same. A later relevant change reopens review. Missing evidence
or a missing public page must be repaired before accepting a no-edit decision.

When removing a mapping or moving its destination, the report retains the
former destination as a separate obligation. Use `--decision retired` to record
an explicit retirement after checking the previous page and its current state.
This can confirm a deleted page or removed heading. The decision remains bound
to any former evidence that still exists and to the observed target bytes or
absence. Changes reopen review until a new accepted checkpoint is established.
Maintain the previous baseline while any required findings remain unresolved.
Review-ledger authority comes from the consumer's repository process. Local
reviewer text alone does not authenticate a GitHub identity.

## Run in CI

Use the [wiki impact action](../integrations/wiki-impact/README.md) with a pinned
provider revision. Supply the consumer configuration, accepted baseline and
local public checkout. Provide review ledgers from the accepted source line.
Native validation should precede impact when using an existing native wiki.

Choose `enforcement: advisory` for reporting or `required` for the review gate.
Complete advisory reports exit 0 even when findings remain. Required unresolved
reviews exit 1. Invalid or incomplete evidence exits 2. The action can strengthen
advisory findings with `fail-on: review-required`.

This workflow records edit responsibility with `publish: false`. The action
saves reports and verified provider identity as artifacts. Keep accepted review
state in durable consumer storage so it remains available after artifact expiry.

## Python integration

```python
from llm_wiki_cli.api import (
    capture_publication_basis,
    compare_publication_impact,
    resolve_publication_finding,
)

candidate = capture_publication_basis(".", target_dir="sibling-wiki")
report = compare_publication_impact(candidate)
```

Supply `baseline` and `reviews` as decoded, accepted JSON documents when
available. `resolve_publication_finding` returns a proposed ledger for the same
review workflow. These functions perform no remote Git operations.
