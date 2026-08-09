# source_identity

**Entry point:** `source_identity` (`api`)
**Source:** [refresh](../modules/refresh.md)
**Modules touched:** [refresh](../modules/refresh.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as source_identity
    participant p1 as resolve
    participant p2 as expanduser
    participant p3 as Path
    participant p4 as run
    participant p5 as str
    participant p6 as strip
    p0-->>p1: resolve
    p0-->>p2: expanduser
    p0-->>p3: Path
    p0-->>p4: run
    p0-->>p5: str
    p0-->>p6: strip
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. source_identity"]
    s2["2. resolve"]
    s3["3. expanduser"]
    s4["4. Path"]
    s5["5. run"]
    s6["6. str"]
    s7["7. strip"]
    s1 -. "Path(source_root).expanduser().resolve(data not statically known)" .-> s2
    s1 -. "Path(source_root).expanduser(data not statically known)" .-> s3
    s1 -. "Path(source_root)" .-> s4
    s1 -. "subprocess.run([...], capture_output=True, text=True, check=True, timeout=10)" .-> s5
    s1 -. "str(root)" .-> s6
    s1 -. "result.stdout.strip(data not statically known)" .-> s7
    b0["process subprocess.run"]
    s1 -. "process subprocess.run" .-> b0
    click s1 "../modules/refresh.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `source_identity` | `source_root: str \| Path`, `baseline: TreeBaseline` | - | - | `{...}` |
| `resolve` | - | - | - | - |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `run` | - | - | - | - |
| `str` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| source_identity | resolve | 632 | `Path(source_root).expanduser().resolve(data not statically known)` |
| source_identity | expanduser | 632 | `Path(source_root).expanduser(data not statically known)` |
| source_identity | Path | 632 | `Path(source_root)` |
| source_identity | run | 635 | `subprocess.run([...], capture_output=True, text=True, check=True, timeout=10)` |
| source_identity | str | 636 | `str(root)` |
| source_identity | strip | 642 | `result.stdout.strip(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| process | `subprocess.run` | `source_identity` | 635 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `source_identity` | `Path(source_root).expanduser().resolve` | 632 |
| unresolved_call | `source_identity` | `Path(source_root).expanduser` | 632 |
| unresolved_call | `source_identity` | `result.stdout.strip` | 642 |

## Behavior

This flow starts at `source_identity` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
