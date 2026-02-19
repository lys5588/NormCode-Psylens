# Compilation Section

**The 4-phase pipeline that transforms natural language ideas into executable NormCode plans.**

---

## 🎯 Purpose

This section documents how NormCode plans are compiled—from initial natural language intent through progressive formalization stages to final executable JSON repositories that the Orchestrator can run.

**Key Questions Answered:**
- How does natural language become structured `.ncd` syntax?
- What happens during formalization?
- How are norms and resources assigned?
- How do `.ncd` / `.pf.ncd` files become executable repositories?

---

## 📚 Documents in This Section

### 1. [Overview](overview.md)
**High-level view of the compilation pipeline**

Learn about:
- The 4 compilation phases
- Progressive formalization philosophy
- Combined workflow (Phases 2-3)
- Critical lessons from debugging

**Start here if**: You want to understand the big picture of compilation.

**Time**: 15 minutes

---

### 2. [Derivation](derivation.md)
**Phase 1: Natural Language → Structure**

Learn about:
- Transforming unstructured intent into hierarchical inferences
- Identifying concepts and operations
- Creating `.ncds` (draft straightforward) format
- Extraction of value and functional concepts

**Start here if**: You want to understand how natural language becomes structure.

**Time**: 20 minutes

---

### 3. [Formalization](formalization.md)
**Phase 2: Adding Flow and Sequence Types**

Learn about:
- Assigning unique flow indices (`1.2.3`)
- **⚠️ Critical: The sibling pattern for flow indices**
- Determining sequence types (`imperative`, `grouping`, `timing`, etc.)
- **⚠️ Critical: Explicit input references for operators**
- Transforming `.ncds` to formal `.ncd`

**Start here if**: You want to understand how structure becomes rigorous syntax.

**Time**: 25 minutes

---

### 4. [Post-Formalization](post_formalization.md)
**Phase 3: Enriching with Context and Configuration**

Learn about:
- **Re-composition**: Mapping to normative context (paradigms, body faculties, perception norms)
- **Provision**: Linking to concrete resources (file paths, prompts, value selectors)
- **Syntax Re-confirmation**: Ensuring tensor coherence (axes, shape, element type)
- **⚠️ Critical: LLM output format, loop state, placeholders**

**Start here if**: You want to understand how syntax becomes executable.

**Time**: 30 minutes

---

### 5. [Activation](activation.md)
**Phase 4: Generating Executable Repositories**

Learn about:
- Transforming enriched `.pf.ncd` to JSON repositories
- Parser (`_.parse_to_nci.py`) and Activator (`_.activate_nci.py`)
- `concept_repo.json` structure and extraction
- `inference_repo.json` structure and working_interpretation

**Start here if**: You want to understand the final compilation output.

**Time**: 35 minutes

---

### 6. [Examples](examples/)
**Working Examples with Parser and Activator**

Contains:
- Example `.pf.ncd` files
- Parser and activator scripts
- Generated repositories

**Start here if**: You want to see complete working examples.

---

## 🗺️ Reading Paths

### For New Users
1. [Overview](overview.md) - Understand the pipeline
2. [Derivation](derivation.md) - See how structure emerges
3. [Formalization](formalization.md) - Understand rigor
4. [Examples](examples/) - See working examples

### For Plan Writers
1. [Overview](overview.md) - Pipeline overview
2. [Formalization](formalization.md) - **⚠️ Critical patterns**
3. [Post-Formalization](post_formalization.md) - Understand annotations
4. [Examples](examples/) - Reference implementations

### For Compiler Developers
1. [Overview](overview.md) - Architecture
2. [Derivation](derivation.md) - Phase 1 logic
3. [Formalization](formalization.md) - Phase 2 logic
4. [Post-Formalization](post_formalization.md) - Phase 3 logic
5. [Activation](activation.md) - Phase 4 logic

### For Debugging
1. [Formalization](formalization.md) - **⚠️ Flow indices, sibling pattern**
2. [Post-Formalization](post_formalization.md) - **⚠️ Annotations, LLM format**
3. [Activation](activation.md) - Check working_interpretation

---

## 🔑 Key Concepts

### The Compilation Pipeline

