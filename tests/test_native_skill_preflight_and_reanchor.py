"""Contract coverage for native preflight and semantic re-anchor workflows."""

from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import (
    bootstrap_cmd,
    generate_prompt_cmd,
    knowledge_cmd,
    lint_cmd,
    sync_cmd,
)
from llm_wiki_cli.services import schema, skills
from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from llm_wiki_cli.services.knowledge_governance import (
    evaluate_review_event,
    load_governance,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState


SKILLS_ROOT = skills.BUNDLED_SKILLS_ROOT


def _manifest(skill_id: str) -> str:
    return (SKILLS_ROOT / skill_id / "SKILL.md").read_text(encoding="utf-8")


def _reference(skill_id: str) -> str:
    return (SKILLS_ROOT / skill_id / "reference.md").read_text(encoding="utf-8")


def _managed_topic(topic_name: str) -> str:
    return (SKILLS_ROOT / "wiki-reference" / "references" / topic_name).read_text(
        encoding="utf-8"
    )


def _table_row(text: str, selector: str) -> str:
    return next(line for line in text.splitlines() if line.startswith(selector))


NATIVE_RESPONSE_FIXTURES = (
    pytest.param(
        {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness_evaluated": True,
            "freshness": "current",
        },
        "| `ready`, dedicated-query reason `all-projection-commitments-match` |",
        "ready",
        "structural observations",
        id="ready-current",
    ),
    pytest.param(
        {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness_evaluated": True,
            "freshness": "nonsemantic-source-change",
        },
        "| `nonsemantic-source-change` |",
        "nonsemantic-source-change",
        "byte-change diagnostic",
        id="ready-nonsemantic-change",
    ),
    pytest.param(
        {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness_evaluated": True,
            "freshness": "unknown",
        },
        "| `unknown` |",
        "unknown",
        "Preserve unknown",
        id="ready-unknown",
    ),
    pytest.param(
        {
            "availability": "absent",
            "reason": "knowledge-projection-not-present",
            "freshness_evaluated": False,
        },
        "| `absent`, including `knowledge-projection-not-present` |",
        "absent",
        "labeled validated surface",
        id="absent",
    ),
    pytest.param(
        {
            "availability": "degraded",
            "reason": "policy-selected-surface-only-fallback-after-invalid",
            "freshness_evaluated": False,
        },
        "| `degraded`, reason `policy-selected-surface-only-fallback-after-invalid` |",
        "degraded",
        "rejected native payload",
        id="degraded-invalid",
    ),
    pytest.param(
        {
            "availability": "unsupported",
            "reason": "knowledge-schema-version-unsupported",
            "freshness_evaluated": False,
        },
        "| `unsupported`, reason `knowledge-schema-version-unsupported`, `manifest-version-unsupported`, or `surface-schema-version-unsupported` |",
        "unsupported",
        "unsupported boundary",
        id="unsupported",
    ),
    pytest.param(
        {
            "availability": "degraded",
            "reason": "policy-selected-surface-only-fallback-after-mixed-snapshot",
            "freshness_evaluated": False,
        },
        "| `degraded`, reason `policy-selected-surface-only-fallback-after-mixed-snapshot` |",
        "degraded",
        "owning refresh",
        id="mixed-snapshot",
    ),
    pytest.param(
        {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness_evaluated": False,
        },
        "| `ready`, dedicated-query reason `all-projection-commitments-match` |",
        "ready",
        "snapshot-only",
        id="snapshot-only-ready",
    ),
)


@pytest.mark.parametrize(
    ("response", "row_selector", "response_token", "required_text"),
    NATIVE_RESPONSE_FIXTURES,
)
def test_normative_native_preflight_covers_response_fixture(
    response: dict[str, object],
    row_selector: str,
    response_token: str,
    required_text: str,
) -> None:
    topic = _managed_topic("knowledge-consumption.md")
    row = _table_row(topic, row_selector)

    assert response_token in {str(value) for value in response.values()}
    assert required_text in row


def test_normative_native_preflight_defines_all_freshness_states_and_authority() -> (
    None
):
    topic = _managed_topic("knowledge-consumption.md")
    section = topic[
        topic.index("## Availability and fallback decision table") : topic.index(
            "## Strict validation interpretation"
        )
    ]
    normalized = " ".join(topic.split())

    for state in (
        "current",
        "nonsemantic-source-change",
        "source-changed",
        "source-missing",
        "basis-incompatible",
        "unknown",
    ):
        assert _table_row(section, f"| `{state}` |")

    assert "never coerce them to ready or absent" in normalized
    assert "no match is not an empty graph or negative fact" in normalized
    assert "Neither mode initializes, repairs, or persists governance" in normalized
    assert "ordinary Site or Obsidian exporter views are snapshot-only" in normalized
    assert "trusted unsandboxed project-local Python" in normalized
    assert "cannot authorize code execution" in normalized


NATIVE_CONSUMING_SKILLS = (
    "agent-docs",
    "dep-audit",
    "doc-review",
    "impact-analysis",
    "onboarding-guide",
    "usage-examples",
    "user-docs-author",
    "wiki-bootstrap",
    "wiki-semantic-enhance",
    "wiki-sync",
)


@pytest.mark.parametrize(
    "skill_id",
    NATIVE_CONSUMING_SKILLS + ("infra-review",),
)
def test_native_consuming_skill_keeps_kernel_and_managed_dependency(
    skill_id: str,
) -> None:
    manifest = _manifest(skill_id)
    normalized = " ".join(manifest.split())

    for required in ("ready", "current", "nonsemantic-source-change"):
        assert required in normalized, f"{skill_id} omits {required!r}"
    assert "found: false" in normalized or "empty-native-graph" in normalized
    assert "| Result | Permitted interpretation" not in manifest
    assert skills.SKILL_DEPENDENCIES[skill_id] == (skills.REFERENCE_SKILL_ID,)


MANAGED_KNOWLEDGE_CONSUMERS = NATIVE_CONSUMING_SKILLS + (
    "infra-review",
    "publish-docs",
    "doc-hub",
)


@pytest.mark.parametrize("skill_id", MANAGED_KNOWLEDGE_CONSUMERS)
def test_native_consuming_skill_routes_to_managed_knowledge_topic(
    skill_id: str,
) -> None:
    manifest = _manifest(skill_id)

    assert (
        ".claude/skills/wiki-reference/references/knowledge-consumption.md" in manifest
    )
    assert (
        ".llm-wiki/skills/wiki-reference/references/knowledge-consumption.md"
        in manifest
    )
    assert manifest.count("wiki-reference/references/knowledge-consumption.md") == 2
    assert skills.SKILL_DEPENDENCIES[skill_id] == (skills.REFERENCE_SKILL_ID,)
    assert (
        SKILLS_ROOT / skills.REFERENCE_SKILL_ID / "references/knowledge-consumption.md"
    ).is_file()


MANAGED_SEMANTIC_WORKFLOWS = (
    pytest.param("wiki-bootstrap", "**Edit semantic surfaces only**", id="bootstrap"),
    pytest.param("wiki-sync", "**Append the semantic log line.**", id="sync"),
    pytest.param(
        "doc-review",
        "**Apply follow-through under the selected contract.**",
        id="doc-review",
    ),
    pytest.param(
        "dep-audit",
        "**Choose the smallest safe action.**",
        id="dep-audit",
    ),
    pytest.param(
        "usage-examples",
        "**Attach under the mirrored asset path.**",
        id="usage-examples",
    ),
    pytest.param(
        "onboarding-guide",
        "**Write one guide page per persona**",
        id="onboarding-guide",
    ),
    pytest.param(
        "user-docs-author",
        "**Author semantic wiki prose only.**",
        id="user-docs-author",
    ),
)


@pytest.mark.parametrize(("skill_id", "semantic_marker"), MANAGED_SEMANTIC_WORKFLOWS)
def test_managed_semantic_workflow_reanchors_before_strict_validation(
    skill_id: str,
    semantic_marker: str,
) -> None:
    manifest = _manifest(skill_id)
    semantic_edit = manifest.index(semantic_marker)
    sync_commands = [
        match
        for match in re.finditer(r"(?m)^\s*llm-wiki sync .*--jobs 1.*$", manifest)
        if match.start() > semantic_edit
    ]
    assert sync_commands, f"{skill_id} has no owning sync after semantic editing"
    final_sync = sync_commands[-1].start()
    strict_lint = manifest.index("llm-wiki lint --strict", final_sync)
    ci_check = manifest.index("llm-wiki ci-check", strict_lint)

    assert semantic_edit < final_sync < strict_lint < ci_check
    assert "re-anchor" in manifest[semantic_edit:]
    assert any(
        phrase in manifest
        for phrase in (
            "no-op",
            "no-edit",
            "no canonical Markdown change",
            "no Markdown edit",
            "no wiki change",
        )
    )


def test_external_semantic_worker_delegates_reanchor_to_supervisor() -> None:
    for skill_id in (
        "agent-docs",
        "doc-review",
        "usage-examples",
        "user-docs-author",
        "wiki-bootstrap",
        "wiki-semantic-enhance",
        "wiki-sync",
    ):
        manifest = _manifest(skill_id)
        assert "supervisor" in manifest
        assert "refresh" in manifest or "re-anchor" in manifest

    semantic = _manifest("wiki-semantic-enhance")
    normalized = " ".join(semantic.split())
    assert "The supervisor must accept the last semantic change" in normalized
    assert "run the owning sync/re-anchor" in normalized


def test_doc_review_splits_mutation_contract_before_any_sync_or_edit() -> None:
    manifest = _manifest("doc-review")
    reference = _reference("doc-review")
    mode_split = manifest.index("**Enter one mode before mutation.**")
    dry_run = manifest.index("llm-wiki sync --dry-run", mode_split)
    applied_sync = manifest.index(
        "apply the previewed deterministic `llm-wiki sync`", dry_run
    )
    final_sync = manifest.index(
        "llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki",
        applied_sync,
    )

    assert mode_split < dry_run < applied_sync < final_sync
    external = manifest[
        manifest.index("- **External `external_agent_docs`:**") : manifest.index(
            "2. **Collect review inputs.**"
        )
    ]
    assert "llm-wiki sync" not in external
    assert "only the packet-named review result" in external
    for forbidden in (
        "source",
        "adopted input wiki",
        "workspace wiki",
        "generated artifacts",
        "native ledgers",
    ):
        assert forbidden in external

    assert "Managed versus external mutation contract" in reference
    assert "Only the exact review-result path and ledger fields" in reference
    assert "Original finding IDs are immutable" in reference


def test_doc_review_maps_native_fact_classes_without_conflating_authority() -> None:
    manifest = _manifest("doc-review")
    reference = _reference("doc-review")
    normalized_manifest = " ".join(manifest.split()).lower()
    normalized_reference = " ".join(reference.split())

    for category in (
        "knowledge_projection",
        "knowledge_schema",
        "knowledge_snapshot",
        "knowledge_evidence",
        "knowledge_freshness",
        "knowledge_governance",
        "knowledge_review",
        "knowledge_verification",
    ):
        assert category in reference
    assert (
        "source is authoritative for observed code structure and behavior"
        in normalized_manifest
    )
    assert "trusted intake and explicit human decisions" in normalized_manifest
    assert "source-changed" in reference
    assert "not automatically false prose" in reference
    assert "Agent review" in normalized_reference
    assert (
        "does not author or satisfy a native human section review"
        in normalized_reference
    )


def test_bootstrap_keeps_locator_only_default_and_separately_confirms_governance() -> (
    None
):
    manifest = _manifest("wiki-bootstrap")
    reference = _reference("wiki-bootstrap")
    section = manifest[
        manifest.index(
            "## Optional governance adoption is a separate decision"
        ) : manifest.index("## Steps")
    ]
    normalized = " ".join(section.split())

    locator_only = section.index("Default bootstrap remains **locator-only**")
    confirmation = section.index("separate explicit owner confirmation")
    dry_run = section.index(
        "llm-wiki knowledge init --wiki-dir docs/llm_wiki --dry-run"
    )
    mutation = section.index(
        "llm-wiki knowledge init --wiki-dir docs/llm_wiki",
        dry_run + len("llm-wiki knowledge init --wiki-dir docs/llm_wiki --dry-run"),
    )
    assert locator_only < confirmation < dry_run < mutation
    assert "does not create durable UIDs, lifecycle, human review" in normalized
    assert "never an automatic repair" in normalized
    assert "restore that exact ledger from version control or backup" in normalized

    ownership = reference[
        reference.index("## Native artifact ownership and recovery") : reference.index(
            "## Validation expectations"
        )
    ]
    for artifact in (
        ".llm-wiki-manifest.json",
        ".llm-wiki-surface.json",
        ".llm-wiki-knowledge.json",
        ".llm-wiki-governance.json",
        ".llm-wiki-verification.json",
    ):
        assert artifact in ownership
    assert "non-rebuildable governance authority" in ownership
    assert "Disposable receipt" in ownership
    assert "cannot replace or recover the ledger" in ownership


def test_sync_documents_governed_move_preview_confirmation_mutation_order() -> None:
    manifest = _manifest("wiki-sync")
    topic = _managed_topic("governance.md")
    section = topic[
        topic.index("## Moves, aliases, and allocation conflicts") : topic.index(
            "## Lifecycle, review, and verification"
        )
    ]

    assert ".claude/skills/wiki-reference/references/governance.md" in manifest
    assert ".llm-wiki/skills/wiki-reference/references/governance.md" in manifest
    assert skills.SKILL_DEPENDENCIES["wiki-sync"] == (skills.REFERENCE_SKILL_ID,)

    filesystem_rename = section.index("filesystem/source rename")
    sync_preview = section.index("llm-wiki sync --dry-run", filesystem_rename)
    status = section.index("llm-wiki knowledge status", sync_preview)
    move_preview = section.index("llm-wiki knowledge move", status)
    dry_run = section.index("--dry-run", move_preview)
    confirmation = section.index("After the preview succeeds", dry_run)
    move_mutation = section.index("llm-wiki knowledge move", confirmation)
    owning_sync = section.index("llm-wiki sync --jobs 1", move_mutation)

    assert (
        filesystem_rename
        < sync_preview
        < status
        < move_preview
        < dry_run
        < confirmation
        < move_mutation
        < owning_sync
    )
    normalized = " ".join(topic.split())
    for required in (
        "retain old locator and natural-key coordinates as aliases",
        "Reject the implicit merge",
        "already owned by another UID is a hard conflict",
        "Source or page disappearance does not deprecate",
        "changed scope, evidence, basis",
        "Machine verification is separate and explicit",
        "restore the exact `.llm-wiki-governance.json`",
        "disposable projection and cannot recover or replace the ledger",
        "`projection: pending-sync`",
    ):
        assert required in normalized


def test_doc_review_hands_changed_native_review_scope_to_a_human() -> None:
    manifest = _manifest("doc-review")
    reference = _reference("doc-review")
    normalized = " ".join(f"{manifest}\n{reference}".split())

    for required in (
        "concept UID/current locator",
        "canonical page",
        "exact section locator",
        "prior event/state",
        "semantic diff",
        "evidence basis",
        "named human/governance owner",
        "Native human-review handoff",
    ):
        assert required in normalized
    assert "Do not author a replacement event" in normalized
    assert "cannot convert an agent result" in normalized
    assert (
        "Generated-only churn that leaves the semantic hash and evidence basis "
        "unchanged keeps a valid review"
    ) in normalized
    assert "machine verification are three separate records" in normalized


def test_doc_review_limits_infrastructure_semantics_to_notes() -> None:
    manifest = " ".join(_manifest("doc-review").split())
    reference = " ".join(_reference("doc-review").split())
    shared = schema.build_schema_content(
        "generic",
        "docs/llm_wiki",
        render_profile=schema.SchemaRenderProfile.EXPANDED_INLINE,
    )
    edit_targets = shared[
        shared.index("- Keep semantic edits surgical:") : shared.index(
            "- After the last canonical Markdown edit"
        )
    ]

    assert "incremental source observations" in manifest
    assert "single `## Notes` section is semantic" in manifest
    assert "every other section remains protected" in manifest
    assert "Infrastructure `## Notes` is the sole semantic section" in reference
    assert "unsupported custom headings are dropped" in reference
    assert "Infrastructure `## Notes` is the only supported semantic" in edit_targets
    assert "separate redacted infrastructure-review report" in " ".join(shared.split())


def test_shared_agent_instructions_include_native_preflight_and_final_reanchor() -> (
    None
):
    content = schema.build_schema_content(
        "generic",
        "docs/llm_wiki",
        render_profile=schema.SchemaRenderProfile.EXPANDED_INLINE,
    )

    assert "## Native knowledge preflight" in content
    assert (
        "ready` with live `current` means only unchanged since observation" in content
    )
    assert "ordinary exporter views" in content
    assert "knowledge init` is opt-in governance adoption" in content
    assert "trusted, unsandboxed project-local code" in content

    changed_code = content[content.index("## When you change code") :]
    semantic_edit = changed_code.index("Enrich new or generic affected pages")
    final_reanchor = changed_code.index(
        "After the last canonical Markdown edit", semantic_edit
    )
    quality_checks = changed_code.index("## Quality checks", final_reanchor)
    assert semantic_edit < final_reanchor < quality_checks


def test_generated_update_prompt_reanchors_after_semantic_pass_before_strict_lint(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "project"
    wiki_root = source_root / "docs" / "llm_wiki"
    source_root.mkdir()
    (source_root / "app.py").write_text("def changed(): ...\n", encoding="utf-8")
    prompt = generate_prompt_cmd._build_prompt(
        str(wiki_root),
        str(source_root),
        change_type="bugfix",
        diff_text="diff --git a/app.py b/app.py\n+def changed(): ...\n",
    )
    normalized = " ".join(prompt.split())
    semantic = prompt.index("## Semantic Pass")
    final_sync = prompt.index("llm-wiki sync --jobs 1", semantic)
    strict_lint = prompt.index("llm-wiki lint --strict --jobs 1", final_sync)

    assert semantic < final_sync < strict_lint
    assert "Final owning sync/re-anchor completed after semantic edits" in normalized
    assert "expired human section reviews" in normalized
    assert "stale machine-verification receipts" in normalized


def test_governed_semantic_edit_reanchors_and_preserves_valid_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "app.py").write_text(
        'class User:\n    """A documented user."""\n    pass\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / "docs" / "llm_wiki"
    bootstrap_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki),
            overwrite=False,
            depth="full",
            skip_workflows=True,
        )
    )
    capsys.readouterr()
    knowledge_cmd.run(
        cli._build_parser().parse_args(
            [
                "knowledge",
                "init",
                "--wiki-dir",
                str(wiki),
                "--bundle-id",
                "kb_native_skill_reanchor",
            ]
        )
    )
    capsys.readouterr()
    governed_state = load_knowledge_state(wiki)
    assert governed_state.knowledge is not None
    governed_knowledge = governed_state.knowledge
    pages = governed_knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
    user_sections = next(
        page["sections"]
        for page in pages
        if page["page_locator"] == "llm-wiki://entities/User"
    )
    description = next(
        section for section in user_sections if section["title"] == "Description"
    )
    governed_ledger = load_governance(wiki).ledger
    user_uid = next(
        uid
        for uid, allocation in governed_ledger.concepts.items()
        if allocation.locator == "llm-wiki://entities/User"
    )
    knowledge_cmd.run(
        cli._build_parser().parse_args(
            [
                "knowledge",
                "review",
                "--wiki-dir",
                str(wiki),
                "--uid",
                user_uid,
                "--section",
                description["locator"],
                "--reviewer-kind",
                "human",
                "--reviewer-id",
                "reviewer",
                "--method",
                "manual-review",
                "--method-version",
                "1",
                "--authored-at",
                "2026-07-27T12:00:00Z",
            ]
        )
    )
    capsys.readouterr()
    reviewed_ledger = load_governance(wiki).ledger
    review_event = next(iter(reviewed_ledger.review_events.values()))
    assert (
        evaluate_review_event(
            review_event,
            reviewed_ledger,
            governed_knowledge,
        ).reasons
        == ()
    )

    module = wiki / "modules" / "app.md"
    placeholder = "_Auto-generated from `app.py`._"
    authored = "Coordinates the documented user model."
    original = module.read_text(encoding="utf-8")
    assert placeholder in original
    module.write_text(original.replace(placeholder, authored), encoding="utf-8")

    before = lint_cmd.build_report(wiki, ".", strict=True)
    snapshot_issues = [
        issue for issue in before.issues if issue.category == "knowledge_snapshot"
    ]
    assert not before.passed
    assert snapshot_issues
    assert "markdown-snapshot-mismatch" in snapshot_issues[0].message

    sync_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki),
            jobs=1,
            no_cache=True,
        )
    )
    capsys.readouterr()

    assert authored in module.read_text(encoding="utf-8")
    after = lint_cmd.build_report(wiki, ".", strict=True)
    assert after.passed, after.by_category()
    reanchored = load_knowledge_state(wiki)
    assert reanchored.status is KnowledgeLoadState.VALID
    assert reanchored.knowledge is not None
    assert (
        evaluate_review_event(
            review_event,
            load_governance(wiki).ledger,
            reanchored.knowledge,
        ).reasons
        == ()
    )

    entity = wiki / "entities" / "User.md"
    entity_before = entity.read_text(encoding="utf-8")
    changed_reviewed_section = "Explains the user identity boundary."
    assert "A documented user." in entity_before
    entity.write_text(
        entity_before.replace("A documented user.", changed_reviewed_section),
        encoding="utf-8",
    )
    pre_expiry = lint_cmd.build_report(wiki, ".", strict=True)
    assert any(issue.category == "knowledge_snapshot" for issue in pre_expiry.issues)

    sync_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki),
            jobs=1,
            no_cache=True,
        )
    )
    capsys.readouterr()
    expired_state = load_knowledge_state(wiki)
    assert expired_state.status is KnowledgeLoadState.VALID
    assert expired_state.knowledge is not None
    assert changed_reviewed_section in entity.read_text(encoding="utf-8")
    assert evaluate_review_event(
        review_event,
        load_governance(wiki).ledger,
        expired_state.knowledge,
    ).reasons == ("scope-changed",)

    expired_lint = lint_cmd.build_report(wiki, ".", strict=True)
    expired_reviews = [
        issue for issue in expired_lint.issues if issue.category == "knowledge_review"
    ]
    assert expired_reviews
    assert "[reason=scope-changed]" in expired_reviews[0].message
