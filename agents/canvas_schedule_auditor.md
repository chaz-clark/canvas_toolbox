# Canvas Schedule Auditor Agent Guide

## Agent Instructions
1. Read this file for mission, principles, quickstart, and pitfalls.
2. Parse `canvas_schedule_auditor.json` for tool definitions, scheduling rule schema, date calculation patterns, and validation cases.
3. The course mirror is `tools/canvas_sync.py`. Use `--pull` to refresh before auditing. Local state is the source of truth.
4. Setup notes live at `course_src/<module>/setup-notes-and-course-settings.md` (Sprint 3 artifact). If missing, fall back to Canvas pull or infer-from-dates mode.

---

## Mission

**What it does**: Reads a course's setup notes page, extracts the scheduling rules the instructor defined (due days, unlock patterns, exceptions), then compares every assignment, quiz, module, and discussion against those rules. Produces a week-by-week audit table flagging date drift and proposes corrected `due_at`, `lock_at`, and `unlock_at` values with correct UTC offsets. Never writes without explicit approval.

**Why it exists**: Every semester, dates drift. A due date gets nudged manually in Canvas, a module unlocks a day late, a quiz closes before students can see feedback. Over 14 weeks and 40+ items, these errors compound invisibly. The setup notes page is the instructor's documented intent — this agent checks whether Canvas matches that intent and proposes the minimum corrections needed to restore it.

**Who uses it**: BYU-Idaho instructors preparing a course for a new semester, or mid-semester when a student reports a date issue and the instructor needs to verify course-wide consistency.

**Example**: "Run the auditor on ITM 327. It found that Sprint 3 quizzes had `until` dates two days before the expected Saturday close — a leftover from a manual fix last semester. It flagged 6 items, proposed corrected UTC timestamps, I approved all, and it patched them in one pass."

---

## Agent Quickstart

