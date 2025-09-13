Debug helpers for this repo

Purpose
- Central place for quick debugging scripts and run-capture artifacts.

Files
- `run_tests_capture.ps1` — PowerShell helper to run tests, capture stdout/stderr, and show the tail.

How to use
1. Open PowerShell in the repo root.
2. Run the script to capture tests: `.
un_tests_capture.ps1`
3. Inspect `debug/test_output.txt` for full logs.

Common tasks to add here
- scripts to reproduce failing tests
- scripts to capture environment (pip/venv info)
- small helper scripts to kill stray processes or dump logs

Safety
- Delivery or external-send scripts should not be added here; keep debugging artifacts local.

Redaction policy
- Debug run outputs and captured logs that may contain test traces, PII, or tokens are removed from the repository before public release.
- If you need to keep sanitized excerpts for future debugging, create files named `REDACTED_*` which contain only placeholder values and high-level context.
</markdown>
