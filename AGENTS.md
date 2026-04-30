# AGENTS.md

Project context for AI coding tools. This file is auto-loaded by Antigravity, Cursor, VS Code Copilot, OpenAI Codex, Aider, and others. Claude Code reads it as a fallback when no `CLAUDE.md` is present.

> If you create a personal `CLAUDE.md` for local notes, start it with `@AGENTS.md` so this file stays loaded too.

## What This Is

A Canvas LMS course management toolkit. It mirrors a live Canvas course into a local `course/` folder, audits structure against pedagogical frameworks, and applies instructor-approved changes via the Canvas REST API. Three courses can be managed in parallel: source (working), master (template), and blueprint (semester rollout).

Universal toolkit — works with any Canvas institution. Originally built for BYU-Idaho but designed to be institution-agnostic.

## Course Architecture

| Variable | Course ID | Purpose |
|---|---|---|
| `CANVAS_COURSE_ID` | [your ID] | Source / working course — `course/` mirrors this |
| `MASTER_COURSE_ID` | [your ID] | Master template — receives pushes from source via `course_mirror.py` |
| `BLUEPRINT_COURSE_ID` | [your ID] | Canvas Blueprint — synced from master; new semester sections cloned from this |

Source → Master → Blueprint is the content flow. Never reverse this direction. If you only have one course, set only `CANVAS_COURSE_ID` and ignore the master/blueprint tools.

## Folder Structure

```
agents/                              ← agent guides, configs, knowledge, templates
  canvas_course_expert.md/.json      ← audit + change agent (7-framework instructional design stack)
  canvas_content_sync.md/.json       ← content push agent
  canvas_blueprint_sync.md/.json     ← blueprint sync agent
  canvas_schedule_auditor.md/.json   ← rule-based date audit agent
  canvas_semester_setup.md/.json     ← semester due date rollout agent
  canvas_new_course_setup.md         ← step-by-step guide for first-time repo setup
  make_ai_agents/                    ← subtree from chaz-clark/Make-AI-Agents (canonical source for agent templates)
    make_agent.md/.json              ← template for creating new agents
    make_agent_qc.md/.json           ← quality control validator for new agents
    make_gems/                       ← upstream agent gem definitions
    source_docs/                     ← upstream source documents
    update_agents/                   ← upstream agent update workflows
  knowledge/                         ← instructional-design references (see knowledge/README.md)
    README.md                        ← routing guide — which framework for which audit question
    cognitive_load_theory_knowledge.md
    hattie_3phase_knowledge.md
    three_domains_knowledge.md
    taxonomy_explorer_knowledge.md
    experiential_learning_knowledge.md
    designer_thinking_knowledge.md
    course_design_language_knowledge.md
    toyota_gap_analysis_knowledge.md
  templates/                         ← reusable HTML/JSON artifacts (see templates/README.md)
    README.md                        ← pattern guide — when to use templates vs knowledge files
    byui_course_design/              ← 11 HTML components + canonical rubric JSON for BYUI courses
tools/                               ← Python CLI scripts (all use uv run python)
  canvas_sync.py                     ← source course mirror (init/status/push/pull)
  sync_context.sh                    ← multi-course wrapper — invokes canvas_sync.py per context (master/s1/s2/blueprint)
  blueprint_sync.py                  ← master → blueprint sync
  course_mirror.py                   ← source → master one-off mirror
  course_quality_check.py            ← duplicate/date/module/floating-item auditor
  canvas_quiz_questions.py           ← classic quiz question manager
  canvas_api_tool.py                 ← audit engine + Canvas write functions

# Single-course layout (legacy — works without any wrapper):
course/                              ← Canvas mirror (gitignored)
  syllabus.html
  _course.json
  [module-slug]/
    _module.json
    *.html / *.json                  ← pages (html) and assignment/quiz metadata (json)
    *.questions.json                 ← classic quiz questions
.canvas/                             ← runtime index files (gitignored)

# Multi-course layout (when using tools/sync_context.sh):
master/                              ← master template working dir
  course/                            ← Canvas mirror for the master
  course_src/
  .canvas/index.json
blueprint/                           ← blueprint working dir (online programs only)
  course/
  .canvas/index.json
s1/                                  ← section 1 working dir
  course/
  .canvas/index.json
s2/                                  ← section 2 working dir (optional, for multi-section semesters)
  course/
  .canvas/index.json

quality_report.md                    ← combined quality report (gitignored, regenerated on demand)
AGENTS.md                            ← this file
CLAUDE.md                            ← optional, gitignored — personal Claude Code notes
```

