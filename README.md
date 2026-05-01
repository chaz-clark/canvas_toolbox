# Canvas Course Toolkit

A Python toolkit for managing Canvas LMS courses as code. Mirror course content locally, sync across multiple courses (source → master → blueprint), audit structure, and manage quiz questions — all via the Canvas REST API.

Built for BYU-Idaho instructors. Works with any Canvas institution.

---

## Quick Start

**1. Install**
```bash
git clone <this-repo>
cd <repo>
uv sync
cp .env.example .env
```

**2. Add your credentials to `.env`**
```
CANVAS_API_TOKEN=your_token_here
CANVAS_BASE_URL=https://your-institution.instructure.com
CANVAS_COURSE_ID=123456
```

- **Course ID:** open your Canvas course — it's the number in the URL after `/courses/`
- **API token:** Canvas → Account → Settings → Approved Integrations → New Access Token (requires instructor or admin role)

**3. Pull your course**
```bash
uv run python tools/canvas_sync.py --init
```

This mirrors your entire Canvas course into a local `course/` folder — all modules, pages, assignments, quizzes, discussions, and the syllabus.

**4. Check what you have**
```bash
ls course/                           # one folder per module
uv run python tools/course_quality_check.py   # audit for issues
```

**5. Edit locally, push to Canvas**
```bash
# Edit any file in course/ with a text editor
uv run python tools/canvas_sync.py --status  # see what changed
uv run python tools/canvas_sync.py --push    # push changes to Canvas
```

That's the core loop. Everything else builds on it.

---

## Using canvas_toolbox as an upstream for course repos

