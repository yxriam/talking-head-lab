param()
# Starts the Windows collector API (collection + account analysis bridge) on 127.0.0.1:8003.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$collector = Join-Path $projectRoot 'collector'
$logs = Join-Path $projectRoot 'logs'
$python = Join-Path $collector '.venv\Scripts\python.exe'
$uvicorn = Join-Path $collector '.venv\Scripts\uvicorn.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'The collector environment is missing. Run scripts\setup.ps1 first.'
}
try {
    $status = Invoke-RestMethod 'http://127.0.0.1:8003/crawl/health' -TimeoutSec 2
    if ($status.status -eq 'ok') { Write-Host 'Facebook collector is already running.'; return }
} catch {}
& $python -c 'import playwright, fastapi, uvicorn, httpx'
if ($LASTEXITCODE -ne 0) {
    throw 'Collector dependencies are incomplete. Run scripts\setup.ps1 again.'
}
New-Item -ItemType Directory -Force -Path $logs | Out-Null
if (-not (Test-Path -LiteralPath $uvicorn)) { throw 'The collector uvicorn entry point is missing. Run scripts\setup.ps1 first.' }
Start-Process -FilePath $uvicorn -WorkingDirectory $collector `
    -ArgumentList @('crawl_server:app', '--host', '127.0.0.1', '--port', '8003') `
    -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'collector.log') `
    -RedirectStandardError (Join-Path $logs 'collector-error.log')
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    try {
        $status = Invoke-RestMethod 'http://127.0.0.1:8003/crawl/health' -TimeoutSec 2
        if ($status.status -eq 'ok') { Write-Host 'Facebook collector: http://127.0.0.1:8003/crawl/health'; return }
    } catch {}
    Start-Sleep -Seconds 1
}
throw 'Facebook collector startup failed. Check logs\collector-error.log.'
