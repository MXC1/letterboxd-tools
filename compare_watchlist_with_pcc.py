import requests
from bs4 import BeautifulSoup

# URL for Prince Charles Cinema "What's On"
PCC_URL = "https://princecharlescinema.com/whats-on/"
LETTERBOXD_URL = "https://letterboxd.com/mxc48/watchlist/"

def strip_year(title):
    import re
    return re.sub(r"\s*\(\d{4}\)$", "", title)

def format_screening_datetime(dt_str):
    # Example input: 'Thursday 16th October 6:10 pm'
    import re
    match = re.match(r"([A-Za-z]+) (\d{1,2}(?:st|nd|rd|th)?) ([A-Za-z]+) (\d{1,2}:\d{2} [ap]m)", dt_str)
    if match:
        weekday, day, month, time = match.groups()
        return f"{weekday:<9} {day:<4} {month:<9} {time:<7}"
    else:
        return dt_str  # fallback

def get_pcc_films():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(PCC_URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    titles = set()
    for el in soup.select('.liveeventtitle'):
        title = el.get_text(strip=True)
        if title:
            titles.add(title)
    return titles

def get_letterboxd_watchlist(max_pages=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    films = set()
    for page_num in range(1, max_pages + 1):
        url = f"{LETTERBOXD_URL}page/{page_num}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        found = False
        for div in soup.find_all("div", class_="react-component"):
            film_name = div.get("data-item-name")
            if film_name:
                films.add(film_name)
                found = True
        if not found:
            break  # Stop if no films found on this page
    return films

def get_pcc_films_with_times():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(PCC_URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    films = {}
    for film_outer in soup.select('div.film_list-outer'):
        title_el = film_outer.select_one('.liveeventtitle')
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        screenings = []
        for perf_outer in film_outer.select('div.performance-list-items-outer'):
            ul = perf_outer.select_one('ul.performance-list-items')
            if not ul:
                continue
            current_date = None
            for child in ul.children:
                # child can be a Tag or NavigableString
                if getattr(child, 'name', None) == 'div' and 'heading' in child.get('class', []):
                    current_date = child.get_text(strip=True)
                elif getattr(child, 'name', None) == 'li':
                    time_span = child.select_one('span.time')
                    time_text = time_span.get_text(strip=True) if time_span else None
                    if current_date and time_text:
                        screenings.append(f"{current_date} {time_text}")
        films[title] = screenings
    return films

def main():
    print("Fetching Prince Charles Cinema films...")
    pcc_films_with_times = get_pcc_films_with_times()
    pcc_films = set(pcc_films_with_times.keys())
    print(f"Found {len(pcc_films)} films at PCC.")

    print("Fetching Letterboxd watchlist...")
    letterboxd_films_raw = get_letterboxd_watchlist()
    letterboxd_films = set(strip_year(film) for film in letterboxd_films_raw)
    print(f"Found {len(letterboxd_films)} films in your Letterboxd watchlist.")

    # Print intersection of the two sets with screening times
    intersection_films = pcc_films & letterboxd_films
    print("\nFilms showing at Prince Charles Cinema that are also in your Letterboxd watchlist:")
    for film in sorted(intersection_films):
        print("")
        film_line = f"-- {film} --"
        line = '-' * len(film_line)
        print(f"{line:^40}")
        print(f"{film_line:^40}")
        print(f"{line:^40}")
        for screening in pcc_films_with_times[film]:
            print(f"  - {format_screening_datetime(screening)}")

if __name__ == "__main__":
    main()
