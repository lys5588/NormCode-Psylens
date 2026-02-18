# Main Page Redesign — Questions We Must Answer

## The Core Premise

NormCode is a language that **faithfully describes AI agent workflows with complexity** —
with readability, navigability, and structure built into the syntax itself.

The plan you write IS the artifact. You own it. You can read it, share it, modify it, run it anywhere.

---

## Questions the Homepage Must Answer (in order)

### 1. WHAT is the problem we're solving?

AI agents do complex, multi-step work — but today there's no faithful way to describe
what they do. The workflow lives in scattered scripts, prompt templates, and platform-specific
configs. You can't read it. You can't easily modify it. You don't truly own it.

- What happens when you want to change step 5 of a 20-step agent?
- What happens when you want to hand your workflow to someone else?
- What happens when the platform you built it on disappears?

### 2. WHY does this need a language (not a tool, not a platform, not just an agent model)?

**Because only a language can be LEARNT by human beings.**

This is the fundamental point. A tool can be used. A platform can be subscribed to.
But a **language** can be **learnt** — and once learnt, it becomes yours forever.
It becomes how you THINK about the problem.

**Without a language, humans have no real control over AI agents:**

- If you use a **raw agent model** (Claude, OpenAI, etc.) — the model is a black box.
  You give it a prompt and hope. You can't specify step-by-step behavior.
  You can't verify what it did. You can't modify step 5 without rewriting everything.

- If you use an **agent framework** (LlamaIndex, LangChain, CrewAI, etc.) — you get
  more structure, but the "workflow" is Python code. Only the developer can read it.
  Only the developer can modify it. The knowledge lives in code, not in a readable plan.

- If you use a **no-code platform** (Defi, Coze) — you're locked into their UI, their abstractions,
  their pricing. The workflow lives on their servers, not in your hands.

**With a language, everything changes:**

- **Learnability** — a person can learn NormCode and then describe ANY AI agent workflow.
  Just like learning SQL lets you query ANY database.
- **Specificity** — a language lets you express EXACTLY what you mean, with precision.
  Tools can only express what the tool designer anticipated. A language can express
  anything within its grammar.
- **Readability** — the plan reads like a description of what the agent does.
  Non-developers can read it. Managers can approve it. Auditors can verify it.
- **Navigability** — indentation shows data flow. You can trace any path, understand
  any step's inputs and outputs at a glance.
- **Portability** — it's a text file. You own it. Version-control it. Share it.
  Take it to any compatible orchestrator. No vendor lock-in.
- **Individual empowerment** — this is the key. Without a language, controlling AI agents
  requires being a developer or trusting a platform. WITH a language, any individual
  who learns it can initiate, audit, modify, and own their AI workflows.

**The analogy:**
- SQL is THE language for data (regardless of database vendor)
- HTML is THE language for documents (regardless of browser)
- NormCode aims to be THE language for AI agent workflows (regardless of orchestrator or LLM)

**NormCode vs. agent frameworks (LlamaIndex, LangChain, etc.):**
These frameworks are powerful but they operate at the CODE level. NormCode operates at
the DESCRIPTION level — it's more readable, more manageable, and accessible to people
who aren't Python developers. The frameworks and NormCode aren't necessarily competitors;
NormCode could compile DOWN to framework calls. The language sits above the implementation.

### 3. WHAT is NormCode exactly?

A structured, human-readable language where:
- Each line is a step (a task or a data input)
- Indentation defines what data each step can see
- Plain language describes what each step does
- The compiler handles execution order, validation, and resource resolution

#### Key Language Properties (from the docs — these are what make it a REAL language)

**A. Minimal, learnable syntax — just 3 core markers:**
- `<-`  Value Concept — "this is data" (nouns)
- `<=`  Functional Concept — "this is an action" (verbs)
- `<*`  Context Concept — loop/timing state
- Everything else is natural language. That's the entire core.

**B. No presumed global context — isolation by design (the killer feature):**
- There is NO shared/global context. Each inference is isolated.
- What's indented under a step = what that step can see. NOTHING ELSE.
- This is fundamentally different from LLM chains / agent frameworks where context
  accumulates and bleeds between steps (causing hallucination, unpredictability).
- In NormCode, isolation is enforced by the STRUCTURE of the language (indentation),
  not by developer discipline or framework conventions.
