"""Independent Markdown table and signature decoding for generated records."""

from __future__ import annotations

import re

from markdown_it import MarkdownIt

from .model import Incomplete


def tables(text: str) -> list[dict]:
    tokens = MarkdownIt("commonmark").enable("table").parse(text)
    section, current, row, result = "", None, None, []
    in_heading = False
    for token in tokens:
        if token.type == "heading_open":
            in_heading = True
        elif token.type == "heading_close":
            in_heading = False
        elif token.type == "table_open":
            current = {"section": section, "rows": []}
            result.append(current)
        elif token.type == "table_close":
            current = None
        elif token.type == "tr_open":
            row = []
        elif token.type == "tr_close" and current is not None:
            current["rows"].append(row)
            row = None
        elif token.type == "inline":
            content = "".join(
                child.content
                for child in (token.children or [])
                if child.type in {"text", "code_inline", "html_inline"}
            )
            if in_heading:
                section = content
            elif current is not None and row is not None:
                row.append(content)
    return result


def split_balanced(text: str, separator=",") -> list[str]:
    """Split a rendered signature without erasing literal or grouping content."""
    result, start, stack, quote, escape = [], 0, [], None, False
    for index, char in enumerate(text):
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"', "`"}:
            # Rust lifetimes are identifiers, not quoted strings.
            if (
                char == "'"
                and re.match(r"'[A-Za-z_]\w*(?!')", text[index:])
                and "'" not in text[index + 1 :].split(",", 1)[0]
            ):
                continue
            quote = char
        elif char in "([{":
            stack.append(char)
        elif char == "<" and (index + 1 == len(text) or text[index + 1] != "="):
            stack.append(char)
        elif char in ")]}":
            if stack:
                stack.pop()
        elif (
            char == ">"
            and stack
            and stack[-1] == "<"
            and (index == 0 or text[index - 1] not in "-=")
        ):
            stack.pop()
        elif (
            char == separator
            and not stack
            and not (
                separator == "="
                and (
                    text[index : index + 2] in {"=>", "=="}
                    or (index > 0 and text[index - 1] in "<>=!")
                )
            )
        ):
            result.append(text[start:index].strip())
            start = index + 1
    result.append(text[start:].strip())
    return result


def signature(text: str, lang: str) -> dict:
    if lang == "haskell":
        return {"signature": text}
    is_async = text.startswith("(async) ")
    if is_async:
        text = text[len("(async) ") :]
    if not text.startswith("("):
        raise Incomplete(f"Unrecognized rendered signature: {text}")
    # The generator puts the result after the matching outer parameter group.
    depth, quote, escaped, end = 0, None, False, None
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            if (
                char == "'"
                and lang == "rust"
                and re.match(r"'[A-Za-z_]\w*", text[index:])
            ):
                continue
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end is None:
        raise Incomplete(f"Unbalanced rendered signature: {text}")
    raw_params = split_balanced(text[1:end]) if text[1:end].strip() else []
    params, keyword_only = [], False
    for raw in raw_params:
        if raw == "/":
            for param in params:
                param["kind"] = "positional_only"
            continue
        if raw == "*":
            keyword_only = True
            continue
        head, colon, annotation = raw.partition(":")
        default = None
        if "=" in (annotation if colon else head):
            value = annotation if colon else head
            parts = split_balanced(value, "=")
            if len(parts) == 2:
                if colon:
                    annotation = parts[0]
                else:
                    head = parts[0]
                default = parts[1]
        name = head.strip()
        kind = "keyword_only" if keyword_only else "positional_or_keyword"
        if name.startswith("**"):
            kind, name = "var_keyword", name[2:]
        elif name.startswith("*"):
            kind, name, keyword_only = "var_positional", name[1:], True
        item = {"name": name, "type": annotation.strip() if colon else ""}
        if lang == "python":
            item["kind"] = kind
        if default is not None:
            item["default"] = default
        params.append(item)
    tail = text[end + 1 :].strip()
    if tail and not tail.startswith("-> "):
        raise Incomplete(f"Unexpected return delimiter: {text}")
    return {
        "params": params,
        "return_type": tail[3:].strip() if tail else "",
        "is_async": is_async,
    }


def named_rows(text: str, section: str, column: str) -> list[dict]:
    results = []
    for table in tables(text):
        if table["section"] != section or not table["rows"]:
            continue
        headings = table["rows"][0]
        if column not in headings:
            continue
        results.extend(dict(zip(headings, row)) for row in table["rows"][1:])
    return results
