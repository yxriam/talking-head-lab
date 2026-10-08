$ErrorActionPreference = 'Stop'
$pidFile = Join-Path (Split-Path -Parent $PSScriptRoot) 'work\local-viewer\server.pid'
if (-not (Test-Path -LiteralPath $pidFile)) { exit 0 }
$viewerProcessId = [int](Get-Content -LiteralPath $pidFile)
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $viewerProcessId" -ErrorAction SilentlyContinue
$expectedScript = Join-Path $PSScriptRoot 'server.mjs'
if ($process -and $process.Name -eq 'node.exe' -and $process.CommandLine.Contains($expectedScript)) {
  Stop-Process -Id $viewerProcessId
}