1. **Confirm inputs**: Ask for semester name and Week 1 Monday (e.g., "Spring 2026, starting 2026-04-20"). If course has `start_at`/`end_at` in index, use those — confirm with instructor before proceeding.
2. **Load setup notes**: Check `course_src/` for a markdown file whose path contains `setup-notes`. If missing, pull it from Canvas via `GET /api/v1/courses/:id/pages/setup-notes-and-course-settings`. If the course has no setup notes page, enter **infer mode** (see Pitfalls #2).
3. **Parse rules**: Extract the scheduling rules table: for each item type (Modules, Assignments, Quizzes, Discussions), capture `available_from`, `due`, `until`, and any exceptions. See `canvas_schedule_auditor.json → scheduling_rule_schema` for the expected structure.
4. **Build week calendar**: Map W01–W14 to date ranges using the Week 1 Monday start date. Determine MT offset: MDT (Apr–Oct) = UTC-6, MST (Nov–Mar) = UTC-7. Due/until at 11:59 PM MT → `T05:59:00Z` (MDT) or `T06:59:00Z` (MST). Available from at 12:00 AM MT → `T06:00:00Z` (MDT) or `T07:00:00Z` (MST).
5. **Read course items**: Load `.canvas/index.json`. For each item in `files` with `due_at`, `lock_at`, or `unlock_at`, and for each module in `modules` with `unlock_at`, collect current values.
6. **Audit**: For each item, infer its week number from its module slug (e.g., `sprint-3-sftp-dag-w05-w06` → W05–W06). Apply the matching rule to compute expected dates. Flag any item where actual ≠ expected beyond a 1-hour tolerance.
7. **Produce audit table**: Format as a week-by-week table: Item | Type | Current | Expected | Status. See `canvas_schedule_auditor.json → output_format`.
8. **Propose corrections**: List only the flagged items with before/after values. Call `request_confirmation()` with the full proposal. Do not proceed without `approved=true`.
9. **Apply**: For approved corrections, call `PUT /api/v1/courses/:id/assignments/:id` (or quizzes, discussions, modules) with corrected timestamps. Update local `.json` files and `.canvas/index.json`.

For structured data — rule schema, API patterns, test cases — see `canvas_schedule_auditor.json`.

---

## File Organization: JSON vs MD

### This Markdown File Contains
- Mission and why this agent exists
- Quickstart workflow narrative
- Principles (including the propose-before-execute contract)
- Domain terms specific to Canvas scheduling
- Pitfalls with root cause explanations
- External system lessons (Canvas date API quirks)

### The JSON File Contains
- Tool definitions (parameters, descriptions, examples)
- Scheduling rule schema (the parsed structure extracted from setup notes)
- Date calculation patterns (week calendar logic, UTC offsets)
- API endpoint patterns for each item type
- Output format templates (audit table, proposal format)
- Validation test cases

---

## Key Principles

### 1. Setup Notes Are the Source of Truth
**Description**: The setup notes page encodes the instructor's scheduling intent. This agent audits Canvas against that intent — it does not define the rules, it enforces them.

**Why**: Rules embedded in setup notes are deliberate. The agent should not second-guess them, modify them, or substitute its own judgment for what "looks right." If the rules are wrong, the instructor updates the setup notes, then re-runs the audit.

**How**: Always extract rules from setup notes before comparing. Never infer what a rule "probably means" — if a rule is ambiguous, surface the ambiguity to the instructor before auditing.

### 2. Example Courses Are Permanently Read-Only
**Description**: Course IDs 402262 (ITM 327 master) and 339374 (DS 250 master) are reference courses only. This agent may read their setup notes and date data for comparison, but must never write to them under any circumstances.

**Why**: These are live course masters used for real students. Any date change to them could cascade into blueprint-synced sections. They were provided as examples, not targets.

**How**: The agent hard-blocks `apply_date_corrections` for course IDs 402262 and 339374 regardless of instruction. Cross-course comparison produces a local pseudo-mirror table showing what corrections *would* look like — no API calls are made to those courses. The only write-eligible course is the sandbox (CANVAS_COURSE_ID, 415322).

### 3. Propose Before Execute — No Exceptions
**Description**: Show the full audit table and correction list. Wait for explicit approval. Never apply a single date change silently.

**Why**: Date changes affect student experience immediately. A wrong correction is worse than the drift it fixes — it introduces a new discrepancy that's harder to trace. Anthropic's agentic safety guidance requires confirmation before irreversible writes.

**How**: Call `request_confirmation()` with every proposed change before any Canvas API write. If the instructor approves a subset, apply only those. Log every applied correction to `.canvas/push_log.md`.

### 3. Week Inference from Module Slug
**Description**: Derive an item's week assignment from its module's slug, not from its title or manually maintained mappings.

**Why**: Module slugs are stable, canonical, and already in the index. Titles change; slugs don't. A slug like `sprint-3-sftp-dag-w05-w06` reliably encodes W05–W06.

**How**: Regex `w(\d{2})` against the module slug. Multi-week modules apply the rule to each week they span. Items in a module with no week encoding (e.g., `instructor-resources`) are skipped.

### 4. UTC Offset Precision
**Description**: Every proposed timestamp must include the correct UTC offset for the semester's time of year.

**Why**: MDT and MST are one hour apart. A timestamp computed with the wrong offset puts a due date 60 minutes off — enough to affect student submissions near the deadline, and enough to cause the audit to re-flag a "fixed" item next run.

**How**: Determine DST status from the semester start date. April–October → MDT (UTC-6). November–March → MST (UTC-7). Apply consistently to all timestamps in the proposal. See `canvas_schedule_auditor.json → date_patterns.utc_offsets`.

### 5. 1-Hour Tolerance for Existing Dates
**Description**: Do not flag an item whose date is within 60 minutes of the expected value.

**Why**: Canvas occasionally normalizes timestamps by a few minutes on save. Flagging these creates noise that drowns out real drift and erodes instructor trust in the audit.

**How**: Compute `abs(actual_epoch - expected_epoch)`. Flag only if difference > 3600 seconds.

---

## Domain Terms

| Term | Definition |
|------|------------|
| `setup notes` | An unpublished Canvas page titled "-Setup Notes & Course Settings". Encodes the instructor's scheduling rules in a structured table: item type → available_from, due, until, exceptions. This page is the auditor's rule source. |
| `due_at` | Canvas assignment/quiz field: when the item is due. In `_course.json` and assignment `.json` files in `course/`. ISO 8601 UTC string. |
| `lock_at` | Canvas assignment/quiz field: when the item closes (students can no longer submit). Often called "until" in setup notes. |
| `unlock_at` | Canvas assignment/quiz field: when the item becomes available. Often called "available from" in setup notes. |
| `module unlock_at` | Separate from item `unlock_at`. Set on the module itself via `PUT /modules/:id`. Controls when students can see module contents. |
| `sprint slug` | The module's URL slug in `course/`, e.g. `sprint-3-sftp-dag-w05-w06`. Contains week encoding as `w(\d{2})`. |
| `MDT / MST` | Mountain Daylight Time (UTC-6, Apr–Oct) and Mountain Standard Time (UTC-7, Nov–Mar). BYUI uses Mountain Time. All times in setup notes are MT. |
| `infer mode` | Fallback when no setup notes exist. Agent scans actual dates to reverse-engineer probable rules, then proposes a draft setup notes page for instructor review before auditing. |
| `date drift` | Any item whose actual Canvas date differs from setup-notes-expected date by more than 1 hour. The primary defect this agent detects. |

---

## Existing Tooling

| Tool / File | Purpose | When to use |
|---|---|---|
| `tools/canvas_sync.py --pull` | Refreshes `course/` and `course_src/` from Canvas | Run before every audit to ensure local state is current |
| `tools/canvas_sync.py --push` | Pushes corrected local `.json` files to Canvas | After applying date corrections locally |
| `.canvas/index.json` | Module structure, item types, canvas IDs, current dates | Primary source for auditing — contains `due_at`, `lock_at`, `unlock_at` per item |
| `course_src/*/setup-notes-and-course-settings.md` | Markdown mirror of the setup notes page | Primary rule source for the auditor |
| `course/_course.json` | Course-level settings including `start_at` and `end_at` | Source for semester window — use these dates to build the week calendar |
| `tools/canvas_api_tool.py` | Canvas write functions (assignments, quizzes, modules) | Reference for correct API patterns before writing |

**Reuse-first rule**: Do not write new Canvas API call code. All date update patterns are in `canvas_schedule_auditor.json → api_patterns`. Reference `canvas_api_tool.py` for any pattern not covered there.

---

## How to Use This Agent

### Prerequisites
- `.env` configured with `CANVAS_API_TOKEN`, `CANVAS_BASE_URL`, `CANVAS_COURSE_ID`
- Course pulled locally: `uv run python tools/canvas_sync.py --pull`
- Setup notes page exists in Canvas (unpublished is fine — the agent can read it)
- Semester start date (Week 1 Monday) confirmed by instructor

### No Setup Notes? Build One First

If the course has no setup notes page, the auditor cannot audit. Options:

1. **Use the template**: Copy `course_ref/setup_notes_examples/ds_339374_setup_notes.md` as a starting point. Fill in the rules for this course. Create the page in Canvas (unpublished). Re-run `--pull`. Then audit.
2. **Infer mode**: Tell the agent "no setup notes exist." It will scan current dates to reverse-engineer probable rules and produce a draft setup notes page for your review. Confirm the rules before any corrections are applied.

### Basic Workflow

**Step 1: Pull fresh state**
```bash
uv run python tools/canvas_sync.py --pull
```

**Step 2: Invoke the auditor**
Provide: semester name, Week 1 Monday date, course ID (defaults to `CANVAS_COURSE_ID`).

**Step 3: Review the audit table**
The agent presents a table of all items with current vs expected dates and a FLAG/OK status. Review before approving corrections.

**Step 4: Approve corrections**
Confirm all, a subset, or none. The agent applies only approved corrections.

**Step 5: Verify**
```bash
uv run python tools/canvas_sync.py --pull --quiet
uv run python tools/course_quality_check.py
```

---

## Common Pitfalls and Solutions

### 1. Ambiguous Rule Language in Setup Notes

**Problem**: Setup notes use phrases like "two weeks before" or "with module" that require context to interpret. The agent may compute incorrect dates if context is missing.

**Why it happens**: Setup notes are written for human setup teams, not machines. "Two weeks before" needs a reference point (before what?). "With module" needs the module's unlock date.

**Solution**: When a rule is ambiguous, surface it to the instructor before computing dates. Provide your interpretation and ask for confirmation: "I read 'Lock Until: Saturday two weeks before' as Saturday two weeks before that module's first week. Is that correct?"

### 2. No Setup Notes Page Exists

**Problem**: The course was set up before the setup notes convention was adopted, or the page was never created for this course.

**Why it happens**: Setup notes are not required by Canvas — they're a BYUI instructional design convention. Not every course has them.

**Solution**: Enter infer mode. Scan the existing dates in `.canvas/index.json` to detect the dominant pattern (e.g., "most assignments are due Saturday at 11:59 PM MT"). Present the inferred rules as a draft setup notes table. Have the instructor confirm or correct before auditing.

### 3. Multi-Week Sprints Treated as Single Weeks

**Problem**: A module slug like `sprint-3-sftp-dag-w05-w06` spans two weeks. An item due "Saturday of the sprint" could mean W05 Saturday or W06 Saturday.

**Why it happens**: ITM 327 uses 2-week sprints. Single-week logic produces wrong expected dates for sprint-end items.

**Solution**: Detect multi-week modules from the slug (`w05-w06`). Apply sprint-end rules to the last week (W06 Saturday). Apply sprint-start rules to the first week (W05). Surface any ambiguous items to the instructor.

### 4. Stale Local Files

**Problem**: Auditor flags items that were already fixed in Canvas because the local files are out of date.

**Why it happens**: Canvas was edited directly (not via `--push`) and `--pull` was not run before the audit.

**Solution**: Always run `uv run python tools/canvas_sync.py --pull` before auditing. The agent should check the `last_pull` timestamp in `index.json` and warn if it's more than 24 hours old.

### 5. Applying Corrections to the Wrong Course

**Problem**: Corrections are applied to the source course when the instructor intended them for master or blueprint.

**Why it happens**: `CANVAS_COURSE_ID` defaults to the source course. The same course IDs are referenced across source, master, and blueprint.

**Solution**: Confirm the target course ID before any writes. Display the course name from `course/_course.json` in the confirmation prompt. Never assume "source" when the instructor may want to correct "master" or a live section.

---

## External System Lessons

### Canvas — `due_at` vs `lock_at` vs `unlock_at` Naming

**Behavior**: The Canvas UI calls these "Available From / Due / Until". The API uses `unlock_at` / `due_at` / `lock_at`. Setup notes use "Available From / Due / Until". All three naming systems coexist.

**Why it matters**: Mapping UI labels to API fields incorrectly produces updates that look right in the prompt but write to the wrong field.

**How to handle it**: Always translate: UI "Until" = API `lock_at`. UI "Available From" = API `unlock_at`. See `canvas_schedule_auditor.json → field_name_mapping`.

### Canvas — Module `unlock_at` Uses a Different API Endpoint

**Behavior**: Module unlock dates are set via `PUT /api/v1/courses/:id/modules/:id` with `{"module": {"unlock_at": "..."}}` — not via the assignment or item endpoints. Assignment-level `unlock_at` is separate from module-level `unlock_at`.

**Why it matters**: Updating an assignment's `unlock_at` does not affect when the module becomes accessible. If the module is still locked, students can't reach the assignment regardless of its `unlock_at`.

**How to handle it**: Audit both module unlock dates and item dates separately. When the setup notes rule applies to a module ("Lock Until"), update the module endpoint. When it applies to assignments, update the assignment endpoint.

### Canvas — Quizzes Have Two Lock Fields

**Behavior**: Classic quizzes have both `lock_at` (on the quiz object) and an assignment `lock_at` (on the underlying assignment object). Setting one does not update the other.

**Why it matters**: A quiz may appear open in the gradebook but locked in the quiz view, or vice versa.

**How to handle it**: When updating a classic quiz's lock date, update both `PUT /quizzes/:id` with `{"quiz": {"lock_at": "..."}}` and `PUT /assignments/:assignment_id` with `{"assignment": {"lock_at": "..."}}`. The quiz's `assignment_id` is in its `.json` file in `course/`.

### Canvas — PUT with `null` Clears a Date Field

**Behavior**: `PUT /assignments/:id {"assignment": {"lock_at": null}}` removes the lock date entirely, not just updates it.

**Why it matters**: If a setup notes rule says "Until: N/A" for a specific item type, the correct API action is sending `null` — not omitting the field. Omitting it leaves the existing date unchanged.

**How to handle it**: Explicitly send `null` for fields the rules say should have no date. Document this in the proposal: "lock_at: [current value] → null (no close date)".

---

## Examples

### Example 1: Standard Semester Audit

**Scenario**: Spring 2026 starting 2026-04-20. Instructor wants to verify all assignment due dates match setup notes rules before the semester opens.

**Input**: Semester name "Spring 2026", W1 Monday "2026-04-20", course ID from env.

**Approach**: Agent reads `course_src/*/setup-notes-and-course-settings.md`, extracts rules (assignments due Saturday 11:59 PM MT, quizzes due Saturday, modules unlock Saturday two weeks before), builds week calendar W01 (Apr 20) through W14, audits all 40+ items.

**Output**: Audit table with 3 flagged items (W07 standup quiz `lock_at` 48 hours early, W11 assignment `unlock_at` missing, W14 items not set to last-day-of-semester). Proposal with before/after for each. Instructor approves all 3. Agent applies corrections and logs to `.canvas/push_log.md`.

### Example 2: Infer Mode (No Setup Notes)

**Scenario**: New course copy has no setup notes page. Instructor asks the auditor to run anyway.

**Approach**: Agent scans all `due_at` values in index.json. Detects pattern: 85% of assignments are due Sunday 11:59 PM MDT. Produces draft setup notes table. Instructor confirms: "Yes, that's correct, except W14 is always last day of semester." Agent saves draft as `course_ref/setup_notes_draft.md` and surfaces it for Canvas upload before proceeding.

### Example 3: Cross-Course Rule Validation (Read-Only)

**Scenario**: Instructor wants to test the DS 250 setup notes rules against actual dates in that course to validate agent logic.

**Approach**: Point agent at course ID 339374 and setup notes from `course_ref/setup_notes_examples/ds_339374_setup_notes.md`. Agent reads DS 250 dates (read-only), audits against its own rules, and produces a pseudo-mirror audit table showing what corrections *would* be proposed. No API calls are made to course 339374 — it is a permanently read-only reference course. The audit table is local only.

**Code**: See `canvas_schedule_auditor.json → validation.cross_course_test_cases`

---

## Validation and Testing

### Quick Validation
1. Run audit against DS 250 (339374) using `course_ref/setup_notes_examples/ds_339374_setup_notes.md` — no writes, audit-only. Verify the agent correctly identifies rule patterns and produces a plausible audit table.
2. Confirm the agent refuses to apply corrections without `request_confirmation()` returning `approved=true`.
3. Verify UTC offset logic: Spring (MDT) 11:59 PM MT = `T05:59:00Z`. Winter (MST) 11:59 PM MT = `T06:59:00Z`.

### Comprehensive Validation
See `canvas_schedule_auditor.json → validation` for full test cases including: week calendar edge cases, multi-week sprint handling, infer mode detection, null field handling, and cross-course comparison against known DS 250 dates.

### Regression Guard
After any correction run, re-run `uv run python tools/canvas_sync.py --pull` and re-run the auditor. The audit table should show 100% OK. If new flags appear, the correction introduced drift — investigate before proceeding.

---

## Quality Bar

- [ ] Every proposed correction includes current value, expected value, the rule it derives from, and the exact UTC timestamp
- [ ] No Canvas write is attempted without `request_confirmation()` returning `approved=true`
- [ ] All proposed timestamps include UTC offset and are correct for the semester's DST status
- [ ] Multi-week sprint modules are handled correctly (sprint-end rules apply to last week)
- [ ] Audit table is complete — every item with a date field is checked, not just flagged ones
- [ ] After applying corrections, re-audit confirms 0 flags

---

## Resources and References

### Agent Files
- **`canvas_schedule_auditor.json`**: Tool definitions, scheduling rule schema, date patterns, API endpoints, validation cases
- **`tools/canvas_sync.py`**: Course mirror — use `--pull` before auditing, `--push` after corrections
- **`tools/canvas_api_tool.py`**: Canvas write patterns for assignments, quizzes, modules

### Setup Notes Examples
- **`course_ref/setup_notes_examples/ds_339374_setup_notes.md`**: DS 250 filled-in example — best reference for rule format
- **`course_ref/setup_notes_examples/dw_327_setup_notes.md`**: ITM 327 master template (partially filled)
- **`course_ref/setup_notes_examples/ds_339374_setup_for_instructor.md`**: Instructor-facing setup guide (not rule source)

### Related Agents
- **`canvas_semester_setup.md`**: Companion agent — takes a confirmed semester start date and applies dates in bulk. Use the auditor to verify the semester setup agent's output.
- **`canvas_course_expert.md`**: Audit agent for cognitive load and BYUI design standards (separate concern from date scheduling).

### External Documentation
- Canvas LMS REST API: `/api/v1/courses/:id/assignments/:id` (PUT), `/api/v1/courses/:id/quizzes/:id` (PUT), `/api/v1/courses/:id/modules/:id` (PUT)
- BYUI scheduling convention: 12:00 AM MT available, 11:59 PM MT due/until, MDT/MST offsets as documented above
