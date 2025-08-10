#!/usr/bin/env python3
"""
Container-optimized NEPSE Scraper

This version is designed to run in Docker containers with proper
signal handling and configuration via environment variables.
"""

import os
import sys
import signal
import json
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

try:
    from nepse_scraper import Nepse_scraper
except ImportError:
    print("Error: nepse_scraper package not found. Please install it using:")
    print("pip install nepse-scraper")
    sys.exit(1)


class ContainerNepseScraper:
    """Container-optimized NEPSE scraper with environment variable configuration."""
    
    def __init__(self):
        self.scraper = Nepse_scraper()
        self.data_folder = os.getenv('DATA_FOLDER', '/app/data')
        self.delay = float(os.getenv('SCRAPER_DELAY', '1.0'))
        self.max_dates = int(os.getenv('MAX_DATES', '10'))
        self.running = True
        
        # Create data folder
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        print(f"Container NEPSE Scraper initialized")
        print(f"Data folder: {self.data_folder}")
        print(f"Delay between requests: {self.delay}s")
        print(f"Max dates to scrape: {self.max_dates}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def get_trading_dates(self, days_back: int = 30) -> List[str]:
        """Get recent trading dates."""
        dates = []
        current_date = date.today()
        
        for i in range(days_back):
            if not self.running:
                break
                
            check_date = current_date - timedelta(days=i)
            # Skip weekends
            if check_date.weekday() < 5:
                dates.append(check_date.strftime('%Y-%m-%d'))
                
            if len(dates) >= self.max_dates:
                break
        
        return dates
    
    def scrape_latest_data(self) -> bool:
        """Scrape latest trading data."""
        try:
            print("Fetching latest trading data...")
            latest_data = self.scraper.get_today_price()
            
            if isinstance(latest_data, dict) and 'content' in latest_data:
                securities_data = latest_data['content']
            elif isinstance(latest_data, list):
                securities_data = latest_data
            else:
                securities_data = latest_data
            
            if not securities_data:
                print("No data found. Market might be closed.")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(securities_data)
            df['scraped_at'] = datetime.now().isoformat()
            
            # Save to CSV
            filename = f"nepse_latest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.data_folder, filename)
            df.to_csv(filepath, index=False)
            
            print(f"Successfully scraped {len(securities_data)} securities to {filename}")
            
            # Also save as JSON for API consumption
            json_filename = f"nepse_latest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_filepath = os.path.join(self.data_folder, json_filename)
            
            with open(json_filepath, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'count': len(securities_data),
                    'data': securities_data[:10]  # Save only first 10 for size
                }, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error scraping data: {e}")
            return False
    
    def scrape_specific_securities(self, symbols: List[str]) -> bool:
        """Scrape specific securities with recent history."""
        try:
            print(f"Scraping data for: {', '.join(symbols)}")
            
            dates = self.get_trading_dates(30)
            all_data = []
            
            for date_str in dates:
                if not self.running:
                    break
                    
                print(f"Fetching data for {date_str}...")
                
                try:
                    daily_data = self.scraper.get_today_price(date_str)
                    
                    if isinstance(daily_data, dict) and 'content' in daily_data:
                        securities_list = daily_data['content']
                    elif isinstance(daily_data, list):
                        securities_list = daily_data
                    else:
                        securities_list = daily_data
                    
                    # Filter for requested symbols
                    for security in securities_list:
                        if security.get('symbol') in symbols:
                            security['date'] = date_str
                            all_data.append(security)
                
                except Exception as e:
                    print(f"Error fetching data for {date_str}: {e}")
                    continue
                
                # Sleep between requests
                if self.running:
                    import time
                    time.sleep(self.delay)
            
            if all_data:
                df = pd.DataFrame(all_data)
                
                # Save combined data
                filename = f"nepse_specific_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.data_folder, filename)
                df.to_csv(filepath, index=False)
                
                print(f"Saved {len(all_data)} records to {filename}")
                
                # Save individual files
                for symbol in symbols:
                    symbol_data = df[df['symbol'] == symbol]
                    if not symbol_data.empty:
                        symbol_file = os.path.join(self.data_folder, f"{symbol}_data.csv")
                        symbol_data.to_csv(symbol_file, index=False)
                
                return True
            else:
                print("No data found for specified securities.")
                return False
                
        except Exception as e:
            print(f"Error scraping specific securities: {e}")
            return False
    
    def run_continuous(self, interval_minutes: int = 60):
        """Run scraper continuously at specified intervals."""
        print(f"Starting continuous scraping every {interval_minutes} minutes...")
        print("Press Ctrl+C to stop.")
        
        import time
        
        while self.running:
            try:
                print(f"\n[{datetime.now()}] Starting scrape cycle...")
                
                success = self.scrape_latest_data()
                if success:
                    print("Scrape cycle completed successfully")
                else:
                    print("Scrape cycle failed")
                
                # Wait for next cycle
                for _ in range(interval_minutes * 60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nStopping continuous scraping...")
                break
            except Exception as e:
                print(f"Error in continuous scraping: {e}")
                time.sleep(60)  # Wait a minute before retry


def main():
    """Main function with environment-based configuration."""
    scraper = ContainerNepseScraper()
    
    # Get operation mode from environment
    mode = os.getenv('SCRAPER_MODE', 'interactive')
    
    if mode == 'latest':
        # Scrape latest data once
        success = scraper.scrape_latest_data()
        sys.exit(0 if success else 1)
    
    elif mode == 'continuous':
        # Run continuously
        interval = int(os.getenv('SCRAPER_INTERVAL', '60'))
        scraper.run_continuous(interval)
    
    elif mode == 'specific':
        # Scrape specific securities from environment variable
        symbols_env = os.getenv('SYMBOLS', 'NABIL,NICA,SCBL')
        symbols = [s.strip() for s in symbols_env.split(',')]
        success = scraper.scrape_specific_securities(symbols)
        sys.exit(0 if success else 1)
    
    else:
        # Interactive mode
        print("\nContainer NEPSE Scraper")
        print("=" * 40)
        print("Available modes (set SCRAPER_MODE env var):")
        print("  latest - Scrape latest data once")
        print("  continuous - Run continuously")
        print("  specific - Scrape specific symbols (set SYMBOLS env var)")
        print("  interactive - This menu (default)")
        
        while scraper.running:
            print("\nChoose an option:")
            print("1. Scrape latest data")
            print("2. Start continuous scraping")
            print("3. Scrape specific securities")
            print("4. Exit")
            
            try:
                choice = input("\nEnter choice (1-4): ").strip()
                
                if choice == '1':
                    scraper.scrape_latest_data()
                
                elif choice == '2':
                    interval = input("Enter interval in minutes (default 60): ").strip()
                    interval = int(interval) if interval else 60
                    scraper.run_continuous(interval)
                
                elif choice == '3':
                    symbols_input = input("Enter symbols (comma-separated): ").strip()
                    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
                    if symbols:
                        scraper.scrape_specific_securities(symbols)
                
                elif choice == '4':
                    print("Goodbye!")
                    break
                
                else:
                    print("Invalid choice.")
                    
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break


if __name__ == "__main__":
    main()
