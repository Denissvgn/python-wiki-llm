# GitHub wiki candidate action

Render the consumer’s mapped pages, preserve the public files in its optional
target copy and retain an independently checked candidate for review on GitHub.
The job needs read access to the consumer repository. It can run on fork pull
requests with `pull_request` and `contents: read`.

```yaml
name: Review wiki candidate
on: [pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  candidate:
    runs-on: ubuntu-24.04
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803
        with:
          persist-credentials: false
          fetch-depth: 0
      - uses: Denissvgn/python-wiki-llm/integrations/wiki-candidate@<full-provider-commit-sha>
        with:
          source-revision: ${{ github.sha }}
          config: .llm-wiki/publication.json
```

Replace the placeholder with a reviewed full commit SHA containing the action.
The action installs its pinned provider with the `publication` extra in a
private virtual environment, verifies the installed files against that source,
and records the provider revision independently of the consumer’s Git revision.
Keep the consumer checkout clean, including ignored files. Use a separate step
and working directory for application-specific build or contract generation.
The helper plan selects the languages in the consumer’s source scope. An
existing native wiki must pass the provider’s integrity and freshness checks.

| Input | Meaning |
| --- | --- |
| `working-directory` | Consumer project inside the checkout. Defaults to `.`. |
| `config` | Consumer-relative publication configuration. Defaults to `.llm-wiki/publication.json`. |
| `src-dir` | Consumer-relative source for an existing native wiki. Defaults to `.`. Source-only projects declare their source in `architecture.root`. |
| `source-revision` | Expected full commit SHA. The default is the consumer checkout’s HEAD. |
| `target-dir` | Optional consumer-relative target copy. Omit to render an artifact-only candidate. |
| `target-revision` | Optional expected full commit SHA of a separate local target Git checkout. A plain tracked copy is identified by its file hashes. |
| `accepted-state-revision` | Full local commit SHA containing accepted review state. Defaults to the PR base on pull requests and to the consumer HEAD on other runs. A pull request may use only its exact base. |
| `baseline`, `reviews`, `previous-receipt`, `candidate-review` | Optional consumer-relative paths to the accepted publication basis, topic ledger, prior ownership and exact approval at the accepted-state revision. |
| `fail-on` | `error` enforces structural checks, complete evidence and the consumer’s configured impact policy. `review-required` also requires an accepted exact candidate approval. |
| `evidence-id` | Unique artifact suffix within the job, using up to 40 lowercase letters, digits, dots, dashes or underscores. Defaults to `default`. |

Supply a tracked target copy or a clean separate target checkout beneath the
consumer when comparing with an existing public wiki. For a separate checkout,
the action verifies the retained bytes against the pinned Git blobs. If Git
converted them during checkout, follow the [checkout recovery instructions](../../docs/sibling-wiki-candidates.md#recover-a-blocked-candidate).
Manually maintained
pages are retained byte for byte. A changed proposal can pass an advisory run
while awaiting human review. For a proposed edit to a baseline or review record,
run against the accepted inputs and promote the proposal through the consumer’s
normal review process.

To recheck an exact approval committed after its candidate was prepared, check
out the **original source SHA** on a trusted manual run. Fetch the commit
containing the accepted decisions, set `accepted-state-revision` to its full
SHA, and supply the paths to the records from that commit. Keep the original
provider SHA, target copy and baseline inputs. This preserves the reviewed
candidate identity while recording where the accepted decisions came from.

The `llm-wiki-candidate-…` job artifact contains `candidate.zip`, including
permitted dotfiles and binary assets, `candidate.diff`, `receipt.json` and the
topic-level `impact.json`. Large text and binary changes in the diff are
identified by their before and after hashes. The provider receipt, helper plan,
applicable native checks and diagnostic logs accompany the candidate. Inspect
the recorded errors when setup or rendering stops before a checked tree exists.
Artifacts are retained for 14 days.

Subsequent steps in the same job can consume `candidate-dir`, `receipt-path`,
`report-path`, `diff-path` and `provider-receipt`. The string outputs `changed`
and `ready` describe a checked public tree. `changed` compares its bytes with
the target copy. `ready` requires complete local checks and exact reviews.
Check the step outcome before consuming any outputs. The action performs no
remote wiki access or delivery.

[Candidate configuration and review guide](../../docs/sibling-wiki-candidates.md)

For a v2 consumer that opts into delivery, pass the successful job's
`artifact-id` and `receipt-id` outputs to the separate protected publisher
in the same workflow run and attempt. The candidate job retains its
read-only permissions. [Delivery and rollback guide](delivery/README.md)
