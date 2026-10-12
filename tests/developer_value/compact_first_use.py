"""Separate first-use gate; never upgrades the historical body-only decision.

Inputs are controller-pinned physical captures. Boolean controls are supplied
evidence, not independent review or a proof of model comprehension.
"""

from collections.abc import Mapping

from .compact_experiment import (
    ESTIMATOR_ID, REQUIRED_CONTROLS, record_sha256, text_sha256,
)


def score_first_use(record, *, expected_sha256, counter):
    """Count every supplied message, prerequisite and required follow-up.

    A complete decoder (or directly readable evidence) must be explicitly
    attested. The wire messages must include the body verbatim or as an MCP
    text block. This is a size/evidence gate, never default-adoption authority.
    """
    if counter.identity != ESTIMATOR_ID or counter.exact is not False:
        raise ValueError("First-use measurements require the pinned estimator")

    def measure(text):
        if not isinstance(text, str) or not text:
            raise ValueError("Every emitted message must be nonempty text")
        count = counter.count(text)
        if (counter.identity != ESTIMATOR_ID or counter.exact is not False
                or type(count) is not int
                or count != (len(text.encode("utf-8")) + 3) // 4):
            raise ValueError("Invalid or changed estimator")
        return {"tokens": count, "bytes": len(text.encode("utf-8")),
                "sha256": text_sha256(text)}

    def arm(value):
        from .compact_experiment import _body_in_wire

        if not isinstance(value, Mapping):
            raise ValueError("A paired physical arm is required")
        messages = value["messages"]
        if not isinstance(messages, list) or not messages:
            raise ValueError("An arm requires actual emitted messages")
        body = measure(value["body"])
        measured = [measure(text) for text in messages]
        return {"body": body, "messages": measured,
                "total_tokens": sum(item["tokens"] for item in measured),
                "body_in_wire": _body_in_wire(
                    value["body"], messages[0], value["wire_encoding"])}

    canonical, compact = arm(record["canonical"]), arm(record["compact"])
    controls = record["controls"]
    if not isinstance(controls, Mapping):
        raise ValueError("Explicit receiving controls are required")
    checks = {name: controls.get(name) is True for name in REQUIRED_CONTROLS}
    checks.update(
        physical_capture_pin=record_sha256(record) == expected_sha256,
        successful_projection=record["status"] == "success",
        complete_first_use=record["complete_first_use"] is True,
        canonical_body_in_wire=canonical["body_in_wire"],
        compact_body_in_wire=compact["body_in_wire"],
        body_at_most_1000=compact["body"]["tokens"] <= 1000,
        body_at_least_half_smaller=2 * compact["body"]["tokens"] <= canonical["body"]["tokens"],
        first_use_at_most_1000=compact["total_tokens"] <= 1000,
        first_use_at_least_half_smaller=2 * compact["total_tokens"] <= canonical["total_tokens"],
    )
    return {"eligible": all(checks.values()), "checks": checks,
            "canonical": canonical, "compact": compact,
            "counter": ESTIMATOR_ID, "exact": False,
            "default_adoption": False, "model_productivity_claim": False}
