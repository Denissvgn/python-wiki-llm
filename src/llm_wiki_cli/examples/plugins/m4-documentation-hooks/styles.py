"""Sample bounded diagram-style hooks for LLM Wiki plugins."""

from __future__ import annotations


def style_flowcharts(context):
    """Return safe Mermaid style hints for generated flowchart surfaces."""
    surface = str((context or {}).get("surface", ""))
    if surface not in {"relationships", "dependencies", "data_flow"}:
        return {}
    return {
        "direction": "LR",
        "node_classes": {"task-handler": "entry"},
        "category_colors": {"entry": "#2E7D32"},
    }
