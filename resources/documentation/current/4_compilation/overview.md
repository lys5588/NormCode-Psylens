# Compilation Overview

**How NormCode transforms natural language intent into executable plans.**

---

## Purpose

The NormCode compilation pipeline progressively formalizes intent into structure, taking you from a rough natural language idea to executable JSON repositories that the Orchestrator can run.

**This document provides**: High-level architecture, design philosophy, and the relationship between all compilation phases.

---

## The Pipeline

### Visual Overview

```
Natural Language Instruction
         ↓
    Phase 1: Derivation
         ↓
    _.ncds (draft straightforward)
         ↓
    Phase 2: Formalization
         ↓
    _.ncd (with flow indices and sequences)
         ↓
    Phase 3: Post-Formalization
         ↓
    _.pf.ncd (enriched with annotations)
         ↓
    Phase 4: Activation
         ↓
    repos/concept_repo.json + repos/inference_repo.json
         ↓
    Orchestrator Execution
```

### The Four Compilation Phases

| Phase | Input | Output | Purpose |
|-------|-------|--------|---------|
| **1. Derivation** | Natural language | `_.ncds` | Extract structure and hierarchy |
| **2. Formalization** | `_.ncds` | `_.ncd` (formal) | Add flow indices, sequence types, bindings |
| **3. Post-Formalization** | `_.ncd` (formal) | `_.pf.ncd` (enriched) | Add norms, resources, axis annotations |
| **4. Activation** | `_.pf.ncd` (enriched) | JSON repositories | Generate executable format |

**Note**: Execution is covered in detail in the [Execution Section](../3_execution/README.md). This section focuses on the four compilation phases.

### Combined Workflow Option

In practice, **Phases 2 and 3 are often combined**, producing `_.pf.ncd` directly from `_.ncds`:

```
_.ncds (Draft)
    ↓ Combined Formalization + Post-Formalization
_.pf.ncd (Post-Formalized, ready for activation)
    ↓ _.parse_to_nci.py
_.pf.nci.json (Intermediate)
    ↓ _.activate_nci.py
repos/concept_repo.json + repos/inference_repo.json
```

This is especially common when:
- Building complex workflows iteratively
- Using LLM-assisted generation
- Needing to see the complete picture (structure + configuration)

---

## Design Philosophy

### Progressive Formalization

NormCode follows a **progressive formalization** approach:

1. **Start flexible** - Natural language is ambiguous but accessible
2. **Add structure** - Hierarchical concepts emerge
3. **Add rigor** - Precise syntax removes ambiguity
4. **Add context** - Execution configuration is specified
5. **Make executable** - Final format for orchestrator

**Key insight**: Each phase answers a specific question while preserving the semantic intent of previous phases.

### The Questions Each Phase Answers

```
┌─────────────────────────────────────────────────┐
│  Phase 1: Derivation                             │
│  Question: WHAT are we trying to do?            │
│  Answer: Structure (concepts and operations)    │
├─────────────────────────────────────────────────┤
│  Phase 2: Formalization                          │
│  Question: IN WHAT ORDER and WHICH SEQUENCE?    │
│  Answer: Flow indices and sequence types        │
├─────────────────────────────────────────────────┤
│  Phase 3: Post-Formalization                     │
│  Question: HOW and WITH WHAT RESOURCES?         │
│  Answer: Norms, paradigms, file paths, axes     │
├─────────────────────────────────────────────────┤
│  Phase 4: Activation                             │
│  Question: WHAT DOES THE ORCHESTRATOR NEED?     │
│  Answer: working_interpretation structures      │
└─────────────────────────────────────────────────┘
```

---

## Phase 1: Derivation

### Goal

Transform unstructured natural language into hierarchical inference structure.

### What It Does

1. Identifies **concepts** (data entities)
2. Identifies **operations** (actions to perform)
3. Extracts dependencies (which concepts feed into which operations)
4. Creates hierarchical tree structure

### Example

**Input (Natural Language)**:
```
"Summarize this document by first cleaning it and then extracting key points."
```

**Output (`.ncds`)**:
```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content, removing headers
        <- raw document
```

