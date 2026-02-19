# Activation

**Phase 4: Generating executable JSON repositories from enriched `.pf.ncd` files.**

---

## Overview

**Activation** is the final phase of NormCode compilation. It transforms the enriched `.pf.ncd` file into executable JSON repositories that the Orchestrator can load and run.

**Input**: `.pf.ncd` (enriched with post-formalization annotations)  
**Output**: `concept_repo.json` + `inference_repo.json`

**Core Task**: Extract and structure all information needed by the Orchestrator's execution engine.

### The Activation Pipeline

```
_.pf.ncd (Post-Formalized Plan)
    ↓ _.parse_to_nci.py
_.pf.nci.json (Intermediate - parsed structure)
    ↓ _.activate_nci.py
repos/concept_repo.json + repos/inference_repo.json
```

The activator reads the parsed NCI (NormCode Intermediate) format and generates the final JSON repositories.

### Key Sub-Tasks

| Sub-Task | Purpose | Details |
|----------|---------|---------|
| **Extraction** | Parse `.ncd` structure | Extract concepts, inferences, annotations |
| **Provision (Supply)** | Validate and resolve resources | See [Provision in Activation](provision_in_activation.md) |
| **Structuring** | Build JSON repositories | Create `working_interpretation` for each sequence |

### The Demand/Supply Model

Post-Formalization **declares demands** (resource paths as annotations). Activation **supplies resources**:

| Phase | Role | What Happens |
|-------|------|--------------|
| **Post-Formalization** | **Demand** | Annotates paths: "I need a prompt at X" |
| **Activation (Provision)** | **Supply** | Validates and resolves: "X exists and is valid" |

---

## The Activation Problem

### Why Activation Is Needed

The `.pf.ncd` format is optimized for human readability and editability, but:
- The Orchestrator needs structured JSON
- Each sequence type expects specific `working_interpretation` fields
- References need initialization data
- Execution order needs to be determinable
- **Resource demands must be validated and resolved**

**Activation bridges the gap** between human-readable `.pf.ncd` and machine-executable JSON.

### ⚠️ CRITICAL: Flow Index Structure Requirements

The activator expects a specific flow index pattern. Getting this wrong causes runtime failures.

**Correct Pattern:**
```
1.7      - {parent value}           (depth 2)
  1.7.1  - <= (functional)          (depth 3) - ALWAYS .1
  1.7.2  - {input1}                 (depth 3) - sibling
  1.7.3  - {input2}                 (depth 3) - sibling
    1.7.3.1 - <= (child functional) (depth 4) - child's .1
    1.7.3.2 - <source>              (depth 4) - sibling of child functional
  1.7.4  - {input3}                 (depth 3) - sibling
```

**Rules:**
1. **Functional concept is always `.1`** - The operator/imperative is the first child
2. **Same depth = same index length** - Siblings have indices with same number of parts
3. **Value concepts are siblings, not children** - Inputs at same depth as functional
4. **Each functional can have its own child tree** - Nested inferences follow same pattern

**Common Mistake (causes bugs):**
```
# WRONG - nesting inputs under functional
1.7.1    - <= (functional)
  1.7.1.1  - {input1}  ← Should be 1.7.2
  1.7.1.2  - {input2}  ← Should be 1.7.3
```

### ⚠️ CRITICAL: Explicit Input References for Operators

Operators that reference concepts in their syntax (like `$. %>(<source>)`) **MUST** declare those concepts as sibling value concepts.

**WRONG - Missing input reference:**
```ncd
<- {AOC validity} | ?{flow_index}: 1.7.3
    <= $. %>(<AOC is valid>) | ?{flow_index}: 1.7.3.1 | ?{sequence}: assigning
    /: BUG: <AOC is valid> is referenced but not declared!
```

**CORRECT - Explicit input reference:**
```ncd
<- {AOC validity} | ?{flow_index}: 1.7.3
    <= $. %>(<AOC is valid>) | ?{flow_index}: 1.7.3.1 | ?{sequence}: assigning
    <- <AOC is valid> | ?{flow_index}: 1.7.3.2
```

**Why?** The scheduler builds a dependency graph from value concepts. Without explicit declarations, it doesn't know to wait for the source concept to complete.

**Symptom:** Value concept shows "empty" status even though source is "complete".

---

## Output Structure

### Two JSON Repositories

Activation generates two separate JSON files:

| File | Purpose | Contains |
|------|---------|----------|
| **`concept_repo.json`** | Static concept definitions | All data entities with types, axes, ground values |
| **`inference_repo.json`** | Operational definitions | All inferences with `working_interpretation` |

### Why Separate?

**Design Decision**: Separating concepts from inferences allows:
- Concepts to be reused across inferences
- Independent concept initialization
- Clear separation of data (concepts) vs logic (inferences)

---

## Concept Repository

### Purpose

**`concept_repo.json`** stores static definitions of all concepts in the plan—both **value concepts** (data entities) and **function concepts** (operations).

### Structure

```json
[
  {
    "id": "c-document",
    "concept_name": "{document}",
    "type": "{}",
    "flow_indices": ["1.2", "1.3.2"],
    "description": "Input document to process",
    "is_ground_concept": true,
    "is_final_concept": false,
    "reference_data": ["%{file_location}7f2(data/input.txt)"],
    "reference_axis_names": ["_none_axis"],
    "reference_element_type": "str",
    "natural_name": "document"
  },
  {
    "id": "c-summary",
    "concept_name": "{summary}",
    "type": "{}",
    "flow_indices": ["1"],
    "description": "Final summarized output",
    "is_ground_concept": false,
    "is_final_concept": true,
    "reference_data": null,
    "reference_axis_names": ["_none_axis"],
    "reference_element_type": "str",
    "natural_name": "summary"
  },
  {
    "id": "fc-summarize-the-text",
    "concept_name": "<= ::(summarize the text)",
    "type": "({})",
    "flow_indices": ["1.1"],
    "description": "Summarize the text",
    "is_ground_concept": false,
    "is_final_concept": false,
    "reference_data": null,
    "reference_axis_names": ["_none_axis"],
    "reference_element_type": "paradigm",
    "natural_name": "summarize the text"
  }
]
```

