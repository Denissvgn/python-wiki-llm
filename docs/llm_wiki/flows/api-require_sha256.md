# require_sha256

**Entry point:** `require_sha256` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_sha256
    participant p1 as isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256)
    participant p2 as require_trimmed_text
    participant p3 as _SHA256_RE.fullmatch
    participant p4 as require_nonempty_text
    participant p5 as isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    participant p6 as value.strip
    participant p7 as contains_control_character
    participant p8 as pattern.search
    p0-->>p1: isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256)(value, str)
    p0->>p2: require_trimmed_text
    p0-->>p3: _SHA256_RE.fullmatch(parsed)
    p2->>p4: require_nonempty_text
    p4-->>p5: isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)
    p4-->>p6: value.strip
    p4->>p7: contains_control_character
    p7-->>p8: pattern.search(value)
```

> Call sequence diagram shows 8 of 8 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 4; effect analysis evaluated: 4, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 4 source steps with known totals: observed: 24, emitted: 24, omitted: 0. Unavailable totals are excluded.

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
| require_sha256 | isinstance (src/llm_wiki_cli/services…lidation.py:require_sha256) | 1146 | `isinstance(value, str)` |
| require_sha256 | require_trimmed_text | 1150 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 704 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text) | 631 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 633 | `value.strip(data not statically known)` |
| require_nonempty_text | contains_control_character | 639 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 693 | `pattern.search(value)` |
| require_sha256 | _SHA256_RE.fullmatch | 1157 | `_SHA256_RE.fullmatch(parsed)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_sha256` | `isinstance` | 1146 |
| external_call | `require_nonempty_text` | `isinstance` | 631 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 633 |
| unresolved_call | `contains_control_character` | `pattern.search` | 693 |
| unresolved_call | `require_sha256` | `_SHA256_RE.fullmatch` | 1157 |

## Behavior

This flow starts at `require_sha256` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
