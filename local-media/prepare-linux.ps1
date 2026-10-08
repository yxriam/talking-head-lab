$ErrorActionPreference = 'Stop'
$log = 'D:\project\cv\local-media\linux-prepare.txt'
$start = New-Object System.Diagnostics.ProcessStartInfo
$start.FileName = 'C:\Windows\System32\wsl.exe'
$start.Arguments = '-d Ubuntu-22.04 -u root --exec bash /mnt/d/project/cv/local-media/prepare-linux.sh'
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.StandardOutputEncoding = [System.Text.Encoding]::UTF8
"Started $(Get-Date -Format o)" | Out-File -LiteralPath $log -Encoding utf8
$process = [System.Diagnostics.Process]::Start($start)
$writer = New-Object System.IO.StreamWriter($log, $true, [System.Text.Encoding]::UTF8)
$writer.AutoFlush = $true
try {
    while (($character = $process.StandardOutput.Read()) -ne -1) { $writer.Write([char]$character) }
} finally { $writer.Dispose() }
$process.WaitForExit()
"ExitCode: $($process.ExitCode)" | Out-File -LiteralPath $log -Append -Encoding utf8
