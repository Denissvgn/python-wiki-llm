"""Pure, pinned retrieval scoring for an independently authored forty-query corpus.

This module never runs a provider or loads a default corpus. Capture, source
selection and the one-shot confirmation lease belong to the external runner.
The adoption rule is fixed here before any observations are scored.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, TypedDict

CATEGORIES = ("exact-symbol", "error-message", "symptom", "paraphrase", "unanswerable")
SPLITS = ("development", "confirmation")
REQUIRED_CONTROLS = ("correctness", "selection")
MAX_RESULTS = 100
MAX_CAPTURE_BYTES = 64 * 1024 * 1024
MAX_RAW_PAGE_BYTES = 1024 * 1024


class ResultRecord(TypedDict, total=False):
    path: str
    section: str | None
    snippet: str


class ObservationRow(TypedDict, total=False):
    query_id: str
    results: list[ResultRecord]
    limit: int
    error: str | None
    definitive_claim: bool | None
    wall_ns: int
    response_bytes: int
    truncated: bool


class ObservationCapture(TypedDict):
    corpus_id: str
    corpus_sha256: str
    provider: str
    selected_source: str
    capture_id: str
    arm: str
    split: str
    rows: list[ObservationRow]


def frozen_results_digest(value: Any) -> str:
    """Hash canonical JSON, including identities, raw results and all metadata."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


corpus_digest = frozen_results_digest


