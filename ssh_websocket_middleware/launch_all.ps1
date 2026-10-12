# run-all.ps1

$ErrorActionPreference = "Stop"

# Store process IDs for cleanup
$global:ProcessIds = @()

# Cleanup function to be called on exit
function Cleanup-Processes {
    Write-Host "Cleaning up processes..."
    foreach ($proc_id in $global:ProcessIds) {
        try {
            $process = Get-Process -Id $proc_id -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Terminating process $proc_id..."
                Stop-Process -Id $proc_id -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 500
            }
        } catch {
            # Process already terminated
        }
    }
}

# Register cleanup on script exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup-Processes }

# Wrap entire script execution in try-catch for better error handling
try {
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
Start-Sleep -Seconds 2
Write-Host "Rekordbox is ready"

# Paths
$Python = "python"    # Or: "C:\path\to\venv\Scripts\python.exe"

$DataBridgeMainPath = "C:\Users\User\Desktop\ProjetsIT\rekordbox-databridge\main.py"
$WebsocketMiddlewareMainPath = "C:\Users\User\Desktop\musique\online\dj gratuit\ovh\ssh_websocket_middleware\main.py"
$SESSION_LOG_DIR = "C:\Users\User\Desktop\musique\sets\recordings"

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

# Function to launch a script and track its process ID
function Start-PythonScript {
    param (
        [string]$ScriptPath
    )

    $resolvedScriptPath = Resolve-ScriptPath -Path $ScriptPath
    $scriptDirectory = Split-Path -Parent $resolvedScriptPath
    $lastWriteTime = (Get-Item -LiteralPath $resolvedScriptPath).LastWriteTime

    Stop-ExistingScriptProcess -ScriptPath $resolvedScriptPath

    Write-Host "Launching: $resolvedScriptPath"
    Write-Host "LastWriteTime: $lastWriteTime"
    
    # Build PowerShell command to run the script with environment variables
    $command = @"
Write-Host "Launching: $resolvedScriptPath"
Write-Host "LastWriteTime: $lastWriteTime"
Set-Location -LiteralPath '$scriptDirectory'

`$env:LAUNCH_SCENARIO = 'UDP_BROADCAST_AND_JSON'
`$env:SESSION_LOG_DIR = '$SESSION_LOG_DIR'
`$env:PRODJ_LOG_LEVEL = 'ERROR'
`$env:PYTHONDONTWRITEBYTECODE = '1'

try {
    & '$Python' -B '$resolvedScriptPath'
} catch {
    Write-Host "Script error: `$_" -ForegroundColor Red
    Write-Host "Press Enter to close this window..."
    Read-Host ""
}
"@

    # Launch PowerShell window with -NoExit so it stays open on error
    $process = Start-Process -FilePath powershell `
        -ArgumentList "-NoExit", "-Command", $command `
        -WorkingDirectory $scriptDirectory `
        -PassThru
    
    $global:ProcessIds += $process.Id
    
    Write-Host "Started PowerShell process with PID $($process.Id)"
}

# Launch all scripts
Start-PythonScript $DataBridgeMainPath
Start-PythonScript $WebsocketMiddlewareMainPath

Write-Host "All scripts launched. Press Ctrl+C to gracefully shutdown..."

# Keep the script running and wait for Ctrl+C
try {
    while ($true) {
        # Monitor processes and exit if all are gone
        $allProcessesAlive = $true
        foreach ($proc_id in $global:ProcessIds) {
            $process = Get-Process -Id $proc_id -ErrorAction SilentlyContinue
            if (-not $process) {
                $allProcessesAlive = $false
                Write-Host "⚠️  Process $proc_id has exited" -ForegroundColor Yellow
            }
        }
        
        if (-not $allProcessesAlive) {
            # Remove dead processes from list
            $global:ProcessIds = @($global:ProcessIds | ForEach-Object {
                if (Get-Process -Id $_ -ErrorAction SilentlyContinue) { $_ }
            })
        }
        
        if ($global:ProcessIds.Count -eq 0) {
            Write-Host "All Python processes have exited" -ForegroundColor Red
            Write-Host "`n⚠️  DEBUGGING MODE: Window will remain open for inspection. Press Enter to close."
            Read-Host "Press Enter to exit"
            break
        }
        
        Start-Sleep -Seconds 1
    }
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host "`n⚠️  DEBUGGING MODE: Window will remain open. Press Enter to close."
    Read-Host "Press Enter to exit"
} finally {
    Cleanup-Processes
    Write-Host "Cleanup complete"
}
} catch {
    # Outer catch block for any initialization errors
    Write-Host "`n" -ForegroundColor Red
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║         FATAL ERROR - DEBUGGING MODE           ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Yellow
    Write-Host "$_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Stack trace:" -ForegroundColor Yellow
    Write-Host "$($_.ScriptStackTrace)" -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "⚠️  Window will remain open for you to inspect the error above." -ForegroundColor Yellow
    Write-Host "Press Enter to close." -ForegroundColor Yellow
    Read-Host ""
    Cleanup-Processes
}
