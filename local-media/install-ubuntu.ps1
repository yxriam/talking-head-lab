param([switch]$WebDownload, [int]$PreviousProcessId = 0)
$ErrorActionPreference = 'Stop'
if ($PreviousProcessId) {
    $previous = Get-CimInstance Win32_Process -Filter "ProcessId=$PreviousProcessId"
    if ($previous) {
        if ($previous.Name -ne 'wsl.exe' -or $previous.CommandLine -notmatch '--install.*Ubuntu-22.04') {
            throw 'Previous process does not match this Ubuntu installation.'
        }
        Stop-Process -Id $PreviousProcessId
    }
}
$log = 'D:\project\cv\local-media\ubuntu-install.txt'
$start = New-Object System.Diagnostics.ProcessStartInfo
$start.FileName = 'C:\Windows\System32\wsl.exe'
$start.Arguments = '--install -d Ubuntu-22.04 --no-launch'
if ($WebDownload) { $start.Arguments += ' --web-download' }
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.StandardOutputEncoding = [System.Text.Encoding]::Unicode
"Started $(Get-Date -Format o)" | Out-File -LiteralPath $log -Encoding utf8
$process = [System.Diagnostics.Process]::Start($start)
$writer = New-Object System.IO.StreamWriter($log, $true, [System.Text.Encoding]::UTF8)
$writer.AutoFlush = $true
try {
    while (($character = $process.StandardOutput.Read()) -ne -1) { $writer.Write([char]$character) }
} finally { $writer.Dispose() }
$process.WaitForExit()
"ExitCode: $($process.ExitCode)" | Out-File -LiteralPath $log -Append -Encoding utf8
