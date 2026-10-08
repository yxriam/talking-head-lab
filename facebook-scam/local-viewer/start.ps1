param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workDir = Join-Path $projectRoot 'work\local-viewer'
New-Item -ItemType Directory -Path $workDir -Force | Out-Null
$viewerUrl = 'http://127.0.0.1:8765'
try {
  $health = Invoke-RestMethod "$viewerUrl/api/health" -TimeoutSec 2
  if ($health.app -ne 'facebook-local-results') { throw 'Port 8765 belongs to another application.' }
  if (-not $NoBrowser) { Start-Process $viewerUrl -WindowStyle Hidden }
  exit 0
} catch { }
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$nodePath = if ($nodeCommand) { $nodeCommand.Source } else { $null }
if (-not $nodePath) {
  $bundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
  if (Test-Path -LiteralPath $bundledNode) { $nodePath = $bundledNode }
}
if (-not $nodePath) { throw 'Node.js was not found. Install Node.js or add node.exe to PATH, then try again.' }
$env:FACEBOOK_VIEWER_PORT = '8765'
$process = Start-Process -FilePath $nodePath -ArgumentList @('"' + (Join-Path $PSScriptRoot 'server.mjs') + '"') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $workDir 'server.log') -RedirectStandardError (Join-Path $workDir 'server-error.log')
$process.Id | Set-Content -LiteralPath (Join-Path $workDir 'server.pid')
for ($attempt = 0; $attempt -lt 30; $attempt++) {
  Start-Sleep -Milliseconds 200
  $process.Refresh()
  if ($process.HasExited) { throw "Viewer failed to start. Read $workDir\server-error.log" }
  try {
    $health = Invoke-RestMethod "$viewerUrl/api/health" -TimeoutSec 1
    if ($health.app -eq 'facebook-local-results') { if (-not $NoBrowser) { Start-Process $viewerUrl -WindowStyle Hidden }; exit 0 }
  } catch { }
}
throw "Viewer did not become ready. Read $workDir\server-error.log"
