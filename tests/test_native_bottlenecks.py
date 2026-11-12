"""A faster partial or changed fixture run cannot become a performance result."""

from copy import deepcopy

import pytest

from release import native_bottlenecks as b


def row(mode, sample, seconds=10):
    return {
        "complete": True,
        "passed": True,
        "source_sha": "a" * 40,
        "mode": mode,
        "sample": sample,
        "seconds": seconds,
        "inventory": ["tests/test_input.py::test_original"],
        "outcomes_sha256": "b" * 64,
        "environment": {"python": "3.13.17", "machine": "AMD64"},
        "fixture_profile": {
            "enabled": mode == "prepared",
            "shared_mutable_files": False,
        },
    }


def observations():
    return [
        row("fresh", 0),
        row("prepared", 0, 8),
        row("prepared", 1, 7),
        row("fresh", 1, 11),
    ]


def test_all_alternating_samples_and_their_spread_are_retained():
    result = b.summarize(observations())
    assert result["modes"]["fresh"]["seconds"] == [10, 11]
    assert result["modes"]["prepared"]["seconds"] == [8, 7]
    assert result["modes"]["prepared"]["min"] == 7
    assert result["modes"]["prepared"]["max"] == 8
    assert result["median_ratio"] == 7.5 / 10.5
    assert result["qualifying"] is result["rollout_authority"] is False


@pytest.mark.parametrize(
    "fault",
    [
        "source",
        "inventory",
        "outcomes",
        "environment",
        "failed",
        "incomplete",
        "duplicate",
        "zero",
        "partial",
    ],
)
def test_mismatched_or_partial_runs_never_report_a_speedup(fault):
    values = deepcopy(observations())
    if fault in {"source", "outcomes"}:
        values[1]["source_sha" if fault == "source" else "outcomes_sha256"] = "c" * 40
    elif fault == "inventory":
        values[1]["inventory"] = []
    elif fault == "environment":
        values[1]["environment"]["python"] = "3.13.18"
    elif fault in {"failed", "incomplete"}:
        values[1]["passed" if fault == "failed" else "complete"] = False
    elif fault == "duplicate":
        values[2]["sample"] = 0
    elif fault == "zero":
        values[1]["seconds"] = 0
    else:
        values.pop()
    with pytest.raises(b.shards.q.QualificationError):
        b.summarize(values)


def test_evidence_in_a_repository_never_places_mutable_test_inputs_under_git(
    tmp_path, monkeypatch
):
    import json
    from pathlib import Path
    from types import SimpleNamespace

    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / ".git").mkdir()
    source = repository / "candidate"
    source.mkdir()
    output = repository / "reports/benchmark"
    output.parent.mkdir()
    args = SimpleNamespace(
        root=source,
        output=output,
        samples=2,
        source_sha="a" * 40,
        archive=repository / "source.tar",
        identity=repository / "identity.json",
        expected_prefix=repository / "venv",
    )
    monkeypatch.setattr(b.canary, "verify_candidate", lambda _: {})
    temporaries = []

    def observed(command, root, env, log, *, timeout):
        temporary = Path(env["TMPDIR"])
        assert temporary.is_dir() and not temporary.is_relative_to(repository)
        temporaries.append(temporary)
        mode = command[command.index("--mode") + 1]
        sample = int(command[command.index("--sample") + 1])
        target = Path(command[command.index("--output") + 1])
        target.mkdir()
        (target / "result.json").write_text(json.dumps(row(mode, sample)))
        return {"exit_code": 0, "seconds": 1, "error": None}

    monkeypatch.setattr(b.runner, "invoke", observed)
    assert b.run(args) == 0
    assert len(temporaries) == 4 and all(not p.exists() for p in temporaries)
