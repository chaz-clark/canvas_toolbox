# Canvas Toolbox

A Canvas LMS course management toolkit — mirrors live Canvas courses to local files, audits structure against an 8-framework instructional-design stack, and applies instructor-approved changes via the Canvas REST API.

## Project Purpose

**This is**:
- A toolkit for managing Canvas courses as code (mirror, edit, audit, push)
- An 8-framework instructional-design audit engine (Cognitive Load, Hattie 3-Phase, Three Domains, BYUI Taxonomy Explorer, Experiential Learning, Designer Thinking, Course Design Language, Toyota A3)
- A multi-course orchestration system (master + blueprint + per-section live courses)
- Tool-agnostic — works with any LLM coding tool that reads AGENTS.md
- Originally built for BYU-Idaho; designed to be institution-agnostic

**This is NOT**:
- A Canvas replacement or LMS
- A student-facing tool
- A version-control system for Canvas content (no commit history, no branching, no conflict detection)
- A NewQuiz or ExternalTool editor (Canvas REST API limitation)

**Audience**: Instructors and instructional designers who edit Canvas courses, want auditable structure, and use LLM coding tools for course design work.

## Structure

```
canvas_toolbox/
├── agents/                ← agent specs, knowledge references, templates
│   ├── canvas_*.md/.json
│   ├── knowledge/         ← instructional-design references (see knowledge/README.md)
│   ├── templates/         ← reusable HTML/JSON artifacts (see templates/README.md)
│   └── AGENT_LAYERS.md    ← runtime / capability / specification taxonomy
├── tools/                 ← Python CLI scripts (uv run python)
│   ├── canvas_sync.py
│   ├── sync_context.sh    ← multi-course wrapper
│   ├── blueprint_sync.py
│   ├── course_mirror.py
│   ├── course_quality_check.py
│   ├── canvas_quiz_questions.py
│   └── canvas_api_tool.py
├── tests/                 ← regression tests (pytest)
├── course_ref/            ← local-only artifacts safe from --pull (answer keys, drafts, setup notes)
├── course_src/            ← markdown authoring workspace (gitignored, --build compiles to course/)
├── make_ai_agents/        ← upstream subtree (gitignored, separate tool)
├── gh_issues_agent/       ← upstream subtree (gitignored, separate tool)
├── master/                ← master course working dir (gitignored, multi-course mode)
├── s1/, s2/, s3/          ← per-section working dirs (gitignored)
├── course/                ← legacy single-course mirror (gitignored)
├── .canvas/               ← runtime indexes and logs (gitignored)
├── AGENTS.md              ← this file
└── README.md              ← user-facing documentation and command reference
```

For full setup and command reference, see [`README.md`](README.md). For agent-engineering taxonomy (Runtime / Capability / Specification / Tool layers), see [`agents/AGENT_LAYERS.md`](agents/AGENT_LAYERS.md).

## Working Style

This project follows the behavioral discipline defined in `make_ai_agents/knowledge/behavioral_discipline.md` (when the upstream `Make-AI-Agents` subtree is populated locally — see Existing Tooling) or the equivalent discipline loaded via the host tool's skill system.

In short, every contributor — human or LLM — operates under these principles: read before claiming, plan before acting on changes, stop on the first defect rather than papering over, find root causes for bugs, document non-trivial changes in a structured form, generate exactly what was asked (no speculative additions), produce mistake-proof outputs, reflect and tell the user about non-obvious learnings, and respect the user's intent without substitution or drift.

