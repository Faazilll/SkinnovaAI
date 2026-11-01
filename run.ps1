# Skinova PowerShell Launcher
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Starting Skinova Dual-Model Multimodal Platform..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$backendPath = Join-Path $PSScriptRoot "backend"
$frontendPath = Join-Path $PSScriptRoot "frontend"

Write-Host "`n[1/2] Launching Backend FastAPI Server (Port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; py -3.13 -m uvicorn app.main:app --reload --port 8000"

Write-Host "[2/2] Launching Frontend Vite Server (Port 5173)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

Write-Host "`n====================================================" -ForegroundColor Cyan
Write-Host "Skinova is running!" -ForegroundColor Cyan
Write-Host "Frontend:        http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend API:     http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Swagger Docs:    http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "Health Endpoint: http://127.0.0.1:8000/health" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan
