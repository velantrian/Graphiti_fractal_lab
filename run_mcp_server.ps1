$ErrorActionPreference = "Stop"

# Always run from the directory where this script lives (project root)
Set-Location -LiteralPath $PSScriptRoot

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) {
  Write-Host "[mcp] ERROR: Python venv not found: `"$py`""
  Write-Host "[mcp] Fix: create venv and install deps:"
  Write-Host "[mcp]   python -m venv .venv"
  Write-Host "[mcp]   .venv\Scripts\python.exe -m pip install -r requirements.txt"
  exit 1
}

& $py -m mcp_server


