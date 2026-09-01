import re

import requests
from bs4 import BeautifulSoup

from letterboxd import fetch_all_poster_items

PCC_URL = "https://princecharlescinema.com/whats-on/"
LETTERBOXD_USERNAME = "mfhcor"


def strip_year(title):
    return re.sub(r"\s*\(\d{4}\)$", "", title)

def get_letterboxd_watchlist(max_pages=10):
    items = fetch_all_poster_items(
        f"/{LETTERBOXD_USERNAME}/watchlist/", max_pages=max_pages
    )
    return {strip_year(item["name"]) for item in items}

def fetch_and_filter_pcc_html(watchlist):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(PCC_URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Find all film blocks
    for film_outer in soup.select('div.film_list-outer'):
        title_el = film_outer.select_one('.liveeventtitle')
        if not title_el:
            continue
        title = strip_year(title_el.get_text(strip=True))
        if title not in watchlist:
            parent_event = film_outer.find_parent('div', class_='jacro-event')
            if parent_event:
                parent_event.decompose()  # Remove the whole film block
            else:
                film_outer.decompose()  # Fallback: remove just the inner block
    return str(soup)

def main():
    print("Fetching Letterboxd watchlist...")
    watchlist = get_letterboxd_watchlist()
    print(f"Found {len(watchlist)} films in your Letterboxd watchlist.")
    print("Fetching and filtering PCC page...")
    filtered_html = fetch_and_filter_pcc_html(watchlist)
    out_path = "results/filtered_pcc_whats_on.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(filtered_html)
    print(f"Filtered HTML saved to {out_path}. Opening in your default browser...")
    import os
    import webbrowser
    abs_path = os.path.abspath(out_path)
    webbrowser.open(f'file://{abs_path}')

if __name__ == "__main__":
    main()
