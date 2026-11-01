@echo off
title Skinova Launcher
echo ====================================================
echo Starting Skinova Dual-Model Multimodal Platform...
echo ====================================================

echo [1/2] Starting Backend FastAPI Server (Port 8000)...
start "Skinova Backend" cmd /k "cd backend && py -3.13 -m uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Frontend Vite Server (Port 5173)...
start "Skinova Frontend" cmd /k "cd frontend && npm run dev"

echo ====================================================
echo Skinova is running!
echo Frontend: http://localhost:5173
echo Backend API Docs: http://127.0.0.1:8000/docs
echo Health Check: http://127.0.0.1:8000/health
echo ====================================================
pause
