<#
.SYNOPSIS
    Start full production services on Windows (FastAPI serves both API and compiled React web).
#>
$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path "$PSScriptRoot\..").Path
. "$PSScriptRoot\env_python.ps1"

# 检查后端基础依赖
$testImport = & $env:PYTHON_BIN -c "import uvicorn, fastapi, lunar_python, pydantic, pytz" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python environment ($env:PYTHON_BIN) is missing required dependencies. Run ./scripts/build_all.ps1 first."
    exit 2
}

# 检查前端构建产物
$distHtml = "$projectDir\frontend\dist\index.html"
if (-not (Test-Path $distHtml)) {
    Write-Error "Compiled frontend assets ($distHtml) are missing. Run ./scripts/build_all.ps1 first."
    exit 2
}

if ($env:START_CLICKHOUSE -eq "1") {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is required when START_CLICKHOUSE=1"
        exit 2
    }
    docker compose -f "$projectDir\docker-compose.yml" up -d clickhouse
}

$env:SERVE_WEB = "1"
$env:WEB_DIST_DIR = "$projectDir\frontend\dist"
if (-not $env:ENABLE_LITERATURE) { $env:ENABLE_LITERATURE = "1" }
if (-not $env:START_CORPUS_API) { $env:START_CORPUS_API = "1" }
$bind = if ($env:APP_API_BIND) { $env:APP_API_BIND } else { "127.0.0.1" }
$port = if ($env:APP_API_PORT) { $env:APP_API_PORT } else { "8090" }
$corpusUrl = if ($env:CORPUS_API_URL) { $env:CORPUS_API_URL } else { "http://127.0.0.1:8088" }

$corpusJob = $null
if ($env:ENABLE_LITERATURE -eq "1" -and $env:START_CORPUS_API -eq "1") {
    try {
        $health = Invoke-RestMethod -Uri "$corpusUrl/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
    } catch {
        $health = $null
    }
    if (-not $health) {
        Write-Host "[Corpus API] 启动后台语料服务..." -ForegroundColor Cyan
        $corpusJob = Start-Job -ScriptBlock {
            param($scriptPath)
            & powershell.exe -File $scriptPath --port 8088
        } -ArgumentList "$PSScriptRoot\run_corpus_api.ps1"
    }
}

try {
    Write-Host "=======================================================" -ForegroundColor Green
    Write-Host " 天机演象 一体化服务启动中..." -ForegroundColor Green
    Write-Host " Web 与 API 地址: http://${bind}:${port}" -ForegroundColor Yellow
    Write-Host " 接口文档:       http://${bind}:${port}/docs" -ForegroundColor Yellow
    Write-Host " 按 Ctrl+C 停止服务" -ForegroundColor Gray
    Write-Host "=======================================================" -ForegroundColor Green

    & "$PSScriptRoot\run_mvp_api.ps1" -Bind $bind -Port $port
} finally {
    if ($corpusJob) {
        Stop-Job $corpusJob -ErrorAction SilentlyContinue
        Remove-Job $corpusJob -ErrorAction SilentlyContinue
    }
}