**Key features**:
- Bottom-up reading (start from `raw document`, work upward)
- Simple markers (`<-`, `<=`)
- Natural language descriptions
- No flow indices yet
- No sequence types yet

### Details

See [Derivation](derivation.md) for complete specification.

---

## Phase 2: Formalization

### Goal

Add structural rigor to make the plan unambiguous and executable.

### What It Does

1. Assigns **unique flow indices** (e.g., `1.2.3`) to every step
2. Determines **sequence type** for each inference
   - Semantic: `imperative`, `judgement`
   - Syntactic: `assigning`, `grouping`, `timing`, `looping`
3. Resolves **concept identity** and **value bindings** (`<:{1}>`, `<:{2}>`)
4. Adds **metadata comments** (`?{sequence}:`, `?{flow_index}:`)

### Example

**Input (`.ncds`)**:
```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content
        <- raw document
```

**Output (`.ncd`)**:
```ncd
:<:{document summary} | ?{flow_index}: 1
    <= ::(summarize this text) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {clean text} | ?{flow_index}: 1.2
        <= ::(extract main content) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {raw document} | ?{flow_index}: 1.2.2
```

**Key changes**:
- Every line has a flow index
- Functional concepts have sequence types
- Root concept marked with `:<:`
- Semantic types added (`{}` for objects, `::()` for imperatives)
- **⚠️ Sibling pattern**: `{raw document}` is `1.2.2` (sibling of `1.2.1`), NOT `1.2.1.1`

### Details

See [Formalization](formalization.md) for complete specification.

---

## Phase 3: Post-Formalization

### Goal

Prepare the plan for execution by enriching it with configuration and grounding.

### What It Does

Three sub-phases:

#### 3.1. Re-composition

Maps abstract intent to the **normative context of execution**.

**Adds**:
- `%{norm_input}`: Paradigm ID to load (e.g., `h_PromptTemplate-c_Generate-o_Text`)
- `%{v_input_norm}`: Vertical input perception norm (e.g., `{prompt_location}`)
- `%{h_input_norm}`: Horizontal input perception norm (e.g., `{file_location}`)
- `%{body_faculty}`: Body faculty to invoke (e.g., `llm`, `file_system`)
- `%{o_shape}`: Output structure hint (e.g., `dict in memory`)

**The Normative Context**:

| Component | Location | Role |
|-----------|----------|------|
| **Body** | `infra/_agent/_body.py` | Agent's tools (file_system, llm, python_interpreter) |
| **Paradigms** | `infra/_agent/_models/_paradigms/` | Action norms (composition patterns) |
| **PerceptionRouter** | `infra/_agent/_models/_perception_router.py` | Perception norms (sign transmutation) |

#### 3.2. Provision

Fills in **concrete resources** within the established normative context.

**Adds**:
- `%{file_location}`: Path to ground data (e.g., `provision/data/price_data.json`)
- `%{v_input_provision}`: Path to prompt/script (e.g., `provision/prompts/sentiment.md`)

#### 3.3. Syntax Re-confirmation

Confirms **reference structure** (axes, shape, element type) for tensor coherence.

**Adds**:
- `%{ref_axes}`: Named axes (e.g., `[signal]`, `[_none_axis]`)
- `%{ref_shape}`: Tensor shape (e.g., `(n_signal,)`)
- `%{ref_element}`: Element type (e.g., `dict(...)`, `%{truth value}`)
- `%{ref_skip}`: Filter documentation (e.g., `filtered by <condition>`)

### Example

**Before Post-Formalization** (`.ncd`):
```ncd
:<:{document summary} | ?{flow_index}: 1
    <= ::(summarize this text) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {clean text} | ?{flow_index}: 1.2
```

**After Post-Formalization** (`.pf.ncd`):
```ncd
:<:{document summary} | ?{flow_index}: 1
    |%{ref_axes}: [_none_axis]
    |%{ref_element}: dict(summary: str)
    <= ::(summarize this text) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        |%{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
        |%{v_input_provision}: provisions/prompts/summarize.md
        |%{h_input_norm}: Literal
        |%{body_faculty}: llm
    <- {clean text} | ?{flow_index}: 1.2
        |%{ref_axes}: [_none_axis]
        |%{ref_element}: str
```

