$ErrorActionPreference = "Stop"

$key = Join-Path $env:USERPROFILE ".ssh\codex_autodl_36228"
$port = 36228
$hostName = "connect.bjb1.seetacloud.com"
$user = "root"

Write-Host "Opening SSH tunnel: http://127.0.0.1:7860"
Write-Host "Keep this PowerShell window open while using the WebUI."
ssh -i $key -N -L 7860:127.0.0.1:7860 -p $port "$user@$hostName"
