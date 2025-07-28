# Alibaba RFQ Web Scraper

A Python web scraper for extracting Request for Quotations (RFQ) data from Alibaba using Selenium.

## Features

- Scrapes product RFQ details like title, buyer, country, quantity, date posted, and more.
- Supports pagination and exports data to CSV and JSON.
- Automated browsing with Selenium and Chrome.


## Prerequisites

- Python 3.7 or newer.
- Google Chrome browser (latest version recommended).
- ChromeDriver that matches your Chrome version (Selenium Manager will auto-download it if using Selenium ≥4.6).


## Installation

Clone this repository and install dependencies:

```bash
git clone https://github.com/your-username/alibaba-rfq-scraper.git
cd alibaba-rfq-scraper
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```


## Usage

1. **Run the script:**

```bash
main.py
```

2. **When prompted,** enter a product keyword to search for RFQs (e.g., `electronics`).
3. The scraper will run and save the results as:
    - `alibaba_rfq_<your_keyword>.csv`
    - `alibaba_rfq_<your_keyword>.json`

## Output

- CSV and JSON files containing scraped RFQ data will be saved in the project directory.


## Notes

- Ensure your Chrome browser is up to date.
- Selenium requires a compatible ChromeDriver. For Selenium version 4.6 and higher, Selenium downloads the correct driver automatically. If not, download [ChromeDriver](https://chromedriver.chromium.org/downloads) matching your browser version and add it to your system PATH.
- Target website structure may change over time, which could break the scraper. In that case, review and update the selectors in the script.


## Troubleshooting

- If you see errors related to driver location, check your Selenium and ChromeDriver setup.
- Some anti-bot measures may require you to manually solve CAPTCHAs or update the scraping logic.