- You can visually trace any data path just by reading the indentation.
- **The key purpose: each step is individually debuggable and optimizable.**
  Because each inference has a known, bounded set of inputs, you can:
  - Debug one step in isolation — reproduce it with just its inputs, no global state
  - Optimize one step without breaking others — change its prompt, swap its LLM, 
    tune its logic — nothing else is affected because nothing else sees its internals
  - Identify exactly where things went wrong — check what went in, check what came out
  - No "where did this hallucination come from?" — the inputs are right there in the indentation

**C. Two types of steps — Semantic vs. Syntactic:**
- **Semantic** (imperative, judgement) — reasoning steps, MAY use LLM, cost tokens
- **Syntactic** (assigning, grouping, timing, looping) — data manipulation, NO LLM, always FREE
- A 20-step plan might only call the LLM 8 times. Data routing is always free.
- This matters for cost efficiency AND for understanding what's "thinking" vs. "plumbing."

**D. Rich operators for complex workflows:**
- Assigning: `$.` (specify), `$+` (accumulate), `$-` (select), `$=` (merge)
- Grouping: `&[{}]` (collect with labels), `&[#]` (flatten to list)
- Timing: `@:'` (conditional), `@:!` (negated), `@.` (wait for completion)
- Looping: `*.` (iterate over collection)
- These are ALL free (no LLM). They give the language real expressive power.

**E. Progressive compilation (4 phases):**
- Phase 1: Derivation — determines execution order from your description
- Phase 2: Formalization — adds flow indices, sequence types, grammar check
- Phase 3: Post-formalization — contextualizes, adds resource demands
- Phase 4: Activation — resolves actual resources, produces executable JSON
- Each phase is inspectable. You can review what the compiler did at every stage.

**F. Execution properties:**
- Inside-out, top-to-bottom execution order
- Automatic parallel execution when steps don't depend on each other
- Orchestrator runs in cycles: CHECK → EXECUTE → UPDATE → REPEAT
- SQLite checkpointing — pause, resume, fork from ANY point
- Smart patching — re-run only what changed, keep cached results
- Flow index system — every node has a unique address (e.g. 1.2.3) for debugging

**G. Visual debugging (Canvas App):**
- See the entire inference graph before execution
- Set breakpoints on any flow index
- Watch execution progress in real-time
- Inspect data at any node

#### The Demo — Proof It's Real

**Show, don't just tell.** The demo (PPT Client) IS the concrete answer to this question.
It's a real AI agent — orchestrated by a NormCode plan — that:
1. Takes inputs (topic, audience, length, reference files)
2. Executes a multi-step workflow (analysis → outline → slide generation → final output)
3. Shows progress step by step (event log, intermediate files)
4. Produces an artifact (the finished presentation)

The user can see: this NormCode plan IS what the agent does. It's not hidden in Python.
It's not locked in a platform. It's a readable plan that drives a real workflow.

The homepage should connect the abstract syntax example to THIS concrete reality:
"Here's a 7-line NormCode plan → here's what it looks like running → here's the output."

### 4. WHAT can you DO with it?

The full lifecycle of a NormCode workflow — what makes it different from "write code and run":

**A. Describe** — Write the workflow (or have AI generate it)
- You or an LLM writes a .ncds file describing the agent's steps in plain language.
- Example: "I want an agent that takes a research topic, finds papers, extracts key findings,
  cross-references them, and produces a literature review."
- The AI (or you) produces a NormCode plan. It's a text file. You can read every line.

**B. Review** — Read it, understand it, approve it BEFORE it runs
- Unlike a Python script or a no-code flow, anyone can read the plan and understand
  what it will do. A manager can approve it. A domain expert can verify the logic.
- Because there's no global context, you can check each step independently:
  "Does step 3 have the right inputs? Does step 5 make sense given what step 4 produces?"

**C. Run** — Compile and execute through the orchestrator
- The compiler transforms your plan through 4 phases into executable JSON.
- The orchestrator runs each step, checkpointing as it goes.
- You can watch it live in Canvas, or run it headless via the API (like the PPT demo).

**D. Inspect** — Debug, understand what happened, trace any issue
- Every step's inputs and outputs are recorded. Every checkpoint is saved to SQLite.
- If step 8 produces bad output, check its inputs — they're right there.
- No guessing. No "maybe the context was polluted." Just facts.

