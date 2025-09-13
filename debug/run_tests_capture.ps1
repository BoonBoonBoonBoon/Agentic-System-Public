# Run tests and capture stdout+stderr to debug/test_output.txt
# Usage: Open PowerShell in repo root and run: .\debug\run_tests_capture.ps1

$ErrorActionPreference = 'Stop'
Write-Output "Running: python -m unittest discover -v tests"
python -m unittest discover -v tests > debug\test_output.txt 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Output "Tests finished with non-zero exit code: $LASTEXITCODE"
} else {
    Write-Output "Tests finished OK"
}

Write-Output "--- Tail of debug/test_output.txt ---"
Get-Content debug\test_output.txt -Tail 300

Write-Output "--- Environment summary ---"
python -c "import sys, json, platform; print('Python', sys.version); print(platform.platform())"
pip list | Out-File -FilePath debug\pip_list.txt -Encoding utf8
Write-Output "Wrote pip list to debug/pip_list.txt"

Write-Output "If a test hangs: press Ctrl+C in the terminal; if it doesn't respond, run:`Get-Process -Name python | Stop-Process -Force` to terminate python processes.`"
