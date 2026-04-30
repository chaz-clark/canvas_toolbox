# BYUI Course Design Templates

Drop-in HTML and JSON templates that match the recipe in [`agents/knowledge/course_design_language_knowledge.md`](../../knowledge/course_design_language_knowledge.md).

These templates are the implementation layer for BYU-Idaho's Course Design Language — the visual grammar, structural beats, rubric shape, and component library used across courses derived from the Architects of Learning faculty-development course (course `405800`).

## Template list

| File | Used in artifact | Purpose |
|---|---|---|
| `artifact_wrapper.html` | All | Banner + role chip + title + subtitle wrapper that every artifact (week page, assignment, syllabus) sits inside |
| `core_questions_callout.html` | Week-instruction page | Blue callout box framing the weekly Core Questions |
| `section_header.html` | All | `<h3>` with icon + underline; used for `Purpose`, `Preparation`, `Weekly Schedule`, etc. |
| `purpose_metaphor_outcome.html` | Week-instruction page | The Metaphor + The Outcome paragraph pair |
| `card_red_readings.html` | Week-instruction page | Red-topped card for Readings & Resources |
| `card_tan_architects_lens.html` | Week-instruction page | Tan-topped reflection-prompt card |
| `weekly_schedule_table.html` | Week-instruction page | Two-column session × topic table |
| `assignment_purpose_overview.html` | Assignment | Two-panel `Purpose` + `Overview` header |
| `assignment_instructions_parts.html` | Assignment | Instructions panel with repeating Part blocks |
| `assignment_submission_criteria.html` | Assignment (optional) | Dashed-border block listing submission criteria |
| `closing_architects_reflection.html` | Assignment + Syllabus | Tan-topped centered reflection card at the bottom |
| `rubric_3level_canonical.json` | Rubrics | Canvas-shape rubric with the 3-level scale (Meets / Developing / Does Not Yet Meet) and `long_description` on every rating |

## Substitution

Templates use `{{mustache}}` placeholders. The two project-level parameters are:

- `{{primary_hex}}` — `#37474F` for syllabus and assignments, `#006A79` for week-instruction pages
- `{{banner_image_url}}` — your course banner file URL (parameterized per course; `161684278` is the AoL course's banner ID)

Other placeholders are content-specific (`{{title}}`, `{{questions}}`, `{{sessions}}`, etc.) — see the corresponding template file.

## Palette

The semantic color roles these templates assume:

| Hex | Role |
|---|---|
| `#37474F` | Primary / assignment chrome |
| `#006A79` | Instructional chrome (week pages) |
| `#006EB6` | Core Questions / callout |
| `#EE5655` | Foundational / resource (red cards) |
| `#DB9888` | Reflection / lens (tan cards) |
| `#CFD8DC` / `#F5F7F8` / `#FBFBFB` / `#EEEEEE` | Neutrals |

Typography: `'Open Sans', Arial, sans-serif` for every heading. Icons: [Material Icons](https://github.com/google/material-design-icons) only — never mix icon libraries.

## Forking for a non-BYUI institution

These templates encode BYUI's institutional design choices. Other universities adopting this toolkit can:

1. Fork this directory to `<institution>_course_design/`
2. Swap the palette hex values for their own brand
3. Adjust the role-chip labels (`Course Syllabus`, `Week NN Instruction`, etc.) to match their nomenclature
4. Replace the banner image URL parameter
5. Update `course_design_language_knowledge.md` to cite the forked templates

The principles in the knowledge file (visual grammar, narrative metaphor, dual-framing, structural beats, observable rubrics, alignment traceability) port without modification — only the implementation specifics here are institution-bound.
