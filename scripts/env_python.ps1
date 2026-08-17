<#
.SYNOPSIS
    Common Python environment resolver for Windows PowerShell scripts.
#>

function Resolve-ProjectPython {
    if ($env:PYTHON_BIN -and (Test-Path $env:PYTHON_BIN)) {
        return $env:PYTHON_BIN
    }

    if ($env:CONDA_PREFIX -and (Test-Path "$env:CONDA_PREFIX\python.exe")) {
        return "$env:CONDA_PREFIX\python.exe"
    }

    $projectDir = Resolve-Path "$PSScriptRoot\.."
    if (Test-Path "$projectDir\.venv\Scripts\python.exe") {
        return "$projectDir\.venv\Scripts\python.exe"
    }

    try {
        $condaBase = conda info --base 2>$null
        if ($condaBase -and (Test-Path "$condaBase\python.exe")) {
            return "$condaBase\python.exe"
        }
    } catch {}

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    return "python"
}

$env:PYTHON_BIN = Resolve-ProjectPython
