param([string]$MigrateFrom)
# One-time Windows setup: collector Python environment and web dependencies.
# -MigrateFrom <old project root> also copies the saved Facebook session and
# collection history from an older layout (old\local-media\...), without deleting them.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$collector = Join-Path $projectRoot 'collector'
$web = Join-Path $projectRoot 'web'
$python = Join-Path $collector '.venv\Scripts\python.exe'

Write-Host '1/3 Collector Python environment...'
if (-not (Test-Path -LiteralPath $python)) {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) { & py.exe -3 -m venv (Join-Path $collector '.venv') }
    else { & python.exe -m venv (Join-Path $collector '.venv') }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create collector\.venv. Install Python 3.10+ and retry.' }
}
& $python -m pip install --disable-pip-version-check -r (Join-Path $collector 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Collector dependency installation failed.' }
& $python -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw 'Playwright browser installation failed.' }

Write-Host '2/3 Web dependencies...'
if (-not (Test-Path -LiteralPath (Join-Path $web 'node_modules\vinext\dist\cli.js'))) {
    Push-Location $web
    try {
        if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'npm was not found. Install Node.js 22.13+ and reopen PowerShell.' }
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed. Node.js 22.13+ is required.' }
    } finally { Pop-Location }
}

Write-Host '3/3 Local data...'
if ($MigrateFrom) {
    $old = Join-Path $MigrateFrom 'local-media'
    foreach ($name in 'facebook-browser', 'crawl-data') {
        $source = Join-Path $old $name
        if (Test-Path -LiteralPath $source) {
            & robocopy.exe $source (Join-Path $collector $name) /E /XO /NFL /NDL /NJH /NJS /NP | Out-Null
            if ($LASTEXITCODE -ge 8) { throw "Copying $name failed." }
            Write-Host "Copied $name from $old"
        }
    }
    $global:LASTEXITCODE = 0
}
Write-Host 'Setup complete. Next: scripts\deploy-inference.ps1 (GPU host), then scripts\start.ps1' -ForegroundColor Green
