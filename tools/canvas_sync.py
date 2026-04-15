"""
canvas_sync.py

Local mirror of a Canvas course. Pulls instructor-authored content into a
folder structure, tracks content hashes, and pushes changes back to Canvas.

Source of truth: local files. Canvas is the delivery target.
Conflict rule: local always wins. If Canvas was edited directly, use --pull
(no path) to re-sync the full course, or --pull <path> for a single file.

Usage:
    uv run python canvas_sync.py --pull               # full course pull (alias for --init)
    uv run python canvas_sync.py --pull <path>        # re-pull one file from Canvas
    uv run python canvas_sync.py --push               # push all local changes to Canvas
    uv run python canvas_sync.py --push "sprint-1"    # push one module
    uv run python canvas_sync.py --status             # show local changes not yet pushed
    uv run python canvas_sync.py --init               # same as --pull (full course pull)

    Add --quiet to any command to suppress per-file output lines.

Folder structure:
    course/
      _course.json
      sprint-1-setup-dag-demo/
        _module.json          # module metadata: position, published, canvas_id, item order
        sprint-1-overview.html
        w01-reading-quiz-ch1.json
        w01-standup-report.json
      sprint-2-api-dag/
        _module.json
        ...
    .canvas/index.json        # canvas_ids, slugs, hashes — sync state

Item types pulled:
    Page        → .html  (body only, metadata in _module.json items list)
    Assignment  → .json  (description + points, due_at, submission_types)
    Discussion  → .json  (message + metadata)
    Quiz        → .json  (description + points_possible)
    ExternalTool, SubHeader, ExternalUrl → .json (metadata only, no editable body)

Items NOT pulled (Canvas-generated, not instructor-authored):
    Gradebook, submissions, enrollments, analytics, student data
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import requests

# Load .env from repo root if python-dotenv is available (optional dependency)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CANVAS_API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "")
_raw_url = os.environ.get("CANVAS_BASE_URL", "").strip().rstrip("/")
if _raw_url and not _raw_url.startswith("http"):
    _raw_url = "https://" + _raw_url
CANVAS_BASE_URL = _raw_url
CANVAS_COURSE_ID = os.environ.get("CANVAS_COURSE_ID", "")

QUIET = False  # set to True via --quiet flag; suppresses per-file output lines
PUSH_LOG = Path(".canvas/push_log.md")


def _vprint(*args, **kwargs):
    """Print only when not in quiet mode."""
    if not QUIET:
        print(*args, **kwargs)


def _log_push(summary: str, comment: str, files_pushed: list[str], direction: str = "push") -> None:
    """Append a commit-style entry to .canvas/push_log.md."""
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    PUSH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PUSH_LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n## [{direction.upper()}] {summary}\n")
        f.write(f"_{ts}_\n\n")
        if comment:
            f.write(f"{comment}\n\n")
        for fp in files_pushed:
            f.write(f"- {fp}\n")
        f.write("\n")

COURSE_DIR = Path("course")
INDEX_PATH = Path(".canvas/index.json")

# Item types with no editable body — store as metadata-only JSON
METADATA_ONLY_TYPES = {"ExternalTool", "ExternalUrl", "ContextModuleSubHeader"}


# ---------------------------------------------------------------------------
# Canvas API helpers
# ---------------------------------------------------------------------------

def _headers() -> dict:
    return {"Authorization": f"Bearer {CANVAS_API_TOKEN}", "Content-Type": "application/json"}


def _get(endpoint: str, params: Optional[dict] = None) -> list | dict:
    """GET with automatic pagination."""
    url = f"{CANVAS_BASE_URL}/api/v1{endpoint}"
    results = []
    while url:
        resp = requests.get(url, headers=_headers(), params=params, timeout=20)
        if resp.status_code >= 400:
            print(f"  ERROR {resp.status_code}: {resp.text[:200]}")
            return []
        data = resp.json()
        if isinstance(data, list):
            results.extend(data)
        else:
            return data  # single object
        # Follow Canvas pagination
        url = None
        link = resp.headers.get("Link", "")
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
        params = None  # params already in URL after first page
    return results


def _put(endpoint: str, payload: dict) -> dict:
    url = f"{CANVAS_BASE_URL}/api/v1{endpoint}"
    resp = requests.put(url, headers=_headers(), json=payload, timeout=20)
    if resp.status_code >= 400:
        return {"error": resp.text[:300], "status_code": resp.status_code}
    body = resp.json() if resp.text else {}
    return {"success": True, "status_code": resp.status_code, "id": body.get("id"), "url": body.get("url")}


def _post(endpoint: str, payload: dict) -> dict:
    url = f"{CANVAS_BASE_URL}/api/v1{endpoint}"
    resp = requests.post(url, headers=_headers(), json=payload, timeout=20)
    if resp.status_code >= 400:
        return {"error": resp.text[:300], "status_code": resp.status_code}
    body = resp.json() if resp.text else {}
    return {"success": True, "status_code": resp.status_code, "id": body.get("id"), "url": body.get("url")}


# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------

def _load_index() -> dict:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text())
    return {"course_id": CANVAS_COURSE_ID, "base_url": CANVAS_BASE_URL, "files": {}, "modules": []}


def _save_index(index: dict) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2, default=str))


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _slug(text: str) -> str:
    """Convert a title to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80]


