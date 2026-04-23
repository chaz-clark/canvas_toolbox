# Course Design Language — Knowledge Reference

The canonical design-language spec for BYU-Idaho Canvas courses, derived from the faculty-development course **Architects of Learning** (course 405800) — the course whose subject matter *is* course architecture and whose own build is the exemplar. Patterns in this file are **prescriptive**, not observational: if you are building or auditing a course at BYU-Idaho, this is the recipe.

Used by: `canvas_course_expert.md` (design/alignment audit), `canvas_content_sync.md` (generates artifacts against the recipe), complements `hattie_3phase_knowledge.md` (learning progression) and `toyota_gap_analysis_knowledge.md` (gap remediation).

---

## Why this exists

Hattie tells you *whether learning is scaffolded*. Toyota tells you *how to close gaps*. Neither tells you whether the course **feels like one coherent artifact** to the student. Incoherence is pure extraneous load: even when content, assessments, and outcomes are all present, students burn working memory re-orienting on every page.

This file names six principles of coherence and gives the HTML recipe for each.

---

## The Palette

These six colors carry semantic meaning across every artifact. Do not introduce new accents; do not repurpose existing ones.

| Hex | Role | Used on |
|---|---|---|
| `#37474F` | Primary / assignment chrome | Assignment banner, chip, title, Instructions left-border, grading-scale header |
| `#006A79` | Instructional chrome | Week-instruction banner, chip, title, section-header text, Weekly Schedule table header |
| `#006EB6` | Core Questions / callout | Blue callout box border + heading |
| `#EE5655` | Foundational / resource | Red-topped cards (Readings & Resources, Foundational Documents) |
| `#DB9888` | Reflection / lens | Tan-topped cards (Architect's Lens, Architect's Reflection), accent underline on italicized subtitles |
| `#CFD8DC` / `#F5F7F8` / `#FBFBFB` / `#EEEEEE` | Neutrals | Card backgrounds, table borders, panel fills |

