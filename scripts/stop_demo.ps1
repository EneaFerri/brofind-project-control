[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
$pidPath = Join-Path $repositoryRoot "data\demo\cockpit.pid"
$expectedInvocation = "(?i)^\s*`"?$([regex]::Escape($venvPython))`"?\s+-m\s+uvicorn\s+app\.main:app(\s|$)"
$expectedPort = '(?i)(^|\s)--port\s+8080(\s|$)'

$listeners = @(Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue)
if (-not $listeners) {
    Write-Host "Nessun server in ascolto sulla porta 8080."
    exit 0
}

$demoProcessIds = [System.Collections.Generic.HashSet[int]]::new()
$stopped = 0
foreach ($listener in $listeners) {
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
    if (-not $processInfo) {
        continue
    }

    $isDemoServer = (
        $processInfo.CommandLine -match $expectedInvocation -and
        $processInfo.CommandLine -match $expectedPort
    )
    if (-not $isDemoServer) {
        Write-Warning "La porta 8080 e occupata da un processo non riconosciuto come Cockpit demo (PID $($listener.OwningProcess)); non viene terminato."
        continue
    }

    [void]$demoProcessIds.Add([int]$listener.OwningProcess)
    $parentProcessId = $processInfo.ParentProcessId
    while ($parentProcessId) {
        $parentInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $parentProcessId" -ErrorAction SilentlyContinue
        if (-not $parentInfo -or $parentInfo.CommandLine -notmatch $expectedInvocation -or $parentInfo.CommandLine -notmatch $expectedPort) {
            break
        }
        [void]$demoProcessIds.Add([int]$parentInfo.ProcessId)
        $parentProcessId = $parentInfo.ParentProcessId
    }
}

foreach ($demoProcessId in $demoProcessIds) {
    Stop-Process -Id $demoProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "Cockpit demo arrestato (PID $demoProcessId)."
    $stopped++
}

if ($stopped -gt 0 -and (Test-Path -LiteralPath $pidPath)) {
    Remove-Item -LiteralPath $pidPath -Force
}

if ($stopped -eq 0) {
    Write-Error "Nessun server demo Cockpit identificato sulla porta 8080. Nessun processo e stato terminato."
}
