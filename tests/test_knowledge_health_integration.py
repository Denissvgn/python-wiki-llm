"""Native roundtrips preserve static navigation and independent assurance claims."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import analysis_capture, ci_report, lint_service
from llm_wiki_cli.services.extraction_service import (
    InventoryRequest,
    get_inventory_result,
)
from llm_wiki_cli.services.inventory_cache import (
    InventoryCacheOptions,
    InventoryCacheStats,
)
from llm_wiki_cli.services.runtime_output import RuntimeDestination


def _source(root):
    package = root / "src/pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        '"""Static package marker."""\n', encoding="utf-8"
    )
    (package / "compat.py").write_text(
        "import sys as _sys\nfrom . import impl as _impl\n_sys.modules[__name__] = _impl\n",
        encoding="utf-8",
    )
    text = (
        '__all__ = ["run"]\nraise RuntimeError("analysis must never import this source")\n'
        "def run(value):\n    def clean(candidate):\n        return leaf0(candidate)\n    return clean(value)\n"
    )
    text += "".join(
        f"def leaf{i}(value):\n    return leaf{i + 1}(value)\n" for i in range(8)
    )
    text += "def leaf8(value):\n    return value\ndef uncertain(callback,value):\n    return callback(value)\n"
    path = package / "impl.py"
    path.write_text(text, encoding="utf-8")
    return path


def _sync(root):
    sync_cmd.run(
        SimpleNamespace(
            src_dir="src",
            wiki_dir="wiki",
            cache_dir=str(root / "cache"),
            no_plugins=True,
            jobs=1,
        )
    )


def _files(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize("storage", ["v1", "packed-v4-deflate"])
def test_native_roundtrip_composes_static_routes_followups_and_advisory_health(
    tmp_path, monkeypatch, storage
):
    monkeypatch.chdir(tmp_path)
    source = _source(tmp_path)
    api.bootstrap_wiki("src", "wiki", knowledge_format=storage)
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    request = InventoryRequest(
        src_dir="src",
        deep=True,
        include_plugins=False,
        parallel_jobs=1,
        cache_options=options,
        capture_data_effect_observations=True,
        capture_import_observations=True,
    )
    cold = get_inventory_result(request)
    warm = get_inventory_result(request)
    assert (
        warm.cache_stats is not None
        and warm.cache_stats.hits == 3
        and warm.cache_stats.fresh_extracted == 0
    )
    assert cold.inventory == warm.inventory
    assert (
        cold.import_observations == warm.import_observations
        and cold.data_effect_observations == warm.data_effect_observations
    )
    page = tmp_path / "wiki/modules/impl.md"
    before = page.read_text(encoding="utf-8")
    head, rest = before.split("## Description\n", 1)
    _, tail = rest.split("\n## ", 1)
    page.write_text(
        head
        + "## Description\n\nStatic helper navigation retains its execution limits.\n\n## "
        + tail,
        encoding="utf-8",
    )
    _sync(tmp_path)
    assert "Static helper navigation retains its execution limits." in page.read_text(
        encoding="utf-8"
    )
    anchored = _files(tmp_path / "wiki")
    _sync(tmp_path)
    assert _files(tmp_path / "wiki") == anchored
    report = lint_service.build_report(
        "wiki",
        "src",
        strict=True,
        include_plugins=False,
        knowledge_drift_report=True,
        include_health_details=True,
    )
    assert report.passed
    notices = {
        row.path: row
        for row in report.diagnostics
        if row.reason_code in {"static-module-alias", "declaration-free-initializer"}
    }
    assert notices["pkg/compat.py"].target == "pkg/impl.py"
    assert notices["pkg/__init__.py"].reason_code == "declaration-free-initializer"
    service = api.build_documentation_query_service(src_dir="src", wiki_dir="wiki")
    first = service.flow_segment("pkg/impl.py:run")
    assert [r["symbol"] for r in first["steps"]] == [
        "run",
        "run.<locals>.clean",
        "leaf0",
        "leaf1",
        "leaf2",
        "leaf3",
        "leaf4",
    ]
    follow = first["steps"][-1]["follow_up"]["request"]
    tail = service.flow_segment(follow["value"], basis=follow["basis"])
    assert [r["symbol"] for r in tail["steps"]] == [
        "leaf4",
        "leaf5",
        "leaf6",
        "leaf7",
        "leaf8",
    ]
    assert (
        first["coverage"]["depth_limit"] == 6 and first["coverage"]["step_limit"] == 12
    )
    uncertain = service.flow_segment("pkg/impl.py:uncertain")
    assert (
        uncertain["steps"][1]["kind"] == "unresolved"
        and uncertain["coverage"]["runtime_completeness"] is False
    )
    explained = service.explain_evidence("llm-wiki://flows/api-run")
    assert explained["evidence"]["freshness"]["state"] == "unknown"
    assert explained["evidence"]["freshness"]["reason"] == "freshness-not-modeled"
    original = analysis_capture.capture_analysis

    def other_runtime(*args, **kwargs):
        captured = original(*args, **kwargs)
        values = {key: dict(value) for key, value in captured.items()}
        for value in values.values():
            value["runtime"] = "sha256:" + "f" * 64
        return analysis_capture._issued(values)

    # Captured-runtime model only; no alternative native runtime proof.
    with monkeypatch.context() as patch:
        patch.setattr(analysis_capture, "capture_analysis", other_runtime)
        changed = lint_service.build_report(
            "wiki",
            "src",
            strict=True,
            include_plugins=False,
            knowledge_drift_report=True,
            include_health_details=True,
        )
        assert changed.passed
        findings = [
            r
            for r in changed.diagnostics
            if r.category == "knowledge_freshness" and "runtime" in r.message
        ]
        assert findings and all(
            r.hint is not None and "target host" in r.hint for r in findings
        )
        assert all(
            "Restore the recorded configuration" not in (r.hint or "") for r in findings
        )
        payload = ci_report.build_ci_check_payload(
            changed,
            report_schema="v4",
            runtime={
                "cache": InventoryCacheStats(enabled=False).to_dict(),
                "report": RuntimeDestination(None).to_payload(),
            },
            command_exit_code=0,
        )
        ci_report.validate_ci_check_payload(payload, cli_exit=0)
        wire = deepcopy(payload)
        text = ci_report.render_ci_markdown(payload, cli_exit=0)
        assert (
            "Release policy: unavailable" in text[:4096]
            and "target host" in text[:4096]
        )
        assert payload == wire
    source.write_text(
        source.read_text(encoding="utf-8")
        + "\n# Same graph, new captured source bytes.\n",
        encoding="utf-8",
    )
    fresh = api.build_documentation_query_service(src_dir="src", wiki_dir="wiki")
    with pytest.raises(ValueError, match="basis"):
        fresh.flow_segment(follow["value"], basis=follow["basis"])
