"""Shared Letterboxd fetching helper.

Every script in this workspace fetches from Letterboxd the same way the
``letterboxd-list-radarr`` service does: a single well-behaved HTTP client
that sends a descriptive bot User-Agent, honours ``robots.txt``, keeps a
polite delay between requests and backs off when Cloudflare serves an
interactive challenge. No headless browsers, no Chrome impersonation, no
challenge solving.

Set ``LETTERBOXD_USER_AGENT`` to override the User-Agent string.
"""

from __future__ import annotations

import os
import re
import time
import urllib.robotparser
from typing import Iterator, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ORIGIN = "https://letterboxd.com"

USER_AGENT = os.environ.get(
    "LETTERBOXD_USER_AGENT",
    "Mozilla/5.0 (compatible; letterboxd-tools/1.0; "
    "+https://github.com/MXC1/letterboxd-tools)",
)

# Seconds to wait between requests, and challenge retry/backoff settings.
REQUEST_DELAY = float(os.environ.get("LETTERBOXD_REQUEST_DELAY", "1.5"))
MAX_RETRIES = int(os.environ.get("LETTERBOXD_MAX_RETRIES", "6"))
BACKOFF_BASE = float(os.environ.get("LETTERBOXD_BACKOFF_BASE", "5"))

_TITLE_YEAR_RE = re.compile(r"^(.*?)\s*\((\d{4})\)$")

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT

_robots: dict[str, urllib.robotparser.RobotFileParser] = {}
_last_request_at = 0.0


class LetterboxdError(RuntimeError):
    """Raised when Letterboxd cannot be fetched politely."""


class DisallowedByRobots(LetterboxdError):
    pass


class BlockedByChallenge(LetterboxdError):
    pass


def _robots_for(url: str) -> urllib.robotparser.RobotFileParser:
    origin = "{0.scheme}://{0.netloc}".format(urlparse(url))
    parser = _robots.get(origin)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(origin + "/robots.txt")
        try:
            resp = session.get(origin + "/robots.txt", timeout=20)
            resp.raise_for_status()
            parser.parse(resp.text.splitlines())
        except requests.RequestException:
            # If robots.txt is unreachable, fail open (same as the radarr guard).
            parser.parse([])
        _robots[origin] = parser
    return parser


def _is_challenge(resp: requests.Response) -> bool:
    if resp.status_code in (403, 503) and "text/html" in resp.headers.get(
        "Content-Type", ""
    ):
        head = resp.text[:2000].lower()
        return "just a moment" in head or "cf-chl" in head or "challenge-platform" in head
    return False


def get(url: str, *, params: Optional[dict] = None) -> requests.Response:
    """GET ``url`` politely, honouring robots.txt and backing off on challenges."""
    global _last_request_at

    if not url.startswith("http"):
        url = urljoin(ORIGIN + "/", url.lstrip("/"))

    if not _robots_for(url).can_fetch(USER_AGENT, url):
        raise DisallowedByRobots(f"robots.txt disallows {url}")

    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        wait = REQUEST_DELAY - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)

        resp = session.get(url, params=params, timeout=30)
        _last_request_at = time.monotonic()

        if _is_challenge(resp):
            last_exc = BlockedByChallenge(
                f"Cloudflare challenge for {url} (attempt {attempt}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE * attempt)
            continue

        resp.raise_for_status()
        return resp

    assert last_exc is not None
    raise last_exc


def get_soup(url: str, *, params: Optional[dict] = None, parser: str = "html.parser") -> BeautifulSoup:
    return BeautifulSoup(get(url, params=params).text, parser)


def parse_title_year(item_name: str) -> dict:
    """Split ``'Film Title (1999)'`` into ``{'title': ..., 'year': ...}``."""
    match = _TITLE_YEAR_RE.match(item_name.strip())
    if match:
        return {"title": match.group(1).strip(), "year": match.group(2)}
    return {"title": item_name.strip(), "year": "Unknown"}


def iter_poster_items(soup: BeautifulSoup) -> Iterator[dict]:
    """Yield film dicts for every poster component on a list/watchlist/films page."""
    for node in soup.select("[data-item-name]"):
        name = node.get("data-item-name")
        if not name:
            continue
        parsed = parse_title_year(name)
        yield {
            "name": name,
            "title": parsed["title"],
            "year": parsed["year"],
            "slug": node.get("data-item-slug"),
            "link": node.get("data-target-link") or node.get("data-item-link"),
        }


def _next_page_url(soup: BeautifulSoup, current_url: str) -> Optional[str]:
    link = soup.select_one(".paginate-nextprev .next[href]")
    if not link:
        return None
    return urljoin(current_url, link["href"])


def fetch_all_poster_items(list_url: str, *, max_pages: int = 50, on_page=None) -> list[dict]:
    """Follow pagination from ``list_url`` collecting every poster item.

    Works for watchlists (``/user/watchlist/``), watched films (``/user/films/``)
    and regular lists (``/user/list/<slug>/``).
    """
    if not list_url.startswith("http"):
        list_url = urljoin(ORIGIN + "/", list_url.lstrip("/"))
    if not list_url.endswith("/"):
        list_url += "/"

    films: list[dict] = []
    url: Optional[str] = list_url
    page = 0
    while url and page < max_pages:
        page += 1
        if on_page:
            on_page(page)
        soup = get_soup(url)
        films.extend(iter_poster_items(soup))
        url = _next_page_url(soup, url)
    return films


def get_rss_items(username: str) -> list[BeautifulSoup]:
    """Return the ``<item>`` elements from a member's RSS feed."""
    soup = get_soup(f"{ORIGIN}/{username}/rss/", parser="xml")
    return soup.find_all("item")
