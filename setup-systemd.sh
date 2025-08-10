#!/bin/bash
# Systemd service setup for NEPSE Scraper

echo "Setting up NEPSE Scraper systemd services..."

# Get current user and working directory
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

echo "User: $CURRENT_USER"
echo "Directory: $CURRENT_DIR"

# Update service files with correct paths and user
sed -i "s|User=futsal|User=$CURRENT_USER|g" nepse-historic.service
sed -i "s|Group=futsal|Group=$CURRENT_USER|g" nepse-historic.service
sed -i "s|WorkingDirectory=/home/futsal/Nepse_direct_Data_Extract|WorkingDirectory=$CURRENT_DIR|g" nepse-historic.service
sed -i "s|/home/futsal/Nepse_direct_Data_Extract/docker-run.sh|$CURRENT_DIR/docker-run.sh|g" nepse-historic.service

sed -i "s|User=futsal|User=$CURRENT_USER|g" nepse-continuous.service
sed -i "s|Group=futsal|Group=$CURRENT_USER|g" nepse-continuous.service
sed -i "s|WorkingDirectory=/home/futsal/Nepse_direct_Data_Extract|WorkingDirectory=$CURRENT_DIR|g" nepse-continuous.service
sed -i "s|/home/futsal/Nepse_direct_Data_Extract/docker-run.sh|$CURRENT_DIR/docker-run.sh|g" nepse-continuous.service

sed -i "s|User=futsal|User=$CURRENT_USER|g" sharesansar-tsp.service
sed -i "s|Group=futsal|Group=$CURRENT_USER|g" sharesansar-tsp.service
sed -i "s|WorkingDirectory=/home/futsal/Nepse_direct_Data_Extract|WorkingDirectory=$CURRENT_DIR|g" sharesansar-tsp.service

# Make docker-run.sh executable
chmod +x docker-run.sh

# Copy service files to systemd directory
echo "Installing service files..."
sudo cp nepse-historic.service /etc/systemd/system/
sudo cp nepse-continuous.service /etc/systemd/system/
sudo cp sharesansar-tsp.service /etc/systemd/system/

# Reload systemd and enable services
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "✅ Services installed successfully!"
echo ""
echo "Available commands:"
echo "==================="
echo ""
echo "🔄 HISTORIC SCRAPER (one-time, several hours):"
echo "   sudo systemctl start nepse-historic     # Start historic scraping"
echo "   sudo systemctl status nepse-historic    # Check status"
echo "   journalctl -u nepse-historic -f         # View logs"
echo ""
echo "🔄 CONTINUOUS SCRAPER (background service):"
echo "   sudo systemctl enable nepse-continuous  # Enable auto-start on boot"
echo "   sudo systemctl start nepse-continuous   # Start continuous scraping"
echo "   sudo systemctl stop nepse-continuous    # Stop continuous scraping"
echo "   sudo systemctl status nepse-continuous  # Check status"
echo "   journalctl -u nepse-continuous -f       # View logs"
echo ""
echo "🔄 SHARESANSAR TSP SCRAPER (background service):"
echo "   sudo systemctl enable sharesansar-tsp   # Enable auto-start on boot"
echo "   sudo systemctl start sharesansar-tsp    # Start ShareSansar TSP scraping"
echo "   sudo systemctl stop sharesansar-tsp     # Stop ShareSansar TSP scraping"
echo "   sudo systemctl status sharesansar-tsp   # Check status"
echo "   journalctl -u sharesansar-tsp -f        # View logs"
echo ""
echo "📊 MONITORING:"
echo "   sudo systemctl list-units | grep 'nepse\\|sharesansar'  # List all scraper services"
echo "   journalctl -u nepse-historic --since today     # Today's historic logs"
echo "   journalctl -u nepse-continuous --since today   # Today's continuous logs"
echo "   journalctl -u sharesansar-tsp --since today    # Today's ShareSansar TSP logs"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Historic scraper takes several hours (318+ securities)"
echo "   - Use 'journalctl -u nepse-historic -f' to monitor progress"
echo "   - Data will be saved to: $CURRENT_DIR/data/"
echo "   - ShareSansar TSP data will be saved to: $CURRENT_DIR/sharesansarTSP/"
