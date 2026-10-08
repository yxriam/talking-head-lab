param([ValidateSet('setup-models','install-generators','sync-runtime','activate-api','continue-deploy','verify-voice','verify-video','install-detectors','install-npr','install-gend','install-echomimic','verify-detectors','inspect-api')][string]$Task = 'setup-models')
$ErrorActionPreference = 'Stop'
$prepareLog = Join-Path $PSScriptRoot 'linux-prepare.txt'
$deadline = (Get-Date).AddMinutes(15)
while (-not ((Get-Content -LiteralPath $prepareLog -Raw) -match 'PREPARE_COMPLETE')) {
    if ((Get-Date) -gt $deadline) { throw 'Linux prerequisites did not finish in time.' }
    Start-Sleep -Seconds 5
}
$log = Join-Path $PSScriptRoot "$Task.log"
$errorLog = Join-Path $PSScriptRoot "$Task-error.log"
$start = New-Object System.Diagnostics.ProcessStartInfo
$start.FileName = 'C:\Windows\System32\wsl.exe'
$start.Arguments = "-d Ubuntu-22.04 -u root --exec bash /mnt/d/project/cv/local-media/$Task.sh"
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
