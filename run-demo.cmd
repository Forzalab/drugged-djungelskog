@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Install the project environment first using the Windows setup in README.md.
    popd
    exit /b 1
)
".venv\Scripts\python.exe" -m barnaby.demo %*
set "barnabyExit=%errorlevel%"
popd
exit /b %barnabyExit%
