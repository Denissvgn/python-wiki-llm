from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Literal, TextIO


RequestedJobs = int | Literal["auto"]


@dataclass(frozen=True)
class ExtractionJobRequest:
    """The user-facing extractor job request and its resolved worker limit."""

    requested_jobs: RequestedJobs
    resolved_jobs: int

    @classmethod
    def parse(cls, value: str) -> "ExtractionJobRequest":
        raw_value = str(value)
        if raw_value == "auto":
            return cls("auto", max(1, os.cpu_count() or 1))
        try:
            resolved_jobs = int(raw_value)
        except ValueError as exc:
            raise ValueError("must be a positive integer or 'auto'") from exc
        if resolved_jobs < 1:
            raise ValueError("must be greater than zero")
        return cls(resolved_jobs, resolved_jobs)

    @classmethod
    def resolved(cls, value: int) -> "ExtractionJobRequest":
        resolved_jobs = max(1, int(value or 1))
        return cls(resolved_jobs, resolved_jobs)


class ExtractionJobsAction(argparse.Action):
    """Resolve ``--jobs`` while preserving whether automatic sizing was requested."""

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        try:
            request = ExtractionJobRequest.parse(values)
        except ValueError as exc:
            raise argparse.ArgumentError(self, str(exc)) from exc
        setattr(namespace, self.dest, request.resolved_jobs)
        setattr(namespace, "requested_jobs", request.requested_jobs)


@dataclass(frozen=True)
class ExtractionJobPlan:
    """A deterministic description of the extraction work about to run."""

    requested_jobs: RequestedJobs = 1
    resolved_jobs: int = 1
    eligible_parallel_plans: int = 0
    effective_workers: int = 0
    parallel_plan_ids: tuple[str, ...] = ()
    sequential_plan_ids: tuple[str, ...] = ()
    cache_elided_plan_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_jobs": self.requested_jobs,
            "resolved_jobs": self.resolved_jobs,
            "eligible_parallel_plans": self.eligible_parallel_plans,
            "effective_workers": self.effective_workers,
            "parallel_plan_ids": list(self.parallel_plan_ids),
            "sequential_plan_ids": list(self.sequential_plan_ids),
            "cache_elided_plan_ids": list(self.cache_elided_plan_ids),
        }


def extraction_job_request_from_args(args) -> ExtractionJobRequest:
    """Build a request from parsed CLI arguments or compatible test namespaces."""

    resolved_jobs = max(1, int(getattr(args, "jobs", 1) or 1))
    raw_request = getattr(args, "requested_jobs", resolved_jobs)
    requested_jobs: RequestedJobs = (
        "auto" if raw_request == "auto" else int(raw_request)
    )
    return ExtractionJobRequest(requested_jobs, resolved_jobs)


def format_extraction_job_plan(plan: ExtractionJobPlan) -> str:
    def _ids(values: tuple[str, ...]) -> str:
        return ",".join(values) if values else "-"

    return (
        "Extractor plan: "
        f"requested={plan.requested_jobs} "
        f"resolved={plan.resolved_jobs} "
        f"eligible_parallel={plan.eligible_parallel_plans} "
        f"effective_workers={plan.effective_workers} "
        f"parallel={_ids(plan.parallel_plan_ids)} "
        f"sequential={_ids(plan.sequential_plan_ids)} "
        f"cache_elided={_ids(plan.cache_elided_plan_ids)}"
    )


def print_extraction_job_plan(
    plan: ExtractionJobPlan, *, file: TextIO | None = None
) -> None:
    print(
        format_extraction_job_plan(plan),
        file=file or sys.stderr,
        flush=True,
    )
