# run-all.ps1

$ErrorActionPreference = "Stop"

# Paths
$Python = "python"    # Or: "C:\path\to\venv\Scripts\python.exe"

$DataBridgeMainPath = "C:\Users\User\Desktop\ProjetsIT\rekordbox-databridge\main.py"
$WebsocketMiddlewareMainPath = "C:\Users\User\Desktop\musique\online\dj gratuit\ovh\ssh_websocket_middleware\main.py"

function Resolve-ScriptPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Script not found: $Path"
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Stop-ExistingScriptProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath
    )

    $escapedPath = [regex]::Escape($ScriptPath)
    $existing = Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match "python|py" -and
            $_.CommandLine -and
            $_.CommandLine -match $escapedPath
        }

    foreach ($proc in $existing) {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped existing process for $ScriptPath (PID $($proc.ProcessId))"
    }
}

# Function to launch a script with the required environment variables
function Start-PythonScript {
    param (
        [string]$ScriptPath
    )

    $resolvedScriptPath = Resolve-ScriptPath -Path $ScriptPath
    $scriptDirectory = Split-Path -Parent $resolvedScriptPath
    $lastWriteTime = (Get-Item -LiteralPath $resolvedScriptPath).LastWriteTime

    Stop-ExistingScriptProcess -ScriptPath $resolvedScriptPath

    $command = @"
Write-Host "Launching: $resolvedScriptPath"
Write-Host "LastWriteTime: $lastWriteTime"
Set-Location -LiteralPath '$scriptDirectory'
`$env:LAUNCH_SCENARIO='UDP_BROADCAST'
`$env:PRODJ_LOG_LEVEL='ERROR'
`$env:PYTHONDONTWRITEBYTECODE='1'
& '$Python' -B '$resolvedScriptPath'
"@

    Start-Process powershell -WorkingDirectory $scriptDirectory -ArgumentList "-NoExit", "-Command", $command
}

# Launch all scripts
Start-PythonScript $DataBridgeMainPath
Start-PythonScript $WebsocketMiddlewareMainPath