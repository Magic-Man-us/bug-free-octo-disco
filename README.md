# bug-free-octo-disco
A simple Python-based test runner for shell scripts. Tests are discovered in the
`tests/` directory by default and follow the pattern `test_*.sh`.

Test scripts use `#!/usr/bin/env bash` shebangs so the correct Bash
installation is located automatically.

On macOS and Windows, ensure a Bash environment is available (e.g. via
Homebrew, WSL or Git Bash) and that it appears on your `PATH`.

## Requirements

Install dependencies via pip:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 test_runner.py [PATTERN ...] [options]
```

### Options

- `-d, --directory DIR`  Directory containing test scripts (default: `tests`)
- `-t, --timeout SECS`   Per-test timeout in seconds (default: 30)
- `--shell SHELL`       Execute tests with the given shell (e.g. `bash`, `zsh`).
  If omitted, each script's shebang is used.
- `--coverage`           Collect coverage with `kcov` if installed
- `--json`              Write JSON results to `test_results.json`
- `--html`              Write HTML summary to `test_results.html`
- `--report-dir DIR`    Output directory for reports

If one or more `PATTERN` arguments are provided, only tests matching those glob
patterns will be executed.

## Example

Run all tests:


```bash
python3 test_runner.py
```

Run a specific test:

```bash
python3 test_runner.py test_success.sh
```

### Developer tests

Unit tests for `test_runner.py` are located in the `pytests/` directory and can
be executed with `pytest`:

```bash
pytest pytests
```

### Reporting

Use `--json` or `--html` to generate reports in JSON or HTML format. Each
result includes the exit code and duration so you can track metrics over time.
