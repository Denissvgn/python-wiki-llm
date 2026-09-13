"""Sample bounded diagram-style hooks for LLM Wiki plugins."""

from __future__ import annotations


def style_flowcharts(context):
    """Return safe Mermaid style hints for generated flowchart surfaces."""
    context = context or {}
    surface = str(context.get("surface", ""))
    if surface not in {"relationships", "dependencies", "data_flow"}:
        return {}
    node_classes = {"task-handler": "entry"}
    if surface == "data_flow":
        # Data-flow nodes use numbered callable labels, not entry-point labels.
        node_classes = (
            {"1. handle_task": "entry", "1. task_handler": "entry"}
            if context.get("category") == "task"
            else {}
        )
    return {
        "direction": "LR",
        "node_classes": node_classes,
        "category_colors": {"entry": "#2E7D32"},
    }
