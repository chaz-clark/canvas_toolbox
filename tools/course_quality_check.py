"""
course_quality_check.py

Checks a Canvas course for common quality issues and writes a structured
quality report to .canvas/quality_report_{course_id}.json.

Checks performed:
  - Duplicate assignment groups
  - Duplicate assignments / quizzes
  - Duplicate module items (same title in same module)
  - Due / lock / unlock dates outside the course date window

Report output separates issues into two buckets:
  "auto_fixable"  — issues a tool or agent can resolve without human input
  "manual_review" — issues that require human judgment or Canvas UI action

Usage:
    uv run python tools/course_quality_check.py                    # source course (CANVAS_COURSE_ID)
    uv run python tools/course_quality_check.py --master           # MASTER_COURSE_ID
    uv run python tools/course_quality_check.py --blueprint        # BLUEPRINT_COURSE_ID
    uv run python tools/course_quality_check.py --all              # all three
    uv run python tools/course_quality_check.py --course 415322    # specific ID
    uv run python tools/course_quality_check.py --fix              # auto-fix fixable issues (source)
    uv run python tools/course_quality_check.py --fix --master     # auto-fix on master
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent.parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

CANVAS_API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "")
_raw = os.environ.get("CANVAS_BASE_URL", "").strip().rstrip("/")
CANVAS_BASE_URL = ("https://" + _raw) if _raw and not _raw.startswith("http") else _raw
SOURCE_ID    = os.environ.get("CANVAS_COURSE_ID", "")
MASTER_ID    = os.environ.get("MASTER_COURSE_ID", "")
BLUEPRINT_ID = os.environ.get("BLUEPRINT_COURSE_ID", "")
REPORT_DIR   = Path(".canvas")


def _h():
    return {"Authorization": f"Bearer {CANVAS_API_TOKEN}"}


def _get_all(url: str, params: dict = None) -> list:
    results, p = [], {"per_page": 100, **(params or {})}
    while url:
        r = requests.get(url, headers=_h(), params=p, timeout=30)
        if r.status_code >= 400:
            print(f"  WARNING: {r.status_code} fetching {url}")
            return results
        results.extend(r.json())
        url, p = None, {}
        for part in r.headers.get("Link", "").split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return results


def _parse_dt(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.rstrip("Z")).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _get_course_window(course_id: str) -> tuple:
    """Return (start_at, end_at) as datetime objects."""
    idx_path = Path(".canvas/index.json")
    if str(course_id) == str(SOURCE_ID) and idx_path.exists():
        idx = json.loads(idx_path.read_text())
        c = idx.get("course", {})
        s = _parse_dt(c.get("start_at"))
        e = _parse_dt(c.get("end_at"))
        if s and e:
            return s, e

    r = requests.get(f"{CANVAS_BASE_URL}/api/v1/courses/{course_id}", headers=_h(), timeout=20)
    if r.ok:
        d = r.json()
        return _parse_dt(d.get("start_at")), _parse_dt(d.get("end_at"))
    return None, None


def _audit_course(course_id: str) -> dict:
    """
    Run all checks. Returns a dict with:
        course_id, label, start_at, end_at,
        auto_fixable: [...],   # can be resolved programmatically
        manual_review: [...]   # require human judgment
    """
    base = CANVAS_BASE_URL
    auto_fixable = []
    manual_review = []

    start_at, end_at = _get_course_window(course_id)

    # ── Assignment groups ──────────────────────────────────────
    groups = _get_all(f"{base}/api/v1/courses/{course_id}/assignment_groups")
    group_counts = Counter(g["name"] for g in groups)
    for name, count in group_counts.items():
        if count > 1:
            dups = [g for g in groups if g["name"] == name][1:]  # keep first, delete rest
            for g in dups:
                auto_fixable.append({
                    "type": "duplicate_assignment_group",
                    "title": name,
                    "canvas_id": g["id"],
                    "action": f"DELETE /api/v1/courses/{course_id}/assignment_groups/{g['id']}",
                    "note": f"Duplicate assignment group '{name}' (id={g['id']})"
                })

    # ── Assignments ────────────────────────────────────────────
    assignments = _get_all(f"{base}/api/v1/courses/{course_id}/assignments")
    by_name = defaultdict(list)
    for a in assignments:
        by_name[a["name"]].append(a)

    for name, items in by_name.items():
        if len(items) > 1:
            # Sort by id ascending — lowest id is oldest (original)
            items_sorted = sorted(items, key=lambda x: x["id"])
            for dup in items_sorted[1:]:
                auto_fixable.append({
                    "type": "duplicate_assignment",
                    "title": name,
                    "canvas_id": dup["id"],
                    "action": f"DELETE /api/v1/courses/{course_id}/assignments/{dup['id']}",
                    "note": f"Duplicate assignment '{name}' (id={dup['id']})"
                })

    # Date checks — assignments
    if start_at and end_at:
        for a in assignments:
            name = a["name"]
            published = a.get("published", True)
            for field in ("due_at", "lock_at", "unlock_at"):
                dt = _parse_dt(a.get(field))
                if dt and not (start_at <= dt <= end_at):
                    entry = {
                        "type": "date_out_of_window",
                        "item_type": "assignment",
                        "published": published,
                        "title": name,
                        "canvas_id": a["id"],
                        "field": field,
                        "value": a.get(field),
                        "course_window": f"{start_at.date()} → {end_at.date()}",
                        "action": f"PUT /api/v1/courses/{course_id}/assignments/{a['id']} — update {field}",
                        "note": f"{'[UNPUBLISHED] ' if not published else ''}Assignment '{name}' {field}={a.get(field)[:10]} is outside course window"
                    }
                    if published:
                        auto_fixable.append(entry)
                    else:
                        manual_review.append(entry)

    # ── Quizzes ────────────────────────────────────────────────
    quizzes = _get_all(f"{base}/api/v1/courses/{course_id}/quizzes")
    qby_name = defaultdict(list)
    for q in quizzes:
        qby_name[q["title"]].append(q)

    for title, items in qby_name.items():
        if len(items) > 1:
            items_sorted = sorted(items, key=lambda x: x["id"])
            for dup in items_sorted[1:]:
                auto_fixable.append({
                    "type": "duplicate_quiz",
                    "title": title,
                    "canvas_id": dup["id"],
                    "action": f"DELETE /api/v1/courses/{course_id}/quizzes/{dup['id']}",
                    "note": f"Duplicate quiz '{title}' (id={dup['id']})"
                })

    if start_at and end_at:
        for q in quizzes:
            published = q.get("published", True)
            for field in ("due_at", "lock_at", "unlock_at"):
                dt = _parse_dt(q.get(field))
                if dt and not (start_at <= dt <= end_at):
                    entry = {
                        "type": "date_out_of_window",
                        "item_type": "quiz",
                        "published": published,
                        "title": q["title"],
                        "canvas_id": q["id"],
                        "field": field,
                        "value": q.get(field),
                        "course_window": f"{start_at.date()} → {end_at.date()}",
                        "action": f"PUT /api/v1/courses/{course_id}/quizzes/{q['id']} — update {field}",
                        "note": f"{'[UNPUBLISHED] ' if not published else ''}Quiz '{q['title']}' {field}={q.get(field)[:10]} is outside course window"
                    }
                    if published:
                        auto_fixable.append(entry)
                    else:
                        manual_review.append(entry)

    # ── Module items ───────────────────────────────────────────
    # Build a set of content IDs AND titles that appear in any module
    # Canvas module item types: "Assignment", "Quiz", "Discussion", "Page", etc.
    modules = _get_all(f"{base}/api/v1/courses/{course_id}/modules", {"include[]": ["items"]})
    module_content_ids: dict[str, set] = defaultdict(set)  # type → set of content_ids
    module_item_titles: set = set()  # all titles present in any module (lowercase for fuzzy-safe exact match)
    for mod in modules:
        items = mod.get("items") or _get_all(
            f"{base}/api/v1/courses/{course_id}/modules/{mod['id']}/items"
        )
        title_map = defaultdict(list)
        for it in items:
            title_map[it.get("title", "")].append(it)
            ctype = it.get("type", "")
            cid_val = it.get("content_id")
            if cid_val:
                module_content_ids[ctype].add(cid_val)
            if it.get("title"):
                module_item_titles.add(it["title"].strip().lower())

        for title, dups in title_map.items():
            if len(dups) > 1 and title:
                # Keep lowest position (first in module), remove rest
                dups_sorted = sorted(dups, key=lambda x: x.get("position", 999))
                for dup in dups_sorted[1:]:
                    auto_fixable.append({
                        "type": "duplicate_module_item",
                        "module": mod["name"],
                        "title": title,
                        "canvas_id": dup["id"],
                        "position": dup.get("position"),
                        "action": f"DELETE /api/v1/courses/{course_id}/modules/{mod['id']}/items/{dup['id']}",
                        "note": f"Duplicate module item in '{mod['name']}': '{title}' (item_id={dup['id']}, pos={dup.get('position')})"
                    })

    # ── Published content not linked in any module ─────────────
    # Canvas classic quizzes have TWO IDs: quiz_id (in /quizzes) and an underlying
    # assignment_id (in /assignments with submission_types=['online_quiz']).
    # Module items for quizzes store the quiz_id, not the assignment_id.
    # Build a lookup: assignment_id → quiz_id so we can cross-check correctly.
    quiz_assignment_id_to_quiz_id = {q.get("assignment_id"): q["id"]
                                     for q in quizzes if q.get("assignment_id")}

    for a in assignments:
        if not a.get("published", False):
            continue
        # If this assignment is the shell for a classic quiz, check the quiz_id in Quiz bucket
        quiz_id_for_assignment = quiz_assignment_id_to_quiz_id.get(a["id"])
        if quiz_id_for_assignment:
            in_module = quiz_id_for_assignment in module_content_ids["Quiz"]
        else:
            in_module = a["id"] in module_content_ids["Assignment"]
        if not in_module:
            name = a["name"]
            # If same title is already in a module under a different ID, it's an orphan duplicate
            same_name_in_module = name.strip().lower() in module_item_titles
            if same_name_in_module:
                auto_fixable.append({
                    "type": "orphaned_duplicate",
                    "item_type": "assignment",
                    "title": name,
                    "canvas_id": a["id"],
                    "note": f"Orphaned assignment '{name}' (id={a['id']}) — same title already in a module under a different ID, this copy is unreachable",
                    "action": f"DELETE /api/v1/courses/{course_id}/assignments/{a['id']}"
                })
            else:
                manual_review.append({
                    "type": "published_not_in_module",
                    "item_type": "assignment",
                    "title": name,
                    "canvas_id": a["id"],
                    "note": f"Published assignment '{name}' (id={a['id']}) is not linked in any module — students cannot find it",
                    "action": f"Add to the appropriate module via Canvas UI or POST /api/v1/courses/{course_id}/modules/:module_id/items"
                })

    # Discussions
    discussions = _get_all(f"{base}/api/v1/courses/{course_id}/discussion_topics")
    for d in discussions:
        if not d.get("published", False):
            continue
        in_module = d["id"] in module_content_ids["Discussion"]
        if not in_module:
            title = d["title"]
            same_name_in_module = title.strip().lower() in module_item_titles
            if same_name_in_module:
                auto_fixable.append({
                    "type": "orphaned_duplicate",
                    "item_type": "discussion",
                    "title": title,
                    "canvas_id": d["id"],
                    "note": f"Orphaned discussion '{title}' (id={d['id']}) — same title already in a module under a different ID",
                    "action": f"DELETE /api/v1/courses/{course_id}/discussion_topics/{d['id']}"
                })
            else:
                manual_review.append({
                    "type": "published_not_in_module",
                    "item_type": "discussion",
                    "title": title,
                    "canvas_id": d["id"],
                    "note": f"Published discussion '{title}' (id={d['id']}) is not linked in any module — students cannot find it",
                    "action": f"Add to the appropriate module via Canvas UI or POST /api/v1/courses/{course_id}/modules/:module_id/items"
                })

    # ── Empty modules ──────────────────────────────────────────
    for mod in modules:
        items = mod.get("items") or []
        if len(items) == 0:
            manual_review.append({
                "type": "empty_module",
                "title": mod["name"],
                "canvas_id": mod["id"],
                "note": f"Module '{mod['name']}' (id={mod['id']}) has no items — may be a sync artifact",
                "action": "Delete via Canvas UI or DELETE /api/v1/courses/{}/modules/{}".format(course_id, mod["id"])
            })

    # ── Course-level manual review items ───────────────────────
    if not start_at or not end_at:
        # Master/template courses intentionally have no dates — only flag for non-master courses
        if str(course_id) != str(MASTER_ID):
            manual_review.append({
                "type": "missing_course_dates",
                "note": "Course has no start_at or end_at set — date window checks were skipped.",
                "action": "Set course start and end dates in Canvas Settings > Course Details"
            })

    # Quiz questions — if a classic quiz has 0 questions it's an empty shell
    for q in quizzes:
        if q.get("quiz_type") != "assignment" and q.get("question_count", 1) == 0:
            manual_review.append({
                "type": "empty_quiz",
                "title": q["title"],
                "canvas_id": q["id"],
                "note": f"Quiz '{q['title']}' has 0 questions.",
                "action": "Use canvas_quiz_questions.py --push <questions-file.json> to add questions"
            })

    return {
        "course_id": course_id,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "course_window": {
            "start_at": start_at.isoformat() if start_at else None,
            "end_at": end_at.isoformat() if end_at else None,
        },
        "auto_fixable": auto_fixable,
        "manual_review": manual_review,
        "summary": {
            "auto_fixable": len(auto_fixable),
            "manual_review": len(manual_review),
            "total_issues": len(auto_fixable) + len(manual_review),
        }
    }


def _print_report(report: dict, label: str):
    cid = report["course_id"]
    w = report["course_window"]
    af = report["auto_fixable"]
    mr = report["manual_review"]

    print(f"\n{'='*62}")
    print(f"  {label} — Course {cid}")
    if w["start_at"] and w["end_at"]:
        print(f"  Window: {w['start_at'][:10]} → {w['end_at'][:10]}")
    else:
        print(f"  Window: NOT SET")
    print(f"{'='*62}")

    if not af and not mr:
        print("  All checks passed — no issues found.")
        return

    if af:
        print(f"\n  AUTO-FIXABLE ({len(af)}) — tools/agents can resolve:")
        by_type = defaultdict(list)
        for item in af:
            by_type[item["type"]].append(item)
        for t, items in by_type.items():
            print(f"    [{t}] x{len(items)}")
            for it in items:
                print(f"      • {it['note']}")

    if mr:
        print(f"\n  MANUAL REVIEW ({len(mr)}) — requires human action:")
        for it in mr:
            print(f"    • {it['note']}")
            print(f"      → {it['action']}")


def _write_md_report(reports: list[dict], labels: dict, path: Path):
    """Write a combined markdown quality report for all audited courses."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Canvas Course Quality Report",
        f"Generated: {now}",
        "",
    ]

    # Overall summary table
    lines += ["## Summary", ""]
    lines += ["| Course | Window | Auto-Fixable | Manual Review | Status |"]
    lines += ["|--------|--------|:------------:|:-------------:|--------|"]
    for r in reports:
        cid = r["course_id"]
        label = labels.get(cid, f"Course {cid}")
        w = r["course_window"]
        window = f"{w['start_at'][:10]} → {w['end_at'][:10]}" if w["start_at"] else "NOT SET"
        af = r["summary"]["auto_fixable"]
        mr = r["summary"]["manual_review"]
        status = "✅ Clean" if r["summary"]["total_issues"] == 0 else ("⚠️ Issues" if af == 0 else "🔴 Action needed")
        lines.append(f"| {label} | {window} | {af} | {mr} | {status} |")
    lines.append("")

    for r in reports:
        cid = r["course_id"]
        label = labels.get(cid, f"Course {cid}")
        w = r["course_window"]
        af = r["auto_fixable"]
        mr = r["manual_review"]

        lines += [f"---", f"## {label}", ""]
        window = f"{w['start_at'][:10]} → {w['end_at'][:10]}" if w["start_at"] else "NOT SET"
        lines += [f"**Course window:** {window}", ""]

        if not af and not mr:
            lines += ["All checks passed — no issues found.", ""]
            continue

        if af:
            lines += [
                f"### 🔴 Auto-Fixable ({len(af)})",
                "_These can be resolved by running `course_quality_check.py --fix` or via agent._",
                "",
            ]
            by_type = defaultdict(list)
            for item in af:
                by_type[item["type"]].append(item)

            type_labels = {
                "duplicate_assignment_group": "Duplicate Assignment Groups",
                "duplicate_assignment":       "Duplicate Assignments",
                "duplicate_quiz":             "Duplicate Quizzes",
                "duplicate_module_item":      "Duplicate Module Items",
                "date_out_of_window":         "Dates Outside Course Window",
                "orphaned_duplicate":         "Orphaned Duplicates (same title in module under different ID)",
            }
            for t, items in by_type.items():
                lines.append(f"**{type_labels.get(t, t)}**")
                for it in items:
                    fix = it.get("action", "")
                    lines.append(f"- {it['note']}")
                    if fix:
                        lines.append(f"  - Fix: `{fix}`")
                lines.append("")

        if mr:
            lines += [
                f"### ⚠️ Manual Review ({len(mr)})",
                "_These require human judgment or Canvas UI action._",
                "",
            ]
            by_type = defaultdict(list)
            for item in mr:
                by_type[item["type"]].append(item)

            type_labels = {
                "missing_course_dates":    "Missing Course Dates",
                "empty_quiz":              "Empty Quizzes (no questions)",
                "empty_module":            "Empty Modules (no items — possible sync artifact)",
                "date_out_of_window":      "Dates Outside Window (Unpublished Items)",
                "published_not_in_module": "Published Content Not Linked in Any Module",
            }
            for t, items in by_type.items():
                lines.append(f"**{type_labels.get(t, t)}**")
                for it in items:
                    lines.append(f"- {it['note']}")
                    action = it.get("action", "")
                    if action:
                        lines.append(f"  - Action: {action}")
                lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _apply_fixes(course_id: str, report: dict, dry_run: bool = False):
    """Delete duplicate items and report date issues (date fixes need human confirmation)."""
    base = CANVAS_BASE_URL
    af = report["auto_fixable"]

    deletable_types = {"duplicate_assignment_group", "duplicate_assignment",
                       "duplicate_quiz", "duplicate_module_item"}
    date_types = {"date_out_of_window"}

    fixed, skipped = 0, 0
    for item in af:
        if item["type"] in deletable_types:
            action = item["action"]  # "DELETE /api/v1/..."
            path = action.split(" ", 1)[1]
            url = f"{base}{path}"
            if dry_run:
                print(f"  [dry-run] DELETE {path}")
            else:
                r = requests.delete(url, headers=_h(), timeout=20)
                ok = r.status_code in (200, 204)
                print(f"  {'OK' if ok else 'FAILED'} DELETE — {item['note']}")
                if ok:
                    fixed += 1
                else:
                    skipped += 1
        elif item["type"] in date_types:
            print(f"  SKIP (date fix needs human decision): {item['note']}")
            skipped += 1

    print(f"\n  Fixed: {fixed}  |  Skipped: {skipped}")


