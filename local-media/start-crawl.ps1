param()
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Create local-media/.venv and install local-media/requirements-crawl.txt first.'
}
try {
    $status = Invoke-RestMethod 'http://127.0.0.1:8003/crawl/health' -TimeoutSec 2
    if ($status.status -eq 'ok') { Write-Host 'Facebook collector is already running.'; return }
} catch {}
& $python -c 'import playwright, fastapi, uvicorn, httpx'
if ($LASTEXITCODE -ne 0) {
    throw 'Install the collector: local-media\.venv\Scripts\python.exe -m pip install -r local-media\requirements-crawl.txt'
}
Start-Process -FilePath $python -WorkingDirectory $PSScriptRoot `
    -ArgumentList @('-m', 'uvicorn', 'crawl_server:app', '--host', '127.0.0.1', '--port', '8003') `
    -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'crawl.log') `
    -RedirectStandardError (Join-Path $PSScriptRoot 'crawl-error.log')
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    try {
        $status = Invoke-RestMethod 'http://127.0.0.1:8003/crawl/health' -TimeoutSec 2
        if ($status.status -eq 'ok') { Write-Host 'Facebook collector: http://127.0.0.1:8003/crawl/health'; return }
    } catch {}
    Start-Sleep -Seconds 1
}
throw 'Facebook collector startup failed. Check local-media/crawl-error.log.'
