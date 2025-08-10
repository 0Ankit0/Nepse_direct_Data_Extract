@echo off
REM Quick setup script for NEPSE Scraper on Windows Server

echo 🚀 NEPSE Scraper Windows Server Setup
echo ==================================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. 
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo Then run this script again.
    pause
    exit /b 1
)

echo ✅ Docker is available

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed.
    echo Please install Git from: https://git-scm.com/download/win
    echo Then run this script again.
    pause
    exit /b 1
)

echo ✅ Git is available

REM Check if we're in the project directory
if not exist "Dockerfile" (
    echo 📁 Cloning NEPSE Scraper repository...
    if exist "Nepse_direct_Data_Extract" (
        echo Directory already exists. Updating...
        cd Nepse_direct_Data_Extract
        git pull origin main
    ) else (
        git clone https://github.com/0Ankit0/Nepse_direct_Data_Extract.git
        cd Nepse_direct_Data_Extract
    )
) else (
    echo 📁 Already in project directory
)

REM Build Docker image
echo 🏗️ Building Docker image...
docker-run.bat build

REM Create data directory
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo 🎉 Setup complete!
echo.
echo 📋 What to do next:
echo.
echo 🔥 For COMPLETE historical data (ALL securities, 1 year history):
echo    docker-run.bat historic
echo    ⚠️ WARNING: This takes 4-8 hours and creates hundreds of files!
echo.
echo ⚡ For quick test (recent data only):
echo    docker-run.bat latest
echo.
echo 🔄 For continuous monitoring (every hour):
echo    docker-run.bat continuous 60
echo.
echo 📊 To check progress:
echo    docker-run.bat logs
echo.
echo 🛑 To stop all containers:
echo    docker-run.bat stop
echo.
echo 🐳 Using Docker Compose:
echo    docker-compose up -d      # Start background service
echo    docker-compose logs -f    # View logs
echo    docker-compose down       # Stop service
echo.
echo 📁 Your data will be saved in: %cd%\data\
echo.
echo For detailed documentation, see:
echo    - README.md
echo    - DOCKER_README.md
echo    - SERVER_DEPLOYMENT.md

pause
