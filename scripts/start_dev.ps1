<#
.SYNOPSIS
    Start full development environment on Windows (FastAPI with reload + Vite dev server).
#>
$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path "$PSScriptRoot\..").Path
. "$PSScriptRoot\env_python.ps1"

$frontendDir = "$projectDir\frontend"
if (-not (Test-Path "$frontendDir\node_modules")) {
    Write-Error "Frontend dependencies are missing. Run: cd frontend; npm install (or scripts/build_all.ps1)"
    exit 2
}

Write-Host "=======================================================" -ForegroundColor Green
Write-Host " 天机演象 开发模式启动" -ForegroundColor Green
Write-Host " 后端 API (热重载): http://127.0.0.1:8090" -ForegroundColor Yellow
Write-Host " 前端 Web (Vite):   http://127.0.0.1:5173" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Green

# 启动后端进程窗口
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-File", "$PSScriptRoot\run_mvp_api.ps1", "--reload"
# 启动前端进程窗口
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-File", "$PSScriptRoot\run_web.ps1"

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5173"

Write-Host "`n[就绪] 已在浏览器中打开 http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "若要停止，请关闭弹出的 PowerShell 窗口。" -ForegroundColor Gray
