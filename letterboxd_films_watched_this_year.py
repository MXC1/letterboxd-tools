import io
import math
import os
import re

from PIL import Image

from letterboxd import get, get_rss_items

# ── Configuration ────────────────────────────────────────────────────────────
USERNAME = "mfhcor"
YEAR = "2026"
OUTPUT_PATH = "results/watched_poster_2026.jpg"

CANVAS_W = 1080
CANVAS_H = 1920
COLS = 6          # posters per row
GAP = 5           # pixels between posters (and around the edges)
BG_COLOR = (12, 12, 12)  # near-black background
# ─────────────────────────────────────────────────────────────────────────────


def fetch_2026_posters(username: str, year: str) -> list[dict]:
    """
    Fetch diary entries from the Letterboxd RSS feed and return
    a list of {poster_url, watched_date, title} dicts for the given year,
    sorted chronologically.

    Note: the RSS feed returns the 50 most-recent diary entries.
    If you've watched more than 50 films since the start of the previous
    calendar year you may need to add manual entries.
    """
    films = []

    for rss_index, item in enumerate(get_rss_items(username)):
        watched_el = item.find("letterboxd:watchedDate")
        desc_el = item.find("description")
        title_el = item.find("letterboxd:filmTitle")

        if not (watched_el and desc_el):
            continue
        if not watched_el.text.strip().startswith(year):
            continue

        img_match = re.search(r'img src="([^"]+)"', desc_el.text)
        if not img_match:
            continue

        films.append(
            {
                "title": title_el.text.strip() if title_el else "Unknown",
                "watched_date": watched_el.text.strip(),
                "poster_url": img_match.group(1),
                "rss_index": rss_index,
            }
        )

    # RSS is newest-first, so a higher rss_index = logged earlier.
    # Sort by date ascending, then rss_index descending to preserve diary order
    # for films watched on the same day.
    films.sort(key=lambda f: (f["watched_date"], -f["rss_index"]))
    return films


def download_posters(films: list[dict]) -> list[Image.Image]:
    images = []
    total = len(films)
    for i, film in enumerate(films, 1):
        print(f"  [{i}/{total}] {film['title']} ({film['watched_date']})")
        try:
            resp = get(film["poster_url"])
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            images.append(img)
        except Exception as e:
            print(f"    ⚠  Could not download poster: {e}")
    return images


def build_poster(images: list[Image.Image]) -> Image.Image:
    n = len(images)
    rows = math.ceil(n / COLS)

    # Cell dimensions that fill the canvas with the given gap
    cell_w = (CANVAS_W - GAP * (COLS + 1)) // COLS
    cell_h = (CANVAS_H - GAP * (rows + 1)) // rows

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)

    for i, img in enumerate(images):
        row, col = divmod(i, COLS)

        # Centre the last (possibly incomplete) row
        films_in_this_row = min(COLS, n - row * COLS)
        total_row_w = films_in_this_row * cell_w + (films_in_this_row - 1) * GAP
        x_offset = (CANVAS_W - total_row_w) // 2

        x = x_offset + col * (cell_w + GAP)
        y = GAP + row * (cell_h + GAP)

        resized = img.resize((cell_w, cell_h), Image.LANCZOS)
        canvas.paste(resized, (x, y))

    return canvas


def main():
    os.makedirs("results", exist_ok=True)

    print(f"Fetching {YEAR} diary entries for @{USERNAME} …")
    films = fetch_2026_posters(USERNAME, YEAR)
    print(f"Found {len(films)} films watched in {YEAR}.\n")

    if not films:
        print("No films found — nothing to render.")
        return

    print("Downloading posters …")
    images = download_posters(films)
    print(f"\nSuccessfully downloaded {len(images)} posters.")

    print("Building poster …")
    poster = build_poster(images)
    poster.save(OUTPUT_PATH, "JPEG", quality=95)
    print(f"\nSaved → {OUTPUT_PATH}  ({CANVAS_W}×{CANVAS_H}px, {len(images)} films)")


if __name__ == "__main__":
    main()
