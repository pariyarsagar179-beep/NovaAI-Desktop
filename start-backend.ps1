# --- Nova AI Backend Auto-Start Script ---
# Launches FastAPI backend using venv and waits until it's ready

$backendPath = "$PSScriptRoot/../backend"
$pythonExe = "$backendPath/venv/Scripts/python.exe"
$mainFile = "$backendPath/main.py"

Write-Host "Starting NovaAI backend..."

# Start backend in background
$process = Start-Process -FilePath $pythonExe -ArgumentList $mainFile -WorkingDirectory $backendPath -PassThru

# Wait for backend to be ready
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while (-not $backendReady -and $attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
        $attempt++
    }
}

if ($backendReady) {
    Write-Host "Backend is ready."
} else {
    Write-Host "Backend failed to start."
}

# Output backend PID so Electron can kill it later
$process.Id