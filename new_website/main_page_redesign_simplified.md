# Main Page — Section-by-Section Sketch

The page tells one story: **You need control over your AI agents. That requires a language. This is it.**

Visitor should get the idea in 10 seconds (hero), get interested in 30 seconds (problem + syntax),
get convinced in 2 minutes (full page scroll).

---

## SECTION 1: HERO

**Badge:** `Open Source · Research-Backed`

**Headline:**
> The language for AI agent workflows

**Subtitle:**
> NormCode lets you describe what your AI agents do — step by step, in readable,
> structured syntax. Review it before it runs. Debug any step. Own the plan.

**CTAs:** [Download Canvas]  [GitHub]  [Paper]

**Design notes:**
- Clean, confident, no clutter
- Headline is category-defining — says WHAT this is
- Subtitle answers "so what?" in one breath — review, debug, own
- No buzzwords. No "revolutionary." Just clarity.

---

## SECTION 2: THE GAP (Problem)

**Headline:**
> Today, nobody can read what your AI agent actually does

**Three columns — the current options and their limits:**

| Raw AI Models | Agent Frameworks | No-Code Platforms |
|---|---|---|
| Claude, GPT, etc. | LangChain, LlamaIndex, CrewAI | Dify, Coze, etc. |
| Black box. Prompt in, output out. Can't specify step-by-step. Can't debug step 5. | Python code. Only the dev can read it. Only the dev can change it. | Locked UI. Their abstractions. Their servers. Their pricing. |
| **You hope it works.** | **You hire someone to maintain it.** | **You rent control.** |

**Punchline (below the columns):**
> What if you could just *describe* what your agent does — in a way anyone can read,
> any machine can run, and you fully own?

**Design notes:**
- This is the "aha" setup. Three pain points the visitor recognizes.
- Keep it short — each column is ~3 lines max.
- The punchline pivots to the solution.

---

## SECTION 3: THE LANGUAGE (Show it)

**Headline:**
> Three symbols. Plain language. That's the whole syntax.

**Left side — syntax intro:**
| Symbol | Meaning | Think of it as |
|---|---|---|
| `<-` | This is data | nouns |
| `<=` | This is an action | verbs |
| `<*` | Loop/timing state | iteration context |

Everything else you write is natural language.

**Right side — a real example:**
```
<- executive summary
    <= generate summary from flagged items
    <- discrepancy flags
        <= check for mismatches
        <- extracted figures
            <= extract financial data
            <- raw document
        <- database results
```

**Below the example — the "aha" explanation:**
> That's a complete AI agent. 7 lines. Read it bottom-up:
> extract data from the document → check for mismatches → summarize the flags.
>
> **Indentation = what each step can see.** The extraction step sees only the raw document.
> The mismatch check sees extracted figures + database results — nothing else.
> No global context. No data leaking between steps.

**Design notes:**
- This is the MOST important section. If the visitor gets this, they get NormCode.
- The code block should feel clean and inviting, not intimidating.
- The "aha" explanation should make the indentation rule click instantly.

---

## SECTION 4: WHY A LANGUAGE (Not another framework)

**Headline:**
> Only a language can be learnt

**Subtitle:**
> Tools are used. Platforms are subscribed to. A language becomes how you think.

**Three cards:**

**Card 1: Learn it once, describe any workflow**
Like SQL for databases — learn NormCode and you can describe any AI agent workflow.
Not tied to any specific framework, model, or platform.

**Card 2: Every step is debuggable on its own**
No global context means each step has a known, bounded set of inputs.
Debug one step in isolation. Optimize one step without breaking others.
When something goes wrong, check the inputs — they're right there in the indentation.

**Card 3: The plan is YOUR artifact**
A .ncds file is a portable text document. Version-control it in Git.
Share it with your team. Take it to any orchestrator.
No vendor lock-in. You own what your agents do.

**Design notes:**
- This is the philosophical argument. Keep it punchy, not preachy.
- The three cards should feel like three undeniable truths, not marketing fluff.

---

## SECTION 5: WHAT YOU CAN DO (Lifecycle)

**Headline:**
> Describe → Review → Run → Inspect → Modify → Share

**Six steps as a horizontal flow or timeline:**

1. **Describe** — Write the plan (or have AI generate it from a description)
2. **Review** — Read every step before it runs. A manager can approve it. A domain expert can verify it.
3. **Run** — The compiler transforms it into executable form. The orchestrator runs each step.
4. **Inspect** — Every input/output recorded. Debug any step by checking what it received.
5. **Modify** — Change one step without breaking others. Fork from any checkpoint.
6. **Share** — The file is yours. Git it, publish it, sell it, hand it to a colleague.

