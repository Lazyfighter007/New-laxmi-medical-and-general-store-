@echo off
setlocal
cd /d "%~dp0"
set "PY=py"
where py >nul 2>nul || set "PY=python"

echo Installing/updating PyInstaller...
%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 goto fail

echo Building MedicalStore.exe...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name "MedicalStore" medical_store.py
if errorlevel 1 goto fail

echo Checking for Inno Setup compiler...
where ISCC.exe >nul 2>nul
if errorlevel 1 (
  if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
  echo.
  echo Inno Setup is not installed.
  echo Install Inno Setup 6, then run this file again.
  echo.
  pause
  exit /b 2
)

"%ISCC%" installer.iss
if errorlevel 1 goto fail

echo.
echo ============================================
echo Setup created successfully:
echo Output\MedicalStoreSetup.exe
echo ============================================
echo.
pause
exit /b 0
:fail
echo.
echo BUILD FAILED. Read the message above.
pause
exit /b 1
