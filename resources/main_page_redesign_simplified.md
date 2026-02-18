# Main Page — Section-by-Section Sketch

The page tells one story: **You need control over your AI agents. That requires a language. This is it.**

Visitor should get the idea in 10 seconds (hero), get interested in 30 seconds (problem + syntax),
get convinced in 2 minutes (full page scroll).

---

## SECTION 1: HERO

**Headline:**
> The language for AI agent workflows

**Subtitle:**
> NormCode lets you describe what your AI agents do — step by step, in readable,
> structured syntax. Review it before it runs. Debug any step. Own the plan.

**CTAs:** [Download Canvas]  [Paper]

**Hero Visual — Code ↔ Graph split:**
Below the CTAs, a side-by-side showing the core idea at a glance:
- **Left:** A compact NormCode snippet (5 lines) in an editor frame
- **Center:** → arrow
- **Right:** Abstract graph/tree representation of the same snippet (SVG nodes + edges)
- **Labels:** "You write this" / "It becomes this"

> **TODO:** Replace the placeholder SVG graph with an actual Canvas graph export
> or a more polished hand-crafted SVG once we investigate how the Canvas app
> renders its graph view.

**Design notes:**
- Clean, confident, no clutter
- Headline is category-defining — says WHAT this is
- Subtitle answers "so what?" in one breath — review, debug, own
- No buzzwords. No "revolutionary." Just clarity.
- The code↔graph visual communicates the value prop instantly without requiring a video click

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
- 📄 Research paper (arXiv 2512.10563)
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
Links: Paper · Docs · Contact
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

---
---

# DESIGN SYSTEM — CONCRETE SPECIFICATION

Mapping `designed principles.md` to this project. What we have, what we need to add, and the exact rules per section.

---

## 🔵 PRINCIPLE AUDIT: What We Already Have vs. What's Missing

### ✅ Already built (in `css/variables.css`, `base.css`, `components.css`, `layout.css`, `responsive.css`)