def main():
    parser = argparse.ArgumentParser(
        description="Canvas course quality check: duplicates, date windows, empty quizzes"
    )
    parser.add_argument("--master",    action="store_true", help="Check MASTER_COURSE_ID")
    parser.add_argument("--blueprint", action="store_true", help="Check BLUEPRINT_COURSE_ID")
    parser.add_argument("--all",       action="store_true", help="Check all three courses")
    parser.add_argument("--course",    metavar="ID",        help="Check a specific course ID")
    parser.add_argument("--fix",       action="store_true", help="Auto-fix duplicate issues (deletes extras)")
    parser.add_argument("--dry-run",   action="store_true", help="Show what --fix would do without changing Canvas")
    args = parser.parse_args()

    if not CANVAS_API_TOKEN or not CANVAS_BASE_URL:
        print("ERROR: CANVAS_API_TOKEN and CANVAS_BASE_URL required in .env")
        sys.exit(1)

    targets = []
    if args.course:
        targets.append((args.course, f"Course {args.course}"))
    elif args.all:
        targets = [
            (SOURCE_ID,    f"Source (CANVAS_COURSE_ID={SOURCE_ID})"),
            (MASTER_ID,    f"Master (MASTER_COURSE_ID={MASTER_ID})"),
            (BLUEPRINT_ID, f"Blueprint (BLUEPRINT_COURSE_ID={BLUEPRINT_ID})"),
        ]
    elif args.master:
        targets.append((MASTER_ID, f"Master (MASTER_COURSE_ID={MASTER_ID})"))
    elif args.blueprint:
        targets.append((BLUEPRINT_ID, f"Blueprint (BLUEPRINT_COURSE_ID={BLUEPRINT_ID})"))
    else:
        targets.append((SOURCE_ID, f"Source (CANVAS_COURSE_ID={SOURCE_ID})"))

    targets = [(cid, label) for cid, label in targets if cid]
    if not targets:
        print("ERROR: No course IDs configured.")
        sys.exit(1)

    REPORT_DIR.mkdir(exist_ok=True)
    all_clean = True
    all_reports = []
    label_map = {}

    for course_id, label in targets:
        print(f"  Checking {label}...")
        report = _audit_course(course_id)
        _print_report(report, label)
        all_reports.append(report)
        label_map[course_id] = label

        # Write JSON report (machine-readable, gitignored)
        report_path = REPORT_DIR / f"quality_report_{course_id}.json"
        report_path.write_text(json.dumps(report, indent=2))

        if args.fix or args.dry_run:
            print(f"\n  {'[DRY RUN] ' if args.dry_run else ''}Applying auto-fixes...")
            _apply_fixes(course_id, report, dry_run=args.dry_run)

        if report["summary"]["total_issues"] > 0:
            all_clean = False

    # Write combined markdown report at repo root
    md_path = Path("quality_report.md")
    _write_md_report(all_reports, label_map, md_path)

    print(f"\n{'='*62}")
    if all_clean:
        print("  All courses clean.")
    else:
        print("  Issues found — review quality_report.md")
        if not args.fix and not args.dry_run:
            print("  Run with --fix to auto-resolve duplicates.")
    print(f"  Report → quality_report.md")
    print(f"{'='*62}\n")

    sys.exit(0 if all_clean else 1)


if __name__ == "__main__":
    main()