### Two Types of Concepts

| Type | Marker | Purpose | Examples |
|------|--------|---------|----------|
| **Value Concepts** | `{}`, `[]`, `<>` | Data entities | `{document}`, `[files]`, `<is valid>` |
| **Function Concepts** | `({})`, `<{}>` | Operations | `<= ::(summarize)`, `<= $. %>({x})` |

**Important**: Function concepts MUST be included in concept_repo.json. The orchestrator looks up each `function_concept` from inference_repo in the concept_repo.

### Fields

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `id` | string | Unique identifier for the concept | `"c-document"`, `"fc-summarize"` |
| `concept_name` | string | Full concept name with markers | `"{document}"`, `"<= ::(summarize)"` |
| `type` | string | Semantic type | `"{}"`, `"[]"`, `"<>"`, `"({})"`, `"<{}>"` |
| `flow_indices` | array | All flow indices where concept appears | `["1.2", "1.3.2"]` |
| `description` | string | Optional description | `"Input document to process"` |
| `is_ground_concept` | boolean | Pre-initialized? | `true` for inputs |
| `is_final_concept` | boolean | Final output? | `true` for root |
| `is_invariant` | boolean | Persist across loop iterations? | `true` for loop state |
| `reference_data` | array or null | Initial perceptual signs | `["%{file_location}(...)"]` |
| `axis_name` | string | Primary axis (for TVA) | `"cycle"`, `"_none_axis"` |
| `reference_axis_names` | array | Full axis list | `["_none_axis"]`, `["signal", "date"]` |
| `reference_element_type` | string | Element data type | `"str"`, `"paradigm"`, `"operator"` |
| `natural_name` | string | Human-readable name | `"document"`, `"summarize the text"` |

### ⚠️ Important: `axis_name` vs `reference_axis_names`

| Field | Purpose | Used By |
|-------|---------|---------|
| `axis_name` | **Primary** axis for list-to-axis conversion | TVA step |
| `reference_axis_names` | **Full list** of expected axes | Shape validation |

**When a paradigm returns a list**, TVA uses `axis_name` to create a new axis dimension:
- Script returns: `[{cycle: 1, events: [...]}, {cycle: 2, events: [...]}, ...]`
- TVA reads `concept.axis_name` (e.g., `"cycle"`)
- TVA creates Reference with shape `(N,)` along that axis

**Extraction from `.pf.ncd`:**
```python
axis_names = parse_axes(axes_str)  # From |%{ref_axes}: [cycle]
primary_axis_name = axis_names[0] if axis_names else "_none_axis"

concept_entry = {
    "axis_name": primary_axis_name,  # Primary for TVA
    "reference_axis_names": axis_names,  # Full list
    ...
}
```

### ID Prefixes

| Prefix | Concept Type | Example |
|--------|--------------|---------|
| `c-` | Value concept | `c-document`, `c-summary` |
| `fc-` | Function concept | `fc-summarize-the-text` |

### Extraction from `.ncd`

**Algorithm for Value Concepts**:

1. **Scan all value concepts** (`<-` lines) and context concepts (`<*` lines)
2. **Generate id** from concept name (e.g., `"{price data}"` → `"c-price-data"`)
3. **Extract concept name** from line
4. **Determine type** from markers (`{}`, `[]`, `<>`)
5. **Collect flow_indices**: Track all flow indices where this concept appears
6. **Check if ground**:
   - Has `:>:` marker?
   - No parent inference?
   - Has `$%` abstraction?
   - Has `|%{file_location}` annotation?
7. **Check if final**: Has `:<:` marker?
8. **Extract reference_data** from `|%{file_location}` or `$%` value
9. **Extract axes** from `|%{ref_axes}` annotation
10. **Generate natural_name** from concept name (strip markers)

**Algorithm for Function Concepts**:

1. **Scan all functional concepts** (`<=` lines)
2. **Generate id** from natural name (e.g., `"summarize the text"` → `"fc-summarize-the-text"`)
3. **Store full `nc_main`** as `concept_name` (e.g., `"<= ::(summarize the text)"`)
4. **Determine type**:
   - Judgement (contains `<{...}>`) → `"<{}>"`
   - All others (imperative, operators) → `"({})"`
5. **Collect flow_indices**: Track all flow indices where this function appears
6. **Set reference_element_type**:
   - Imperative/judgement → `"paradigm"`
   - Operators (`$`, `&`, `@`, `*`) → `"operator"`
7. **Extract natural_name** from the action description

**Why Function Concepts Are Required**:

The orchestrator's execution engine looks up each `function_concept` string from `inference_repo.json` in the `concept_repo.json`. If a function concept is missing, execution fails with:

```
'Function concept '<= ::(action name)' not found in ConceptRepo.'
```

**Example**:

**`.ncd` Input**:
```ncd
<- {price data} | ?{flow_index}: 1.2
    |%{file_location}: provision/data/prices.json
    |%{ref_axes}: [date]
    |%{ref_element}: perceptual_sign
```

