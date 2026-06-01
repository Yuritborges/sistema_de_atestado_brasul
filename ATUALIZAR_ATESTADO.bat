@echo off
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo [ERRO] .venv nao encontrada. Rode:
  echo   python -m venv .venv
  echo   .\.venv\Scripts\activate
  echo   pip install -r requirements.txt
  pause
  exit /b 1
)
powershell -ExecutionPolicy Bypass -File "%~dp0tools\build_release.ps1"
if errorlevel 1 (
  echo.
  echo [ERRO] Falha no build/release.
  pause
  exit /b 1
)
echo.
echo [OK] current atualizado. Feche o programa nos PCs e abra o atalho de novo.
pause
