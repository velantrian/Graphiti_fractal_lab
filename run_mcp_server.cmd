@echo off
setlocal enabledelayedexpansion

REM Ensure UTF-8 output (helps avoid mojibake in Cursor Output)
chcp 65001 >nul

REM Always run from the directory where this script lives (project root)
set "ROOT=%~dp0"
cd /d "%ROOT%"

set "PY=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [mcp] ERROR: Python venv not found: "%PY%"
  echo [mcp] Fix: create venv and install deps:
  echo [mcp]   python -m venv .venv
  echo [mcp]   .venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)

REM Run MCP server
"%PY%" -m mcp_server


