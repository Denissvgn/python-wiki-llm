"""Focused contracts for shared service-layer validation."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path, PurePosixPath

import pytest

from llm_wiki_cli.services import bootstrap_runtime
from llm_wiki_cli.services import (
    documentation_calibration_controller as calibration_controller,
)
from llm_wiki_cli.services import documentation_calibration
from llm_wiki_cli.services import (
    documentation_claim_evidence as claim_evidence,
)
from llm_wiki_cli.services import documentation_native
from llm_wiki_cli.services import documentation_queries
from llm_wiki_cli.services import documentation_review
from llm_wiki_cli.services import documentation_run
from llm_wiki_cli.services import documentation_worklist
from llm_wiki_cli.services import documentation_wiki_input as wiki_input
from llm_wiki_cli.services import infrastructure_sync
from llm_wiki_cli.services import knowledge_artifacts
from llm_wiki_cli.services import knowledge_envelope
from llm_wiki_cli.services import knowledge_evidence
from llm_wiki_cli.services import knowledge_freshness
from llm_wiki_cli.services import knowledge_governance
from llm_wiki_cli.services import knowledge_graph
from llm_wiki_cli.services import knowledge_index
from llm_wiki_cli.services import knowledge_links
from llm_wiki_cli.services import knowledge_model
from llm_wiki_cli.services import knowledge_projection
from llm_wiki_cli.services import mcp_server
from llm_wiki_cli.services import obsidian
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services import section_ownership
from llm_wiki_cli.services import site_export
from llm_wiki_cli.services import skills
from llm_wiki_cli.services import source_snapshot
from llm_wiki_cli.services import sync_manifest
from llm_wiki_cli.services import team
from llm_wiki_cli.services import verification_contracts
from llm_wiki_cli.services import wiki_surface
from llm_wiki_cli.services import wiki_surface_index
from llm_wiki_cli.services.documentation_calibration_controller import (
    P0CalibrationSchemaError,
)
from llm_wiki_cli.services.documentation_claim_evidence import (
    DocumentationClaimEvidenceError,
)
from llm_wiki_cli.services.documentation_run import DocumentationSchemaError
from llm_wiki_cli.services.documentation_review import DocumentationReviewError
from llm_wiki_cli.services.documentation_worklist import (
    DocumentationWorklistError,
)
from llm_wiki_cli.services.documentation_wiki_input import (
    DocumentationWikiInputError,
)
from llm_wiki_cli.services.knowledge_projection import KnowledgeProjectionError
from llm_wiki_cli.services.site_export import SiteExportError
from llm_wiki_cli.services.validation import (
    SharedValidationError,
    coerce_nonnegative_int,
    coerce_positive_int,
    contains_control_character,
    is_portable_relative_path,
    normalize_legacy_portable_relative_path,
    normalize_optional_portable_relative_path,
    path_is_in_top_level_directory,
    path_is_under,
    path_is_under_scope,
    path_is_within,
    paths_overlap,
    posix_path_text,
    require_int,
    require_mapping,
    require_nonempty_text,
    require_portable_relative_path,
    require_positive_int,
    require_repository_relative_path,
    require_sequence,
    require_string,
    require_trimmed_text,
    require_trimmed_text_list,
    resolved_paths_equal,
)


_REPOSITORY_PATH_ADAPTERS = (
    pytest.param(
        lambda value: sync_manifest._validate_repository_path(value, "field"),
        "field: ",
        id="sync-manifest",
    ),
    pytest.param(
        lambda value: source_snapshot._validate_repository_path(value, "field"),
        "field: ",
        id="source-snapshot",
    ),
    pytest.param(
        lambda value: knowledge_envelope._repository_relative_path(value, "field"),
        "field: ",
        id="knowledge-envelope",
    ),
    pytest.param(
        knowledge_evidence._validate_source_path,
        "source_path ",
        id="knowledge-evidence",
    ),
)


@pytest.mark.parametrize(
    "value",
    [
        "README.md",
        ".llm-wiki-docs/evidence/result.json",
        "docs/caf\u00e9 guide.md",
        "assets/usage/screenshot@2x.png",
    ],
)
def test_shared_portable_path_accepts_canonical_cross_platform_paths(
    value: str,
) -> None:
    assert require_portable_relative_path(value) == value
    assert is_portable_relative_path(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        ".",
        "../outside.md",
        "/absolute.md",
        r"C:\absolute.md",
        r"docs\relative.md",
        "docs//page.md",
        "docs/./page.md",
        "docs/page.md ",
        "docs/trailing./page.md",
        "docs/page.md:stream",
        "docs/COM\u00b9.md",
        "docs/cafe\u0301.md",
        "docs/page\x7f.md",
        "docs/\ud800.md",
    ],
)
def test_shared_portable_path_rejects_only_noncanonical_or_nonportable_input(
    value: str,
) -> None:
    with pytest.raises(SharedValidationError):
        require_portable_relative_path(value)
    assert is_portable_relative_path(value) is False


def test_shared_path_relationship_and_display_helpers() -> None:
    assert path_is_under("module/subpackage", "module") is True
    assert path_is_under("module2", "module") is False
    assert path_is_under("module", "") is False
    assert path_is_under_scope("\\module\\subpackage\\", "module") is True
    assert path_is_under_scope("any/path", "") is True

    root = Path("workspace")
    child = root / "docs"
    sibling = Path("other")
    assert path_is_within(root, root) is True
    assert path_is_within(child, root) is True
    assert path_is_within(sibling, root) is False
    assert paths_overlap(root, child) is True
    assert paths_overlap(child, sibling) is False
    assert path_is_in_top_level_directory(
        root / "legacy" / "old.md",
        root,
        "legacy",
    )
    assert not path_is_in_top_level_directory(
        root / "docs" / "page.md",
        root,
        "legacy",
    )
    assert resolved_paths_equal(Path("."), Path.cwd()) is True
    assert posix_path_text(r"docs\guide.md") == "docs/guide.md"
    assert contains_control_character("line\nbreak") is True
    assert contains_control_character("delete\x7f") is False
    assert (
        contains_control_character(
            "delete\x7f",
            reject_delete_character=True,
        )
        is True
    )


def test_observational_path_normalizer_keeps_only_safe_legacy_spelling() -> None:
    legacy = r" ./docs\guides\start.md "
    assert (
        normalize_optional_portable_relative_path(legacy)
        == "docs/guides/start.md"
    )
    assert documentation_calibration._portable_relative_path(legacy) == (
        "docs/guides/start.md"
    )

    for invalid in (
        "docs/CON.md",
        "docs/cafe\u0301.md",
        "../outside.md",
        ".//absolute.md",
    ):
        assert normalize_optional_portable_relative_path(invalid) is None
        assert documentation_calibration._portable_relative_path(invalid) is None


def test_protected_store_compatibility_can_explicitly_normalize_windows_spelling(
) -> None:
    assert (
        require_portable_relative_path(
            r"events\0001.json", normalize_backslashes=True
        )
        == "events/0001.json"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("./docs/guide.md", "docs/guide.md"),
        ("docs//guide.md", "docs/guide.md"),
        ("docs/./guide.md", "docs/guide.md"),
        ("docs/guide.md/", "docs/guide.md"),
    ],
)
def test_posix_spelling_normalization_requires_explicit_compatibility_mode(
    value: str,
    expected: str,
) -> None:
    with pytest.raises(SharedValidationError):
        require_portable_relative_path(value)
    assert (
        require_portable_relative_path(
            value,
            normalize_posix_spelling=True,
        )
        == expected
    )


def test_legacy_observational_normalizer_is_loose_only_before_strict_output(
) -> None:
    assert (
        normalize_legacy_portable_relative_path(
            r" ./docs\guides//./start.md/ "
        )
        == "docs/guides/start.md"
    )
    assert normalize_legacy_portable_relative_path(".//safe.md") == "safe.md"
    assert (
        normalize_legacy_portable_relative_path(
            ".//safe.md",
            reject_dot_prefixed_absolute=True,
        )
        is None
    )
    for invalid in (
        "../outside.md",
        "/absolute.md",
        "C:drive-relative.md",
        "docs/CON.md",
        "docs/cafe\u0301.md",
        "docs/page\x7f.md",
        "docs/\ud800.md",
    ):
        assert normalize_legacy_portable_relative_path(invalid) is None


@pytest.mark.parametrize(
    ("validator", "value", "expected"),
    [
        pytest.param(
            lambda value: knowledge_model._relative_path(value, "p"),
            None,
            "p: must be a string",
            id="model-type",
        ),
        pytest.param(
            lambda value: knowledge_model._relative_path(value, "p"),
            "\\absolute.md",
            "p: must be repository-relative",
            id="model-leading-backslash",
        ),
        pytest.param(
            lambda value: knowledge_model._relative_path(value, "p"),
            r"docs\page.md",
            "p: must use POSIX '/' separators",
            id="model-separator",
        ),
        pytest.param(
            lambda value: knowledge_model._relative_path(value, "p"),
            "docs/../page.md",
            "p: must be normalized without empty or dot segments",
            id="model-traversal",
        ),
        pytest.param(
            lambda value: knowledge_index._relative_path(value, "p"),
            None,
            "p: must be a non-empty normalized string",
            id="index-type",
        ),
        pytest.param(
            lambda value: knowledge_index._relative_path(value, "p"),
            "C:drive-relative.md",
            "p: must be repository-relative",
            id="index-drive-relative",
        ),
        pytest.param(
            lambda value: knowledge_index._relative_path(value, "p"),
            "\\\\server\\page.md",
            "p: must use POSIX '/' separators",
            id="index-unc",
        ),
        pytest.param(
            lambda value: knowledge_index._relative_path(value, "p"),
            "docs//page.md",
            "p: must be a normalized path without empty or dot segments",
            id="index-normalization",
        ),
        pytest.param(
            lambda value: knowledge_graph._relative_path(value, "p"),
            "\x7f",
            (
                "p: must be a non-empty normalized string without "
                "control characters"
            ),
            id="graph-control",
        ),
        pytest.param(
            lambda value: knowledge_graph._relative_path(value, "p"),
            "/absolute.md",
            "p: must be a repository-relative POSIX path",
            id="graph-absolute",
        ),
        pytest.param(
            lambda value: knowledge_graph._relative_path(value, "p"),
            "docs/../page.md",
            "p: must be a normalized relative path",
            id="graph-traversal",
        ),
        pytest.param(
            lambda value: knowledge_governance._relative_path(value, "p"),
            "docs//\npage.md",
            "p: must be a normalized relative path",
            id="governance-structure-before-control",
        ),
        pytest.param(
            lambda value: knowledge_governance._relative_path(value, "p"),
            "docs/\npage.md",
            "p: must not contain control characters",
            id="governance-control",
        ),
        pytest.param(
            lambda value: knowledge_links._canonical_relative_path(value, "p"),
            None,
            "p: must be a non-empty string",
            id="links-type",
        ),
        pytest.param(
            lambda value: knowledge_links._canonical_relative_path(value, "p"),
            "docs/page\x7f.md",
            "p: must be a repository-relative POSIX path",
            id="links-control",
        ),
        pytest.param(
            lambda value: knowledge_links._canonical_relative_path(value, "p"),
            "docs/./page.md",
            "p: must be normalized without empty or dot segments",
            id="links-normalization",
        ),
        pytest.param(
            lambda value: knowledge_freshness._validate_source_path(value, "p"),
            None,
            "p: must contain non-empty string source paths",
            id="freshness-type",
        ),
        pytest.param(
            lambda value: knowledge_freshness._validate_source_path(value, "p"),
            "docs/page\x7f.md",
            (
                "p: contains unsafe repository-relative source path "
                "'docs/page\\x7f.md'"
            ),
            id="freshness-control",
        ),
    ],
)
def test_migrated_path_adapters_preserve_exact_legacy_diagnostics(
    validator: Callable[[object], object],
    value: object,
    expected: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        validator(value)
    assert str(raised.value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("./docs/guide.md", "docs/guide.md"),
        ("docs//guide.md", "docs/guide.md"),
        ("docs/./guide.md", "docs/guide.md"),
        ("docs/guide.md/", "docs/guide.md"),
    ],
)
def test_graph_relative_path_preserves_legacy_posix_normalization(
    value: str,
    expected: str,
) -> None:
    assert knowledge_graph._relative_path(value, "p") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (r" docs\guide.md ", "docs/guide.md"),
        ("./docs/guide.md", "docs/guide.md"),
        ("docs//guide.md", "docs/guide.md"),
        ("docs/./guide.md", "docs/guide.md"),
        ("docs/guide.md/", "docs/guide.md"),
    ],
)
def test_observational_adapters_preserve_safe_legacy_normalization(
    value: str,
    expected: str,
) -> None:
    assert (
        documentation_queries._normalise_source_path(
            value,
            field="p",
            required=True,
        )
        == expected
    )
    assert documentation_worklist._normalise_relative_path(value) == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (None, "p must be a non-empty string."),
        ("/absolute.md", "p must be a relative source path."),
        ("docs/../page.md", "p must not contain '..'."),
        (".", "p must be a source file path."),
        ("docs/CON.md", "p must be a relative source path."),
    ],
)
def test_documentation_query_path_preserves_required_diagnostic_tiers(
    value: object,
    message: str,
) -> None:
    with pytest.raises(documentation_queries.DocumentationQueryError) as raised:
        documentation_queries._normalise_source_path(
            value,
            field="p",
            required=True,
        )
    assert str(raised.value) == message
    assert (
        documentation_queries._normalise_source_path(
            value,
            field="p",
            required=False,
        )
        is None
    )


def test_worklist_path_normalizer_rejects_legacy_absolute_escape_outputs(
) -> None:
    assert documentation_worklist._normalise_relative_path(".//page.md") is None
    assert documentation_worklist._normalise_relative_path("./C:/page.md") is None


@pytest.mark.parametrize(
    "value",
    [
        "docs/CON.md",
        "docs/cafe\u0301.md",
        "docs/trailing./page.md",
        "docs/page.md:stream",
        "docs/page*.md",
        "docs/page\x7f.md",
        "docs/\ud800.md",
    ],
)
def test_all_migrated_path_adapters_reject_only_cross_platform_hazards(
    value: str,
) -> None:
    raising_adapters = (
        lambda: knowledge_model._relative_path(value, "p"),
        lambda: knowledge_index._relative_path(value, "p"),
        lambda: knowledge_graph._relative_path(value, "p"),
        lambda: knowledge_governance._relative_path(value, "p"),
        lambda: knowledge_links._canonical_relative_path(value, "p"),
        lambda: knowledge_freshness._validate_source_path(value, "p"),
        lambda: documentation_queries._normalise_source_path(
            value,
            field="p",
            required=True,
        ),
    )
    for adapter in raising_adapters:
        with pytest.raises(ValueError):
            adapter()

    assert knowledge_artifacts._is_safe_relative_path(value) is False
    assert infrastructure_sync._valid_repository_path(value) is False
    assert documentation_worklist._normalise_relative_path(value) is None
    assert (
        documentation_queries._normalise_source_path(
            value,
            field="p",
            required=False,
        )
        is None
    )


def test_all_migrated_path_adapters_accept_canonical_portable_input() -> None:
    value = "docs/caf\u00e9 guide.md"
    assert knowledge_model._relative_path(value, "p") == value
    assert knowledge_index._relative_path(value, "p") == value
    assert knowledge_graph._relative_path(value, "p") == value
    assert knowledge_governance._relative_path(value, "p") == value
    assert knowledge_links._canonical_relative_path(value, "p") == value
    assert knowledge_freshness._validate_source_path(value, "p") is None
    assert knowledge_artifacts._is_safe_relative_path(value) is True
    assert infrastructure_sync._valid_repository_path(value) is True
    assert documentation_worklist._normalise_relative_path(value) == value
    assert (
        documentation_queries._normalise_source_path(
            value,
            field="p",
            required=True,
        )
        == value
    )


def test_infrastructure_path_predicate_preserves_legacy_type_boundary() -> None:
    with pytest.raises(TypeError):
        infrastructure_sync._valid_repository_path(None)  # type: ignore[arg-type]


@pytest.mark.parametrize(("validator", "prefix"), _REPOSITORY_PATH_ADAPTERS)
@pytest.mark.parametrize(
    ("value", "message"),
    [
        (None, "must be a non-empty repository-relative path"),
        ("", "must be a non-empty repository-relative path"),
        (" docs/page.md", "must be a repository-relative POSIX path"),
        ("docs/\npage.md", "must be a repository-relative POSIX path"),
        ("/docs/page.md", "must be a repository-relative POSIX path"),
        ("C:docs/page.md", "must be a repository-relative POSIX path"),
        (r"docs\page.md", "must be a repository-relative POSIX path"),
        ("docs//page.md", "must be a normalized repository-relative path"),
        ("docs/../page.md", "must be a normalized repository-relative path"),
    ],
)
def test_repository_path_adapters_preserve_exact_legacy_diagnostic_tiers(
    validator: Callable[[object], object],
    prefix: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        validator(value)
    assert str(raised.value) == f"{prefix}{message}"


@pytest.mark.parametrize(("validator", "prefix"), _REPOSITORY_PATH_ADAPTERS)
@pytest.mark.parametrize(
    "value",
    [
        "docs/CON.md",
        "docs/cafe\u0301.md",
        "docs/trailing./page.md",
        "docs/page.md:stream",
    ],
)
def test_repository_path_adapters_reject_cross_platform_hazards(
    validator: Callable[[object], object],
    prefix: str,
    value: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        validator(value)
    assert str(raised.value) == (
        f"{prefix}must be a normalized repository-relative path"
    )


def test_repository_path_shared_helper_can_use_a_portability_diagnostic() -> None:
    assert (
        require_repository_relative_path(
            "docs/caf\u00e9 guide.md",
            text_error=ValueError("text"),
            posix_error=ValueError("posix"),
            normalized_error=ValueError("normalized"),
            portability_error=ValueError("portable"),
        )
        == "docs/caf\u00e9 guide.md"
    )
    with pytest.raises(ValueError, match=r"^portable$"):
        require_repository_relative_path(
            "docs/CON.md",
            text_error=ValueError("text"),
            posix_error=ValueError("posix"),
            normalized_error=ValueError("normalized"),
            portability_error=ValueError("portable"),
        )


def test_shared_scalar_rules_reject_python_and_json_edge_cases() -> None:
    error = ValueError("invalid")

    assert require_trimmed_text("value", error=error) == "value"
    assert require_trimmed_text_list(["one", "two"], error=error) == [
        "one",
        "two",
    ]
    assert require_mapping({"key": "value"}, error=error, require_string_keys=True)
    assert require_positive_int(1, invalid_error=error) == 1

    for invalid_text in ("", " value", "value\ninjected"):
        with pytest.raises(ValueError, match="invalid"):
            require_trimmed_text(invalid_text, error=error)
    with pytest.raises(ValueError, match="invalid"):
        require_trimmed_text_list(
            ["duplicate", "duplicate"],
            error=error,
            reject_duplicates=True,
        )
    with pytest.raises(ValueError, match="invalid"):
        require_mapping({1: "value"}, error=error, require_string_keys=True)
    for invalid_integer in (True, 0, -1, 1.0):
        with pytest.raises(ValueError, match="invalid"):
            require_positive_int(invalid_integer, invalid_error=error)


def test_shared_sequence_string_and_coercive_integer_policies_are_explicit() -> None:
    error = ValueError("invalid")

    assert require_string("", error=error) == ""
    assert require_int(-1, error=error) == -1
    assert (
        require_nonempty_text(
            " padded ",
            error=error,
            normalize=True,
            reject_control_characters=False,
        )
        == "padded"
    )
    assert require_sequence((1, 2), error=error) == (1, 2)
    assert require_trimmed_text_list(
        (" padded ", "\ncontrol"),
        error=error,
        require_trimmed_items=False,
        reject_control_characters=False,
        container_type=tuple,
    ) == [" padded ", "\ncontrol"]
    assert coerce_nonnegative_int("0", error=error) == 0
    assert coerce_positive_int(1.9, error=error) == 1

    for invalid in (None, 1, b"text"):
        with pytest.raises(ValueError, match="invalid"):
            require_string(invalid, error=error)
    for invalid in (True, 1.0, "1"):
        with pytest.raises(ValueError, match="invalid"):
            require_int(invalid, error=error)
    for invalid in (None, "", " \t "):
        with pytest.raises(ValueError, match="invalid"):
            require_nonempty_text(invalid, error=error, normalize=True)
    for invalid in ("text", b"text", {"item": 1}):
        with pytest.raises(ValueError, match="invalid"):
            require_sequence(invalid, error=error)
    for invalid in (True, "-1", object()):
        with pytest.raises(ValueError, match="invalid"):
            coerce_nonnegative_int(invalid, error=error)
    for invalid in (False, "0", object()):
        with pytest.raises(ValueError, match="invalid"):
            coerce_positive_int(invalid, error=error)


@pytest.mark.parametrize(
    ("validator", "error_type"),
    [
        (knowledge_graph._nonnegative_int, knowledge_graph.KnowledgeGraphError),
        (
            knowledge_governance._nonnegative_int,
            knowledge_governance.GovernanceError,
        ),
        (
            knowledge_artifacts._nonnegative_integer,
            knowledge_artifacts.KnowledgeArtifactError,
        ),
        (
            verification_contracts._nonnegative_int,
            verification_contracts.VerificationReceiptError,
        ),
    ],
)
@pytest.mark.parametrize("value", [True, -1, 1.0, "0", None])
def test_nonnegative_integer_adapters_preserve_domain_diagnostics(
    validator: Callable[[object, str], int],
    error_type: type[ValueError],
    value: object,
) -> None:
    assert validator(0, "record.total") == 0

    with pytest.raises(error_type) as raised:
        validator(value, "record.total")
    assert getattr(raised.value, "field") == "record.total"
    assert getattr(raised.value, "message") == "must be a non-negative integer"
    assert str(raised.value) == "record.total: must be a non-negative integer"


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "1", None])
def test_knowledge_graph_positive_integer_adapter_preserves_diagnostic(
    value: object,
) -> None:
    with pytest.raises(knowledge_graph.KnowledgeGraphError) as raised:
        knowledge_graph._positive_int(value, "graph.limit")
    assert str(raised.value) == "graph.limit: must be a positive integer"
    assert knowledge_graph._positive_int(1, "graph.limit") == 1


@pytest.mark.parametrize(
    ("validator", "expected"),
    [
        (
            lambda: knowledge_graph._only_fields(
                {"unknown": True},
                "record",
                {"required"},
                required={"required"},
            ),
            "record.unknown: unknown field",
        ),
        (
            lambda: knowledge_governance._exact_fields(
                {"unknown": True},
                "record",
                {"required"},
            ),
            "record.required: is required",
        ),
        (
            lambda: knowledge_artifacts._validate_surface_keys(
                {"unknown": True},
                "record",
                {"required"},
                set(),
            ),
            "record.required: is required",
        ),
        (
            lambda: verification_contracts._exact_fields(
                {"unknown": True},
                "record",
                {"required"},
            ),
            "record.required: is required",
        ),
    ],
)
def test_exact_field_adapters_preserve_missing_unknown_precedence(
    validator: Callable[[], None],
    expected: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        validator()
    assert str(raised.value) == expected


@pytest.mark.parametrize(
    ("validator", "expected"),
    [
        (
            lambda: knowledge_graph._object([], "record"),
            "record: must be an object",
        ),
        (
            lambda: knowledge_graph._object({1: True}, "record"),
            "record: object keys must be strings",
        ),
        (
            lambda: knowledge_graph._array((), "record"),
            "record: must be an array",
        ),
        (
            lambda: knowledge_graph._enum("other", ("one", "two"), "record"),
            "record: must be one of 'one', 'two'",
        ),
        (
            lambda: knowledge_graph._name("name\x7f", "record"),
            "record: must be a non-empty normalized string without control "
            "characters",
        ),
        (
            lambda: knowledge_graph._hash("sha256:INVALID", "record"),
            "record: must be a sha256: digest",
        ),
        (
            lambda: knowledge_governance._object({1: True}, "record"),
            "record: must use string keys",
        ),
        (
            lambda: knowledge_governance._array((), "record"),
            "record: must be an array",
        ),
        (
            lambda: knowledge_governance._hash("sha256:INVALID", "record"),
            "record: must be a canonical SHA-256 value",
        ),
        (
            lambda: verification_contracts._sha256("invalid", "record"),
            "record must be a canonical lowercase SHA-256 value",
        ),
        (
            lambda: verification_contracts._object({1: True}, "record"),
            "record: must use string keys",
        ),
        (
            lambda: verification_contracts._array((), "record"),
            "record: must be an array",
        ),
        (
            lambda: verification_contracts._string(1, "record"),
            "record: must be a string",
        ),
        (
            lambda: sync_manifest._mapping_value({1: True}, "record"),
            "record: must use string keys",
        ),
        (
            lambda: section_ownership._section_array({}, "record"),
            "record: must be an array",
        ),
        (
            lambda: section_ownership._section_string("", "record"),
            "record: must be a non-empty string",
        ),
        (
            lambda: section_ownership._section_hash("invalid", "record"),
            "record: must be a sha256 content hash",
        ),
        (
            lambda: section_ownership._section_int(True, "record", minimum=0),
            "record: must be an integer >= 0",
        ),
        (
            lambda: team._reject_unknown_keys(
                {"z": True, "a": True}, set(), "team config"
            ),
            "team config contains unknown key(s): a, z",
        ),
    ],
)
def test_shared_scalar_adapters_preserve_domain_diagnostics(
    validator: Callable[[], object],
    expected: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        validator()
    assert str(raised.value) == expected


def test_projection_validation_adapters_preserve_domain_diagnostics() -> None:
    with pytest.raises(KnowledgeProjectionError) as raised:
        knowledge_projection._require_exact_fields(
            {"known": True, "unknown": True},
            "projection",
            {"known", "missing"},
        )
    assert raised.value.code == "projection-shape-invalid"
    assert raised.value.field == "projection.unknown"
    assert raised.value.message == "is not an allowed field"

    with pytest.raises(KnowledgeProjectionError) as raised:
        knowledge_projection._require_positive_int(-1, "projection.limit")
    assert raised.value.field == "projection.limit"
    assert raised.value.message == "must be a non-negative integer"

    with pytest.raises(KnowledgeProjectionError) as raised:
        knowledge_projection._require_relative_path(
            "docs/CON.md", "projection.canonical_path"
        )
    assert raised.value.field == "projection.canonical_path"
    assert raised.value.message == "must be a normalized repository-relative path"


def test_review_validation_adapters_preserve_normalization_and_messages() -> None:
    assert documentation_review._required_json_text(" padded ", "field") == "padded"
    assert documentation_review._required_string_list(
        [" padded ", "\ncontrol"],
        "items",
    ) == (" padded ", "\ncontrol")
    assert documentation_review._positive_int("2", "count") == 2
    assert documentation_review._non_negative_int(1.9, "count") == 1

    with pytest.raises(
        DocumentationReviewError,
        match=r"record is missing required fields: missing\.",
    ):
        documentation_review._require_exact_fields(
            {"known": True},
            frozenset({"known", "missing"}),
            "record",
        )
    with pytest.raises(
        DocumentationReviewError,
        match=r"count must be a positive integer\.",
    ):
        documentation_review._required_positive_int(True, "count")
    with pytest.raises(
        DocumentationReviewError,
        match=r"record contains unsupported fields: 1\.",
    ):
        documentation_review._require_exact_fields(
            {"known": True, 1: True},  # type: ignore[dict-item]
            frozenset({"known"}),
            "record",
        )


def test_worklist_and_site_validation_adapters_preserve_public_errors() -> None:
    assert documentation_worklist._require_non_negative_int(0, "p1_budget") is None
    with pytest.raises(
        DocumentationWorklistError,
        match=r"max_context_entries must be a positive integer\.",
    ):
        documentation_worklist._require_positive_int(0, "max_context_entries")

    assert site_export._require_digest("", "knowledge_hash", allow_empty=True) == ""
    with pytest.raises(
        SiteExportError,
        match=r"Publication receipt knowledge_hash must be a SHA-256 digest\.",
    ):
        site_export._require_digest("SHA256:" + ("0" * 64), "knowledge_hash")


def test_documentation_run_uses_strict_canonical_paths_and_preserves_message() -> None:
    for invalid in (r"docs\page.md", "docs/COM\u00b9.md", "docs/cafe\u0301.md"):
        with pytest.raises(DocumentationSchemaError) as raised:
            documentation_run._portable_path(invalid)
        assert str(raised.value).startswith("path ")
        assert repr(invalid) in str(raised.value)


def test_documentation_run_validates_paths_before_collision_keys() -> None:
    with pytest.raises(DocumentationSchemaError) as raised:
        documentation_run._portable_path_tuple(["../outside.md", "../outside.md"])
    assert str(raised.value) == (
        "path must be a non-empty workspace-relative portable path: "
        "'../outside.md'"
    )


def test_claim_evidence_path_adapter_preserves_its_error_contract() -> None:
    with pytest.raises(
        DocumentationClaimEvidenceError,
        match=r"capture_path must be a portable repository-relative path\.",
    ):
        claim_evidence._portable_path("assets/usage/cafe\u0301.png", "capture_path")


def test_calibration_path_adapter_rejects_noncanonical_wire_separator() -> None:
    with pytest.raises(
        P0CalibrationSchemaError,
        match=r"artifact path is not portable:",
    ):
        calibration_controller._portable_relative_path(
            r"evidence\result.json",
            label="artifact path",
        )


@pytest.mark.parametrize(
    ("validator", "value", "expected"),
    [
        (
            lambda value: calibration_controller._require_choice(
                value, {"accepted"}, "status"
            ),
            "accepted\x00",
            "status must be one of: accepted.",
        ),
        (
            lambda value: calibration_controller._require_sha256(
                value, "digest"
            ),
            "sha256:" + ("0" * 64) + "\x00",
            "digest must be a lowercase sha256 digest.",
        ),
        (
            lambda value: calibration_controller._require_uuid(value, "id"),
            "00000000-0000-0000-0000-000000000000\x00",
            "id must be a UUID.",
        ),
    ],
)
def test_calibration_closed_validators_preserve_control_character_diagnostics(
    validator: Callable[[str], str],
    value: str,
    expected: str,
) -> None:
    with pytest.raises(P0CalibrationSchemaError) as raised:
        validator(value)
    assert str(raised.value) == expected


def test_calibration_timestamp_rejects_control_separator_as_invalid_iso() -> None:
    # ``datetime.fromisoformat`` accepts any one-character date/time separator.
    # The protocol does not: an embedded control is newly rejected as invalid.
    assert (
        calibration_controller._require_timestamp(
            "2026-07-31T12:30:00Z",
            "issued_at",
        )
        == "2026-07-31T12:30:00Z"
    )
    with pytest.raises(
        P0CalibrationSchemaError,
        match=r"^issued_at is not an ISO timestamp\.$",
    ):
        calibration_controller._require_timestamp(
            "2026-07-31\x0012:30:00Z",
            "issued_at",
        )


def test_wiki_input_path_adapter_rejects_single_non_nfc_entry() -> None:
    with pytest.raises(
        DocumentationWikiInputError,
        match="Wiki path is not NFC-normalized",
    ) as raised:
        wiki_input._validate_portable_relative_path(
            PurePosixPath("docs/cafe\u0301.md"),
            {},
        )
    assert raised.value.category == "nonportable_path"


@pytest.mark.parametrize(
    "value",
    [
        "../outside.py",
        "/absolute.py",
        "C:drive.py",
        "docs/CON.py",
        "docs/cafe\u0301.py",
        "docs/page.py:stream",
        "docs/page\x7f.py",
    ],
)
def test_remaining_path_adapters_reject_cross_platform_hazards(
    value: str,
) -> None:
    assert documentation_native._is_safe_relative_posix_path(value) is False
    assert wiki_surface_index._safe_source_path(value, Path(".")) is None
    with pytest.raises(
        mcp_server.McpWikiError,
        match=r"^Unsafe source path:",
    ):
        mcp_server._normalise_source_path(value)
    with pytest.raises(
        obsidian.ObsidianError,
        match=r"^Unsafe expected Obsidian mirror path:",
    ):
        obsidian._validate_mirror_scan_relative_path(value)


def test_remaining_path_adapters_preserve_canonical_and_legacy_boundaries(
    tmp_path: Path,
) -> None:
    canonical = "docs/caf\u00e9-guide.py"
    assert documentation_native._is_safe_relative_posix_path(canonical) is True
    assert wiki_surface_index._safe_source_path(canonical, tmp_path) == canonical
    assert mcp_server._normalise_source_path(canonical) == canonical
    assert obsidian._validate_mirror_scan_relative_path(canonical) == canonical

    absolute_inside = tmp_path / canonical
    assert (
        wiki_surface_index._safe_source_path(str(absolute_inside), tmp_path)
        == canonical
    )
    assert (
        wiki_surface_index._safe_source_path(r"docs\legacy.py", tmp_path)
        == "docs/legacy.py"
    )
    assert (
        documentation_native._is_safe_relative_posix_path(
            "docs/page.MD",
            required_suffix=".md",
        )
        is False
    )


def test_review_paths_keep_legacy_observational_values_without_authority() -> None:
    assert documentation_review._normalise_paths(
        [
            " /absolute.py ",
            "../outside.py",
            r".\docs\page.py",
            "",
        ]
    ) == (
        "../outside.py",
        "/absolute.py",
        "docs/page.py",
    )


@pytest.mark.parametrize(
    ("joiner", "error_type"),
    [
        (obsidian._safe_join, obsidian.ObsidianError),
        (site_export._safe_join, site_export.SiteExportError),
    ],
)
def test_shared_safe_join_adapters_reject_escape_and_portability_hazards(
    tmp_path: Path,
    joiner: Callable[[Path, str], Path],
    error_type: type[Exception],
) -> None:
    assert joiner(tmp_path, "docs/page.md") == tmp_path / "docs/page.md"
    for invalid in ("../outside.md", "/absolute.md", "docs/CON.md"):
        with pytest.raises(error_type):
            joiner(tmp_path, invalid)


def test_plugin_component_paths_require_portable_existing_files(
    tmp_path: Path,
) -> None:
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    (plugin_dir / "valid.md").write_text("valid", encoding="utf-8")
    (plugin_dir / "CON").write_text("reserved", encoding="utf-8")

    assert plugins._safe_component_path(plugin_dir, "valid.md", "path") == (
        "valid.md"
    )
    with pytest.raises(
        plugins.PluginError,
        match=r"^path must be a relative file path\.$",
    ):
        plugins._safe_component_path(plugin_dir, "CON", "path")


@pytest.mark.parametrize(
    "page_id",
    ["CON", "aux", "LPT1", "COM\u00b9", "trailing."],
)
def test_wiki_page_ids_reject_reserved_or_nonportable_components(
    page_id: str,
) -> None:
    assert wiki_surface.is_safe_page_id(page_id) is False


@pytest.mark.parametrize(
    "value",
    ["CON", "aux", "LPT1", "COM\u00b9", "trailing.", "two..dots"],
)
def test_page_component_generators_share_portable_output(value: str) -> None:
    bootstrap_value = bootstrap_runtime._safe_page_component(value)
    manifest_value = sync_manifest._safe_page_component(value)

    assert bootstrap_value == manifest_value
    assert wiki_surface.is_safe_page_id(bootstrap_value) is True


def test_directory_guard_adapters_preserve_domain_diagnostics(
    tmp_path: Path,
) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    assert obsidian._validate_existing_dir(existing, "wiki") is None
    assert site_export._validate_existing_dir(existing, "wiki") is None

    missing = tmp_path / "missing"
    with pytest.raises(
        obsidian.ObsidianError,
        match=r"^wiki does not exist or is not a directory:",
    ):
        obsidian._validate_existing_dir(missing, "wiki")
    with pytest.raises(
        site_export.SiteExportError,
        match=r"^wiki does not exist or is not a directory:",
    ):
        site_export._validate_existing_dir(missing, "wiki")
    with pytest.raises(skills.SkillsError, match="Invalid destination directory"):
        skills._ensure_safe_base(Path("."))
