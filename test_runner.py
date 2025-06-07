import subprocess
import logging
import os
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("test_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_test_scripts(directory: str = "tests") -> List[Path]:
    test_dir = Path(directory)
    return sorted([f for f in test_dir.glob("test_*.sh") if f.is_file()])

def run_test(script_path: Path, timeout: int = 30) -> Tuple[str, int, str, str]:
    logger.info(f"Running: {script_path}")
    try:
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Don't raise even if exit code != 0
        )
        return (script_path.name, result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired as e:
        return (script_path.name, -1, "", f"Timeout after {timeout}s")
    except Exception as e:
        return (script_path.name, -2, "", f"Unexpected error: {e}")

def run_all_tests():
    scripts = find_test_scripts()
    logger.info(f"Found {len(scripts)} test scripts.")

    failures = []
    for script in scripts:
        name, code, out, err = run_test(script)
        if code == 0:
            logger.info(f"[PASS] {name}")
        else:
            logger.error(f"[FAIL] {name} (exit {code})")
            logger.error(f"  STDERR:\n{err.strip()}")
            failures.append(name)

    logger.info("==== Test Summary ====")
    logger.info(f"Total: {len(scripts)}, Passed: {len(scripts) - len(failures)}, Failed: {len(failures)}")

    if failures:
        logger.error("Failed Tests:")
        for name in failures:
            logger.error(f" - {name}")
        exit(1)
    else:
        logger.info("All tests passed.")
        exit(0)

if __name__ == "__main__":
    run_all_tests()
