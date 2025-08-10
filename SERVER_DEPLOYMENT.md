# 🚀 Server Deployment Guide

## After Cloning the Repository

Follow these steps to set up and run the NEPSE scraper on your server:

### 📋 Prerequisites

Make sure your server has:
- **Docker** and **Docker Compose** installed
- **Git** installed
- **Internet connection** (for accessing NEPSE API)
- **Sufficient storage** (expect several GB for full historical data)

### 🔧 Step-by-Step Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/0Ankit0/Nepse_direct_Data_Extract.git
cd Nepse_direct_Data_Extract
```

#### 2. Make Scripts Executable (Linux/Mac)
```bash
chmod +x docker-run.sh
```

#### 3. Build the Docker Image
```bash
# Linux/Mac
./docker-run.sh build

# Windows
docker-run.bat build

# Or manually
docker build -t nepse-scraper:latest .
```

#### 4. Choose Your Scraping Strategy

**🎯 For Complete Historical Data (Recommended for first run):**
```bash
# This will scrape ALL securities with 1 year of historical data
# ⚠️ WARNING: Takes 4-8 hours and creates hundreds of CSV files

# Linux/Mac
./docker-run.sh historic

# Windows
docker-run.bat historic

# Or with Docker Compose
docker-compose up nepse-scraper
```

**📊 For Recent Data Only (Quick test):**
```bash
# Linux/Mac
./docker-run.sh latest

# Windows
docker-run.bat latest
```

**🔄 For Continuous Monitoring:**
```bash
# Run every 60 minutes (default)
./docker-run.sh continuous

# Run every 30 minutes
./docker-run.sh continuous 30

# Or with Docker Compose
docker-compose up -d nepse-continuous
```

### 📂 Data Location

After running, your data will be in:
```
./data/
├── NABIL_historical_data.csv
├── NICA_historical_data.csv
├── SCBL_historical_data.csv
└── [300+ more CSV files...]
```

### 🔍 Monitoring and Management

#### Check Running Containers
```bash
docker ps
```

#### View Logs
```bash
# Real-time logs
docker-compose logs -f nepse-scraper

# Or with utility script
./docker-run.sh logs
```

#### Stop All Containers
```bash
./docker-run.sh stop
# Or
docker-compose down
```

#### Access Container Shell (for debugging)
```bash
./docker-run.sh shell
```

### 🎛️ Configuration Options

#### Environment Variables
Create a `.env` file for custom configuration:
```bash
# .env file
DATA_FOLDER=/app/data
SCRAPER_DELAY=1.0
TZ=Asia/Kathmandu
```

#### Custom Docker Compose
Edit `docker-compose.yml` to:
- Change scraping intervals
- Set memory limits
- Configure restart policies
- Add volume mounts

### 🚨 Production Considerations

#### 1. Resource Requirements
```yaml
# Add to docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: "0.5"
```

#### 2. Log Management
```bash
# Rotate logs to prevent disk space issues
docker system prune -f
```

#### 3. Backup Strategy
```bash
# Backup data folder regularly
tar -czf nepse_backup_$(date +%Y%m%d).tar.gz data/
```

#### 4. Monitoring Script
```bash
#!/bin/bash
# monitor.sh - Check if scraper is running
if ! docker ps | grep -q nepse; then
    echo "NEPSE scraper not running, restarting..."
    docker-compose up -d nepse-continuous
fi
```

### 🔄 Maintenance Commands

#### Update to Latest Code
```bash
git pull origin main
docker-compose down
./docker-run.sh build
docker-compose up -d
```

#### Clean Up Old Data
```bash
# Remove files older than 30 days
find ./data -name "*.csv" -mtime +30 -delete
```

#### System Cleanup
```bash
# Remove unused Docker images
docker system prune -a -f
```

### 🐛 Troubleshooting

#### Common Issues

**1. Permission Denied**
```bash
sudo chown -R $USER:$USER ./data
chmod 755 ./data
```

**2. Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8080
# Kill the process or change port in docker-compose.yml
```

**3. Out of Disk Space**
```bash
# Check disk usage
df -h
# Clean up Docker
docker system prune -a -f
```

**4. Container Keeps Restarting**
```bash
# Check logs for errors
docker logs nepse-scraper
```

**5. No Data Generated**
```bash
# Check if NEPSE API is accessible
curl -I https://www.nepalstock.com
# Check container logs
docker logs nepse-scraper
```

### 📊 Expected Results

After running the full historical scraper, expect:

- **~318 CSV files** (one per security)
- **File sizes**: 1-50KB per security (depending on trading activity)
- **Total size**: 50-500MB for all data
- **Time taken**: 4-8 hours for complete run
- **API calls**: ~17,000 requests to NEPSE

### 🔔 Notifications

#### Set up Slack/Email notifications (optional)
```bash
# Add to your crontab for daily status
0 9 * * * /path/to/check_scraper.sh | mail -s "NEPSE Scraper Status" your@email.com
```

### 📱 Quick Commands Summary

```bash
# Essential commands for server management
./docker-run.sh build          # Build image
./docker-run.sh historic       # Full historical data (hours)
./docker-run.sh latest         # Recent data (minutes)
./docker-run.sh continuous 60  # Ongoing monitoring
./docker-run.sh logs           # Check progress
./docker-run.sh stop           # Stop everything
docker-compose up -d           # Background service
docker-compose down            # Stop services
```

This guide should get your NEPSE scraper running smoothly on any server! 🎉
