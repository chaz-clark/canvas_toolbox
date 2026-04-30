# Knowledge References

Distilled instructional-design knowledge sources used by the Canvas audit agents (`agents/canvas_course_expert.md` and the audit rules in `canvas_course_expert.json`). Each file is a self-contained reference: theory, audit indicators, and the tag the agent emits when the framework applies.

These files travel with the upstream `agents/` folder, so any course repo that pulls from canvas_toolbox gets them automatically.

---

## How to choose between them

The seven files cover overlapping but distinct ground. Quick routing:

| If you're auditing… | Start with |
|---|---|
| Module navigation, item count, working-memory load | [`cognitive_load_theory_knowledge.md`](cognitive_load_theory_knowledge.md) |
| Whether learning progresses Surface → Deep → Transfer | [`hattie_3phase_knowledge.md`](hattie_3phase_knowledge.md) |
| Whether the course covers more than just thinking (cognitive vs. affective vs. psychomotor) | [`three_domains_knowledge.md`](three_domains_knowledge.md) *(academic framing)* or [`taxonomy_explorer_knowledge.md`](taxonomy_explorer_knowledge.md) *(BYUI tool framing)* |
| Whether the module sequence is brain-aligned (experience before explanation) | [`experiential_learning_knowledge.md`](experiential_learning_knowledge.md) |
| Whether the course was built backward from outcomes (vs. forward from content) | [`designer_thinking_knowledge.md`](designer_thinking_knowledge.md) |
| Writing a precise change plan for a flagged issue | [`toyota_gap_analysis_knowledge.md`](toyota_gap_analysis_knowledge.md) |

---

## The files

### [`hattie_3phase_knowledge.md`](hattie_3phase_knowledge.md)

**Source:** Hattie, J. (2009). *Visible Learning*.
**Core idea:** Every learner moves through three phases — Surface → Deep → Transfer. A gap at any phase blocks the next.
**When to use:** Diagnosing *what kind of learning* a module is supporting. Course content can be present and still fail because Surface gaps (no overview, broken nav) starve Deep and Transfer of any foundation.
**Audit tag:** `hattie_phase` ∈ {surface, deep, transfer, all}.

---

### [`cognitive_load_theory_knowledge.md`](cognitive_load_theory_knowledge.md)

**Source:** Sweller (1988); Atkinson & Shiffrin memory model; Medical College of Wisconsin CLT guide (2022).
**Core idea:** Working memory holds 5–9 chunks. Three load types compete for that space — **manage** intrinsic, **minimize** extraneous, **maximize** germane.
**When to use:** Almost always. CLT is the mechanics layer underneath Hattie's phases — every audit issue gets a CLT load type.
**Audit tag:** `cognitive_load_type` ∈ {extraneous, intrinsic, germane}.
**Pairs with:** `hattie_3phase_knowledge.md` (which phase is which load blocking?).

---

### [`three_domains_knowledge.md`](three_domains_knowledge.md)

