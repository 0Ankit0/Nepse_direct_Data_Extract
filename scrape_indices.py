import os
import time
import re
import pandas as pd
from playwright.sync_api import sync_playwright

INDICES_URL = 'https://www.nepalstock.com/indices'
BASE_DOWNLOAD_DIR = 'Indices'

def scrape_indices_tables():
    os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)
    print("Starting indices scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        print(f"Navigating to {INDICES_URL}")
        page.goto(INDICES_URL, timeout=60000, wait_until='domcontentloaded')
        time.sleep(2)
        # Set items per page to 500
        try:
            per_page_select = page.query_selector('div.table__perpage select')
            if per_page_select:
                per_page_select.select_option('500')
                print("Set items per page to 500.")
                time.sleep(1)
        except Exception as e:
            print(f"Could not set items per page: {e}")
        # Get the indices select element and all options
        indices_select = page.query_selector('select')
        if not indices_select:
            print("No indices select found.")
            browser.close()
            return
        options = indices_select.query_selector_all('option')
        for opt in options:
            value = opt.get_attribute('value')
            name = opt.text_content().strip()
            if not value or not name or value == '':
                continue
            print(f"Processing: {name}")
            # Select the index
            indices_select.select_option(value)
            time.sleep(0.5)
            # Click Filter
            try:
                filter_btn = page.query_selector('button.box__filter--search, button:has-text("Filter")')
                if filter_btn:
                    filter_btn.click()
                    time.sleep(2)
            except Exception as e:
                print(f"Could not click Filter button for {name}: {e}")
            # Wait for table
            table = page.query_selector('div.table-responsive table')
            if not table:
                print(f"No table found for {name}")
                continue
            # Get headers
            header_row = table.query_selector('thead tr')
            headers = [th.text_content().strip() for th in header_row.query_selector_all('th')]
            # Get data rows
            data = []
            for row in table.query_selector_all('tbody tr'):
                cells = row.query_selector_all('td')
                if len(cells) != len(headers):
                    continue
                data.append([cell.text_content().strip() for cell in cells])
            # Save as CSV
            safe_name = re.sub(r'[^\w\-_ ]', '_', name)
            csv_path = os.path.join(BASE_DOWNLOAD_DIR, f"{safe_name}.csv")
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(csv_path, index=False)
            print(f"Saved {name} to {csv_path}")
        browser.close()
    print("All indices tables saved.")

if __name__ == '__main__':
    scrape_indices_tables()
