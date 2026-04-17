"""
gh_close.py

Post a comment and close a GitHub issue. Moves the local file from
.github_issues/open/ to .github_issues/closed/.

Usage:
    uv run python gh_issues_agent/tools/gh_close.py --issue 42
    uv run python gh_issues_agent/tools/gh_close.py --issue 42 --comment "Fixed in commit abc123."

Env vars required:
    GH_TOKEN       GitHub personal access token (repo or public_repo scope)

Env vars optional:
    GITHUB_REPO    owner/repo — auto-detected from git remote if not set
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
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


def close_issue(repo, number, comment=None):
    base = f"{API_BASE}/repos/{repo}/issues/{number}"

    if comment:
        resp = requests.post(
            f"{base}/comments",
            headers=_headers(),
            json={"body": comment},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"  Comment posted to #{number}")

    resp = requests.patch(
        base,
        headers=_headers(),
        json={"state": "closed"},
        timeout=30,
    )
    resp.raise_for_status()
    print(f"  Issue #{number} closed on GitHub")

    CLOSED_DIR.mkdir(parents=True, exist_ok=True)
    moved = False
    for f in sorted(OPEN_DIR.glob(f"issue-{number:04d}-*.md")):
        dest = CLOSED_DIR / f.name
        shutil.move(str(f), str(dest))
        print(f"  Moved {f.name} -> closed/")
        moved = True

    if not moved:
        print(f"  Note: no local file found for #{number} in open/ — run gh_sync.py to refresh")


def main():
    parser = argparse.ArgumentParser(
        description="Close a GitHub issue and move its local file to closed/"
    )
    parser.add_argument("--issue", type=int, required=True, help="Issue number to close")
    parser.add_argument(
        "--comment", type=str, default=None,
        help="Comment to post before closing (include commit hash or PR reference)"
    )
    args = parser.parse_args()

    if not GH_TOKEN:
        print("ERROR: GH_TOKEN not set in .env")
        sys.exit(1)

    repo = GITHUB_REPO or _detect_repo()
    if not repo:
        print("ERROR: Could not detect repo. Set GITHUB_REPO=owner/repo in .env")
        sys.exit(1)

    print(f"Closing #{args.issue} on {repo}...")
    close_issue(repo, args.issue, args.comment)
    print("Done.")


if __name__ == "__main__":
    main()