**Concept Repo Entry**:
```json
{
  "id": "c-price-data",
  "concept_name": "{price data}",
  "type": "{}",
  "flow_indices": ["1.2", "1.6.2.2"],
  "description": "Price data retrieved from market sources",
  "is_ground_concept": true,
  "is_final_concept": false,
  "reference_data": ["%{file_location}price(provision/data/prices.json)"],
  "reference_axis_names": ["date"],
  "natural_name": "price data"
}
```

---

## Inference Repository

### Purpose

**`inference_repo.json`** stores operational definitions—what operations to execute and how.

### Structure

```json
[
  {
    "flow_info": {"flow_index": "1.1"},
    "inference_sequence": "imperative_in_composition",
    "concept_to_infer": "{summary}",
    "function_concept": "::(summarize the text)",
    "value_concepts": ["{clean text}"],
    "context_concepts": [],
    "working_interpretation": {
      "paradigm": "h_PromptTemplate-c_Generate-o_Text",
      "value_order": {"{clean text}": 1},
      "workspace": {},
      "flow_info": {"flow_index": "1.1"}
    }
  }
]
```

### Common Fields (All Sequences)

| Field | Type | Purpose |
|-------|------|---------|
| `flow_info` | dict | `{"flow_index": "1.2.3"}` |
| `inference_sequence` | string | Sequence type (e.g., `"imperative_in_composition"`) |
| `concept_to_infer` | string | Output concept name |
| `function_concept` | string | Operation definition |
| `value_concepts` | array | Input concept names (from `<-` lines) |
| `context_concepts` | array | Context concept names (from `<*` lines) |
| `working_interpretation` | dict | **Sequence-specific configuration** |

### The Critical Field: working_interpretation

**`working_interpretation`** is the key output of activation. It contains exactly what each sequence's IWI (Input Working Interpretation) step expects.

**Common sub-fields** (all sequences):
```json
{
  "workspace": {},
  "flow_info": {"flow_index": "1.2.3"}
}
```

**Sequence-specific fields**: Vary by sequence type (see below).

---

## Working Interpretation by Sequence Type

### 1. Imperative Sequence

**For**: `inference_sequence: "imperative_in_composition"`

