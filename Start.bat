@echo off
setlocal

:: This script automates the setup and launch of the Mind Set application.
:: It creates a virtual environment, installs dependencies, and runs the UI.

set PYTHON_SCRIPT=app_ui.py
set VENV_DIR=venv

echo =================================
echo      Mind Set GUI Launcher
echo =================================
echo.

:: Check if the main Python UI script exists
if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] The main script '%PYTHON_SCRIPT%' was not found.
    echo Please make sure all project files are in the same folder.
    goto:end
)

:: Check for the virtual environment directory and create it if it doesn't exist
echo [INFO] Checking for virtual environment...
if not exist "%VENV_DIR%\" (
    echo [INFO] Virtual environment not found. Creating one now...
    python -m venv %VENV_DIR%
    
    :: Verify that the virtual environment was created successfully
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create the virtual environment.
        echo Please ensure Python 3.7+ is installed and added to your system's PATH.
        goto:end
    )
    echo [SUCCESS] Virtual environment created.
) else (
    echo [INFO] Virtual environment already exists.
)

:: Activate the virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate the virtual environment.
    goto:end
)

:: Check if requirements.txt exists before trying to install
if not exist "requirements.txt" (
    echo [ERROR] 'requirements.txt' not found. Cannot install dependencies.
    goto:end
)

:: Install or verify dependencies from requirements.txt
echo [INFO] Installing/verifying dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies. Please check your internet connection.
    goto:end
)
echo [SUCCESS] Dependencies are up to date.
echo.

:: Start the main Python GUI application
echo [INFO] Starting Mind Set GUI...
python %PYTHON_SCRIPT%

echo.
echo [INFO] Application has closed.

:end
echo Press any key to exit.
pause > nul
endlocal