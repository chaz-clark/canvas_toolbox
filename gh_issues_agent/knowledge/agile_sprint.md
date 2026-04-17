# Canvas Toolbox — Agile Sprint Plan

Tracks active and completed sprints for canvas_toolbox. Updated when issues are closed and committed to GitHub. Each sprint maps to a GitHub Milestone. See `gh_issues_agent_mission.md` for the full rationale behind the milestone order.

---

## Sprint Status Legend

- `[ ]` — not started
- `[~]` — in progress
- `[x]` — complete (closed on GitHub + committed)

---

## Sprint 1 — Trust the Mirror 🔧

**Goal:** Fix bugs where the local mirror silently lies. Every push or pull should do exactly what it says.

**Milestone:** Trust the Mirror
**Status:** Complete ✅

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #1 | False positive: homepage appears in orphaned_pages list | XS | `[x]` | 735463a |
| #3 | Classic quiz push missing title field | XS | `[x]` | 735463a |
| #5 | Classic quiz push missing points_possible | XS | `[x]` | 735463a |
| #2 | Assignment grading_type + submission_types not round-tripped; stale index on rename | S | `[x]` | 1905e8e |

**Work order:** #1 first (isolated, one-line fix). Then #3 and #5 together (same function, same gap). Then #2 last (broadest scope — pull path + index rebuild + validation).

**Definition of done:**
- All four issues closed on GitHub with commit references
- `gh_sync.py` run confirms all moved to `.github_issues/closed/`
- `course_quality_check.py --test` passes (no regressions)

---

## Sprint 2 — Safe to Work In 🏗️

**Goal:** Establish safe zones for local-only artifacts. Expand mirror visibility into New Quizzes.

**Milestone:** Safe to Work In
**Status:** Not started

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #4 | course_ref/ protected folder for local-only artifacts | M | `[ ]` | — |
| #6 | New Quizzes pull support — Phase 1: read-only sidecar files | L | `[ ]` | — |

**Work order:** #4 before #6 (and before #7, #9 in Sprint 3). The `course_ref/` pattern needs to exist before file upload and markdown mirror are built on top of it.

**Definition of done:**
- `course_ref/` is documented and `--pull` does not delete files placed there
- New Quizzes pull down as sidecar `.newquiz.json` files in `course/`
- Index updated with `quiz_engine`, `new_quiz_id`, `settings_path` fields

---

## Sprint 3 — Author Like a Human ✍️

**Goal:** Lower the authoring barrier for teachers. Markdown is easier to edit and better for agents.

**Milestone:** Author Like a Human
**Status:** Not started

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #9 | Markdown authoring mirror (course_src/) — Phase 1: pages only | XL | `[ ]` | — |
| #7 | Canvas file upload for .docx templates — Phase 1: upload + store URL | M | `[ ]` | — |

**Work order:** #9 first. The markdown mirror establishes `course_src/` as a pattern. File upload (#7) can use `course_ref/` (from Sprint 2) as its local home for template files.

**Definition of done:**
- `--pull` optionally populates `course_src/` with `.md` versions of Canvas pages
- Build step compiles `course_src/*.md` → `course/*.html` before push
- File upload pushes local assets to Canvas Files and stores `canvas_file_id` + URL in index

---

## Sprint 4 — Agents That Teach 🤖

**Goal:** New agent capabilities grounded in pedagogy that actively improve course quality.

**Milestone:** Agents That Teach
**Status:** Not started

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #8 | Canvas Schedule Auditor Agent | L | `[ ]` | — |

**Work order:** Single issue. Build after Sprint 3 so the auditor can reason over `course_src/` markdown natively.

**Definition of done:**
- Agent reads setup notes and infers scheduling rules
- Produces week-by-week audit table flagging date drift
- Proposes corrected `due_at`, `lock_at`, `unlock_at` values with UTC offsets
- Propose-before-execute pattern enforced (no silent writes)

---

## Completed Sprints

*(None yet — updated as sprints finish)*

---

## How to Update This File

When closing an issue:
1. Mark its row `[x]` and fill in the commit hash
2. When all issues in a sprint are `[x]`, mark the sprint Status as **Complete** and move it to Completed Sprints below
3. Run `gh_sync.py` to confirm all sprint issues are in `.github_issues/closed/`
4. Note any scope changes or lessons learned in the sprint's notes before archiving
