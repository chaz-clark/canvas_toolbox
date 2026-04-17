# course_ref/

Safe zone for local-only course artifacts. Files here are never touched by `--pull`.

## What belongs here

- Answer keys and grading rubrics
- Draft prompts and assignment briefs before they go into Canvas
- Study materials and supplementary resources
- Export helpers, transformation scripts, reference documents
- Any file that supports course management but is not a Canvas content object

## What does NOT belong here

Canvas-backed content (pages, assignments, quizzes, discussions) belongs in `course/`.
Those files are the live mirror and get overwritten on every `--pull`.

## Safe zones summary

| Folder | Purpose | Safe from --pull? |
|---|---|---|
| `course/` | Canvas mirror — source of truth for live content | No — overwritten on pull |
| `course_ref/` | Local-only artifacts — never synced to Canvas | Yes — never touched |
| `course/*.questions.json` | Classic quiz push sources — local only | Yes — explicitly skipped |
