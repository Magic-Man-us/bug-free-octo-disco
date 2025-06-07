import subprocess
import logging
import argparse
import shutil
import json
import time
from pathlib import Path
from typing import Iterable, List, Tuple, Dict

from colorama import Fore, Style, init


def save_json_report(results: List[Dict], filename: Path) -> None:
    """Write test results to a JSON file."""
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)


def save_html_report(results: List[Dict], filename: Path) -> None:
    """Write a minimal HTML summary of test results."""
    with open(filename, "w") as f:
        f.write("<html><body><h1>Test Report</h1><table border='1'>")
        f.write("<tr><th>Test</th><th>Status</th><th>Exit Code</th><th>Duration (s)</th></tr>")
        for r in results:
            color = {
                0: "green",
                -1: "orange",
            }.get(r["exit_code"], "red")
            f.write(
                f"<tr><td>{r['name']}</td>"
                f"<td style='color:{color}'>{'PASS' if r['exit_code']==0 else 'FAIL'}</td>"
                f"<td>{r['exit_code']}</td>"
                f"<td>{r['duration']:.2f}</td></tr>"
            )
        f.write("</table></body></html>")

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

def run_test(
    script_path: Path, timeout: int = 30, coverage_dir: Path | None = None
) -> Tuple[str, int, str, str, float]:
    """Run a single test script and return its results with duration."""
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
        start = time.perf_counter()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # Don't raise even if exit code != 0
        )
        duration = time.perf_counter() - start
        return (
            script_path.name,
            result.returncode,
            result.stdout,
            result.stderr,
            duration,
        )
    except subprocess.TimeoutExpired as e:
        return (script_path.name, -1, "", f"Timeout after {timeout}s", timeout)
    except Exception as e:
        return (script_path.name, -2, "", f"Unexpected error: {e}", 0.0)

def run_all_tests(
    directory: str,
    patterns: Iterable[str],
    timeout: int,
    coverage: bool,
    json_report: bool = False,
    html_report: bool = False,
    report_dir: Path = Path("."),
) -> None:
    """Run all discovered tests and optionally write reports."""
    scripts = find_test_scripts(directory, patterns)
    logger.info(f"Found {len(scripts)} test scripts.")

    failures = []
    results: List[Dict[str, object]] = []
    coverage_dir = Path("coverage") if coverage else None
    for script in scripts:
        coverage_path = coverage_dir / script.stem if coverage_dir else None
        name, code, out, err, dur = run_test(
            script, timeout=timeout, coverage_dir=coverage_path
        )
        results.append(
            {
                "name": name,
                "exit_code": code,
                "stdout": out,
                "stderr": err,
                "duration": dur,
            }
        )
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

    report_path = Path(report_dir)
    if json_report:
        save_json_report(results, report_path / "test_results.json")
        logger.info("JSON report saved.")
    if html_report:
        save_html_report(results, report_path / "test_results.html")
        logger.info("HTML report saved.")

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
    parser.add_argument("--json", action="store_true", help="Write JSON results to test_results.json")
    parser.add_argument("--html", action="store_true", help="Write HTML summary to test_results.html")
    parser.add_argument("--report-dir", default=".", help="Directory for output reports")
    args = parser.parse_args()

    patterns = args.tests if args.tests else ["test_*.sh"]
    run_all_tests(
        args.directory,
        patterns,
        args.timeout,
        args.coverage,
        json_report=args.json,
        html_report=args.html,
        report_dir=args.report_dir,
    )