**E. Modify** — Change one step, fork the whole plan, adapt it to your needs
- Change a prompt in step 5? Just edit that line. Nothing else is affected.
- Want to try a different approach at step 3? Fork from the checkpoint.
  Steps 1-2 don't need to re-run — their results are cached.
- Add steps, remove steps, reorganize — the compiler re-validates.

**F. Own & Share** — The artifact is yours
- The .ncds/.ncd file is a portable text document. It's not locked in any platform.
- Version-control it in Git. Share it with colleagues. Publish it as a template.
- In a mature ecosystem: a marketplace of NormCode plans. Download a "customer support
  triage agent," adapt it to your company, run it on your own infrastructure.
- **You own what your agents do.** No vendor can take that away.

The full lifecycle: **Describe → Review → Run → Inspect → Modify → Own → Share**

### 5. WHO is this for?

**Today (early adopters):**
- **AI engineers** tired of debugging opaque LangChain/LlamaIndex pipelines — who want
  a cleaner way to define what their agents do, with real debuggability
- **Research teams** building multi-step AI workflows who need reproducibility and
  the ability to inspect/modify individual steps
- **Technical founders** building AI products who want the agent logic to be a portable,
  versionable artifact — not locked into a specific framework or platform

**Tomorrow (broader adoption):**
- **Product managers / domain experts** who want to read and approve what an AI agent
  does before it runs — without needing to read Python code
- **Teams & organizations** who need a shared, readable format to collaborate on
  agent behavior — like how teams share SQL queries or API specs
- **End users** who want to understand, customize, and OWN their AI workflows —
  not just click buttons in someone else's SaaS
- **Regulated industries** (finance, legal, healthcare) who must prove what each step
  saw, what it decided, and why — with full auditability at the language level

**The aspiration:**
Anyone who wants to control what an AI agent does — not just use one, but understand it,
modify it, and own it — should be able to learn NormCode and do exactly that.

### 6. WHY should I believe this? (Credibility)

This isn't vaporware. It's working software with academic foundations:

- **Published research** — peer-reviewed paper on arXiv (2512.10563) describing the
  formal theory: concept types, inference structure, compilation pipeline, execution model
- **Working compiler** — the 4-phase compilation pipeline is implemented and running
- **Working visual editor** — Canvas App for designing, debugging, and executing plans
  (downloadable now, Windows alpha)
- **Working demo** — the PPT Client is a real AI agent orchestrated by a NormCode plan,
  running on a live server, producing real output
- **Open source** — GitHub repository, MIT license, transparent development
- **Team** — researchers and engineers from Oxford, UCL, Shenzhen University
- **Already handling real complexity** — the PPT generation demo uses loops, conditionals,
  multi-step reasoning, and produces multi-file output. This isn't a toy.

### 7. HOW do I start?

**Path 1: See it first**
- Try the interactive demo (PPT Client) — watch a real NormCode agent run
- Watch the Canvas demo video — see the visual editor in action

**Path 2: Learn the language**
- Read the syntax reference — 3 core markers, that's the starting point
- Read the examples — see real NormCode plans for common patterns
- Read the compilation pipeline — understand how plans become executable

**Path 3: Build something**
- Download Canvas (Windows alpha) — visual editor for designing and debugging plans
- Download an example project — open it in Canvas, run it, modify it
- Write your own .ncds file — describe a workflow, compile it, run it

---

## The One-Sentence Vision

> **What if every AI agent workflow was a readable, ownable, portable document —
> that anyone could understand, modify, and run?**

## Key Messaging Angles (pick one as the lead)

**A.** "A language for AI agent workflows" — category-defining, like "SQL for agents"
**B.** "Describe it. Own it. Run it." — emphasizes the artifact and user ownership
**C.** "AI workflows you can read, modify, and own" — emphasizes user power
**D.** "The faithful description of what your AI agent does" — emphasizes accuracy/trust

## What Makes This Different from Current Framing

The current page says: "A simple language for complex AI agents" — this is ABOUT the language.
The new framing should be ABOUT the user: what YOU can do, what YOU own, what YOU control.

The language is the means. The user's power over their AI workflows is the end.

