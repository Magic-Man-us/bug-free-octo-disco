import subprocess
import logging
import argparse
import shutil
from pathlib import Path
from typing import Iterable, List, Tuple

from colorama import Fore, Style, init

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("test_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
init(autoreset=True)

def find_test_scripts(directory: str = "tests", patterns: Iterable[str] = ("test_*.sh",)) -> List[Path]:
    """Return a sorted list of test script paths matching the given patterns."""
    test_dir = Path(directory)
    scripts: List[Path] = []
    for pattern in patterns:
        scripts.extend(test_dir.glob(pattern))
    # Remove duplicates and ensure only files
    unique_scripts = {s.resolve() for s in scripts if s.is_file()}
    return sorted(unique_scripts)

def run_test(script_path: Path, timeout: int = 30, coverage_dir: Path | None = None) -> Tuple[str, int, str, str]:
    """Run a single test script and return its results."""
    logger.info(f"Running: {script_path}")
    cmd = ["bash", str(script_path)]
    if coverage_dir:
        kcov = shutil.which("kcov")
        if not kcov:
            logger.warning("Coverage requested but kcov not found. Running without coverage.")
        else:
            coverage_dir.mkdir(parents=True, exist_ok=True)
            cmd = [kcov, str(coverage_dir), "bash", str(script_path)]
    try:
        result = subprocess.run(
            cmd,
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

def run_all_tests(directory: str, patterns: Iterable[str], timeout: int, coverage: bool):
    """Run all discovered tests according to the provided options."""
    scripts = find_test_scripts(directory, patterns)
    logger.info(f"Found {len(scripts)} test scripts.")

    failures = []
    coverage_dir = Path("coverage") if coverage else None
    for script in scripts:
        coverage_path = coverage_dir / script.stem if coverage_dir else None
        name, code, out, err = run_test(script, timeout=timeout, coverage_dir=coverage_path)
        if code == 0:
            logger.info(Fore.GREEN + f"[PASS] {name}")
        else:
            logger.error(Fore.RED + f"[FAIL] {name} (exit {code})")
            if err.strip():
                logger.error(Fore.RED + f"  STDERR:\n{err.strip()}")
            failures.append(name)

    logger.info("==== Test Summary ====")
    logger.info(
        f"Total: {len(scripts)}, Passed: {len(scripts) - len(failures)}, Failed: {len(failures)}"
    )

    if failures:
        logger.error(Fore.RED + "Failed Tests:")
        for name in failures:
            logger.error(Fore.RED + f" - {name}")
        exit(1)
    else:
        logger.info(Fore.GREEN + "All tests passed.")
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run shell test scripts")
    parser.add_argument("tests", nargs="*", help="Specific test patterns to run")
    parser.add_argument("-d", "--directory", default="tests", help="Directory containing test scripts")
    parser.add_argument("-t", "--timeout", type=int, default=30, help="Per-test timeout in seconds")
    parser.add_argument("--coverage", action="store_true", help="Collect coverage using kcov if available")
    args = parser.parse_args()

    patterns = args.tests if args.tests else ["test_*.sh"]
    run_all_tests(args.directory, patterns, args.timeout, args.coverage)
