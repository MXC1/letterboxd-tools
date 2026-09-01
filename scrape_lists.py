"""Scrape one or more Letterboxd lists and write every film to a file.

Usage:
    python3 scrape_lists.py                         # use the LISTS below
    python3 scrape_lists.py URL [URL ...]           # scrape given list URLs
    python3 scrape_lists.py -o out.txt URL [URL]    # custom output path

Works with any list-shaped Letterboxd URL: /<user>/list/<slug>/ and also
/<user>/watchlist/ and /<user>/films/.
"""

import argparse
import os

from letterboxd import fetch_all_poster_items, get_soup

# Edit this list, or pass URLs on the command line.
LISTS = [
    "https://letterboxd.com/mfhcor/list/download/",
    "https://letterboxd.com/mfhcor/list/download-1080p/",
]

DEFAULT_OUTPUT = os.path.join("results", "scraped_lists.txt")


def list_title(url: str) -> str:
    try:
        title = get_soup(url).select_one("h1.title-1, meta[property='og:title']")
        if title is not None:
            return title.get("content") if title.name == "meta" else title.get_text(strip=True)
    except Exception:
        pass
    return url


def scrape_list(url: str) -> list[dict]:
    return fetch_all_poster_items(
        url, on_page=lambda page: print(f"  page {page}...")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("urls", nargs="*", default=None, help="Letterboxd list URLs")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help=f"output file (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    urls = args.urls or LISTS

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    total = 0
    with open(args.output, "w", encoding="utf-8") as out:
        for url in urls:
            title = list_title(url)
            print(f"Scraping {title} ({url})")
            films = scrape_list(url)
            total += len(films)

            out.write(f"# {title}\n")
            out.write(f"# {url}\n")
            out.write(f"# {len(films)} films\n\n")
            for film in films:
                out.write(f"{film['title']} ({film['year']})\n")
            out.write("\n")
            print(f"  {len(films)} films")

    print(f"\nWrote {total} films from {len(urls)} list(s) to {args.output}")


if __name__ == "__main__":
    main()
