#Requires -RunAsAdministrator

$ErrorActionPreference = 'Stop'
$distro = 'Ubuntu-22.04'
$listenAddress = '127.0.0.1'
$port = 8002

$addresses = ((& wsl.exe -d $distro -u root -- hostname -I) -join ' ').Trim().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries)
$wslAddress = $addresses | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -First 1
if (-not $wslAddress) { throw 'Could not read the Ubuntu IPv4 address.' }

$route = ((& wsl.exe -d $distro -u root -- ip route show default) -join ' ')
$gatewayMatch = [regex]::Match($route, 'default via (\d+\.\d+\.\d+\.\d+)')
if (-not $gatewayMatch.Success) { throw 'Could not read the WSL-to-Windows gateway address.' }
$gateway = $gatewayMatch.Groups[1].Value

# Replace only this project's loopback port proxy on port 8002.
& netsh.exe interface portproxy delete v4tov4 listenaddress=$listenAddress listenport=$port | Out-Null
& netsh.exe interface portproxy add v4tov4 listenaddress=$listenAddress listenport=$port connectaddress=$wslAddress connectport=$port | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Failed to create the port 8002 proxy.' }

if (Get-Command Get-NetFirewallHyperVRule -ErrorAction SilentlyContinue) {
    Get-NetFirewallHyperVRule -Name 'MediaAppLocalApi' -ErrorAction SilentlyContinue | Remove-NetFirewallHyperVRule
    New-NetFirewallHyperVRule `
        -Name 'MediaAppLocalApi' -DisplayName 'Media App Local API' -Direction Inbound `
        -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' `
        -Protocol TCP -LocalPorts $port -RemoteAddresses $gateway -Action Allow | Out-Null
}

Write-Host "Port proxy updated: ${listenAddress}:$port -> ${wslAddress}:$port" -ForegroundColor Green