**Key changes**:
- Annotation lines added (starting with `|%{...}`)
- Paradigm specified with full naming convention
- Prompt path declared
- Reference structure declared
- Ready for activation

### Details

See [Post-Formalization](post_formalization.md) for complete specification.

---

## Phase 4: Activation

### Goal

Transform the annotated `.ncd` into executable JSON repositories that the Orchestrator can load and run.

### What It Does

1. Extracts **concept definitions** → `concept_repo.json`
2. Extracts **inference definitions** → `inference_repo.json`
3. Generates **working_interpretation** dicts for each inference
4. Maps `.ncd` syntax to the structures each sequence's IWI step expects

### Output Structure

**`concept_repo.json`**:
```json
[
  {
    "concept_name": "{document summary}",
    "type": "{}",
    "is_ground_concept": false,
    "is_final_concept": true,
    "reference_axis_names": ["_none_axis"],
    "reference_data": null
  }
]
```

**`inference_repo.json`**:
```json
[
  {
    "flow_info": {"flow_index": "1.1"},
    "inference_sequence": "imperative_in_composition",
    "concept_to_infer": "{document summary}",
    "function_concept": "::(summarize this text)",
    "value_concepts": ["{clean text}"],
    "working_interpretation": {
      "paradigm": "h_PromptTemplate-c_GenerateThinkJson-o_Literal",
      "value_order": {"{clean text}": 1},
      "workspace": {},
      "flow_info": {"flow_index": "1.1"}
    }
  }
]
```

**Key insight**: The `working_interpretation` dict contains exactly what each sequence's IWI (Input Working Interpretation) step needs to execute.

### Details

See [Activation](activation.md) for complete specification.

---

## Format Ecosystem

### The Relationship Between Formats

```
_.ncds (draft)
   ↓ Formalization (+ Post-Formalization)
_.pf.ncd (post-formalized)
   ↓ Parser
_.pf.nci.json (intermediate)
   ↓ Activator
repos/concept_repo.json + repos/inference_repo.json
   ↓ Load
Orchestrator
```

### Format Purposes

| Format | Created By | Read By | Purpose |
|--------|-----------|---------|---------|
| **`_.ncds`** | You/LLM | Compiler | Easy authoring (draft) |
| **`_.ncd`** | Compiler | Compiler | Formal syntax (intermediate) |
| **`_.pf.ncd`** | Compiler | Parser | Post-formalized with annotations |
| **`_.pf.nci.json`** | Parser | Activator | Parsed inference structure |
| **`concept_repo.json`** | Activator | Orchestrator | Concept repository |
| **`inference_repo.json`** | Activator | Orchestrator | Inference repository |

### The Activation Pipeline

```bash
# Step 1: Parse the post-formalized NCD to NCI (intermediate format)
python _.parse_to_nci.py

# Step 2: Activate the NCI to generate repositories
python _.activate_nci.py
```

**Output**: `repos/concept_repo.json` and `repos/inference_repo.json`

---

## The Semi-Formal Philosophy

### Why Not Fully Formal?

NormCode sits between pure natural language and fully formal code:

| Approach | Pros | Cons |
|----------|------|------|
| **Pure NL** | Expressive, accessible | Ambiguous, hard to execute |
| **Fully Formal** | Unambiguous, executable | Rigid, hard to write, requires expertise |
| **Semi-Formal (NormCode)** | Structured yet readable, LLM-friendly | Requires learning syntax |

### Progressive Refinement

The compilation pipeline enables **progressive refinement**:

1. **Draft quickly** in `.ncds` (natural language with minimal markers)
2. **Formalize** to `.ncd` (add rigor automatically)
3. **Enrich** with annotations (configure execution)
4. **Activate** to JSON (ready to run)

At each stage, you can:
- **Inspect** - See what the compiler generated
- **Modify** - Adjust before next phase
- **Validate** - Check correctness

### Round-Trip Consistency

You can go backwards:

```
JSON repositories → .ncd → .ncds
```

This enables:
- **Debugging**: Inspect compiled output in readable format
- **Version control**: Store as `.ncd` (text) instead of JSON
- **Modification**: Edit compiled plans and re-activate

