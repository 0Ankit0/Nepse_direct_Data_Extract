
import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright

REPORTS_URL = 'https://www.nepalstock.com/reports/annual-reports'
BASE_DOWNLOAD_DIR = 'nepse_annual_reports'

def scrape_annual_report_excels():
    """Download all annual report Excels, use Name field as folder, and save each sheet as CSV in that folder."""
    import re
    os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)
    print("Starting annual report Excel scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        print(f"Navigating to {REPORTS_URL}")
        page.goto(REPORTS_URL, timeout=60000, wait_until='domcontentloaded')
        time.sleep(2)
        # Set items per page to 500 and click Filter
        try:
            per_page_select = page.query_selector('div.table__perpage select')
            if per_page_select:
                per_page_select.select_option('500')
                print("Set items per page to 500.")
                time.sleep(1)
        except Exception as e:
            print(f"Could not set items per page: {e}")
        try:
            filter_btn = page.query_selector('button.box__filter--search, button:has-text("Filter")')
            if filter_btn:
                filter_btn.click()
                print("Clicked Filter button.")
                time.sleep(2)
        except Exception as e:
            print(f"Could not click Filter button: {e}")
        time.sleep(2)
        # Find the table and all rows
        table = page.query_selector('div.table-responsive')
        if not table:
            print("No reports table found.")
            browser.close()
            return
        rows = table.query_selector_all('tr')[1:]  # skip header
        print(f"Found {len(rows)} reports.")
        for idx, row in enumerate(rows, 1):
            try:
                cells = row.query_selector_all('td')
                if not cells or len(cells) < 2:
                    continue
                # Name is in the second cell (index 1)
                name = cells[1].text_content().strip()
                # Find Excel download link in this row
                excel_link = row.query_selector('a[download][href$=".xlsx"], a[download][href$=".xls"]')
                if not excel_link:
                    print(f"[{idx}] No Excel download link for {name}")
                    continue
                with page.expect_download() as download_info:
                    excel_link.click()
                download = download_info.value
                filename = download.suggested_filename
                # Use Name field as folder name (sanitize)
                safe_name = re.sub(r'[^\w\-_ ]', '_', name)
                name_dir = os.path.join(BASE_DOWNLOAD_DIR, safe_name)
                os.makedirs(name_dir, exist_ok=True)
                local_excel_path = os.path.join(name_dir, filename)
                download.save_as(local_excel_path)
                print(f"[{idx}] Downloaded Excel for {name}: {filename}")
                # Read Excel and save each sheet as CSV
                xls = pd.ExcelFile(local_excel_path)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    safe_sheet = re.sub(r'[^\w\-_ ]', '_', sheet_name)
                    csv_path = os.path.join(name_dir, f"{safe_sheet}.csv")
                    df.to_csv(csv_path, index=False)
                    print(f"    Saved sheet '{sheet_name}' to {csv_path}")
            except Exception as e:
                print(f"[{idx}] Error for {name if 'name' in locals() else 'unknown'}: {e}")
        browser.close()
    print("All Excel reports processed.")

def main():
    scrape_annual_report_excels()

if __name__ == '__main__':
    main()
