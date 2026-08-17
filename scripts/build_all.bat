@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
pushd "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"
popd

set "FRONTEND_DIR=%PROJECT_DIR%\frontend"
if not defined BUILD_INSTALL_DEPENDENCIES set "BUILD_INSTALL_DEPENDENCIES=1"
if not defined BUILD_RUN_TESTS set "BUILD_RUN_TESTS=1"

call "%~dp0env_python.bat"

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 找不到 npm 命令，请先安装 Node.js >&2
    exit /b 2
)

echo [build] 使用 Python 环境: %PYTHON_BIN%
"%PYTHON_BIN%" --version
if %errorlevel% neq 0 (
    echo [错误] Python 解释器无法执行: %PYTHON_BIN% >&2
    exit /b 2
)

if "%BUILD_INSTALL_DEPENDENCIES%"=="1" (
    echo [build] 正在安装后端依赖...
    "%PYTHON_BIN%" -m pip install -r "%PROJECT_DIR%\backend\requirements.txt"
    if %errorlevel% neq 0 (
        echo [错误] 后端依赖安装失败 >&2
        exit /b %errorlevel%
    )
    "%PYTHON_BIN%" -m pip install -r "%PROJECT_DIR%\backend\requirements-dev.txt"
    if %errorlevel% neq 0 (
        echo [错误] 后端开发依赖安装失败 >&2
        exit /b %errorlevel%
    )

    echo [build] 正在安装前端依赖...
    npm --prefix "%FRONTEND_DIR%" install
    if %errorlevel% neq 0 (
        echo [错误] 前端依赖安装失败 >&2
        exit /b %errorlevel%
    )
) else (
    if not exist "%FRONTEND_DIR%\node_modules" (
        echo [错误] 前端 node_modules 不存在且 BUILD_INSTALL_DEPENDENCIES=0 >&2
        exit /b 2
    )
)

echo [build] 编译后端 Python 源码...
"%PYTHON_BIN%" -m compileall -q "%PROJECT_DIR%\backend\app" "%PROJECT_DIR%\backend\tests"

if "%BUILD_RUN_TESTS%"=="1" (
    echo [build] 运行后端测试...
    "%PYTHON_BIN%" -m pytest "%PROJECT_DIR%\backend\tests"
    if %errorlevel% neq 0 (
        echo [错误] 后端测试未通过 >&2
        exit /b %errorlevel%
    )
)

echo [build] 构建前端生产包 (同源 API 模式)...
set "VITE_API_ROOT="
npm --prefix "%FRONTEND_DIR%" run build
if %errorlevel% neq 0 (
    echo [错误] 前端构建失败 >&2
    exit /b %errorlevel%
)

if not exist "%FRONTEND_DIR%\dist\index.html" (
    echo [错误] 前端构建产物 dist\index.html 不存在 >&2
    exit /b 1
)

echo [build] 构建完成!
echo   Python:   %PYTHON_BIN%
echo   后端目录: %PROJECT_DIR%\backend\app
echo   前端产物: %FRONTEND_DIR%\dist
