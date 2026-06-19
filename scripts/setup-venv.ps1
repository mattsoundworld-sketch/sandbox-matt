$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = py -3.14 -c "import sys; print(sys.executable)" 2>$null
if (-not $python) {
    Write-Error "Python 3.14 was not found. Install it first (for example: winget install -e --id Python.Python.3.14 --scope user)."
}

if (Test-Path ".venv") {
    try {
        Remove-Item -Recurse -Force ".venv"
    }
    catch {
        Write-Warning "Could not remove existing .venv (it may be in use). Close terminals/apps using it and run again."
        throw
    }
}

py -3.14 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

Write-Host "Done. Activate with: .\.venv\Scripts\Activate.ps1"
