# Paradigm - Complete Extraction

*Extracted from: Provision: The New Vision*

---

## Core Definition

**Paradigms** are declarative JSON specifications that define how semantic operations execute. They bridge data types and tools.

**Key insight**:
- The paradigm defines the *interface* (what input types are expected)
- The provision step provides the *paths* and configures value concept annotations
- **Where perception happens depends on h_input_norm**: MVP (`h_Literal`) or paradigm (`h_FilePath`)

---

## The Core Principle: Paradigm is a Continuation of MVP

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

---

## Paradigm Structure

Paradigms have three main sections:

```json
{
  "metadata": {
    "description": "What this paradigm does",
    "inputs": {
      "vertical": { /* setup-time inputs (prompts, configs) */ },
      "horizontal": { /* runtime inputs (data from value concepts) */ }
    },
    "outputs": { /* output format */ }
  },
  "env_spec": {
    "tools": [ /* tools and affordances available */ ]
  },
  "sequence_spec": {
    "steps": [
      /* Steps 1..N-1: Prepare individual morphisms */
      /* Step N: composition_tool.compose → instruction_fn */
    ]
  }
}
```

### The `sequence_spec` Pattern

1. **Steps 1 to N-1**: Prepare individual morphisms by getting affordance functions from tools
2. **Final step**: `composition_tool.compose` combines all morphisms into `instruction_fn`

The `instruction_fn` is the composed function that the orchestrator executes with horizontal inputs.

### The `composition_tool.compose` Plan

The final step's `plan` parameter defines:
- **`output_key`**: Name for this intermediate result
- **`function`**: Which morphism to apply (references a `result_key` from earlier steps)
- **`params`**: Runtime values (from `__initial_input__` or previous outputs)
- **`literal_params`**: Static values
- **`condition`** (optional): Conditional execution
- **`return_key`**: Which output to return as the final result

---

## Paradigm Naming Convention

```
[v_Norm]-[h_Norm(s)]-[c_CompositionSteps]-[o_OutputFormat].json
```

| Prefix | Pattern | Examples |
|--------|---------|----------|
| `v_` | Perception norm or Literal variant | `v_PromptLocation`, `v_LiteralTemplate` |
| `h_` | Perception norm or Literal variant | `h_Literal`, `h_LiteralPath`, `h_LiteralUserPrompt` |
| `c_` | Action description | `c_GenerateThinkJson`, `c_CachedPyExec`, `c_MultiFilePicker` |
| `o_` | `[Collection]Type` | `o_Literal`, `o_FileLocation`, `o_ListFileLocation` |

### Input Norm Naming Patterns

| Input Type | Naming Pattern | Examples |
|------------|----------------|----------|
| **Perception norm** | `[Norm]` | `FileLocation`, `PromptLocation`, `ScriptLocation` |
| **Literal (generic)** | `Literal` | `h_Literal` |
| **Literal (specialized)** | `Literal[Descriptor]` | `LiteralTemplate`, `LiteralPath`, `LiteralUserPrompt`, `LiteralInputs` |

### Key Rules

- **Input norms match PerceptionRouter vocabulary**: `FileLocation`, `PromptLocation`, `ScriptLocation`, `SavePath`
- **Literal variants use `Literal[Descriptor]`**: `LiteralTemplate`, `LiteralPath`, `LiteralUserPrompt`, `LiteralInputs`
- **Output collections put collection first**: `o_ListFileLocation` (not `o_FileLocationList`)

---

## Paradigm Design Philosophy

**Paradigms should bridge data types and tools, not encode specific use cases.**

### ✅ Good Paradigm Design

```
v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
```
- Takes a prompt (vertical) and data (horizontal)
- Generates with LLM and extracts JSON
- **Reusable for**: Sentiment analysis, classification, extraction, summarization, etc.

```
h_LiteralUserPrompt-c_MultiFilePicker-o_ListFileLocation
```
- Takes a user prompt (horizontal)
- Opens a file picker dialog
- **Reusable for**: Any file selection task

### ❌ Avoid: Over-Specific Paradigms

```
v_SentimentPrompt-h_Reviews-c_AnalyzeSentiment-o_SentimentScore
```
- Encodes a specific use case (sentiment analysis)
- Can't be reused for other tasks
- Creates paradigm proliferation

---

## Retrieving Vertical Inputs in Paradigms

Vertical inputs (prompts, scripts, configurations) arrive at the paradigm wrapped in perceptual signs. The paradigm's `sequence_spec` must **extract the raw path** before using it.

