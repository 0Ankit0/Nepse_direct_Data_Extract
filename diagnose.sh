#!/bin/bash
# NEPSE Scraper Diagnostic Script

echo "🔍 NEPSE Scraper Diagnostic Report"
echo "=================================="
echo ""

# Check current user and directory
echo "📂 Environment:"
echo "   User: $(whoami)"
echo "   Directory: $(pwd)"
echo "   Date: $(date)"
echo ""

# Check Docker
echo "🐳 Docker Status:"
if command -v docker &> /dev/null; then
    echo "   ✅ Docker installed: $(docker --version)"
    if sudo systemctl is-active --quiet docker; then
        echo "   ✅ Docker service running"
    else
        echo "   ❌ Docker service NOT running"
        echo "   🔧 Fix: sudo systemctl start docker"
    fi
else
    echo "   ❌ Docker NOT installed"
    echo "   🔧 Fix: Install Docker first"
fi
echo ""

# Check Docker image
echo "🖼️  Docker Image:"
if docker images | grep -q nepse-scraper; then
    echo "   ✅ nepse-scraper image exists"
    docker images | grep nepse-scraper
else
    echo "   ❌ nepse-scraper image NOT found"
    echo "   🔧 Fix: ./docker-run.sh build"
fi
echo ""

# Check scripts
echo "📜 Scripts:"
if [ -x "./docker-run.sh" ]; then
    echo "   ✅ docker-run.sh executable"
else
    echo "   ❌ docker-run.sh not executable"
    echo "   🔧 Fix: chmod +x docker-run.sh"
fi

if [ -f "./auto_historic_scraper.py" ]; then
    echo "   ✅ auto_historic_scraper.py exists"
else
    echo "   ❌ auto_historic_scraper.py missing"
fi
echo ""

# Check data directory
echo "📁 Data Directory:"
if [ -d "./data" ]; then
    echo "   ✅ data/ directory exists"
    echo "   📊 Files: $(ls -la data/ | wc -l) items"
else
    echo "   ❌ data/ directory missing"
    echo "   🔧 Fix: mkdir -p data"
fi
echo ""

# Check systemd service
echo "🔧 Systemd Service:"
if systemctl list-unit-files | grep -q nepse-historic; then
    echo "   ✅ nepse-historic service installed"
    echo "   Status: $(systemctl is-active nepse-historic)"
    echo "   Enabled: $(systemctl is-enabled nepse-historic)"
else
    echo "   ❌ nepse-historic service NOT installed"
    echo "   🔧 Fix: ./setup-systemd.sh"
fi
echo ""

# Check recent logs
echo "📋 Recent Service Logs (last 5 lines):"
if systemctl list-unit-files | grep -q nepse-historic; then
    journalctl -u nepse-historic --no-pager -n 5 2>/dev/null || echo "   No logs available"
else
    echo "   Service not installed"
fi
echo ""

# Test basic Docker functionality
echo "🧪 Docker Test:"
if docker run --rm hello-world &>/dev/null; then
    echo "   ✅ Docker works correctly"
else
    echo "   ❌ Docker test failed"
    echo "   🔧 Check Docker permissions and service"
fi
echo ""

echo "💡 Quick Fixes:"
echo "==============="
echo "1. Build Docker image: ./docker-run.sh build"
echo "2. Make scripts executable: chmod +x *.sh"
echo "3. Create data directory: mkdir -p data"
echo "4. Install services: ./setup-systemd.sh"
echo "5. Start Docker: sudo systemctl start docker"
echo ""
echo "🚀 To run historic scraper:"
echo "   sudo systemctl start nepse-historic"
echo "   journalctl -u nepse-historic -f"