```
Natural Language
      ↓
Phase 1: Derivation
      ↓
   _.ncds (draft straightforward)
      ↓
Phase 2: Formalization (often combined with Phase 3)
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

### Progressive Formalization

NormCode compilation follows a **progressive formalization** philosophy:

1. **Start loose** - Natural language intent
2. **Add structure** - Hierarchical concepts and operations
3. **Add rigor** - Flow indices, sequence types, bindings
4. **Add context** - Norms, resources, configurations
5. **Make executable** - JSON repositories

**Note**: Phases 2-3 are often combined, producing `_.pf.ncd` directly from `_.ncds`.

---

## 💡 The Big Picture

### What Each Phase Does

| Phase | Question Answered | Input | Output |
|-------|-------------------|-------|--------|
| **Derivation** | *What* are we trying to do? | Natural language | `_.ncds` structure |
| **Formalization** | *In what order* and *which sequence*? | `_.ncds` | `_.ncd` (formal) |
| **Post-Formalization** | *How* and *with what resources*? | `_.ncd` (formal) | `_.pf.ncd` (enriched) |
| **Activation** | *What does the Orchestrator need*? | `_.pf.ncd` (enriched) | JSON repositories |

### The Format Ecosystem

| Format | Purpose | Created By |
|--------|---------|------------|
| **`_.ncds`** | Draft (easiest to write) | You or LLM |
| **`_.ncd`** | Formal syntax (intermediate) | Compiler |
| **`_.pf.ncd`** | Post-formalized with annotations | Compiler |
| **`_.pf.nci.json`** | Parsed inference structure | Parser |
| **`concept_repo.json`** | Concept repository | Activator |
| **`inference_repo.json`** | Inference repository | Activator |

---

## 📖 Common Questions

**Q: Do I need to understand the entire pipeline?**  
A: No. If you're just writing plans, read Overview and the critical sections in Formalization/Post-Formalization.

**Q: What's the difference between formalization and post-formalization?**  
A: Formalization adds syntactic rigor (flow, sequences). Post-formalization adds execution context (norms, resources). They are often combined.

**Q: Can I write `.pf.ncd` by hand?**  
A: Yes, this is common. LLMs often generate `_.pf.ncd` directly from requirements.

**Q: What are the most common bugs?**  
A: 1) Wrong flow index structure (not using sibling pattern), 2) Missing explicit input references, 3) Wrong LLM output format.

**Q: What is working_interpretation?**  
A: A dict in `inference_repo.json` that each sequence's IWI step reads to understand how to execute.

**Q: Where do paradigm names come from?**  
A: From the paradigm registry in `infra/_agent/_models/_paradigms/`. See [Post-Formalization](post_formalization.md).

**Q: How do I activate a `.pf.ncd` file?**  
A: Run `python _.parse_to_nci.py` then `python _.activate_nci.py`. See [Activation](activation.md).

---

## 🎓 Understanding Levels

### Level 1: Basic Understanding
**Goal**: Understand what compilation does

**Learn**:
- [Overview](overview.md) - Pipeline overview
- [Examples](examples/) - See working examples

**You can**: Read and understand NormCode plans.

---

### Level 2: Plan Writing
**Goal**: Write correct plans and avoid common bugs

**Learn**:
- [Derivation](derivation.md) - Structure extraction
- [Formalization](formalization.md) - **⚠️ Critical: sibling pattern, explicit inputs**
- [Post-Formalization](post_formalization.md) - **⚠️ Critical: annotations, LLM format**

**You can**: Write plans that compile and execute correctly.

---

### Level 3: Compiler Development
**Goal**: Extend or modify the compiler

**Learn**:
- All documents in detail
- [Activation](activation.md) - Repository generation
- Parser/activator scripts in examples

**You can**: Extend compiler, add new sequences, modify activation logic.

---

## 🚀 Quick Start Examples

### Example 1: Write and Compile a Simple Plan

**Step 1: Write draft (_.ncds)**
```ncds
<- result
    <= calculate the sum
    <- number A
    <- number B
