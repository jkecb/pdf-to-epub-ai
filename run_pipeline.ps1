# PowerShell wrapper for the Python orchestrator.

Param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $InputPdf,

    [Parameter(Position = 1)]
    [string[]] $ExtraArgs
)

if (-not (Test-Path $InputPdf)) {
    Write-Host "Input file '$InputPdf' not found." -ForegroundColor Red
    exit 1
}

python -m pipeline $InputPdf @ExtraArgs
