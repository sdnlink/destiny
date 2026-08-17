<#
.SYNOPSIS
    Run Vite Web development server on Windows.
#>
$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path "$PSScriptRoot\..").Path
$frontendDir = "$projectDir\frontend"

if (-not (Test-Path "$frontendDir\node_modules")) {
    Write-Error "Frontend dependencies are missing. Run: cd frontend; npm install (or scripts/build_all.ps1)"
    exit 2
}

Write-Host "[Web] 启动 Vite 开发服务..." -ForegroundColor Green
Set-Location "$frontendDir"
npm run dev
