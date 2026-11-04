@echo off
rem Deploy on Windows (cmd). Mirrors deploy.ps1 / deploy.sh:
rem   set DEPLOY_SKIP_BUILD=1 to skip build, set DEPLOY_START=0 to build only.
setlocal
set "PROJECT_DIR=%~dp0.."

if not "%DEPLOY_SKIP_BUILD%"=="1" (
    call "%~dp0build_all.bat"
    if errorlevel 1 (
        echo Build failed. Aborting deploy.
        exit /b 1
    )
)

if "%DEPLOY_START%"=="0" (
    echo Deployment assets are ready. DEPLOY_START=0, service was not started.
    exit /b 0
)

call "%~dp0start_all.bat"
endlocal
