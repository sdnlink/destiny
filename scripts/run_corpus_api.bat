@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
pushd "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"
popd

call "%~dp0env_python.bat"

echo [Corpus API] 启动内部语料服务...
cd /d "%PROJECT_DIR%\backend"
"%PYTHON_BIN%" -m app.corpus_api %*