**Design notes:**
- This should feel like a journey/timeline, not a feature list.
- Each step should be 1–2 sentences max.
- Visual: maybe a horizontal pipeline with icons, or numbered cards in a row.

---

## SECTION 6: SEE IT IN ACTION (Demo + Video)

**Headline:**
> From plan to output — watch a real agent run

**Two items side by side (or tabbed):**

**A. Canvas Demo Video** (click to play)
- Shows the visual editor: graph view, breakpoints, real-time execution
- Caption: "Design, debug, and run NormCode plans visually"

**B. Live Demo — PPT Agent** (link to /demo)
- A real AI agent orchestrated by a NormCode plan
- Takes a topic → produces a full presentation
- Caption: "Try it yourself — a working NormCode agent generating presentations"

**Design notes:**
- This is the PROOF section. People have seen the syntax, heard the pitch — now show it working.
- Video and demo link should be equally prominent.
- If possible, show a before/after: "here's the NormCode plan" → "here's what it produced"

---

## SECTION 7: KEY PROPERTIES (Technical depth for those who want it)

**Headline:**
> Built for real complexity

**Six compact cards (2×3 grid):**

| Card | Title | One-liner |
|---|---|---|
| 1 | Semantic vs. Syntactic | Only reasoning costs tokens. Data routing is always free. |
| 2 | Parallel Execution | Independent steps run simultaneously. No manual threading. |
| 3 | Checkpoint & Resume | SQLite state at every step. Pause, resume, fork from anywhere. |
| 4 | Smart Patching | Change one step, re-run only what's affected. Cache the rest. |
| 5 | Flow Index System | Every node has a unique address. Set breakpoints, trace logs. |
| 6 | Progressive Compilation | 4 phases from description to execution. Inspect every stage. |

**Design notes:**
- This is for the technical visitor who's now interested and wants depth.
- Keep each card to a title + one sentence. Link to docs for more.
- This section can be collapsed/skippable for non-technical visitors.

---

## SECTION 8: WHO IT'S FOR

**Headline:**
> Built for anyone who wants to control — not just use — AI agents

**Three columns:**

**Today** (early adopters)
- AI engineers wanting cleaner pipelines
- Research teams needing reproducibility
- Technical founders wanting portable agent logic

**Tomorrow** (broader adoption)
- Product managers reviewing agent behavior
- Teams sharing workflows like SQL queries
- Regulated industries proving compliance

**The aspiration**
> Anyone who wants to understand, modify, and own what their AI agents do.

**Design notes:**
- "Today" validates the visitor ("this is for me right now").
- "Tomorrow" paints the vision ("this is going somewhere big").
- The aspiration line is the emotional hook.

---

## SECTION 9: CREDIBILITY

**Headline:**
> Not a pitch. Working software.

**Compact evidence strip (icons + labels, one row):**
- 📄 Published paper (arXiv 2512.10563)
- 💻 Open source (GitHub, MIT)
- 🖥️ Working Canvas editor (download now)
- 🤖 Working demo (live PPT agent)

**University logo strip:**
Oxford · UCL · Shenzhen University

**Design notes:**
- This should feel understated and confident, not boastful.
- One row, small, factual. Let the evidence speak.

---

## SECTION 10: GET STARTED (CTA)

**Headline:**
> Start here

**Three paths (cards or columns):**

**See it first**
- Watch the demo video
- Try the live PPT agent
→ "I want to understand before I commit"

**Learn the language**
- Read the syntax (3 symbols)
- Browse examples
- Understand the compilation pipeline
→ "I want to learn how it works"

**Build something**
- Download Canvas
- Open an example project
- Write your first .ncds plan
→ "I'm ready to try it"

**Design notes:**
- Three paths for three mindsets: curious / studious / doer
- Each path has 2-3 links and a one-line persona description
- The "Build something" path should be the most prominent (primary CTA)

---

## FOOTER

NormCode 规范码 — The Language for AI Agent Workflows
Links: Paper · GitHub · Docs · Contact
Office: TIMETABLE GBA Youth Innovation Base, Nansha, Guangzhou
© 2025 广州心镜智科技工作室

---

## Page Flow Summary

```
HERO          → What is this? (10 seconds)
THE GAP       → Why does it matter? (recognize the pain)
THE LANGUAGE  → Show me (the "aha" moment — 3 symbols, one example)
WHY LANGUAGE  → Why not just a tool? (the deeper argument)
LIFECYCLE     → What can I do with it? (the user journey)
SEE IT        → Prove it (video + live demo)
PROPERTIES    → Technical depth (for the interested)
WHO           → Is this for me? (validation)
CREDIBILITY   → Can I trust this? (evidence)
GET STARTED   → What do I do next? (action)
```

