#!/bin/bash
# Systemd service setup for ShareSansar TSP Scraper

echo "Setting up ShareSansar TSP Scraper systemd service..."

# Get current user and working directory
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

echo "User: $CURRENT_USER"
echo "Directory: $CURRENT_DIR"

# Update service file with correct paths and user
sed -i "s|User=futsal|User=$CURRENT_USER|g" sharesansar-tsp.service
sed -i "s|Group=futsal|Group=$CURRENT_USER|g" sharesansar-tsp.service
sed -i "s|WorkingDirectory=/home/futsal/Nepse_direct_Data_Extract|WorkingDirectory=$CURRENT_DIR|g" sharesansar-tsp.service

# Make docker-run.sh executable
chmod +x docker-run.sh

# Copy service file to systemd directory
echo "Installing service file..."
sudo cp sharesansar-tsp.service /etc/systemd/system/

# Reload systemd and enable services
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo ""
echo "✅ ShareSansar TSP Service installed successfully!"
echo ""
echo "Available commands:"
echo "==================="
echo ""
echo "🔄 SHARESANSAR TSP SCRAPER (background service):"
echo "   sudo systemctl enable sharesansar-tsp   # Enable auto-start on boot"
echo "   sudo systemctl start sharesansar-tsp    # Start ShareSansar TSP scraping"
echo "   sudo systemctl stop sharesansar-tsp     # Stop ShareSansar TSP scraping"
echo "   sudo systemctl status sharesansar-tsp   # Check status"
echo "   journalctl -u sharesansar-tsp -f        # View logs"
echo ""
echo "📊 MONITORING:"
echo "   sudo systemctl list-units | grep sharesansar  # List ShareSansar services"
echo "   journalctl -u sharesansar-tsp --since today   # Today's logs"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Data will be saved to: $CURRENT_DIR/sharesansarTSP/"
echo "   - Service runs continuously every 2 hours"
echo "   - Use 'journalctl -u sharesansar-tsp -f' to monitor progress"