Typography: `'Open Sans', Arial, sans-serif` for every heading. Body inherits Canvas default. Icons: [Material Icons](https://github.com/google/material-design-icons) only — never mix icon libraries, never use emoji for functional roles.

---

## Principle 1 — Unified Visual Grammar

Every artifact is assembled from the same small set of components: banner + role chip + title (+ optional subtitle), section headers with an icon, callout boxes, cards with a semantic top-border, tables with the primary color in the header. Students learn the grammar once on Week 01 and get it for free for the rest of the course.

### Recipe (required on every instructional artifact)
1. **Banner image** — full-width, course banner file, background color matches the artifact's primary color
2. **Role chip** directly under the banner — one of: `Course Syllabus`, `Week NN Instruction`, `Week NN Assignment`, `Announcement`. Chip background = artifact's primary color; white text; `0.75rem`; `4px 12px` padding; `border-radius: 4px`
3. **H1 title** in the artifact's primary color, `2.2rem`, Open Sans, `line-height: 1.1`
4. **Optional subtitle** — gray `#666`, `1.1rem`, italic, left-border `3px solid #DB9888`, `padding-left: 15px`
5. **Content area** — white background, `40px` padding, `border: 1px solid #e0e0e0`, rounded bottom corners

### Gap signals (audit)
| Signal | What it means |
|---|---|
| Artifact has no banner or chip | Students can't tell what kind of thing they're on |
| Banner color doesn't match the chip/title color | Breaks the semantic palette |
| H1 uses a different font or size on different pages | No grammar; every page is a new read |
| Same content type rendered different ways across weeks | Pattern-breaking — trains the wrong mental model |
| Color used decoratively (different accent per page) | Noise, not signal |
| >6 accent colors on one page | Visual hierarchy collapses |

---

## Principle 2 — Sustained Narrative Metaphor

The course is named for a metaphor (*Architects of Learning*) and the metaphor is *load-bearing*, not decorative. It appears in the course title, in the name of recurring components, in the reasoning of every weekly overview, and in the capstone. Students carry the metaphor out of the course as the handle they hold the content by.

### Recipe
1. **Choose a single metaphor** that maps to the domain. For course-design courses: architecture (foundation, blueprint, load-bearing, stress test, structural integrity). For writing courses: craft (draft, revision, reader). Pick one and commit.
2. **Name recurring components with the metaphor**:
   - Reflection prompt on every week page → `The Architect's Lens`
   - Closing reflection on every assignment → `The Architect's Reflection`
   - Course-level guiding question → `The Architect's Question`
3. **Use the metaphor to reason in week purpose statements**:
   > *The Metaphor:* Just as an architect subjects a structure to stress tests, we must design assessments that accurately measure whether students can withstand the rigors of the "Peak Actions" we've identified.
   > *The Outcome:* By the end of this week, you will have a draft of your primary assessments that align with your weekly outcomes.
4. **Keep the metaphor visible in the capstone.** If Week 13 abandons the language, the metaphor was never load-bearing.

### Gap signals
| Signal | What it means |
|---|---|
| Metaphor named in syllabus, absent from weekly pages | Marketing language, not design language |
| Metaphor switches or mixes (architect + journey + recipe) | Framework thrash |
| Weekly artifacts use the metaphor in titles but not in reasoning | Surface decoration |
| Metaphor disappears after Week 3 or 4 | Writer fatigue, not design |

---

## Principle 3 — Dual-Framing on Every Task

Every instructional artifact opens with a two-panel header. One panel answers *why this exists*. The other answers *what you will have by the end*. Neither panel is optional and neither may repeat the other.

### Recipe — Week instruction page
1. **Core Questions callout** (blue, `#006EB6`) — 1–3 questions the week answers
2. **Purpose section** with two paragraphs:
   - **The Metaphor:** — relates the week to the course's central metaphor
   - **The Outcome:** — names the concrete artifact the student will have by week's end (a draft, a map, a reflection — never "understand X")

### Recipe — Assignment
Two side-by-side flex panels at the top of the body (each `flex: 1; min-width: 280px;`):
- **Purpose** (left) — one sentence on why this assignment exists in the course arc
- **Overview** (right) — one sentence on what the student will produce

### Gap signals
| Signal | What it means |
|---|---|
| Page starts with instructions, no purpose | Student executing without knowing why |
| "Outcome" is a learning-objective verb ("students will understand") | No observable target |
| Purpose and Overview say the same thing | Dual-framing is performative, not functional |
| Assignment description opens with submission logistics | Priority inversion — admin before meaning |

---

## Principle 4 — Consistent Structural Beats

Beyond visual grammar, there is a **rhythm**. Every week page hits the same beats in the same order; every assignment hits its own set of beats in the same order. Students develop an automatic navigation schema.

### Recipe — Week instruction page, in this order
1. Banner + chip + title + subtitle
2. Core Questions callout (blue)
3. Purpose section (icon: `format_shapes`) — Metaphor + Outcome
4. Preparation section (icon: `build`) — one row of cards:
   - **Readings & Resources** card (red-top `#EE5655`, icon: `chrome_reader_mode` or `account_balance`)
   - **The Architect's Lens** card (tan-top `#DB9888`, icon: `eyeglasses`) — italic reflection prompt
5. Weekly Schedule section (icon: `event`) — 2-column table, header `#006A79`, rows: `Class Session N` | topic & focus

### Recipe — Assignment, in this order
1. Banner + chip + title
2. Purpose + Overview two-panel
3. `#f5f7f8` panel with `Instructions` header, containing numbered **Part N** blocks. Each Part block: white bg, `border-left: 5px solid #37474F`, H4 title, 1–3 paragraphs.
4. *(Optional)* `Submission Criteria` block — dashed border `#37474F`, icon `check_circle_outline`, bulleted list
5. **The Architect's Reflection** closing card — tan-top, centered, large eyeglasses icon, italic blockquote

### Recipe — Syllabus, in this order
1. Banner + `Course Syllabus` chip + course title H1
2. Course Description + Course Outcomes two-panel (description is 2/3 width, outcomes panel is 1/3 width on `#f5f7f8`)
3. Instructor Information — one card per instructor in a responsive grid
4. Grading Scale + Grading Components two-panel
5. AI Policy section (border-left `#37474f`, `#f8fafb` bg)
6. Course Policies grid (responsive minmax 300px)
7. Closing **Architect's Reflection** card

### Gap signals
| Signal | What it means |
|---|---|
| Section order changes week to week | No schema can form |
| Some weeks have a reflection, some don't | Inconsistent closure |
| Assignments vary between bullet instructions and prose instructions | Extra parsing cost per assignment |
| Weeks 11–13 abandon the structure used in Weeks 01–10 | Capstone is exactly when structure matters most |

---

## Principle 5 — Rubrics as Observable Behaviors, Not Adjectives

Use a **3-level rating scale** on every rubric. Each rating gets a name and a full sentence describing what that level looks like. No adjectives standing alone.

### Recipe
1. **Three rating levels, always**: `Meets Expectations` → `Developing` → `Does Not Yet Meet Expectations`
2. **Each rating has a `description` (the name) and a `long_description` (the full sentence).** Never write "Excellent" with no body.
3. **Meets-level descriptor describes the minimum threshold**, not aspirational. Developing describes partial coverage. Does-not-yet describes what's missing.
4. **Include an Organization and Professional Communication criterion on every rubric** — consistent weight (1 point is typical) — to train students that craft matters regardless of content.
5. **Weight criteria by priority.** The heaviest criterion is the central learning target, not the longest one to grade.
6. **Tag each criterion to a framework or outcome** in the `description` field (e.g., `Scaffolding Through Bloom's Taxonomy`, `Course Map Alignment`).
7. **Show the rubric to students before submission**, not after grading.

### Canonical example (Week 07 Course Map rubric, criterion 5 of 5)

> **Course Map Alignment** — 3 points
> - **Meets Expectations (3):** Completes a course map that shows how course outcomes connect to module outcomes, assessments, activities, and instructional materials. The relationships among these elements are present and usable for planning the course.
> - **Developing (2):** Completes a course map, but some connections among outcomes, assessments, activities, or materials are missing, partial, or uneven.
> - **Does Not Yet Meet Expectations (0):** Provides an incomplete course map or does not show usable connections among outcomes, assessments, activities, and materials.

Notice: Meets is observable ("relationships are present and usable for planning"), Developing names the specific degradation ("missing, partial, or uneven"), Does-Not-Yet names the absent behavior ("does not show usable connections").

### Gap signals
| Signal | What it means |
|---|---|
| 5+ rating levels | Discrimination collapses — graders default to middle |
| Rating descriptors are single adjectives | Grade depends on grader mood |
| Criteria overlap | Students graded twice for one thing |
| No Organization/Communication criterion on any assignment | Signals craft doesn't matter (it always does) |
| Weights don't match criterion importance | Students optimize for grade, not learning |
| Rubric shown only at grading time | Used for judgment, not learning |

### Fetching rubrics with a student token
`GET /api/v1/courses/:id/rubrics` requires teacher permission. Workaround:
```
GET /api/v1/courses/:id/assignments/:id?include[]=rubric
```
Returns the full criterion + ratings tree for student tokens.

---

## Principle 6 — Alignment Traceability

You can draw a straight line from **any artifact a student touches** back to a **course-level outcome**. The chain is:

`Course Outcome → Module Outcome → Assessment → Rubric Criterion → Activity`

A broken link anywhere in the chain is a latent gap.

### Recipe
1. **Write course outcomes first, once, in the syllabus.** Phrase each as an observable capability.
2. **Write module outcomes as a Bloom's-scaffolded sub-sequence of the course outcomes.** Earlier weeks sit lower on the taxonomy (Remember, Understand, Apply); later weeks climb (Analyze, Evaluate, Create).
3. **Make each assignment's rubric criteria restate module outcome language.** If the module taught Bloom's scaffolding, the rubric has a criterion called `Scaffolding Through Bloom's Taxonomy`.
4. **Reference outcomes explicitly** in the assignment's Purpose panel when possible.
5. **Verify the capstone rubric maps to the course outcomes listed in the syllabus.** This is the traceability audit.

### Gap signals
| Signal | What it means |
|---|---|
| Syllabus outcomes never reappear in any week page or assignment | Outcomes are ornamental |
| Rubric criteria measure something the week's instruction didn't teach | Assessment/instruction mismatch |
| Module outcomes use identical verbs at the same Bloom level every week | No scaffolding |
| A rubric exists but the assignment body doesn't mention its criteria | Students grade-farm instead of learning |
| A course outcome has no assessment mapped to it | Unverifiable outcome — drop it or build for it |

### Auditable from a course mirror
Proposed extension to `course_quality_check.py` (flag: `--alignment`):

1. Parse outcomes from `syllabus.html` → list of course outcomes
2. For each module (`_module.json` + overview page), extract module-level outcomes
3. For each assignment (`*.json`), fetch rubric via `assignments/:id?include[]=rubric`
4. Tokenize criterion descriptions; check substring coverage of outcome verbs/nouns
5. Flag: (a) course outcomes with no downstream rubric criterion, (b) rubric criteria with no upstream module outcome, (c) module outcomes with no rubric evidence

---

## Cognitive Load Mapping

| Principle | Primary load axis |
|---|---|
| 1. Unified Visual Grammar | Reduces **extraneous load** |
| 2. Sustained Metaphor | Reduces **extraneous load**, supports **germane load** (transfer) |
| 3. Dual-Framing | Reduces **extraneous load** (priority set before content) |
| 4. Consistent Structural Beats | Reduces **extraneous load** (navigation schema becomes automatic) |
| 5. Observable Rubrics | Reduces **extraneous load**, increases **germane load** (criteria as study tool) |
| 6. Alignment Traceability | Aligns **intrinsic load** to outcomes |

None of these principles add content load. They all reduce friction, freeing working memory for the intrinsic difficulty of the material.

---

## Hattie Phase Mapping

| Principle | Strongest phase impact |
|---|---|
| 1. Unified Visual Grammar | **Surface** — navigation predictability |
| 2. Sustained Metaphor | **Transfer** — the handle students carry content with |
| 3. Dual-Framing | **Surface → Deep** — intention before acquisition |
| 4. Consistent Structural Beats | **Surface** — schema for course navigation |
| 5. Observable Rubrics | **Deep → Transfer** — self-assessment against observable targets |
| 6. Alignment Traceability | **All phases** — broken alignment blocks any phase it touches |

---

## Quick Audit Checklist

Score each 0–2 (0 = absent, 1 = inconsistent, 2 = consistent):

| # | Question | Score |
|---|---|---|
| 1 | Does every artifact of the same type look the same? | 0–2 |
| 2 | Is there a metaphor, and does it survive to the capstone? | 0–2 |
| 3 | Does every task open with both *why* and *what you'll have*? | 0–2 |
| 4 | Do section beats repeat in the same order every week? | 0–2 |
| 5 | Do rubric ratings describe observable behavior, not adjectives? | 0–2 |
| 6 | Can I trace every rubric criterion back to a course outcome? | 0–2 |

**Total / 12.** A course under 6/12 is assembled, not architected. A course 10+/12 is teaching students *by example* what good design looks like — the highest form of instructional design there is.

---

## Appendix A — HTML Component Templates

Drop-in HTML for generating artifacts that match the recipe. `{{mustache}}` variables for substitution. The course banner file ID (`161684278` in AoL) should be parameterized per course; other styling is canonical.

### A.1 — Artifact wrapper

```html
<div class="byui-container" style="border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px; overflow: hidden; margin-top: 0;">
  <div style="width: 100%; line-height: 0; background-color: {{primary_hex}};">
    <img style="width: 100%; height: auto; display: block;" role="presentation"
         src="{{banner_image_url}}" alt="{{course_name}} Banner" loading="lazy">
  </div>
  <header class="banner-title-area" style="background-color: #ffffff; padding: 30px 40px 10px 40px; border-bottom: 1px solid #eee;">
    <div style="display: flex; flex-direction: column; gap: 8px;">
      <span style="display: inline-block; background-color: {{primary_hex}}; color: #ffffff; padding: 4px 12px; font-size: 0.75rem; width: fit-content; border-radius: 4px;"> {{role_chip}} </span>
      <h1 style="margin: 0; font-family: 'Open Sans', Arial, sans-serif; font-size: 2.2rem; color: {{primary_hex}}; line-height: 1.1;">{{title}}</h1>
      {{#subtitle}}
      <p style="margin: 5px 0 0 0; color: #666; font-size: 1.1rem; border-left: 3px solid #DB9888; padding-left: 15px; font-style: italic;">{{subtitle}}</p>
      {{/subtitle}}
    </div>
  </header>
  <div class="main-content" style="padding: 40px; background-color: #ffffff;">
    {{body}}
  </div>
</div>
```

**Primary hex by artifact:** syllabus and assignments → `#37474F`; week-instruction pages → `#006A79`.
**Role chip values:** `Course Syllabus` | `Week NN Instruction` | `Week NN Assignment` | `Announcement`.

### A.2 — Core Questions callout (week-instruction only)

```html
<section class="callout-blue" style="background-color: #f0f7f9; border-left: 6px solid #006EB6; padding: 25px; margin-bottom: 40px; border-radius: 0 8px 8px 0;">
  <h3 style="color: #006eb6; margin-top: 0; font-size: 1.3rem; display: flex; align-items: center; gap: 12px; font-family: 'Open Sans', sans-serif;">
    <img style="width: 28px; height: 28px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/help_outline/materialicons/24dp/2x/baseline_help_outline_black_24dp.png" alt="" loading="lazy">
    Core Questions
  </h3>
  <ul style="margin: 10px 0 0 5px;">
    {{#questions}}<li>{{.}}</li>{{/questions}}
  </ul>
</section>
```

### A.3 — Section header (icon + underline)

```html
<h3 class="section-header" style="color: #006a79; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; margin: 40px 0 20px 0; font-family: 'Open Sans', sans-serif; font-size: 1.2rem; display: flex; align-items: center; gap: 12px;">
  <img style="width: 28px; height: 28px;" src="{{material_icon_url}}" alt="" loading="lazy">
  {{label}}
</h3>
```

**Canonical section labels + icons (week-instruction):** `Purpose` / `format_shapes`, `Preparation` / `build`, `Weekly Schedule` / `event`.

### A.4 — Purpose / Metaphor + Outcome pair (week-instruction)

```html
<p><strong>The Metaphor:</strong> {{metaphor_paragraph}}</p>
<p><strong>The Outcome:</strong> {{observable_artifact_statement}}</p>
```

### A.5 — Red card: Readings & Resources

```html
<div class="card card-red" style="flex: 1; min-width: 300px; background-color: #fbfbfb; padding: 25px; border-radius: 8px; border: 1px solid #eee; border-top: 6px solid #EE5655;">
  <h4 style="color: #ee5655; margin-top: 0; font-size: 1.1rem; display: flex; align-items: center; gap: 12px; font-family: 'Open Sans', sans-serif;">
    <img style="width: 32px; height: 32px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/chrome_reader_mode/materialicons/24dp/2x/baseline_chrome_reader_mode_black_24dp.png" alt="" loading="lazy">
    Readings &amp; Resources
  </h4>
  <ul style="line-height: 1.6; margin-top: 10px; font-size: 0.95rem;">
    {{#items}}<li><strong><a href="{{url}}" target="_blank">{{title}}</a>:</strong> {{annotation}}</li>{{/items}}
  </ul>
</div>
```

### A.6 — Tan card: The Architect's Lens (reflection prompt on week pages)

```html
<div class="card card-tan" style="flex: 1; min-width: 300px; background-color: #fbfbfb; padding: 25px; border-radius: 8px; border: 1px solid #eee; border-top: 6px solid #DB9888;">
  <h4 style="color: #db9888; margin-top: 0; font-size: 1.1rem; display: flex; align-items: center; gap: 12px; font-family: 'Open Sans', sans-serif;">
    <img style="width: 32px; height: 32px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/symbols/web/eyeglasses/materialsymbolsoutlined/eyeglasses_24px.svg" alt="" loading="lazy">
    The Architect's Lens
  </h4>
  <p style="font-style: italic; margin-top: 10px; font-size: 0.95rem;">{{prompt}}</p>
</div>
```

### A.7 — Weekly Schedule table

```html
<div class="table-wrap" style="overflow-x: auto; margin-top: 20px;">
  <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
    <thead>
      <tr>
        <th style="width: 30%; background-color: #006a79; color: white; padding: 15px; text-align: left; font-size: 0.85rem;" scope="col">Session</th>
        <th style="background-color: #006a79; color: white; padding: 15px; text-align: left; font-size: 0.85rem;" scope="col">Topic &amp; Focus</th>
      </tr>
    </thead>
    <tbody>
      {{#sessions}}
      <tr{{#alt}} style="background-color: #f9f9f9;"{{/alt}}>
        <td style="padding: 15px; border-bottom: 1px solid #eee;"><strong>Class Session {{n}}</strong></td>
        <td style="padding: 15px; border-bottom: 1px solid #eee;">{{focus}}</td>
      </tr>
      {{/sessions}}
    </tbody>
  </table>
</div>
```

### A.8 — Assignment: Purpose + Overview two-panel

```html
<div style="display: flex; flex-wrap: wrap; gap: 30px; margin-bottom: 40px;">
  <div style="flex: 1; min-width: 280px;">
    <h3 style="color: #37474f; font-size: 1.1rem; border-bottom: 2px solid #37474F; padding-bottom: 5px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
      <img style="width: 20px; height: 20px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/lightbulb_outline/materialicons/24dp/2x/baseline_lightbulb_outline_black_24dp.png" alt="" loading="lazy">
      Purpose
    </h3>
    <p style="font-size: 0.95rem; margin: 0;">{{why_sentence}}</p>
  </div>
  <div style="flex: 1; min-width: 280px;">
    <h3 style="color: #37474f; font-size: 1.1rem; border-bottom: 2px solid #37474F; padding-bottom: 5px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
      <img style="width: 20px; height: 20px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/visibility/materialicons/24dp/2x/baseline_visibility_black_24dp.png" alt="" loading="lazy">
      Overview
    </h3>
    <p style="font-size: 0.95rem; margin: 0;">{{what_sentence}}</p>
  </div>
</div>
```

### A.9 — Assignment: Instructions panel with Part blocks

```html
<div style="background-color: #f5f7f8; border-radius: 8px; padding: 30px; border: 1px solid #CFD8DC;">
  <h3 style="color: #37474f; margin-top: 0; margin-bottom: 25px; font-size: 1.4rem; font-family: 'Open Sans', sans-serif; display: flex; align-items: center; gap: 12px;">
    <img style="width: 28px; height: 28px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/list/materialicons/24dp/2x/baseline_list_black_24dp.png" alt="" loading="lazy">
    Instructions
  </h3>
  {{#parts}}
  <div style="margin-bottom: 20px; background: white; padding: 20px; border-radius: 6px; border-left: 5px solid #37474F;">
    <h4 style="margin-top: 0; color: #37474f; font-size: 1.1rem;">Part {{n}}: {{part_title}}</h4>
    <p style="margin-bottom: 0;">{{body_html}}</p>
  </div>
  {{/parts}}
</div>
```

### A.10 — Assignment: Submission Criteria block (optional)

```html
<div style="margin-top: 30px; padding: 25px; border: 1px dashed #37474F; border-radius: 8px; background-color: #fff;">
  <h4 style="margin-top: 0; color: #37474f; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
    <img style="width: 20px; height: 20px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/png/action/check_circle_outline/materialicons/24dp/2x/baseline_check_circle_outline_black_24dp.png" alt="" loading="lazy">
    Submission Criteria
  </h4>
  <ul style="font-size: 0.95rem; margin-bottom: 0; padding-left: 20px;">
    {{#criteria}}<li><strong>{{label}}:</strong> {{detail}}</li>{{/criteria}}
  </ul>
</div>
```

### A.11 — Closing card: The Architect's Reflection

Used at the bottom of every assignment *and* the syllabus. Ties the artifact back to the metaphor.

```html
<div class="card card-tan" style="margin-top: 40px; background-color: #fbfbfb; padding: 30px; border-radius: 8px; border: 1px solid #eee; border-top: 6px solid #DB9888; text-align: center;">
  <div style="display: flex; justify-content: center; margin-bottom: 15px;">
    <img style="width: 48px; height: 48px;" src="https://raw.githubusercontent.com/google/material-design-icons/master/symbols/web/eyeglasses/materialsymbolsoutlined/eyeglasses_24px.svg" alt="" loading="lazy">
  </div>
  <h4 style="color: #db9888; margin-top: 0; font-size: 1.1rem; font-family: 'Open Sans', sans-serif;">The Architect's Reflection</h4>
  <blockquote style="margin: 20px 0 0 0; padding: 0; border: none; font-style: italic; font-size: 1.1rem; color: #555; line-height: 1.6;">
    "{{reflection_question}}"
  </blockquote>
</div>
```

---

## Appendix B — Rubric JSON template

The shape Canvas returns (and expects) for a compliant rubric, fetched via `GET /api/v1/courses/:id/assignments/:id?include[]=rubric`:

```json
{
  "rubric": [
    {
      "id": "_criterion_id",
      "description": "Course Map Alignment",
      "long_description": "",
      "points": 3.0,
      "criterion_use_range": false,
      "ratings": [
        {
          "id": "_rating_id",
          "description": "Meets Expectations",
          "long_description": "Completes a course map that shows how course outcomes connect to module outcomes, assessments, activities, and instructional materials. The relationships among these elements are present and usable for planning the course.",
          "points": 3.0
        },
        {
          "id": "_rating_id",
          "description": "Developing",
          "long_description": "Completes a course map, but some connections among outcomes, assessments, activities, or materials are missing, partial, or uneven.",
          "points": 2.0
        },
        {
          "id": "_rating_id",
          "description": "Does Not Yet Meet Expectations",
          "long_description": "Provides an incomplete course map or does not show usable connections among outcomes, assessments, activities, and materials.",
          "points": 0.0
        }
      ]
    }
  ],
  "rubric_settings": {
    "title": "{{assignment_title}}",
    "points_possible": 10.0,
    "free_form_criterion_comments": false,
    "hide_score_total": false,
    "hide_points": false
  }
}
```

Every rubric should include the `Organization and Professional Communication` criterion as one of its rows (typically 1 point, 3 ratings) regardless of subject matter.
