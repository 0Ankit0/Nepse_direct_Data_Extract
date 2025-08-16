import os
import csv
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
data_folder = 'sharesansarTSP'
url = 'https://www.sharesansar.com/today-share-price'
start_date = datetime(2020, 1, 1)
end_date = datetime.now()

# Ensure output folder exists
os.makedirs(data_folder, exist_ok=True)

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

def scrape_date(date_str, csv_path, url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f'Processing {date_str}...')
        page.goto(url, timeout=60000)
        page.wait_for_selector('input[name="date"]', timeout=20000)
        page.fill('input[name="date"]', date_str)
        page.click('#btn_todayshareprice_submit')
        try:
            page.wait_for_selector('table#headFixed', timeout=20000)
        except:
            print(f'No table for {date_str}')
            browser.close()
            return
        table = page.query_selector('table#headFixed')
        if not table:
            print(f'No table for {date_str}')
        elif save_table_to_csv(table, csv_path):
            print(f'Saved {csv_path}')
        else:
            print(f'Empty table for {date_str}')
        browser.close()

def main():
    # First step: Check what dates need to be scraped before launching browser
    dates_to_scrape = []
    current_date = start_date
    print("Checking existing files...")
    while current_date <= end_date:
        if is_weekend(current_date):
            current_date += timedelta(days=1)
            continue
        date_str = current_date.strftime('%Y-%m-%d')
        csv_path = os.path.join(data_folder, f'{date_str}.csv')
        if not os.path.exists(csv_path):
            print(f'Will scrape {date_str} (saving to {csv_path})')
            dates_to_scrape.append((date_str, csv_path))
        current_date += timedelta(days=1)
    
    # If no dates need scraping, exit without launching browser
    if not dates_to_scrape:
        print("All files already exist. No browser scraping needed.")
        return
    
    print(f"Found {len(dates_to_scrape)} dates to scrape. Launching concurrent scrapers...")
    max_workers = 4  # Adjust based on your system/network
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(scrape_date, date_str, csv_path, url)
            for date_str, csv_path in dates_to_scrape
        ]
        for future in as_completed(futures):
            pass  # All output is handled in scrape_date

# Ensure main() is called when the script is run directly
if __name__ == '__main__':
    main()