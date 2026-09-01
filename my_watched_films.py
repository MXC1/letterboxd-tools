"""Print the films a member has watched (from their /films/ grid)."""

from letterboxd import fetch_all_poster_items

USERNAME = "mfhcor"


def get_all_watched_films(username: str = USERNAME, max_pages: int = 5) -> list[dict]:
    return fetch_all_poster_items(
        f"/{username}/films/",
        max_pages=max_pages,
        on_page=lambda page: print(f"Fetching page {page}..."),
    )


if __name__ == "__main__":
    films = get_all_watched_films()
    print(f"\nFilms {USERNAME} has watched ({len(films)}):\n")
    for film in films:
        print(f"{film['title']} ({film['year']})")
