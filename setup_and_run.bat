@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo      Endee Resume Matcher - 0 to 1 Setup
echo ==================================================

:: --------------------------------------------------
:: 1. CHECK & INSTALL PYTHON
:: --------------------------------------------------
echo.
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH. Checking for Winget...
    winget --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo Winget found. Attempting to install Python 3.11...
        choice /M "Do you want to install Python 3.11 automatically?"
        if !errorlevel! equ 1 (
            winget install -e --id Python.Python.3.11
            if !errorlevel! neq 0 (
                echo Installation failed. Please install Python manually.
                start https://www.python.org/downloads/
                pause
                exit /b 1
            )
            echo Python installed. Please restart this script to reload PATH.
            pause
            exit /b 0
        ) else (
            echo Python is required. Exiting.
            pause
            exit /b 1
        )
    ) else (
        echo Winget not found. Please install Python manually.
        start https://www.python.org/downloads/
        pause
        exit /b 1
    )
) else (
    echo Python found.
)

:: --------------------------------------------------
:: 2. CHECK & START DOCKER
:: --------------------------------------------------
echo.
echo [2/5] Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker not found! Please install Docker Desktop.
    echo Opening download page...
    start https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: Check if Docker daemon is running
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is installed but not running.
    echo Attempting to start Docker Desktop...
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        echo Waiting for Docker to initialize (this may take a minute)...
        :WAIT_DOCKER
        timeout /t 5 >nul
        docker ps >nul 2>&1
        if !errorlevel! neq 0 goto WAIT_DOCKER
        echo Docker started successfully.
    ) else (
        echo Could not find Docker Desktop executable. Please start it manually.
        pause
        exit /b 1
    )
)

:: --------------------------------------------------
:: 3. START ENDEE SERVER (PORT HANDLING)
:: --------------------------------------------------
echo.
echo [3/5] configuring Endee Server...

:: Check if our container is already running
docker ps --format "{{.Names}}" | findstr "endee-server" >nul
if %errorlevel% equ 0 (
    echo Endee server container is already running.
) else (
    :: Remove stopped container if it exists to avoid name conflict
    docker rm endee-server >nul 2>&1

    :: Try port 8080 first
    echo Attempting to start on port 8080...
    docker run -d -p 8080:8080 -v endee-data:/data --name endee-server endeeio/endee-server:latest >nul 2>&1
    
    if !errorlevel! neq 0 (
        echo Port 8080 might be in use. Trying port 8081...
        docker run -d -p 8081:8080 -v endee-data:/data --name endee-server endeeio/endee-server:latest
        if !errorlevel! neq 0 (
            echo Failed to start Endee. Please check Docker logs.
            pause
            exit /b 1
        )
        echo Running on port 8081.
        set ENDEE_URL=http://127.0.0.1:8081/api/v1
    ) else (
        echo Running on default port 8080.
    )
    
    echo Waiting for Endee to initialize...
    timeout /t 5 >nul
)

:: --------------------------------------------------
:: 4. PYTHON VIRTUAL ENVIRONMENT
:: --------------------------------------------------
echo.
echo [4/5] Setting up Environment...
if exist "venv" (
    echo Virtual environment exists.
) else (
    echo Creating virtual environment...
    python -m venv venv
)

:: --------------------------------------------------
:: 5. INSTALL & RUN
:: --------------------------------------------------
echo.
echo [5/5] Installing dependencies and launching...
call venv\Scripts\activate
pip install -r requirements.txt >nul 2>&1

echo.
echo ==================================================
echo    Launching Streamlit App...
echo    If a port conflict occurred, we set ENDEE_URL automatically.
echo ==================================================
echo.

streamlit run app.py

pause
