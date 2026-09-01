"""Print a member's full Letterboxd watchlist and save it to results/."""

import os

from letterboxd import fetch_all_poster_items

USERNAME = "mfhcor"
OUTPUT_FILE = os.path.join("results", "my_watchlist.txt")


def get_full_watchlist(username: str = USERNAME) -> list[dict]:
    return fetch_all_poster_items(
        f"/{username}/watchlist/",
        on_page=lambda page: print(f"Fetching page {page}..."),
    )


if __name__ == "__main__":
    watchlist = get_full_watchlist()

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    lines = [f"{film['title']} ({film['year']})" for film in watchlist]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Watchlist for {USERNAME} ({len(watchlist)} films):\n\n")
        f.write("\n".join(lines) + "\n")

    print(f"\nWatchlist for {USERNAME} ({len(watchlist)} films):\n")
    print("\n".join(lines))
    print(f"\nSaved to {OUTPUT_FILE}")
