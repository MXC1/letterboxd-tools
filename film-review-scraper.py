"""Return pages of Letterboxd reviews for a single film in plaintext.

Useful if you want to analyse those reviews e.g. using AI.
"""

import pathlib

import requests
from bs4.element import NavigableString

from letterboxd import BlockedByChallenge, get_soup


def film_exists(slug: str) -> bool:
    try:
        get_soup(f"https://letterboxd.com/film/{slug}/")
        return True
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return False
        raise


def prompt_film() -> str:
    print("Enter the film you want to return reviews for.")
    print("Must be the same as it is in the URL on Letterboxd.")
    print("E.g: v-for-vendetta")
    while True:
        slug = input("Film: ").strip()
        if not slug:
            continue
        if film_exists(slug):
            return slug
        print("That film does not exist.")


def prompt_pages() -> int:
    pages = ""
    while not pages.isdigit():
        pages = input("How many pages of reviews to return: ").strip()
    return int(pages)


def render_inline(node) -> str:
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
    paragraphs = body_el.find_all("p", recursive=False)
    if not paragraphs:
        return "".join(render_inline(child) for child in body_el.children).strip()
    rendered = ["".join(render_inline(child) for child in p.children).strip() for p in paragraphs]
    return "\n\n".join(p for p in rendered if p)


def main() -> None:
    film = prompt_film()
    number_of_pages = prompt_pages()

    output_file_location = pathlib.Path.cwd() / f"{film}-{number_of_pages}.txt"
    print(f"Output file location: {output_file_location}")

    with open(output_file_location, "w", encoding="utf-8") as output_file:
        for page in range(1, number_of_pages + 1):
            url = f"https://letterboxd.com/film/{film}/reviews/page/{page}/"
            try:
                soup = get_soup(url)
            except BlockedByChallenge as exc:
                raise SystemExit(f"Letterboxd served a challenge and would not back off: {exc}")

            reviews = soup.select("article.production-viewing")
            if not reviews:
                break

            print(f"Parsing page: {page}")

            for review in reviews:
                rating_el = review.select_one("span.inline-rating svg title")
                body_el = review.select_one("div.js-review-body")
                if body_el is None:
                    continue

                for tag in body_el(["style", "script"]):
                    tag.decompose()
                for spoiler in body_el.select("p.contains-spoilers"):
                    spoiler.decompose()

                rating = rating_el.text.strip() if rating_el else "No Rating"
                output_file.write(f"{rating} - ")
                output_file.write(render_review_body(body_el).replace("\n", " ").strip())
                output_file.write("\n")

    print("Done!")


if __name__ == "__main__":
    main()
