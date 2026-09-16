# require_sha256

**Entry point:** `require_sha256` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_sha256
    participant p1 as isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256)
    participant p2 as require_trimmed_text
    participant p3 as require_nonempty_text
    participant p4 as isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    participant p5 as value.strip
    participant p6 as contains_control_character
    participant p7 as pattern.search
    participant p8 as _SHA256_RE.fullmatch
    p0-->>p1: isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256)
    p0->>p2: require_trimmed_text
    p2->>p3: require_nonempty_text
    p3-->>p4: isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    p3-->>p5: value.strip
    p3->>p6: contains_control_character
    p6-->>p7: pattern.search
    p0-->>p8: _SHA256_RE.fullmatch
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_sha256"]
    s2["2. isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256)"]
    s3["3. require_trimmed_text"]
    s4["4. require_nonempty_text"]
    s5["5. isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)"]
    s6["6. value.strip"]
    s7["7. contains_control_character"]
    s8["8. pattern.search"]
    s9["9. _SHA256_RE.fullmatch"]
    s1 -. "isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256)(value, str)" .-> s2
    s1 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s3
    s3 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)" .-> s5
    s4 -. "value.strip(data not statically known)" .-> s6
    s4 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s7
    s7 -. "pattern.search(value)" .-> s8
    s1 -. "_SHA256_RE.fullmatch(parsed)" .-> s9
    click s1 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s7 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_sha256` | `value: object`, `digest_error: Exception`, `text_error: Exception \| None`, `reject_control_characters: bool`, `allow_empty: bool` | - | - | `parsed`, `parsed` |
| `isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256)` | - | - | - | - |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |
| `_SHA256_RE.fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_sha256 | isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256) | 1138 | `isinstance(value, str)` |
| require_sha256 | require_trimmed_text | 1142 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 696 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text) | 623 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 625 | `value.strip(data not statically known)` |
| require_nonempty_text | contains_control_character | 631 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 685 | `pattern.search(value)` |
| require_sha256 | _SHA256_RE.fullmatch | 1149 | `_SHA256_RE.fullmatch(parsed)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_sha256` | `isinstance` | 1138 |
| external_call | `require_nonempty_text` | `isinstance` | 623 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 625 |
| unresolved_call | `contains_control_character` | `pattern.search` | 685 |
| unresolved_call | `require_sha256` | `_SHA256_RE.fullmatch` | 1149 |

## Behavior

This flow starts at `require_sha256` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
