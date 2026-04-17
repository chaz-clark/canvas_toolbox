# Semantic Versioning — Canvas Toolbox

Source of truth for how canvas_toolbox versions are assigned, tagged, and released. The agent must consult this file before tagging any sprint completion.

---

## Format

```
vMAJOR.MINOR.PATCH
```

Current version: **v1.0.0** (initial public release)

---

## Rules

### PATCH — `v1.0.X`
Bug fixes that correct existing behavior without changing the interface.

**Triggers:**
- A push/pull path silently ignored a field (now fixed)
- A false positive or false negative in quality checks
- An index that went stale or kept orphaned entries
- Any fix where the tool now does what it already claimed to do

**Sprint mapping:** Sprint 1 (Trust the Mirror) → `v1.0.1` on completion

---

### MINOR — `v1.X.0`
New capabilities added in a backward-compatible way.

**Triggers:**
- A new tool or script added to `tools/`
- A new agent added to `agents/`
- A new supported Canvas item type (e.g. New Quizzes pull)
- A new folder convention (e.g. `course_ref/`, `course_src/`)
- A new CLI flag on an existing tool

**Sprint mapping:**
- Sprint 2 (Safe to Work In) → `v1.1.0`
- Sprint 3 (Author Like a Human) → `v1.2.0`
- Sprint 4 (Agents That Teach) → `v1.3.0`

---

### MAJOR — `vX.0.0`
Breaking changes — existing workflows must change to keep working.

**Triggers:**
- `course/` folder structure changes (renames, reorganization)
- `.canvas/index.json` schema changes that break existing index files
- A tool flag or command is removed or renamed
- The three-course architecture model changes

**Process:** Major bumps require a migration note in the README before tagging.

---

## Tagging Rules

1. **Tag at sprint completion, not per issue.** One tag per milestone keeps the tag history readable.
2. **All sprint issues must be closed on GitHub before tagging.**
3. **QC must pass on the sandbox course before tagging.** See `sprint_qc.md`.
4. **Tag on `main` only.** Never tag a work-in-progress branch.
5. **Tag message = sprint name + one-line summary.**

### How to tag

```bash
git tag -a v1.0.1 -m "Sprint 1: Trust the Mirror — fix quiz push, homepage orphan false positive, assignment index rebuild"
git push origin v1.0.1
```

---

## Version History

| Version | Date | Sprint | Summary |
|---|---|---|---|
| v1.0.0 | 2026-04-17 | — | Initial public release |
| v1.0.1 | — | Sprint 1 | Trust the Mirror: fix classic quiz push (title, points), homepage false positive, assignment round-trip + index rebuild |
| v1.1.0 | — | Sprint 2 | Safe to Work In: course_ref/ pattern, New Quizzes pull |
| v1.2.0 | — | Sprint 3 | Author Like a Human: markdown mirror, Canvas file upload |
| v1.3.0 | — | Sprint 4 | Agents That Teach: Canvas Schedule Auditor Agent |

---

## Pre-Tag Checklist

Before running `git tag`:

- [ ] All sprint issues show `[x]` in `agile_sprint.md`
- [ ] All sprint issues closed on GitHub (confirmed via `gh_sync.py`)
- [ ] QC passed on sandbox course (see `sprint_qc.md`)
- [ ] `agile_sprint.md` sprint marked Complete and moved to Completed Sprints
- [ ] Version History table above updated with date and summary
- [ ] README reflects any new commands or behavior
