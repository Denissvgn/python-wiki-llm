"""Map documented inventory representations to independent source identities."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy

from .model import Finding, Incomplete, compare_sets, compare_value, identities


def flatten(entry: dict) -> list[dict]:
    records = []
    class_occurrences = Counter()
    for cls in entry.get("classes", []):
        class_occurrences[cls["name"]] += 1
        records.append(
            {
                **cls,
                "kind": "class",
                "declaration_kind": cls.get("kind", "class"),
                "owner": "",
            }
        )
        for collection, kind in (("attributes", "attribute"), ("methods", "method")):
            for member in cls.get(collection, []):
                records.append(
                    {
                        **member,
                        "kind": kind,
                        "owner": cls["name"],
                        "owner_occurrence": class_occurrences[cls["name"]],
                    }
                )
    for function in entry.get("functions", []):
        records.append(
            {
                **function,
                "kind": "function",
                "declaration_kind": function.get("kind", "function"),
                "owner": "",
            }
        )
    return records


def supported_source(observation: dict, lang: str) -> list[dict]:
    """Express source facts at the inventory's declared representational scope.

    Receiver parameters are implicit for Python/Rust methods. Rust impls on
    foreign types appear as module functions; their source owner stays recorded.
    Generic binder lists and alias RHS are not represented by the existing
    inventory schema. Types *inside* represented signatures remain structural.
    """
    records = deepcopy(observation["declarations"])
    classes = {r["name"] for r in records if r["kind"] == "class"}
    for record in records:
        if lang == "python" and record["kind"] == "method":
            params = record.get("params", [])
            if (
                params
                and params[0]["name"] in {"self", "cls"}
                and "staticmethod" not in record.get("decorators", [])
            ):
                record["params"] = params[1:]
        if lang == "rust" and record["kind"] == "method":
            record["source_owner"] = record["owner"]
            record["params"] = [
                p for p in record.get("params", []) if "receiver" not in p
            ]
            if record["owner"] not in classes:
                record["kind"], record["owner"] = "function", ""
    return records


def ordered(records: list[dict]) -> list[dict]:
    # Line distinguishes overload occurrences; attributes may not carry a line
    # in the wire format, so preserve their relative order within their owner.
    return sorted(
        records,
        key=lambda r: (r.get("owner", ""), r["kind"], r["name"], r.get("line", 0)),
    )


def paired(expected: list[dict], actual: list[dict]):
    left, right = ordered(expected), ordered(actual)
    expected_map = dict(zip(identities(left), left))
    actual_map = dict(zip(identities(right), right))
    for identity, source in expected_map.items():
        yield identity, source, actual_map.get(identity)


def compare_parameters(
    source: list[dict], actual: list[dict], lang: str, normalize
) -> tuple[bool, str]:
    if len(source) != len(actual):
        return False, "parameter-count"
    for expected, observed in zip(source, actual):
        if expected["name"] != observed["name"]:
            return False, "parameter-order-or-name"
        keys = {"type", "default"}
        if lang == "python":
            keys.add("kind")
        for key in keys:
            if not compare_value(
                expected.get(key),
                observed.get(key),
                field=key,
                language=lang,
                normalize=normalize,
            ):
                return False, "parameter-" + key
    return True, "parameter-contract"


def compare_records(
    source: dict,
    actual: dict,
    lang: str,
    normalize,
    *,
    fact: str,
    representation: str,
    reference: str | None = None,
) -> list[Finding]:
    result = []
    fields = []
    if source["kind"] in {"method", "function"}:
        if "params" in source:
            okay, reason = compare_parameters(
                source["params"], actual.get("params", []), lang, normalize
            )
            result.append(
                Finding(
                    fact,
                    representation,
                    "pass" if okay else "fail",
                    reason,
                    source["params"],
                    actual.get("params", []),
                    reference,
                )
            )
        fields.extend(
            k for k in ("return_type", "signature", "is_async") if k in source
        )
    elif source["kind"] == "attribute":
        fields.append("type")
        if lang in {"python", "typescript"}:
            fields.append("default")
        if lang == "typescript":
            fields.append("optional")
    if (
        source["kind"] == "class"
        and lang in {"python", "typescript"}
        and "bases" in source
    ):
        fields.append("bases")
    for field in fields:
        expected, observed = source.get(field), actual.get(field)
        if field == "default" and observed == "":
            observed = None
        if field == "bases":
            okay = len(expected or []) == len(observed or []) and all(
                normalize(lang, "type", left) == normalize(lang, "type", right)
                for left, right in zip(expected or [], observed or [])
            )
        else:
            okay = compare_value(
                expected, observed, field=field, language=lang, normalize=normalize
            )
        result.append(
            Finding(
                fact,
                representation,
                "pass" if okay else "fail",
                "declaration-" + field,
                expected,
                observed,
                reference,
            )
        )
    if source.get("type_parameters"):
        result.append(
            Finding(
                fact,
                representation,
                "not-applicable",
                "generic-binder-list-not-exposed; generic-arguments-in-types-are-compared",
                source["type_parameters"],
                reference=reference,
            )
        )
    if source["kind"] == "class" and source.get("type"):
        result.append(
            Finding(
                fact,
                representation,
                "not-applicable",
                "alias-or-named-type-body-not-exposed",
                source["type"],
                reference=reference,
            )
        )
    return result


def compare_inventory(
    observation: dict,
    entry: dict,
    lang: str,
    normalize,
    *,
    path: str,
    representation="inventory",
) -> list[Finding]:
    source, actual = supported_source(observation, lang), flatten(entry)
    findings = compare_sets(source, actual, fact=path, representation=representation)
    for identity, expected, observed in paired(source, actual):
        fact = path + ":" + "/".join(map(str, identity))
        if observed is None:
            continue
        if "line" in observed and observed["line"] != expected["line"]:
            findings.append(
                Finding(
                    fact,
                    representation,
                    "fail",
                    "declaration-coordinate",
                    expected["line"],
                    observed["line"],
                )
            )
        findings.extend(
            compare_records(
                expected,
                observed,
                lang,
                normalize,
                fact=fact,
                representation=representation,
            )
        )
    return findings


def select_original(entry: dict, selector: list[str]) -> list[dict]:
    if selector == ["module"]:
        return [{"value": entry.get("module")}]
    rows = [entry]
    for index in range(0, len(selector), 2):
        collection, name = selector[index : index + 2]
        rows = [
            item
            for row in rows
            for item in row.get(collection, [])
            if item.get("module" if collection == "imports" else "name") == name
        ]
    return rows


def compare_original(
    fact: dict, entry: dict, lang: str, normalize, representation: str
) -> Finding:
    if fact["applicability"] != "supported":
        return Finding(
            fact["id"], representation, "not-applicable", fact["proposition"]
        )
    rows = select_original(entry, fact["selector"])
    if len(rows) > 1:
        # A unique source coordinate must adjudicate repeated declarations.
        exact = [row for row in rows if row.get("line") == fact["lines"][0]]
        rows = exact or [
            row
            for row in rows
            if fact["lines"][0] <= row.get("line", -1) <= fact["lines"][1]
        ]
    if len(rows) != 1:
        return Finding(
            fact["id"],
            representation,
            "fail",
            "missing-or-ambiguous-declaration",
            fact["expected"],
            rows,
        )
    observed = rows[0]
    okay = all(
        compare_value(
            value, observed.get(key), field=key, language=lang, normalize=normalize
        )
        for key, value in fact["expected"].items()
    )
    return Finding(
        fact["id"],
        representation,
        "pass" if okay else "fail",
        "frozen-source-fact",
        fact["expected"],
        observed,
    )


def require_unique_facts(facts: list[dict]) -> None:
    if not facts:
        raise Incomplete("A corpus must contain frozen source facts")
    counts = Counter(fact["id"] for fact in facts)
    if any(count != 1 for count in counts.values()):
        raise Incomplete("Duplicate frozen fact identities")
