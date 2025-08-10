import os
import csv
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

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

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        current_date = start_date
        while current_date <= end_date:
            if is_weekend(current_date):
                current_date += timedelta(days=1)
                continue
            date_str = current_date.strftime('%Y-%m-%d')
            csv_path = os.path.join(data_folder, f'{date_str}.csv')
            if os.path.exists(csv_path):
                current_date += timedelta(days=1)
                continue
            print(f'Processing {date_str}...')
            page.goto(url, timeout=60000)
            # Wait for date picker and set date
            page.wait_for_selector('input[name="date"]', timeout=20000)
            page.fill('input[name="date"]', date_str)
            # Click the correct search button to load the table
            page.click('#btn_todayshareprice_submit')
            # Wait for the table with id 'headFixed' to appear
            try:
                page.wait_for_selector('table#headFixed', timeout=20000)
            except:
                print(f'No table for {date_str}')
                current_date += timedelta(days=1)
                continue
            table = page.query_selector('table#headFixed')
            if not table:
                print(f'No table for {date_str}')
                current_date += timedelta(days=1)
                continue
            if save_table_to_csv(table, csv_path):
                print(f'Saved {csv_path}')
            else:
                print(f'Empty table for {date_str}')
            current_date += timedelta(days=1)
        browser.close()

if __name__ == '__main__':
    main()
