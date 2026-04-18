# Canvas Toolbox — Agile Sprint Plan

Tracks active and completed sprints for canvas_toolbox. Updated when issues are closed and committed to GitHub. Each sprint maps to a GitHub Milestone. See `gh_issues_agent_mission.md` for the full rationale behind the milestone order.

---

## Sprint Status Legend

- `[ ]` — not started
- `[~]` — in progress
- `[x]` — complete (closed on GitHub + committed)

---

## Active Sprints

*(No active sprints — all issues closed. Open new issues to start Sprint 5.)*

---

## Completed Sprints

---

### Sprint 1 — Trust the Mirror 🔧

**Goal:** Fix bugs where the local mirror silently lies. Every push or pull should do exactly what it says.

**Milestone:** Trust the Mirror
**Status:** Complete ✅
**Tag:** v1.0.1

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #1 | False positive: homepage appears in orphaned_pages list | XS | `[x]` | 735463a |
| #3 | Classic quiz push missing title field | XS | `[x]` | 735463a |
| #5 | Classic quiz push missing points_possible | XS | `[x]` | 735463a |
| #2 | Assignment grading_type + submission_types not round-tripped; stale index on rename | S | `[x]` | 1905e8e |

**Lessons learned:** #1, #3, #5 were safe to batch in one commit. #2 needed its own — broader scope touching pull path, index rebuild, and validation. Good pattern for future sprints.

---

### Sprint 2 — Safe to Work In 🏗️

**Goal:** Establish safe zones for local-only artifacts. Expand mirror visibility into New Quizzes.

**Milestone:** Safe to Work In
**Status:** Complete ✅
**Tag:** v1.1.0

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #4 | course_ref/ protected folder for local-only artifacts | M | `[x]` | 5f697d1 |
| #10 | Automated regression test suite + GitHub Actions CI | M | `[x]` | ae3f9c1 |
| #6 | New Quizzes pull support — Phase 1: read-only sidecar files | L | `[x]` | 34f6c13 |

**Lessons learned:** CI workflow created but triggers commented out pending BYUI policy on storing API tokens in GitHub secrets. Regression suite hits real Canvas sandbox — no mocking, by design.

---

### Sprint 3 — Author Like a Human ✍️

**Goal:** Lower the authoring barrier for teachers. Markdown is easier to edit and better for agents.

**Milestone:** Author Like a Human
**Status:** Complete ✅
**Tag:** v1.2.0

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #9 | Markdown authoring mirror (course_src/) — Phase 1: pages only | XL | `[x]` | 24764b0 |
| #7 | Canvas file upload for .docx templates — Phase 1: upload + store URL | M | `[x]` | 66b2342 |

**Lessons learned:** Canvas file upload uses a two-step pre-signed URL flow — not a simple multipart POST. `course_src/` markdown mirrors are now the foundation for Sprint 4 agent work.

---

### Sprint 4 — Agents That Teach 🤖

**Goal:** New agent capabilities grounded in pedagogy that actively improve course quality.

**Milestone:** Agents That Teach
**Status:** Complete ✅
**Tag:** v1.3.0

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #8 | Canvas Schedule Auditor Agent | L | `[x]` | 12d4a84 |

**Lessons learned:** Agent needs a clarify-before-audit phase — ambiguous setup notes language causes systematic wrong flags. Institution-specific rules (BYUI: no Sunday dates, W05 Student Feedback) must be keyed by institution, not hardcoded. DS 250 cross-course read-only test validated agent logic; clarification session pending.

---

## How to Update This File

When closing an issue:
1. Mark its row `[x]` and fill in the commit hash
2. When all issues in a sprint are `[x]`, mark the sprint Status as **Complete** and move it to Completed Sprints above
3. Run `gh_sync.py` to confirm all sprint issues are in `.github_issues/closed/`
4. Note lessons learned before archiving