## Setup

See `agents/canvas_new_course_setup.md` for a full walkthrough. Quick path:

```bash
uv sync
cp .env.example .env
# Edit .env — add CANVAS_API_TOKEN, CANVAS_BASE_URL, CANVAS_COURSE_ID,
#              MASTER_COURSE_ID, BLUEPRINT_COURSE_ID, S1_COURSE_ID (if using sections)

uv run python tools/canvas_sync.py --init           # pull source course into course/
uv run python tools/blueprint_sync.py --pull        # mirror blueprint + build mapping (if using)
uv run python tools/course_mirror.py --pull         # map master item IDs (if using)
```

## Multi-course architecture

A typical course has multiple Canvas instances tied to one shared design:

- **Master** (always 1) — template course where authoring happens
- **Blueprint** (optional, online programs only) — Canvas Blueprint that semester sections clone from
- **S1, S2, S3, ...** (per semester, typically 2–3) — live student sections

`canvas_sync.py` itself is single-course — it reads `CANVAS_COURSE_ID` from `.env`, mirrors to `course/`, writes `.canvas/index.json` (all CWD-relative). The orchestration of "which course am I working on right now" lives one layer up, in [`tools/sync_context.sh`](tools/sync_context.sh).

### How `sync_context.sh` works

The wrapper does three things:

1. Reads `.env` to find the course ID for the requested context
2. Creates and `cd`s into a context folder (`master/`, `s1/`, etc.)
3. Invokes `canvas_sync.py` from that folder with `CANVAS_COURSE_ID` set

Because every per-course path in `canvas_sync.py` is CWD-relative, each context lands in its own isolated tree:

```
master/course/                  master/.canvas/index.json
s1/course/                      s1/.canvas/index.json
s2/course/                      s2/.canvas/index.json
```

Zero changes were needed to `canvas_sync.py` to support this — the script never knows it's running in a "context", and the wrapper doesn't need to understand sync internals. Clean separation.

### .env mapping

| Context | .env variable | Folder |
|---|---|---|
| `master` | `MASTER_COURSE_ID` | `master/` |
| `blueprint` | `BLUEPRINT_COURSE_ID` | `blueprint/` |
| `s1` | `S1_COURSE_ID` | `s1/` |
| `s2` | `S2_COURSE_ID` | `s2/` |
| `s3` | `S3_COURSE_ID` | `s3/` |

Add additional sections by adding `S<N>_COURSE_ID` to `.env` — the wrapper resolves any `s<N>` context up to `s99`.

### Usage

```bash
tools/sync_context.sh master --pull              # pull master into master/course/
tools/sync_context.sh master --status            # status for master
tools/sync_context.sh s1 --pull                  # pull section 1
tools/sync_context.sh s2 --push "sprint-1"       # push one module of section 2
tools/sync_context.sh blueprint --pull           # pull blueprint
tools/sync_context.sh master --build             # build markdown → HTML for master
```

Single-course users without sections can keep using `tools/canvas_sync.py` directly with `course/` at repo root — the wrapper is opt-in.

### Migration from single-course to multi-course

If you have an existing setup with `course/` and `.canvas/index.json` at repo root and want to add sections:

```bash
# Move existing single-course mirror under master/
mkdir -p master
mv course master/course
mv course_src master/course_src 2>/dev/null || true
mv .canvas master/.canvas

# Verify nothing broke
tools/sync_context.sh master --status

# Now add sections via .env (S1_COURSE_ID=…) and pull them
tools/sync_context.sh s1 --pull
```

