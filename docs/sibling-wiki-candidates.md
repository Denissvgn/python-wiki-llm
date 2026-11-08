# GitHub wiki candidates

Prepare a local GitHub wiki candidate from explicitly mapped public Markdown.
Its receipt binds the input basis, provider identity, target-copy hashes,
owned paths, operations, structural checks and exact review state. Generation
and checking perform no remote Git operations.

## Declare authored content

Keep the complete configuration described in the [sibling wiki guide](sibling-wiki.md).
Merge a `content` section and give every generated page a repository edit location:

```json
{
  "content": {
    "root": "docs/public",
    "assets": [{
      "source_document": "docs/public/assets/account.txt",
      "wiki_path": "assets/account.txt",
      "owner": "account-maintainers"
    }]
  },
  "topics": [{
    "id": "accounts.overview",
    "owner": "account-maintainers",
    "wiki_page": "Accounts.md",
    "edit_at": "repository",
    "source_document": "docs/public/Accounts.md",
    "depends_on": [{"architecture_page": "modules/accounts.md"}]
  }]
}
```

Source documents and assets use consumer-relative paths under `content.root`.
Pin Markdown line endings, for example with `*.md text eol=lf` in
`.gitattributes`, to keep exact review bases reproducible across operating systems.
Public page filenames are flat Markdown names. Map `Home.md` and `_Sidebar.md`
as repository-authored topics when the project owns them. Handwritten topics
remain `edit_at: wiki`; their observed bytes are preserved in the candidate.

Export requires whole-page ownership. A repository-authored page cannot share
its destination with manual or separately mapped sections. Existing section
bindings remain available for read-only impact reporting.

Use relative source links between mapped documents and assets. The exporter
rewrites them to wiki destinations. A native wiki link such as
`[[Wiki tooling|Wiki-Tooling]]` can refer to a preserved manual page. Repository
file links require an explicit `content.repository_url` and pinned
`--source-revision`; local host paths cannot establish public links.

## Import a manual page deliberately

Copy its reviewed wording into the declared source document. Add a before-hash
adoption for the exact bytes in the pinned target copy:

```json
{
  "content": {
    "root": "docs/public",
    "adoptions": [{
      "path": "Accounts.md",
      "expected_hash": "sha256:<64 lowercase hexadecimal characters>",
      "reason": "Move the reviewed overview to its repository edit location"
    }]
  }
}
```

The adoption records a proposed ownership change; the resulting candidate still
needs review. A changed target page requires a fresh reviewed adoption.
Unmanaged pages and assets stay unchanged.

After an accepted owned tree becomes the next target copy, remove any one-time
adoption whose before hash no longer describes that copy. Subsequent ownership
comes from the accepted previous receipt.

An accepted previous candidate receipt supplies the earlier owned inventory
through `--previous-receipt`. Removing a mapping does not delete its public page.
An owned removal requires a `content.removals` entry with `path`, `expected_hash`
and `reason`, an accepted impact baseline and retirement review. A rename
combines an explicit removal with its new destination. Unmanaged content cannot
be removed by this workflow.

## Render and inspect

Use a pinned local target copy when one exists. A new project can omit
`--target-dir` and prepare an artifact-only candidate. Source-only consumers use
`architecture.baseline: bootstrap-source`; native evidence is prepared in
temporary storage. Existing native wikis retain their integrity prerequisite.

The following commands show an ongoing review with an accepted baseline. On
first adoption, omit `--baseline` consistently from export, impact and check.

```bash
.venv/bin/llm-wiki docs wiki export --target-dir sibling-wiki --baseline .llm-wiki/publication-baseline.json --output-dir reports/wiki-candidate --receipt reports/wiki-candidate.json
.venv/bin/llm-wiki docs wiki check --target-dir sibling-wiki --baseline .llm-wiki/publication-baseline.json --candidate-dir reports/wiki-candidate --receipt reports/wiki-candidate.json
```

The candidate directory must be new or empty and separate from authored,
native and target inputs. Keep metadata outside the candidate tree. Use a fresh
directory after changing the source or mapping. The checker re-reads candidate
bytes, re-renders current inputs and rejects stale or altered content. Identical
inputs produce identical page bytes.

Relative candidate paths resolve under the consumer root; explicit absolute
artifact paths are also supported. For source-only projects, generated code or
package attachments must stay outside selected source inputs, using an excluded
output directory or an external artifact directory. Source selection is never
changed by the exporter. Topic decisions for an external artifact can use the
receipt's `basis` and `impact` with the Python review API.

