"""
Sprint 2 regression tests — Safe to Work In
Covers issues: #4
"""
import subprocess
import sys
from pathlib import Path

from conftest import sandbox_env  # noqa: F401  (used as fixture via import)


# ---------------------------------------------------------------------------
# #4 — course_ref/ must survive --pull
# ---------------------------------------------------------------------------

def test_course_ref_survives_pull(sandbox_env):
    """#4: files in course_ref/ must not be deleted by a full --pull."""
    test_file = Path("course_ref/_regression_test.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("regression sentinel")

    try:
        result = subprocess.run(
            [sys.executable, "tools/canvas_sync.py", "--pull", "--quiet"],
            env=sandbox_env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Pull failed:\n{result.stderr}"
        assert test_file.exists(), (
            "REGRESSION #4: course_ref/ file was deleted by --pull"
        )
    finally:
        test_file.unlink(missing_ok=True)


def test_questions_json_survives_pull(sandbox_env):
    """#4: *.questions.json files in course/ must not be deleted by --pull."""
    import json
    test_file = Path("course/_regression_test.questions.json")
    test_file.write_text(json.dumps([{"question_name": "regression test"}]))

    try:
        result = subprocess.run(
            [sys.executable, "tools/canvas_sync.py", "--pull", "--quiet"],
            env=sandbox_env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Pull failed:\n{result.stderr}"
        assert test_file.exists(), (
            "REGRESSION #4: .questions.json file in course/ was deleted by --pull"
        )
    finally:
        test_file.unlink(missing_ok=True)
