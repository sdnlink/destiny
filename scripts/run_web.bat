@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
pushd "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"
popd

set "FRONTEND_DIR=%PROJECT_DIR%\frontend"

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [错误] 前端依赖尚未安装。请先在 frontend 目录执行: npm install 或运行 scripts\build_all.bat >&2
    exit /b 2
)

echo [Web] 启动 Vite 开发服务...
cd /d "%FRONTEND_DIR%"
npm run dev