**API token**: Canvas → Account → Settings → Approved Integrations → New Access Token. Requires instructor or admin role on all courses you plan to write to.

## Commands

```bash
# Source course (CANVAS_COURSE_ID)
uv run python tools/canvas_sync.py --pull                        # Canvas → course/
uv run python tools/canvas_sync.py --pull --quiet                # suppress per-file output
uv run python tools/canvas_sync.py --status                      # show local changes not yet pushed
uv run python tools/canvas_sync.py --push                        # push all changes to Canvas
uv run python tools/canvas_sync.py --push "[module-slug]"        # push one module only
uv run python tools/canvas_sync.py --push syllabus               # push syllabus only

# Blueprint (master → BLUEPRINT_COURSE_ID)
uv run python tools/blueprint_sync.py --pull                     # full init + build mapping
uv run python tools/blueprint_sync.py --push                     # sync master → blueprint
uv run python tools/blueprint_sync.py --status                   # mapping + date coverage

# Master (source → MASTER_COURSE_ID)
uv run python tools/course_mirror.py --pull                      # map master item IDs
uv run python tools/course_mirror.py --push                      # push course/ → master

# Quality check — run after every push
uv run python tools/course_quality_check.py                      # check source course
uv run python tools/course_quality_check.py --master             # check master
uv run python tools/course_quality_check.py --blueprint          # check blueprint
uv run python tools/course_quality_check.py --all                # all three → quality_report.md
uv run python tools/course_quality_check.py --all --fix          # auto-fix duplicates

# Classic quiz questions
uv run python tools/canvas_quiz_questions.py --push <file.questions.json>   # idempotent
uv run python tools/canvas_quiz_questions.py --list <file.questions.json>
uv run python tools/canvas_quiz_questions.py --clear <file.questions.json>

# Smoke test (no credentials needed)
uv run python tools/canvas_api_tool.py --test
```

## Agents

Each agent in `agents/` is a pair of files: a `.md` guide (mission, principles, pitfalls) and a `.json` (structured data, API patterns, mappings). Load both when invoking the agent.

| Agent | Purpose |
|---|---|
| `canvas_course_expert` | Audit course content against the 8-framework instructional-design stack (CLT, Hattie, Three Domains, Taxonomy Explorer, Experiential Learning, Designer Thinking, Course Design Language, Toyota A3) |
| `canvas_content_sync` | Push page/assignment content changes to Canvas |
| `canvas_blueprint_sync` | Sync master → blueprint including dates, completion requirements, prerequisites |
| `canvas_schedule_auditor` | Rule-based date audit — propose-before-execute, with institution-aware rules |
| `canvas_semester_setup` | Roll due dates forward for a new semester given a Week 1 start date |
| `canvas_new_course_setup` | First-time setup walkthrough for a new course fork |
| `make_agent` | Template for creating new agents in this system (lives in `agents/make_ai_agents/` subtree) |
| `make_agent_qc` | Validate a new agent against make_agent standards (lives in `agents/make_ai_agents/` subtree) |

For framework theory and the routing rules between them, see [`agents/knowledge/README.md`](agents/knowledge/README.md).

For the agent-engineering taxonomy that distinguishes runtime, capability, and specification layers — and the AI engineering practices for each — see [`agents/AGENT_LAYERS.md`](agents/AGENT_LAYERS.md).

## Sync Limitations

**This is not git.** No commit history, no branching, no conflict detection.

- Local edits → Canvas: `--status` → `--push` → `--pull --quiet`
- Canvas-side edit → local: `--pull` (answer `y` to accept Canvas, discard local)
- **NewQuiz/ExternalTool** items cannot be pushed via REST API — manage in Canvas UI. The sync scripts warn when a module contains only these types (the module shell syncs but lands empty).

## Critical Invariants

