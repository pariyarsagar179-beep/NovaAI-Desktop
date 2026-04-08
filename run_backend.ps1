# -------------------------------
# NovaAI Backend Runner Script
# -------------------------------

Write-Host "Starting NovaAI Backend..." -ForegroundColor Cyan

# 1. Move into backend folder
Set-Location "$PSScriptRoot\backend"

# 2. Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "$PSScriptRoot\venv\Scripts\Activate.ps1"

# 3. Run Uvicorn
Write-Host "Running Uvicorn on http://127.0.0.1:8000" -ForegroundColor Green
uvicorn main:app --host 0.0.0.0 --port 8000 --reload