```

**Step 2: Write post-formalized (_.pf.ncd)**
```ncd
:<:{result} | ?{flow_index}: 1
    | %{ref_axes}: [_none_axis]
    | %{ref_element}: int
    <= ::(calculate the sum) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        | %{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
        | %{v_input_provision}: provisions/prompts/sum.md
    <- {number A} | ?{flow_index}: 1.2
        | %{ref_axes}: [_none_axis]
        | %{ref_element}: int
        | %{literal<$% int>}: 5
    <- {number B} | ?{flow_index}: 1.3
        | %{ref_axes}: [_none_axis]
        | %{ref_element}: int
        | %{literal<$% int>}: 3
```

**Step 3: Parse and activate**
```bash
python _.parse_to_nci.py
python _.activate_nci.py
```

**Result**: `repos/concept_repo.json` and `repos/inference_repo.json`

---

### Example 2: Critical Pattern - Sibling Flow Indices

```ncd
# CORRECT - inputs are siblings of functional
:<:{output} | ?{flow_index}: 1
    <= ::(process) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {input1} | ?{flow_index}: 1.2      # sibling of 1.1
    <- {input2} | ?{flow_index}: 1.3      # sibling of 1.1

# WRONG - inputs nested under functional
:<:{output} | ?{flow_index}: 1
    <= ::(process) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        <- {input1} | ?{flow_index}: 1.1.1    # WRONG!
        <- {input2} | ?{flow_index}: 1.1.2    # WRONG!
```

---

### Example 3: Critical Pattern - Explicit Input References

```ncd
# WRONG - missing input reference for $.
<- {result} | ?{flow_index}: 1.2
    <= $. %>(<source value>) | ?{flow_index}: 1.2.1 | ?{sequence}: assigning
    # Missing: <- <source value> | ?{flow_index}: 1.2.2

# CORRECT - explicit input reference
<- {result} | ?{flow_index}: 1.2
    <= $. %>(<source value>) | ?{flow_index}: 1.2.1 | ?{sequence}: assigning
    <- <source value> | ?{flow_index}: 1.2.2
        | %{ref_axes}: [_none_axis]
        | %{ref_element}: str
```

---

## 🔗 External Resources

### Previous Sections
- **[Introduction](../1_intro/README.md)** - What is NormCode?
- **[Grammar](../2_grammar/README.md)** - The `.ncd` syntax
- **[Execution](../3_execution/README.md)** - How plans run

### Source Code
- `infra/_agent/_models/_paradigms/` - Paradigm registry
- `infra/_agent/_models/_perception_router.py` - Perception norms
- Example parser/activator scripts in `examples/`

---

## 📊 Document Status

| Document | Status | Content Coverage |
|----------|--------|------------------|
| **Overview** | ✅ Complete | Pipeline, philosophy, critical lessons |
| **Derivation** | ✅ Complete | Natural language → structure |
| **Formalization** | ✅ Complete | Flow indices, sibling pattern, explicit inputs |
| **Post-Formalization** | ✅ Complete | Annotations, LLM format, loop state |
| **Activation** | ✅ Complete | JSON repositories, working_interpretation |
| **Examples** | ✅ Complete | Working parser/activator implementations |

---

## 🎯 Next Sections

After mastering compilation:

- Return to **[Execution](../3_execution/README.md)** - See how compiled plans run

---

## 💡 Key Takeaways

### The Compilation Promise

**NormCode's compilation transforms intent into executable structure while maintaining auditability**:

1. **Progressive formalization**: Each phase adds specificity without losing meaning
2. **Combined workflow**: Phases 2-3 often combined for efficiency
3. **Explicit configuration**: All norms and resources are declared
4. **Auditable output**: Every decision is traceable in the JSON repositories

### ⚠️ Critical Rules to Remember

| Rule | Why It Matters |
|------|----------------|
| **Sibling pattern for flow indices** | Prevents dependency resolution failures |
| **Explicit input references** | Creates required edges in inference graph |
| **LLM output format `{"thinking": "...", "result": ...}`** | Prevents `None` output from paradigms |
| **`%{selector_packed}: true` for bundled data** | Prevents unwanted unpacking |
| **`%{is_invariant}: true` for loop state** | Prevents state reset between iterations |
| **Placeholder for empty lists** | Prevents `(0,)` shape issues |

### Design Philosophy

```
Flexibility → Structure → Rigor → Configuration → Execution

Each phase answers a specific question about WHAT, HOW, WHEN, and WITH WHAT.
```

---

**Ready to dive in?** Start with [Overview](overview.md) to understand the pipeline, then explore each phase in detail.
