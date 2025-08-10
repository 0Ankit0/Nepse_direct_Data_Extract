# NEPSE Scraper Docker Guide

This guide explains how to run the NEPSE scraper in Docker containers for consistent, scalable deployment.

## 🐳 Quick Start

### Build the Image
```bash
# Linux/Mac
./docker-run.sh build

# Windows
docker-run.bat build

# Or manually
docker build -t nepse-scraper:latest .
```

### Run Latest Data Scraper (Once)
```bash
# Linux/Mac
./docker-run.sh latest

# Windows
docker-run.bat latest

# Or manually
docker run --rm -v "$(pwd)/data:/app/data" -e SCRAPER_MODE=latest nepse-scraper:latest
```

### Run Continuous Scraper
```bash
# Linux/Mac - every 60 minutes (default)
./docker-run.sh continuous

# Linux/Mac - every 30 minutes
./docker-run.sh continuous 30

# Windows
docker-run.bat continuous 30
```

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `Dockerfile` | Main container definition |
| `docker-compose.yml` | Multi-container orchestration |
| `container_scraper.py` | Container-optimized scraper |
| `docker-run.sh` | Linux/Mac utility script |
| `docker-run.bat` | Windows utility script |
| `.dockerignore` | Docker build exclusions |

## 🔧 Container Modes

The container scraper supports multiple modes via environment variables:

### 1. Latest Mode (One-time scrape)
```bash
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -e SCRAPER_MODE=latest \
  nepse-scraper:latest
```

### 2. Continuous Mode (Scheduled scraping)
```bash
docker run -d \
  --name nepse-continuous \
  -v "$(pwd)/data:/app/data" \
  -e SCRAPER_MODE=continuous \
  -e SCRAPER_INTERVAL=60 \
  nepse-scraper:latest
```

### 3. Specific Securities Mode
```bash
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -e SCRAPER_MODE=specific \
  -e SYMBOLS="NABIL,NICA,SCBL,EBL" \
  nepse-scraper:latest
```

### 4. Interactive Mode
```bash
docker run -it --rm \
  -v "$(pwd)/data:/app/data" \
  nepse-scraper:latest
```

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPER_MODE` | `interactive` | Mode: `latest`, `continuous`, `specific`, `interactive` |
| `SCRAPER_INTERVAL` | `60` | Interval in minutes for continuous mode |
| `SCRAPER_DELAY` | `1.0` | Delay in seconds between API requests |
| `MAX_DATES` | `10` | Maximum number of historical dates to scrape |
| `SYMBOLS` | `NABIL,NICA,SCBL` | Comma-separated symbols for specific mode |
| `DATA_FOLDER` | `/app/data` | Container data directory |
| `TZ` | `Asia/Kathmandu` | Timezone |

## 🐙 Docker Compose Usage

### Start with Docker Compose
```bash
# Start the scraper service
docker-compose up -d nepse-scraper

# Start with web interface
docker-compose up -d

# View logs
docker-compose logs -f nepse-scraper

# Stop services
docker-compose down
```

### Customize Docker Compose
Edit `docker-compose.yml` to change:
- Environment variables
- Volume mounts
- Commands
- Resource limits

## 📊 Data Persistence

Data is persisted using Docker volumes:

```bash
# Local data directory is mounted to container
-v "$(pwd)/data:/app/data"
```

### Data Structure
```
data/
├── nepse_latest_20250810_120000.csv
├── nepse_latest_20250810_120000.json
├── NABIL_data.csv
├── NICA_data.csv
└── ...
```

## 🔍 Monitoring and Logs

### View Container Logs
```bash
# Follow logs for running container
docker logs -f nepse-continuous

# View logs with utility script
./docker-run.sh logs nepse-continuous
```

### Access Container Shell
```bash
# Open bash shell in container
./docker-run.sh shell

# Or manually
docker run -it --rm -v "$(pwd)/data:/app/data" nepse-scraper:latest /bin/bash
```

### Health Checks
```bash
# Check if container is running
docker ps --filter ancestor=nepse-scraper

# Check container status
docker inspect nepse-continuous
```

## 🚀 Production Deployment

### 1. Resource Limits
Add to docker-compose.yml:
```yaml
services:
  nepse-scraper:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
        reservations:
          memory: 256M
```

### 2. Restart Policies
```yaml
restart: unless-stopped
# or
restart: always
```

### 3. Network Configuration
```yaml
networks:
  nepse-net:
    driver: bridge
```

### 4. Secrets Management
```yaml
secrets:
  - nepse_config
```

## 🔧 Troubleshooting

### Common Issues

1. **Permission Denied on Data Folder**
   ```bash
   sudo chown -R 1000:1000 ./data
   ```

2. **Container Exits Immediately**
   ```bash
   # Check logs
   docker logs <container-id>
   
   # Run with interactive shell
   docker run -it nepse-scraper:latest /bin/bash
   ```

3. **API Connection Issues**
   - Check internet connectivity
   - Verify NEPSE API is accessible
   - Increase `SCRAPER_DELAY` if rate limited

4. **Out of Memory**
   ```bash
   # Increase container memory limit
   docker run -m 1g nepse-scraper:latest
   ```

### Debug Mode
```bash
# Run with debug output
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -e PYTHONUNBUFFERED=1 \
  nepse-scraper:latest python -u container_scraper.py
```

## 📈 Scaling

### Multiple Instances
```bash
# Run multiple scrapers for different symbols
docker run -d --name nepse-banking -e SYMBOLS="NABIL,NICA,EBL" nepse-scraper:latest
docker run -d --name nepse-insurance -e SYMBOLS="NICL,UNL,PLI" nepse-scraper:latest
```

### Load Balancing
Use Docker Swarm or Kubernetes for advanced orchestration.

## 🛡️ Security

### Non-root User
The container runs as a non-root user (`appuser`) for security.

### Network Security
```yaml
networks:
  nepse-net:
    driver: bridge
    internal: true  # No external access
```

### Read-only Filesystem
```yaml
read_only: true
tmpfs:
  - /tmp
  - /app/logs
```

## 📋 Utility Scripts Reference

### Linux/Mac (docker-run.sh)
```bash
./docker-run.sh build                    # Build image
./docker-run.sh latest                   # One-time scrape
./docker-run.sh continuous [interval]    # Continuous scraping
./docker-run.sh specific [symbols]       # Specific securities
./docker-run.sh interactive              # Interactive mode
./docker-run.sh stop                     # Stop all containers
./docker-run.sh logs [container]         # View logs
./docker-run.sh shell                    # Container shell
```

### Windows (docker-run.bat)
```cmd
docker-run.bat build
docker-run.bat latest
docker-run.bat continuous 30
docker-run.bat specific "NABIL,NICA"
docker-run.bat interactive
docker-run.bat stop
docker-run.bat logs
docker-run.bat shell
```

## 🎯 Use Cases

### 1. Development/Testing
```bash
# Quick test with latest data
./docker-run.sh latest
```

### 2. Production Monitoring
```bash
# Continuous scraping every 30 minutes
./docker-run.sh continuous 30
```

### 3. Research/Analysis
```bash
# Scrape specific high-value securities
./docker-run.sh specific "NABIL,NICA,SCBL,EBL,NBL"
```

### 4. Scheduled Jobs
```bash
# Add to crontab for daily runs
0 9 * * 1-5 docker run --rm -v /path/to/data:/app/data -e SCRAPER_MODE=latest nepse-scraper:latest
```

This containerized setup provides a robust, scalable solution for NEPSE data scraping with proper error handling, logging, and data persistence.
