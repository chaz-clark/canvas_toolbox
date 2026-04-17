# GitHub Issues Agent — Mission & Strategy

This file captures the working mission, issue triage philosophy, and current milestone plan for the canvas_toolbox GitHub issues workflow. It evolves as the project matures.

---

## Canvas Toolbox Mission

**Help normal teachers use agents to improve their courses** — expanding agent knowledge and skills, applying best practices in course architecture, and bringing proven student learning pedagogy into the tools.

The toolbox is not a developer tool. It is an instructor tool. Every decision about what to build, fix, or prioritize should be filtered through: *does this make it easier for a teacher to run a better course?*

---

## How Issues Relate to the Mission

Three things have to be true before the mission pays off:

1. **The mirror has to be trustworthy.** Agents can only act on course data they can read and write reliably. Bugs that make the local mirror lie to you block everything downstream.

2. **Authoring has to be human-friendly.** Teachers won't edit Canvas HTML. If the content layer isn't approachable, agents can't help teachers write better course content.

3. **Agent capabilities have to be grounded in pedagogy.** New agents should make courses better in measurable ways — clearer structure, better-paced dates, reduced cognitive load — not just add API coverage.

This gives us a natural priority ordering: **fix the foundation → make it safe and ergonomic → add intelligence on top**.

---

## Value Streams (Milestone Framework)

Issues are grouped into four themed milestones rather than traditional sprint velocity. This reflects the project's solo-maintainer reality and the mission-driven sequencing above.

### Milestone 1 — Trust the Mirror 🔧
*Fix bugs where the local mirror silently lies. Teachers won't use a tool they can't trust.*

Issues: #1, #2, #3, #5

- #1 — False positive: homepage appears in orphaned_pages list (XS)
- #3 — Classic quiz push missing title field (XS)
- #5 — Classic quiz push missing points_possible (XS)
- #2 — Assignment grading_type + submission_types not round-tripped; stale index on rename (S)

Work order: #1, #3+#5 together, then #2.

### Milestone 2 — Safe to Work In 🏗️
*Establish safe zones for local-only artifacts. Expand mirror visibility.*

Issues: #4, #6

- #4 — course_ref/ pattern: protected folder for local-only artifacts not at risk from --pull (M)
- #6 — New Quizzes pull support: Phase 1 read-only sidecar files (L)

Do #4 before #6, #7, or #9 — it establishes the pattern that makes those features safe.

### Milestone 3 — Author Like a Human ✍️
*Lower the authoring barrier. Markdown is easier for teachers and better for agents.*

Issues: #9, #7

- #9 — Markdown authoring mirror (course_src/) — Phase 1: pages only (XL)
- #7 — Canvas file upload for .docx templates — Phase 1: upload + store URL (M)

The markdown mirror (#9) is strategic: agents reason over markdown far better than Canvas HTML. Everything the agents help teachers write gets easier once this layer exists.

### Milestone 4 — Agents That Teach 🤖
*New agent capabilities that directly improve course quality.*

Issues: #8

- #8 — Canvas Schedule Auditor Agent: reads setup notes, infers rules, audits dates, proposes corrections (L)

This turns passive instructor documentation into an active rule system. High mission alignment — agents directly improving course architecture.

---

## Recommended Sprint Order

```
Sprint 1 (bugs, fast):     #1 → #3 + #5 together → #2
Sprint 2 (foundation):     #4 → #6
Sprint 3 (authoring UX):   #9 Phase 1 → #7 Phase 1
Sprint 4 (agents):         #8
```

---

## Issue Sizing Reference

| Label | Effort | Examples |
|---|---|---|
| XS | < 1 hour | Single-field fix in push path |
| S | 2–4 hours | Multi-field round-trip + index fix |
| M | half day | New folder pattern + docs + guard logic |
| L | 1–2 days | New agent or major feature Phase 1 |
| XL | 2–3 days | Architectural addition (e.g. markdown mirror) |

---

## Principles for New Issues

When a new issue is filed, classify it against this framework before picking it up:

1. **Is it a trust bug?** (mirror returns wrong data, push silently ignores fields, index goes stale) → Milestone 1 priority. Fix before anything else.
2. **Does it create an unsafe workflow?** (local files at risk of deletion, no safe home for helper artifacts) → Milestone 2.
3. **Does it reduce authoring friction for teachers?** → Milestone 3.
4. **Does it add agent intelligence grounded in pedagogy?** → Milestone 4.
5. **Is it API coverage for its own sake?** → Defer or label `wontfix` if it doesn't serve a teacher workflow.

---

## Token Efficiency — Let Python Do the Heavy Lifting

Agents are expensive per token. Python scripts are fast and cheap. The right division:

- **Agent:** reads knowledge files, identifies what to do, edits tool code, reviews results
- **Python scripts:** execute all bulk API work (paginate responses, write files, build indexes)

**Never have an agent loop over API responses itself** when a Python script can do it in one `uv run`. If you find yourself writing agent logic that iterates over Canvas items, fetch the data once with a script and hand the agent the structured output.

This is already the pattern in canvas_sync.py, blueprint_sync.py, and gh_sync.py. New features should follow the same model: add a Python tool, let the agent orchestrate it.

---

## What This Agent Is Not For

- Tracking PRs (issues only)
- Replacing Canvas UI for things the API can't do
- Building features for developers — the audience is instructors

---

## Living Document Notes

Update this file when:
- A milestone is completed and lessons were learned
- A new value stream emerges that doesn't fit the current four
- The mission expands (e.g. multi-institution support, LMS-agnostic tooling)
- A new agent is added that changes how issues should be triaged
