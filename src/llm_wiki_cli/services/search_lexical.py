"""Pure informative lexical discovery; matches never establish source truth."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
import hashlib
import math
import posixpath
import re
import unicodedata
from urllib.parse import unquote, urlsplit

from .markdown_sections import parse_markdown_document, semantic_table_key, split_table_row
from .wiki_media import mask_fenced_code_blocks
from .search_rank import MAX_SEARCH_BYTES, MAX_SEARCH_PAGES, _STOP_WORDS, _WORDS

RANKING_VERSION = "llm-wiki-search/lexical-v2"
CONFIGURATION_ID = "idf-sections-word-forms-links/v1"
_SEMANTIC = frozenset({"description", "behavior", "notes", "usage", "troubleshooting"})
_DEFINITIONS = frozenset({"functions", "methods", "classes"})
_INVENTORY = frozenset({"imports", "relationships", "modules", "entities", "touches", "sequence", "surface overview"})
_LINK = re.compile(r"\]\(([^\s)]+)\)")
_SYMBOL = re.compile(r"[\w.]+\Z", re.UNICODE)


def _normal(text):
    return unicodedata.normalize("NFKC", text).strip().casefold()


def _word_form(word):
    """Approximate English word families for discovery, never identity matching."""
    if not word.isascii() or not word.isalpha() or len(word) < 4:
        return word
    if word.endswith("ies") and len(word) > 4:
        word = word[:-3] + "y"
    elif word.endswith(("ches", "shes", "sses", "xes", "zes")):
        word = word[:-2]
    elif word.endswith("s") and not word.endswith(("ss", "us")):
        word = word[:-1]
    if word.endswith("ied") and len(word) > 5:
        word = word[:-3] + "y"
    elif word.endswith("ing") and len(word) > 5:
        word = word[:-3]
        if len(word) > 3 and word[-1] == word[-2] and word[-1] in "bdfgmnprt":
            word = word[:-1]
    elif word.endswith("ed") and len(word) > 4:
        word = word[:-2]
        if len(word) > 3 and word[-1] == word[-2] and word[-1] in "bdfgmnprt":
            word = word[:-1]
    if len(word) > 4 and word.endswith(("e", "y")):
        word = word[:-1]
    return word


def _tokens(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text).casefold()
    return [_word_form(word) for word in _WORDS.findall(text) if word not in _STOP_WORDS]


def _fields(page):
    """Disjoint captured spans; child sections do not multiply parent evidence."""
    content = page["content"]
    document = parse_markdown_document(content, page["uri"])
    sections = document.sections
    preamble_end = sections[0].start if sections else len(document.normalized_markdown)
    fields = [{"heading": [], "start": 0, "end": preamble_end, "weight": 1.5,
               "words": Counter(_tokens(document.normalized_markdown[:preamble_end]))}]
    definitions = set()
    role_heading = ""
    for index, section in enumerate(sections):
        end = sections[index + 1].start if index + 1 < len(sections) else len(document.normalized_markdown)
        heading = section.title.casefold()
        if section.level <= 2:
            role_heading = heading if section.level == 2 else ""
        owner = role_heading
        weight = 3.0 if owner in _SEMANTIC else 1.8 if owner in _DEFINITIONS else .45 if owner in _INVENTORY else 1.0
        body = document.normalized_markdown[section.body_start:end]
        words = Counter(_tokens(body))
        fields.append({"heading": list(section.heading_path), "start": section.body_start,
                       "end": end, "weight": weight, "words": words,
                       "locator": section.locator, "ordinal": section.ordinal,
                       "occurrence_path": list(section.occurrence_path)})
        module = page["kind"] in {"module", "modules"}
        entity = page["kind"] in {"entity", "entities"}
        if (module and heading in {"functions", "classes"}) or (entity and heading == "methods"):
            header = None
            for line in mask_fenced_code_blocks(body).splitlines():
                cells = split_table_row(line)
                if not cells:
                    header = None
                    continue
                names = [cell.strip().casefold() for cell in cells]
                required = "bases" if heading == "classes" else "signature"
                if names[0] in {"name", "method", "class", "function"} and required in names:
                    header = names
                    continue
                if header is not None and len(cells) == len(header):
                    name = semantic_table_key(cells[0])
                    if _SYMBOL.fullmatch(name):
                        definitions.add(_normal(name))
                        if entity:
                            definitions.add(_normal(page["id"] + "." + name))
    all_words = Counter()
    for field in fields:
        all_words.update(field["words"])
    title, path = set(_tokens(page["title"])), set(_tokens(page["path"]))
    return fields, all_words, title, path, definitions, document.normalized_markdown


def _identity_tier(page, needle, definitions):
    reasons = []
    for field, reason in (("id", "exact-page-id"), ("path", "exact-path"), ("uri", "exact-uri")):
        if needle == _normal(page[field]):
            reasons.append(reason)
    if reasons:
        return 2, reasons
    if needle in definitions:
        return 1, ["defined-symbol"]
    return 0, []


def _linked_candidates(documents, strict, terms):
    """One-hop leads from matched diagnostic prose, never source correctness."""
    counts = Counter(document[0]["path"] for document in documents)
    targets = {document[0]["path"]: document for document in documents
               if counts[document[0]["path"]] == 1}
    suggestions = {}
    for tier, score, result in strict:
        if tier or result["kind"] not in {"guide", "guides"}:
            continue
        donor = targets.get(result["path"])
        if donor is None:
            continue
        for field in donor[1]:
            if len(terms & field["words"].keys()) < 2:
                continue
            headings = [part.casefold() for part in field["heading"]]
            if not any(part in _SEMANTIC for part in headings):
                continue
            span = donor[6][field["start"]:field["end"]]
            for link in _LINK.findall(mask_fenced_code_blocks(span)):
                try:
                    parsed = urlsplit(link)
                except ValueError:
                    continue
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                path = posixpath.normpath(posixpath.join(posixpath.dirname(result["path"]), unquote(parsed.path)))
                target = targets.get(path)
                if (path.startswith(("../", "/")) or target is None
                        or target[0]["kind"] not in {"module", "modules", "entity", "entities"}):
                    continue
                value = score * .5
                prior = suggestions.get(path)
                evidence = {"path": result["path"], "content_sha256": donor[7],
                            "section_locator": field.get("locator"), "target_path": path}
                if prior is None or (value, result["path"]) > (prior[0], prior[1]["path"]):
                    suggestions[path] = (value, evidence)
    linked = []
    for path, (score, evidence) in sorted(suggestions.items()):
        page, _, _, _, _, _, content, digest = targets[path]
        result = deepcopy({key: value for key, value in page.items() if key != "content"})
        source_index = page.get("indexing") or page.get("source_index")
        wiki_hash = (source_index.get("original_wiki_content_sha256", source_index.get("wiki_content_sha256", digest))
                     if isinstance(source_index, Mapping) else digest)
        result.update(score=round(score, 6), reasons=["linked-semantic-candidate:" + evidence["path"]],
            snippet=re.sub(r"\s+", " ", content[:250]).strip(), matched_sections=[], matched_section_locations=[],
            linked_evidence=[evidence], provenance={"content_sha256": wiki_hash, "indexed_content_sha256": digest,
                "ranking": RANKING_VERSION, "configuration": CONFIGURATION_ID,
                "qualification": "linked-discovery-candidate; live comparison not performed"})
        linked.append((0, score, result))
    return linked


def rank_pages(pages, query: str, *, limit=20, max_pages=MAX_SEARCH_PAGES, max_bytes=MAX_SEARCH_BYTES) -> dict:
    """Rank only supplied captured text within honest, fail-closed work bounds."""
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise ValueError("Search query must contain 1–4096 characters")
    for value, name, ceiling in ((limit, "limit", 100), (max_pages, "max_pages", MAX_SEARCH_PAGES),
                                 (max_bytes, "max_bytes", MAX_SEARCH_BYTES)):
        if type(value) is not int or not 1 <= value <= ceiling:
            raise ValueError(f"Search {name} must be between 1 and {ceiling}")
    terms = set(_tokens(query))
    needle = _normal(query)
    documents, identities, inbound = [], [], Counter()
    frequency = Counter()
    scanned = 0
    for page in pages:
        if len(documents) >= max_pages:
            raise ValueError("Search exceeds page limit; restrict the supplied corpus")
        if not isinstance(page, Mapping) or any(not isinstance(page.get(key), str)
                for key in ("content", "path", "title", "id", "kind", "uri")):
            raise ValueError("Search pages require captured text and stable identity fields")
        raw = page["content"].encode("utf-8")
        scanned += len(raw)
        if scanned > max_bytes:
            raise ValueError("Search exceeds UTF-8 byte limit; restrict the supplied corpus")
        digest = hashlib.sha256(raw).hexdigest()
        identities.append((page["path"], digest))
        fields, words, title, path, definitions, normalized_content = _fields(page)
        frequency.update(set(words) | title | path)
        documents.append((page, fields, words, title, path, definitions, normalized_content, digest))
        links = set()
        for link in _LINK.findall(page["content"]):
            try:
                parsed = urlsplit(link)
            except ValueError:
                continue
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(page["path"]), unquote(parsed.path)))
            if not target.startswith(("../", "/")):
                links.add(target)
        inbound.update(links)
    count = len(documents)
    weights = {term: math.log1p((count + 1) / (frequency[term] + 1)) for term in terms}
    total_weight = sum(weights.values())
    average_length = sum(sum(document[2].values()) for document in documents) / max(1, count)
    strict, relaxed = [], []
    for page, fields, words, title, path, definitions, content, digest in documents:
        matched = terms & (words.keys() | title | path)
        tier, reasons = _identity_tier(page, needle, definitions)
        coverage = sum(weights[term] for term in matched) / total_weight if total_weight else 0.0
        minimum = max(1, math.ceil(len(terms) / 2))
        strong = tier > 0 or (len(matched) >= minimum and coverage >= .45)
        fallback = not strong and len(terms) >= 4 and len(matched) >= 2 and coverage >= .15
        if not strong and not fallback:
            continue
        length = sum(words.values())
        normalization = .35 + .65 * length / max(1, average_length)
        score = 0.0
        section_matches = []
        for field in fields:
            hits = matched & field["words"].keys()
            if not hits:
                continue
            value = sum(weights[term] * (field["words"][term] * 2.2)
                        / (field["words"][term] + 1.2 * normalization) for term in hits) * field["weight"]
            score += value
            section_matches.append((value, field, hits))
        score += 5 * sum(weights[term] for term in terms & title)
        score += 3 * sum(weights[term] for term in terms & path)
        score += 8 * coverage
        score += min(.25, math.log1p(inbound[page["path"]]) / 20)
        phrase = needle in _normal(content)
        if phrase:
            score += 4
            reasons.append("exact-phrase")
        reasons.append("lexical:" + ",".join(sorted(matched)))
        if terms & title:
            reasons.append("title-match")
        if terms & path:
            reasons.append("path-match")
        if fallback:
            reasons.append("relaxed-long-query-fallback")
        else:
            reasons.append("strict-informative-term-match" if not tier else "identity-precedence")
        section_matches.sort(key=lambda item: (-item[0], item[1]["start"]))
        if section_matches:
            _, field, hits = section_matches[0]
            span = content[field["start"]:field["end"]]
            positions = [span.casefold().find(term) for term in hits if span.casefold().find(term) >= 0]
            position = min(positions, default=0)
            snippet = re.sub(r"\s+", " ", span[max(0, position - 70):position + 180]).strip()
            heading = field["heading"]
            reasons.append("section:" + (" / ".join(heading) if heading else "preamble"))
        else:
            snippet = re.sub(r"\s+", " ", content[:250]).strip()
            heading = []
        result = deepcopy({key: value for key, value in page.items() if key != "content"})
        source_index = page.get("indexing") or page.get("source_index")
        wiki_hash = (source_index.get("original_wiki_content_sha256", source_index.get("wiki_content_sha256", digest))
                     if isinstance(source_index, Mapping) else digest)
        result.update(score=round(score, 6), reasons=reasons, snippet=snippet,
            matched_sections=[list(item[1]["heading"]) for item in section_matches[:3]],
            matched_section_locations=[{"heading_path": list(item[1]["heading"]),
                "locator": item[1].get("locator"), "ordinal": item[1].get("ordinal"),
                "occurrence_path": item[1].get("occurrence_path", []),
                "start": item[1]["start"], "end": item[1]["end"],
                "text_scope": "normalized-indexed-text"} for item in section_matches[:3]],
            provenance={"content_sha256": wiki_hash, "indexed_content_sha256": digest,
                        "ranking": RANKING_VERSION, "configuration": CONFIGURATION_ID,
                        "qualification": "lexical-discovery-candidate; live comparison not performed"})
        (strict if strong else relaxed).append((tier, score, result))
    # Fallback only supplements a sparse strict list; it never changes identity order.
    matches = strict + (relaxed if len(strict) < 3 else [])
    by_path = {item[2]["path"]: index for index, item in enumerate(matches)}
    for item in _linked_candidates(documents, strict, terms):
        position = by_path.get(item[2]["path"])
        if position is None:
            by_path[item[2]["path"]] = len(matches)
            matches.append(item)
            continue
        current = matches[position]
        if current[0] == 0:
            current[2]["linked_evidence"] = item[2]["linked_evidence"]
            current[2]["reasons"].extend(item[2]["reasons"])
            if item[1] > current[1]:
                matches[position] = (0, item[1], {**current[2], "score": item[2]["score"]})
    matches.sort(key=lambda item: (-item[0], -item[1], item[2]["path"].casefold(), item[2]["path"]))
    identity = hashlib.sha256()
    for path, digest in sorted(identities):
        identity.update(path.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n")
    total, returned = len(matches), min(len(matches), limit)
    bounds = {"total": total, "returned": returned, "truncated": total > returned}
    return {"query": query, "mode": "ranked", "ranking": RANKING_VERSION,
        "corpus_id": "sha256:" + identity.hexdigest(), "scanned": {"pages": count, "bytes": scanned},
        "resource_limits": {"pages": max_pages, "bytes": max_bytes}, "total": total,
        "returned": returned, "count": returned, "truncated": bounds["truncated"],
        "bounds": {"results": bounds}, "results": [item[2] for item in matches[:limit]]}
