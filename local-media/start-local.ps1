param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$webRoot = Join-Path $projectRoot 'facebook-scam\video-forensics-web'
$distro = 'Ubuntu-22.04'
$siteUrl = 'http://localhost:3100/studio'

function Resolve-Node {
    $command = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $bundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
    if (Test-Path $bundledNode) { return $bundledNode }
    throw 'Node.js 22 was not found. Install Node.js 22 LTS, reopen PowerShell, and run this script again.'
}

function Test-Url($url, $timeoutSeconds = 2, $headers = @{}) {
    try {
        Invoke-WebRequest $url -UseBasicParsing -TimeoutSec $timeoutSeconds -Headers $headers | Out-Null
        return $true
    } catch { return $false }
}

function Start-WslKeeper {
    $pidFile = Join-Path $PSScriptRoot '.wsl-keeper.pid'
    if (Test-Path $pidFile) {
        $savedPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
        $savedProcess = if ($savedPid) { Get-Process -Id $savedPid -ErrorAction SilentlyContinue }
        if ($savedProcess -and $savedProcess.ProcessName -eq 'wsl') { return }
        Remove-Item -LiteralPath $pidFile -Force
    }
    # A systemd service alone does not keep WSL alive, so hold a hidden WSL client process.
    $keeper = Start-Process -FilePath 'wsl.exe' `
        -ArgumentList @('-d', $distro, '-u', 'root', '--exec', '/usr/bin/sleep', 'infinity') `
        -WindowStyle Hidden -PassThru
    Set-Content -Path $pidFile -Value $keeper.Id -Encoding ascii
}

Write-Host '1/5 Starting the Facebook collector...'
& (Join-Path $PSScriptRoot 'start-crawl.ps1')
Write-Host '2/5 Starting Ubuntu and WSL keepalive...'
Start-WslKeeper

Write-Host '3/5 Starting the local AI backend...'
& wsl.exe -d $distro -u root -- bash -lc 'swapon /swapfile-media 2>/dev/null || true; swapon /swapfile-media-2 2>/dev/null || true'
if ($LASTEXITCODE -ne 0) {
    throw 'Could not initialize the WSL inference swap files.'
}
& wsl.exe -d $distro -u root -- systemctl start local-media.service
if ($LASTEXITCODE -ne 0) {
    throw 'Backend startup failed. Run: wsl -d Ubuntu-22.04 -u root -- systemctl status local-media.service'
}

$wslAddress = ((& wsl.exe -d $distro -u root -- hostname -I) -join ' ').Trim().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries) |
    Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -First 1
if (-not $wslAddress) { throw 'Could not read the Ubuntu IPv4 address.' }
$apiUrl = "http://${wslAddress}:8002/health"
$localHeaders = @{ Host = 'localhost' }

$connected = $false
for ($attempt = 0; $attempt -lt 10; $attempt++) {
    if (Test-Url $apiUrl 2 $localHeaders) { $connected = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $connected) { throw 'The Ubuntu backend is unavailable. See the connection troubleshooting section in the startup guide.' }

Write-Host '4/5 Starting the web app...'
$node = Resolve-Node
if (-not (Test-Url $siteUrl)) {
    $previousMediaApi = $env:LOCAL_MEDIA_API
    $env:LOCAL_MEDIA_API = "http://${wslAddress}:8002"
    Start-Process -FilePath $node `
        -ArgumentList @('node_modules/vinext/dist/cli.js', 'dev', '--host', '127.0.0.1', '--port', '3100') `
        -WorkingDirectory $webRoot -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $PSScriptRoot 'web.log') `
        -RedirectStandardError (Join-Path $PSScriptRoot 'web-error.log')
    $env:LOCAL_MEDIA_API = $previousMediaApi
}

$siteReady = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if (Test-Url $siteUrl) { $siteReady = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $siteReady) { throw 'Web app startup failed. See local-media\web-error.log.' }

Write-Host '5/5 Startup complete.' -ForegroundColor Green
Write-Host "Website: $siteUrl"
Write-Host "Backend: http://${wslAddress}:8002 (proxied through the website)"
if (-not $NoBrowser) { Start-Process $siteUrl }
