param([switch]$NoRestart)
# Copies the inference runtime from this checkout to the WSL GPU host
# (/opt/media-app/local-media), verifies SHA256, restarts the API and checks health.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$distro = 'Ubuntu-22.04'
$repo = ((& wsl.exe -d $distro -u root -- wslpath -a ($projectRoot -replace '\\', '/')) -join '').Trim()
if (-not $repo) { throw 'Could not translate the project path for WSL.' }
& wsl.exe -d $distro -u root -- bash "$repo/inference/deploy/sync-runtime.sh"
if ($LASTEXITCODE -ne 0) { throw 'Runtime sync failed; the running service was not restarted.' }
if ($NoRestart) { return }
& wsl.exe -d $distro -u root -- systemctl restart local-media.service
if ($LASTEXITCODE -ne 0) { throw 'Service restart failed. Run: wsl -d Ubuntu-22.04 -u root -- systemctl status local-media.service' }
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    & wsl.exe -d $distro -u root -- curl -fsS -o /dev/null http://127.0.0.1:8002/health
    if ($LASTEXITCODE -eq 0) { Write-Host 'Inference API is healthy.' -ForegroundColor Green; return }
    Start-Sleep -Seconds 1
}
throw 'The inference API did not become healthy after the restart.'
