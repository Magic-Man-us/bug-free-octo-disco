# bug-free-octo-disco
A simple Python-based test runner for shell scripts. Tests are discovered in the
`tests/` directory by default and follow the pattern `test_*.sh`.

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
- `--coverage`           Collect coverage with `kcov` if installed

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