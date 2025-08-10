#!/usr/bin/env python3
"""
Test Docker setup by building image and running a quick test
"""

import subprocess
import os
import sys

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print("Output:", result.stdout[:500])  # First 500 chars
            return True
        else:
            print(f"❌ {description} - FAILED")
            print("Error:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - EXCEPTION: {e}")
        return False

def main():
    print("🐳 NEPSE Scraper Docker Test")
    print("=" * 50)
    
    # Check if Docker is available
    if not run_command("docker --version", "Checking Docker availability"):
        print("❌ Docker is not available. Please install Docker first.")
        sys.exit(1)
    
    # Build the image
    if not run_command("docker build -t nepse-scraper:test .", "Building Docker image"):
        print("❌ Failed to build Docker image")
        sys.exit(1)
    
    # Test the container with latest mode
    test_command = 'docker run --rm -v "%cd%/data:/app/data" -e SCRAPER_MODE=latest nepse-scraper:test python container_scraper.py' if os.name == 'nt' else 'docker run --rm -v "$(pwd)/data:/app/data" -e SCRAPER_MODE=latest nepse-scraper:test python container_scraper.py'
    
    if run_command(test_command, "Testing container with latest mode"):
        print("✅ Docker container test successful!")
        
        # Check if data was created
        if os.path.exists("data") and os.listdir("data"):
            print("✅ Data files were created successfully!")
            print("📁 Data files:", os.listdir("data"))
        else:
            print("⚠️  No data files found, but container ran successfully")
    else:
        print("❌ Container test failed")
        sys.exit(1)
    
    # Clean up test image
    run_command("docker rmi nepse-scraper:test", "Cleaning up test image")
    
    print("\n🎉 All tests passed! Your Docker setup is ready.")
    print("\n📋 Next steps:")
    print("1. Build the production image: docker build -t nepse-scraper:latest .")
    print("2. Run with utility scripts: ./docker-run.sh build && ./docker-run.sh latest")
    print("3. Use docker-compose for production: docker-compose up -d")

if __name__ == "__main__":
    main()