# ---------------------------------------------------------------------------
# Pull: Canvas → local files
# ---------------------------------------------------------------------------

def _pull_page(course_id: str, page_url: str) -> Optional[str]:
    """Fetch page body HTML. Returns None on error."""
    data = _get(f"/courses/{course_id}/pages/{page_url}")
    if isinstance(data, list) or "body" not in data:
        return None
    return data.get("body", "")


def _pull_assignment(course_id: str, assignment_id: int) -> Optional[dict]:
    data = _get(f"/courses/{course_id}/assignments/{assignment_id}")
    if isinstance(data, list):
        return None
    return {
        "canvas_id": data.get("id"),
        "name": data.get("name"),
        "description": data.get("description", ""),
        "points_possible": data.get("points_possible"),
        "due_at": data.get("due_at"),
        "lock_at": data.get("lock_at"),
        "unlock_at": data.get("unlock_at"),
        "submission_types": data.get("submission_types", []),
        "published": data.get("published", False),
    }


def _pull_discussion(course_id: str, topic_id: int) -> Optional[dict]:
    data = _get(f"/courses/{course_id}/discussion_topics/{topic_id}")
    if isinstance(data, list):
        return None
    return {
        "canvas_id": data.get("id"),
        "title": data.get("title"),
        "message": data.get("message", ""),
        "due_at": data.get("assignment", {}).get("due_at") if data.get("assignment") else None,
        "lock_at": data.get("assignment", {}).get("lock_at") if data.get("assignment") else None,
        "unlock_at": data.get("assignment", {}).get("unlock_at") if data.get("assignment") else None,
        "published": data.get("published", False),
    }


def _pull_quiz(course_id: str, quiz_id: int) -> Optional[dict]:
    data = _get(f"/courses/{course_id}/quizzes/{quiz_id}")
    if isinstance(data, list):
        return None
    return {
        "canvas_id": data.get("id"),
        "title": data.get("title"),
        "description": data.get("description", ""),
        "points_possible": data.get("points_possible"),
        "quiz_type": data.get("quiz_type"),
        "due_at": data.get("due_at"),
        "lock_at": data.get("lock_at"),
        "unlock_at": data.get("unlock_at"),
        "published": data.get("published", False),
    }


def _check_env():
    """Fail fast if required env vars are missing."""
    missing = [v for v in ("CANVAS_API_TOKEN", "CANVAS_BASE_URL", "CANVAS_COURSE_ID") if not os.environ.get(v)]
    if missing:
        print(f"ERROR: Missing required .env variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in all three values.")
        sys.exit(1)


