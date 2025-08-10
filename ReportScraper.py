import os
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# Constants
base_url = 'https://merolagani.com/CompanyReports.aspx?type=ANNUAL'
reports_folder = 'reports'
start_fiscal_year = 71  # Starting from 071-072
current_fiscal_year = 82  # Up to 082-083 based on the dropdown

# Ensure output folder exists
os.makedirs(reports_folder, exist_ok=True)

def clean_text(text):
    """Clean and normalize text data"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def extract_pdf_content(page, pdf_url):
    """Extract content from PDF page"""
    try:
        page.goto(pdf_url, timeout=60000)
        page.wait_for_load_state('networkidle', timeout=30000)
        # Wait up to 15 seconds for the embed.pdfobject to appear
        try:
            page.wait_for_selector('embed.pdfobject', timeout=15000)
        except Exception:
            time.sleep(3)  # fallback wait
        # Try to get the embed.pdfobject src
        try:
            pdf_embed_element = page.query_selector('embed.pdfobject')
            if pdf_embed_element:
                pdf_src = pdf_embed_element.get_attribute('src')
                if pdf_src and '.pdf' in pdf_src.lower():
                    return {
                        'pdf_url': pdf_src,
                        'pdf_embed_found': True,
                        'extraction_method': 'embed_pdfobject_class',
                        'source_url': pdf_url
                    }
        except Exception as embed_error:
            print(f"    Failed to extract via embed.pdfobject: {str(embed_error)}")
        # Fallback: try other methods (JavaScript, other embeds)
        try:
            page_content = page.content()
            js_patterns = [
                r"fileUrl\s*:\s*['\"]([^'\"]+\.pdf[^'\"]*)['\"]",
                r"src\s*:\s*['\"]([^'\"]+\.pdf[^'\"]*)['\"]",
                r"url\s*:\s*['\"]([^'\"]+\.pdf[^'\"]*)['\"]",
                r"['\"]([^'\"]*\.pdf[^'\"]*)['\"]"
            ]
            for pattern in js_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if 'http' in match or match.startswith('/'):
                            pdf_url2 = match if match.startswith('http') else f"https://images.merolagani.com{match}"
                            return {
                                'pdf_url': pdf_url2,
                                'pdf_embed_found': True,
                                'extraction_method': 'javascript_fileurl',
                                'source_url': pdf_url
                            }
        except Exception as js_error:
            print(f"    Failed to extract via JavaScript: {str(js_error)}")
        try:
            embed_elements = page.query_selector_all('embed, object, iframe')
            for element in embed_elements:
                src = element.get_attribute('src') or element.get_attribute('data')
                if src and '.pdf' in src.lower():
                    return {
                        'pdf_url': src,
                        'pdf_embed_found': True,
                        'extraction_method': 'embed_object_iframe',
                        'source_url': pdf_url
                    }
        except Exception as element_error:
            print(f"    Failed to extract via embed/object/iframe: {str(element_error)}")
        return {
            'pdf_url': None,
            'pdf_embed_found': False,
            'extraction_method': 'failed',
            'source_url': pdf_url,
            'error': 'No PDF URL found in page'
        }
    except Exception as e:
        print(f"    Error extracting PDF content: {str(e)}")
        return {
            'pdf_url': None,
            'pdf_embed_found': False,
            'extraction_method': 'error',
            'source_url': pdf_url,
            'error': str(e)
        }

def download_pdf_file(page, pdf_url, company_folder, fiscal_year, announcement_title):
    if not pdf_url:
        return None

    try:
        # Use only the fiscal year for the PDF filename, matching the JSON filename
        pdf_filename = f"FY_{fiscal_year}.pdf"
        pdf_path = os.path.join(company_folder, pdf_filename)

        # Download the PDF
        response = page.request.get(pdf_url)
        if response.status == 200:
            with open(pdf_path, 'wb') as f:
                f.write(response.body())
            return pdf_path
        else:
            print(f"Failed to download PDF: {response.status}")
            return None
    except Exception as e:
        print(f"Error downloading PDF: {str(e)}")
        return None

def download_pdfs_for_company(page, symbol, fiscal_year, announcement_links):
    """Download PDFs from announcement links"""
    try:
        # Create company folder
        company_folder = os.path.join(reports_folder, symbol.lower())
        os.makedirs(company_folder, exist_ok=True)
        
        pdf_downloaded = False
        
        for i, link in enumerate(announcement_links):
            print(f"    Processing announcement {i+1}/{len(announcement_links)}: {link['title'][:50]}...")
            
            # Extract PDF content from the announcement page
            pdf_content = extract_pdf_content(page, link['url'])
            
            # Download PDF if found
            if pdf_content.get('pdf_url'):
                pdf_path = download_pdf_file(page, pdf_content['pdf_url'], company_folder, fiscal_year, link['title'])
                
                if pdf_path:
                    print(f"    Downloaded PDF: {os.path.basename(pdf_path)}")
                    pdf_downloaded = True
                    break  # Only download first PDF found
                else:
                    print(f"    Failed to download PDF")
            else:
                print(f"    No PDF found in announcement")
            
            # Small delay between processing announcements
            time.sleep(1)
        
        return pdf_downloaded
        
    except Exception as e:
        print(f"Error downloading PDFs: {str(e)}")
        return False

def get_announcement_links(page, symbol, fiscal_year):
    """Get announcement links for a specific company and fiscal year"""
    try:
        print(f"  Getting announcement links for {symbol} FY {fiscal_year}...")
        
        # Navigate to the reports page
        print(f"    Navigating to {base_url}")
        page.goto(base_url, timeout=60000)
        
        try:
            page.wait_for_load_state('networkidle', timeout=15000)
        except:
            try:
                page.wait_for_load_state('domcontentloaded', timeout=10000)
            except:
                time.sleep(5)
        
        # Debug: Take a screenshot and check what's on the page
        print(f"    Page loaded, looking for form elements...")
        
        # Try multiple possible selectors for the symbol input
        symbol_input = None
        symbol_selectors = [
            '#ctl00_ContentPlaceHolder1_ASCompanyFilter_txtAutoSuggest',
            'input[name*="txtAutoSuggest"]',
            'input[id*="txtAutoSuggest"]',
            '#ctl00_ContentPlaceHolder1_txtSymbol',
            'input[placeholder*="Stock Symbol"]',
            'input[placeholder*="symbol"]'
        ]
        
        for selector in symbol_selectors:
            symbol_input = page.query_selector(selector)
            if symbol_input:
                print(f"    Found symbol input with selector: {selector}")
                break
        
        if not symbol_input:
            print(f"    Symbol input not found with any selector. Available inputs:")
            all_inputs = page.query_selector_all('input')
            for i, inp in enumerate(all_inputs[:10]):  # Show first 10 inputs
                inp_id = inp.get_attribute('id') or 'no-id'
                inp_name = inp.get_attribute('name') or 'no-name'
                inp_placeholder = inp.get_attribute('placeholder') or 'no-placeholder'
                print(f"      Input {i}: id='{inp_id}', name='{inp_name}', placeholder='{inp_placeholder}'")
            return []
        
        # Enter the company symbol
        print(f"    Entering symbol: {symbol}")
        symbol_input.fill('')  # Clear any existing text
        symbol_input.fill(symbol)
        time.sleep(2)
        
        # Handle autocomplete dropdown if it appears
        try:
            # Wait for autocomplete and click on first option if available
            page.wait_for_selector('.ui-autocomplete .ui-menu-item', timeout=3000)
            first_option = page.query_selector('.ui-autocomplete .ui-menu-item:first-child')
            if first_option:
                first_option.click()
                time.sleep(1)
                print(f"    Selected autocomplete option")
        except:
            # No autocomplete appeared, continue
            print(f"    No autocomplete found, continuing...")
            pass
        
        # Select fiscal year
        print(f"    Selecting fiscal year: {fiscal_year}")
        fiscal_year_selectors = [
            '#ctl00_ContentPlaceHolder1_ddlFiscalYearFilter',
            'select[name*="ddlFiscalYearFilter"]',
            'select[id*="ddlFiscalYearFilter"]',
            '#ctl00_ContentPlaceHolder1_ddlFiscalYear',
            'select[name*="ddlFiscalYear"]'
        ]
        
        fiscal_year_select = None
        fiscal_year_selector_used = None
        for selector in fiscal_year_selectors:
            fiscal_year_select = page.query_selector(selector)
            if fiscal_year_select:
                fiscal_year_selector_used = selector
                print(f"    Found fiscal year dropdown with selector: {selector}")
                break
        
        if fiscal_year_select:
            page.select_option(fiscal_year_selector_used, fiscal_year)
            time.sleep(1)
        else:
            print(f"    Fiscal year dropdown not found. Available selects:")
            all_selects = page.query_selector_all('select')
            for i, sel in enumerate(all_selects[:5]):  # Show first 5 selects
                sel_id = sel.get_attribute('id') or 'no-id'
                sel_name = sel.get_attribute('name') or 'no-name'
                print(f"      Select {i}: id='{sel_id}', name='{sel_name}'")
            return []
        
        # Click search button
        print(f"    Clicking search button")
        search_button_selectors = [
            '#ctl00_ContentPlaceHolder1_lbtnSearch',
            'a[id*="lbtnSearch"]',
            'a[href*="lbtnSearch"]',
            '#ctl00_ContentPlaceHolder1_btnSearch',
            'input[name*="btnSearch"]',
            'a.btn.btn-primary'
        ]
        
        search_button = None
        for selector in search_button_selectors:
            search_button = page.query_selector(selector)
            if search_button:
                print(f"    Found search button with selector: {selector}")
                break
        
        if search_button:
            search_button.click()
            time.sleep(3)
            
            # Wait for results to load
            try:
                page.wait_for_load_state('networkidle', timeout=15000)
            except:
                time.sleep(5)
        else:
            print(f"    Search button not found. Available buttons/inputs:")
            all_buttons = page.query_selector_all('input[type="submit"], button')
            for i, btn in enumerate(all_buttons[:5]):  # Show first 5 buttons
                btn_id = btn.get_attribute('id') or 'no-id'
                btn_name = btn.get_attribute('name') or 'no-name'
                btn_value = btn.get_attribute('value') or 'no-value'
                print(f"      Button {i}: id='{btn_id}', name='{btn_name}', value='{btn_value}'")
            return []
        
        # Extract announcement links
        print(f"    Looking for announcement links...")
        announcement_elements = page.query_selector_all('.announcement-list .media, .media')
        
        print(f"    Found {len(announcement_elements)} elements with media class")
        
        links = []
        for element in announcement_elements:
            try:
                # Look for link in the element - the media div itself might be clickable
                link_element = element.query_selector('a[href*="AnnouncementDetail"]')
                if not link_element:
                    # Check if the media div itself has a click handler or data attributes
                    onclick = element.get_attribute('onclick')
                    if onclick and 'AnnouncementDetail' in onclick:
                        # Extract URL from onclick
                        import re
                        url_match = re.search(r"AnnouncementDetail\.aspx\?id=(\d+)", onclick)
                        if url_match:
                            announcement_id = url_match.group(1)
                            href = f"https://merolagani.com/AnnouncementDetail.aspx?id={announcement_id}"
                            title_element = element.query_selector('.media-body h5, .media-body h4, .media-body .media-heading, .media-body')
                            title = clean_text(title_element.inner_text() if title_element else 'No title')
                            
                            links.append({
                                'title': title,
                                'url': href
                            })
                            continue
                
                if link_element:
                    href = link_element.get_attribute('href')
                    title = clean_text(link_element.inner_text() or link_element.get_attribute('title') or 'No title')
                    
                    if href:
                        # Ensure full URL
                        if href.startswith('/'):
                            href = f"https://merolagani.com{href}"
                        elif not href.startswith('http'):
                            href = f"https://merolagani.com/{href}"
                        
                        links.append({
                            'title': title,
                            'url': href
                        })
            except Exception as link_error:
                print(f"    Error processing announcement element: {str(link_error)}")
                continue
        
        print(f"    Found {len(links)} announcement links")
        if links:
            for i, link in enumerate(links):
                print(f"      {i+1}. {link['title'][:50]}...")
        
        return links
        
    except Exception as e:
        print(f"Error getting announcement links: {str(e)}")
        return []

def scrape_company_report(page, symbol, fiscal_year):
    """Scrape company report for specific fiscal year"""
    try:
        print(f"  Scraping {symbol} FY {fiscal_year}...")
        
        # Get announcement links
        announcement_links = get_announcement_links(page, symbol, fiscal_year)
        
        # Download PDFs from the links
        success = download_pdfs_for_company(page, symbol, fiscal_year, announcement_links)
        return success
        
    except Exception as e:
        print(f"Error scraping {symbol} FY {fiscal_year}: {str(e)}")
        return False

def get_companies_from_fiscal_years():
    """Get list of companies by checking fiscal year options and common symbols"""
    # For now, return a predefined list of major companies
    # This can be expanded by scraping the actual dropdown or from a comprehensive list
    companies = [
        {'symbol': 'ADBL'}, {'symbol': 'NABIL'}, {'symbol': 'SCB'}, {'symbol': 'HBL'}, {'symbol': 'EBL'},
        {'symbol': 'BOKL'}, {'symbol': 'NICA'}, {'symbol': 'MBL'}, {'symbol': 'LBL'}, {'symbol': 'KBL'},
        {'symbol': 'MACHHAPUCHHRE'}, {'symbol': 'NMB'}, {'symbol': 'PRVU'}, {'symbol': 'SBL'}, {'symbol': 'NBL'},
        {'symbol': 'GBIME'}, {'symbol': 'CZBIL'}, {'symbol': 'SANIMA'}, {'symbol': 'MEGA'}, {'symbol': 'PCBL'},
        {'symbol': 'LAXMI'}, {'symbol': 'SUNRISE'}, {'symbol': 'CCBL'}, {'symbol': 'CIVIL'}, {'symbol': 'NTC'},
        {'symbol': 'NLIC'}, {'symbol': 'NLICL'}, {'symbol': 'PICL'}, {'symbol': 'LGIL'}, {'symbol': 'SICL'},
        {'symbol': 'NIL'}, {'symbol': 'PRIN'}, {'symbol': 'SIL'}, {'symbol': 'UIC'}, {'symbol': 'PIC'},
        {'symbol': 'CHDC'}, {'symbol': 'STC'}, {'symbol': 'AKPL'}, {'symbol': 'UPPER'}, {'symbol': 'CHCL'},
        {'symbol': 'SHPC'}, {'symbol': 'KPCL'}, {'symbol': 'NHPC'}, {'symbol': 'BPCL'}, {'symbol': 'HURJA'},
        {'symbol': 'RADHI'}, {'symbol': 'RURU'}, {'symbol': 'AKJCL'}, {'symbol': 'TRH'}, {'symbol': 'UMHL'},
        {'symbol': 'CHL'}, {'symbol': 'HPL'}, {'symbol': 'BARUN'}, {'symbol': 'UMRH'}, {'symbol': 'PMHPL'},
        {'symbol': 'MHNL'}, {'symbol': 'PPCL'}, {'symbol': 'NGPL'}, {'symbol': 'DHPL'}, {'symbol': 'SJCL'},
        {'symbol': 'RHPL'}, {'symbol': 'UNHPL'}, {'symbol': 'API'}, {'symbol': 'AHPC'}, {'symbol': 'BNHC'},
        {'symbol': 'JOSHI'}, {'symbol': 'ACLBSL'}, {'symbol': 'SLBSL'}, {'symbol': 'NLBBL'}, {'symbol': 'ADBL'},
        {'symbol': 'GILB'}, {'symbol': 'GBLBS'}, {'symbol': 'KLBSL'}, {'symbol': 'MLBSL'}, {'symbol': 'RLFL'}
    ]
    
    return companies


def main():
    print("Starting MeroLagani reports scraper...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Get list of companies to scrape
            print("Getting company list...")
            companies = get_companies_from_fiscal_years()
            
            print(f"Found {len(companies)} companies to process")
            
            # Scrape reports for each company and fiscal year
            for company in companies:
                symbol = company['symbol']
                print(f"\\nProcessing company: {symbol}")
                
                # Create company folder
                company_folder = os.path.join(reports_folder, symbol.lower())
                os.makedirs(company_folder, exist_ok=True)
                
                # Scrape each fiscal year from 071-072 to 082-083
                for fiscal_year in range(start_fiscal_year, current_fiscal_year + 1):
                    fiscal_year_str = f"{fiscal_year:03d}-{(fiscal_year+1):03d}"
                    
                    # Check if PDF file already exists
                    existing_pdf = os.path.join(company_folder, f"FY_{fiscal_year_str}.pdf")
                    if os.path.exists(existing_pdf):
                        print(f"  Skipping FY {fiscal_year_str} (PDF already exists)")
                        continue
                    
                    print(f"  Scraping FY {fiscal_year_str}...")
                    
                    # Scrape and download the report
                    success = scrape_company_report(page, symbol, fiscal_year_str)
                    
                    if success:
                        print(f"  Successfully downloaded report for FY {fiscal_year_str}")
                    else:
                        print(f"  No PDF found for FY {fiscal_year_str}")
                    
                    # Small delay between requests
                    time.sleep(2)
                
                # Longer delay between companies
                time.sleep(3)
        
        except Exception as e:
            print(f"Error in main process: {str(e)}")
        
        finally:
            browser.close()
    
    print("\\nScraping completed!")

if __name__ == '__main__':
    main()
