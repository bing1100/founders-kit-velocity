#!/usr/bin/env python3
"""List Velocity's event and program pages with their dates and signup links, read live from the public sitemap.

  python radar.py                     upcoming events (the next 60 days by default)
  python radar.py --days 120          look further ahead
  python radar.py --all               every page, newest first, including undated programs
  python radar.py --markdown          print a Markdown table you can paste into the README

Velocity's website is the source of truth. This only saves you from checking dozens of pages by hand. Dates written without a year
(such as "Nov 16") are not read, so a multi-week event appears only under its first full date.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

BASE = "https://www.velocityincubator.com"
USER_AGENT = "founders-kit-velocity-radar (+https://github.com/bing1100/founders-kit-velocity)"
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
# Only full month names: every page's sidebar repeats the next event in short form ("Nov 16, 2026").
DATE_RE = re.compile(rf"\b({MONTHS}) (\d{{1,2}}), (20\d\d)\b")
SIGNUP_RE = re.compile(r"fillout\.com|luma\.com|lu\.ma|eventbrite|ticketfi|airtable\.com/app|forms\.office", re.I)
# The shared form for booking a coach appears site-wide, so it says nothing about this event.
GENERIC_FORMS = ("5ZQrB5NE7Pus",)
CLOSED_RE = re.compile(r"Registrations? closed|Applications? closed", re.I)


@dataclass
class Page:
    slug: str
    title: str = ""
    summary: str = ""
    dates: list = field(default_factory=list)
    signups: list = field(default_factory=list)
    closed: bool = False

    @property
    def url(self) -> str:
        return f"{BASE}/programs-events/{self.slug}"

    @property
    def signup(self) -> str:
        return self.signups[0] if self.signups else self.url


def fetch(url: str, retries: int = 2) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries:
                raise
            time.sleep(1 + attempt)
    raise AssertionError("unreachable")


def slugs_from_sitemap(xml: str) -> list[str]:
    return sorted(set(re.findall(r"<loc>https://www\.velocityincubator\.com/programs-events/([^<]+)</loc>", xml)))


def parse_page(slug: str, source: str) -> Page:
    page = Page(slug)
    title = re.search(r"<title>(.*?)</title>", source, re.S)
    if title:
        page.title = html.unescape(title.group(1)).split("|")[0].strip()
    summary = re.search(r'name="description"\s+content="([^"]*)"', source) or \
        re.search(r'content="([^"]*)"\s+name="description"', source)
    if summary:
        page.summary = html.unescape(summary.group(1)).strip()
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", source, flags=re.S)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))
    found = set()
    for month, day, year in DATE_RE.findall(text):
        try:
            found.add(datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date())
        except ValueError:
            continue
    page.dates = sorted(found)
    links = dict.fromkeys(html.unescape(u) for u in re.findall(r'href="(https?://[^"]+)"', source))
    page.signups = [u for u in links if SIGNUP_RE.search(u) and not any(g in u for g in GENERIC_FORMS)]
    page.closed = bool(CLOSED_RE.search(text))
    return page


def load_pages(workers: int = 6) -> tuple[list[Page], list[str]]:
    slugs = slugs_from_sitemap(fetch(f"{BASE}/sitemap.xml"))
    if not slugs:
        raise RuntimeError("the sitemap lists no /programs-events/ pages, so the site may have changed")
    failed: list[str] = []

    def one(slug: str):
        try:
            return parse_page(slug, fetch(f"{BASE}/programs-events/{slug}"))
        except (urllib.error.URLError, TimeoutError) as e:
            failed.append(f"{slug}: {e}")
            return None
    with ThreadPoolExecutor(workers) as pool:
        return [p for p in pool.map(one, slugs) if p], failed


def upcoming(pages: list[Page], today: date, days: int) -> list[tuple[date, Page]]:
    horizon = today + timedelta(days=days)
    rows = []
    for page in pages:
        future = [d for d in page.dates if today <= d <= horizon]
        if future:
            rows.append((future[0], page))
    return sorted(rows, key=lambda r: (r[0], r[1].slug))


def all_rows(pages: list[Page]) -> list[tuple[date | None, Page]]:
    dated = sorted(((p.dates[-1], p) for p in pages if p.dates), key=lambda r: (r[0], r[1].slug), reverse=True)
    return dated + [(None, p) for p in sorted(pages, key=lambda p: p.slug) if not p.dates]


def markdown_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("[", "(").replace("]", ")")


def print_rows(rows: list, as_markdown: bool) -> None:
    if as_markdown:
        print("| Date | Event | Sign up |\n|---|---|---|")
    for day, page in rows:
        when = day.isoformat() if day else "no date"
        link = "closed" if page.closed else page.signup
        if as_markdown:
            signup = "closed; see page" if page.closed else f"[Sign up]({page.signup})"
            print(f"| {when} | [{markdown_cell(page.title or page.slug)}]({page.url}) | {signup} |")
        else:
            print(f"{when:11} {(page.title or page.slug)[:58]:60} {link}")


def main() -> None:
    ap = argparse.ArgumentParser(description="List Velocity events and signup links from the public site.")
    ap.add_argument("--days", type=int, default=60, help="how many days ahead to look")
    ap.add_argument("--all", action="store_true", help="list every page, including past events and undated programs")
    ap.add_argument("--markdown", action="store_true", help="print a Markdown table")
    args = ap.parse_args()
    try:
        pages, failed = load_pages()
    except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
        sys.exit(f"ERROR: could not read {BASE}: {e}")
    today = date.today()
    rows = all_rows(pages) if args.all else upcoming(pages, today, args.days)
    if rows:
        print_rows(rows, args.markdown)
    else:
        print(f"No dated events in the next {args.days} days across {len(pages)} pages.")
    if not args.markdown:
        print(f"\nChecked {len(pages)} pages on {today}. Dates are read from page text, so confirm on the page before "
              "you plan around one.")
    for line in failed:
        print(f"Could not read {line}", file=sys.stderr)


if __name__ == "__main__":
    main()
