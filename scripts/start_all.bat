@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
pushd "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"
popd

call "%~dp0env_python.bat"

rem 检查后端基础依赖
"%PYTHON_BIN%" -c "import uvicorn, fastapi, lunar_python, pydantic, pytz" >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] Python 环境 (%PYTHON_BIN%) 缺少必要依赖。
    echo 请先运行 scripts\build_all.bat 或执行 pip install -r backend\requirements.txt >&2
    exit /b 2
)

rem 检查前端已编译产物
if not exist "%PROJECT_DIR%\frontend\dist\index.html" (
    echo [错误] 前端编译产物 (frontend\dist\index.html) 缺失。
    echo 请先运行 scripts\build_all.bat 进行构建。 >&2
    exit /b 2
)

if "%START_CLICKHOUSE%"=="1" (
    where docker >nul 2>nul
    if %errorlevel% neq 0 (
        echo [错误] 设置了 START_CLICKHOUSE=1 但未检测到 Docker >&2
        exit /b 2
    )
    docker compose -f "%PROJECT_DIR%\docker-compose.yml" up -d clickhouse
)

set "SERVE_WEB=1"
set "WEB_DIST_DIR=%PROJECT_DIR%\frontend\dist"
if not defined ENABLE_LITERATURE set "ENABLE_LITERATURE=1"
if not defined START_CORPUS_API set "START_CORPUS_API=1"
if not defined APP_API_BIND set "APP_API_BIND=127.0.0.1"
if not defined APP_API_PORT set "APP_API_PORT=8090"
if not defined CORPUS_API_URL set "CORPUS_API_URL=http://127.0.0.1:8088"

if "%ENABLE_LITERATURE%"=="1" if "%START_CORPUS_API%"=="1" (
    curl --fail --silent --max-time 1 "%CORPUS_API_URL%/health" >nul 2>nul
    if %errorlevel% neq 0 (
        echo [Corpus API] 在后台启动内部语料服务窗口...
        start "Tianji Corpus Service (Port 8088)" /min cmd /c "call "%~dp0run_corpus_api.bat" --port 8088"
    )
)

echo =======================================================
echo  天机演象 一体化服务启动中...
echo  Web 与 API 地址: http://%APP_API_BIND%:%APP_API_PORT%
echo  接口文档:       http://%APP_API_BIND%:%APP_API_PORT%/docs
echo  按 Ctrl+C 停止服务
echo =======================================================

call "%~dp0run_mvp_api.bat"
