# Sprint QC Runbook

QC gate that must pass before any sprint commit is pushed or tagged. Uses a sandbox Canvas course to validate fixes against a live Canvas instance without touching the production course.

---

## Setup

Add to `.env`:
```
CANVAS_SANDBOX_ID=your_sandbox_course_id
```

The sandbox course should be a real Canvas course the instructor controls — it can be empty or a copy. It is safe to read from and write to during QC runs.

To run QC against the sandbox instead of the production course, temporarily swap the course ID:
```bash
# In .env, set:
CANVAS_COURSE_ID=your_sandbox_course_id
```
Or pass inline:
```bash
CANVAS_COURSE_ID=$CANVAS_SANDBOX_ID uv run python tools/canvas_sync.py --pull
```

---

## QC Levels

### Level 0.5 — Sandbox Prerequisites (run before any sprint-specific tests)

Verify the sandbox course has the content types required for the current sprint's tests. Do not proceed to Level 2 if prerequisites are missing — add the required content to the sandbox first.

```bash
uv run python -c "
import json
from collections import Counter
d = json.load(open('.canvas/index.json'))
types = Counter(v.get('type') for v in d.get('files', {}).values())
has_hp = bool(d.get('homepage'))
print('Content inventory:')
for t, n in sorted(types.items(), key=lambda x: -x[1]):
    print(f'  {t}: {n}')
print(f'  Homepage: {\"yes\" if has_hp else \"no\"}')
"
```

| Sprint | Required content types | Minimum count | Can agent create? |
|---|---|---|---|
| Sprint 1 | Homepage, Quiz (classic) | 1 homepage, 1+ classic quiz | Yes — via API |
| Sprint 2 | NewQuiz, Assignment | 1+ NewQuiz, 1+ assignment | Partial — assignments yes, NewQuiz no (UI only) |
| Sprint 3 | Page, Assignment | 5+ pages, 1+ assignment | Yes — via API |
| Sprint 4 | Page (setup notes), Assignment with due dates | 1 setup-notes page, 3+ dated assignments | Yes — via API |

**If a prerequisite is missing:**

- **Agent can create it** (pages, assignments, classic quizzes): Create a minimal test fixture via the Canvas API before running tests, and delete it after. Document the fixture in the sprint QC notes.
  ```python
  # Example: create a minimal classic quiz for testing
  POST /api/v1/courses/{sandbox_id}/quizzes
  {"quiz": {"title": "QC Test Quiz", "quiz_type": "assignment", "points_possible": 10}}
  ```

- **Agent cannot create it** (NewQuiz, ExternalTool, LTI items): Stop and ask the user:
  > "The sandbox course is missing a required content type for Sprint N QC: **[type]**. This must be created manually in the Canvas UI. Please add at least one **[type]** to the sandbox course (ID: {CANVAS_SANDBOX_ID}), then let me know when it's ready."

**Current sandbox inventory (145706 — Canvas Instructor SandboxS21_141):**
- Pages: 132 ✓
- Assignments: 33 ✓
- Quizzes (classic): 22 ✓
- Discussions: 12 ✓
- NewQuiz: 4 ✓ (confirm API accessibility before Sprint 2)
- Homepage: yes ✓

---

### Level 0 — Smoke Tests (always run first, no credentials needed)
```bash
uv run python tools/canvas_api_tool.py --test
```
Must pass with no errors before any sandbox testing begins.

### Level 1 — Sandbox Pull (validates read path)
```bash
CANVAS_COURSE_ID=$CANVAS_SANDBOX_ID uv run python tools/canvas_sync.py --pull --quiet
```
Confirms the tool connects, pulls without errors, and writes a valid `course/` and `index.json`.

### Level 2 — Sprint-Specific Tests (validates the actual fixes)
Run the tests listed for the current sprint below.

### Level 3 — Quality Check (confirms no regressions)
```bash
CANVAS_COURSE_ID=$CANVAS_SANDBOX_ID uv run python tools/course_quality_check.py
```
Should produce no new issues that weren't present before the sprint.

---

## Sprint 1 — Trust the Mirror QC

**Status:** Not started
**Issues being validated:** #1, #2, #3, #5

### #1 — Homepage false positive fix