---

## Key Compilation Concepts

### Flow Indices

**Hierarchical addresses** for every step in the plan.

**Format**: `1.2.3` where each number is a level in the tree.

**⚠️ CRITICAL: The Sibling Pattern**

```
1         Root concept
1.1         Functional concept (operation) - ALWAYS .1
1.2         Value concept (first input) - sibling of .1
1.2.1         Nested functional concept - child's .1
1.2.2         Nested value concept - sibling of child's .1
1.3         Value concept (second input) - sibling of 1.2
```

**Rules**:
1. **Functional concept is always `.1`** under its parent
2. **Value concept inputs are siblings** (`.2`, `.3`, `.4`), NOT children (`.1.1`, `.1.2`)
3. **Same depth = same index length**

**Common Mistake**:
```
# WRONG - nesting inputs under functional
1.1       Functional
1.1.1       Input 1  ← Should be 1.2
1.1.2       Input 2  ← Should be 1.3
```

**Purpose**:
- Unique identification
- Dependency tracking
- Checkpoint/resume markers
- Cross-references

### Sequence Types

**Categories of operations** that determine execution strategy.

**Semantic** (call LLMs):
- `imperative` - Execute commands (`::()`)
- `judgement` - Evaluate conditions (`::<>`)

**Syntactic** (deterministic):
- `assigning` - Data routing (`$=`, `$.`, `$+`, `$-`, `$%`)
- `grouping` - Collection creation (`&[{}]`, `&[#]`)
- `timing` - Execution control (`@:'`, `@:!`, `@.`)
- `looping` - Iteration (`*.`)

**Purpose**:
- Choose execution pipeline
- Cost estimation (semantic = tokens, syntactic = free)
- Dependency analysis

### Value Bindings

**Explicit ordering** of inputs in functional concepts.

**Syntax**: `<:{1}>`, `<:{2}>`, `<:{3}>` on value concepts

**Purpose**:
- Resolve ambiguity in multi-input operations
- Enable predictable value passing
- Support paradigm input mapping

**Example**:
```ncd
<= ::(sum {1} and {2} to get {3})
<- {first number}<:{1}>
<- {second number}<:{2}>
<- {result}<:{3}>
```

### Annotations

**Metadata comments** that configure execution.

**Types**:

| Prefix | Type | Purpose | Example |
|--------|------|---------|---------|
| `?{...}:` | Syntactical | Structure metadata | `?{flow_index}: 1.2.3` |
| `%{...}:` | Referential | Data configuration | `%{paradigm}: python_script` |
| `...:` | Derivation (un-decomposed) | Source text | `...: Calculate sum` |
| `?:` | Derivation (question) | Decomposition guide | `?: What operation?` |
| `/:` | Derivation (complete) | Description | `/: Computes total` |

**Purpose**:
- Guide execution without modifying syntax
- Declare configuration
- Enable tooling (validation, visualization)

---

## Compilation Guarantees

### What Compilation Ensures

1. **Syntactic Validity**: Every `.ncd` is parseable
2. **Flow Consistency**: Flow indices are unique and hierarchical
3. **Sequence Completeness**: Every inference has a valid sequence type
4. **Reference Structure**: All concepts have declared axes and types
5. **Resource Grounding**: All perceptual signs are linked to resources
6. **Working Interpretation**: Every inference has complete configuration

### What Compilation Does NOT Ensure

- **Semantic Correctness**: The plan might not do what you intend
- **Runtime Success**: LLM calls might fail, resources might be missing
- **Logical Soundness**: Dependencies might have cycles (detected by orchestrator)
- **Optimal Performance**: Some plans might be inefficient

**Compilation validates STRUCTURE, not INTENT.**

---

## Tradeoffs and Honest Assessment

### Costs of Compilation

| Challenge | Reality |
|-----------|---------|
| **Compilation Overhead** | Multi-phase pipeline takes time |
| **Syntax Density** | `.ncd` is verbose with annotations |
| **Learning Curve** | Understanding all phases takes effort |
| **Debugging Complexity** | Errors can occur at any phase |

### Why Accept These Costs?