Inspect `operations`, `checks.findings` and `impact.findings` in the receipt.
HTML links/media and YAML front matter are outside this profile; use Markdown
links and declared assets. External URLs are not fetched.
Target checks cover Home/navigation, local links, anchors, assets and portable
path collisions. Caller-supplied `--source-revision` and `--target-revision`
label pinned inputs; they do not verify a remote repository. The receipt records
`target.remote_verified: false` and `delivery_ready: false`.

## Review the proposed public text

Compare the candidate with its pinned target copy and inspect the supporting
evidence. Resolve topic obligations against the candidate directory so the
resulting decisions bind the proposed text:

```bash
.venv/bin/llm-wiki docs impact --target-dir reports/wiki-candidate --baseline .llm-wiki/publication-baseline.json --output reports/candidate-impact.json
.venv/bin/llm-wiki docs impact resolve --target-dir reports/wiki-candidate --baseline .llm-wiki/publication-baseline.json --report reports/candidate-impact.json --finding <finding-id> --decision still-current --reviewer alice --reason "The proposed topic matches the current evidence" --output .llm-wiki/publication-reviews.proposed.json
```

Include `--reviews` when extending an existing topic ledger. Each topic decision
remains bound to its evidence and target bytes. A candidate also needs a separate
exact-artifact approval covering its complete tree and ownership changes:

```bash
.venv/bin/llm-wiki docs wiki review --target-dir sibling-wiki --candidate-dir reports/wiki-candidate --receipt reports/wiki-candidate.json --reviewer alice --reason "Reviewed the public diff, assets and ownership changes" --output .llm-wiki/candidate-review.proposed.json
```

Local-snapshot review requires the original `--target-dir`; the command checks
that its bytes still match the receipt and keeps review metadata outside it.
Artifact-only review omits that option. Current configuration inputs remain
protected even when reviewing an older receipt.

Submit canonical content, mapping changes and both proposed review records
through the consumer's normal repository review process. Reviewer text alone
does not authenticate an identity. After acceptance, supply the accepted records
and recheck the original candidate:

```bash
.venv/bin/llm-wiki docs wiki check --target-dir sibling-wiki --baseline .llm-wiki/publication-baseline.json --candidate-dir reports/wiki-candidate --receipt reports/wiki-candidate.json --reviews .llm-wiki/publication-reviews.json --candidate-review .llm-wiki/candidate-review.json --output reports/wiki-candidate.checked.json --require-ready
```

Use the same baseline and previous-receipt inputs as the export. Candidate
identity excludes accepted review state, so exact approvals can clear review
without changing page bytes. Changes to source, mapping, provider, target base
or candidate files require a fresh candidate and review. Local `ready` requires
structural checks, topic review and the exact candidate approval. It does not
authorize delivery. Baselines and delivered checkpoints never advance automatically.

Successful preparation exits 0 while review is pending. Structural failures
exit 1, and `--require-ready` also exits 1 for unresolved review. Invalid inputs,
stale receipts and changed candidate files exit 2.

## Consumer automation

Install the selected provider with its `publication` extra from a verified
immutable distribution or exact source revision, in an isolated environment.
Verify its installed code origin. Keep application-specific reference generation
and freshness comparison in the consumer's environment, as described in
[CLI reference data](cli-reference-data.md). Run native integrity when required,
then prepare and check the candidate. Retain the tree, receipt and proposed diff
as review artifacts. Store accepted baselines, topic ledgers and approvals in
durable consumer storage. Consumers use their own CI profiles and only the
source-language helpers they need.

Receipts also record the Markdown parser version. Keep exports and checks in
the same pinned consumer environment. Bind an asset as a topic `source_file`
dependency when it supports a claim; the complete candidate approval covers all
declared assets regardless of their topic bindings.

The [source-only example](../examples/sibling-wiki/README.md) includes authored
Home/sidebar pages, an asset, explicit manual-page adoption and a preserved
manual topic. GitHub credentials and a publisher are unnecessary for local
preparation and review.

## Python integration

```python
from llm_wiki_cli.api import (
    export_publication_candidate,
    check_publication_candidate,
    review_publication_candidate,
    validate_publication_receipt,
)

receipt = export_publication_candidate(
    ".", output_dir="reports/wiki-candidate", target_dir="sibling-wiki"
)
validate_publication_receipt(receipt)
proposal = review_publication_candidate(
    receipt, reviewer="alice", reason="Reviewed the complete public candidate"
)
checked = check_publication_candidate(
    ".", candidate_dir="reports/wiki-candidate", receipt=receipt,
    target_dir="sibling-wiki", candidate_review=proposal,
)
```

The API returns detached JSON-compatible records. Accept review proposals under
the consumer's policy before supplying them as accepted input. Invalid requests
use the public `InvalidRequestError` taxonomy.
