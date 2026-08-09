# __init__ Module

**Path:** `src/llm_wiki_cli/eval_lite/__init__.py`

## Description

Provider-free inspection planning for paired qualified-context arms.

## Imports

| Source | Symbols |
|--------|---------|
| `.planner` | `EVAL_LITE_PLAN_SCHEMA_VERSION`, `EVAL_LITE_TASK_SCHEMA_VERSION`, `EvaluationPlan`, `EvaluationPlanError`, `build_evaluation_plan`, `materialize_evaluation_plan`, `normalize_task_manifest` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/eval_lite/__init__.py"]
    n1["src/llm_wiki_cli/eval_lite/planner.py"]
    n0 --> n1
    click n0 "../modules/eval_lite___init__.md"
    click n1 "../modules/planner.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Outbound | [planner](../modules/planner.md) |
