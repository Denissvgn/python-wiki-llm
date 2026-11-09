# GitHub wiki candidates

Prepare a local GitHub wiki candidate from explicitly mapped public Markdown.
Its receipt binds the input basis, provider identity, target-copy hashes,
owned paths, operations, structural checks and exact review state. Generation
and checking perform no remote Git operations.

## Choose the source and public target

Install the provider with its `publication` extra in a separate environment.
Choose the source of the architecture evidence, then decide whether to supply
a local copy of an existing public wiki.

| Starting point | Setup |
| --- | --- |
| New Python project | Set `architecture.baseline` to `bootstrap-source` and `architecture.root` to the Python source directory. Map an authored document to `Home.md`. Local export works before Git initialization and uses the built-in Python extractor. Omit `--target-dir` for the first artifact. |
| New non-Python project | Use the same source-only configuration. Put the source selection under the configured source root, inspect the helper plan and prepare the helpers it lists. |
| Existing managed native wiki | Set `architecture.baseline` to `existing-wiki`, `architecture.root` to the native wiki directory and `architecture.source_root` to the source used to generate it. Export and check then validate current native evidence locally and in the action. An explicit action `src-dir` must agree with the declared source root. |
| Manually maintained public wiki | Use either source baseline. Map manual topics with `edit_at: wiki` and run `docs impact --target-dir "Snapshots/Public wiki"` against a local public copy. To move one page to repository ownership, import it with the reviewed before-hash. The other pages, navigation and attachments keep their original bytes. |

For example, for TypeScript under `Application code/`, run the following
from the consumer root. Set `LLM_WIKI_CACHE_DIR` to an absolute helper-cache
directory outside the checkout. Keep it set for export and check.

```sh
llm-wiki prepare-extractors --src-dir "Application code" --plan --format json
llm-wiki prepare-extractors --src-dir "Application code" --cache-dir "$LLM_WIKI_CACHE_DIR"
llm-wiki docs wiki export --config "Review settings/Wiki policy.json" --output-dir reports/candidate --receipt reports/receipt.json
llm-wiki docs wiki check --config "Review settings/Wiki policy.json" --candidate-dir reports/candidate --receipt reports/receipt.json
```

Prepare dependencies while the required tools and downloads are available.
With the installed provider, matching runtime, prepared helpers and local
inputs, candidate generation and checking can run offline. If TypeScript
extraction reports `node not found`, install Node and npm, then prepare the
helper. If Node is available and the TypeScript helper is missing, run
`prepare-extractors` against the selected source using the cache that export
will read. In PowerShell, set the cache with
`$env:LLM_WIKI_CACHE_DIR` and pass that value to `--cache-dir`. Use `/` in
paths stored in policy JSON on every platform. Quote CLI paths that contain
spaces. `--config` and `--target-dir` resolve under `--consumer-root`.

### Recover a blocked candidate

- **Stale native evidence.** Inspect `native-integrity.json` and
  `native-freshness.json` from the candidate action. Run the owning native
  sync with the original source, selection and runtime, then export a fresh
  candidate and review its new receipt. If the report lists retained
  historical pages as the remaining cause, preserve the historical wiki.
  A project that needs a current-only baseline can bootstrap a separate
  native wiki and review the changed configuration and topic bindings.
- **Pinned target bytes differ.** A Git checkout can be clean even when Git
  has converted line endings or applied a checkout filter. The candidate
  action compares each retained file to the blob at the pinned wiki commit.
  For automatic line-ending conversion, use a fresh independent checkout,
  for example `git clone --config core.autocrlf=false "$WIKI_CLONE_URL" "Snapshots/Public wiki"`.
  Check the target's attributes if a filter still changes the bytes. When
  using a plain snapshot, its inventory of file hashes identifies it.
- **Approval is pending.** With `publish: false`, a valid candidate can
  report `ready: false` while it awaits review. Use the receipt to review
  the artifact or hand off mapped edits to an author. On a fork pull request,
  the read-only workflow uses the proposed source and reads accepted records
  at their paths in the PR base commit. Submit new decisions through the
  consumer's review process.

Source and wiki branches have independent names. The optional publisher
discovers the wiki's default branch when no override is configured.
[Delivery and branch selection](../integrations/wiki-candidate/delivery/README.md)

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
native and target inputs. Keep receipts, baselines and review records outside
both the public target copy and the candidate directory. Files in the target
copy are carried into the public candidate. Use a fresh directory after
changing the source or mapping. The checker re-reads candidate
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

## Propose a reviewed edit to a mapped topic

Use `docs wiki maintain` when an impact finding calls for a change to
repository-authored Markdown. It copies the selected original documents into
an isolated documentation workspace and records the finding, dependencies and
before-hash for each topic. A manual wiki topic remains with its wiki editor.
For wording that is still accurate, use the existing topic decision workflow.