### The `states.vertical` Structure

During MFP (Model Function Perception), the orchestrator populates `states.vertical` with the vertical input value. This value is a **perceptual sign** (e.g., `%{prompt_location}abc(provisions/prompts/task.md)`).

### Extracting Paths with `perception_router.strip_sign`

To get the raw path from a perceptual sign, use the `perception_router.strip_sign` function:

```json
{
  "output_key": "prompt_path",
  "function": {"__type__": "MetaValue", "key": "perception_router.strip_sign"},
  "params": {"__positional__": {"__type__": "MetaValue", "key": "states.vertical"}}
}
```

**Result**: `"provisions/prompts/task.md"` (the raw path, stripped of the sign wrapper)

### ❌ Common Mistake: Accessing Non-Existent Keys

```json
{
  "output_key": "prompt_path",
  "function": {"__type__": "MetaValue", "key": "states.function.paradigm_config.vertical.prompt_path"},
  "params": {}
}
```

**Error**: `KeyError: 'paradigm_config'`

This pattern assumes a nested structure that doesn't exist. Always use `perception_router.strip_sign` on `states.vertical`.

### Script Paradigms: Extracting Multiple Fields

For script paradigms where the vertical input contains multiple fields (script path and function name), extract each field separately:

```json
[
  {
    "output_key": "script_path",
    "function": {"__type__": "MetaValue", "key": "perception_router.strip_sign"},
    "params": {"__positional__": {"__type__": "MetaValue", "key": "states.vertical.script_path"}}
  },
  {
    "output_key": "function_name",
    "function": {"__type__": "MetaValue", "key": "perception_router.strip_sign"},
    "params": {"__positional__": {"__type__": "MetaValue", "key": "states.vertical.function_name"}}
  }
]
```

### The Pattern Summary

| Vertical Input Type | Access Pattern | Extract With |
|---------------------|----------------|--------------|
| **Prompt** (`v_PromptLocation`) | `states.vertical` | `perception_router.strip_sign(states.vertical)` |
| **Script** (`v_ScriptLocation`) | `states.vertical.script_path`, `states.vertical.function_name` | `perception_router.strip_sign(...)` on each |
| **Template** (`v_LiteralTemplate`) | `states.vertical` | Direct access (already literal) |

---

## Critical: Read Prompts During MFP, Not in Composition

**The composed function (TVA) cannot access step results from MFP.** Resources must be fully loaded during MFP steps, not inside the composition plan.

### ❌ Wrong Pattern: Reading in Composition

