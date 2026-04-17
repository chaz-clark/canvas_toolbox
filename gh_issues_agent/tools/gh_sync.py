"""
gh_sync.py

Pull all open GitHub issues + comments into .github_issues/open/ as markdown files.
Moves files for issues no longer open to .github_issues/closed/.

Usage:
    uv run python gh_issues_agent/tools/gh_sync.py

Env vars required:
    GH_TOKEN       GitHub personal access token (repo or public_repo scope)

Env vars optional:
    GITHUB_REPO    owner/repo — auto-detected from git remote if not set
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

GH_TOKEN = os.environ.get("GH_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

OPEN_DIR = Path(".github_issues/open")
CLOSED_DIR = Path(".github_issues/closed")

API_BASE = "https://api.github.com"


def _headers():
    return {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_all_pages(url, params=None):
    params = dict(params or {})
    params["per_page"] = 100
    results = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results


def _detect_repo():
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        m = re.search(r"github\.com[:/](.+?/[^.]+?)(?:\.git)?$", url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def _format_date(iso):
    try:
        iso_clean = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso


def _render_issue(issue, comments):
    number = issue["number"]
    title = issue["title"]
    state = issue["state"]
    labels = [lb["name"] for lb in issue.get("labels", [])]
    created = issue.get("created_at", "")
    updated = issue.get("updated_at", "")
    author = issue.get("user", {}).get("login", "unknown")
    url = issue.get("html_url", "")
    body = (issue.get("body") or "").strip()

    lines = [
        "---",
        f"issue: {number}",
        f'title: "{title}"',
        f"state: {state}",
        f"labels: [{', '.join(labels)}]",
        f"created: {created}",
        f"updated: {updated}",
        f"author: {author}",
        f"url: {url}",
        "---",
        "",
        f"# #{number} — {title}",
        "",
        "## Description",
        "",
        body if body else "_No description provided._",
    ]

    if comments:
        lines += ["", "---", "", "## Comments", ""]
        for c in comments:
            commenter = c.get("user", {}).get("login", "unknown")
            date = _format_date(c.get("created_at", ""))
            comment_body = (c.get("body") or "").strip()
            lines += [
                f"### @{commenter} — {date}",
                "",
                comment_body if comment_body else "_Empty comment._",
                "",
            ]

    return "\n".join(lines) + "\n"


def _issue_filename(number, title):
    return f"issue-{number:04d}-{_slugify(title)}.md"


def sync(repo):
    OPEN_DIR.mkdir(parents=True, exist_ok=True)
    CLOSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Syncing issues from {repo}...")

    issues = _get_all_pages(f"{API_BASE}/repos/{repo}/issues", {"state": "open"})
    issues = [i for i in issues if "pull_request" not in i]
    print(f"  {len(issues)} open issue(s) found\n")

    current_numbers = set()

    for issue in issues:
        number = issue["number"]
        title = issue["title"]
        current_numbers.add(number)

        comments = []
        if issue.get("comments", 0) > 0:
            comments = _get_all_pages(
                f"{API_BASE}/repos/{repo}/issues/{number}/comments"
            )

        filename = _issue_filename(number, title)
        content = _render_issue(issue, comments)
        (OPEN_DIR / filename).write_text(content, encoding="utf-8")

        label_str = ", ".join(lb["name"] for lb in issue.get("labels", []))
        label_str = f" [{label_str}]" if label_str else ""
        print(f"  #{number}{label_str} {title}")

    # Move files for issues no longer open → closed/
    moved = 0
    for f in sorted(OPEN_DIR.glob("issue-*.md")):
        m = re.match(r"issue-(\d+)-", f.name)
        if m and int(m.group(1)) not in current_numbers:
            shutil.move(str(f), str(CLOSED_DIR / f.name))
            moved += 1
            print(f"  -> moved {f.name} to closed/")

    print(f"\nDone: {len(issues)} open, {moved} moved to closed/")


def main():
    if not GH_TOKEN:
        print("ERROR: GH_TOKEN not set in .env")
        sys.exit(1)

    repo = GITHUB_REPO or _detect_repo()
    if not repo:
        print("ERROR: Could not detect repo. Set GITHUB_REPO=owner/repo in .env")
        sys.exit(1)

    sync(repo)


if __name__ == "__main__":
    main()
