@echo off
REM Simple wrapper around the Python pipeline orchestrator.

if "%~1"=="" (
    echo Usage: run_pipeline.bat ^<input.pdf^> [--skip-ai] [...]
    exit /b 1
)

set "INPUT_PDF=%~1"
shift

if not exist "%INPUT_PDF%" (
    echo Input file "%INPUT_PDF%" not found.
    exit /b 1
)

python -m pipeline "%INPUT_PDF%" %*
