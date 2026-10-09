param([ValidateSet('setup-models','install-generators','sync-runtime','activate-api','continue-deploy','verify-voice','verify-video','install-detectors','install-npr','install-gend','install-echomimic','verify-detectors','inspect-api')][string]$Task = 'setup-models')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$logs = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$repo = ((& C:\Windows\System32\wsl.exe -d Ubuntu-22.04 -u root -- wslpath -a ($projectRoot -replace '\\', '/')) -join '').Trim()
$prepareLog = Join-Path $logs 'linux-prepare.txt'
$script = Get-ChildItem -LiteralPath (Split-Path $PSScriptRoot -Parent) -Recurse -Filter "$Task.sh" | Select-Object -First 1
if (-not $script) { throw "Task script $Task.sh was not found under inference." }
$scriptPath = "$repo/inference/$($script.Directory.Name)/$Task.sh"
$deadline = (Get-Date).AddMinutes(15)
while (-not ((Get-Content -LiteralPath $prepareLog -Raw) -match 'PREPARE_COMPLETE')) {
    if ((Get-Date) -gt $deadline) { throw 'Linux prerequisites did not finish in time.' }
    Start-Sleep -Seconds 5
}
$log = Join-Path $logs "$Task.log"
$errorLog = Join-Path $logs "$Task-error.log"
$start = New-Object System.Diagnostics.ProcessStartInfo
$start.FileName = 'C:\Windows\System32\wsl.exe'
$start.Arguments = "-d Ubuntu-22.04 -u root --exec bash $scriptPath"
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$start.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$start.StandardErrorEncoding = [System.Text.Encoding]::UTF8
$process = [System.Diagnostics.Process]::Start($start)
$errors = $process.StandardError.ReadToEndAsync()
$writer = New-Object System.IO.StreamWriter($log, $false, [System.Text.Encoding]::UTF8)
$writer.AutoFlush = $true
try {
    while (($character = $process.StandardOutput.Read()) -ne -1) { $writer.Write([char]$character) }
} finally { $writer.Dispose() }
$process.WaitForExit()
$errors.Result | Out-File -LiteralPath $errorLog -Encoding utf8
"ExitCode: $($process.ExitCode)" | Out-File -LiteralPath $log -Append -Encoding utf8
