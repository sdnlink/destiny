@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
pushd "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"
popd

call "%~dp0env_python.bat"

if not defined APP_API_BIND set "APP_API_BIND=127.0.0.1"
if not defined APP_API_PORT set "APP_API_PORT=8090"

if not "%APP_API_BIND%"=="127.0.0.1" (
    if not "%APP_API_BIND%"=="localhost" (
        if not "%APP_API_BIND%"=="::1" (
            if not defined APP_API_TOKEN (
                echo [错误] 绑定非回环地址时必须设置 APP_API_TOKEN >&2
                exit /b 2
            )
        )
    )
)

echo [MVP API] 启动计算服务: http://%APP_API_BIND%:%APP_API_PORT%
echo [MVP API] 交互文档: http://%APP_API_BIND%:%APP_API_PORT%/docs
"%PYTHON_BIN%" -m uvicorn app.main:app --app-dir "%PROJECT_DIR%\backend" --host "%APP_API_BIND%" --port "%APP_API_PORT%" %*
