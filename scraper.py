import csv
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from cookie_manager import CookieManager


BASE_URL = "https://pro.coinmarketcap.com/"
USAGE_URL = "https://pro.coinmarketcap.com/account/api-usage"
CSV_PATH = "api_usage.csv"


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    chrome_binary = os.getenv("CHROME_BINARY")
    if chrome_binary:
        options.binary_location = chrome_binary
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver


def wait_for_table(driver: webdriver.Chrome) -> None:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
    )


def parse_table_rows(driver: webdriver.Chrome) -> List[Dict[str, Any]]:
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    parsed: List[Dict[str, Any]] = []
    for row in rows:
        cells = [cell.text.strip() for cell in row.find_elements(By.CSS_SELECTOR, "td")]
        if len(cells) < 7:
            continue
        parsed.append(
            {
                "timestamp": cells[0],
                "request_number": cells[1],
                "http_status": cells[2],
                "ip_address": cells[3],
                "endpoint": cells[4],
                "request_time": cells[5],
                "credit_count": cells[6],
            }
        )
    return parsed


def write_csv(rows: List[Dict[str, Any]], path: str) -> None:
    fieldnames = [
        "timestamp",
        "request_number",
        "http_status",
        "ip_address",
        "endpoint",
        "request_time",
        "credit_count",
        "scraped_at",
    ]
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        scraped_at = datetime.now(timezone.utc).isoformat()
        for row in rows:
            row["scraped_at"] = scraped_at
            writer.writerow(row)


def scrape() -> int:
    manager = CookieManager()
    if not manager.validate_cookies():
        print("Cookies appear expired. Re-authentication required.", file=sys.stderr)
        return 2

    driver = build_driver()
    try:
        driver.get(BASE_URL)
        manager.inject_cookies(driver)
        driver.get(USAGE_URL)

        try:
            wait_for_table(driver)
        except TimeoutException:
            print("Timed out waiting for API usage table.", file=sys.stderr)
            return 3

        rows = parse_table_rows(driver)
        if not rows:
            print("No rows scraped. Check selectors or authentication.", file=sys.stderr)
            return 4

        write_csv(rows, CSV_PATH)
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(scrape())
