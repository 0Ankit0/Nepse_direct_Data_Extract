#!/bin/bash
# Quick setup script for NEPSE Scraper on server

set -e  # Exit on any error

echo "🚀 NEPSE Scraper Server Setup"
echo "=" * 50

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    echo "📦 Installing Docker on Ubuntu/Debian..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Please log out and back in for group changes to take effect."
}

# Function to install Docker on CentOS/RHEL
install_docker_centos() {
    echo "📦 Installing Docker on CentOS/RHEL..."
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Please log out and back in for group changes to take effect."
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if git is installed
if ! command_exists git; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if docker is installed
if ! command_exists docker; then
    echo "⚠️ Docker is not installed."
    echo "Would you like to install Docker? (y/n)"
    read -r install_docker
    
    if [ "$install_docker" = "y" ] || [ "$install_docker" = "Y" ]; then
        if [ -f /etc/ubuntu-release ] || [ -f /etc/debian_version ]; then
            install_docker_ubuntu
        elif [ -f /etc/redhat-release ] || [ -f /etc/centos-release ]; then
            install_docker_centos
        else
            echo "❌ Unsupported OS. Please install Docker manually."
            exit 1
        fi
        
        echo "Please log out and back in, then run this script again."
        exit 0
    else
        echo "❌ Docker is required. Exiting."
        exit 1
    fi
fi

echo "✅ Prerequisites satisfied"

# Check if we're already in the project directory
if [ ! -f "Dockerfile" ]; then
    echo "📁 Cloning NEPSE Scraper repository..."
    if [ -d "Nepse_direct_Data_Extract" ]; then
        echo "Directory already exists. Updating..."
        cd Nepse_direct_Data_Extract
        git pull origin main
    else
        git clone https://github.com/0Ankit0/Nepse_direct_Data_Extract.git
        cd Nepse_direct_Data_Extract
    fi
else
    echo "📁 Already in project directory"
fi

# Make scripts executable
echo "🔧 Setting up permissions..."
chmod +x docker-run.sh

# Build Docker image
echo "🏗️ Building Docker image..."
./docker-run.sh build

# Create data directory
mkdir -p data logs

echo "🎉 Setup complete!"
echo ""
echo "📋 What to do next:"
echo ""
echo "🔥 For COMPLETE historical data (ALL securities, 1 year history):"
echo "   ./docker-run.sh historic"
echo "   ⚠️ WARNING: This takes 4-8 hours and creates hundreds of files!"
echo ""
echo "⚡ For quick test (recent data only):"
echo "   ./docker-run.sh latest"
echo ""
echo "🔄 For continuous monitoring (every hour):"
echo "   ./docker-run.sh continuous 60"
echo ""
echo "📊 To check progress:"
echo "   ./docker-run.sh logs"
echo ""
echo "🛑 To stop all containers:"
echo "   ./docker-run.sh stop"
echo ""
echo "🐳 Using Docker Compose:"
echo "   docker-compose up -d      # Start background service"
echo "   docker-compose logs -f    # View logs"
echo "   docker-compose down       # Stop service"
echo ""
echo "📁 Your data will be saved in: $(pwd)/data/"
echo ""
echo "For detailed documentation, see:"
echo "   - README.md"
echo "   - DOCKER_README.md"
echo "   - SERVER_DEPLOYMENT.md"
