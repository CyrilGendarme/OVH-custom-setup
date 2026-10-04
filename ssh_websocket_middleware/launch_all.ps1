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

# Launch Rekordbox and wait until it is fully launched (main window up and responding)
$RekordboxExePath = Get-ChildItem -Path "C:\Program Files\rekordbox\*\rekordbox.exe" -ErrorAction SilentlyContinue |
    Sort-Object { $_.Directory.Name } -Descending | Select-Object -First 1 -ExpandProperty FullName
$RekordboxTimeoutSeconds = 180
$rekordboxRunning = Get-Process -Name "rekordbox" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
if (-not $rekordboxRunning) {
    if (-not $RekordboxExePath) {
        throw "Rekordbox not found under C:\Program Files\rekordbox"
    }
    # Created through WMI so Rekordbox is not a child of this console: closing the CLI windows will not close it
    $created = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine      = "`"$RekordboxExePath`""
        CurrentDirectory = (Split-Path -Parent $RekordboxExePath)
    }
    if ($created.ReturnValue -ne 0) { throw "Failed to launch Rekordbox (WMI return code $($created.ReturnValue))" }
    Write-Host "Launched Rekordbox"
}
Write-Host "Waiting for Rekordbox to be fully launched..."
$deadline = (Get-Date).AddSeconds($RekordboxTimeoutSeconds)
$rekordboxReady = $false
while ((Get-Date) -lt $deadline) {
    $rb = Get-Process -Name "rekordbox" -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.Responding -and $_.MainWindowTitle } |
        Select-Object -First 1
    if ($rb) { $rekordboxReady = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $rekordboxReady) {
    throw "Rekordbox did not become ready within $RekordboxTimeoutSeconds seconds"
}
Write-Host "Rekordbox window detected, waiting 20 seconds for it to finish loading..."
Start-Sleep -Seconds 20
Write-Host "Rekordbox is ready"

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