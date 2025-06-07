import os
import shutil
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from test_runner import find_test_scripts, run_test, run_all_tests


TESTS_DIR = Path(__file__).resolve().parent.parent / "tests"
SUCCESS_SCRIPT = TESTS_DIR / "test_success.sh"
FAIL_SCRIPT = TESTS_DIR / "test_fail.sh"

def test_find_test_scripts_default():
    scripts = find_test_scripts(str(TESTS_DIR))
    names = [p.name for p in scripts]
    assert "test_success.sh" in names
    assert "test_fail.sh" in names


def test_find_test_scripts_pattern():
    scripts = find_test_scripts(str(TESTS_DIR), patterns=["test_success.sh"])
    assert scripts == [SUCCESS_SCRIPT]


def test_run_test_success():
    name, code, out, err = run_test(SUCCESS_SCRIPT)
    assert name == "test_success.sh"
    assert code == 0
    assert err == ""


def test_run_test_failure():
    name, code, out, err = run_test(FAIL_SCRIPT)
    assert name == "test_fail.sh"
    assert code == 1


def test_run_all_tests_pass(tmp_path, caplog):
    # copy only success script
    dst = tmp_path / "tests"
    dst.mkdir()
    shutil.copy(SUCCESS_SCRIPT, dst / SUCCESS_SCRIPT.name)
    caplog.set_level("INFO")
    with pytest.raises(SystemExit) as exc:
        run_all_tests(str(dst), ["test_*.sh"], timeout=5, coverage=False)
    assert exc.value.code == 0
    assert "All tests passed" in caplog.text


def test_run_all_tests_fail(tmp_path, caplog):
    dst = tmp_path / "tests"
    dst.mkdir()
    shutil.copy(SUCCESS_SCRIPT, dst / SUCCESS_SCRIPT.name)
    shutil.copy(FAIL_SCRIPT, dst / FAIL_SCRIPT.name)
    caplog.set_level("INFO")
    with pytest.raises(SystemExit) as exc:
        run_all_tests(str(dst), ["test_*.sh"], timeout=5, coverage=False)
    assert exc.value.code == 1
    assert "Failed Tests" in caplog.text
