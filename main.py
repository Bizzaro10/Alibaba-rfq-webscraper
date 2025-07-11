from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import csv
import re
import urllib.parse

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_rfq_data(text):
    data = {}
    
    # Extract Title (everything before "Quantity Required:")
    title_match = re.split(r'Quantity Required:', text, 1)
    data['Title'] = title_match[0].strip() if len(title_match) > 0 else ""
    
    # Extract Quantity Required
    quantity_match = re.search(r'Quantity Required:\s*(\d+)\s*([^\n]+)', text)
    data['Quantity Required'] = f"{quantity_match.group(1)} {quantity_match.group(2).strip()}" if quantity_match else ""
    
    # Extract Posted in (Country)
    country_match = re.search(r'Posted in:\s*([^\n]+)', text)
    data['Country'] = country_match.group(1).strip() if country_match else ""
    
    # Extract Quotes Left
    quotes_match = re.search(r'Quotes Left\s*(\d+)', text)
    data['Quotes Left'] = quotes_match.group(1) if quotes_match else "0"
    
    # Extract Date Posted
    date_match = re.search(r'Date Posted:\s*([^\n]+)', text)
    data['Date Posted'] = date_match.group(1).strip() if date_match else ""
    
    # Extract Buyer Name
    lines = text.split('\n')
    buyer_name = ""
    
    # Find the line after "Date Posted:"
    for i, line in enumerate(lines):
        if 'Date Posted:' in line and i + 1 < len(lines):
            # Get the next few lines after "Date Posted:"
            for j in range(i + 1, min(i + 4, len(lines))):  # Look at next 3 lines maximum
                current_line = lines[j].strip()
                # Skip empty lines and lines with time indicators
                if not current_line or 'Quote Now' in current_line or 'hours before' in current_line or 'days ago' in current_line:
                    continue
                    
                # If line starts with a single letter and a space, take the rest of the line
                if len(current_line) > 2 and current_line[1] == ' ':
                    buyer_name = current_line[2:].strip()
                    break
                # If it's just a single letter, take the next non-empty line
                elif len(current_line) == 1:
                    # Look at the next line for the full name
                    if j + 1 < len(lines):
                        next_line = lines[j + 1].strip()
                        if next_line and 'Quote Now' not in next_line and 'Email Confirmed' not in next_line:
                            buyer_name = next_line
                            break
                # Otherwise take the current line if it doesn't contain badges
                elif not any(badge in current_line for badge in ['Email Confirmed', 'Typically replies', 'Interactive user', 'Complete order via RFQ']):
                    buyer_name = current_line
                    break
    
    # Clean up the buyer name
    if buyer_name:
        # Remove any remaining badges or status indicators
        buyer_name = re.sub(r'(Email Confirmed|Typically replies|Interactive user|Complete order via RFQ|Experienced buyer)', '', buyer_name).strip()
    
    data['Buyer Name'] = buyer_name
    
    # Check for badges
    data['Email Confirmed'] = 'yes' if 'Email Confirmed' in text else 'no'
    data['Experienced Buyer'] = 'yes' if 'Experienced buyer' in text else 'no'
    data['Complete Order'] = 'yes' if 'Complete order via RFQ' in text else 'no'
    
    return data

def get_total_pages(driver):
    try:
        # Wait for pagination element to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.next-pagination"))
        )
        
        # Try to find the last page number from the pagination buttons
        page_buttons = driver.find_elements(By.CSS_SELECTOR, "div.next-pagination button.next-btn")
        
        # Filter out non-numeric buttons (like next/prev arrows)
        page_numbers = [int(btn.text) for btn in page_buttons if btn.text.strip().isdigit()]
        
        if page_numbers:
            return max(page_numbers)
        
        # If no numbered buttons found, check if there's a next page button
        next_button = driver.find_elements(By.CSS_SELECTOR, "button.next-btn.next-next")
        if next_button:
            return 2  # At least 2 pages exist
            
    except Exception as e:
        print(f"Error detecting pagination: {str(e)}")
    return 1

