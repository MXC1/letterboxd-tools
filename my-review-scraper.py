import os
import random
import time

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Configuration ─────────────────────────────────────────────────────────────
USERNAME = "mfhcor"
CHROMEDRIVER_PATH = r"chromedriver\win64\152.0.7977.64\chromedriver.exe"
OUTPUT_FILE = os.path.join("results", "my_letterboxd_reviews.txt")
# ─────────────────────────────────────────────────────────────────────────────


def make_driver() -> webdriver.Chrome:
    options = Options()
    # Letterboxd sits behind Cloudflare, which fingerprints headless Chrome
    # (even with anti-automation flags) and blocks pagination past page 1
    # with an unsolvable "Just a moment..." challenge. A real, visible
    # browser window passes reliably, so headless mode is intentionally
    # not used here.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)


CHALLENGE_TITLE = "Just a moment..."
MAX_CHALLENGE_RETRIES = 4


def get_reviews_page(driver: webdriver.Chrome, page_num: int) -> list:
    """Load a single reviews page and return its review article elements.

    Letterboxd's Cloudflare bot check occasionally serves an interactive
    "Just a moment..." challenge instead of the real page, even with a
    real browser. Retry a few times rather than mistaking a challenge for
    the end of the review list.
    """
    url = f"https://letterboxd.com/{USERNAME}/films/reviews/page/{page_num}/"

    for attempt in range(1, MAX_CHALLENGE_RETRIES + 1):
        driver.get(url)

        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.title != CHALLENGE_TITLE
                or d.find_elements(By.CSS_SELECTOR, "article.production-viewing")
            )
        except Exception:
            pass

        if driver.title != CHALLENGE_TITLE:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            return soup.select("article.production-viewing")

        print(f"  Blocked by Cloudflare challenge on page {page_num}, retrying ({attempt}/{MAX_CHALLENGE_RETRIES})...")
        time.sleep(3 * attempt)

    raise RuntimeError(
        f"Could not get past Cloudflare's challenge for page {page_num} after "
        f"{MAX_CHALLENGE_RETRIES} attempts."
    )


def render_inline(node) -> str:
    """Render an inline HTML node to text, keeping line breaks and italics."""
    if isinstance(node, NavigableString):
        return str(node)
    if node.name == "br":
        return "\n"
    inner = "".join(render_inline(child) for child in node.children)
    if node.name in ("i", "em"):
        return f"*{inner}*"
    if node.name in ("b", "strong"):
        return f"**{inner}**"
    return inner


def render_review_body(body_el) -> str:
    """Convert a review body element to text, preserving paragraphs/line breaks/italics."""
    paragraphs = body_el.find_all("p", recursive=False)
    if not paragraphs:
        return "".join(render_inline(child) for child in body_el.children).strip()

    rendered = ["".join(render_inline(child) for child in p.children).strip() for p in paragraphs]
    return "\n\n".join(p for p in rendered if p)


def extract_review(article) -> dict:
    title = article.select_one("h2.primaryname a").text.strip()

    year_el = article.select_one("span.releasedate a")
    year = year_el.text.strip() if year_el else "Unknown"

    rating_el = article.select_one("span.inline-rating svg title")
    rating = rating_el.text.strip() if rating_el else "No rating"

    body_el = article.select_one("div.js-review-body")
    review_text = render_review_body(body_el) if body_el else ""

    return {"title": title, "year": year, "rating": rating, "review": review_text}


def main() -> None:
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    driver = make_driver()
    page_num = 1

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            while True:
                if page_num > 1:
                    # A short, randomized pause between pages avoids the
                    # bursty request pattern that trips Cloudflare's bot check.
                    time.sleep(random.uniform(2, 4))

                print(f"Fetching page {page_num}...")
                articles = get_reviews_page(driver, page_num)
                if not articles:
                    break

                for article in articles:
                    review = extract_review(article)
                    file.write(f"Title: {review['title']} ({review['year']})\n")
                    file.write(f"Rating: {review['rating']}\n")
                    file.write(f"Review: {review['review']}\n")
                    file.write("\n" + "=" * 40 + "\n\n")

                print(f"Page {page_num} processed.")
                page_num += 1
    finally:
        driver.quit()

    print("All reviews fetched and saved.")


if __name__ == "__main__":
    main()
