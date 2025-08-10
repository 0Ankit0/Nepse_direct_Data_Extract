#!/usr/bin/env python3
"""
ShareSansar TSP Scraper

Container-optimized scraper for ShareSansar Today's Share Price data
with support for continuous operation and environment-based configuration.
"""

import os
import csv
import sys
import signal
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# Constants with environment variable support
data_folder = os.getenv('TSP_DATA_FOLDER', 'sharesansarTSP')
url = os.getenv('SHARESANSAR_URL', 'https://www.sharesansar.com/today-share-price')
start_date = datetime(2020, 1, 1)
end_date = datetime.now()

# Ensure output folder exists
os.makedirs(data_folder, exist_ok=True)

class ShareSansarTSPScraper:
    """Container-optimized ShareSansar TSP scraper with continuous operation support."""
    
    def __init__(self):
        self.data_folder = data_folder
        self.url = url
        self.running = True
        self.delay = float(os.getenv('SCRAPER_DELAY', '1.0'))
        
        # Ensure output folder exists
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        print(f"ShareSansar TSP Scraper initialized")
        print(f"Data folder: {self.data_folder}")
        print(f"Delay between requests: {self.delay}s")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False

def is_weekend(date):
    # Friday = 4, Saturday = 5
    return date.weekday() in [4, 5]

