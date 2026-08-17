<#
.SYNOPSIS
    Run the FastAPI MVP Calculation service on Windows.
#>
[CmdletBinding()]
param(
    [string]$Bind = $(if ($env:APP_API_BIND) { $env:APP_API_BIND } else { "127.0.0.1" }),
    [string]$Port = $(if ($env:APP_API_PORT) { $env:APP_API_PORT } else { "8090" }),
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path "$PSScriptRoot\..").Path
. "$PSScriptRoot\env_python.ps1"

if ($Bind -ne "127.0.0.1" -and $Bind -ne "localhost" -and $Bind -ne "::1" -and -not $env:APP_API_TOKEN) {
    Write-Error "APP_API_TOKEN is required when binding beyond loopback"
    exit 2
}

Write-Host "[MVP API] 启动计算服务: http://${Bind}:${Port}" -ForegroundColor Green
Write-Host "[MVP API] 交互文档: http://${Bind}:${Port}/docs" -ForegroundColor Cyan

& $env:PYTHON_BIN -m uvicorn app.main:app `
    --app-dir "$projectDir\backend" `
    --host $Bind `
    --port $Port `
    @RemainingArgs