For example, in the source-only example consumer, first export a candidate
using the commands in its README. From that consumer's root, use your installed
`llm-wiki` and a fresh workspace outside the checkout.

```bash
scratch=$(mktemp -d)
workspace="$scratch/workspace"
printf '%s\n' 'Keep the public account guide consistent with the account implementation.' > "$scratch/brief.md"
llm-wiki docs prepare --workspace "$workspace" --baseline bootstrap-source --src-dir project \
  --site-name Accounts --project-brief "$scratch/brief.md" \
  --audience operator --audience-intent 'operator=manage accounts'

# Use these same candidate, receipt and topic inputs when collecting the patch.
wiki_inputs=(--workspace "$workspace" --candidate-dir reports/wiki-candidate \
  --receipt reports/wiki-candidate.json --target-dir sibling-wiki --topic accounts.overview)
llm-wiki docs wiki maintain "${wiki_inputs[@]}"
```

For a managed native wiki, prepare with `--baseline existing-wiki`, its
configured `--input-wiki-dir`, the matching `--src-dir` and current native
evidence. Bind the workspace before issuing its first packet. Supply the same
baseline, topic reviews and previous receipt used to check the candidate.
Repeat `--topic` to select more than one pending repository-owned topic.

The preparation result lists the work that awaits a host. The supervisor
issues the normal `wiki-enrichment`, `user-docs` and `review` packets. During
`user-docs`, the author edits only the assigned copies under `mapped-docs/`,
reports their paths in `changed_document_paths` relative to that directory,
and cites native evidence in `claims_evidence_pages`. The reviewer reads the
exact edited text and returns findings. With `--actor`, the supervisor records
the identity of the worker it dispatched. The host authenticates those
identities. Use a reviewer
distinct from the authors, keep lifecycle control files under supervisor
ownership, and retain the resulting review record.

```bash
llm-wiki docs packet --workspace "$workspace" --stage wiki-enrichment --format json
llm-wiki docs record-result --workspace "$workspace" --actor "$ENRICHER_ID" --result "$ENRICHER_RESULT"
llm-wiki docs packet --workspace "$workspace" --stage user-docs --format json
llm-wiki docs record-result --workspace "$workspace" --actor "$AUTHOR_ID" --result "$AUTHOR_RESULT"
llm-wiki docs packet --workspace "$workspace" --stage review --format json
llm-wiki docs record-result --workspace "$workspace" --actor "$REVIEWER_ID" --result "$REVIEW_RESULT"
llm-wiki docs verify --workspace "$workspace"
llm-wiki docs wiki patch "${wiki_inputs[@]}" --format patch > "$scratch/accounts.patch"
git apply --check "$scratch/accounts.patch"
```

The collector re-renders the reviewed Markdown against the candidate's other
pages and assets and checks their links and anchors before emitting the patch.
The patch uses consumer-relative paths. If the consumer is a subdirectory of
a Git repository, run `git apply --check --directory=path/to/consumer` with
the patch file from the Git root. Python callers can use
`api.prepare_publication_maintenance` and `api.build_publication_patch` with
the same workspace, candidate, receipt and topic IDs. The default CLI JSON and
the Python result include the review identity, document hashes and patch
digest. Submit the edit through the
consumer's normal repository review. After it lands, export and review a fresh
wiki candidate. Preparation and patch collection leave the canonical Markdown,
the public target and accepted publication records untouched.

See the [documentation workspace handoff](standalone-documentation.md#run-the-agent-stages)
for the stage contracts and supervisor responsibilities.

## Consumer automation

Run `llm-wiki install-ci --profile documentation --action-ref "$ACTION_COMMIT_SHA"`
to install the read-only candidate workflow in a configured consumer. For the
included source-only example, also pass `--target-dir sibling-wiki` to supply
the before-image used by its adoption. The [automation guide](automation.md#install-a-github-wiki-candidate-workflow)
describes installation, and the [candidate action](../integrations/wiki-candidate/README.md)
documents its inputs and review artifacts.

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

## Deliver or roll back a reviewed wiki

For an initialized GitHub wiki, a separate protected publisher can deliver a
reviewed candidate from the eligible source commit. Version 1 configurations
remain read-only. Version 2 adds the explicit `publish` opt-in, an optional
target branch and an exact tag for release-based documentation. The publisher
checks the live source and target, records ownership in the wiki commit and
fetches the commit back before reporting success. Rollback uses its own
reviewed proposal and creates a new commit on top of the current wiki.
See the [delivery and rollback guide](../integrations/wiki-candidate/delivery/README.md).

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