Total: 10 sections. Scannable in 30 seconds. Full read in ~3 minutes.
The story arc: **Pain → Language → Show → Prove → Act.**

---
---

# WHAT WE NEED TO BUILD THIS

Everything below is what's required to turn the sketch above into a mature, professional website.
Organized by: **what we already have**, **what you (the user) need to provide**, and **what I can build with CSS/JS**.

---

## ✅ ASSETS WE ALREADY HAVE

These are in the project and ready to use:

| Asset | Location | Used in |
|---|---|---|
| Psylens logo (with caption) | `assets/images/psylens_logo_caption.png` | Nav, footer, hero |
| Psylens logo (raw) | `assets/images/logo.png` | Favicon, smaller uses |
| University logos (6) | `assets/images/school_logo/` | Section 9: Credibility |
| Timetable office photo | `assets/images/timetable.jpg` | Footer or About |
| Canvas demo video | `assets/videos/normcode_canvas_demo_combined.mp4` | Section 6: See It |
| Canvas installer (.exe) | `assets/downloads/NormCodeCanvasSetup-1.0.7-alpha.exe` | Hero CTA, Section 10 |
| Portable demo (.zip) | `assets/downloads/democh_20260120_134822.normcode-portable.zip` | Section 10 |
| Live PPT demo | `demo/index.html` | Section 6, Section 10 |

---

## 📸 SCREENSHOTS NEEDED FROM YOU

These are the **key visuals** that make the page look like a real product, not a text-only academic page.
I cannot generate these — they need to come from the actual Canvas App.

### PRIORITY 1 — Hero & Product Showcase (most impactful)

**Screenshot A: Canvas App — Full Window (wide)**
- Purpose: **Hero background image** + main product showcase
- What to capture: The full Canvas App window showing a workflow graph with multiple nodes connected
- Size: As wide as possible (full screen / 1920×1080 or wider)
- Tip: Pick a workflow that looks visually rich — many nodes, clear connections, some expanded
- This single image does the most work on the entire page. It says "this is real software."

**Screenshot B: Canvas App — Graph View (zoomed in)**
- Purpose: Section 3 (The Language) or Section 6 (See It) — show the visual representation of a NormCode plan
- What to capture: A closer view of the DAG/graph — nodes with labels, arrows showing data flow
- Should clearly show that the graph corresponds to the NormCode text structure

### PRIORITY 2 — Demo & Proof (builds trust)

**Screenshot C: Canvas App — Code Editor Panel**
- Purpose: Section 3 (The Language) — show real NormCode syntax in the actual editor
- What to capture: The editor panel with a NormCode `.ncds` file open, syntax visible
- Should show indentation, markers (`<-`, `<=`), natural language descriptions
- Bonus: if the editor has syntax highlighting, that's even better

**Screenshot D: Canvas App — Execution/Debug View**
- Purpose: Section 4 (Why a Language — debuggability) and Section 6 (See It)
- What to capture: The execution view showing a workflow mid-run — breakpoints, step status, input/output data
- Should convey: "you can see exactly what each step received and produced"

**Screenshot E: PPT Demo — 3-Panel Interface**
- Purpose: Section 6 (See It) — the live demo in action
- What to capture: The demo page (`demo/index.html`) with all 3 panels visible:
  config panel (left) + execution panel (middle) + file browser (right)
- Ideally mid-execution or showing completed results

### PRIORITY 3 — Nice to have (polish)

**Screenshot F: Canvas App — Before/After**
- Purpose: Section 6 — side-by-side of "the NormCode plan" and "the output it produced"
- What to capture: Split view or two screenshots — the `.ncds` plan → the generated result

**Screenshot G: A `.ncds` File in a Regular Text Editor (VSCode/Notepad)**
- Purpose: Section 4 (The plan is YOUR artifact) — show it's just a text file
- What to capture: A `.ncds` file open in VSCode or any editor, proving portability
- Conveys: "this is not locked in a platform — it's a file you own"

---

## 🎨 WHAT I CAN BUILD WITH CSS/JS (no assets needed)

These are the design elements I'll create programmatically:

### Hero Section
- **Dark gradient background** — deep navy/charcoal (`#0f172a` → `#1e293b`) with subtle radial glow
- **Frosted overlay** on the product screenshot (Screenshot A) — semi-transparent so it reads as a background
- **Floating product frame** — CSS device mockup around Screenshot A (subtle shadow, rounded corners, browser chrome)
- **Animated subtle particles or grid** — optional, lightweight canvas animation for tech feel

