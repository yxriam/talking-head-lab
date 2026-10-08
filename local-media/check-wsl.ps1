$ErrorActionPreference = 'Continue'
$report = 'D:\project\cv\local-media\wsl-status.txt'
"WSL verification $(Get-Date -Format o)" | Out-File -LiteralPath $report -Encoding utf8
"Account: $([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)" | Out-File -LiteralPath $report -Append -Encoding utf8
function Read-Wsl([string]$arguments) {
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = 'C:\Windows\System32\wsl.exe'
    $start.Arguments = $arguments
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.StandardOutputEncoding = [System.Text.Encoding]::Unicode
    $process = [System.Diagnostics.Process]::Start($start)
    $process.StandardOutput.ReadToEnd() | Out-File -LiteralPath $report -Append -Encoding utf8
    $process.WaitForExit()
}
Read-Wsl '--status'
Read-Wsl '--list --verbose'
Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform | Select-Object FeatureName,State | Out-File -LiteralPath $report -Append -Encoding utf8
Get-CimInstance Win32_ComputerSystem | Select-Object HypervisorPresent | Out-File -LiteralPath $report -Append -Encoding utf8
Get-CimInstance Win32_Processor | Select-Object VirtualizationFirmwareEnabled,SecondLevelAddressTranslationExtensions | Out-File -LiteralPath $report -Append -Encoding utf8
"RebootPending: $(Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending')" | Out-File -LiteralPath $report -Append -Encoding utf8
'CHECK_COMPLETE' | Out-File -LiteralPath $report -Append -Encoding utf8