The common pattern: each Canvas course gets its own git repo (for that semester's `course/` state, CLAUDE.md, answer keys, etc.), and pulls **scripts and agents** from canvas_toolbox as an upstream. This keeps tooling in sync across many courses while each course owns its own content.

### Initial setup (in the downstream course repo)

```bash
git remote add upstream https://github.com/chaz-clark/canvas_toolbox.git
git fetch upstream
```

### Pulling updates from upstream

**Do not use `git pull upstream main`.** The two repos have unrelated histories and different content. Instead, cherry-pick just the files canvas_toolbox owns:

```bash
git fetch upstream
git checkout upstream/main -- tools/ agents/ .env.example .gitignore README.md
git status                              # review the changes
git commit -m "sync canvas_toolbox upstream"
```

Run this any time you want the latest tooling. Safe to re-run — `course/`, `.env`, `CLAUDE.md`, and everything in `.canvas/` are untouched.

**Why not `--allow-unrelated-histories`:** that permanently fuses the two repos' histories. From then on every pull drags in *all* of canvas_toolbox's commits, including ones you don't want. The selective checkout above is the intended workflow, not a workaround.

### What upstream owns vs. what the course repo owns

| Upstream (canvas_toolbox)     | Course repo                            |
|-------------------------------|----------------------------------------|
| `tools/` (Python scripts)     | `course/` (live course mirror)         |
| `agents/` (agent guides)      | `.env` (credentials, course IDs)       |
| `.env.example`                | `CLAUDE.md` (course-specific context)  |
| `.gitignore`                  | `course_ref/` (local-only artifacts)   |
| `README.md`                   | `.canvas/` (per-course indexes)        |

### Pushing improvements back upstream

If you improve a script or agent and want the fix to reach other courses, push it to canvas_toolbox directly — don't try to push from a downstream course repo.

```bash
# in the canvas_toolbox repo
git checkout main
# make the same edit here
git commit -m "..."
git push origin main
# then in each course repo, run the sync command above
```

---

## What it does

| Tool | Purpose |
|------|---------|
| `canvas_sync.py` | Mirror a Canvas course into a local `course/` folder. Pull, edit, push. Optionally pull referenced files and fuzzy-search Canvas Files. |
| `blueprint_sync.py` | One-way sync from master → Blueprint course (for semester rollouts) |
| `course_mirror.py` | One-off mirror between any two courses by title-matching |
| `course_quality_check.py` | Audit any course — three opt-in modes: structural (default), files (orphans + broken refs), alignment (outcome → rubric chain) |
| `canvas_quiz_questions.py` | Manage classic Canvas quiz questions from a local JSON file |
| `canvas_api_tool.py` | Cognitive load + Hattie 3-phase course auditor |

**Source of truth: your local `course/` folder.** Canvas is the delivery target.

---

## Setup

**Requirements:** Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
git clone <this-repo>
cd <repo>
uv sync
cp .env.example .env
```

**`.env` variables:**
```
CANVAS_API_TOKEN=your_token
CANVAS_BASE_URL=https://byui.instructure.com
CANVAS_COURSE_ID=123456          # your working/source course
MASTER_COURSE_ID=123457          # master template course (optional)
BLUEPRINT_COURSE_ID=123458       # Canvas Blueprint course (optional)
```

**Find your course ID:** open your Canvas course — it's the number in the URL after `/courses/`.

**Generate an API token:** Canvas → Account → Settings → Approved Integrations → New Access Token. Requires instructor or admin role.

---

## Three-Course Architecture (optional)

For courses that use Canvas Blueprints for semester rollout:

```
Source (CANVAS_COURSE_ID)   ← you edit this; course/ mirrors it
       ↓ course_mirror.py
Master (MASTER_COURSE_ID)   ← clean template
       ↓ blueprint_sync.py
Blueprint (BLUEPRINT_COURSE_ID) ← Canvas clones new sections from this
```

If you only have one course, just use `canvas_sync.py` and ignore the rest.

---

## canvas_sync.py — course mirror

```bash
uv run python tools/canvas_sync.py --pull            # pull full course into course/
uv run python tools/canvas_sync.py --pull --quiet    # same, suppress per-file output
uv run python tools/canvas_sync.py --status          # show local changes not yet pushed
uv run python tools/canvas_sync.py --push            # push all local changes to Canvas
uv run python tools/canvas_sync.py --push "sprint-1" # push one module only
uv run python tools/canvas_sync.py --push syllabus   # push syllabus only
```

**Sync order:** always `--status` before `--push`. Don't push without knowing what changed.

### What gets pulled

| Type | Format | Editable |
|------|--------|----------|
| Pages | `.html` — body only | Yes |
| Assignments | `.json` — description, points, due date | Yes |
| Discussions | `.json` — title, body | Yes |
| Quizzes | `.json` — description, metadata | Yes |
| ExternalTool / SubHeader / ExternalUrl | `.json` — metadata only | No — manage in Canvas UI |

**Not pulled:** gradebook, submissions, student data.

### File-aware commands (opt-in)

Every `--pull` automatically scans content for `/courses/X/files/N` references and writes a reverse map at `index["linked_files"]`. The map is free — it's just a regex scan, no extra API calls. Three opt-in commands then work with that map:

```bash
# After --pull has populated linked_files, download the referenced files
uv run python tools/canvas_sync.py --pull-files

# Read-only fuzzy search — find files in Canvas by name, no download
uv run python tools/canvas_sync.py --find-file "rubric"

# Search + interactive picker — pick from matches, download selected
uv run python tools/canvas_sync.py --pull-file "syllabus"

# Skip individual files larger than threshold (e.g. 100mb, 1gb)
uv run python tools/canvas_sync.py --pull-files --max-file-size 100mb

# Abort if total download size exceeds threshold
uv run python tools/canvas_sync.py --pull-files --max-total-size 500mb
```

Files land at `course/_files/<canvas-folder-path>/<filename>`. Each linked_files entry gets enriched with `filename`, `display_name`, `size`, `folder`, `url`, `content_type`, `local_path`.

**Pre-download confirmation:**

| Total scanned size | Behavior |
|---|---|
| < 50 MB | Silent — auto-proceed |
| 50 MB – 1 GB | Prompt with summary + top 5 largest |
| > 1 GB | Prompt with full list before proceeding |

Bypass the prompt for CI: `CANVAS_SYNC_NO_PROMPT=1`.

---

## blueprint_sync.py — master → blueprint

```bash
uv run python tools/blueprint_sync.py --pull     # mirror blueprint into blueprint_course/ + build mapping
uv run python tools/blueprint_sync.py --status   # show mapping + date coverage
uv run python tools/blueprint_sync.py --push     # sync master content + dates → blueprint
```

Syncs: settings, homepage, syllabus, all mapped pages/assignments/quizzes/discussions (with dates), module published state, item completion requirements, sprint prerequisite chain.

**Does not sync:** NewQuiz/ExternalTool content (Canvas REST API limitation — manage these in Canvas UI).

---

## course_quality_check.py — course auditor

Three opt-in audit modes — each runs alone (mode-switching, not combined). Output: `quality_report.md` at repo root + `.canvas/<audit-type>_*.json` for machine-readable.

### Default — structural audit

Issues that cause student problems:

```bash
uv run python tools/course_quality_check.py              # check source course
uv run python tools/course_quality_check.py --master     # check master
uv run python tools/course_quality_check.py --blueprint  # check blueprint
uv run python tools/course_quality_check.py --all        # all three
uv run python tools/course_quality_check.py --all --fix  # auto-fix duplicates
```

**Checks:**
- Duplicate assignment groups, assignments, quizzes, module items
- Published items not linked in any module (students cannot find these)
- Empty modules (sync artifact when all items are NewQuiz/ExternalTool)
- Due/lock/unlock dates outside the course date window

### `--files` — files audit

Surfaces what Canvas's Files UI hides. Cross-references `index["linked_files"]` (built by `canvas_sync.py --pull`) against `GET /courses/:id/files`.

```bash
uv run python tools/course_quality_check.py --files            # source course
uv run python tools/course_quality_check.py --files --master   # master
uv run python tools/course_quality_check.py --files --all      # all three
```

**Three findings:**

| Finding | What it is |
|---|---|
| **Orphans** | Files in Canvas but not referenced from any synced content |
| **Broken references** | File IDs referenced from content but file deleted from Canvas |
| **Likely duplicates** | Files with same display_name, different IDs |

Output also includes top-N orphans by size for cleanup prioritization. **Read-only — no Canvas writes.** A future `--delete-orphans` flag is intentionally NOT in scope until the audit has run against real courses for a semester to calibrate false-positive rate.

**Caveat:** orphan classification is only as reliable as canvas_sync's content scan. Files referenced from surfaces canvas_sync doesn't deeply scan (New Quiz item bodies, rubric long_descriptions, gradebook custom columns) will be falsely flagged as orphans. Verify before acting.

### `--alignment` — alignment-chain audit

Walks Course Design Language Principle 6: **Course Outcome → Module Outcome → Rubric Criterion → Activity.** Flags breaks in the chain.

```bash
uv run python tools/course_quality_check.py --alignment            # source course
uv run python tools/course_quality_check.py --alignment --master   # master
uv run python tools/course_quality_check.py --alignment --all      # all three
```

**Three break categories:**

| Break | Meaning |
|---|---|
| **Course outcomes with no rubric** | Course-level outcome that no assessment evidences |
| **Rubric criteria with no outcome** | Criterion the rubric grades on but no upstream outcome justifies |
| **Module outcomes with no rubric** | Module-level outcome with no rubric coverage |

Heuristic text-based matching (token-set overlap, threshold ≥ 2 shared significant tokens). False positives expected — treat output as a starting point for instructor review, not a list of bugs to fix.

Outcomes are extracted from `course/syllabus.html` and per-module overview pages by looking for headers containing "outcome" / "objective" / "goal" followed by a list. Rubric criteria come from `GET /assignments/:id?include[]=rubric` (works with student tokens, unlike the `/rubrics` endpoint).

---

## canvas_quiz_questions.py — quiz questions

Manages questions for classic Canvas quizzes (not NewQuiz) from a local JSON file:

```bash
uv run python tools/canvas_quiz_questions.py --push course/.../quiz.questions.json  # idempotent
uv run python tools/canvas_quiz_questions.py --list course/.../quiz.questions.json  # read-only
uv run python tools/canvas_quiz_questions.py --clear course/.../quiz.questions.json # delete all
```

**Question file format** (`*.questions.json`):
```json
{
  "canvas_quiz_id": 5911959,
  "course_id": "415322",
  "questions": [
    {
      "question_name": "Short label",
      "question_text": "Full question shown to student.",
      "question_type": "multiple_choice_question",
      "points_possible": 1,
      "answers": [
        {"answer_text": "Correct answer", "answer_weight": 100},
        {"answer_text": "Wrong answer",   "answer_weight": 0}
      ]
    }
  ]
}
```

Supported types: `multiple_choice_question`, `true_false_question`, `short_answer_question`, `multiple_answers_question`, `essay_question`.

Note: `canvas_quiz_id` and `course_id` are course-specific — the same quiz has different IDs in each course. Push to each course separately.

---

## canvas_api_tool.py — structural auditor

```bash
uv run python tools/canvas_api_tool.py --test    # smoke tests, no credentials needed
```

Scores your course against a stack of instructional-design frameworks:

| Framework | What it checks |
|---|---|
| **Cognitive Load Theory** | Working-memory load — manage intrinsic, minimize extraneous, maximize germane |
| **Hattie's 3-Phase Model** | Surface → Deep → Transfer progression; gaps at Surface block everything downstream |
| **Three Domains of Learning** | Cognitive, Affective, Psychomotor coverage (Wilson) |
| **BYUI Taxonomy Explorer** | Verb-level outcome classification (BYUI institutional view, Simpson psychomotor) |
| **Experiential Learning** | Brain-aligned sequencing — Experience → Observation → Discussion → Explanation → Theory |
| **Designer Thinking** | Backward design — Outcome → Evidence → Experience → Content → Reality Check |
| **Toyota Gap Analysis** | Change-plan format — Current State → Target State → Gap → Root Cause → Countermeasure → Verification |

Full descriptions and when-to-use guidance: [`agents/knowledge/README.md`](agents/knowledge/README.md).

---

## Canvas API Gotchas

- **Module prerequisites** — use form-encoded `data={"module[prerequisite_module_ids][]": id}`, not JSON. JSON returns 200 but silently does nothing.
- **Completion requirements** — must be set on every item in a module for the prerequisite lock to enforce. `must_submit` for assignments/quizzes, `must_view` for pages/tools/URLs.
- **Classic quiz points** — Canvas may show 0 after questions are pushed. Fix with `PUT /quizzes/:id {"quiz": {"points_possible": N}}`.
- **late_policy PATCH** — returns 403 for instructor tokens. Set manually in Canvas Settings → Gradebook, or use admin token.
- **IDs are course-specific** — the same assignment has a different ID in every course and every cloned section. Always match content across courses by title, never by ID.
- **Content + module = two steps** — creating an assignment/quiz/page makes it exist in the course but students cannot access it until it is also added as a module item.

---

## Using with AI Coding Tools

This repo ships an `AGENTS.md` at the root that any modern AI coding tool will load as project context. Adoption status:

| Tool | What you do | What happens |
|---|---|---|
| **Claude Code** (CLI) | Just open the repo | AGENTS.md is auto-loaded as a fallback when no CLAUDE.md is present. If you keep a personal CLAUDE.md for local notes, start it with `@AGENTS.md` to import this file. |
| **Antigravity** (Gemini IDE) | Just open the repo | Native AGENTS.md auto-load since v1.20.3 |
| **VS Code + Copilot** | Set `chat.useAgentsMdFile: true` once in user settings | Copilot loads AGENTS.md for every new chat in this workspace |
| **VS Code + Claude / ChatGPT extension** | Same setting flip | Same behavior — AGENTS.md is the cross-tool standard |
| **Cursor** | Just open the repo | Native AGENTS.md auto-load |
| **OpenAI Codex** (CLI) | Just open the repo | Codex was the original AGENTS.md adopter — native |
| **Aider, goose, Windsurf, Zed, Jules, JetBrains Junie, Amp** | Just open the repo | All native |

After AGENTS.md loads, ask the agent *"what can you do for me?"* — the canvas_course_expert TLDR is built in.

---

## BYUI Course Design Conventions

Each student-facing module follows this order:

1. **Overview page** — learning outcomes, estimated time, how items connect
2. **Content** — readings, videos, demos
3. **Teach One Another** — discussion where students explain or apply to peers
4. **Prove It** — assignment, quiz, or milestone demonstrating mastery

Module naming: `Sprint X: Topic (WXX–WXX)` or `Week X: Topic`.

---

## Troubleshooting

**`--pull` returns empty modules** — verify `CANVAS_COURSE_ID` is correct and the token has instructor access. Test: `GET /api/v1/courses/:id` — response should show `"type": "teacher"` in enrollments.

**Push returns 403** — token is read-only or student-level. Generate a new token from an instructor or admin account.

**`--status` shows everything changed after `--pull`** — index hashes may not have been written. Re-run `--pull` (safe to re-run).

**Page looks wrong in Canvas after push** — Canvas adds its own CSS wrapper. The `.html` files store body only. Check in Student View, not the editor.

**Quality check shows "published not in module"** — the item exists in the course but was never linked to a module. Add it via Canvas UI or `POST /modules/:id/items`.

---

## Files

| File | Purpose |
|------|---------|
| `tools/canvas_sync.py` | Source course mirror |
| `tools/blueprint_sync.py` | Master → Blueprint sync |
| `tools/course_mirror.py` | Source → Master mirror |
| `tools/course_quality_check.py` | Course health auditor |
| `tools/canvas_quiz_questions.py` | Classic quiz question manager |
| `tools/canvas_api_tool.py` | Cognitive load auditor + Canvas write functions |
| `agents/canvas_blueprint_sync.md/.json` | Blueprint sync agent guide + API schema |
| `agents/canvas_course_expert.md/.json` | Audit agent guide + rules |
| `agents/canvas_content_sync.md/.json` | Content sync agent guide |
| `agents/knowledge/` | Instructional-design knowledge references (CLT, Hattie, Three Domains, BYUI Taxonomy Explorer, Experiential Learning, Designer Thinking, Toyota Gap Analysis) — see [`agents/knowledge/README.md`](agents/knowledge/README.md) |
| `course/` | Live course mirror — source of truth |
| `AGENTS.md` | Cross-tool project context — auto-loaded by Antigravity, Cursor, VS Code Copilot, Codex, Claude Code (fallback), Aider |