def save_table_to_csv(table, filename):
    rows = table.query_selector_all('tr')
    if not rows or len(rows) < 2:
        return False
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in rows:
            cols = [col.inner_text().strip() for col in row.query_selector_all('th, td')]
            writer.writerow(cols)
    return True

    def is_weekend(self, date):
        """Check if date is weekend (Friday or Saturday in Nepal)."""
        # Friday = 4, Saturday = 5
        return date.weekday() in [4, 5]

    def save_table_to_csv(self, table, filename):
        """Save table data to CSV file."""
        try:
            rows = table.query_selector_all('tr')
            if not rows or len(rows) < 2:
                return False
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for row in rows:
                    cols = [col.inner_text().strip() for col in row.query_selector_all('th, td')]
                    writer.writerow(cols)
            return True
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False

    def scrape_date_data(self, target_date, page):
        """Scrape data for a specific date."""
        if self.is_weekend(target_date):
            return False
            
        date_str = target_date.strftime('%Y-%m-%d')
        csv_path = os.path.join(self.data_folder, f'{date_str}.csv')
        
        if os.path.exists(csv_path):
            print(f'Data for {date_str} already exists, skipping...')
            return True
            
        print(f'Processing {date_str}...')
        
        try:
            page.goto(self.url, timeout=60000)
            
            # Wait for date picker and set date
            page.wait_for_selector('input[name="date"]', timeout=20000)
            page.fill('input[name="date"]', date_str)
            
            # Click the search button to load the table
            page.click('#btn_todayshareprice_submit')
            
            # Wait for the table with id 'headFixed' to appear
            page.wait_for_selector('table#headFixed', timeout=20000)
            table = page.query_selector('table#headFixed')
            
            if not table:
                print(f'No table found for {date_str}')
                return False
                
            if self.save_table_to_csv(table, csv_path):
                print(f'Successfully saved {csv_path}')
                return True
            else:
                print(f'Empty table for {date_str}')
                return False
                
        except Exception as e:
            print(f'Error processing {date_str}: {e}')
            return False

    def scrape_historical_data(self, start_date=None, end_date=None):
        """Scrape historical data from start_date to end_date."""
        start_date = start_date or datetime(2020, 1, 1)
        end_date = end_date or datetime.now()
        
        print(f"Starting historical data scraping from {start_date.date()} to {end_date.date()}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            current_date = start_date
            success_count = 0
            total_count = 0
            
            while current_date <= end_date and self.running:
                if self.scrape_date_data(current_date, page):
                    success_count += 1
                total_count += 1
                current_date += timedelta(days=1)
                
                # Add delay between requests
                if self.delay > 0:
                    time.sleep(self.delay)
            
            browser.close()
            print(f"Historical scraping completed. {success_count}/{total_count} dates processed successfully.")
            return success_count > 0

    def scrape_recent_data(self, days_back=7):
        """Scrape recent data for the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"Scraping recent data for last {days_back} days")
        return self.scrape_historical_data(start_date, end_date)

    def run_continuous(self, interval_minutes=60):
        """Run scraper continuously at specified intervals."""
        print(f"Starting continuous scraping every {interval_minutes} minutes...")
        
        while self.running:
            try:
                print(f"\n[{datetime.now()}] Running scraper cycle...")
                success = self.scrape_recent_data(days_back=3)  # Check last 3 days
                
                if success:
                    print("Scraper cycle completed successfully")
                else:
                    print("Scraper cycle completed with some issues")
                
                if not self.running:
                    break
                
                # Wait for the specified interval
                print(f"Waiting {interval_minutes} minutes for next cycle...")
                for _ in range(interval_minutes * 60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nReceived interrupt signal...")
                break
            except Exception as e:
                print(f"Error in continuous scraping: {e}")
                if self.running:
                    print("Waiting 5 minutes before retry...")
                    time.sleep(300)  # Wait 5 minutes before retry
        
        print("Continuous scraping stopped.")


def main():
    """Main function with environment-based configuration."""
    scraper = ShareSansarTSPScraper()
    
    # Get operation mode from environment
    mode = os.getenv('SCRAPER_MODE', 'interactive')
    
    if mode == 'historical':
        # Full historical scrape
        success = scraper.scrape_historical_data()
        sys.exit(0 if success else 1)
    
    elif mode == 'recent':
        # Recent data only
        days_back = int(os.getenv('DAYS_BACK', '7'))
        success = scraper.scrape_recent_data(days_back)
        sys.exit(0 if success else 1)
    
    elif mode == 'continuous':
        # Run continuously
        interval = int(os.getenv('SCRAPER_INTERVAL', '60'))
        scraper.run_continuous(interval)
    
    else:
        # Interactive mode or legacy mode
        print("\nShareSansar TSP Scraper")
        print("=" * 40)
        print("Available modes (set SCRAPER_MODE env var):")
        print("  historical - Full historical scrape")
        print("  recent - Recent data only (set DAYS_BACK env var)")
        print("  continuous - Run continuously")
        print("  interactive - This menu (default)")
        
        # Legacy mode - run historical scrape if no environment mode set
        if mode == 'interactive':
            while scraper.running:
                print("\nChoose an option:")
                print("1. Full historical scrape")
                print("2. Recent data scrape")
                print("3. Start continuous scraping")
                print("4. Exit")
                
                try:
                    choice = input("\nEnter choice (1-4): ").strip()
                    
                    if choice == '1':
                        scraper.scrape_historical_data()
                    
                    elif choice == '2':
                        days = input("Enter days back (default 7): ").strip()
                        days = int(days) if days else 7
                        scraper.scrape_recent_data(days)
                    
                    elif choice == '3':
                        interval = input("Enter interval in minutes (default 60): ").strip()
                        interval = int(interval) if interval else 60
                        scraper.run_continuous(interval)
                    
                    elif choice == '4':
                        print("Goodbye!")
                        break
                    
                    else:
                        print("Invalid choice.")
                        
                except (KeyboardInterrupt, EOFError):
                    print("\nExiting...")
                    break
        else:
            # Legacy direct execution
            scraper.scrape_historical_data()


# Legacy functions for backward compatibility
def is_weekend(date):
    """Legacy function for backward compatibility."""
    return date.weekday() in [4, 5]

def save_table_to_csv(table, filename):
    """Legacy function for backward compatibility."""
    rows = table.query_selector_all('tr')
    if not rows or len(rows) < 2:
        return False
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in rows:
            cols = [col.inner_text().strip() for col in row.query_selector_all('th, td')]
            writer.writerow(cols)
    return True

if __name__ == '__main__':
    main()
