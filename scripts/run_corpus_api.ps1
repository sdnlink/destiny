<#
.SYNOPSIS
    Run internal corpus API on Windows.
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path "$PSScriptRoot\..").Path
. "$PSScriptRoot\env_python.ps1"

Write-Host "[Corpus API] 启动内部语料服务..." -ForegroundColor Green
Set-Location "$projectDir\backend"
& $env:PYTHON_BIN -m app.corpus_api $RemainingArgs
