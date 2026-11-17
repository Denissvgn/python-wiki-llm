"""Self-contained readable task evidence without observation/default codecs."""

from copy import deepcopy


READABLE_FIELDS = (
    "canonical", "intent", "state", "capture", "native", "anchors", "facts",
    "requirements", "coverage", "omissions", "followups", "limitations",
)


def readable_projection(canonical, request):
    """Preserve full selected evidence; authoritative capture stays host-owned."""
    return deepcopy({
        "canonical": {key: canonical[key] for key in (
            "task_id", "request_id", "result_id", "profile_id")},
        "intent": {key: request[key] for key in ("kind", "text", "task_ref")},
        "state": canonical["state"],
        "capture": {key: canonical["basis"][key] for key in (
            "scope", "paths", "changes", "native_availability_required",
            "source_selection_compatible")},
        "native": {key: canonical["storage"][key] for key in (
            "status", "reason", "lookup_complete", "validation_scope",
            "whole_store_validated", "unverified_records")},
        "anchors": canonical["anchors"],
        "facts": canonical["facts"],
        "requirements": request["requirements"],
        "coverage": canonical["coverage"],
        "omissions": canonical["omissions"],
        "followups": canonical["followups"],
        "limitations": canonical["limitations"],
    })


def readable_expansion(payload):
    return deepcopy({key: payload[key] for key in READABLE_FIELDS})


def readable_session_metadata(metadata):
    """Keep delivery identity/currentness qualifications; telemetry is opt-in."""
    optional = {"work", "reuse", "reconstructed_context_bytes",
                "emitted_context_bytes", "emitted_context_tokens", "delta_bytes"}
    return deepcopy({key: value for key, value in metadata.items() if key not in optional})
