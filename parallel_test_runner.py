import argparse
import subprocess
import logging
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional
import string


class Colors:
    """Terminal color codes for basic output highlighting."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"


def setup_logger(verbose: bool) -> None:
    """Configure the root logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("test_run.log"), logging.StreamHandler()],
    )

logger = logging.getLogger(__name__)



def safe_name(name):
    # Remove or replace non-printable characters
    return ''.join(c for c in name if c in string.printable and c not in "\x1b")



def find_test_scripts(directory: str = "tests", tags: Optional[List[str]] = None) -> List[Path]:
    """Locate test shell scripts optionally filtered by tags."""
    test_dir = Path(directory)
    scripts = [f for f in test_dir.glob("test_*.sh") if f.is_file()]
    if not tags:
        return sorted(scripts)

    tagged_scripts: List[Path] = []
    for script in scripts:
        contents = script.read_text()
        script_tags = re.findall(r"#\s*@(\w+)", contents)
        if any(tag in script_tags for tag in tags):
            tagged_scripts.append(script)
    return sorted(tagged_scripts)


def run_test(script_path: Path, shell: str, timeout: int = 30) -> Dict:
    """Execute a single shell test script and return its result dictionary."""
    logger.debug("Running: %s", script_path)

        result = subprocess.run(
            [shell, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        status = "PASS" if result.returncode == 0 else "FAIL"
        return {
            "name": script_path.name,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": status,
        }
    except subprocess.TimeoutExpired:
        return {
            "name": script_path.name,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "status": "TIMEOUT",
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "name": script_path.name,
            "exit_code": -2,
            "stdout": "",
            "stderr": str(exc),
            "status": "ERROR",
        }


def run_all_tests(scripts: List[Path], shell: str, max_workers: int = 4, timeout: int = 30) -> List[Dict]:
    """Run all tests concurrently and return a list of result dictionaries."""
    logger.info("Running %d tests with %d workers...", len(scripts), max_workers)
    results: List[Dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_test, s, shell, timeout): s for s in scripts}
        for future in as_completed(futures):
            result = future.result()
            status = result["status"]
            color = {
                "PASS": Colors.GREEN,
                "FAIL": Colors.RED,
                "TIMEOUT": Colors.YELLOW,
                "ERROR": Colors.RED,
            }.get(status, Colors.RESET)
            logger.info("%s[%s]%s %s", color, status, Colors.RESET, safe_name(result["name"]))
            results.append(result)
    return results


def save_json_report(results: List[Dict], filename: str = "test_results.json") -> None:
    """Write test results to a JSON file."""
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)


def save_html_report(results: List[Dict], filename: str = "test_results.html") -> None:
    """Write a minimal HTML summary of test results."""
    with open(filename, "w") as f:
        f.write("<html><body><h1>Test Report</h1><table border='1'>")
        f.write("<tr><th>Test</th><th>Status</th><th>Exit Code</th></tr>")
        for r in results:
            color = {
                "PASS": "green",
                "FAIL": "red",
                "TIMEOUT": "orange",
                "ERROR": "darkred",
            }.get(r["status"], "black")
            f.write(
                f"<tr><td>{r['name']}</td><td style='color:{color}'>{r['status']}</td><td>{r['exit_code']}</td></tr>"
            )
        f.write("</table></body></html>")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run Bash test scripts.")
    parser.add_argument("--directory", "-d", default="tests", help="Directory to search for test scripts")
    parser.add_argument("--shell", default="bash", help="Shell to use (default: bash)")
    parser.add_argument("--tags", nargs="*", help="Only run tests matching one or more tags like @network @slow")
    parser.add_argument("--workers", type=int, default=4, help="Max parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per test in seconds")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Write results to test_results.json")
    parser.add_argument("--html", action="store_true", help="Write HTML test summary")
    return parser.parse_args()


def main() -> None:
    """Entry point for the command line interface."""
    args = parse_args()
    setup_logger(args.verbose)
    scripts = find_test_scripts(args.directory, args.tags)
    if not scripts:
        logger.warning("No test scripts found.")
        return
    results = run_all_tests(scripts, args.shell, args.workers, args.timeout)
    passed = sum(1 for r in results if r["status"] == "PASS")
    logger.info("Summary: %d/%d passed", passed, len(results))
    if args.json:
        save_json_report(results)
        logger.info("JSON report saved.")
    if args.html:
        save_html_report(results)
        logger.info("HTML report saved.")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