| Principle | Status | Our Implementation |
|---|---|---|
| 1. Design tokens | ✅ Done | `variables.css` — colors, spacing (4→96px scale), typography (12→40px), shadows (3 levels), radius (3 levels), transitions (3 speeds) |
| 2. Grid + rhythm | ✅ Done | `.container` (1100px), `.container-wide` (1200px), `.container-narrow` (800px), grid helpers (2/3/4/auto-fit) |
| 3. Typography | ✅ Done | IBM Plex Sans + Mono, 8-step type scale, tight heading tracking, 1.7 body line-height |
| 4. Color system | ✅ Done | Neutral base + single blue accent (#4DA3FF), soft tints, inverse colors for dark sections |
| 5. Components | ✅ Done | Buttons (primary/secondary/ghost, lg/sm), cards, code blocks, badges, tables, info boxes |
| 6. States | ⚠️ Partial | hover/active on buttons ✓, focus-visible ✓, download states ✓, ripple ✓. Missing: disabled, loading skeleton |
| 7. Motion | ✅ Done | 150/200/400ms transitions, fade-in scroll animation, shimmer, ripple. Calm easing. |
| 8. Responsiveness | ✅ Done | 3 breakpoints (900/768/480), stacking, touch-friendly |
| 9. Accessibility | ⚠️ Partial | focus-visible ✓, skip-link ✓, sr-only ✓. Missing: ARIA for dynamic nav, reduced-motion |
| 10. Performance | ✅ Done | CSS variables, single font family, lazy video loading |
| 11. Consistency | ✅ Done | One radius per category, one shadow per level, one input height pattern |
| 12. No copied assets | ✅ N/A | Original design |

### 🔴 What's Missing for the New Main Page

| Gap | What to add | Where |
|---|---|---|
| **Hero dark mode** | Dark hero section with gradient bg, screenshot overlay | `layout.css` — new `.hero-dark` variant |
| **Product frame** | CSS window chrome / device mockup for screenshots | `components.css` — new `.product-frame` |
| **Split layout** | 50/50 two-column section for text+image pairs | `components.css` — new `.split-section` |
| **Timeline / steps** | Horizontal connected-step component for lifecycle | `components.css` — new `.timeline` |
| **Editor code block** | Code block with macOS-style title bar + line numbers | `components.css` — enhance `.code-block` |
| **Section dividers** | Angled/curved SVG between sections | `layout.css` — new `.section-divider` |
| **Evidence badges** | Horizontal pill badges with icons | `components.css` — enhance `.badge` |
| **Comparison columns** | 3-column layout for The Gap section | `components.css` — new `.comparison-grid` |
| **Glow card** | Highlighted card with accent glow for primary CTA | `components.css` — new `.card-glow` |
| **Reduced motion** | `prefers-reduced-motion` media query | `responsive.css` |
| **`--text-5xl`** | Larger hero headline size (48–56px) | `variables.css` |

---

## 📐 PAGE LAYOUT BLUEPRINT — Section by Section

Each section below specifies: **background**, **container**, **layout pattern**, **key components**, and **spacing**.

### Section 1: HERO

```
┌─────────────────────────────────────────────────────────────────┐
│  DARK GRADIENT BG (#0f172a → #1e293b) + radial glow            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  container (1100px, centered)                           │    │
│  │                                                         │    │
│  │  H1: The language for AI agent workflows                │    │
│  │      (--text-5xl, white, tight tracking)                │    │
│  │                                                         │    │
│  │  Subtitle (--text-lg, inverse-muted, max-width 600px)   │    │
│  │                                                         │    │
│  │  [btn-primary] [btn-secondary]                          │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐                    │
│  │  <- summary      │   │   [summary]      │                    │
│  │    <= summarize   │   │       ↑          │                    │
│  │    <- flags       │ → │   [flags]        │                    │
│  │      <= check     │   │     ↑    ↑       │                    │
│  │      <- data      │   │  [check]  [data] │                    │
│  └──────────────────┘   └──────────────────┘                    │
│   You write this          It becomes this                        │
│                                                                 │
│  .hero-visual (max-width 900px, centered)                       │
│  TODO: Replace placeholder SVG with Canvas graph export          │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `linear-gradient(135deg, #0f172a 0%, #1e293b 100%)` + subtle radial glow at top center
- **Container:** `.container` centered, `padding: 96px 32px 64px`
- **Text:** All white/inverse colors
- **Hero visual:** Code↔graph split below CTAs — compact code editor + abstract SVG graph
- **Mobile:** Stack vertically (code on top, arrow rotated 90°, graph below), headline `--text-2xl`

### Section 2: THE GAP

```
┌─────────────────────────────────────────────────────────────────┐
│  WHITE BG                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header (centered, narrow)                     │    │
│  │  H2 + subtitle                                          │    │
│  ├─────────┬─────────┬─────────┐                           │    │
│  │ Card 1  │ Card 2  │ Card 3  │  .comparison-grid         │    │
│  │ Raw AI  │ Framewk │ No-Code │  (3 cols, equal height)   │    │
│  │ icon    │ icon    │ icon    │                           │    │
│  │ desc    │ desc    │ desc    │                           │    │
│  │ verdict │ verdict │ verdict │  verdict in bold/accent    │    │
│  └─────────┴─────────┴─────────┘                           │    │
│                                                             │    │
│  Punchline text (centered, italic, max-width 700px)        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-white)` — clean contrast after dark hero
- **Container:** `.container`, `padding: 80px 32px`
- **Grid:** `.grid-3` with comparison cards
- **Cards:** Light border, subtle top-accent stripe (different color per card)
- **Mobile:** Stack to 1 column

### Section 3: THE LANGUAGE

```
┌─────────────────────────────────────────────────────────────────┐
│  SUBTLE BG (--bg-subtle / --bg-page)                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header (centered)                             │    │
│  │  H2: "Three symbols. Plain language."                   │    │
│  ├─────────────────┬───────────────────────────────────┐    │    │
│  │  Syntax table   │  Code block (editor style)        │    │    │
│  │  3 rows         │  ┌─ macOS title bar ─────────┐    │    │    │
│  │  <-  = data     │  │ ● ● ●   example.ncds      │    │    │    │
│  │  <=  = action   │  ├────────────────────────────┤    │    │    │
│  │  <*  = loop     │  │ 1  <- executive summary    │    │    │    │
│  │                 │  │ 2      <= generate summary  │    │    │    │
│  │  "Everything    │  │ 3      <- discrepancy flags │    │    │    │
│  │   else is       │  │ ...                        │    │    │    │
│  │   natural       │  └────────────────────────────┘    │    │    │
│  │   language"     │                                    │    │    │
│  └─────────────────┴───────────────────────────────────┘    │    │
│                                                             │    │
│  "Aha" explanation block (centered, max-width 700px)       │    │
│  Callout box style with left accent border                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-page)` — light gray
- **Layout:** `.split-section` — 40%/60% grid (syntax table narrower, code wider)
- **Code block:** Enhanced with `.code-editor` — title bar with 3 dots, filename, line numbers, NormCode syntax coloring
- **Explanation:** `.info-box` style below, centered
- **Mobile:** Stack vertically, code block full-width

### Section 4: WHY A LANGUAGE

```
┌─────────────────────────────────────────────────────────────────┐
│  WHITE BG                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header                                        │    │
│  │  H2: "Only a language can be learnt"                    │    │
│  │  Subtitle: "Tools are used..."                          │    │
│  ├─────────┬─────────┬─────────┐                           │    │
│  │ Card 1  │ Card 2  │ Card 3  │  .grid-3                  │    │
│  │ icon    │ icon    │ icon    │  standard cards            │    │
│  │ title   │ title   │ title   │  with card-icon            │    │
│  │ text    │ text    │ text    │                            │    │
│  └─────────┴─────────┴─────────┘                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-white)`
- **Layout:** Standard section header + `.grid-3` of `.card` with `.card-icon`
- **Cards:** Existing card component, icon + title + paragraph

### Section 5: LIFECYCLE

```
┌─────────────────────────────────────────────────────────────────┐
│  SUBTLE BG                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header                                        │    │
│  │  H2: "Describe → Review → Run → Inspect → Modify"      │    │
│  │                                                         │    │
│  │  ①──────②──────③──────④──────⑤──────⑥                   │    │
│  │  Desc   Review  Run   Inspect Modify Share              │    │
│  │  text   text    text  text    text   text               │    │
│  │                                                         │    │
│  │  .timeline (horizontal connected steps)                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-page)`
- **Layout:** New `.timeline` component — horizontal on desktop, vertical on mobile
- **Step items:** Numbered circle + label + 1-line description, connected by lines
- **Mobile:** Vertical timeline with left-aligned circles + right text

### Section 6: SEE IT IN ACTION

```
┌─────────────────────────────────────────────────────────────────┐
│  DARK BG (--bg-dark)                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header (white text)                           │    │
│  │  H2: "From plan to output"                              │    │
│  ├─────────────────┬───────────────────────────────────┐    │    │
│  │  Video Player   │  Demo CTA Card                    │    │    │
│  │  .product-frame │  Screenshot E + play overlay      │    │    │
│  │  with screenshot│  or direct link to /demo           │    │    │
│  │  + play overlay │  Caption text                     │    │    │
│  └─────────────────┴───────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-dark)` — creates rhythm (white → gray → white → gray → dark)
- **Layout:** `.grid-2` or full-width video with side CTA
- **Video:** Existing `.video-container` with `.video-poster` overlay
- **Demo card:** Screenshot E in `.product-frame` with link to `/demo`

### Section 7: KEY PROPERTIES

```
┌─────────────────────────────────────────────────────────────────┐
│  WHITE BG                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header                                        │    │
│  │  H2: "Built for real complexity"                        │    │
│  ├──────────┬──────────┬──────────┐                        │    │
│  │ Card 1   │ Card 2   │ Card 3   │                        │    │
│  ├──────────┼──────────┼──────────┤  .grid-3               │    │
│  │ Card 4   │ Card 5   │ Card 6   │  compact cards         │    │
│  └──────────┴──────────┴──────────┘                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-white)`
- **Layout:** `.grid-3` (2×3), compact `.card` with `.card-icon`
- **Cards:** Icon + title + one-liner. Optional "Learn more →" link to docs

### Section 8: WHO IT'S FOR

```
┌─────────────────────────────────────────────────────────────────┐
│  SUBTLE BG                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header                                        │    │
│  ├─────────────────┬──────────────────┐                    │    │
│  │  "Today"        │  "Tomorrow"       │  .grid-2           │    │
│  │  - bullet       │  - bullet         │  larger cards      │    │
│  │  - bullet       │  - bullet         │                    │    │
│  │  - bullet       │  - bullet         │                    │    │
│  └─────────────────┴──────────────────┘                    │    │
│                                                             │    │
│  Aspiration quote (centered, italic)                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-page)`
- **Layout:** `.grid-2`, two cards with bullet lists
- **Quote:** Centered, slightly larger text, subtle styling

### Section 9: CREDIBILITY

```
┌─────────────────────────────────────────────────────────────────┐
│  WHITE BG (compact section, less padding)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header (smaller)                              │    │
│  │  H2: "Not a pitch. Working software."                   │    │
│  │                                                         │    │
│  │  [badge] Paper  [badge] Canvas  [badge] Live Demo        │    │
│  │                                                         │    │
│  │  .logo-strip (grayscale → color on hover)               │    │
│  │  [Oxford]  [UCL]  [SZU]                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-white)`, reduced padding (48px instead of 80px)
- **Layout:** Centered, badges in a flex row, logo strip below
- **Badges:** Enhanced `.badge` with inline SVG icon + text
- **Logo strip:** Existing `.logo-strip` component

### Section 10: GET STARTED

```
┌─────────────────────────────────────────────────────────────────┐
│  DARK BG (--bg-dark)                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  .section-header (white text)                           │    │
│  │  H2: "Start here"                                       │    │
│  ├─────────┬─────────┬─────────┐                           │    │
│  │ Card 1  │ Card 2  │ Card 3  │  .grid-3                  │    │
│  │ See it  │ Learn   │★Build   │  Card 3 = .card-glow      │    │
│  │ links   │ links   │ links   │  accent border + glow     │    │
│  └─────────┴─────────┴─────────┘                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

- **Background:** `var(--bg-dark)` — dark closing section mirrors dark hero
- **Layout:** `.grid-3` of cards
- **Primary card:** `.card-glow` — accent border, subtle box-shadow glow
- **Cards on dark bg:** Dark surface (`rgba(255,255,255,0.05)`) with light text

---

## 🎨 NEW CSS TOKENS TO ADD

Add to `variables.css`:

```css
/* ---- Extended type scale for hero ---- */
--text-5xl: 3.5rem;    /* 56px — hero headline desktop */

/* ---- Dark section surfaces ---- */
--bg-dark-surface: rgba(255, 255, 255, 0.05);
--bg-dark-surface-hover: rgba(255, 255, 255, 0.08);
--border-dark: rgba(255, 255, 255, 0.1);

/* ---- Hero gradient ---- */
--hero-gradient-start: #0f172a;
--hero-gradient-end: #1e293b;
--hero-glow: rgba(77, 163, 255, 0.15);

/* ---- Spacing: add 80px step ---- */
--space-5xl: 5rem;     /* 80px — large section padding */
--space-6xl: 7.5rem;   /* 120px — hero padding */
```

---

## 🧱 NEW CSS COMPONENTS TO BUILD

### 1. `.hero-dark` — Dark hero variant

```css
.hero-dark {
    background: linear-gradient(135deg, var(--hero-gradient-start), var(--hero-gradient-end));
    position: relative;
    overflow: hidden;
}
.hero-dark::before {
    /* radial glow */
    content: '';
    position: absolute;
    top: -50%;
    left: 50%;
    transform: translateX(-50%);
    width: 800px;
    height: 800px;
    background: radial-gradient(circle, var(--hero-glow) 0%, transparent 70%);
    pointer-events: none;
}
.hero-dark h1, .hero-dark h2, .hero-dark h3 { color: #fff; }
.hero-dark p, .hero-dark .subtitle { color: var(--text-inverse-muted); }
.hero-dark .badge-accent {
    background: rgba(77, 163, 255, 0.15);
    color: rgba(77, 163, 255, 0.9);
}
```

### 2. `.product-frame` — Screenshot with window chrome

```css
.product-frame {
    border-radius: var(--border-radius-lg);
    overflow: hidden;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border-dark);
}
.product-frame-bar {
    background: #2d2d2d;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.product-frame-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
}
.product-frame-dot:nth-child(1) { background: #ff5f57; }
.product-frame-dot:nth-child(2) { background: #febc2e; }
.product-frame-dot:nth-child(3) { background: #28c840; }
.product-frame img {
    width: 100%;
    display: block;
}
```

### 3. `.code-editor` — Code block with editor UI

```css
.code-editor {
    border-radius: var(--border-radius-lg);
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.code-editor-bar {
    background: #2d2d2d;
    padding: 8px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: var(--text-xs);
    color: rgba(255,255,255,0.5);
}
/* dots same as product-frame-dot */
.code-editor pre {
    background: var(--code-bg);
    margin: 0;
    padding: var(--space-lg);
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    line-height: 1.8;
    overflow-x: auto;
}
.code-editor .line-num {
    color: rgba(255,255,255,0.2);
    user-select: none;
    margin-right: 1.5em;
    display: inline-block;
    text-align: right;
    width: 2em;
}
```

### 4. `.split-section` — Two-column text + visual

```css
.split-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-2xl);
    align-items: center;
}
.split-section.reverse {
    /* image left, text right (Z-pattern) */
}
.split-section.ratio-40-60 {
    grid-template-columns: 2fr 3fr;
}
/* mobile: stack */
@media (max-width: 768px) {
    .split-section { grid-template-columns: 1fr; }
}
```

### 5. `.timeline` — Horizontal lifecycle steps

```css
.timeline {
    display: flex;
    align-items: flex-start;
    gap: 0;
    position: relative;
}
.timeline-step {
    flex: 1;
    text-align: center;
    position: relative;
}
.timeline-step-num {
    width: 40px; height: 40px;
    border-radius: 50%;
    background: var(--accent);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    margin: 0 auto var(--space-sm);
    position: relative;
    z-index: 1;
}
.timeline-step::before {
    /* connecting line */
    content: '';
    position: absolute;
    top: 20px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--border);
    z-index: 0;
}
.timeline-step:first-child::before { left: 50%; }
.timeline-step:last-child::before { right: 50%; }
.timeline-step h4 { font-size: var(--text-sm); margin-bottom: 4px; }
.timeline-step p { font-size: var(--text-xs); color: var(--text-muted); }

/* mobile: vertical */
@media (max-width: 768px) {
    .timeline { flex-direction: column; align-items: flex-start; }
    .timeline-step { text-align: left; display: flex; gap: 16px; }
    .timeline-step::before {
        top: 0; bottom: 0; left: 20px;
        width: 2px; height: auto; right: auto;
    }
}
```

### 6. `.card-glow` — Highlighted card for primary CTA

```css
.card-glow {
    border-color: var(--accent);
    box-shadow: 0 0 20px rgba(77, 163, 255, 0.15);
}
.card-glow:hover {
    box-shadow: 0 0 30px rgba(77, 163, 255, 0.25);
}
```

### 7. `.comparison-grid` — The Gap section columns

```css
.comparison-grid .card {
    border-top: 3px solid var(--border);
    text-align: center;
}
.comparison-grid .card:nth-child(1) { border-top-color: var(--error); }
.comparison-grid .card:nth-child(2) { border-top-color: var(--warning); }
.comparison-grid .card:nth-child(3) { border-top-color: var(--accent); }
.comparison-grid .card .verdict {
    font-weight: 600;
    margin-top: var(--space-md);
    font-style: italic;
}
```

---

## 🎨 SECTION BACKGROUND RHYTHM

The page alternates backgrounds to create visual depth (per Principle #9):

```
Section 1  HERO       → DARK  (gradient #0f172a → #1e293b)
Section 2  THE GAP    → WHITE (--bg-white)
Section 3  LANGUAGE   → GRAY  (--bg-page / --bg-subtle)
Section 4  WHY LANG   → WHITE (--bg-white)
Section 5  LIFECYCLE  → GRAY  (--bg-page)
Section 6  SEE IT     → DARK  (--bg-dark)
Section 7  PROPERTIES → WHITE (--bg-white)
Section 8  WHO        → GRAY  (--bg-page)
Section 9  CREDIBIL.  → WHITE (--bg-white, compact)
Section 10 GET STARTED→ DARK  (--bg-dark)
FOOTER                → DARK  (--bg-dark, continues from section 10)
```

Pattern: **Dark → White → Gray → White → Gray → Dark → White → Gray → White → Dark → Dark**
This creates 3 "zones": bright opening (2-5), dark proof (6), bright depth (7-9), dark close (10+footer).

---

## 📏 SPACING RHYTHM

Per Principle #5, all section spacing follows the token scale:

| Element | Spacing | Token |
|---|---|---|
| Hero top padding | 120px | `--space-6xl` |
| Hero bottom padding (to product frame) | 64px | `--space-3xl` |
| Regular section padding | 80px top/bottom | `--space-5xl` |
| Compact section padding (credibility) | 48px | `--space-2xl` |
| Section title → subtitle | 8px | `--space-sm` |
| Section subtitle → content | 48px | `--space-2xl` |
| Card internal padding | 24px | `--space-lg` |
| Grid gap | 24px | `--space-lg` |
| Card icon → title | 16px | `--space-md` |

No random values. Everything maps to a token.

---

## 📱 RESPONSIVE RULES (per Principle #8)

| Breakpoint | What changes |
|---|---|
| `≤1024px` | Hero headline `--text-3xl` (40px), product frame smaller, reduce section padding |
| `≤768px` | Everything stacks, timeline goes vertical, mobile nav, hero `--text-2xl` (32px) |
| `≤480px` | Minimal padding, buttons full-width, headline `--text-xl` (24px) |

Plus: add `prefers-reduced-motion` — disable all transitions/animations.

```css
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## ✅ ALIGNMENT RULE (per Principle #11)

**We use: Option B — Centered Marketing Style**

- All section headers centered
- All grids centered within container
- CTAs centered
- Text blocks centered with `max-width` for readability
- Exception: The Language split-section has left-aligned text + right code block

Stick to this. Do not randomly left-align some sections and center others.

---

## 📦 COMPLETE BUILD CHECKLIST

Before shipping, verify against the design principles:

- [ ] All values use tokens (no magic numbers)
- [ ] Every interactive element has hover + focus-visible states
- [ ] Section padding is consistent (80px, or 48px for compact)
- [ ] Grid gaps are uniform (24px)
- [ ] Card padding is uniform (24px)
- [ ] Background rhythm alternates correctly (white/gray/dark)
- [ ] All text blocks have max-width (600–800px)
- [ ] Hero product frame has appropriate shadow + border-radius
- [ ] Mobile layout stacks at ≤768px, touch targets ≥44px
- [ ] Typography scale: hero > section h2 > card h3 > body > small
- [ ] Reduced-motion preference respected
- [ ] Skip-link and focus-visible work
- [ ] All screenshots are 2x resolution, compressed
- [ ] Page loads in < 3s on 3G (lazy images, deferred JS)