### Code Blocks (Section 3: The Language)
- **Editor-style code block** — dark background, title bar with dots (macOS-style window chrome), line numbers, NormCode syntax highlighting via CSS (color `<-` differently from `<=`, highlight natural language in a lighter color)
- Completely built in HTML/CSS — no screenshot needed for this

### Section Backgrounds
- **Alternating light/dark sections** — white → light gray → white → dark navy (for contrast/rhythm)
- **Subtle mesh gradient** or geometric pattern on the dark sections
- **Section dividers** — angled or curved SVG dividers between sections for visual flow

### Lifecycle Timeline (Section 5)
- **Horizontal connected steps** — numbered circles with connecting lines, icons for each step
- **All SVG icons** — inline SVGs for Describe (pen), Review (eye), Run (play), Inspect (magnifier), Modify (wrench), Share (share)

### Property Cards (Section 7)
- **2×3 grid** with subtle border, hover lift effect, small SVG icon per card
- All icons are inline SVG — no image files needed

### Credibility Strip (Section 9)
- **University logos** already exist — I'll add grayscale filter + hover color effect
- **Evidence badges** — pill-shaped badges with inline SVG icons

### CTA Section (Section 10)
- **Dark background** section with three cards, primary card highlighted
- **Glow effect** on the primary "Build something" card

### General Polish
- **Scroll-triggered fade-in animations** — sections fade in as user scrolls (already have this in `main.js`)
- **Smooth hover states** on all interactive elements
- **Responsive design** — all sections adapt to mobile/tablet
- **Loading states** — skeleton shimmer for images while loading

---

## 📐 SCREENSHOT SPECS (how to capture them)

To make the screenshots look their best on the page:

| Property | Recommendation |
|---|---|
| **Resolution** | 2x / Retina if possible (e.g., 2560×1440 or 1920×1080 at 2x) |
| **Format** | PNG for sharp UI, JPG for large backgrounds (quality 85+) |
| **Aspect ratio** | 16:9 for wide shots (A, E), ~4:3 for focused panels (B, C, D) |
| **Background** | Dark theme preferred (matches the hero dark gradient better) |
| **Content** | Use a real, meaningful workflow — not "hello world." The financial audit example or the PPT demo workflow would be ideal. |
| **Clean UI** | Close any popups, notifications, or unrelated windows before capturing |
| **Window state** | Maximized but with window chrome visible (title bar) — this proves it's real software |

---

## 📁 WHERE TO PUT THEM

Place all screenshots in:
```
new_website/assets/images/screenshots/
├── canvas-full.png          ← Screenshot A (hero background)
├── canvas-graph.png         ← Screenshot B (graph view)
├── canvas-editor.png        ← Screenshot C (code editor)
├── canvas-execution.png     ← Screenshot D (execution/debug)
├── demo-ppt.png             ← Screenshot E (PPT demo 3-panel)
├── canvas-before-after.png  ← Screenshot F (optional)
└── ncds-in-vscode.png       ← Screenshot G (optional)
```

---

## 🔢 BUILD PRIORITY ORDER

Once you provide the screenshots, I'll build in this order:

| Phase | What | Depends on |
|---|---|---|
| **Phase 1** | Hero section (dark bg + product image + CTAs) | Screenshot A |
| **Phase 2** | The Language section (editor-style code block + explanation) | Nothing (CSS only) |
| **Phase 3** | The Gap section (3-column problem statement) | Nothing (CSS only) |
| **Phase 4** | Why a Language + Lifecycle + Properties | Nothing (CSS only) |
| **Phase 5** | See It section (video + demo screenshots) | Screenshots D, E |
| **Phase 6** | Who + Credibility + CTA sections | Nothing (CSS only) |
| **Phase 7** | Final polish (animations, responsive, i18n Chinese text) | All above done |

**Phases 2–4 and 6 can be built immediately** — they don't need any screenshots.
**Phases 1 and 5 need your screenshots** to look professional.

---

## ⚡ SUMMARY: What you need to do

1. **Open Canvas App** with a good-looking workflow
2. **Take 5 screenshots** (A through E, prioritize A first)
3. **Drop them in** `new_website/assets/images/screenshots/`
4. **Tell me** and I'll build the whole page

If you can only provide **one screenshot**, make it **Screenshot A** (the full Canvas window).
That alone transforms the hero from "text on white" to "real product."

