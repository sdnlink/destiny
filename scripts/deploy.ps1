<#
.SYNOPSIS
    Deploy on Windows: build assets, then start services.
.DESCRIPTION
    与 deploy.sh 行为一致：DEPLOY_SKIP_BUILD=1 跳过构建，DEPLOY_START=0 只构建不启动。
#>
$ErrorActionPreference = "Stop"
$projectDir = (Resolve-Path "$PSScriptRoot\..").Path

if ($env:DEPLOY_SKIP_BUILD -ne "1") {
    & "$PSScriptRoot\build_all.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed. Aborting deploy."
        exit $LASTEXITCODE
    }
}

if ($env:DEPLOY_START -eq "0") {
    Write-Host "Deployment assets are ready. DEPLOY_START=0, service was not started."
    exit 0
}

& "$PSScriptRoot\start_all.ps1"