1. **Edit `course/` locally first.** Canvas is the sync target, not the source.
2. **Canvas IDs are course-specific.** The same assignment has a different ID in every course and cloned section. Match content across courses by title, never by ID.
3. **Adding content requires two steps: course + module.** An assignment/quiz/page not linked as a module item is invisible to students. Run `course_quality_check.py` after every push.
4. **Completion requirements enable the prerequisite chain.** Every item in every locked module must have `must_submit` (assignments/quizzes) or `must_view` (pages/tools) set, or the module lock silently stops enforcing.
5. **Confirm scope before any write.** Always verify the target course ID before pushing. Master, blueprint, and source are different courses with different IDs.
6. **`request_confirmation()` must return `approved=true` before any Canvas write.** All audit agents enforce this for any create/update/delete operation.

## Canvas API Gotchas

- **Module prerequisites**: form-encoded `data={"module[prerequisite_module_ids][]": id}` — JSON payload returns 200 but silently does nothing
- **Module published state**: `data={"module[workflow_state]": "active"|"unpublished"}` (form-encoded)
- **Semester due date updates**: always send `lock_at: null, unlock_at: null` alongside `due_at` — reading quizzes retain prior-semester availability windows that cause 400 errors if not cleared
- **late_policy PATCH**: 403 for instructor tokens — set manually in Canvas Settings → Gradebook or use admin token
- **Classic quiz points**: may show 0 after question push — fix with `PUT /quizzes/:id {"quiz": {"points_possible": N}}`
- **Quiz IDs**: a classic quiz has both a `quiz_id` (used by module items) and an underlying `assignment_id` (used by `PUT /assignments/:id` for due dates)
- **Discussions use a different due date field**: `todo_date` in `PUT /discussion_topics/:id`, not `due_at`

## Quality Check Workflow

Run after every push to any course:

```bash
uv run python tools/course_quality_check.py --all
```

Report categories:
- **Auto-fixable** (`--fix`): duplicate assignment groups, assignments, quizzes, module items; orphaned duplicates
- **Manual review**: published items not in any module, empty modules, dates outside the course window, missing course dates

`quality_report.md` at repo root is the human-readable output. Per-course JSON in `.canvas/quality_report_*.json` is machine-readable for agents.

## Course-Specific Notes

<!-- Add per-institution notes here: module/sprint structure, grading model, competency thresholds, timezone, known Canvas quirks. Or create a personal CLAUDE.md (gitignored) and put them there. -->

---

## Roadmap

The following items are planned next for this toolkit. Snapshot of the agreed direction toward making canvas_toolbox installable as a cross-tool deployable skill across universities and AI tools.

1. **Convert `canvas_course_expert` → `.agents/skills/canvas-audit/`** — first deployable skill following the [Agent Skills](https://agentskills.io/specification) standard. Parameterize for non-BYUI institutions (institution name, course ID env vars, audit framework subset). Test discovery in Antigravity, VS Code Copilot, and Claude Code.
2. **Capture conversion pattern as `agents/deploy_agent.md`** — template for transforming a `make_agent`-produced spec into a `.agents/skills/<name>/` package. Sibling to `make_agent.md` (design-time) and `make_agent_qc.md` (validation).
3. **Convert `canvas_schedule_auditor` using the new template** — validates `deploy_agent.md` on a different agent shape. Confirms the template generalizes.
4. **Document per-tool quickstart in README** — "Using Claude Code? Just works. Antigravity? Just works. VS Code Copilot? Flip `chat.useAgentsMdFile: true` once. Cursor? Just works."
5. **When `toyota-way-agents` skill lands in the upstream `Make-AI-Agents` subtree, cite it from AGENTS.md** as the recommended companion to `make_agent` for non-technical users. The skill is designed and tracked upstream (not in this repo); this item is just the canvas_toolbox side of "consume it once it's there."

Vision: another university clones this repo, opens it in whatever AI coding tool they use, and the canvas-audit capability is auto-discovered by their AI — zero install friction beyond clone-and-open.
