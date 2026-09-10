# load_knowledge_schema

**Entry point:** `load_knowledge_schema` (`api`)
**Source:** [knowledge_model](../modules/knowledge_model.md)
**Modules touched:** [knowledge_model](../modules/knowledge_model.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_knowledge_schema
    participant p1 as resources.files(…).joinpath
    participant p2 as resources.files
    participant p3 as json.loads
    participant p4 as resource.read_text
    participant p5 as KnowledgeModelError
    participant p6 as isinstance
    p0-->>p1: resources.files(…).joinpath
    p0-->>p2: resources.files
    p0-->>p3: json.loads
    p0-->>p4: resource.read_text
    p0->>p5: KnowledgeModelError
    p0-->>p6: isinstance
    p0->>p5: KnowledgeModelError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_knowledge_schema"]
    s2["2. resources.files(…).joinpath"]
    s3["3. resources.files"]
    s4["4. json.loads"]
    s5["5. resource.read_text"]
    s6["6. KnowledgeModelError"]
    s7["7. isinstance"]
    s8["8. KnowledgeModelError"]
    s1 -. "resources.files(…).joinpath(KNOWLEDGE_SCHEMA_FILENAME)" .-> s2
    s1 -. "resources.files('llm_wiki_cli.schemas')" .-> s3
    s1 -. "json.loads(resource.read_text(...))" .-> s4
    s1 -. "resource.read_text(encoding='utf-8')" .-> s5
    s1 -->|"KnowledgeModelError('schema', ...)"| s6
    s1 -. "isinstance(payload, dict)" .-> s7
    s1 -->|"KnowledgeModelError('schema', 'packaged schema must be a JSON object')"| s8
    b0["filesystem_read resource.read_text"]
    s1 -. "filesystem_read resource.read_text" .-> b0
    click s1 "../modules/knowledge_model.md"
    click s6 "../modules/knowledge_model.md"
    click s8 "../modules/knowledge_model.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_knowledge_schema` | - | `KNOWLEDGE_SCHEMA_FILENAME`, `json`, `KNOWLEDGE_SCHEMA_FILENAME` | - | `payload` |
| `resources.files(…).joinpath` | - | - | - | - |
| `resources.files` | - | - | - | - |
| `json.loads` | - | - | - | - |
| `resource.read_text` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_knowledge_schema | resources.files(…).joinpath | 706 | `resources.files('llm_wiki_cli.schemas').joinpath(KNOWLEDGE_SCHEMA_FILENAME)` |
| load_knowledge_schema | resources.files | 706 | `resources.files('llm_wiki_cli.schemas')` |
| load_knowledge_schema | json.loads | 709 | `json.loads(resource.read_text(...))` |
| load_knowledge_schema | resource.read_text | 709 | `resource.read_text(encoding='utf-8')` |
| load_knowledge_schema | KnowledgeModelError | 717 | `KnowledgeModelError('schema', ...)` |
| load_knowledge_schema | isinstance | 720 | `isinstance(payload, dict)` |
| load_knowledge_schema | KnowledgeModelError | 721 | `KnowledgeModelError('schema', 'packaged schema must be a JSON object')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `resource.read_text` | `load_knowledge_schema` | 709 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `load_knowledge_schema` | `resources.files('llm_wiki_cli.schemas').joinpath` | 706 |
| external_call | `load_knowledge_schema` | `resources.files` | 706 |
| external_call | `load_knowledge_schema` | `isinstance` | 720 |

## Behavior

This flow starts at `load_knowledge_schema` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
