param([switch]$IncludeBackend)
# Stops the web app (3100) and the collector (8003) started from any checkout.
# The GPU backend keeps running unless -IncludeBackend is given.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
foreach ($port in 3100, 8003) {
    $owners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        $process = Get-Process -Id $owner -ErrorAction SilentlyContinue
        if ($process -and $process.ProcessName -match '^(node|python|pythonw)$') {
            Stop-Process -Id $owner -Force
            Write-Host "Stopped $($process.ProcessName) on port $port (PID $owner)."
        } elseif ($process) {
            Write-Host "Port $port is held by $($process.ProcessName) (PID $owner); left untouched."
        }
    }
}
if ($IncludeBackend) {
    & wsl.exe -d Ubuntu-22.04 -u root -- systemctl stop local-media.service
    $pidFile = Join-Path $projectRoot 'logs\wsl-keeper.pid'
    if (Test-Path -LiteralPath $pidFile) {
        $keeper = Get-Process -Id (Get-Content $pidFile | Select-Object -First 1) -ErrorAction SilentlyContinue
        if ($keeper -and $keeper.ProcessName -eq 'wsl') { Stop-Process -Id $keeper.Id -Force }
        Remove-Item -LiteralPath $pidFile -Force
    }
    Write-Host 'Stopped the GPU backend service.'
}
