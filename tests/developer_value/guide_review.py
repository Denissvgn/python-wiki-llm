"""Test-owned guide receipts: pinned provenance, not semantic verification."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

GUIDE_NAMES = (
    "orientation", "making-a-change", "symptom-investigation",
    "documentation-maintenance",
)
QUESTIONS = tuple(f"Q{number}" for number in range(1, 9))
REVIEW_SCOPE = "whole-four-guides-including-unregistered-prose"


def commitment(value: Any) -> str:
    """Canonical JSON commitment for controller-pinned inputs."""
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _file(root: Path, path: str) -> Path:
    _require(isinstance(path, str) and bool(path), "relative artifact path required")
    parts = PurePosixPath(path)
    _require(
        not parts.is_absolute() and parts.as_posix() == path
        and not ({"..", "."} & set(parts.parts)) and "\\" not in path,
        "noncanonical path or path escape",
    )
    target = root / path
    _require(target.resolve().is_relative_to(root.resolve()), "path escape")
    _require(not any(
        root.joinpath(*parts.parts[:index]).is_symlink()
        for index in range(1, len(parts.parts) + 1)
    ), "artifact symlink")
    return target


def _artifact(root: Path, descriptor: dict) -> bytes:
    _require(set(descriptor) == {"path", "sha256"}, "artifact descriptor required")
    content = _file(root, descriptor["path"]).read_bytes()
    _require(hashlib.sha256(content).hexdigest() == descriptor["sha256"],
             "artifact hash drift")
    return content


def _normal(text: str) -> str:
    return " ".join(text.split())


def _markdown_view(markdown: str) -> tuple[str, str, set[str]]:
    """Separate prose from all visible text and real CommonMark destinations."""
    prose, visible, links = [], [], set()
    for token in MarkdownIt("commonmark").parse(markdown):
        if token.type in {"html_block", "html_inline"}:
            _require(not re.sub(r"<!--.*?(?:-->|$)", "", token.content,
                                flags=re.DOTALL).strip(),
                     "noncomment HTML forbidden")
        if token.type in {"fence", "code_block"}:
            visible.append(token.content)
        if token.type != "inline":
            continue
        pieces = []
        for child in token.children or []:
            if child.type == "html_inline":
                _require(not re.sub(r"<!--.*?(?:-->|$)", "", child.content,
                                    flags=re.DOTALL).strip(),
                         "noncomment HTML forbidden")
            elif child.type in {"text", "code_inline"}:
                pieces.append(child.content)
            elif child.type in {"softbreak", "hardbreak"}:
                pieces.append("\n")
            elif child.type == "link_open":
                destination = child.attrGet("href")
                if destination is not None:
                    links.add(destination)
            elif child.type == "image":
                raise ValueError("images outside source-grounded guide format")
        text = "".join(pieces)
        prose.append(text)
        visible.append(text)
    return "\n".join(prose), "\n".join(visible), links


def _slice(root: Path, ref: dict, selected: dict) -> None:
    _require(set(ref) == {
        "path", "whole_file_sha256", "start_line", "end_line", "slice_sha256", "quote",
    }, "exact source slice descriptor required")
    _require(ref["path"] in selected, "unselected source reference")
    content = _file(root, ref["path"]).read_bytes()
    start, end = ref["start_line"], ref["end_line"]
    _require(type(start) is int and type(end) is int
             and 1 <= start <= end <= len(content.splitlines()),
             "source slice coordinates required")
    quote = b"".join(content.splitlines(keepends=True)[start - 1:end])
    _require(
        ref["whole_file_sha256"] == selected[ref["path"]]
        == hashlib.sha256(content).hexdigest()
        and ref["slice_sha256"] == hashlib.sha256(quote).hexdigest()
        and ref["quote"] == quote.decode("utf-8"),
        "source slice byte or hash drift",
    )


def _source_links(root: Path, guide: dict, hyperlinks: set[str], refs: list,
                  guides: dict, selected: dict, supplemental: dict) -> None:
    cited = set()
    for href in hyperlinks:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc:
            _require(parsed.scheme in {"http", "https"} and bool(parsed.netloc),
                     "unsupported link scheme")
            continue
        _require(bool(parsed.path) and not parsed.query
                 and "\\" not in unquote(parsed.path), "relative source link required")
        target = (_file(root, guide["path"]).parent / unquote(parsed.path)).resolve()
        _require(target.is_relative_to(root.resolve()), "source link escapes root")
        path = target.relative_to(root.resolve()).as_posix()
        _file(root, path).read_bytes()
        if path in selected:
            matches = [ref for ref in refs if ref["path"] == path
                       and parsed.fragment == f"L{ref['start_line']}-L{ref['end_line']}"]
            _require(bool(matches), "source link lacks exact bound slice")
            cited.update(commitment(ref) for ref in matches)
        else:
            _require((path in {item["path"] for item in guides.values()} or path in supplemental)
                     and not parsed.fragment, "unselected source or unbound local link")
    _require({commitment(ref) for ref in refs} <= cited,
             "every material source slice needs a rendered citation")


def _visible_text(text: str, prose: str) -> None:
    _require(isinstance(text, str) and bool(text.strip()), "material text required")
    view, _, _ = _markdown_view(text)
    _require("<!--" not in text and bool(view.strip())
             and _normal(view) in _normal(prose),
             "material text must be present in visible prose")


def validate_guide_phase(
    bundle: dict, *, root: Path, source_hashes: dict, review: dict,
    phase_window: dict, expected_questions: tuple[str, ...] = QUESTIONS,
    expected_examples: dict[str, dict] | None = None,
) -> dict:
    """Check controller-pinned phase receipts without importing or writing source.

    Review, source selection, and the measured window must be supplied by the
    controller independently of the bundle. Matching receipts cannot authenticate
    their authors or prove semantic truth. The external whole-guide review covers
    unregistered prose; answer verdicts supply comprehension acceptance. Time
    before the external boundary and unavailable token/dollar totals are excluded.
    Examples retain successful and failed outcomes; no zero-exit assumption applies.
    """
    try:
        phase = bundle["phase"]
        _require(bundle["schema_version"] == "af14-guide-phase/v1"
                 and phase in {"author", "update"}, "known guide phase required")
        _require(bundle["runtime_acceptance"] == "unestablished",
                 "guide runtime acceptance must remain unestablished")
        _require(isinstance(source_hashes, dict) and bool(source_hashes)
                 and bundle["source_hashes"] == source_hashes,
                 "phase source identity drift")
        for path, digest in source_hashes.items():
            _artifact(root, {"path": path, "sha256": digest})
        guides = bundle["guides"]
        _require(set(guides) == set(GUIDE_NAMES), "exactly four named guides required")
        _require(len({guide["path"] for guide in guides.values()}) == 4,
                 "four distinct guide artifacts required")
        supplemental = {}
        descriptors = bundle.get("supplemental_artifacts", [])
        _require(isinstance(descriptors, list), "supplemental artifact descriptors must be a list")
        for descriptor in descriptors:
            content = _artifact(root, descriptor)
            path = descriptor["path"]
            _require(PurePosixPath(path).suffix == ".json" and path not in source_hashes
                     and path not in {guide["path"] for guide in guides.values()}
                     and path not in supplemental,
                     "unique non-source JSON supplemental artifact required")
            json.loads(content)
            supplemental[path] = descriptor["sha256"]
        views, links, counts = {}, {}, {}
        for name, descriptor in guides.items():
            markdown = _artifact(root, descriptor).decode("utf-8")
            prose, visible, hyperlinks = _markdown_view(markdown)
            count = len(re.findall(r"\b\w+(?:['’-]\w+)*\b", visible))
            _require(0 < count <= 1000, "guide exceeds 1000 words or is empty")
            views[name], links[name], counts[name] = prose, hyperlinks, count
        claims = bundle["material_claims"]
        _require(isinstance(claims, list) and bool(claims), "material claims required")
        identities, by_guide = {}, {name: [] for name in GUIDE_NAMES}
        for claim in claims:
            identity, name = claim["id"], claim["guide"]
            _require(isinstance(identity, str) and bool(identity)
                     and identity not in identities and name in guides,
                     "unique named material claim required")
            _visible_text(claim["text"], views[name])
            _require(isinstance(claim["refs"], list) and bool(claim["refs"]),
                     "material source slices required")
            for ref in claim["refs"]:
                _slice(root, ref, source_hashes)
            by_guide[name].extend(claim["refs"])
            identities[identity] = claim
        _require(all(by_guide.values()), "every guide needs material source claims")
        for name in GUIDE_NAMES:
            _source_links(
                root, guides[name], links[name], by_guide[name], guides, source_hashes, supplemental,
            )
        questions = set(expected_questions)
        _require(len(questions) == len(expected_questions) and bool(questions),
                 "unique expected questions required")
        answers = bundle["answers"]
        _require(set(answers) == questions, "all expected answers and no unknown answers required")
        for answer in answers.values():
            name = answer["guide"]
            _require(name in guides, "answer names unknown guide")
            _visible_text(answer["text"], views[name])
            ids = answer["claim_ids"]
            _require(isinstance(ids, list) and bool(ids) and len(set(ids)) == len(ids)
                     and all(identity in identities and identities[identity]["guide"] == name
                             for identity in ids), "answer needs same-guide material claims")
        examples = bundle["examples"]
        _require(isinstance(examples, list), "retained examples must be a list")
        example_ids = set()
        for example in examples:
            identity = example["id"]
            _require(isinstance(identity, str) and bool(identity) and identity not in example_ids
                     and example["guide"] in guides and isinstance(example["argv"], list)
                     and bool(example["argv"]) and all(isinstance(arg, str) for arg in example["argv"])
                     and type(example["exit_code"]) is int and isinstance(example["stdout"], str)
                     and isinstance(example["stderr"], str), "retained example outcome required")
            example_ids.add(identity)
        if expected_examples is not None:
            actual = {item["id"]: item for item in examples}
            _require(set(actual) == set(expected_examples) and all(
                {"exit_code", "stdout", "stderr"} <= set(expected)
                and all(key in actual[identity] and actual[identity][key] == value
                        for key, value in expected.items())
                for identity, expected in expected_examples.items()
            ), "external expected example outcome drift")
        digest = commitment(bundle)
        _require(review["status"] == "accepted" and review["phase"] == phase
                 and review["runtime_acceptance"] == "unestablished"
                 and review["material_claim_scope"] == REVIEW_SCOPE,
                 "independent whole-guide source review required")
        author, reviewer = bundle["author_id"], review["reviewer_id"]
        _require(isinstance(author, str) and bool(author.strip())
                 and review["author_id"] == author and isinstance(reviewer, str)
                 and bool(reviewer.strip()) and reviewer.strip() != author.strip(),
                 "independent reviewer required")
        _require(review["bundle_sha256"] == digest and review["source_hashes"] == source_hashes
                 and review["guide_artifacts"] == guides
                 and review["material_claims_sha256"] == commitment(claims)
                 and review["answers_sha256"] == commitment(answers), "review binding drift")
        _require(set(review["answer_verdicts"]) == questions
                 and all(verdict == "accepted" for verdict in review["answer_verdicts"].values()),
                 "external review must accept every expected answer")
        _artifact(root, review["reference_artifact"])
        _require(phase_window["phase"] == phase and phase_window["bundle_sha256"] == digest
                 and phase_window["source_hashes"] == source_hashes, "phase window binding drift")
        start, end = phase_window["started_monotonic_ns"], phase_window["ended_monotonic_ns"]
        rounds = phase_window["revision_rounds"]
        _require(type(start) is int and type(end) is int and 0 <= start <= end
                 and end - start <= 7200 * 10**9, "external elapsed phase exceeds 120 minutes")
        _require(type(rounds) is int and 0 <= rounds <= 2, "phase exceeds two revision rounds")
        _artifact(root, phase_window["evidence_receipt"])
        return {
            "valid_phase": True, "phase": phase, "word_counts": counts,
            "elapsed_seconds": (end - start) / 10**9, "revision_rounds": rounds,
            "runtime_acceptance": "unestablished", "actual_tokens": None,
            "actual_dollars": None, "acceptance": "externally-reviewed-source-and-comprehension",
        }
    except (KeyError, TypeError, AttributeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed or unavailable guide phase evidence") from exc
