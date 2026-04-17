# DRAFT — Medium Article
# Sharing Agent Tools Across Projects Without Losing Your Mind

*Status: draft — convert to Medium post. References: canvas_toolbox and gh_issues_agent repos.*

---

## The Problem Every Agent Builder Hits

You build an agent workflow for one project. It works well — maybe better than you expected. You tweak it, fix a few things, add some knowledge files based on what you learned actually using it. Then you start a second project and realize you want the same agent there.

So you copy the folder over. Now you have two copies. You improve one. The other goes stale. You merge some changes manually. Something breaks. You lose track of which version has which fix.

This is the **agent reuse problem**, and it hits differently than normal code reuse because of one constraint that most solutions ignore: **agents need to read your files to reason about your project**. They can't work from an installed package. They can't navigate into a nested submodule in a detached HEAD state. They need flat, readable files in the working tree.

This article is about the pattern I landed on: git subtree with a fork-based PR contribution model. It keeps shared agent tooling in one upstream repo, lets each project pull improvements, and gives you a review gate to keep project-specific knowledge from contaminating the shared tools.

---

## Why the Standard Solutions Don't Quite Work

### Git submodules — the classic wrong answer for agents

Submodules are the first thing developers reach for when they want to link one repo inside another. They technically work — but they're hostile to agents.

When you add a submodule, the files live in a nested git repo with its own HEAD state. Updating requires `git submodule update --remote`. The files don't show up as normal tracked files in your project. An agent scanning your working tree can see the folder but not always the contents cleanly.

More practically: submodules have a reputation for biting developers who forget to initialize them or who make changes in the submodule without pushing. That friction is even worse when an agent is doing the driving.

### Installing as a package — too opaque

You could turn your agent tools into a pip package and install it. Clean dependency management, versioned releases, the whole thing. But now the agent config files live in `site-packages`, not in your project tree. An agent helping you work on the project can't read the tools it's supposed to use. The configuration that makes the agent smart is hidden from the agent.

### Just copying the files — honest but brittle

The most common real-world solution: copy the files into each project, and occasionally manually sync updates. This works better than you'd expect because the shared tools tend to be small and stable. But it scales poorly once you have more than two or three projects, and it has no mechanism to contribute improvements back.

---

## The Pattern That Actually Works: Subtree + Fork PR

Git subtree gives you the best of both worlds: the shared files live in your project tree as normal files (agents can read them), but they're linked to an upstream repo you can sync with one command.

Here's the setup:

```bash
# One-time: add the upstream agent repo and your fork as named remotes
git remote add gh-agent-upstream https://github.com/you/gh_issues_agent.git
git remote add gh-agent-fork https://github.com/you/gh_issues_agent_fork.git

# Wire the subtree into your project
git subtree add --prefix gh_issues_agent gh-agent-upstream main --squash
```

After this, `gh_issues_agent/` appears in your project as ordinary files. Your agent can read them. You can edit them. Git tracks them normally.

Pulling improvements from upstream when the agent repo gets better:
```bash
git subtree pull --prefix gh_issues_agent gh-agent-upstream main --squash
```

Contributing improvements back upstream:
```bash
git subtree push --prefix gh_issues_agent gh-agent-fork contribute/improve-sync-script
# Then open a PR: your fork → upstream main
```

That last step — the PR — is where the magic is.

---

## The Fork PR as a Quality Gate

Here's the insight that makes this work long-term: **agent tools get better in the context of real projects, not when they're first written**.

You discover what's missing when you use the tools. You add a field you didn't know you needed. You fix an edge case that only shows up on real data. You add a knowledge file based on something that burned you.

But not all of those improvements belong in the shared upstream repo. Some of them are specific to your project — your course IDs, your sprint plan, your domain gotchas. The PR review is how you separate the two.

When you open a PR from your fork to the upstream agent repo, the review asks one question: *is this a genuine improvement to the shared tool, or is it a project-specific detail that snuck into the wrong file?*

A simple checklist on the upstream PR template handles this:
- No hardcoded IDs, URLs, or credentials
- No project-specific domain knowledge in shared files  
- Knowledge file changes are generic principles, not project rules