**Test:**
```bash
CANVAS_COURSE_ID=$CANVAS_SANDBOX_ID uv run python tools/canvas_sync.py --pull --quiet
```
**Pass criteria:**
- `index["orphaned_pages"]` does not contain an entry whose `page_url` matches `index["homepage"]["page_url"]`
- Verify: `python3 -c "import json; d=json.load(open('.canvas/index.json')); hp=d.get('homepage',{}).get('page_url'); print('PASS' if not any(o['page_url']==hp for o in d.get('orphaned_pages',[])) else 'FAIL — homepage still in orphans')"`

---

### #3 + #5 — Classic quiz title and points_possible push

**Setup:** Identify a classic quiz in the sandbox course. Note its `canvas_id` from `.canvas/index.json` after pull.

**Test:**
1. Edit the local quiz JSON in `course/`: change `title` and set `points_possible` to a test value
2. Push:
```bash
CANVAS_COURSE_ID=$CANVAS_SANDBOX_ID uv run python tools/canvas_sync.py --push
```
3. Verify in Canvas UI (or via API):
```bash
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses/$CANVAS_SANDBOX_ID/quizzes/QUIZ_ID" \
  | python3 -m json.tool | grep -E '"title"|"points_possible"'
```

**Pass criteria:**
- Canvas quiz title matches the edited local value
- Canvas `points_possible` matches the edited local value
- No error returned by `--push`

---

### #2 — Assignment grading_type + submission_types round-trip + index rebuild

**Test A — grading_type and submission_types push:**
1. Edit a local assignment JSON: set `grading_type` to `pass_fail` and `submission_types` to `["online_upload"]`
2. Push:
```bash
CANVAS_COURSE_ID=$CANVAS_SANDBOX_ID uv run python tools/canvas_sync.py --push
```
3. Verify:
```bash
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses/$CANVAS_SANDBOX_ID/assignments/ASSIGNMENT_ID" \
  | python3 -m json.tool | grep -E '"grading_type"|"submission_types"'
```
**Pass:** `grading_type` = `"pass_fail"`, `submission_types` = `["online_upload"]`

**Test B — index rebuild on full pull:**
1. Rename an assignment title directly in Canvas UI on the sandbox course
2. Run full pull:
```bash
CANVAS_COURSE_ID=$CANVAS_SANDBOX_ID uv run python tools/canvas_sync.py --pull
```
**Pass:** Old filename gone from `course/`, new filename present, `.canvas/index.json` reflects new title and filepath — no stale entries

---

## Sprint 2 QC — Safe to Work In

*(Defined when Sprint 2 begins)*

**Issues:** #4, #6

### #4 — course_ref/ not deleted by --pull
- Place a test file in `course_ref/`
- Run `--pull`
- Pass: file still present after pull

### #6 — New Quizzes sidecar files
- Confirm `.newquiz.json` sidecar files appear for New Quiz items after pull
- Confirm index contains `quiz_engine`, `new_quiz_id`, `settings_path` fields

---

## Sprint 3 QC — Author Like a Human

*(Defined when Sprint 3 begins)*

**Issues:** #9, #7

### #9 — Markdown mirror
- Run extended pull, confirm `course_src/*.md` files created for pages
- Edit a markdown file, run build step, confirm `course/*.html` updated
- Push and verify Canvas page updated

### #7 — File upload
- Upload a test `.docx` to sandbox Canvas Files
- Confirm `canvas_file_id` and URL stored in index
- Pass: file visible in Canvas Files

---

## Sprint 4 QC — Agents That Teach

*(Defined when Sprint 4 begins)*

**Issues:** #8

### #8 — Schedule Auditor
- Provide a known-bad date configuration in sandbox
- Run auditor
- Pass: correctly flags the bad dates, proposes corrected values, does not write without approval

---

## QC Sign-Off

Before marking a sprint complete, confirm:

- [ ] Level 0 smoke tests pass
- [ ] Level 0.5 sandbox prerequisites verified — required content types exist in sandbox
- [ ] Level 1 sandbox pull completes without error
- [ ] All sprint-specific tests pass (see above)
- [ ] Level 3 quality check shows no new issues introduced by this sprint
- [ ] `agile_sprint.md` updated with `[x]` for all sprint issues
- [ ] Ready to tag per `semantic_versioning.md`
