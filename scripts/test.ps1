param([switch]$SkipWeb)
# Runs every program test that needs no GPU, then builds the web app.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $projectRoot 'collector\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts\setup.ps1 first.' }
# Test-only dependencies of the inference modules; a no-op when already installed.
& $python -m pip install --disable-pip-version-check -q python-multipart numpy
if ($LASTEXITCODE -ne 0) { throw 'Could not install the test-only dependencies.' }
Push-Location $projectRoot
try {
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Program tests failed.' }
} finally { Pop-Location }
function Resolve-Node {
    $command = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $bundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
    if (Test-Path $bundledNode) { return $bundledNode }
    throw 'Node.js 22 was not found. Install Node.js 22 LTS, reopen PowerShell, and run this script again.'
}
if (-not $SkipWeb) {
    $node = Resolve-Node
    Push-Location (Join-Path $projectRoot 'web')
    try {
        & $node 'node_modules/vinext/dist/cli.js' build
        if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
    } finally { Pop-Location }
}
Write-Host 'All checks passed.' -ForegroundColor Green
