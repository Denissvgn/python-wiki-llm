# Sibling wiki impact action

Find public wiki sections that need review when their architecture evidence changes. The action reads a consumer's publication configuration, native wiki and accepted snapshot, then saves a JSON report and Markdown summary. It supports a local wiki checkout or pinned local copy and requires no wiki publishing credential.

The provider comes from this action's checkout. Pin the action to a reviewed full commit SHA. The action creates a separate virtual environment, installs that provider noneditably, and verifies its installed code against the action source. Your application's package and virtual environment are not installed or changed.

Follow the [sibling wiki guide](../../docs/sibling-wiki.md) to configure architecture dependencies and review state. The example below assumes the consumer already provides its native wiki, accepted snapshot and a local public wiki copy at `sibling-wiki/`.

```yaml
name: Sibling wiki impact
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  impact:
    runs-on: ubuntu-24.04
    timeout-minutes: 40
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803
        with:
          persist-credentials: false
      - name: Check public documentation impact
        id: impact
        uses: Denissvgn/python-wiki-llm/integrations/wiki-impact@<full-commit-sha>
        with:
          config: .llm-wiki/publication.json
          baseline: .llm-wiki/publication-baseline.json
          target-dir: sibling-wiki
```

Replace `<full-commit-sha>` with the immutable provider revision you selected. Configure `architecture.root` and topic dependencies in the consumer's publication configuration. Supply the local public wiki copy explicitly through `target-dir`; its path is not stored in the configuration. Relative inputs resolve from `working-directory`, which defaults to the checked-out project root. The local target must stay within that consumer directory; check out additional content beneath it when needed. The action does not clone a wiki or contact its Git remote during impact evaluation.

Omit `baseline` for the CLI's initial assessment. Before accepting the first baseline, review the initial coverage and mapping decisions. An existing manual wiki can remain manually edited while the report identifies sections to inspect. Changes to configuration, evidence or section text invalidate decisions tied to the previous basis.

| Input | Default | Purpose |
| --- | --- | --- |
| `config` | `.llm-wiki/publication.json` | Consumer publication configuration. |
| `baseline` | Empty | Accepted local snapshot; empty selects initial assessment. |
| `reviews` | Empty | Optional accepted review ledger. |
| `target-dir` | Empty | Consumer-relative local public wiki directory. |
| `working-directory` | `.` | Consumer directory inside `GITHUB_WORKSPACE`. |
| `fail-on` | `error` | Preserve CLI policy, or additionally fail on advisory findings with `review-required`. |
| `evidence-id` | `default` | Unique suffix for multiple invocations in one job; lowercase letters, digits, `.`, `_` and `-`, up to 40 characters. |

Pass `reviews` only from the consumer's trusted accepted source. A ledger included in a proposed change has not become accepted merely because the action can read it. This action checks the supplied local evidence; repository review rules determine who may accept mappings and dispositions. Keep shared baselines and accepted decisions unchanged during PR evaluation and promote reviewed state through the consumer's normal review process.

The action preserves failures required by the configured CLI policy. `fail-on: error` allows complete advisory reports with review findings to succeed; malformed, unavailable or incomplete evidence fails. `fail-on: review-required` also fails a complete advisory report requiring review. The action does not weaken a required gate configured in the consumer project.

| Output | Meaning |
| --- | --- |
| `report-path` | JSON report location, when produced. |
| `summary-path` | Markdown report location, when produced. |
| `provider-receipt` | Verified installed provider identity and fingerprint. |
| `complete` | All evidence required for this evaluation was available. |
| `review_required` | Public content or coverage needs attention. |
| `changed` | Evaluation observed changed inputs; interpret alongside `complete`. |
| `ready` | The impact review gate is satisfied. Delivery needs its own checked candidate and verified remote base. |

Boolean outputs are the strings `true` and `false`. An unavailable report defaults to `complete=false`, `review_required=true`, `changed=false` and `ready=false`. Reports, provider identity and diagnostics are retained in a job artifact for 14 days. Store accepted checkpoints and review state in the consumer's durable configuration or state backend; artifact retention does not replace that state.
