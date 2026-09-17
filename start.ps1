$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pythonCandidates = @((Join-Path $PSScriptRoot '.venv\Scripts\python.exe'), $bundledPython)
$systemPython = Get-Command python -ErrorAction SilentlyContinue
if ($systemPython) { $pythonCandidates += $systemPython.Source }
foreach ($candidate in $pythonCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        & $candidate -c 'import openpyxl' 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $candidate (Join-Path $PSScriptRoot 'app.py')
            exit $LASTEXITCODE
        }
    }
}
Write-Host 'Python 3.10+ and openpyxl are required. See README.md.'
Read-Host 'Press Enter to close'
exit 1
