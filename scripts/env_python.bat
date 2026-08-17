@echo off
rem Common Python environment resolver for Windows CMD scripts
rem Sets PYTHON_BIN environment variable

if defined PYTHON_BIN (
    if exist "%PYTHON_BIN%" (
        goto :found
    )
)

if defined CONDA_PREFIX (
    if exist "%CONDA_PREFIX%\python.exe" (
        set "PYTHON_BIN=%CONDA_PREFIX%\python.exe"
        goto :found
    )
)

if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYTHON_BIN=%~dp0..\.venv\Scripts\python.exe"
    goto :found
)

rem Check if conda is in path and get its base
for /f "tokens=*" %%i in ('conda info --base 2^>nul') do (
    if exist "%%i\python.exe" (
        set "PYTHON_BIN=%%i\python.exe"
        goto :found
    )
)

rem Check if python is in PATH
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    if exist "%%i" (
        set "PYTHON_BIN=%%i"
        goto :found
    )
)

rem Fallback to python
set "PYTHON_BIN=python"

:found
