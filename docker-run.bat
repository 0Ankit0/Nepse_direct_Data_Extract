@echo off
REM Docker run scripts for NEPSE Scraper (Windows batch version)

echo NEPSE Scraper Docker Utilities (Windows)
echo ==========================================

if "%1"=="build" goto build
if "%1"=="historic" goto historic
if "%1"=="latest" goto latest
if "%1"=="continuous" goto continuous
if "%1"=="specific" goto specific
if "%1"=="interactive" goto interactive
if "%1"=="stop" goto stop
if "%1"=="logs" goto logs
if "%1"=="shell" goto shell
goto usage

:build
echo Building NEPSE Scraper Docker image...
docker build -t nepse-scraper:latest .
echo Build complete!
goto end

:historic
echo Running FULL historical scraper (ALL securities, 1 year data - takes hours!)
echo This will scrape 318+ securities with complete historical data
docker run --rm -v "%cd%/data:/app/data" nepse-scraper:latest python auto_historic_scraper.py
goto end

:latest
echo Running latest data scraper (recent data only)...
docker run --rm -v "%cd%/data:/app/data" -e SCRAPER_MODE=latest nepse-scraper:latest python container_scraper.py
goto end

:continuous
set interval=%2
if "%interval%"=="" set interval=60
echo Running continuous scraper (interval: %interval% minutes)...
docker run -d --name nepse-continuous -v "%cd%/data:/app/data" -e SCRAPER_MODE=continuous -e SCRAPER_INTERVAL=%interval% --restart unless-stopped nepse-scraper:latest python container_scraper.py
echo Container 'nepse-continuous' started in background
echo Use 'docker logs -f nepse-continuous' to view logs
echo Use 'docker stop nepse-continuous' to stop
goto end

:specific
set symbols=%2
if "%symbols%"=="" set symbols=NABIL,NICA,SCBL
echo Running specific securities scraper for: %symbols%
docker run --rm -v "%cd%/data:/app/data" -e SCRAPER_MODE=specific -e SYMBOLS=%symbols% nepse-scraper:latest python container_scraper.py
goto end

:interactive
echo Running interactive scraper...
docker run -it --rm -v "%cd%/data:/app/data" nepse-scraper:latest python container_scraper.py
goto end

:stop
echo Stopping all NEPSE scraper containers...
for /f %%i in ('docker ps -q --filter ancestor=nepse-scraper 2^>nul') do docker stop %%i
goto end

:logs
set container=%2
if "%container%"=="" set container=nepse-continuous
echo Viewing logs for container: %container%
docker logs -f %container%
goto end

:shell
echo Opening shell in NEPSE scraper container...
docker run -it --rm -v "%cd%/data:/app/data" nepse-scraper:latest /bin/bash
goto end

:usage
echo Usage: %0 {build^|historic^|latest^|continuous^|specific^|interactive^|stop^|logs^|shell}
echo.
echo Commands:
echo   build                    - Build the Docker image
echo   historic                 - Run FULL historical scraper (ALL securities, 1 year data)
echo   latest                   - Run latest data scraper once (recent data only)
echo   continuous [interval]    - Run continuous scraper (default: 60 min)
echo   specific [symbols]       - Run specific securities scraper
echo   interactive              - Run in interactive mode
echo   stop                     - Stop all running containers
echo   logs [container]         - View container logs
echo   shell                    - Open shell in container
echo.
echo Examples:
echo   %0 build
echo   %0 historic              (WARNING: Takes several hours!)
echo   %0 latest
echo   %0 continuous 30
echo   %0 specific "NABIL,NICA,SCBL"
echo   %0 interactive

:end
