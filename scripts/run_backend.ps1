# InvestCops - Backend Start Script for Beginners
# Double-click or run this file. It starts the backend and opens your browser.

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  INVESTCOPS AI - Backend Launcher" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$BackendDir = Join-Path $Root "backend"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Python environment not found!" -ForegroundColor Red
    Write-Host "Please run this once from the project folder:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .venv\Scripts\pip install -r backend\requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press Enter to close..."
    Read-Host
    exit 1
}

Write-Host "[1/3] Starting backend server on http://localhost:8000 ..." -ForegroundColor Green
Start-Process -FilePath $VenvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000" -WorkingDirectory $BackendDir -WindowStyle Minimized

Write-Host "[2/3] Waiting for server to wake up..."
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            $ok = $true
            break
        }
    } catch {
        # server not ready yet, keep waiting
    }
}

if ($ok) {
    Write-Host "[3/3] Server is RUNNING. Opening browser..." -ForegroundColor Green
    Write-Host ""
    Write-Host "  API Docs   : http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  Health     : http://localhost:8000/api/health" -ForegroundColor Cyan
    Write-Host ""
    Start-Process "http://localhost:8000/docs"
} else {
    Write-Host "[ERROR] Server did not start. Check the error in the other window." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to close this window..."
Read-Host