**Required Fields**:
```json
{
  "paradigm": "v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal",
  "body_faculty": "llm",
  "value_order": {
    "{input 1}": 1,
    "{input 2}": 2
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Optional Fields**:
```json
{
  "value_selectors": {
    "{concept}": {
      "packed": true,
      "source": "{another_concept}",
      "key": "field_name",
      "index": 0,
      "unpack": false
    }
  },
  "values": {"{ground_concept}": "pre_set_value"},
  "create_axis_on_list_output": false
}
```

**Extraction**:
1. **paradigm**: From `|%{norm_input}` annotation
2. **body_faculty**: From `|%{body_faculty}` annotation (default: `"llm"`)
3. **value_order**: From `<:{N}>` bindings OR explicit `|%{value_order}` annotation
4. **value_selectors**: From `|%{selector_packed}`, `|%{selector_source}`, etc.
5. **values**: For ground concepts with direct values
6. **create_axis_on_list_output**: Based on output type (`[]` → false)

### ⚠️ Explicit Value Order (`%{value_order}`)

When an inference has many value concepts but only needs a subset as inputs, use explicit value_order:

```ncd
<= ::(combine information) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    | %{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    | %{value_order}: [{all testing information}]
```

**Generated working_interpretation:**
```json
"value_order": {
  "{all testing information}": 1
}
```

Without explicit `%{value_order}`, the activator infers from all value_concepts in the tree, which may include unwanted concepts.

### Value Selectors

When bundled data needs special handling:

| Annotation | Purpose | Selector Field |
|------------|---------|----------------|
| `%{selector_packed}: true` | Keep as single input | `"packed": true` |
| `%{selector_source}: {concept}` | Read from another concept | `"source": "{concept}"` |
| `%{selector_key}: field` | Select dict key | `"key": "field"` |
| `%{selector_index}: N` | Select list index | `"index": N` |
| `%{selector_unpack}: true` | Unpack into separate inputs | `"unpack": true` |

**Example `.pf.ncd`:**
```ncd
<- {all user inputs}<:{1}> | ?{flow_index}: 1.2.8.1.2.2
    | %{ref_axes}: [_none_axis]
    | %{ref_element}: dict
    | %{selector_packed}: true
```

**Generated value_selectors:**
```json
"value_selectors": {
  "{all user inputs}": {
    "packed": true
  }
}
```

### 2. Judgement Sequence

**For**: `inference_sequence: "judgement_in_composition"`

**Same as Imperative, PLUS**:
```json
{
  "assertion_condition": {
    "quantifiers": {
      "axis": "for-each",
      "concept": "{signal}"
    },
    "condition": true
  }
}
```

**Extraction**:
- **assertion_condition**: From truth assertion in functional concept
  - `<ALL True>` → `{"quantifiers": {"axis": "all"}, "condition": true}`
  - `<FOR EACH {x} True>` → `{"quantifiers": {"axis": "for-each", "concept": "{x}"}, "condition": true}`

### 3. Assigning Sequence

**For**: `inference_sequence: "assigning"`

**Required Fields**:
```json
{
  "syntax": {
    "marker": ".",
    "assign_source": "{source}"
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Marker-Specific Fields**:

| Marker | Operator | Required Fields |
|--------|----------|-----------------|
| `"="` (identity) | `$=` | `canonical_concept`, `alias_concept` |
| `"%"` (abstraction) | `$%` | `face_value`, `axis_names` |
| `"."` (specification) | `$.` | `assign_source` (can be string or array) |
| `"+"` (continuation) | `$+` | `assign_source`, `assign_destination`, `by_axes` |
| `"-"` (derelation) | `$-` | `selector` |

### Specification Operator (`$.`)

**Syntax**: `$. %>({output}) %<[{src1}, {src2}]` or `$. %>({output})`

**Source Selection Priority**:
1. **Annotation** (highest): `%{assign_sources}: [{src1}, {src2}]`
2. **Inline list**: `%<[{src1}, {src2}]`
3. **Inline single** (fallback): `%>({X})` - X is both output and source

**Example:**
```ncd
<= $. %>({output}) | ?{sequence}: assigning
    | %{assign_sources}: [{src1}, {src2}, {src3}]
```

**Generated syntax:**
```json
"syntax": {
  "marker": ".",
  "assign_source": ["{src1}", "{src2}", "{src3}"]
}
```

### Continuation Operator (`$+`)

**Syntax**: `$+ %>([destination]) %<({source}) %:(axis)`

**Example:**
```ncd
<= $+ %>([AOC schemas records]) %<({new AOC}) %:(_none_axis) | ?{sequence}: assigning
```

**Generated syntax:**
```json
"syntax": {
  "marker": "+",
  "assign_source": "{new AOC}",
  "assign_destination": "[AOC schemas records]",
  "by_axes": "_none_axis"
}
```

**Note**: Use `%:(_none_axis)` when appending to lists with grouped values (shape `(1,)` on `_none_axis`).

### Abstraction Operator (`$%`)

**Syntax**: `$% %>([%(literal_value)])`

**Annotation for literal value**: `%{literal<$% name>}: value`

**Example:**
```ncd
<= $% %>([%(1)]) | ?{sequence}: assigning
    | %{literal<$% counters>}: [1]
```

**Generated syntax:**
```json
"syntax": {
  "marker": "%",
  "face_value": ["%(1)"],
  "axis_names": ["counter"]
}
```

**Important**: The activator must preserve the literal wrapper notation (`%(1)`) in `face_value`, not parse it to raw values.

**Extraction**:
1. **marker**: From operator symbol (`$=` → `"="`, `$.` → `"."`, etc.)
2. **assign_source**: From `%>({concept})` or `%<({concept})` depending on operator
3. **assign_destination**: From `%>([dest])` for continuation
4. **by_axes**: From `%:(axis)` modifier
5. **face_value**: From `%{literal<$% name>}` annotation (preserves literal wrapper)
6. **selector**: From `%^(<selector>)` modifier

### 4. Grouping Sequence

**For**: `inference_sequence: "grouping"`

**Two Grouping Operators**:

| Operator | Marker | Result | Use Case |
|----------|--------|--------|----------|
| `&[{}]` | `"in"` | Dict with labeled keys | Bundle named items |
| `&[#]` | `"across"` | Flat list | Collect items |

**Required Fields**:
```json
{
  "syntax": {
    "marker": "in",
    "sources": ["{source1}", "{source2}"],
    "create_axis": null,
    "by_axes": [["_none_axis"], ["_none_axis"]]
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

### ⚠️ Grouping WITHOUT Axis Creation (Packed Output)

When `%+(axis)` is NOT specified, `create_axis` is `null`:

```ncd
<= &[#] %>[{source}] | ?{sequence}: grouping
    /: NO %+(axis) = packed output with shape (1,)
```

**Generated syntax:**
```json
"syntax": {
  "marker": "across",
  "sources": ["{source}"],
  "create_axis": null,
  "by_axes": [["_none_axis"]]
}
```

**Result**: Shape `(1,)` with all items wrapped in single element.

### Grouping WITH Axis Creation

When `%+(axis)` IS specified:

```ncd
<= &[#] %>[{source}] %+(new_axis) | ?{sequence}: grouping
```

**Generated syntax:**
```json
"syntax": {
  "marker": "across",
  "sources": ["{source}"],
  "create_axis": "new_axis",
  "by_axes": [["_none_axis"]]
}
```

**Result**: Shape `(N,)` with N separate elements along `new_axis`.

### `by_axes` Field

The `by_axes` field specifies which axes to collapse from **each** input:

```json
"by_axes": [["_none_axis"], ["_none_axis"], ["_none_axis"]]
```

- One entry per value concept (source)
- Each entry is a list of axes to collapse from that input
- `["_none_axis"]` collapses the singleton axis from each input

**Extraction**:
1. **marker**: From operator (`&[{}]` → `"in"`, `&[#]` → `"across"`)
2. **sources**: From `%>[{src1}, {src2}]` modifier
3. **create_axis**: From `%+(axis_name)` modifier, or `null` if not present
4. **by_axes**: Build as `[["_none_axis"]]` for each value concept
5. **protect_axes**: From `<$!{axis}>` markers (rarely used)

### 5. Timing Sequence

**For**: `inference_sequence: "timing"`

**Required Fields**:
```json
{
  "syntax": {
    "marker": "if",
    "condition": "<validation passed>"
  },
  "blackboard": null,
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Extraction**:
1. **marker**: From operator (`@:'` → `"if"`, `@:!` → `"if!"`, `@.` → `"after"`)
2. **condition**: From concept in parentheses
3. **blackboard**: Set to `null` (orchestrator provides at runtime)

### 6. Looping Sequence

**For**: `inference_sequence: "looping"` or `"quantifying"`

**Required Fields**:
```json
{
  "syntax": {
    "marker": "every",
    "loop_index": 1,
    "LoopBaseConcept": "{documents}",
    "CurrentLoopBaseConcept": "{document}*1",
    "group_base": "document",
    "InLoopConcept": {"{carry}*1": 1},
    "ConceptToInfer": ["{summary}"]
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Extraction**:
1. **marker**: Always `"every"` (only type implemented)
2. **loop_index**: From `%@(N)` modifier
3. **LoopBaseConcept**: From `%>({base})` modifier
4. **CurrentLoopBaseConcept**: Auto-generated as `{base}*N`
5. **group_base**: From `%:({axis})` modifier (strip braces)
6. **InLoopConcept**: From context concepts with `<$*-N>` markers
7. **ConceptToInfer**: From `%<({result})` modifier

---

## Provision: The Supply Side

During activation, resource demands from Post-Formalization are validated and resolved.

**For detailed documentation, see [Provision in Activation](provision_in_activation.md).**

### ⚠️ CRITICAL: Provision Happens During Activation, Not Post-Formalization

**Common Automation Mistake**: Filling in concrete resource paths (`%{v_input_provision}`) during post-formalization.

**WRONG** - Provision mixed into post-formalization:
```ncd
/: During post-formalization, I filled in BOTH normative context AND concrete resources:
<= ::(research and write this section) | ?{flow_index}: 1.4.2.1 | ?{sequence}: imperative
    | %{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    | %{v_input_norm}: prompt_location
    | %{v_input_provision}: provisions/prompts/write_section.md  /: ❌ Provision here
    | %{h_input_norm}: Literal
```

**CORRECT** - Separate phases:

**Post-Formalization** (normative context only):
```ncd
<= ::(research and write this section) | ?{flow_index}: 1.4.2.1 | ?{sequence}: imperative
    | %{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    | %{v_input_norm}: prompt_location
    | %{h_input_norm}: Literal
    | %{body_faculty}: llm
    /: NO provision paths here - just the normative framework
```

**Activation + Provision** (concrete resources):
```ncd
/: During activation, provision paths are filled in:
<= ::(research and write this section) | ?{flow_index}: 1.4.2.1
    | %{v_input_provision}: provisions/prompts/write_section.md
    /: Resource paths filled during activation phase
```

**Why Separate?**
- Allows reusing the same formalized plan with different provisions
- Enables updating prompts without re-running formalization
- Creates clear audit trail of what decisions were made at each phase
- Maintains separation of concerns: "how" (post-formalization) vs "with what" (provision)

### Prompt Template Variable Format

Prompt templates referenced by `%{v_input_provision}` should use the proper variable format:

**WRONG** - Raw placeholders:
```markdown
## User Message

$input_1

## Available Commands

$input_2
```

**CORRECT** - XML-wrapped placeholders:
```markdown
## User Message

<user_message>
$input_1
</user_message>

## Available Commands

<command_schema>
$input_2
</command_schema>
```

**Rules**:
1. Use `$input_x` format (not `{1}` or other variations)
2. Wrap each in descriptive XML tags: `<descriptive_name>$input_x</descriptive_name>`
3. This ensures safe parsing and self-documenting templates

### Summary

| Resource Type | Demand (Post-Formalization) | Supply (Activation) |
|---------------|----------------------------|---------------------|
| **Paradigms** | `\|%{norm_input}: paradigm-id` | Load JSON, validate structure |
| **Prompts** | `\|%{v_input_provision}: path` | Validate file exists, check variable format |
| **Data files** | `\|%{file_location}: path` | Validate, create perceptual signs |
| **Scripts** | Referenced by paradigm | Validate script exists |

### Key Outputs

After provision, the `working_interpretation` contains:
- Validated paradigm IDs
- Resolved prompt paths
- Ground concept `reference_data` with perceptual signs

---

## Paradigm Integration During Activation

### How Paradigms Execute

Paradigms are JSON specifications that define how semantic operations execute. During activation, paradigms are loaded and their specifications become part of the `working_interpretation`.

**Key Insight**: The paradigm defines the *interface* (what input types are expected). The provision step provides the *paths* and configures value concept annotations.

### The MVP-Paradigm Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MVP (Memory Value Perception)                                          │
│  For each value concept:                                                │
│    • If annotation is a PERCEPTUAL SIGN (|%{file_location}: path)       │
│      → PerceptionRouter perceives it → produces LITERAL content         │
│    • If annotation is a LITERAL (|%{literal<$% ...>}: value)            │
│      → Pass value as-is → no perception                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PARADIGM (Composed Function)                                           │
│  Receives what MVP produces:                                            │
│    • h_Literal → expects literal data (MVP perceived the sign)          │
│    • h_FilePath → expects file path (MVP passed literal through)        │
│      → Paradigm's composition reads the file internally                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Vertical Input Extraction in Paradigms

Vertical inputs (prompts, scripts) arrive at the paradigm wrapped in perceptual signs. The paradigm's `sequence_spec` must **extract the raw path** before using it.

**The `states.vertical` Structure**: During MFP, the orchestrator populates `states.vertical` with the vertical input value (a perceptual sign like `%{prompt_location}abc(provisions/prompts/task.md)`).

**Extraction Pattern** - Use `perception_router.strip_sign`:
```json
{
  "output_key": "prompt_path",
  "function": {"__type__": "MetaValue", "key": "perception_router.strip_sign"},
  "params": {"__positional__": {"__type__": "MetaValue", "key": "states.vertical"}}
}
```

**Result**: `"provisions/prompts/task.md"` (the raw path, stripped of the sign wrapper)

### ⚠️ CRITICAL: Read Resources During MFP, Not in Composition

**The composed function (TVA) cannot access step results from MFP.** Resources must be fully loaded during MFP steps, not inside the composition plan.

**WRONG** - Reading in composition:
```json
{
  "step_index": 1,
  "affordance": "perception_router.strip_sign",
  "result_key": "raw_prompt_path"
},
{
  "step_index": 2,
  "affordance": "composition_tool.compose",
  "params": {
    "plan": [
      {
        "output_key": "prompt_content",
        "function": {"__type__": "MetaValue", "key": "read_fn"},
        "params": {"__positional__": {"__type__": "MetaValue", "key": "raw_prompt_path"}}
      }
    ]
  }
}
```
**Error**: `Key 'path/to/prompt.md' not found in context`

**CORRECT** - Reading during MFP:
```json
{
  "step_index": 1,
  "affordance": "perception_router.strip_sign",
  "result_key": "raw_prompt_path"
},
{
  "step_index": 2,
  "affordance": "prompt_tool.read_now",
  "params": {
    "template_name": {"__type__": "MetaValue", "key": "raw_prompt_path"}
  },
  "result_key": "prompt_obj"
},
{
  "step_index": 3,
  "affordance": "prompt_tool.create_template_function",
  "params": {
    "template": {"__type__": "MetaValue", "key": "prompt_obj"}
  },
  "result_key": "template_fn"
},
{
  "step_index": 4,
  "affordance": "composition_tool.compose",
  "params": {
    "plan": [
      {
        "output_key": "filled_prompt",
        "function": {"__type__": "MetaValue", "key": "template_fn"},
        "params": {"__positional__": "__initial_input__"}
      }
    ]
  }
}
```

**Why this works**: The prompt is read and transformed into a function (`template_fn`) during MFP. The composition only uses the resulting function, not raw data from earlier steps.

---

## Extraction Strategy

### Meet from Both Ends

Activation uses a **bidirectional approach**:

1. **Bottom-up (Execution Requirements)**: Know what each IWI step expects
2. **Top-down (Extraction Rules)**: Parse `.pf.ncd` syntax to produce that structure

### Annotation Pattern Reference

The activator extracts fields from these annotation patterns:

| Annotation | Pattern | Purpose | Example |
|------------|---------|---------|---------|
| `%{name}: value` | `r"%\{(\w+)\}:\s*(.+)"` | Key-value annotation | `%{ref_axes}: [signal]` |
| `%{literal<$% X>}: value` | `r"%\{literal<\$([%=.+-])\s*([^>]+)>\}:\s*(.+)"` | Literal for abstraction | `%{literal<$% counters>}: [1]` |
| `<:{N}>` | `r"<:\{(\d+)\}>"` | Input binding order | `<:{1}>`, `<:{2}>` |
| `%>({concept})` | `r"%>\(\{([^}]+)\}\)"` | Output/source (object) | `%>({result})` |
| `%>[{concept}]` | `r"%>\(\[([^\]]+)\]\)"` | Output/source (relation) | `%>[{items}]` |
| `%<({concept})` | `r"%<\(\{([^}]+)\}\)"` | Source element | `%<({new item})` |
| `%:(axis)` | `r"%:\(([^)]+)\)"` | Axis name | `%:(_none_axis)` |
| `%+(axis)` | `r"%\+\(([^)]+)\)"` | Create axis (grouping) | `%+(signal)` |
| `%{value_order}: [...]` | Custom parser | Explicit input ordering | `%{value_order}: [{a}, {b}]` |
| `%{selector_packed}: true` | `r"%\{selector_packed\}:\s*(.+)"` | Keep bundled | `%{selector_packed}: true` |
| `%{is_invariant}: true` | `r"%\{is_invariant\}:\s*(.+)"` | Loop persistence | `%{is_invariant}: true` |

### The Syntax Mapping Task

**Core challenge**: Transform dense `.pf.ncd` annotations into structured `working_interpretation` dicts.

**Algorithm**:

```python
def activate_inference(ncd_inference):
    # 1. Extract basic fields
    flow_index = extract_flow_index(ncd_inference)
    sequence_type = extract_sequence_type(ncd_inference)
    concept_to_infer = extract_concept_to_infer(ncd_inference)
    function_concept = extract_function_concept(ncd_inference)
    value_concepts = extract_value_concepts(ncd_inference)
    context_concepts = extract_context_concepts(ncd_inference)
    
    # 2. Build working_interpretation based on sequence_type
    if sequence_type == "imperative_in_composition":
        wi = build_imperative_wi(ncd_inference)
    elif sequence_type == "judgement_in_composition":
        wi = build_judgement_wi(ncd_inference)
    elif sequence_type == "assigning":
        wi = build_assigning_wi(ncd_inference)
    elif sequence_type == "grouping":
        wi = build_grouping_wi(ncd_inference)
    elif sequence_type == "timing":
        wi = build_timing_wi(ncd_inference)
    elif sequence_type == "looping":
        wi = build_looping_wi(ncd_inference)
    
    # 3. Return inference entry
    return {
        "flow_info": {"flow_index": flow_index},
        "inference_sequence": sequence_type,
        "concept_to_infer": concept_to_infer,
        "function_concept": function_concept,
        "value_concepts": value_concepts,
        "context_concepts": context_concepts,
        "working_interpretation": wi
    }
```

---

## Complex Extraction: Value Selectors

### The Problem

Some `working_interpretation` dicts contain **intermediate keys** that don't appear in `value_concepts`.

**Example**:
```json
{
  "value_order": {
    "{input files}": 0,
    "input_files_as_dict": 1,
    "other_input_files": 2
  },
  "value_selectors": {
    "input_files_as_dict": {
      "source_concept": "{input files}",
      "key": "{original prompt}"
    },
    "other_input_files": {
      "source_concept": "{input files}",
      "key": "{other files}",
      "unpack": true
    }
  }
}
```

**Observation**: `"input_files_as_dict"` and `"other_input_files"` are NOT in `value_concepts`, but they ARE in `value_order`.

### Why This Happens

**Answer**: Concept provenance tracking.

When `{input files}` was created by a `&[{}]` (group-in) operation:
```ncd
<- {input files}
    <= &[{}]
    <- {original prompt}
    <- {other files}
```

The activation compiler knows:
1. `{input files}` is a dictionary with keys `"{original prompt}"` and `"{other files}"`
2. The paradigm needs these as separate inputs
3. Generate `value_selectors` to extract them

### Extraction Rules for value_selectors

**Trigger**: When a value concept was created by `&[{}]` grouping.

**Algorithm**:
1. **Trace concept provenance**: How was this concept created?
2. **If created by `&[{}]`**: Extract the sub-concept keys
3. **Generate value_selectors**: One per sub-concept
4. **Add to value_order**: Create intermediate keys

**Selector Fields**:

| Field | Purpose | Example |
|-------|---------|---------|
| `source_concept` | Which concept to extract from | `"{input files}"` |
| `key` | Dictionary key to extract | `"{original prompt}"` |
| `index` | Array index (for lists) | `0`, `-1` |
| `unpack` | Flatten/spread | `true` |
| `branch` | Perceptual sign control | `{"path": "NULL", "content": "file_location"}` |

### Branch Field

**Purpose**: Control perceptual sign transmutation.

**Example**:
```json
{
  "branch": {
    "path": "NULL",
    "content": "file_location"
  }
}
```

**Meaning**:
- `"path": "NULL"` - No path transformation
- `"content": "file_location"` - Extract file location string

**When used**: For concepts that are perceptual signs requiring transmutation.

---

## Ground Concept Identification

### What Makes a Concept "Ground"?

A concept is **ground** if it's pre-initialized (not computed by an inference).

**Criteria**:
1. Has `:>:` marker (explicit input marker)
2. Created by `$%` abstraction operator
3. Has `|%{file_location}` annotation
4. No parent inference (leaf node)
5. Marked in compilation configuration

### Extraction

**Algorithm**:
```python
def is_ground_concept(concept_ncd):
    if has_input_marker(concept_ncd):  # :>:
        return True
    if has_abstraction(concept_ncd):  # $%
        return True
    if has_file_location_annotation(concept_ncd):
        return True
    if no_parent_inference(concept_ncd):
        return True
    return False
```

**Ground concepts** get `reference_data` populated in `concept_repo.json`.

---

## Activation Validation

### Pre-Activation Checks

Before running activation, ensure:

- [ ] All inferences have flow indices
- [ ] All functional concepts have sequence types
- [ ] Paradigm annotations present (for semantic sequences)
- [ ] Axes declared (for all concepts)
- [ ] Resource paths exist (for ground concepts)

### Post-Activation Checks

After generating repositories, validate:

- [ ] All concepts in `concept_repo.json`
- [ ] All inferences in `inference_repo.json`
- [ ] All `working_interpretation` dicts complete
- [ ] All required fields present
- [ ] No orphaned references

### Common Activation Errors

| Error | Symptom | Fix |
|-------|---------|-----|
| **Missing paradigm** | No `paradigm` field in WI | Add `\|%{norm_input}` annotation |
| **Missing value_order** | Empty `value_order` dict | Add value bindings (`<:{N}>`) or `%{value_order}` |
| **Invalid flow_index** | Non-hierarchical indices | Re-run formalization |
| **Missing axes** | `reference_axis_names` is null | Add `\|%{ref_axes}` annotation |
| **Wrong sequence type** | IWI expects different fields | Fix `?{sequence}:` marker |

### ⚠️ Critical Errors from Debugging

| Error | Symptom | Fix |
|-------|---------|-----|
| **Function concept not found** | `'Function concept '<= ::()' not found in ConceptRepo'` | Ensure activator adds function concepts to concept_repo |
| **Missing assign_source** | `AR failed: 'assign_source' must be specified` | Add explicit input reference as sibling value concept |
| **Missing assign_destination** | `AR failed for continuation (+)` | Add `%>([dest])` and `%<({src})` to `$+` operator |
| **Wrong flow index nesting** | Inputs at `.1.1` instead of `.2` | Fix flow indices - inputs are siblings of functional |
| **Empty reference status** | Value concept "empty" but source "complete" | Add explicit input reference for operators |
| **Shape mismatch** | Cross product with `(0,)` produces nothing | Initialize lists with placeholder `(1,)` |
| **Too many inputs** | Wrong concepts passed to paradigm | Use explicit `%{value_order}` |
| **Literal not preserved** | `%(1)` becomes `1` | Use `extract_literal_annotation_value` to preserve wrapper |

### ⚠️ Paradigm-Related Runtime Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| **`KeyError: 'paradigm_config'`** | Paradigm tries to access `states.function.paradigm_config.vertical.*` | Use `perception_router.strip_sign` on `states.vertical` instead |
| **`Key 'path/to/file' not found in context`** | Composition plan references a step result that isn't available during TVA | Read resources during MFP steps, not inside composition |
| **`AttributeError: 'NoneType' has no attribute 'main'`** | Paradigm calls `main` but script doesn't define it | Add a `main` function alias to the script |
| **Wrong prompt variable format** | Template uses `{1}` instead of `$input_1` | Use `<name>$input_x</name>` XML-wrapped format |

### ⚠️ Activator Indentation Bug (Critical)

**Problem**: Python code running outside intended conditional blocks.

```python
# BUG: This runs for ALL markers and OVERWRITES!
if marker == "%":
    wi["syntax"] = {"marker": "%", "face_value": ...}
elif marker == ".":
    wi["syntax"] = {"marker": ".", "assign_source": ...}

wi["syntax"] = {"marker": marker, "assign_source": None}  # OVERWRITES!
```

**Fix**: Ensure all syntax assignments are inside their respective blocks:
```python
else:
    # Only for unhandled markers
    wi["syntax"] = {"marker": marker, "assign_source": None}
```

---

## Tools and Automation

### Automated Activation

**Command** (if implemented):
```bash
python compiler.py activate enriched.ncd
```

**Output**: `enriched.concept.json` and `enriched.inference.json`

### Manual Activation

**Not recommended** - the extraction logic is complex and error-prone.

**Use automated tools** whenever possible.

### Validation Tools

**Command**:
```bash
python compiler.py validate-repos concept_repo.json inference_repo.json
```

**Checks**:
- All required fields present
- Field types correct
- References are valid
- Sequences match expectations

---

## Round-Trip: Repositories → .ncd

### Why Round-Trip Matters

Being able to go **backwards** (JSON → `.ncd`) enables:
- **Debugging**: Inspect compiled output in readable format
- **Version control**: Store as text instead of JSON
- **Modification**: Edit compiled plans
- **Validation**: Ensure compilation is lossless

### Deactivation Process

**Algorithm**:
```python
def deactivate(concept_repo, inference_repo):
    # 1. Reconstruct inference tree from flow_indices
    tree = build_tree(inference_repo)
    
    # 2. For each inference, reconstruct .ncd lines
    ncd_lines = []
    for inference in tree:
        ncd_lines.append(concept_to_ncd(inference))
        ncd_lines.append(function_to_ncd(inference))
        ncd_lines.extend(values_to_ncd(inference))
        ncd_lines.extend(contexts_to_ncd(inference))
        ncd_lines.extend(annotations_to_ncd(inference))
    
    # 3. Return formatted .ncd
    return format_ncd(ncd_lines)
```

**Challenges**:
- Reconstructing indentation from flow indices
- Determining which annotations to include
- Handling value_selectors (synthetic keys)

---

## Performance Considerations

### Activation Time

**Typical**: < 1 second for plans with 50 inferences

**Factors**:
- Number of inferences
- Complexity of value_selectors
- Paradigm lookup time

### Optimization Strategies

1. **Cache paradigm lookups**: Don't re-read paradigm files
2. **Batch concept extraction**: Process all concepts in one pass
3. **Lazy validation**: Only validate on demand

---

## Related Topics

- **[Provision in Activation](provision_in_activation.md)** - How resource demands are validated and resolved (the supply side)
- **[Post-Formalization](post_formalization.md)** - How resource demands are declared (the demand side)
- **[Paradigms](examples/paradigms/paradigms.md)** - Complete paradigm specification and design patterns

## Next Steps

After activation:

- **[Execution Section](../3_execution/README.md)** - How the orchestrator runs the generated repositories

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Two repositories** | Concepts (data) separated from inferences (logic) |
| **working_interpretation** | Critical field containing sequence-specific configuration |
| **Syntax mapping** | Transform `.pf.ncd` annotations to WI dicts |
| **Value selectors** | Handle `packed`, `source`, `key`, `index` annotations |
| **Ground concepts** | Pre-initialized with reference_data |
| **Round-trip** | Can go from JSON back to `.pf.ncd` |

### ⚠️ Critical Lessons from Debugging

| Lesson | Detail |
|--------|--------|
| **Flow index sibling pattern** | Functional is `.1`, inputs are `.2`, `.3`, `.4` (NOT `.1.1`, `.1.2`) |
| **Explicit input references** | Operators MUST declare inputs as sibling value concepts |
| **Function concepts required** | Must be in concept_repo.json or orchestrator fails |
| **axis_name vs reference_axis_names** | TVA uses `axis_name`, validation uses `reference_axis_names` |
| **Preserve literal wrappers** | `%(1)` must stay as `%(1)` in face_value, not become `1` |
| **is_invariant field** | Loop state containers need `is_invariant: true` |
| **Grouping create_axis** | `null` = packed `(1,)`, `"axis"` = expanded `(N,)` |
| **by_axes for each input** | One `["_none_axis"]` entry per source concept |
| **Provision happens in activation** | NOT during post-formalization; keep phases separate |
| **Prompt template format** | Use `<name>$input_x</name>` XML-wrapped placeholders |
| **Read resources during MFP** | Paradigm composition cannot access MFP step results directly |
| **Use strip_sign for vertical inputs** | Access `states.vertical` via `perception_router.strip_sign` |

### Required Fields by Sequence Type

| Sequence | Required in `syntax` |
|----------|---------------------|
| **assigning** (abstraction `%`) | `marker`, `face_value`, `axis_names` |
| **assigning** (specification `.`) | `marker`, `assign_source` |
| **assigning** (continuation `+`) | `marker`, `assign_source`, `assign_destination`, `by_axes` |
| **grouping** | `marker`, `sources`, `create_axis`, `by_axes` |
| **looping** | `marker`, `LoopBaseConcept`, `CurrentLoopBaseConcept`, `ConceptToInfer` |
| **imperative/judgement** | `paradigm`, `body_faculty`, `value_order` |

### The Activation Promise

**Activation makes plans executable**:

1. Enriched `.pf.ncd` → Structured JSON repositories
2. Each sequence gets exactly what it needs
3. Ground concepts pre-initialized
4. Function concepts included for orchestrator lookup
5. **Provision completes** - concrete resources resolved (separate from post-formalization's normative context)
6. **Paradigms validated** - JSON loaded, structure verified
7. Ready for orchestrator loading
8. Fully auditable and traceable

**Result**: Executable repositories that the orchestrator can load and run, with complete traceability back to source `.pf.ncd`.

---

**Ready to execute?** See the [Execution Section](../3_execution/README.md) to understand how the orchestrator runs these repositories.