def _path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("expected a nonempty relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or value != path.as_posix() or value == ".":
        raise ValueError("path must be canonical and remain inside its source root")
    return value


def validate_corpus(corpus: Mapping[str, Any]) -> None:
    """Validate balance and relevance declarations without reading source files."""
    if not isinstance(corpus.get("corpus_id"), str) or not corpus["corpus_id"]:
        raise ValueError("corpus_id is required")
    if not corpus.get("version") or set(corpus.get("categories", [])) != set(CATEGORIES):
        raise ValueError("version and all five categories are required")
    fixture_types = corpus.get("fixture_types", [])
    if len(fixture_types) != 3 or len(set(fixture_types)) != 3:
        raise ValueError("exactly three distinct fixture types are required")
    fixtures = corpus.get("fixtures", {})
    if isinstance(fixtures, list):
        if len({fixture.get("id") for fixture in fixtures}) != len(fixtures):
            raise ValueError("fixture IDs must be distinct")
        fixtures = {fixture["id"]: fixture for fixture in fixtures}
    if not isinstance(fixtures, Mapping) or not fixtures:
        raise ValueError("fixtures must be a nonempty identity mapping")
    if {fixture["type"] for fixture in fixtures.values()} != set(fixture_types):
        raise ValueError("all fixture types must be represented")
    queries = corpus.get("queries", [])
    if len(queries) != 40:
        raise ValueError("exactly forty queries are required")
    ids: set[str] = set()
    texts: set[str] = set()
    counts: Counter[tuple[str, str]] = Counter()
    for query in queries:
        identity = query.get("id")
        text = query.get("query")
        if not isinstance(identity, str) or not identity or identity in ids:
            raise ValueError("query IDs must be distinct and nonempty")
        if not isinstance(text, str) or not text.strip() or text.strip().casefold() in texts:
            raise ValueError("query strings must be distinct and nonempty")
        ids.add(identity)
        texts.add(text.strip().casefold())
        fixture = query.get("fixture")
        category, split = query.get("category"), query.get("split")
        if fixture not in fixtures or category not in CATEGORIES or split not in SPLITS:
            raise ValueError("unknown fixture, category or split")
        counts[(split, category)] += 1
        owners = query.get("expected_owners")
        sections = query.get("expected_sections")
        if not isinstance(owners, list) or not isinstance(sections, list):
            raise ValueError("expected owners and sections must be explicit lists")
        if len(set(owners)) != len(owners) or len({frozen_results_digest(section) for section in sections}) != len(sections):
            raise ValueError("relevance declarations must be unique")
        for owner in owners:
            _path(owner)
        fixture_files = fixtures[fixture].get("files", {})
        authored = fixtures[fixture].get("authored_content", {})
        if any(owner not in fixture_files for owner in owners):
            raise ValueError("relevant owners must be declared fixture source files")
        for section in sections:
            if not isinstance(section, Mapping) or section.get("owner") not in owners:
                raise ValueError("section declarations must bind a declared relevant owner")
            heading = section.get("heading", section.get("heading_path"))
            if not isinstance(heading, str) or heading not in authored.get(section["owner"], {}):
                raise ValueError("section headings must exist in predeclared authored content")
            if not section.get("quote") and not section.get("source_cite"):
                raise ValueError("section relevance must contain a quote or source citation")
            quote = section.get("quote")
            if quote is not None and (not isinstance(quote, str) or not quote or quote not in authored[section["owner"]][heading]):
                raise ValueError("section quote must match predeclared authored content")
        if category == "unanswerable":
            if owners or sections or query.get("expected_top_one_owner") is not None:
                raise ValueError("unanswerable queries cannot declare relevant targets")
        elif not owners or not sections:
            raise ValueError("answerable queries must predeclare owners and sections")
        if category == "exact-symbol" and query.get("expected_top_one_owner") not in owners:
            raise ValueError("exact-symbol queries require a declared top-one owner")
        if not query.get("relevancecite"):
            raise ValueError("every query requires a predeclared relevance citation")
    if any(counts[(split, category)] != 4 for split in SPLITS for category in CATEGORIES):
        raise ValueError("each split must contain four queries in each category")


@dataclass(frozen=True)
class CaptureBinding:
    """Values supplied by the runner's frozen plan, never inferred from results."""

    corpus_id: str
    corpus_sha256: str
    provider: str
    selected_source: str
    capture_id: str
    results_sha256: str
    arm: str
    aliases_sha256: str


@dataclass(frozen=True)
class Ratio:
    numerator: int
    denominator: int

    @property
    def value(self) -> Fraction | None:
        return Fraction(self.numerator, self.denominator) if self.denominator else None

    def to_dict(self) -> dict[str, Any]:
        return {"numerator": self.numerator, "denominator": self.denominator,
                "value": float(self.value) if self.value is not None else None}


@dataclass(frozen=True)
class PageTrace:
    rank: int
    path: str
    owner: str | None
    relevant: bool
    section: str | None
    raw_json: str


@dataclass(frozen=True)
class QueryScore:
    query_id: str
    category: str
    status: str
    expected_owners: tuple[str, ...]
    owner_top5: tuple[str, ...]
    emitted_top5: tuple[PageTrace, ...]
    all_pages: tuple[PageTrace, ...]
    owner_hits: int
    emitted_owner_hits: int
    emitted_page_hits: int
    expected_sections: int
    emitted_section_hits: int
    exact_top_one_correct: bool | None
    definitive_claim: bool | None
    metadata_json: str


@dataclass(frozen=True)
class SplitScore:
    binding: CaptureBinding
    split: str
    query_ids: tuple[str, ...]
    queries: tuple[QueryScore, ...]
    owner_recall: Ratio
    owner_precision: Ratio
    emitted_recall: Ratio
    emitted_precision: Ratio
    exact_correct: int
    exact_total: int
    unanswerable_total: int
    unanswerable_claims_observed: int
    unanswerable_definitive_claims: int
    unanswerable_candidates: int
    unanswerable_candidate_pages: int
    missing: int
    errors: int

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for name in ("owner_recall", "owner_precision", "emitted_recall", "emitted_precision"):
            result[name] = getattr(self, name).to_dict()
        return result


def _validate_capture(corpus: Mapping[str, Any], observations: Mapping[str, Any],
                      aliases: Mapping[str, Mapping[str, str]], expected: CaptureBinding) -> None:
    if corpus["corpus_id"] != expected.corpus_id or corpus_digest(corpus) != expected.corpus_sha256:
        raise ValueError("corpus differs from externally pinned identity")
    if len(json.dumps(observations, ensure_ascii=False, allow_nan=False).encode()) > MAX_CAPTURE_BYTES:
        raise ValueError("capture exceeds frozen raw byte limit")
    if frozen_results_digest(observations) != expected.results_sha256:
        raise ValueError("results differ from externally pinned capture")
    if frozen_results_digest(aliases) != expected.aliases_sha256:
        raise ValueError("aliases differ from externally pinned manifest projection")
    for field in ("corpus_id", "corpus_sha256", "provider", "selected_source", "capture_id", "arm"):
        if not isinstance(getattr(expected, field), str) or not getattr(expected, field) or observations.get(field) != getattr(expected, field):
            raise ValueError(f"capture identity mismatch: {field}")
    fixtures = corpus["fixtures"]
    fixture_map = fixtures if isinstance(fixtures, Mapping) else {fixture["id"]: fixture for fixture in fixtures}
    if set(aliases) != set(fixture_map):
        raise ValueError("aliases must explicitly cover all declared fixture identities")
    for fixture_id, fixture_aliases in aliases.items():
        if not isinstance(fixture_aliases, Mapping):
            raise ValueError("fixture aliases must map exact page paths to single owners")
        for page, owner in fixture_aliases.items():
            _path(page)
            _path(owner)
            if owner not in fixture_map[fixture_id]["files"]:
                raise ValueError("alias owner is outside selected fixture source")


def score_split(corpus: Mapping[str, Any], observations: Mapping[str, Any],
                aliases: Mapping[str, Mapping[str, str]], split: str, *, expected: CaptureBinding) -> SplitScore:
    """Score only the specified split. Missing/error rows remain in denominators.

    Primary @5 deduplicates owners across *all* emitted pages before taking five.
    Unmapped paths occupy individual negative slots. Safeguards use the actual
    first five emitted pages, preserving duplicates and their original ranks.
    """
    validate_corpus(corpus)
    if split not in SPLITS:
        raise ValueError("split must be explicit development or confirmation")
    _validate_capture(corpus, observations, aliases, expected)
    selected = [query for query in corpus["queries"] if query["split"] == split]
    selected_ids = {query["id"] for query in selected}
    if observations.get("split") != split:
        raise ValueError("observation split must match the explicitly selected split")
    records = observations.get("rows")
    if not isinstance(records, list):
        raise ValueError("capture rows must be an explicit list")
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        identity = record.get("query_id")
        if identity not in selected_ids or identity in indexed:
            raise ValueError("duplicate or out-of-split observation query")
        indexed[identity] = record
    rows: list[QueryScore] = []
    owner_hits = emitted_owner_hits = emitted_page_hits = owner_slots = page_slots = targets = 0
    exact_correct = exact_total = unanswered = claims_observed = claims = candidates = candidate_pages = 0
    missing = errors = 0
    for query in selected:
        record = indexed.get(query["id"])
        status = "missing" if record is None else "error" if record.get("error") else "observed"
        missing += status == "missing"
        errors += status == "error"
        raw_results = record.get("results", []) if record else []
        if not isinstance(raw_results, list):
            raise ValueError("raw results must be a list")
        limit = record.get("limit") if record else MAX_RESULTS
        if type(limit) is not int or not 1 <= limit <= MAX_RESULTS or len(raw_results) > limit:
            raise ValueError("capture limit must be 1..100 and bound all returned pages")
        relevant = set(query["expected_owners"])
        pages: list[PageTrace] = []
        owner_labels: list[str] = []
        owner_relevance: list[bool] = []
        seen: set[tuple[str, str]] = set()
        for rank, raw in enumerate(raw_results, 1):
            path = _path(raw.get("path"))
            owner = aliases[query["fixture"]].get(path)
            section = raw.get("section")
            if section is not None and not isinstance(section, str):
                raise ValueError("page section must be a string or null")
            raw_json = json.dumps(raw, sort_keys=True, ensure_ascii=False, allow_nan=False)
            if len(raw_json.encode()) > MAX_RAW_PAGE_BYTES:
                raise ValueError("raw page exceeds frozen byte limit")
            pages.append(PageTrace(rank, path, owner, owner in relevant, section, raw_json))
            label = ("owner", owner) if owner is not None else ("unmapped", path)
            if label not in seen:
                seen.add(label)
                owner_labels.append(owner if owner is not None else "unmapped:" + path)
                owner_relevance.append(owner is not None and owner in relevant)
        emitted = pages[:5]
        distinct = owner_labels[:5]
        hits = sum(owner_relevance[:5])
        emitted_hits = len(relevant.intersection(page.owner for page in emitted))
        page_hits = sum(page.relevant for page in emitted)
        section_hits = sum(any(page.owner == target["owner"]
                               and page.section == target.get("heading", target.get("heading_path"))
                               for page in emitted) for target in query["expected_sections"])
        exact = None
        if query["category"] == "exact-symbol":
            exact_total += 1
            exact = bool(status == "observed" and pages and pages[0].owner == query["expected_top_one_owner"])
            exact_correct += exact
        claim = record.get("definitive_claim") if record and status == "observed" else None
        if claim is not None and type(claim) is not bool:
            raise ValueError("definitive_claim must be an observed boolean or null")
        if query["category"] == "unanswerable":
            unanswered += 1
            claims_observed += claim is not None
            claims += claim is True
            candidates += bool(pages)
            candidate_pages += len(pages)
        else:
            targets += len(relevant)
            # Error outputs are retained as raw trace, but cannot establish retrieval success.
            if status == "observed":
                owner_hits += hits
                emitted_owner_hits += emitted_hits
                emitted_page_hits += page_hits
            owner_slots += len(distinct)
            page_slots += len(emitted)
        rows.append(QueryScore(query["id"], query["category"], status,
                               tuple(query["expected_owners"]), tuple(distinct), tuple(emitted),
                               tuple(pages), hits if status == "observed" else 0,
                               emitted_hits if status == "observed" else 0,
                               page_hits if status == "observed" else 0,
                               len(query["expected_sections"]), section_hits if status == "observed" else 0, exact, claim,
                               json.dumps({key: value for key, value in (record or {}).items()
                                           if key != "results"}, sort_keys=True, allow_nan=False)))
    return SplitScore(expected, split, tuple(query["id"] for query in selected), tuple(rows),
                      Ratio(owner_hits, targets), Ratio(owner_hits, owner_slots),
                      Ratio(emitted_owner_hits, targets), Ratio(emitted_page_hits, page_slots),
                      exact_correct, exact_total, unanswered, claims_observed, claims,
                      candidates, candidate_pages, missing, errors)


@dataclass(frozen=True)
class GateDecision:
    eligible: bool
    checks: Mapping[str, bool]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"eligible": self.eligible, "checks": dict(self.checks), "reasons": list(self.reasons)}


