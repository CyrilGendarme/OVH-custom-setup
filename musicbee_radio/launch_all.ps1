# run-all.ps1

$ErrorActionPreference = "Stop"

# Launch OBS Studio first
$OBSExePath = "C:\Program Files\obs-studio\bin\64bit\obs64.exe"
if (Test-Path -LiteralPath $OBSExePath) {
    Start-Process -FilePath $OBSExePath -WorkingDirectory (Split-Path -Parent $OBSExePath)
    Write-Host "Launched OBS Studio"
} else {
    throw "OBS Studio not found at $OBSExePath"
}

# Wait until OBS is fully started (WebSocket server accepting connections) before anything else
$OBSWebSocketPort = 4455
$OBSTimeoutSeconds = 120
Write-Host "Waiting for OBS to be fully launched..."
$deadline = (Get-Date).AddSeconds($OBSTimeoutSeconds)
$obsReady = $false
while ((Get-Date) -lt $deadline) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.Connect("127.0.0.1", $OBSWebSocketPort)
        $obsReady = $true
    } catch {
        Start-Sleep -Seconds 1
    } finally {
        $client.Close()
    }
    if ($obsReady) { break }
}
if (-not $obsReady) {
    throw "OBS did not become ready within $OBSTimeoutSeconds seconds (WebSocket port $OBSWebSocketPort)"
}
Start-Sleep -Seconds 2
Write-Host "OBS is ready"

# Launch MusicBee
$MusicBeeExePath = "C:\Program Files (x86)\MusicBee\MusicBee.exe"
if (Test-Path -LiteralPath $MusicBeeExePath) {
    Start-Process -FilePath $MusicBeeExePath
    Write-Host "Launched MusicBee"
} else {
    Write-Host "Warning: MusicBee not found at $MusicBeeExePath"
}

# Paths
$Python = "python"    # Or: "C:\path\to\venv\Scripts\python.exe"

$ListenerScriptPath = "C:\Users\User\Desktop\musique\online\dj gratuit\ovh\musicbee_radio\listener.py"
$RandomEventsScriptPath = "C:\Users\User\Desktop\musique\online\dj gratuit\ovh\obs_helpers\random_events.py"

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

function Start-PythonScript {
    param (
        [Parameter(Mandatory = $true)]
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
`$env:PYTHONDONTWRITEBYTECODE='1'
& '$Python' -B '$resolvedScriptPath'
"@

    Start-Process powershell -WorkingDirectory $scriptDirectory -ArgumentList "-NoExit", "-Command", $command
}

Start-PythonScript $ListenerScriptPath
Start-PythonScript $RandomEventsScriptPath