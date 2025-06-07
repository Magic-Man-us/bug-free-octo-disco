import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from parallel_test_runner import find_test_scripts, run_test, run_all_tests

TESTS_DIR = ROOT / "tests"
TAGGED_SCRIPT = TESTS_DIR / "test_tagged.sh"
SUCCESS_SCRIPT = TESTS_DIR / "test_success.sh"
FAIL_SCRIPT = TESTS_DIR / "test_fail.sh"


def test_find_test_scripts_with_tag():
    scripts = find_test_scripts(str(TESTS_DIR), tags=["slow"])
    assert TAGGED_SCRIPT in scripts
    # only tagged should appear when filtering
    assert SUCCESS_SCRIPT not in scripts


def test_run_test_success():
    result = run_test(SUCCESS_SCRIPT, shell="bash")
    assert result["name"] == "test_success.sh"
    assert result["status"] == "PASS"
    assert result["exit_code"] == 0


def test_run_all_tests_parallel(tmp_path):
    dst = tmp_path / "tests"
    dst.mkdir()
    for src in (SUCCESS_SCRIPT, FAIL_SCRIPT):
        dst_path = dst / src.name
        dst_path.write_text(src.read_text())
        dst_path.chmod(0o755)

    scripts = list(dst.glob("test_*.sh"))
    results = run_all_tests(scripts, shell="bash", max_workers=2, timeout=5)
    statuses = {r["name"]: r["status"] for r in results}
    assert statuses["test_success.sh"] == "PASS"
    assert statuses["test_fail.sh"] == "FAIL"