def adoption_gate(baseline: SplitScore, candidate: SplitScore, *,
                  controls: Mapping[str, bool]) -> GateDecision:
    """Fixed confirmation rule. Fractions make exact threshold boundaries stable.

    Arms stay independent: the runner compares each candidate to its matching
    baseline. No aggregation of augmented and unaugmented source arms is allowed.
    Full eight-case exact-symbol checks must additionally be supplied by the
    runner as the mandatory ``exact_development`` control.
    """
    checks: dict[str, bool] = {}
    checks["confirmation_split"] = baseline.split == candidate.split == "confirmation"
    checks["same_corpus_and_schedule"] = (baseline.binding.corpus_id == candidate.binding.corpus_id
        and baseline.binding.corpus_sha256 == candidate.binding.corpus_sha256
        and baseline.query_ids == candidate.query_ids)
    checks["same_arm"] = baseline.binding.arm == candidate.binding.arm
    checks["same_selected_source"] = baseline.binding.selected_source == candidate.binding.selected_source
    checks["same_aliases"] = baseline.binding.aliases_sha256 == candidate.binding.aliases_sha256
    checks["distinct_capture"] = baseline.binding.capture_id != candidate.binding.capture_id
    for name in (*REQUIRED_CONTROLS, "exact_development"):
        checks[name] = controls.get(name) is True
    checks["observations_complete"] = not (baseline.missing or candidate.missing or baseline.errors or candidate.errors)
    br, cr = baseline.owner_recall.value, candidate.owner_recall.value
    bp, cp = baseline.owner_precision.value, candidate.owner_precision.value
    ber, cer = baseline.emitted_recall.value, candidate.emitted_recall.value
    bep, cep = baseline.emitted_precision.value, candidate.emitted_precision.value
    checks["owner_recall_gain"] = br is not None and cr is not None and cr - br >= Fraction(1, 10)
    checks["owner_precision_noninferiority"] = bp is not None and cp is not None and cp >= bp - Fraction(1, 20)
    checks["emitted_recall_noninferiority"] = ber is not None and cer is not None and cer >= ber
    checks["emitted_precision_noninferiority"] = bep is not None and cep is not None and cep >= bep - Fraction(1, 20)
    checks["exact_confirmation"] = candidate.exact_total == 4 and candidate.exact_correct == candidate.exact_total
    checks["unanswerable_claims_observed"] = (baseline.unanswerable_claims_observed == baseline.unanswerable_total == 4
        and candidate.unanswerable_claims_observed == candidate.unanswerable_total == 4)
    checks["no_unanswerable_definitive_claims"] = candidate.unanswerable_definitive_claims == 0
    reasons = tuple(name for name, passed in checks.items() if not passed)
    return GateDecision(not reasons, checks, reasons)
