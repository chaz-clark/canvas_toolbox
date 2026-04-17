# Canvas API Gotchas

Hard-learned quirks of the Canvas REST API. These are not obvious from reading the docs and have caused silent failures or wasted debugging time. Consult this before writing any new Canvas API code.

---

## Encoding

### Module prerequisites require form-encoded data, not JSON

`PUT /api/v1/courses/:id/modules/:id` with `{"module": {"prerequisite_module_ids": [...]}}` as JSON returns 200 but **silently does nothing**. Canvas ignores the JSON body for this field.

**Fix:** Use form-encoded data:
```python
requests.put(url, headers=headers, data={"module[prerequisite_module_ids][]": module_id})
```

Same applies to `module[workflow_state]` (published/unpublished).

---

## Grading

### Classic quiz points_possible is not auto-calculated correctly

After pushing questions to a classic quiz, Canvas may auto-calculate `points_possible` from the question weights — but the quiz object itself can still show 0. Always explicitly `PUT /quizzes/:id {"quiz": {"points_possible": N}}` after pushing questions.

### Valid grading_type values

Canvas rejects unrecognized values with `"Validation failed: Grading type is not included in the list"`. The accepted values are:

| Canvas value | Meaning |
|---|---|
| `points` | numeric score (default) |
| `pass_fail` | Complete / Incomplete in gradebook |
| `percent` | percentage |
| `letter_grade` | A/B/C/D/F |
| `gpa_scale` | GPA scale |
| `not_graded` | no grade |

**Common mistake:** `complete_incomplete` is not a valid value — use `pass_fail`.

---

## Content types

### New Quizzes cannot be pushed via REST API

New Quiz items (`submission_types: ["external_tool"]`) are LTI-based. You can read them via `/assignments` but cannot create or modify their content via REST. Any attempt to push content to a New Quiz through the assignments endpoint will appear to succeed (200) but the quiz body will not change. New Quiz content must be managed in the Canvas UI.

### Classic quizzes have two IDs

A classic quiz has:
- A `quiz_id` — used in `/quizzes/:id` endpoints and in module items
- An underlying `assignment_id` — the quiz also appears in `/assignments` with `submission_types: ["online_quiz"]`

These are different numbers. The quality check must map between them to avoid false "not in module" positives. Never assume quiz_id == assignment_id.

### late_policy PATCH returns 403 for instructor tokens

`PATCH /api/v1/courses/:id/late_policy` requires an admin token, not an instructor token. Instructor tokens return 403 silently. Set late policies manually in Canvas Settings → Gradebook, or use an admin token.

---

## Issues endpoint returns Pull Requests

`GET /repos/:owner/:repo/issues` (GitHub, not Canvas — but relevant for this repo's gh_issues_agent tooling) returns both issues and PRs. Filter by `"pull_request" not in item` before processing.

---

## Dates

### lock_at / unlock_at vs due_at

Canvas assignments have three date fields:
- `due_at` — when it's due (shown in Grades)
- `lock_at` — when students can no longer submit
- `unlock_at` — when students can first see/submit the assignment

All three must be pushed separately. Pushing only `due_at` does not set availability windows.

### Discussions use todo_date, not due_at

Graded discussions store their due date in `assignment.due_at`. Ungraded discussions use `todo_date`. Pulling and pushing the wrong field results in silent date mismatches.

### Canvas dates are ISO 8601 UTC strings

Canvas stores all dates as strings like `"2026-01-15T06:59:00Z"`. When pushing, send UTC ISO strings. Local timezone offsets will be accepted but may display incorrectly for students in other timezones.

---

## Index and sync

### Full --pull must rebuild index["files"] from scratch

If `index["files"]` is updated in-place (not reset), renamed or deleted Canvas items leave stale filepath entries. These cause false hash diffs on `--status` and orphaned local files. Always reset `index["files"] = {}` before the pull loop and delete local files that were in `prior_hashes` but not in the new index.

### Canvas-side renames create new page_url slugs

When you rename a Canvas Page, Canvas generates a new `page_url` slug. The old URL still resolves (Canvas redirects) but the new slug is the canonical one. After a rename, a full `--pull` is required to update the local filepath and index entry.

---

## Scope

### Course IDs are not portable

The same assignment/quiz/page has a different `canvas_id` in every course (source, master, blueprint, cloned sections). Match content across courses by **title**, never by ID. IDs are only reliable within a single course.

### Always confirm target course ID before any write

Source (415322), master (402262), and blueprint (415130) are different courses. A push scoped to the wrong course_id replicates changes to the wrong course with no warning. Print the course ID at the start of every write operation.
