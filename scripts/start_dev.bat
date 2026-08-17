@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
pushd "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"
popd

call "%~dp0env_python.bat"

rem 检查后端依赖
"%PYTHON_BIN%" -c "import uvicorn, fastapi, lunar_python, pydantic, pytz" >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 检测到后端依赖不完整，正在检查安装...
    echo 建议先运行 scripts\build_all.bat 或 pip install -r backend\requirements.txt
)

rem 检查前端依赖
if not exist "%PROJECT_DIR%\frontend\node_modules" (
    echo [错误] 前端依赖尚未安装。请先在 frontend 目录执行: npm install 或运行 scripts\build_all.bat >&2
    pause
    exit /b 2
)

echo =======================================================
echo  天机演象 开发模式一键启动
echo  后端 API (带热重载): http://127.0.0.1:8090
echo  前端 Web (Vite开发): http://127.0.0.1:5173
echo =======================================================

echo 正在分别启动后端和前端服务窗口...
start "天机演象 - 后端API (Port 8090)" cmd /c "call "%~dp0run_mvp_api.bat" --reload"
start "天机演象 - 前端Web (Port 5173)" cmd /c "call "%~dp0run_web.bat""

rem 等待 2 秒后打开浏览器
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5173

echo.
echo [就绪] 浏览器已自动打开 http://127.0.0.1:5173
echo 若要关闭服务，请关闭弹出的两个服务窗口。
echo.
