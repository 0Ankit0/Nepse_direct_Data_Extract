import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_company_listings():
    """Scrape company listings from Nepal Stock Exchange website"""
    
    # Try multiple URLs that might have company listings
    url = 'https://www.nepalstock.com/company'

    companies = []
    
    print("Starting Nepal Stock Exchange company listings scraper...")
    url = 'https://www.nepalstock.com/company'
    print(f"\nTrying URL: {url}")
    with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-http2',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run'
                ]
            )
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768},
                ignore_https_errors=True,
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Cache-Control': 'no-cache'
                }
            )
            page = context.new_page()
            max_retries = 3
            success = False
            for attempt in range(max_retries):
                try:
                    print(f"Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                    page.goto(url, timeout=60000, wait_until='domcontentloaded')
                    success = True
                    break
                except Exception as e:
                    print(f"Error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        print("All attempts failed for this URL")
                    time.sleep(2)
            if not success:
                browser.close()
                return companies
            print("Page loaded successfully!")
            time.sleep(2)
            try:
                # Set Items Per Page to 500
                per_page_select = page.query_selector('div.table__perpage select')
                if per_page_select:
                    per_page_select.select_option('500')
                    print("Set items per page to 500.")
                    time.sleep(1)
            except Exception as e:
                print(f"Could not set items per page: {e}")
            try:
                # Select 'All Instrument' in the instrument dropdown
                instrument_selects = page.query_selector_all('select')
                for sel in instrument_selects:
                    options = sel.query_selector_all('option')
                    for opt in options:
                        if 'All Instrument' in (opt.text_content() or ''):
                            sel.select_option('')
                            print("Selected 'All Instrument'.")
                            time.sleep(1)
                            break
            except Exception as e:
                print(f"Could not select 'All Instrument': {e}")
            try:
                # Click the Filter button
                filter_btn = page.query_selector('button.box__filter--search, button:has-text("Filter")')
                if filter_btn:
                    filter_btn.click()
                    print("Clicked Filter button.")
                    time.sleep(2)
            except Exception as e:
                print(f"Could not click Filter button: {e}")
            time.sleep(2)
            # Extract the table
            table = None
            try:
                table = page.query_selector('div.table-responsive')
                if not table:
                    table = page.query_selector('.table-responsive')
                if not table:
                    print("No table found with selector 'table-responsive'.")
                    browser.close()
                    return companies
            except Exception as e:
                print(f"Error finding table: {e}")
                browser.close()
                return companies
            rows = table.query_selector_all('tr')
            print(f"Found {len(rows)} rows in table")
            if len(rows) < 2:
                print("Table has insufficient rows")
                browser.close()
                return companies
            # Get headers
            headers = []
            header_row = rows[0]
            header_cells = header_row.query_selector_all('th, td')
            for cell in header_cells:
                try:
                    text = cell.text_content() or ""
                    headers.append(text.strip())
                except:
                    headers.append("")
            print(f"Headers: {headers}")
            # Extract data rows
            for row in rows[1:]:
                cells = row.query_selector_all('td')
                if len(cells) >= len(headers):
                    company_data = {}
                    for i, cell in enumerate(cells[:len(headers)]):
                        try:
                            text = cell.text_content() or ""
                            if i < len(headers):
                                company_data[headers[i]] = text.strip()
                        except:
                            if i < len(headers):
                                company_data[headers[i]] = ""
                    if company_data:
                        companies.append(company_data)
            print(f"Successfully extracted {len(companies)} companies")
            browser.close()
            # No break needed, single URL
    output_data = {
        "scraping_info": {
            "source_url": "https://www.nepalstock.com/company",
            "scraped_at": datetime.now().isoformat(),
            "total_companies": len(companies)
        },
        "companies": companies
    }
    
    filename = "Company_listings.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved {len(companies)} companies to {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")
        return False

def main():
    """Main function"""
    
    # Scrape the company listings and save to JSON
    success = scrape_company_listings()
    if success:
        print("\nScraping completed successfully!")
        # Optionally, load and print a sample
        try:
            with open('Company_listings.json', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Total companies scraped: {data['scraping_info']['total_companies']}")
            if data['companies']:
                print("\nSample company data:")
                print(json.dumps(data['companies'][0], indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Could not load or print sample data: {e}")
    else:
        print("No companies data was scraped")

if __name__ == '__main__':
    main()
