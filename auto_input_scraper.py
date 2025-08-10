#!/usr/bin/env python3
"""
Auto-input version of historic scraper that simulates user inputs
This provides inputs automatically to the interactive script:
- Input "1" for option 1 (Scrape ALL securities)
- Input "y" to confirm
"""

import subprocess
import sys
import os

def main():
    print("Starting NEPSE Historical Data Scraper with AUTO INPUTS")
    print("=" * 60)
    print("Auto-providing inputs:")
    print("  - Choice: 1 (Scrape ALL securities)")
    print("  - Confirmation: y (Yes, continue)")
    print("=" * 60)
    
    # Prepare the inputs as a string
    inputs = "1\ny\n"  # Option 1, then 'y' for confirmation
    
    try:
        # Get the Python executable path
        python_exe = sys.executable
        
        # Run the historical scraper with auto inputs
        process = subprocess.Popen(
            [python_exe, "nepse_historical_scraper.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Send the inputs and get output
        output, _ = process.communicate(input=inputs)
        
        # Print all output
        print(output)
        
        # Check return code
        if process.returncode == 0:
            print("\n✅ Historical scraping completed successfully!")
        else:
            print(f"\n❌ Historical scraping failed with return code: {process.returncode}")
            sys.exit(process.returncode)
            
    except Exception as e:
        print(f"❌ Error running historical scraper: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
