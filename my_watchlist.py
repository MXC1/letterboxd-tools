import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Configuration ─────────────────────────────────────────────────────────────
USERNAME = "mfhcor"
CHROMEDRIVER_PATH = r"chromedriver\win64\147.0.7727.117\chromedriver.exe"
# ─────────────────────────────────────────────────────────────────────────────

_YEAR_RE = re.compile(r"^(.*?)\s*\((\d{4})\)$")


def _parse_item_name(item_name: str) -> dict:
    """Split 'Film Title (1999)' into {title, year}. Year defaults to 'Unknown'."""
    m = _YEAR_RE.match(item_name)
    if m:
        return {"title": m.group(1), "year": m.group(2)}
    return {"title": item_name, "year": "Unknown"}


def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)


def get_watchlist_page(driver: webdriver.Chrome, page_num: int) -> list[dict]:
    """Load a single watchlist page and return a list of {title, year} dicts."""
    url = f"https://letterboxd.com/{USERNAME}/watchlist/page/{page_num}/"
    driver.get(url)

    # Wait for at least one LazyPoster react component to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.react-component[data-component-class='LazyPoster']")
            )
        )
    except Exception:
        return []

    soup = BeautifulSoup(driver.page_source, "html.parser")
    films = []

    for div in soup.find_all("div", class_="react-component",
                             attrs={"data-component-class": "LazyPoster"}):
        item_name = div.get("data-item-name")
        if item_name:
            films.append(_parse_item_name(item_name))

    return films


def get_full_watchlist() -> list[dict]:
    """Paginate through the watchlist until an empty page is returned."""
    driver = make_driver()
    all_films = []
    page_num = 1

    try:
        while True:
            print(f"Fetching page {page_num}...")
            films = get_watchlist_page(driver, page_num)
            if not films:
                break
            all_films.extend(films)
            page_num += 1
    finally:
        driver.quit()

    return all_films


if __name__ == "__main__":
    watchlist = get_full_watchlist()

    print(f"\nWatchlist for {USERNAME} ({len(watchlist)} films):\n")
    for film in watchlist:
        print(f"{film['title']} ({film['year']})")