def cmd_init():
    """Pull the full course down into course/ folder."""
    _check_env()

    course_id = CANVAS_COURSE_ID

    # Warn if there are unsaved local changes — pull will overwrite them
    index_check = _load_index()
    _unsaved = []
    for fp, meta in index_check.get("files", {}).items():
        p = Path(fp)
        if p.exists() and _file_hash(p) != meta.get("hash"):
            _unsaved.append(fp)
    for key in ("homepage", "syllabus"):
        m = index_check.get(key)
        if m:
            p = Path(m["filepath"])
            if p.exists() and _file_hash(p) != m.get("hash"):
                _unsaved.append(m["filepath"])
    if _unsaved:
        print(f"WARNING: {len(_unsaved)} local file(s) have unpushed changes that will be overwritten:")
        for fp in _unsaved:
            print(f"  M  {fp}")
        print("\n  If YOUR local edits should win → abort and run --push first, then --pull.")
        print("  If CANVAS edits should win (you made changes in Canvas UI) → continue.")
        try:
            confirm = input("\nContinue pull and overwrite local changes? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm != "y":
            print("Pull aborted. Run --push first, then re-run --pull.")
            return

    print(f"Initializing course {course_id} from {CANVAS_BASE_URL}...\n")

    index = _load_index()
    # Snapshot existing hashes before overwriting — used to detect Canvas-side changes
    prior_hashes = {fp: meta.get("hash") for fp, meta in index.get("files", {}).items()}
    # Include homepage and syllabus in prior snapshot
    if index.get("homepage"):
        prior_hashes[index["homepage"]["filepath"]] = index["homepage"].get("hash")
    if index.get("syllabus"):
        prior_hashes[index["syllabus"]["filepath"]] = index["syllabus"].get("hash")
    index["files"] = index.get("files", {})
    index["modules"] = []  # rebuilt fresh each init

    # Course metadata + Syllabus
    course = _get(f"/courses/{course_id}?include[]=syllabus_body")
    COURSE_DIR.mkdir(exist_ok=True)

    # Late policy
    late_policy_resp = _get(f"/courses/{course_id}/late_policy")
    late_policy = late_policy_resp.get("late_policy", {}) if late_policy_resp else {}

    course_meta = {
        "canvas_id": course.get("id"),
        "name": course.get("name"),
        "course_code": course.get("course_code"),
        "workflow_state": course.get("workflow_state"),
        "grading_standard_id": course.get("grading_standard_id"),
        "start_at": course.get("start_at"),
        "end_at": course.get("end_at"),
        "late_policy": {
            "late_submission_deduction_enabled": late_policy.get("late_submission_deduction_enabled", False),
            "late_submission_deduction": late_policy.get("late_submission_deduction", 0.0),
            "late_submission_interval": late_policy.get("late_submission_interval", "day"),
            "late_submission_minimum_percent_enabled": late_policy.get("late_submission_minimum_percent_enabled", False),
            "late_submission_minimum_percent": late_policy.get("late_submission_minimum_percent", 0.0),
            "missing_submission_deduction_enabled": late_policy.get("missing_submission_deduction_enabled", False),
            "missing_submission_deduction": late_policy.get("missing_submission_deduction", 0.0),
        },
    }
    course_path = COURSE_DIR / "_course.json"
    course_path.write_text(json.dumps(course_meta, indent=2))
    index["course"] = course_meta  # summary in index for agent lookup
    index["course_hash"] = _file_hash(course_path)
    print(f"Course: {course.get('name')}")

    # Homepage (Canvas front_page — not a module item)
    homepage = _get(f"/courses/{course_id}/front_page")
    if homepage and not homepage.get("errors"):
        homepage_body = homepage.get("body", "")
        homepage_url = homepage.get("url", "front-page")
        homepage_path = COURSE_DIR / "homepage.html"
        homepage_path.write_text(homepage_body, encoding="utf-8")
        h_hp = _file_hash(homepage_path)
        index["homepage"] = {
            "filepath": str(homepage_path),
            "page_url": homepage_url,
            "title": homepage.get("title", ""),
            "hash": h_hp,
        }
        _vprint(f"  [homepage] homepage.html ({len(homepage_body)} chars)")

    # Syllabus (Canvas left-sidebar Syllabus tab — not a module item)
    syllabus_body = course.get("syllabus_body", "")
    syllabus_path = COURSE_DIR / "syllabus.html"
    syllabus_path.write_text(syllabus_body, encoding="utf-8")
    h = _file_hash(syllabus_path)
    index["syllabus"] = {
        "type": "Syllabus",
        "filepath": str(syllabus_path),
        "hash": h,
        "note": "Push via PUT /courses/:id with course[syllabus_body]. Not a module item.",
    }
    _vprint(f"  [syllabus] syllabus.html ({len(syllabus_body)} chars)")

    # Modules
    modules = _get(f"/courses/{course_id}/modules", params={"per_page": 50, "include[]": "items"})
    print(f"Pulling {len(modules)} modules...")

    for mod in modules:
        mod_title = mod.get("name", f"module-{mod['id']}")
        mod_slug = _slug(mod_title)
        mod_dir = COURSE_DIR / mod_slug
        mod_dir.mkdir(exist_ok=True)

        _vprint(f"  [{'+' if mod.get('published') else ' '}] {mod_title}")

        # Index entry for this module (structured view for agent)
        mod_index_entry = {
            "canvas_id": mod.get("id"),
            "title": mod_title,
            "slug": mod_slug,
            "position": mod.get("position"),
            "published": mod.get("published", False),
            "items": [],
        }

        items_meta = []
        for item in mod.get("items", []):
            item_type = item.get("type", "")
            item_title = item.get("title", "unknown")
            item_canvas_id = item.get("id")  # module item id
            content_id = item.get("content_id")
            page_url = item.get("page_url")
            item_slug = _slug(item_title)
            published = item.get("published", False)

            item_record = {
                "module_item_id": item_canvas_id,
                "content_id": content_id,
                "type": item_type,
                "title": item_title,
                "position": item.get("position"),
                "published": published,
                "filename": None,
            }

            filepath = None  # resolved below per type
            _item_dates = {}  # due_at, lock_at, unlock_at — populated per type below

            if item_type == "Page" and page_url:
                filename = f"{item_slug}.html"
                filepath = mod_dir / filename
                body = _pull_page(course_id, page_url)
                if body is not None:
                    filepath.write_text(body, encoding="utf-8")
                    item_record["filename"] = filename
                    item_record["page_url"] = page_url
                    h = _file_hash(filepath)
                    index["files"][str(filepath)] = {
                        "canvas_id": content_id,
                        "type": "Page",
                        "title": item_title,
                        "page_url": page_url,
                        "module_item_id": item_canvas_id,
                        "module_slug": mod_slug,
                        "module_canvas_id": mod.get("id"),
                        "hash": h,
                        "published": published,
                    }
                    _vprint(f"      [page] {filename}")

            elif item_type == "Assignment" and content_id:
                filename = f"{item_slug}.json"
                filepath = mod_dir / filename
                data = _pull_assignment(course_id, content_id)
                if data:
                    filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                    item_record["filename"] = filename
                    h = _file_hash(filepath)
                    # Distinguish New Quizzes (external_tool) from plain assignments
                    sub_types = data.get("submission_types", [])
                    entry_type = "NewQuiz" if sub_types == ["external_tool"] else "Assignment"
                    _item_dates = {
                        "due_at": data.get("due_at"),
                        "lock_at": data.get("lock_at"),
                        "unlock_at": data.get("unlock_at"),
                    }
                    index["files"][str(filepath)] = {
                        "canvas_id": content_id,
                        "type": entry_type,
                        "title": item_title,
                        "module_item_id": item_canvas_id,
                        "module_slug": mod_slug,
                        "module_canvas_id": mod.get("id"),
                        "hash": h,
                        "published": published,
                    }
                    _vprint(f"      [{entry_type.lower()}] {filename}")

            elif item_type == "Discussion" and content_id:
                filename = f"{item_slug}.json"
                filepath = mod_dir / filename
                data = _pull_discussion(course_id, content_id)
                if data:
                    filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                    item_record["filename"] = filename
                    h = _file_hash(filepath)
                    _item_dates = {
                        "due_at": data.get("assignment", {}).get("due_at") if isinstance(data.get("assignment"), dict) else None,
                        "lock_at": data.get("assignment", {}).get("lock_at") if isinstance(data.get("assignment"), dict) else None,
                        "unlock_at": data.get("assignment", {}).get("unlock_at") if isinstance(data.get("assignment"), dict) else None,
                    }
                    index["files"][str(filepath)] = {
                        "canvas_id": content_id,
                        "type": "Discussion",
                        "title": item_title,
                        "module_item_id": item_canvas_id,
                        "module_slug": mod_slug,
                        "module_canvas_id": mod.get("id"),
                        "hash": h,
                        "published": published,
                    }
                    _vprint(f"      [discussion] {filename}")

            elif item_type == "Quiz" and content_id:
                filename = f"{item_slug}.json"
                filepath = mod_dir / filename
                data = _pull_quiz(course_id, content_id)
                if data:
                    filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                    item_record["filename"] = filename
                    h = _file_hash(filepath)
                    _item_dates = {
                        "due_at": data.get("due_at"),
                        "lock_at": data.get("lock_at"),
                        "unlock_at": data.get("unlock_at"),
                    }
                    index["files"][str(filepath)] = {
                        "canvas_id": content_id,
                        "type": "Quiz",
                        "title": item_title,
                        "module_item_id": item_canvas_id,
                        "module_slug": mod_slug,
                        "module_canvas_id": mod.get("id"),
                        "hash": h,
                        "published": published,
                    }
                    _vprint(f"      [quiz] {filename}")

            elif item_type in METADATA_ONLY_TYPES:
                filename = f"{item_slug}.json"
                filepath = mod_dir / filename
                meta = {
                    "canvas_id": item_canvas_id,
                    "type": item_type,
                    "title": item_title,
                    "external_url": item.get("external_url"),
                    "published": published,
                }
                filepath.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                item_record["filename"] = filename
                _vprint(f"      [meta] {filename}")

            items_meta.append(item_record)

            # Add to structured module index for agent lookup
            mod_index_entry["items"].append({
                "module_item_id": item_canvas_id,
                "canvas_id": content_id,
                "type": item_type,
                "title": item_title,
                "position": item.get("position"),
                "published": published,
                "filepath": str(mod_dir / item_record["filename"]) if item_record.get("filename") else None,
                **_item_dates,
            })

        # Write _module.json
        module_json = {
            "canvas_id": mod.get("id"),
            "title": mod_title,
            "position": mod.get("position"),
            "published": mod.get("published", False),
            "items": items_meta,
        }
        (mod_dir / "_module.json").write_text(json.dumps(module_json, indent=2), encoding="utf-8")
        index["modules"].append(mod_index_entry)

    # -----------------------------------------------------------------------
    # Assignment Groups (grading weight structure)
    # -----------------------------------------------------------------------
    print("\nPulling assignment groups...")
    ag_data = _get(f"/courses/{course_id}/assignment_groups", params={"include[]": ["assignments"]})
    index["assignment_groups"] = [
        {
            "canvas_id": ag.get("id"),
            "name": ag.get("name"),
            "group_weight": ag.get("group_weight"),
            "assignments": [
                {
                    "canvas_id": a.get("id"),
                    "name": a.get("name"),
                    "points_possible": a.get("points_possible"),
                    "published": a.get("published"),
                    "due_at": a.get("due_at"),
                }
                for a in ag.get("assignments", [])
            ],
        }
        for ag in ag_data
    ]
    print(f"  {len(index['assignment_groups'])} assignment groups")

    # -----------------------------------------------------------------------
    # Course settings (homepage, nav)
    # -----------------------------------------------------------------------
    print("Pulling course settings...")
    settings = _get(f"/courses/{course_id}/settings")
    nav_tabs = _get(f"/courses/{course_id}/tabs")
    index["course"]["default_view"] = course.get("default_view")
    index["course"]["settings"] = settings if isinstance(settings, dict) else {}
    index["course"]["nav_tabs"] = [
        {"id": t.get("id"), "label": t.get("label"), "hidden": t.get("hidden", False)}
        for t in (nav_tabs if isinstance(nav_tabs, list) else [])
    ]
    print(f"  {len(index['course'].get('nav_tabs', []))} nav tabs")

    # -----------------------------------------------------------------------
    # Orphaned pages (published to course but not in any module)
    # -----------------------------------------------------------------------
    print("Pulling all pages to find orphans...")
    all_pages = _get(f"/courses/{course_id}/pages", params={"per_page": 50})
    linked_page_urls = {
        meta.get("page_url")
        for meta in index["files"].values()
        if meta.get("type") == "Page" and meta.get("page_url")
    }
    orphans = [
        {
            "canvas_id": p.get("page_id") or p.get("url"),
            "title": p.get("title"),
            "page_url": p.get("url"),
            "published": p.get("published", False),
            "updated_at": p.get("updated_at"),
        }
        for p in (all_pages if isinstance(all_pages, list) else [])
        if p.get("url") not in linked_page_urls
    ]
    index["orphaned_pages"] = orphans
    print(f"  {len(orphans)} orphaned pages (not linked in any module)")

    # -----------------------------------------------------------------------
    # Announcements
    # -----------------------------------------------------------------------
    print("Pulling announcements...")
    announcements = _get(f"/courses/{course_id}/discussion_topics", params={"only_announcements": True, "per_page": 50})
    index["announcements"] = [
        {
            "canvas_id": a.get("id"),
            "title": a.get("title"),
            "posted_at": a.get("posted_at"),
            "published": a.get("published", False),
            "message_preview": (a.get("message") or "")[:200],
        }
        for a in (announcements if isinstance(announcements, list) else [])
    ]
    print(f"  {len(index['announcements'])} announcements")

    # -----------------------------------------------------------------------
    # Gradebook columns (custom columns only — not assignment-based columns)
    # -----------------------------------------------------------------------
    print("Pulling gradebook custom columns...")
    gb_columns = _get(f"/courses/{course_id}/custom_gradebook_columns", params={"per_page": 50})
    index["gradebook_columns"] = [
        {
            "canvas_id": col.get("id"),
            "title": col.get("title"),
            "position": col.get("position"),
            "hidden": col.get("hidden", False),
            "teacher_notes": col.get("teacher_notes", False),
        }
        for col in (gb_columns if isinstance(gb_columns, list) else [])
    ]
    print(f"  {len(index['gradebook_columns'])} custom gradebook columns")

    # -----------------------------------------------------------------------
    # Groups / Group Sets
    # -----------------------------------------------------------------------
    print("Pulling group categories (group sets)...")
    group_categories = _get(f"/courses/{course_id}/group_categories", params={"per_page": 50})
    group_sets = []
    for cat in (group_categories if isinstance(group_categories, list) else []):
        cat_id = cat.get("id")
        groups = _get(f"/group_categories/{cat_id}/groups", params={"per_page": 50})
        group_sets.append({
            "canvas_id": cat_id,
            "name": cat.get("name"),
            "self_signup": cat.get("self_signup"),
            "group_limit": cat.get("group_limit"),
            "groups": [
                {
                    "canvas_id": g.get("id"),
                    "name": g.get("name"),
                    "members_count": g.get("members_count", 0),
                }
                for g in (groups if isinstance(groups, list) else [])
            ],
        })
    index["group_sets"] = group_sets
    print(f"  {len(group_sets)} group sets")

    # -----------------------------------------------------------------------
    # Calendar Events (office hours, TA labs, review sessions, etc.)
    # -----------------------------------------------------------------------
    print("Pulling calendar events...")
    cal_events = _get(f"/calendar_events", params={
        "context_codes[]": f"course_{course_id}",
        "per_page": 50,
        "all_events": True,
    })
    index["calendar_events"] = [
        {
            "canvas_id": e.get("id"),
            "title": e.get("title"),
            "start_at": e.get("start_at"),
            "end_at": e.get("end_at"),
            "location_name": e.get("location_name"),
            "description_preview": (e.get("description") or "")[:200],
            "workflow_state": e.get("workflow_state"),
        }
        for e in (cal_events if isinstance(cal_events, list) else [])
    ]
    print(f"  {len(index['calendar_events'])} calendar events")

    _save_index(index)
    total = len(index["files"])

    # -----------------------------------------------------------------------
    # Stale index entry pruning — remove index entries whose files don't exist
    # (happens when Canvas items are renamed and get new slugs/filenames)
    # -----------------------------------------------------------------------
    missing_from_disk = [fp for fp in list(index["files"].keys()) if not Path(fp).exists()]
    for fp in missing_from_disk:
        del index["files"][fp]
    if missing_from_disk:
        _vprint(f"  Pruned {len(missing_from_disk)} stale index entries (files renamed/removed)")

    # -----------------------------------------------------------------------
    # Stale file cleanup — delete any tracked-extension files not in new index
    # -----------------------------------------------------------------------
    tracked_paths = set(index["files"].keys())
    # Also protect homepage, syllabus, and _course.json — tracked separately, not in index["files"]
    if index.get("homepage"):
        tracked_paths.add(index["homepage"]["filepath"])
    if index.get("syllabus"):
        tracked_paths.add(index["syllabus"]["filepath"])
    tracked_paths.add(str(COURSE_DIR / "_course.json"))
    deleted = []
    for ext in ("*.json", "*.html"):
        for f in COURSE_DIR.rglob(ext):
            if f.name == "_module.json":
                continue
            rel = str(f)
            if rel not in tracked_paths:
                f.unlink()
                deleted.append(rel)
                print(f"  [deleted] {rel}")

    # -----------------------------------------------------------------------
    # Auto-log: record what changed vs prior index (undocumented Canvas edits)
    # -----------------------------------------------------------------------
    # Build full hash map of new state (files + homepage + syllabus)
    new_hashes = {fp: meta.get("hash") for fp, meta in index["files"].items()}
    if index.get("homepage"):
        new_hashes[index["homepage"]["filepath"]] = index["homepage"].get("hash")
    if index.get("syllabus"):
        new_hashes[index["syllabus"]["filepath"]] = index["syllabus"].get("hash")

    changed_from_canvas = [
        fp for fp, h in new_hashes.items()
        if fp in prior_hashes and prior_hashes[fp] != h
    ]
    new_files = [fp for fp in new_hashes if fp not in prior_hashes]
    log_entries = changed_from_canvas + new_files + deleted

    if log_entries:
        summary = f"Full pull — {len(changed_from_canvas)} changed, {len(new_files)} new, {len(deleted)} deleted"
        _log_push(summary, "(automatic — canvas-side changes pulled, no manual summary)", log_entries, direction="pull")
        print(f"  Changes logged to {PUSH_LOG}")

    print(f"\nPull complete. {total} files tracked in .canvas/index.json")
    print(f"  {len(index['modules'])} modules, {total} content files")
    if deleted:
        print(f"  {len(deleted)} stale file(s) removed")
    print(f"Course folder: {COURSE_DIR.resolve()}")


# ---------------------------------------------------------------------------
# Status: diff local vs index
# ---------------------------------------------------------------------------

def cmd_status():
    """Show which local files differ from what was last synced to Canvas."""
    index = _load_index()
    files = index.get("files", {})

    if not files:
        print("No tracked files. Run --init first.")
        return

    changed = []
    missing = []

    for filepath_str, meta in files.items():
        path = Path(filepath_str)
        if not path.exists():
            missing.append(filepath_str)
            continue
        current_hash = _file_hash(path)
        if current_hash != meta.get("hash"):
            changed.append((filepath_str, meta))

    if not changed and not missing:
        print("Everything up to date. Nothing to push.")
        return

    if changed:
        print(f"Modified ({len(changed)} files):")
        for fp, meta in changed:
            print(f"  M  {fp}  [{meta['type']}]")

    if missing:
        print(f"\nMissing locally ({len(missing)} files):")
        for fp in missing:
            print(f"  ?  {fp}")

    print(f"\nRun --push to sync changes to Canvas.")


# ---------------------------------------------------------------------------
# Push: local files → Canvas
# ---------------------------------------------------------------------------

def _push_page(filepath: Path, meta: dict) -> bool:
    page_url = meta.get("page_url")
    if not page_url:
        print(f"    ERROR: no page_url in index for {filepath}")
        return False
    body = filepath.read_text(encoding="utf-8")
    result = _put(f"/courses/{CANVAS_COURSE_ID}/pages/{page_url}", {
        "wiki_page": {"body": body, "published": meta.get("published", True)}
    })
    if result.get("error"):
        print(f"    ERROR: {result['error']}")
        return False
    return True


def _push_assignment(filepath: Path, meta: dict) -> bool:
    canvas_id = meta.get("canvas_id")
    if not canvas_id:
        print(f"    ERROR: no canvas_id in index for {filepath}")
        return False
    data = json.loads(filepath.read_text(encoding="utf-8"))
    result = _put(f"/courses/{CANVAS_COURSE_ID}/assignments/{canvas_id}", {
        "assignment": {
            "description": data.get("description", ""),
            "points_possible": data.get("points_possible"),
            "published": data.get("published", True),
        }
    })
    if result.get("error"):
        print(f"    ERROR: {result['error']}")
        return False
    return True


def _push_quiz(filepath: Path, meta: dict) -> bool:
    """Push classic quiz description via the quizzes endpoint."""
    canvas_id = meta.get("canvas_id")
    if not canvas_id:
        print(f"    ERROR: no canvas_id in index for {filepath}")
        return False
    data = json.loads(filepath.read_text(encoding="utf-8"))
    result = _put(f"/courses/{CANVAS_COURSE_ID}/quizzes/{canvas_id}", {
        "quiz": {"description": data.get("description", "")}
    })
    if result.get("error"):
        print(f"    ERROR: {result['error']}")
        return False
    return True


def _push_discussion(filepath: Path, meta: dict) -> bool:
    canvas_id = meta.get("canvas_id")
    if not canvas_id:
        print(f"    ERROR: no canvas_id in index for {filepath}")
        return False
    data = json.loads(filepath.read_text(encoding="utf-8"))
    result = _put(f"/courses/{CANVAS_COURSE_ID}/discussion_topics/{canvas_id}", {
        "title": data.get("title", ""),
        "message": data.get("message", ""),
        "published": data.get("published", True),
    })
    if result.get("error"):
        print(f"    ERROR: {result['error']}")
        return False
    return True


def cmd_push(target: Optional[str] = None):
    """Push changed local files to Canvas. Optionally filter to a module folder."""
    _check_env()

    index = _load_index()
    files = index.get("files", {})

    # Check homepage separately — tracked under index["homepage"], not index["files"]
    homepage_meta = index.get("homepage")
    if homepage_meta and (not target or "homepage" in target):
        homepage_path = Path(homepage_meta["filepath"])
        if homepage_path.exists():
            current_hash = _file_hash(homepage_path)
            if current_hash != homepage_meta.get("hash"):
                print(f"  [Homepage] {homepage_path}")
                body = homepage_path.read_text(encoding="utf-8")
                page_url = homepage_meta.get("page_url", "front-page")
                resp = requests.put(
                    f"{CANVAS_BASE_URL}/api/v1/courses/{CANVAS_COURSE_ID}/pages/{page_url}",
                    headers=_headers(),
                    json={"wiki_page": {"body": body}}, timeout=20)
                if resp.status_code < 400:
                    index["homepage"]["hash"] = current_hash
                    print(f"    OK")
                else:
                    print(f"    FAILED: {resp.text[:200]}")
                _save_index(index)

    # Check _course.json — late_policy and other course-level settings
    course_path = COURSE_DIR / "_course.json"
    if course_path.exists() and (not target or "_course" in target or "course" == target):
        course_hash = _file_hash(course_path)
        stored_hash = index.get("course_hash")
        if course_hash != stored_hash:
            print(f"  [Course] {course_path}")
            data = json.loads(course_path.read_text(encoding="utf-8"))
            lp = data.get("late_policy", {})
            if lp:
                resp = requests.patch(
                    f"{CANVAS_BASE_URL}/api/v1/courses/{CANVAS_COURSE_ID}/late_policy",
                    headers=_headers(),
                    json={"late_policy": lp}, timeout=20)
                if resp.status_code in (200, 204):
                    index["course_hash"] = course_hash
                    index["course"] = data
                    print(f"    OK (late_policy updated)")
                else:
                    print(f"    FAILED late_policy: {resp.text[:200]}")
                _save_index(index)

    # Check syllabus separately — it's tracked under index["syllabus"], not index["files"]
    syllabus_meta = index.get("syllabus")
    if syllabus_meta and (not target or "syllabus" in target):
        syllabus_path = Path(syllabus_meta["filepath"])
        if syllabus_path.exists():
            current_hash = _file_hash(syllabus_path)
            if current_hash != syllabus_meta.get("hash"):
                print(f"  [Syllabus] {syllabus_path}")
                body = syllabus_path.read_text(encoding="utf-8")
                url = f"{CANVAS_BASE_URL}/api/v1/courses/{CANVAS_COURSE_ID}"
                resp = requests.put(url, headers=_headers(),
                                    json={"course": {"syllabus_body": body}}, timeout=20)
                result = {"success": resp.status_code < 400, "status_code": resp.status_code,
                          "error": resp.text[:200] if resp.status_code >= 400 else None}
                if result.get("success"):
                    index["syllabus"]["hash"] = current_hash
                    print(f"    OK")
                else:
                    print(f"    FAILED: {result.get('error')}")
                _save_index(index)

    push_candidates = {}
    for filepath_str, meta in files.items():
        path = Path(filepath_str)
        # Filter to target module if specified
        if target and target not in filepath_str:
            continue
        if not path.exists():
            continue
        current_hash = _file_hash(path)
        if current_hash != meta.get("hash"):
            push_candidates[filepath_str] = (path, meta)

    if not push_candidates:
        print("Nothing to push — all files match Canvas.")
        return

    # Commit-style log prompt
    print(f"\n{len(push_candidates)} file(s) ready to push.")
    try:
        summary = input("Push summary (required): ").strip()
        if not summary:
            print("Aborted — summary is required.")
            return
        comment = input("Additional comments (optional, Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        # Non-interactive context (agent, CI) — proceed without prompt
        summary = "Automated push"
        comment = ""

    print(f"\nPushing {len(push_candidates)} changed file(s)...\n")

    pushed = 0
    for filepath_str, (path, meta) in push_candidates.items():
        item_type = meta.get("type")
        print(f"  [{item_type}] {filepath_str}")

        ok = False
        if item_type == "Page":
            ok = _push_page(path, meta)
        elif item_type == "Assignment":
            ok = _push_assignment(path, meta)
        elif item_type == "Discussion":
            ok = _push_discussion(path, meta)
        elif item_type == "Quiz":
            ok = _push_quiz(path, meta)
        elif item_type == "NewQuiz":
            print(f"    Canvas-only: NewQuiz descriptions must be edited in Canvas UI (API not supported)")
            # Acknowledge current state so it doesn't reappear on every push
            index["files"][filepath_str]["hash"] = _file_hash(path)
            _save_index(index)
            continue
        elif item_type in METADATA_ONLY_TYPES:
            print(f"    SKIP: {item_type} is metadata-only (manage in Canvas directly)")
            continue
        else:
            print(f"    SKIP: unknown type {item_type}")
            continue

        if ok:
            index["files"][filepath_str]["hash"] = _file_hash(path)
            print(f"    OK")
            pushed += 1
        else:
            print(f"    FAILED — hash not updated, will retry on next push")

    _save_index(index)
    pushed_files = [fp for fp, (path, meta) in push_candidates.items()
                    if index["files"].get(fp, {}).get("hash") == _file_hash(path)]
    _log_push(summary, comment, list(push_candidates.keys()), direction="push")
    print(f"\nPushed {pushed}/{len(push_candidates)} files.")
    print(f"Logged to {PUSH_LOG}")


# ---------------------------------------------------------------------------
# Pull single resource (re-sync from Canvas → local)
# ---------------------------------------------------------------------------

def cmd_pull(target: str):
    """
    Re-pull a specific file from Canvas, overwriting local.
    Use this when Canvas was edited directly and you want to accept that change.
    Logs the undocumented Canvas change to .canvas/push_log.md.
    Example: --pull course/sprint-1-setup-dag-demo/sprint-1-overview.html
    """
    index = _load_index()
    files = index.get("files", {})

    matches = {k: v for k, v in files.items() if target in k}
    if not matches:
        print(f"No tracked file matching: {target}")
        return

    for filepath_str, meta in matches.items():
        path = Path(filepath_str)
        item_type = meta.get("type")
        print(f"Pulling {filepath_str} from Canvas...")

        if item_type == "Page":
            page_url = meta.get("page_url")
            body = _pull_page(CANVAS_COURSE_ID, page_url)
            if body is not None:
                path.write_text(body, encoding="utf-8")
                index["files"][filepath_str]["hash"] = _file_hash(path)
                print(f"  OK — local file updated from Canvas")
            else:
                print(f"  ERROR — could not fetch page {page_url}")

        elif item_type == "Assignment":
            data = _pull_assignment(CANVAS_COURSE_ID, meta["canvas_id"])
            if data:
                path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                index["files"][filepath_str]["hash"] = _file_hash(path)
                print(f"  OK — local file updated from Canvas")

        elif item_type == "Discussion":
            data = _pull_discussion(CANVAS_COURSE_ID, meta["canvas_id"])
            if data:
                path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                index["files"][filepath_str]["hash"] = _file_hash(path)
                print(f"  OK — local file updated from Canvas")

        else:
            print(f"  SKIP: pull not implemented for {item_type}")

    _save_index(index)

    # Log undocumented Canvas-side change
    pulled_files = list(matches.keys())
    try:
        comment = input("Note about this Canvas-side change (optional, Enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        comment = ""
    _log_push(f"Canvas-side edit accepted: {target}", comment, pulled_files, direction="pull")
    print(f"Logged to {PUSH_LOG}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="canvas_sync — local mirror of a Canvas course",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  --pull              Full course pull from Canvas (cleans stale local files)
  --pull <path>       Re-pull one file from Canvas and log the Canvas-side change
  --push              Push all local changes to Canvas (prompts for summary + comment)
  --push <module>     Push changed files in one module only
  --status            Show local changes not yet pushed
  --init              Alias for --pull (full course pull)

Flags:
  --quiet             Suppress per-file lines; show only headers and totals

Change log:  .canvas/push_log.md  (appended on every --push and --pull <path>)
        """
    )
    parser.add_argument("--init", action="store_true", help="Pull full course into course/ (same as --pull with no path)")
    parser.add_argument("--status", action="store_true", help="Show changed files")
    parser.add_argument("--push", nargs="?", const="", metavar="MODULE", help="Push changed files to Canvas")
    parser.add_argument("--pull", nargs="?", const="", metavar="PATH",
                        help="Full course pull (no path) or re-pull one file from Canvas (with path)")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-file output; show only headers and totals")

    args = parser.parse_args()

    if args.quiet:
        globals()["QUIET"] = True

    if args.init or args.pull == "":
        cmd_init()
    elif args.status:
        cmd_status()
    elif args.push is not None:
        cmd_push(args.push if args.push else None)
    elif args.pull:
        cmd_pull(args.pull)
    else:
        parser.print_help()