Git's subtree push helps automatically: it replays your project history and extracts **only commits that touched files under the `gh_issues_agent/` prefix**, rewriting them as if they lived at the repo root. Your canvas_toolbox course work, your sprint QC notes, your project-specific commits — none of them appear. The commit filter is structural. The PR review catches content leaks.

---

## The Flywheel

Once this is set up across two or three projects, something nice happens.

You use the agent on a real project and discover it handles a case poorly. You improve the tool while you're working — in context, with real data, motivated by a real need. You push the improvement upstream via your fork. All your other projects get it on the next `subtree pull`.

The projects improve the shared tools. The shared tools improve the projects. Each iteration happens in the context that exposes what actually needs fixing, not in the abstract when the tool was first written.

This is close to how good open source tool development works. It's also how experienced developers think about internal shared libraries. The new part is applying this pattern to agent tooling specifically — where the tools are small Python scripts and markdown knowledge files rather than compiled packages.

---

## The Project-Specific Knowledge Boundary

The other half of making this work is being deliberate about what *doesn't* go upstream.

Every project using a shared agent will have its own:
- **Sprint or task tracking** — what's in progress, what's done, what's next
- **Domain-specific knowledge** — API gotchas, data model quirks, integration notes
- **QC runbooks** — how to validate that a fix actually works in this project's environment
- **Mission and priorities** — what this project is trying to accomplish and in what order

These live in the project's own `knowledge/` folder inside the agent directory. They're excluded from subtree pushes by their location. They don't travel upstream. They're exactly as they should be: local expertise about a specific project.

The shared upstream repo gets the generic tools, the agent configuration structure, and the general principles. The project gets the context that makes those tools useful for this specific domain.

---

## Practical Setup in Two Projects

To make this concrete: this pattern came out of building [canvas_toolbox](link), a toolkit for managing Canvas LMS courses as code. The agent workflow — syncing GitHub issues, triaging by sprint, closing with commit references — is handled by a tool called [gh_issues_agent](link).

`gh_issues_agent` started as a folder inside `canvas_toolbox`. Once the workflow was proven useful on that project, it made sense to extract it: the issue sync and close scripts are completely generic. Any GitHub project could use them.

The project-specific pieces stayed behind in `canvas_toolbox`:
- `agile_sprint.md` — the sprint plan for canvas_toolbox specifically
- `sprint_qc.md` — how to QC canvas_toolbox fixes against a sandbox Canvas course
- `canvas_api_gotchas.md` — hard-learned Canvas API quirks specific to this domain

The shared pieces moved to the upstream `gh_issues_agent` repo:
- `gh_sync.py` and `gh_close.py` — the actual sync and close scripts
- `gh_issues_agent.md` and `gh_issues_agent.json` — the agent configuration and workflow definition
- `gh_issues_agent_mission.md` — the generic issue triage philosophy
- `semantic_versioning.md` — versioning rules that apply to any project

Any project that wants this issue management workflow can add it with:
```bash
git subtree add --prefix gh_issues_agent https://github.com/you/gh_issues_agent.git main --squash
```

And contribute improvements back via fork PR.

---

## The Broader Takeaway

The pattern isn't really about git subtree specifically. It's about recognizing that agent workflows have a different reuse model than traditional code.

Traditional reuse: write once, package, install everywhere, update via version bumps.

Agent reuse: write in context, improve while using, share the generic parts, keep the specific parts local, iterate the shared tools from real project feedback.

The subtree + fork PR workflow is just one implementation of that model. The deeper principle is: **agents work on projects, not packages**. Keep their tools as readable source files in the working tree. Accept a small amount of structure in exchange for full transparency. Design the shared/local boundary deliberately.

The agent tooling ecosystem is new enough that best practices are still forming. But the projects that get this right early will be able to compound their agent improvements across every repo they work in, rather than reinventing the same workflows from scratch each time.

---

*Repos referenced in this article:*
- *[canvas_toolbox](link) — Canvas LMS course management toolkit*
- *[gh_issues_agent](link) — GitHub issues management agent (extracted from canvas_toolbox)*
