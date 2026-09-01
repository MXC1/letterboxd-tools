# letterboxd-tools

A grab-bag of scripts for pulling data off Letterboxd (watchlist, watched
films, reviews, diary) and cross-referencing it with the Prince Charles
Cinema listings.

## Fetching approach

Every script fetches Letterboxd through `letterboxd.py`, which mirrors what the
[`letterboxd-list-radarr`](https://github.com/screeny05/letterboxd-list-radarr)
service does:

- one shared `requests.Session` with a descriptive **bot** User-Agent
  (not a spoofed browser),
- `robots.txt` is honoured per-origin,
- a polite delay between requests,
- exponential backoff when Cloudflare serves a "Just a moment…" challenge.

No Selenium, no headless Chrome, no challenge solving. If Cloudflare keeps
challenging a deeply-paginated URL past the retry budget the script raises
`BlockedByChallenge` rather than silently returning a short list.

### Tunables (environment variables)

| Variable | Default | Meaning |
| --- | --- | --- |
| `LETTERBOXD_USER_AGENT` | `Mozilla/5.0 (compatible; letterboxd-tools/1.0; +…)` | UA string |
| `LETTERBOXD_REQUEST_DELAY` | `1.5` | seconds between requests |
| `LETTERBOXD_MAX_RETRIES` | `6` | challenge retries per URL |
| `LETTERBOXD_BACKOFF_BASE` | `5` | seconds, multiplied by attempt number |

## Setup

```bash
pip install -r requirements.txt
```

## Scripts

| Script | What it does |
| --- | --- |
| `my_watchlist.py` | Print the full watchlist |
| `my_watched_films.py` | Print watched films from the `/films/` grid |
| `my-review-scraper.py` | Dump all of your reviews to `results/my_letterboxd_reviews.txt` |
| `film-review-scraper.py` | Dump N pages of reviews for one film (interactive) |
| `letterboxd_films_watched_this_year.py` | Build a poster collage from the RSS diary feed |
| `compare_watchlist_with_pcc.py` | Watchlist ∩ Prince Charles Cinema, with screening times |
| `filtered_pcc_scraper.py` | Save the PCC "What's On" page filtered to your watchlist |
| `probe_rss.py` | Sanity-check the RSS feed |

The Letterboxd account is `mfhcor`.