**Source:** Wilson, L.O. *The Second Principle*. Bloom (1956), Krathwohl (1964), Anderson & Krathwohl (2001), Harrow (1972).
**Core idea:** Courses can be cognitive, affective, or psychomotor — and most "non-emotional" courses still imply affective objectives they never name. Wilson uses **Harrow's 6-level psychomotor**.
**When to use:** When auditing learning outcomes against the academic-research framing, or when the affective domain (collaboration, judgment, professional behavior) is in scope.
**Audit tag:** `learning_domain` ∈ {cognitive, affective, psychomotor, multi}.
**Pairs with:** `taxonomy_explorer_knowledge.md` (BYUI's tool view of the same three domains).

---

### [`taxonomy_explorer_knowledge.md`](taxonomy_explorer_knowledge.md)

**Source:** BYU-Idaho. *The Taxonomy Explorer.* `content.byui.edu/file/c5d91be3-…/Taxonomy_Explorer.html`
**Core idea:** BYUI's institutional verb-classification tool. Same three domains as Wilson, but uses **Simpson's 7-level psychomotor** (Perception → Origination) instead of Harrow.
**When to use:** When the course's outcomes were written using BYUI's verb-lookup tool, or when faculty prefer the BYUI institutional view.
**Audit tag:** `taxonomy_source` ∈ {byui_explorer, wilson, agnostic}.
**Pairs with:** `three_domains_knowledge.md` (theory, holistic-design rationale, physical ≠ psychomotor boundary — all deferred to that file).

---

### [`experiential_learning_knowledge.md`](experiential_learning_knowledge.md)

**Source:** Aswad, M. *How does the brain learn? And why don't we teach that way?* Times Higher Education, Campus.
**Core idea:** The brain learns experience-first. Reverse the dominant LMS pattern — instead of *theory → example → practice*, sequence as **Experience → Observation → Discussion → Explanation → Theory**.
**When to use:** When a module is structurally complete but feels like transmission. Experiential adds the sequencing diagnostic that Hattie and CLT alone miss.
**Audit tag:** `sequencing` ∈ {experience_first, explanation_first, not_applicable}.
**Pairs with:** `hattie_3phase_knowledge.md` (sequences across phases), `designer_thinking_knowledge.md` (educator-as-designer rationale).

---

### [`designer_thinking_knowledge.md`](designer_thinking_knowledge.md)

**Source:** Backward Design framework (Wiggins & McTighe lineage), distilled from BYUI *Teacher and Designer Thinking* materials.
**Core idea:** Design backward from outcomes. Five stages — Outcome → Evidence → Experience → Content → Reality Check. *Content is a tool, not the destination.*
**When to use:** When a course has lots of content but unclear outcomes, or when assessments don't trace back to claimed outcomes.
**Audit tag:** `design_mode` ∈ {teacher, designer}.
**Pairs with:** `experiential_learning_knowledge.md` (supplies the neural rationale for content-as-tool).

---

### [`toyota_gap_analysis_knowledge.md`](toyota_gap_analysis_knowledge.md)

**Source:** Toyota Production System / A3 Problem Solving methodology.
**Core idea:** For every flagged issue, force specificity: Current State → Target State → Gap → Root Cause → Countermeasure → Verification. Surfaces systemic causes that propagate across modules.
**When to use:** Always — this is the **change-plan format** every audit finding ends in. Without it, the audit is a list of complaints; with it, it's a plan.
**Audit tag:** none (it's the output format, not a classifier).

---

## Tag stack — full audit output

A well-formed audit issue carries up to seven tag dimensions so the reader can route it cleanly:

| Tag | From file |
|---|---|
| `hattie_phase` | `hattie_3phase_knowledge.md` |
| `cognitive_load_type` | `cognitive_load_theory_knowledge.md` |
| `learning_domain` | `three_domains_knowledge.md` or `taxonomy_explorer_knowledge.md` |
| `taxonomy_source` | `taxonomy_explorer_knowledge.md` (only when BYUI-tool framing was used) |
| `sequencing` | `experiential_learning_knowledge.md` |
| `design_mode` | `designer_thinking_knowledge.md` |
| `design_coherence` | `course_design_language_knowledge.md` *(forthcoming — issue #15)* |
| `design_principle` | `course_design_language_knowledge.md` *(forthcoming — issue #15)* |

The last two are paired (two-axis): `design_coherence` ∈ `{architected, partial, assembled}` describes *how well* a principle is satisfied; `design_principle` ∈ `{visual_grammar, narrative_metaphor, dual_framing, structural_beats, observable_rubrics, alignment_traceability}` says *which principle* the finding is about.

The Toyota A3 structure wraps the issue itself.

---

## Adding a new knowledge file

If you add a new framework reference here, follow the existing pattern:

1. Frontmatter: source citation, who uses it (`canvas_course_expert.md` etc.), companion files.
2. Theory section — short, prose-first.
3. Canvas Audit Indicators — concrete signals that flag the issue.
4. The audit tag the agent should emit.
5. Quick Reference for Auditors — a numbered checklist.
6. Add a one-paragraph entry to this README.
