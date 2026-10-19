[CmdletBinding()]
param(
    [int]$Port = 8080,
    [switch]$NoBrowser,
    [int]$HealthTimeoutSeconds = 40,
    [string]$DatabasePath = ""
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repositoryRoot

$venvDirectory = Join-Path $repositoryRoot ".venv"
$venvPython = Join-Path $venvDirectory "Scripts\python.exe"
$requirementsPath = Join-Path $repositoryRoot "requirements.txt"
$createdEnvironment = $false

function Get-PythonVersion {
    param(
        [string]$FilePath,
        [string[]]$PrefixArguments = @()
    )

    $versionArguments = @($PrefixArguments) + @(
        "-c",
        "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    )
    $version = & $FilePath @versionArguments 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    return ($version | Select-Object -Last 1).Trim()
}

# Versioni supportate, dalla preferita: allineate a requires-python in pyproject.toml.
$supportedMinorVersions = @("3.15", "3.14", "3.13")
$supportedVersionPattern = "^3\.(13|14|15)\.\d+$"
$supportedVersionsLabel = "Python 3.13, 3.14 o 3.15"

function Find-SupportedPython {
    $foundVersions = @()

    $pyLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        foreach ($minorVersion in $supportedMinorVersions) {
            $version = Get-PythonVersion -FilePath $pyLauncher.Source -PrefixArguments @("-$minorVersion")
            if ($version -match "^$([regex]::Escape($minorVersion))\.\d+$") {
                return @{
                    FilePath = $pyLauncher.Source
                    PrefixArguments = @("-$minorVersion")
                    Version = $version
                }
            }
        }
    }

    foreach ($commandName in @("python.exe", "python3.exe")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }
        $version = Get-PythonVersion -FilePath $command.Source
        if ($version) {
            $foundVersions += $version
        }
        if ($version -match $supportedVersionPattern) {
            return @{
                FilePath = $command.Source
                PrefixArguments = @()
                Version = $version
            }
        }
    }

    if ($foundVersions) {
        throw "Trovato Python $($foundVersions -join ', '), non supportato per la demo: installare $supportedVersionsLabel e rilanciare start_demo.bat."
    }
    throw "Python non trovato. Installare $supportedVersionsLabel e rilanciare start_demo.bat."
}

if (Test-Path -LiteralPath $venvDirectory) {
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw "La cartella .venv esiste ma e incompleta. Rimuoverla e rilanciare start_demo.bat con $supportedVersionsLabel."
    }
    $venvVersion = Get-PythonVersion -FilePath $venvPython
    if ($venvVersion -notmatch $supportedVersionPattern) {
        throw "La .venv usa Python $venvVersion, non supportato: rimuoverla e rilanciare start_demo.bat con $supportedVersionsLabel."
    }
    Write-Host "Ambiente locale rilevato: Python $venvVersion. Nessuna reinstallazione dipendenze."
}
else {
    $launcher = Find-SupportedPython
    Write-Host "Creazione .venv locale con Python $($launcher.Version)..."
    & $launcher.FilePath @($launcher.PrefixArguments) -m venv $venvDirectory
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw "Creazione .venv non riuscita."
    }
    $createdEnvironment = $true

    Write-Host "Installazione iniziale dipendenze da requirements.txt..."
    & $venvPython -m pip install --disable-pip-version-check -r $requirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw "Installazione dipendenze non riuscita. Il server non verra avviato."
    }
}

$dependencyProbe = @"
import fastapi
import httpx
import jinja2
import multipart
import openpyxl
import pypdf
import docx
import extract_msg
import sqlalchemy
import alembic
import uvicorn
"@

& $venvPython -c $dependencyProbe
if ($LASTEXITCODE -ne 0) {
    if ($createdEnvironment) {
        throw "Verifica dipendenze fallita dopo il setup. Il server non verra avviato."
    }
    throw "La .venv esistente non contiene tutte le dipendenze. Rimuoverla e rilanciare start_demo.bat per il setup iniziale."
}

& $venvPython -m pip check --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    throw "La .venv contiene dipendenze incoerenti. Il server non verra avviato."
}

$demoDataRoot = Join-Path $repositoryRoot "data\demo"
if ([string]::IsNullOrWhiteSpace($DatabasePath)) {
    $resolvedDatabasePath = Join-Path $demoDataRoot "brofind_demo.db"
}
elseif ([System.IO.Path]::IsPathRooted($DatabasePath)) {
    $resolvedDatabasePath = [System.IO.Path]::GetFullPath($DatabasePath)
}
else {
    $resolvedDatabasePath = [System.IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot $DatabasePath)
    )
}

$env:BROFIND_RUNTIME = "demo"
$env:BROFIND_DATABASE_PATH = $resolvedDatabasePath
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue

$logDirectory = Join-Path $demoDataRoot "logs"
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$stdoutLog = Join-Path $logDirectory "server.stdout.log"
$stderrLog = Join-Path $logDirectory "server.stderr.log"

$serverArguments = @(
    "-m", "uvicorn", "app.main:app",
    "--host", "127.0.0.1",
    "--port", $Port.ToString()
)
$serverParameters = @{
    FilePath = $venvPython
    ArgumentList = $serverArguments
    WorkingDirectory = $repositoryRoot
    PassThru = $true
    WindowStyle = "Hidden"
    RedirectStandardOutput = $stdoutLog
    RedirectStandardError = $stderrLog
}

Write-Host "Avvio Cockpit in runtime demo..."
$serverProcess = Start-Process @serverParameters

$healthUrl = "http://127.0.0.1:$Port/health"
$deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
$healthy = $false
$health = $null

try {
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
        $serverProcess.Refresh()
        if ($serverProcess.HasExited) {
            throw "Uvicorn e terminato prima di rendere disponibile /health."
        }
        try {
            $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
            $expectedDatabaseName = Split-Path -Leaf $resolvedDatabasePath
            if (
                $health.status -eq "ok" -and
                $health.runtime -eq "demo" -and
                $health.database -eq $expectedDatabaseName
            ) {
                $healthy = $true
                break
            }
        }
        catch {
            # Server non ancora pronto: continua fino al timeout.
        }
    }

    if (-not $healthy) {
        throw "Health check non valido entro $HealthTimeoutSeconds secondi. Il browser non verra aperto."
    }

    $pidPath = Join-Path $demoDataRoot "cockpit.pid"
    Set-Content -LiteralPath $pidPath -Value $serverProcess.Id -Encoding ASCII
    Write-Host "DEMO_READY PID=$($serverProcess.Id) URL=http://127.0.0.1:$Port DATABASE=$resolvedDatabasePath"

    if (-not $NoBrowser) {
        Start-Process "http://127.0.0.1:$Port"
    }
}
catch {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Error $_
    if (Test-Path -LiteralPath $stderrLog) {
        Write-Host "--- server.stderr.log ---"
        Get-Content -LiteralPath $stderrLog -Tail 30
    }
    throw
}