```json
{
  "step_index": 1,
  "affordance": "perception_router.strip_sign",
  "result_key": "raw_prompt_path"
},
{
  "step_index": 2,
  "affordance": "file_system.read",
  "result_key": "read_fn"
},
{
  "step_index": 3,
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

**Error**: `Key 'path/to/prompt.md' not found in context` — The `raw_prompt_path` value from step 1 isn't available in the composition's execution context.

### ✅ Correct Pattern: Reading During MFP

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

## Critical: Script Paradigms Must Also Read During MFP

Script paradigms follow the same pattern — read the script file and create a bound executor function during MFP:

### ✅ Correct Pattern for Script Execution

```json
{
  "step_index": 1,
  "affordance": "perception_router.strip_sign",
  "params": {
    "token": {"__type__": "MetaValue", "key": "states.vertical"}
  },
  "result_key": "raw_script_path"
},
{
  "step_index": 2,
  "affordance": "file_system.read_now",
  "params": {
    "path": {"__type__": "MetaValue", "key": "raw_script_path"}
  },
  "result_key": "script_read_result"
},
{
  "step_index": 3,
  "affordance": "formatter_tool.extract_content",
  "params": {
    "data": {"__type__": "MetaValue", "key": "script_read_result"}
  },
  "result_key": "script_content"
},
{
  "step_index": 4,
  "affordance": "python_interpreter.create_function_executor",
  "params": {
    "script": {"__type__": "MetaValue", "key": "script_content"},
    "function_name": "main"
  },
  "result_key": "execute_fn"
},
{
  "step_index": 5,
  "affordance": "composition_tool.compose",
  "params": {
    "plan": [
      {
        "output_key": "execution_result",
        "function": {"__type__": "MetaValue", "key": "execute_fn"},
        "params": {"__positional__": "__initial_input__"}
      }
    ]
  }
}
```

**Key steps**:
1. **Strip sign** → get raw file path
2. **Read file immediately** → get `{"status": "success", "content": "..."}` dict
3. **Extract content** → get just the script code string
4. **Create bound executor** → `python_interpreter.create_function_executor` binds script content into a callable
5. **Composition uses bound executor** → only needs to pass input params

**Note**: The `extract_content` affordance uses this call_code pattern:
```json
"call_code": "result = params['data']['content']"
```

This extracts the `content` field from the file read result during MFP, since MetaValue keys don't support nested access like `script_read_result.content`.

---

## Paradigms in Resource Types

**Demand** (Post-Formalization):
```ncd
|%{norm_input}: h_LiteralPath-c_ReadFile-o_Literal
```

**Supply** (Activation): Load paradigm JSON, validate structure, include in `working_interpretation`.

---

## Paradigms in Directory Structure

```
provisions/
├── path_mapping.json          # Resource resolution mappings
├── paradigms/
│   ├── llm/
│   │   ├── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json
│   │   └── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Boolean.json
│   ├── file_system/
│   │   ├── h_LiteralPath-c_ReadFile-o_Literal.json
│   │   └── h_LiteralPath-c_ReadJsonFile-o_Struct.json
│   └── python_interpreter/
│       └── h_Literal-c_CheckPhaseComplete-o_Boolean.json
```

### Naming Convention

**Paradigms**: `[v_Norm]-[h_Norm(s)]-[c_Steps]-[o_Format].json`

---

## Paradigms in Path Mapping

**`path_mapping.json`** provides indirection between demand paths and actual file locations:

```json
{
  "paradigms": {
    "v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal": "paradigms/llm/v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json"
  }
}
```

---

## Paradigm Validation

| Resource Type | Validation | Error on Failure |
|---------------|------------|------------------|
| **Paradigm** | File exists, valid JSON, required fields present | `ParadigmNotFoundError` |

### Runtime Errors Related to Paradigms

| Error | Cause | Resolution |
|-------|-------|------------|
| `KeyError: 'paradigm_config'` | Paradigm tries to access `states.function.paradigm_config.vertical.*` | Use `perception_router.strip_sign` on `states.vertical` instead |
| `Key 'path/to/file' not found in context` | Composition plan references a step result that isn't available during TVA | Read resources during MFP steps, not inside composition |
| `AttributeError: 'NoneType' has no attribute 'main'` | Paradigm calls `main` but script doesn't define it | Add a `main` function alias to the script |

---

## Common Patterns Using Paradigms

### Pattern 1: LLM Operation with Prompt (h_Literal)

```ncd
<= ::(classify operation type) | ?{sequence}: imperative
    |%{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    |%{v_input_norm}: prompt_location
    |%{v_input_provision}: provisions/prompts/phase_3/classify_operation.md
    |%{h_input_norm}: Literal
<- {operation context} | ?{flow_index}: 1.2
    |%{file_location}: (from previous inference output)
```

**Key**: Value concept has perceptual sign → MVP perceives → h_input_norm is `Literal`.

### Pattern 2: File Read Operation (h_LiteralPath)

```ncd
<= ::(read progress from file if exists) | ?{sequence}: imperative
    |%{norm_input}: h_LiteralPath-c_ReadFileIfExists-o_Literal
    |%{h_input_norm}: literal_path
<- {progress file path} | ?{flow_index}: 1.2
    |%{literal<$% file_path>}: provisions/data/progress.json
```

**Key**: Value concept is literal → MVP passes through → paradigm reads file internally.

### Pattern 3: Python Script Execution

```ncd
<= ::(check if phase 1 already complete in progress) | ?{sequence}: imperative
    |%{norm_input}: h_Literal-c_CheckPhaseComplete-o_Boolean
    |%{h_input_norm}: Literal
<- {current progress} | ?{flow_index}: 1.2
    |%{file_location}: (from previous inference output)
```

**Key**: Value concept has perceptual sign → MVP perceives → h_input_norm is `Literal`.

---

## Best Practices

### Version Your Paradigms

When creating new paradigm variations:
```
paradigms/llm/
├── h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Literal.json      # Standard
├── h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Literal-v2.json   # New version
```

---

## Key Takeaways

1. **The paradigm is a continuation of MVP** — it receives what MVP produces
2. **The h_input_norm must be consistent** — if MVP perceives, use `Literal`; if not, describe the literal type
3. **Activation supplies resources** — validates, resolves, embeds
4. **Vertical inputs must be stripped** — use `perception_router.strip_sign` on `states.vertical` to extract raw paths in paradigms
5. **Scripts should provide a `main` alias** — paradigms call `main`, delegate to descriptive function names
