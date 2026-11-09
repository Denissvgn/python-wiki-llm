# Deliver a reviewed sibling wiki

This action delivers an approved GitHub wiki candidate to an initialized
GitHub.com wiki. It checks the source policy and the live wiki branch, writes
the reviewed changes, and fetches the result into a fresh Git repository for
verification. The existing candidate workflow remains usable on its own.

## Set up the publisher

1. Create the wiki's first page on GitHub and record its Git clone URL.
   GitHub serves pages from the wiki repository's default branch. An explicit
   `target.branch` selects a different existing branch when that is the
   intended deployment destination. An inaccessible repository requires an
   access or network diagnosis. [GitHub wiki setup](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)
2. Copy [the manual workflow](workflow.yml.example) to
   `.github/workflows/reviewed-wiki-delivery.yml` in the **consumer**
   repository. Replace both `FULL_PROVIDER_COMMIT` tokens with the same
   reviewed 40-character provider commit containing both actions. The
   example uses the consumer root, the default configuration and the caller's
   own wiki. For a separate target, set the publisher's `target-repository`
   to the authorized `owner/repository`, update the read-only clone URL and
   use that target's wiki identity for the concurrency group.
3. Protect the eligible source branch or release tags, and restrict the
   `wiki-publisher` environment to those refs. Configure required reviewers
   and control which workflows may use its secrets. Give only this environment
   the `WIKI_GIT_TOKEN` credential authorized for Git writes to the selected
   wiki. A private target can supply a separate read-only `WIKI_READ_TOKEN`
   to the preparation job. The caller token needs only source read access.
   [Environment protection and secrets](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
4. Adopt `llm-wiki-publication/v2` in the consumer configuration with
   `"publish": false`. Keep the authored content, owners, topics and target
   declarations. The default source policy follows the current default branch.
   For a release use `"source_policy": "release"` with an exact short
   `"release_tag": "v4.1.0"` and dispatch on that protected tag.
   Run `qualify` from the eligible source ref with publishing disabled.
   It resolves the source and target refs, validates existing checkpoint
   history and requests a Git receive-pack dry run against the existing
   branch. The result records `write_verified: false`. A real approved update
   followed by successful readback qualifies the complete write path. Repeat
   qualification when rotating the wiki credential.
5. After qualification, set `publish` to the JSON boolean `true` through
   source review. Changing the policy requires a new reviewed candidate.
   For immutable tags, qualify on a rehearsal ref, then review the enabled
   policy before cutting the release tag. Version 1 remains read-only.

## Deliver

Prepare and review the candidate against a clean checkout of the separate
wiki at its exact commit. Record the source SHA, wiki base SHA and pinned
provider SHA. The [candidate guide](../../../docs/sibling-wiki-candidates.md)
describes topic decisions, exact candidate approval, adoptions and removals.

The example keeps accepted records on a separate protected branch named
`wiki-reviews`. Keep their paths relative to the consumer. Store the accepted
topic ledger at `.llm-wiki/publication-reviews.json` and the exact approval
at `.llm-wiki/candidate-review.json`. When applicable, supply the same
accepted baseline and previous full ownership receipt that were used for
review. The separate branch lets a review land while the eligible source SHA
stays current.

Dispatch `deliver` with the reviewed wiki commit as `target-revision`.
The preparation job reconstructs and independently checks that exact candidate
without the publisher credential. Its successful job outputs identify one
immutable artifact and one checked receipt. The publisher consumes those
outputs from the same run and attempt. It checks the installed provider,
committed opt-in policy, protected approval records, reviewed bytes, and live
refs. Rerun the **entire workflow** after an interrupted run so preparation
and delivery share the same attempt.

An update creates a direct child of the reviewed wiki tip and uses an
explicit, fast-forward-only Git push. Its `.llm-wiki-delivery.json` file
records portable source, provider, ownership and receipt commitments. Keep
the checked full receipt in durable consumer storage. After verified delivery,
use the receipt named by the checkpoint as `.llm-wiki/previous-receipt.json`
for the next review. Remove one-time adoptions once ownership is established.
A byte- and ownership-identical proposal produces no commit.

Read `delivery-result.json` in the job artifact. A verified delivery includes
`readback_verified: true`, the wiki branch, commit and Git tree. If the
source moved, export against its newly eligible revision. If the target moved,
inspect the new base and preserve manual edits in a newly reviewed candidate.
A lost push response triggers a fresh readback. If verification still fails,
keep the last verified checkpoint and compare the remote before another
delivery. An exact retry can recognize a previously accepted commit.

## Roll back

1. Dispatch `plan-rollback` with the current wiki tip as `target-revision`
   and an earlier wiki commit on the same branch's first-parent history as
   `restore-revision`. Inspect the proposed paths, hashes and diff in
   `delivery-result.json`.
2. Review the exact proposal and commit a record with the following fields
   to `.llm-wiki/rollback-review.json` on the protected approval branch.

   ```json
   {
     "schema_version": "llm-wiki-rollback-review/v1",
     "rollback_id": "sha256:<digest from the reviewed proposal>",
     "reviewer": "wiki-maintainer",
     "reason": "Restore the previously approved account guide"
   }
   ```

3. Dispatch `rollback` with the **same** source, target and restore revisions.
   The publisher recomputes the proposal before using the approval. It restores
   the earlier owned content through a new forward commit, preserves later
   unmanaged changes, and verifies the resulting remote tree. A conflict
   with a now-manual path requires a new review. The source high-water mark
   continues to guard against older deployments after a rollback.

The example workflow is opt-in. The read-only installer generates only the
candidate workflow. Copying a delivery report or dispatching a pull request
does not arm this publisher.