def main():
    keyword = input("Enter product to search : ")
    
    driver = setup_driver()
    all_results = []
    current_page = 1
    
    try:
        # Open the Alibaba RFQ search page
        driver.get("https://sourcing.alibaba.com/rfq/rfq_search_list.htm?country=AE&recently=Y")
        time.sleep(3)
        
        # Handle cookies if they appear
        try:
            cookie_btn = driver.find_element(By.CSS_SELECTOR, "button[data-role='accept-all']")
            cookie_btn.click()
            time.sleep(1)
        except:
            pass
        
        # Locate search input and enter search term
        search_input = driver.find_element(By.NAME, 'SearchText')
        search_input.send_keys(keyword)
        time.sleep(5)
        
        # Locate and click the search button
        search_btn = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
        search_btn.click()
        
        # Wait for results to load
        time.sleep(10)

        while True:
            print(f"\nScraping page {current_page}")
            
            # Wait for RFQ items to be present
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.next-col.next-col-24.alife-bc-brh-rfq-list__col"))
                )
            except TimeoutException:
                print("No more items found, ending scraping")
                break
            
            # Find all RFQ items
            items = driver.find_elements(By.CSS_SELECTOR, "div.next-col.next-col-24.alife-bc-brh-rfq-list__col.js_alife-bc-brh-rfq-list_col")
            
            if not items:
                print("No items found on current page")
                break
            
            page_results = []
            for item in items:
                item_text = item.text
                if item_text:  # Only process non-empty items
                    rfq_data = scrape_rfq_data(item_text)
                    page_results.append(rfq_data)
                    print(f"Scraped: {rfq_data['Title'][:50]}... by {rfq_data['Buyer Name']}")
            
            all_results.extend(page_results)
            print(f"Scraped {len(page_results)} RFQs from page {current_page}")
            
            # Try to find and click the next page link
            try:
                # Look for the next page link using the page number
                next_page = current_page + 1
                next_page_xpath = f"//a[contains(@href, 'page={next_page}')]"
                
                # Wait for the next page link to be clickable
                next_page_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, next_page_xpath))
                )
                
                # Scroll the link into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_link)
                time.sleep(2)
                
                # Click the next page link
                next_page_link.click()
                print(f"Navigating to page {next_page}")
                current_page += 1
                
                # Wait for the page to load
                time.sleep(10)
                
            except TimeoutException:
                print(f"No link found for page {next_page}, ending scraping")
                break
            except Exception as e:
                print(f"Error navigating to next page: {str(e)}")
                break
        
        if all_results:
            # Save to CSV
            csv_filename = f"alibaba_rfq_{keyword.replace(' ', '_')}.csv"
            fieldnames = ['Title', 'Buyer Name', 'Posted in', 'Quotes Left', 'Country', 
                         'Quantity Required', 'Email Confirmed', 'Experienced Buyer', 
                         'Complete Order', 'Date Posted']
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in all_results:
                    row = {
                        'Title': item['Title'],
                        'Buyer Name': item['Buyer Name'],
                        'Posted in': item['Country'],  # Using Country as Posted in
                        'Quotes Left': item['Quotes Left'],
                        'Country': item['Country'],
                        'Quantity Required': item['Quantity Required'],
                        'Email Confirmed': item['Email Confirmed'],
                        'Experienced Buyer': item['Experienced Buyer'],
                        'Complete Order': item['Complete Order'],
                        'Date Posted': item['Date Posted']
                    }
                    writer.writerow(row)
            
            print(f"\nSuccessfully scraped {len(all_results)} RFQs from {current_page - 1} pages")
            print(f"Data saved to {csv_filename}")
            
            # Save to JSON as backup
            json_filename = f"alibaba_rfq_{keyword.replace(' ', '_')}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            
        else:
            print("No RFQs found matching your search")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()