For the full principles and override rules, see `knowledge/behavioral_discipline.md` → "The Ten Principles". The four no-override principles (P-001 Read Before Claiming, P-003 Stop on Defect, P-007 Pull Don't Push, P-010 Respect Intent) apply unconditionally.

**Project-specific rules**:
- **Local files are source of truth.** Canvas is the sync target, not the source. Never treat Canvas as authoritative unless `--pull` was just run.
- **Canvas IDs are course-specific.** Match content across courses by title, never by ID. The same assignment has different IDs in master, blueprint, and every section.
- **Adding content requires two steps: course + module.** Creating an assignment, quiz, or page is not enough — it must also be added as a module item, or students cannot find it.
- **Confirm scope before any write.** Master, blueprint, and sections are different courses with different IDs. A push scoped wrong replicates to the wrong course.
- **`request_confirmation()` must return `approved=true` before any Canvas write.** Audit agents enforce this; honor it manually too.
- **Run `course_quality_check.py` after every push** — surfaces orphaned items, duplicates, and dates outside the course window.
- **Completion requirements enable the prerequisite chain.** Sequential sprint locks silently fail if any item lacks `must_submit` (assignments, quizzes) or `must_view` (pages, tools, URLs).

## Active Context

_Last updated: 2026-04-30_

- **v0.5.0 just shipped** — Course Design Language as the 8th knowledge framework, with the `byui_course_design/` template-set (11 HTML components + canonical rubric JSON)
- **v0.4.0 multi-course orchestration** in production — `tools/sync_context.sh` invokes `canvas_sync.py` per context (master/blueprint/s1/s2/...). Tested against DS 250 (master + S1 + S2 + Blueprint).
- **Make-AI-Agents subtree** at `make_ai_agents/` is gitignored. Populate locally with the subtree-add command in Existing Tooling when needed.
- **Open canvas_toolbox issues**: [#16](https://github.com/chaz-clark/canvas_toolbox/issues/16) (file-aware pulling + fuzzy search), [#17](https://github.com/chaz-clark/canvas_toolbox/issues/17) (orphan/broken-reference audit), [#18](https://github.com/chaz-clark/canvas_toolbox/issues/18) (alignment-chain audit). All bigger features; no current pain.
- **Roadmap (canvas_toolbox)**: convert `canvas_course_expert` to deployable `.agents/skills/canvas-audit/` (first deployable skill, parameterize for non-BYUI institutions); capture conversion as `agents/deploy_agent.md`; convert `canvas_schedule_auditor` to validate the template; cite `toyota-way-agents` skill from AGENTS.md once it lands upstream and gets subtree'd.
- **Upstream-tracked work** lives in [`Make-AI-Agents`](https://github.com/chaz-clark/Make-AI-Agents) (separate repo, separate issue tracker). Toyota Way × AI agents skill design + subtree consumer hygiene live there.

Vision: another university clones this repo, opens it in any modern AI coding tool, and the canvas-audit capability is auto-discovered by their LLM — zero install friction beyond clone-and-open.

## Domain Terms

| Term | Definition |
|---|---|
| **Master** | The template course where authoring happens. One per course. Identified by `MASTER_COURSE_ID` in `.env`. Folder: `master/` (or `course/` in legacy single-course mode). |
| **Blueprint** | A Canvas Blueprint course that semester sections clone from. Optional — only used by online programs. Identified by `BLUEPRINT_COURSE_ID`. Folder: `blueprint/`. |
| **Section** | A live student-facing course for a specific semester (S1, S2, S3...). Cloned from blueprint or master. Identified by `S1_COURSE_ID`, `S2_COURSE_ID`, etc. Folders: `s1/`, `s2/`, `s3/`. |
| **Sprint module** | A weekly or bi-weekly module containing related content. Sequential by default; can have prerequisites that lock later sprints until prior items are completed. |
| **Module item** | An entry inside a module — Page, Assignment, Quiz, Discussion, ExternalTool, ExternalUrl, or SubHeader. Has its own `module_item_id` distinct from the underlying content's `canvas_id`. |
| **NewQuiz** | Canvas's newer quiz engine (LTI-based). Cannot be content-pushed via REST API — must be edited in Canvas UI. Distinct from Classic Quiz. |
| **Classic Quiz** | Canvas's original quiz engine. Has both a `quiz_id` (in `/quizzes`) and an underlying `assignment_id` (in `/assignments` with `submission_types: ["online_quiz"]`). REST API works fully. |
| **Source of truth** | The local working folder (`master/course/` in multi-course mode, `course/` in single-course). Canvas is the sync *target*. |

## External System Lessons

Canvas API has multiple non-obvious behaviors discovered through use. Each is a real footgun:

| Behavior | Why it matters | How to handle |
|---|---|---|
| Module prerequisites silently fail with JSON payload | Returns 200 OK but doesn't actually set the prerequisite | Always use form-encoded: `data={"module[prerequisite_module_ids][]": id}` |
| Module published state is form-encoded too | Same pattern as prerequisites | `data={"module[workflow_state]": "active"\|"unpublished"}` |
| Semester due-date updates fail without `lock_at: null` and `unlock_at: null` | Reading quizzes retain prior-semester availability windows; sending `due_at` alone causes 400 errors | Always send all three together when rolling forward dates |
| `late_policy` PATCH returns 403 for instructor tokens | Cannot set programmatically with most tokens | Set manually in Canvas Settings → Gradebook, or use admin token |
| Classic quiz `points_possible` may show 0 after question push | Canvas auto-calculates from questions but doesn't update the quiz object | Explicit `PUT /quizzes/:id {"quiz": {"points_possible": N}}` after question push |
| Classic quizzes have two IDs | Module items reference `quiz_id`; due dates use `assignment_id` | Quality check maps both to avoid false "not in module" positives |
| Discussions use `todo_date`, not `due_at` | Different field on `PUT /discussion_topics/:id` | Don't conflate with assignment / quiz date semantics |
| NewQuiz / ExternalTool items can't be content-pushed via REST | Module shell syncs but item body is empty in target | Sync scripts skip and warn; manage these in Canvas UI |
| `GET /courses/:id/rubrics` requires teacher token | Returns 403 with student token | Workaround: `GET /courses/:id/assignments/:id?include[]=rubric` works for student tokens too |
| Empty modules are a sync artifact | When all items in a module are NewQuiz / ExternalTool, the module shell syncs but lands empty | Sync scripts warn before; quality check flags after |

## Existing Tooling

Before generating new sync or audit code, check whether these already do what's needed:

| Tool | Purpose | When to use |
|---|---|---|
| `tools/canvas_sync.py` | Single-course mirror (pull, status, push, build, upload) | All single-course sync work |
| `tools/sync_context.sh <context>` | Multi-course wrapper — invokes `canvas_sync.py` for master / blueprint / s1 / s2 / ... | Anytime more than one course is in this repo |
| `tools/blueprint_sync.py` | Master → Blueprint sync (one-way overwrite, content + dates + completion requirements) | Online programs using Canvas Blueprint |
| `tools/course_mirror.py` | Source → Master one-off mirror | Manually replicating between two courses |
| `tools/course_quality_check.py` | Audit for duplicates, floating items, empty modules, dates outside the course window | After every push to any course |
| `tools/canvas_quiz_questions.py` | Classic quiz question manager (push, list, clear) | Editing quiz questions outside Canvas UI |
| `tools/canvas_api_tool.py` | Audit engine + Canvas write functions | Wrapped by audit agents; rarely invoked directly |
| `agents/canvas_course_expert` | 8-framework instructional-design audit | Conceptual / pedagogical audit |
| `agents/canvas_schedule_auditor` | Rule-based date audit (propose-before-execute) | Pre-semester or mid-semester date validation |
| `agents/canvas_blueprint_sync` / `canvas_content_sync` | Agent guides for sync workflows | Reference, not invoked directly |
| `agents/canvas_semester_setup` | Roll due dates forward for a new semester | Once per semester |
| `agents/canvas_new_course_setup` | First-time setup walkthrough | Once per new course adoption |

For framework theory (CLT / Hattie / etc.), see [`agents/knowledge/README.md`](agents/knowledge/README.md). For the agent abstraction taxonomy, see [`agents/AGENT_LAYERS.md`](agents/AGENT_LAYERS.md).

**Populating the gitignored upstream subtrees**:

```bash
# Make-AI-Agents (template generation skills: make_agent, make_AGENTS, make_gem)
git subtree add --prefix=make_ai_agents \
  https://github.com/chaz-clark/Make-AI-Agents.git main --squash

# gh_issues_agent (separate tool, populate similarly if needed)
```

After populating either subtree, edits flow upstream (edit at the source repo, not here). Future updates: `git subtree pull --prefix=<name> <url> main --squash`.
