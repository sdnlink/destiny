<#
.SYNOPSIS
    Build and verify frontend and backend on Windows.
#>
param(
    [switch]$SkipInstall,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path "$PSScriptRoot\..").Path
$frontendDir = "$projectDir\frontend"
. "$PSScriptRoot\env_python.ps1"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Required command is missing: npm"
    exit 2
}

Write-Host "[build] 使用 Python 环境: $env:PYTHON_BIN" -ForegroundColor Cyan
& $env:PYTHON_BIN --version

$installDeps = -not $SkipInstall -and ($env:BUILD_INSTALL_DEPENDENCIES -ne "0")
$runTests = -not $SkipTests -and ($env:BUILD_RUN_TESTS -ne "0")

if ($installDeps) {
    Write-Host "[build] 正在安装后端依赖..." -ForegroundColor Green
    & $env:PYTHON_BIN -m pip install -r "$projectDir\backend\requirements.txt"
    & $env:PYTHON_BIN -m pip install -r "$projectDir\backend\requirements-dev.txt"

    Write-Host "[build] 正在安装前端依赖..." -ForegroundColor Green
    npm --prefix "$frontendDir" install
} elseif (-not (Test-Path "$frontendDir\node_modules")) {
    Write-Error "Frontend dependencies are missing and SkipInstall is set."
    exit 2
}

Write-Host "[build] 编译后端 Python 源码..." -ForegroundColor Green
& $env:PYTHON_BIN -m compileall -q "$projectDir\backend\app" "$projectDir\backend\tests"

if ($runTests) {
    Write-Host "[build] 运行后端测试..." -ForegroundColor Green
    & $env:PYTHON_BIN -m pytest "$projectDir\backend\tests"
}

Write-Host "[build] 构建前端生产包 (同源 API 模式)..." -ForegroundColor Green
$env:VITE_API_ROOT = ""
npm --prefix "$frontendDir" run build

if (-not (Test-Path "$frontendDir\dist\index.html")) {
    Write-Error "Frontend build did not produce dist/index.html"
    exit 1
}

Write-Host "[build] 构建完成!" -ForegroundColor Green
Write-Host "  Python:   $env:PYTHON_BIN"
Write-Host "  后端目录: $projectDir\backend\app"
Write-Host "  前端产物: $frontendDir\dist"
