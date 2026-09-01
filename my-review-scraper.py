"""Dump all of a member's Letterboxd reviews to a text file."""

import os

from bs4.element import NavigableString

from letterboxd import BlockedByChallenge, get_soup

# ── Configuration ─────────────────────────────────────────────────────────────
USERNAME = "mfhcor"
OUTPUT_FILE = os.path.join("results", "my_letterboxd_reviews.txt")
# ─────────────────────────────────────────────────────────────────────────────


def get_reviews_page(page_num: int) -> list:
    url = f"https://letterboxd.com/{USERNAME}/films/reviews/page/{page_num}/"
    soup = get_soup(url)
    return soup.select("article.production-viewing")


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

    page_num = 1
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        while True:
            print(f"Fetching page {page_num}...")
            try:
                articles = get_reviews_page(page_num)
            except BlockedByChallenge as exc:
                raise SystemExit(f"Letterboxd served a challenge and would not back off: {exc}")
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

    print("All reviews fetched and saved.")


if __name__ == "__main__":
    main()
