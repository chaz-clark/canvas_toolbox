# GitHub Issues Agent — How to Use

This agent manages GitHub issues for canvas_toolbox as a local, file-based workflow. No browser required — issues live in `.github_issues/` as readable markdown files with full comment history.

---

## Setup

Make sure `.env` has your GitHub token:
```
GH_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

Token scope needed: `public_repo` (this repo is public). Generate at:
GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → New token.

---

## Daily Workflow

### 1. Sync issues at the start of each session
```bash
uv run python gh_issues_agent/tools/gh_sync.py
```
Pulls all open issues + comments into `.github_issues/open/` as markdown files. Issues closed since your last sync are moved to `.github_issues/closed/` automatically.

### 2. Pick what to work on
```bash
ls .github_issues/open/
```
Open `gh_issues_agent/knowledge/agile_sprint.md` — find the active sprint and work the next `[ ]` issue in order. Read the full issue file (description + comments) before writing any code.

### 3. Fix it and commit
Reference the issue number in your commit message:
```bash
git commit -m "fix homepage false positive in orphaned_pages list

Closes #1"
```
GitHub will auto-close the issue when this is pushed if you use `Closes #N`, `Fixes #N`, or `Resolves #N` in the commit message or PR body.

### 4. Update the sprint
Open `gh_issues_agent/knowledge/agile_sprint.md` and mark the issue `[x]` with the commit hash. If all issues in the sprint are `[x]`, mark the sprint Complete and move it to the Completed Sprints section.

### 5. Close the issue explicitly (with context)
```bash
uv run python gh_issues_agent/tools/gh_close.py --issue 1 --comment "Fixed in commit abc123. Added homepage filter to cmd_init() orphan list."
```
This posts the comment to GitHub, closes the issue, and moves the local file from `open/` to `closed/`.

### 6. Re-sync to confirm and pick the next issue
```bash
uv run python gh_issues_agent/tools/gh_sync.py
```

---

## Using Claude Code as the Agent

Load the agent context before asking Claude to help with an issue:

1. Open the issue file: `.github_issues/open/issue-NNNN-slug.md`
2. Tell Claude: *"Read gh_issues_agent/gh_issues_agent.md and gh_issues_agent/gh_issues_agent.json, then help me work through issue #N."*
3. Claude will have the triage framework, label taxonomy, and close templates from the JSON — it knows what a good close comment looks like.

For triage across all open issues:

> *"Read gh_issues_agent/knowledge/gh_issues_agent_mission.md and all files in .github_issues/open/, then propose the next issue to work on and why."*

---

## Tool Reference

### gh_sync.py
```bash
uv run python gh_issues_agent/tools/gh_sync.py
```
- Pulls all open issues + comments from GitHub
- Writes `.github_issues/open/issue-NNNN-slug.md` for each
- Moves files for issues no longer open → `closed/`
- Auto-detects repo from git remote (or set `GITHUB_REPO=owner/repo` in `.env`)

### gh_close.py
```bash
uv run python gh_issues_agent/tools/gh_close.py --issue N
uv run python gh_issues_agent/tools/gh_close.py --issue N --comment "Fixed in commit abc123."
```
- Posts comment to issue (if `--comment` provided)
- Closes issue on GitHub
- Moves local file from `open/` to `closed/`

Always include `--comment` with a commit hash or description — it's the audit trail.

---

## Issue Triage Reference

See `gh_issues_agent/knowledge/gh_issues_agent_mission.md` for the full milestone plan. Quick version:

| Priority | Label / Type | Action |
|---|---|---|
| 1 | `bug` — mirror lies or push silently fails | Fix before anything else |
| 2 | `enhancement` — core workflow gap | Batch by affected tool |
| 3 | `documentation` | Quick win, one pass |
| 4 | `question` | Answer in comment, close |
| 5 | `duplicate` | Close with reference to canonical issue |

Current milestone order: **Trust the Mirror → Safe to Work In → Author Like a Human → Agents That Teach**

---

## File Structure

```
gh_issues_agent/
  README.md                          ← this file
  gh_issues_agent.md                        ← agent guide (mission, principles, pitfalls)
  gh_issues_agent.json                      ← structured data (label taxonomy, API patterns)
  knowledge/
    agile_sprint.md                  ← active sprint plan, updated as issues close
    gh_issues_agent_mission.md              ← living mission doc + milestone rationale
    github_issues_reference.md       ← GitHub API patterns and field reference
  tools/
    gh_sync.py                       ← sync open issues → .github_issues/open/
    gh_close.py                      ← close issue + move file to closed/

.github_issues/                      ← gitignored, local only
  open/                              ← one .md file per open issue
  closed/                            ← archived after resolution
```

---

## Troubleshooting

**gh_sync.py returns 401**
→ GH_TOKEN is missing, expired, or lacks `public_repo` scope. Regenerate.

**gh_sync.py returns 404**
→ Repo not detected correctly. Set `GITHUB_REPO=chaz-clark/canvas_toolbox` in `.env`.

**Issue file missing after sync**
→ The issue was closed on GitHub directly. Check `.github_issues/closed/`.

**gh_close.py returns 403**
→ Token doesn't have write access to issues. Needs `public_repo` scope minimum.

**PR files appearing in open/**
→ GitHub's issues endpoint returns PRs too. `gh_sync.py` filters them by checking for the `pull_request` key — if PRs are slipping through, the API response structure may have changed.