1. **Auditability**: Know exactly what each step will do before execution
2. **Debuggability**: Inspect intermediate stages when things go wrong
3. **Flexibility**: Can intervene at any phase
4. **Reliability**: Progressive formalization catches issues early
5. **Optimization**: Can analyze and improve before running

**The honest tradeoff**: Compilation complexity pays off for complex, high-stakes workflows. For simple tasks, it's overkill.

---

## Tools and Automation

### Parser and Activator Scripts

**The two key scripts for activation**:

```bash
# Parse _.pf.ncd to intermediate NCI format
python _.parse_to_nci.py
# Output: _.pf.nci.json

# Activate NCI to generate repositories
python _.activate_nci.py
# Output: repos/concept_repo.json + repos/inference_repo.json
```

### Example Project Structure

```
project/
├── _.ncds                    # Draft (optional)
├── _.pf.ncd                  # Post-formalized plan
├── _.parse_to_nci.py         # Parser script
├── _.activate_nci.py         # Activator script
├── _.pf.nci.json             # Intermediate (generated)
├── repos/
│   ├── concept_repo.json     # Concept definitions
│   └── inference_repo.json   # Inference definitions
└── provisions/
    ├── prompts/              # Prompt templates
    ├── scripts/              # Python scripts
    └── paradigms/            # Paradigm JSON files
```

### LLM-Assisted Compilation

Plans are typically created with LLM assistance:

1. **Derivation**: LLM generates `_.ncds` from natural language
2. **Formalization + Post-Formalization**: LLM generates `_.pf.ncd` directly
3. **Activation**: Scripts parse and activate to JSON

The documentation files in this folder guide LLMs on correct patterns.

---

## Performance Considerations

### Compilation Time

| Phase | Typical Time | Factors |
|-------|--------------|---------|
| **Derivation** | Seconds-Minutes | LLM calls if used |
| **Formalization** | Milliseconds | Pure parsing |
| **Post-Formalization** | Seconds | Paradigm lookup, annotation injection |
| **Activation** | Milliseconds | JSON serialization |

**Total**: Usually under 1 minute for typical plans.

### Optimization Strategies

1. **Cache intermediate stages**: Save `.ncd` to skip re-formalization
2. **Batch compile**: Process multiple plans together
3. **Incremental compilation**: Only re-compile changed inferences
4. **Lazy annotation**: Defer post-formalization until execution

---

## Next Steps

After understanding the overview:

- **[Derivation](derivation.md)** - Phase 1 in detail
- **[Formalization](formalization.md)** - Phase 2 in detail
- **[Post-Formalization](post_formalization.md)** - Phase 3 in detail
- **[Activation](activation.md)** - Phase 4 in detail
- **[Examples](examples/)** - Working examples with parser and activator

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Progressive formalization** | Each phase adds specificity while preserving intent |
| **Four phases** | Derivation → Formalization → Post-Formalization → Activation |
| **Combined workflow** | Phases 2-3 often combined, producing `.pf.ncd` directly |
| **Semi-formal philosophy** | Balance between flexibility and rigor |
| **Parser + Activator** | Two scripts transform `.pf.ncd` to JSON repositories |

### ⚠️ Critical Lessons from Debugging

| Lesson | Detail |
|--------|--------|
| **Flow index sibling pattern** | Functional is `.1`, inputs are `.2`, `.3`, `.4` (NOT `.1.1`, `.1.2`) |
| **Explicit input references** | Operators MUST declare inputs as sibling value concepts |
| **LLM output format** | Prompts MUST specify `{"thinking": "...", "result": ...}` |
| **Value selectors** | Use `%{selector_packed}: true` for bundled data |
| **Loop state** | Use `%{is_invariant}: true` for persistent loop variables |
| **Empty lists** | Initialize with placeholder `(1,)`, not empty `(0,)` |

### The Compilation Promise

**NormCode's compilation transforms natural language into executable structure**:

1. Start with accessible natural language
2. Progressively add formalization
3. Enrich with execution context
4. Generate audit-ready JSON repositories
5. Execute with full traceability

**Result**: Plans that are both human-understandable and machine-executable.

---

**Ready to dive deeper?** Continue to [Derivation](derivation.md) to see how natural language becomes structure.
