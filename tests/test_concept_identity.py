"""Focused contract tests for pure durable concept identity."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from llm_wiki_cli.services.concept_identity import (
    AliasType,
    ConceptAllocation,
    ConceptIdentityError,
    ConceptReference,
    IdentityAlias,
    IdentityCollision,
    IdentityCollisionError,
    IdentityUpdate,
    add_identity_alias,
    aliases_for_move,
    allocate_concept,
    derive_concept_uid,
    find_identity_collisions,
    identity_coordinate_key,
    move_allocation,
    validate_alias_value,
    validate_bundle_id,
    validate_concept_kind,
    validate_concept_uid,
    validate_identity_registry,
    validate_locator,
    validate_natural_key,
)


def _module_reference(
    *,
    locator: str = "llm-wiki://modules/core",
    natural_key: str = "module:src/pkg/core.py",
) -> ConceptReference:
    return ConceptReference(
        locator=locator,
        concept_kind="source-module",
        natural_key=natural_key,
    )


def _module_allocation(
    *,
    bundle_id: str = "bundle:project-1",
    locator: str = "llm-wiki://modules/core",
    natural_key: str = "module:src/pkg/core.py",
) -> ConceptAllocation:
    reference = _module_reference(locator=locator, natural_key=natural_key)
    return ConceptAllocation(
        uid=derive_concept_uid(
            bundle_id,
            reference.concept_kind,
            reference.natural_key,
        ),
        concept_kind=reference.concept_kind,
        natural_key=reference.natural_key,
        locator=reference.locator,
    )


def test_records_validate_normalize_alias_enum_and_are_immutable():
    reference = _module_reference()
    allocation = _module_allocation()
    alias = IdentityAlias("locator", "modules/old_core.md", allocation.uid)

    assert reference.locator == "llm-wiki://modules/core"
    assert allocation.reference == reference
    assert alias.alias_type is AliasType.LOCATOR
    with pytest.raises(FrozenInstanceError):
        allocation.locator = "modules/other.md"  # type: ignore[misc]


def test_uid_derivation_is_domain_separated_deterministic_and_byte_stable():
    uid = derive_concept_uid(
        "bundle:project-1",
        "source-module",
        "module:src/pkg/core.py",
    )

    assert uid == "lw:module:5c00fce982315d200afd5b8e015a0c75"
    assert (
        derive_concept_uid(
            "bundle:project-1",
            "source-module",
            "module:src/pkg/core.py",
        )
        == uid
    )
    assert (
        derive_concept_uid(
            "bundle:project-2",
            "source-module",
            "module:src/pkg/core.py",
        )
        != uid
    )
    assert (
        derive_concept_uid(
            "bundle:project-1",
            "source-module",
            "module:src/pkg/other.py",
        )
        != uid
    )
    assert (
        derive_concept_uid(
            "bundle:project-1",
            "example.com/custom",
            "custom:item-1",
        ).startswith("lw:concept:")
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        " unknown ",
        "unknown",
        "/private/checkout",
        r"C:\private\checkout",
        "https://user:secret@example.test/repo",
        "bundle id",
        "bundle:\u200bhidden",
    ],
)
def test_bundle_id_rejects_machine_local_credential_and_unsafe_values(value):
    with pytest.raises(ConceptIdentityError) as caught:
        validate_bundle_id(value)
    assert caught.value.field == "bundle_id"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "Source Module",
        "source_module",
        "source-module!",
        "custom-unqualified",
        "namespace/",
        "../source-module",
        "source-\u200bmodule",
    ],
)
def test_concept_kind_rejects_prose_and_unsafe_values(value):
    with pytest.raises(ConceptIdentityError) as caught:
        validate_concept_kind(value)
    assert caught.value.field == "concept_kind"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "this is explanatory prose",
        "module:/absolute/core.py",
        "module:C:/absolute/core.py",
        r"module:src\core.py",
        "module:src/../core.py",
        "module:src//core.py",
        "module:https://user:secret@example.test/core.py",
        "module:file:/etc/passwd",
        "module:user:secret@example.test/repo",
        "module:git@example.test/repo",
        "module:src/%2fcore.py",
        "module:src/%GGcore.py",
        "module:%41",
        "module:src%2Fcore.py",
        "module:src/%20core.py",
        "module:src/\u200bcore.py",
        "Module:src/core.py",
        "module:src/core.py?",
        "module:src/core.py;drop",
    ],
)
def test_natural_key_rejects_absolute_credential_control_and_prose_values(value):
    with pytest.raises(ConceptIdentityError) as caught:
        validate_natural_key(value)
    assert caught.value.field == "natural_key"


def test_natural_key_accepts_occurrence_fragments_and_canonical_utf8_escapes():
    assert (
        validate_natural_key("entity:src/models.py#User@2")
        == "entity:src/models.py#User@2"
    )
    assert validate_natural_key("entity:src/models.py#%C3%89tat") == (
        "entity:src/models.py#%C3%89tat"
    )


@pytest.mark.parametrize(
    "value",
    [
        "/tmp/wiki/modules/core.md",
        r"C:\wiki\modules\core.md",
        "llm-wiki://user:secret@modules/core",
        "llm-wiki://modules/core?secret=x",
        "llm-wiki://modules/../core",
        "modules/core.md#section",
        "modules/core two.md",
        " modules/core.md",
    ],
)
def test_locator_rejects_absolute_credentials_and_noncanonical_routes(value):
    with pytest.raises(ConceptIdentityError) as caught:
        validate_locator(value)
    assert caught.value.field == "locator"


def test_locator_accepts_both_canonical_coordinate_forms():
    assert validate_locator("modules/core.md") == "modules/core.md"
    assert validate_locator("llm-wiki://modules/core") == (
        "llm-wiki://modules/core"
    )


def test_path_and_resource_uri_share_one_locator_ownership_coordinate():
    assert identity_coordinate_key("locator", "modules/core.md") == (
        "llm-wiki://modules/core"
    )
    first = _module_allocation(locator="llm-wiki://modules/core")
    second = _module_allocation(
        bundle_id="bundle:project-2",
        locator="modules/core.md",
        natural_key="module:src/other.py",
    )
    collisions = find_identity_collisions((first, second))
    assert [collision.code for collision in collisions] == [
        "locator-collision"
    ]

    alias = IdentityAlias("locator", "modules/core.md", second.uid)
    codes = {
        collision.code
        for collision in find_identity_collisions((first, second), (alias,))
    }
    assert "alias-current-collision" in codes


@pytest.mark.parametrize(
    "value",
    [
        "",
        "lw:module:ABCDEF0123456789ABCDEF0123456789",
        "lw:module:abcd",
        "module:0123456789abcdef0123456789abcdef",
        "lw:source-module:0123456789abcdef0123456789abcdef/extra",
        "lw:module:0123456789abcdef0123456789abcdef\n",
    ],
)
def test_persisted_uid_validation_is_strict(value):
    with pytest.raises(ConceptIdentityError) as caught:
        validate_concept_uid(value)
    assert caught.value.field == "uid"


def test_allocation_rejects_uid_tag_that_disagrees_with_concept_kind():
    with pytest.raises(ConceptIdentityError) as caught:
        ConceptAllocation(
            uid="lw:entity:" + ("a" * 32),
            concept_kind="source-module",
            natural_key="module:src/core.py",
            locator="modules/core.md",
        )

    assert caught.value.code == "uid-kind-mismatch"


def test_alias_values_use_their_own_strict_coordinate_namespace():
    assert (
        validate_alias_value("natural-key", "module:src/old/core.py")
        == "module:src/old/core.py"
    )
    assert validate_alias_value("locator", "modules/old_core.md") == (
        "modules/old_core.md"
    )
    with pytest.raises(ConceptIdentityError):
        validate_alias_value("locator", "module:src/old/core.py")
    with pytest.raises(ConceptIdentityError):
        validate_alias_value("natural-key", "modules/old_core.md")


def test_collision_detection_reports_duplicate_uid_and_current_coordinates():
    first = _module_allocation()
    duplicate_uid = ConceptAllocation(
        uid=first.uid,
        concept_kind=first.concept_kind,
        natural_key="module:src/pkg/renamed.py",
        locator="modules/renamed.md",
    )
    same_key = _module_allocation(
        bundle_id="bundle:project-2",
        locator="modules/project_two.md",
    )

    collisions = find_identity_collisions((first, duplicate_uid, same_key))
    assert {collision.code for collision in collisions} == {
        "duplicate-uid",
        "natural-key-collision",
    }
    with pytest.raises(IdentityCollisionError) as caught:
        validate_identity_registry((first, duplicate_uid, same_key))
    assert caught.value.collisions == collisions


def test_alias_collision_missing_owner_and_current_coordinate_are_detected():
    first = _module_allocation()
    second = _module_allocation(
        bundle_id="bundle:project-2",
        locator="modules/second.md",
        natural_key="module:src/second.py",
    )
    orphan_uid = derive_concept_uid(
        "bundle:orphan",
        "source-module",
        "module:src/orphan.py",
    )
    aliases = (
        IdentityAlias("locator", "modules/legacy.md", first.uid),
        IdentityAlias("locator", "modules/legacy.md", second.uid),
        IdentityAlias("natural-key", first.natural_key, second.uid),
        IdentityAlias("locator", "modules/orphan.md", orphan_uid),
    )

    codes = {
        collision.code
        for collision in find_identity_collisions((first, second), aliases)
    }
    assert codes == {
        "alias-collision",
        "alias-current-collision",
        "alias-missing-allocation",
    }


def test_duplicate_alias_record_is_a_conflict_but_alias_helper_is_idempotent():
    allocation = _module_allocation()
    alias = IdentityAlias("locator", "modules/legacy.md", allocation.uid)
    collisions = find_identity_collisions((allocation,), (alias, alias))
    assert [collision.code for collision in collisions] == ["duplicate-alias"]

    first = add_identity_alias(
        allocation,
        "locator",
        "modules/legacy.md",
    )
    second = add_identity_alias(
        allocation,
        "locator",
        "modules/legacy.md",
        aliases=first.aliases,
    )
    assert second == first


def test_allocate_is_idempotent_for_current_and_historical_coordinates():
    reference = _module_reference()
    allocation = allocate_concept("bundle:project-1", reference)
    assert allocation == allocate_concept(
        "bundle:project-1",
        reference,
        allocations=(allocation,),
    )

    moved = move_allocation(
        allocation,
        _module_reference(
            locator="modules/new_core.md",
            natural_key="module:src/new/core.py",
        ),
    )
    assert (
        allocate_concept(
            "bundle:project-1",
            reference,
            allocations=(moved.allocation,),
            aliases=moved.aliases,
        )
        == moved.allocation
    )


@pytest.mark.parametrize(
    "bundle_id",
    ["", "/private/checkout", "https://user:secret@example.test/repo"],
)
def test_allocate_validates_bundle_even_when_an_existing_identity_resolves(
    bundle_id,
):
    reference = _module_reference()
    allocation = _module_allocation()

    with pytest.raises(ConceptIdentityError) as caught:
        allocate_concept(
            bundle_id,
            reference,
            allocations=(allocation,),
        )

    assert caught.value.field == "bundle_id"


def test_allocate_does_not_silently_resolve_coordinates_owned_by_two_uids():
    first = _module_allocation()
    second = _module_allocation(
        bundle_id="bundle:project-2",
        locator="modules/second.md",
        natural_key="module:src/second.py",
    )
    reference = ConceptReference(
        locator=second.locator,
        concept_kind="source-module",
        natural_key=first.natural_key,
    )

    with pytest.raises(IdentityCollisionError) as caught:
        allocate_concept(
            "bundle:new",
            reference,
            allocations=(first, second),
        )
    assert caught.value.code == "reference-collision"


def test_move_carries_uid_and_retains_both_prior_coordinates_as_aliases():
    allocation = _module_allocation()
    new_reference = _module_reference(
        locator="modules/new_core.md",
        natural_key="module:src/new/core.py",
    )

    update = move_allocation(allocation, new_reference)

    assert update.allocation.uid == allocation.uid
    assert update.allocation.reference == new_reference
    assert update.aliases == (
        IdentityAlias("locator", allocation.locator, allocation.uid),
        IdentityAlias("natural-key", allocation.natural_key, allocation.uid),
    )
    assert aliases_for_move(
        allocation,
        new_reference,
        aliases=update.aliases,
    ) == update.aliases


def test_move_back_to_an_alias_makes_it_current_without_redundant_alias():
    original = _module_allocation()
    first_move = move_allocation(
        original,
        _module_reference(
            locator="modules/new_core.md",
            natural_key="module:src/new/core.py",
        ),
    )

    moved_back = move_allocation(
        first_move.allocation,
        original.reference,
        aliases=first_move.aliases,
    )

    assert moved_back.allocation == original
    assert moved_back.aliases == (
        IdentityAlias(
            "locator",
            first_move.allocation.locator,
            original.uid,
        ),
        IdentityAlias(
            "natural-key",
            first_move.allocation.natural_key,
            original.uid,
        ),
    )


def test_move_preserves_existing_aliases_and_rejects_kind_change_or_collision():
    allocation = _module_allocation()
    other = _module_allocation(
        bundle_id="bundle:project-2",
        locator="modules/occupied.md",
        natural_key="module:src/occupied.py",
    )
    existing_alias = IdentityAlias(
        "locator",
        "modules/oldest.md",
        allocation.uid,
    )

    update = move_allocation(
        allocation,
        _module_reference(
            locator="modules/new_core.md",
            natural_key="module:src/new/core.py",
        ),
        allocations=(allocation, other),
        aliases=(existing_alias,),
    )
    assert existing_alias in update.aliases

    with pytest.raises(ConceptIdentityError) as kind_error:
        move_allocation(
            allocation,
            ConceptReference(
                locator="entities/core.md",
                concept_kind="code-entity",
                natural_key="entity:src/pkg/core.py#Core@1",
            ),
        )
    assert kind_error.value.code == "concept-kind-change"

    with pytest.raises(IdentityCollisionError):
        move_allocation(
            allocation,
            _module_reference(
                locator=other.locator,
                natural_key="module:src/new/core.py",
            ),
            allocations=(allocation, other),
        )


def test_explicit_alias_does_not_store_redundant_current_coordinate():
    allocation = _module_allocation()
    update = add_identity_alias(
        allocation,
        AliasType.LOCATOR,
        allocation.locator,
    )
    assert update.aliases == ()


def test_alias_helper_removes_redundant_current_alias_before_adding_history():
    allocation = _module_allocation()
    redundant = IdentityAlias(
        AliasType.LOCATOR,
        allocation.locator,
        allocation.uid,
    )

    update = add_identity_alias(
        allocation,
        AliasType.LOCATOR,
        "modules/legacy.md",
        aliases=(redundant,),
    )

    assert update.aliases == (
        IdentityAlias(
            AliasType.LOCATOR,
            "modules/legacy.md",
            allocation.uid,
        ),
    )


def test_exported_result_records_validate_and_deep_freeze_collections():
    allocation = _module_allocation()
    alias = IdentityAlias(
        AliasType.LOCATOR,
        "modules/legacy.md",
        allocation.uid,
    )
    mutable_aliases = [alias]
    update = IdentityUpdate(allocation, mutable_aliases)  # type: ignore[arg-type]
    mutable_aliases.clear()

    assert update.aliases == (alias,)
    with pytest.raises(TypeError):
        IdentityUpdate("not-an-allocation", ())  # type: ignore[arg-type]
    with pytest.raises(ConceptIdentityError) as duplicate:
        IdentityUpdate(allocation, (alias, alias))
    assert duplicate.value.code == "duplicate-alias"
    with pytest.raises(ConceptIdentityError) as redundant:
        IdentityUpdate(
            allocation,
            (
                IdentityAlias(
                    AliasType.LOCATOR,
                    allocation.locator,
                    allocation.uid,
                ),
            ),
        )
    assert redundant.value.code == "alias-current-collision"


def test_collision_record_validates_and_canonicalizes_uid_collection():
    first = _module_allocation()
    second = _module_allocation(
        bundle_id="bundle:project-2",
        locator="modules/second.md",
        natural_key="module:src/second.py",
    )
    mutable_uids = [second.uid, first.uid]

    collision = IdentityCollision(
        "locator-collision",
        "locator",
        "modules/shared.md",
        mutable_uids,  # type: ignore[arg-type]
    )
    mutable_uids.clear()

    assert collision.uids == tuple(sorted((first.uid, second.uid)))
    with pytest.raises(ConceptIdentityError):
        IdentityCollision(
            "NOT NORMALIZED",
            "locator",
            "modules/shared.md",
            (first.uid,),
        )
    with pytest.raises(ConceptIdentityError):
        IdentityCollision(
            "locator-collision",
            "locator",
            "modules/shared.md",
            (),
        )


def test_registry_output_is_canonical_and_input_records_remain_unchanged():
    first = _module_allocation()
    second = _module_allocation(
        bundle_id="bundle:project-2",
        locator="modules/second.md",
        natural_key="module:src/second.py",
    )
    aliases = (
        IdentityAlias("natural-key", "module:src/z.py", second.uid),
        IdentityAlias("locator", "modules/a.md", first.uid),
    )

    allocations_result, aliases_result = validate_identity_registry(
        (second, first),
        aliases,
    )

    assert allocations_result == tuple(sorted((first, second), key=lambda item: item.uid))
    assert [alias.alias_type for alias in aliases_result] == [
        AliasType.LOCATOR,
        AliasType.NATURAL_KEY,
    ]
    assert first.locator == "llm-wiki://modules/core"
