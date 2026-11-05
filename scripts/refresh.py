#!/usr/bin/env python3
"""Find what changed on Velocity's website since the last check, and refresh the README's auto-updated events block.

  python scripts/refresh.py                       update the events block and the page snapshot; print a report
  python scripts/refresh.py --check               report only; write nothing
  python scripts/refresh.py --report report.md    also save the report as Markdown (the weekly pull request uses it)

Velocity's site has no feed or webhooks, but its sitemap records when each page was last edited. This compares those
dates with data/velocity-pages.json and lists every changed, new or removed page, with the lines in this kit that
link to it. A person, or the kit-refresh Claude skill, then checks those pages and updates the hand-written tables.
Only the block between the velocity-radar markers in README.md is rewritten automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "velocity-radar"))
import radar  # noqa: E402

SNAPSHOT = ROOT / "data" / "velocity-pages.json"
README = ROOT / "README.md"
START, END = "<!-- velocity-radar:start -->", "<!-- velocity-radar:end -->"
SITE = "https://www.velocityincubator.com"
# Company profiles and news posts change constantly and aren't summarized in the kit, so they are only counted.
BULK = ("/company/", "/news/")
# velocity.fund has no sitemap, so its key pages are tracked by a hash of their visible text.
HASHED = ["https://velocity.fund/", "https://velocity.fund/how-we-help.html", "https://velocity.fund/team.html"]
DOC_GLOBS = ["README.md", "docs/*.md", "skills/*/SKILL.md", "tools/*/README.md"]


def parse_sitemap(xml: str) -> dict[str, str]:
    """Map each page path to its last-modified timestamp ("" if the sitemap gives none)."""
    pages = {}
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>\s*([^<\s]+)\s*</loc>", block)
        if not loc:
            continue
        path = loc.group(1).replace(SITE, "") or "/"
        mod = re.search(r"<lastmod>\s*([^<\s]+)\s*</lastmod>", block)
        pages[path] = mod.group(1) if mod else ""
    return pages


def text_hash(source: str) -> str:
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", source, flags=re.S)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def diff(old: dict, new: dict) -> dict:
    """Compare two snapshots. Tracked pages are listed one by one; bulk pages (companies, news) are summarized."""
    old_pages, new_pages = old.get("pages", {}), new.get("pages", {})
    tracked = lambda p: not p.startswith(BULK)  # noqa: E731
    result = {
        "changed": sorted(p for p in new_pages if tracked(p) and p in old_pages and new_pages[p] != old_pages[p]),
        "added": sorted(p for p in new_pages if tracked(p) and p not in old_pages),
        "removed": sorted(p for p in old_pages if tracked(p) and p not in new_pages),
        "new_news": sorted(p for p in new_pages if p.startswith("/news/") and p not in old_pages),
        "new_companies": sorted(p for p in new_pages if p.startswith("/company/") and p not in old_pages),
        "hash_changed": sorted(u for u, h in new.get("hashes", {}).items() if old.get("hashes", {}).get(u) not in
                               (None, h)),
    }
    result["any"] = any(result[k] for k in ("changed", "added", "removed", "new_news", "hash_changed"))
    return result


def references(url_fragment: str) -> list[str]:
    """Where this kit links to a page, as 'file:line' strings."""
    hits = []
    pattern = re.compile(re.escape(url_fragment) + r"(?=[)\s\"'#?<|]|$)")
    for glob in DOC_GLOBS:
        for path in sorted(ROOT.glob(glob)):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}")
    return hits


def events_block(pages: list, today: date, days: int) -> str:
    rows = radar.upcoming(pages, today, days)
    lines = [f"Events with a date in the next {days} days, read from velocityincubator.com by "
             "[velocity-radar](tools/velocity-radar/). Confirm on the event page before you plan around one.", ""]
    if not rows:
        lines.append(f"_No dated events in the next {days} days. Check the [Students page]"
                     f"({SITE}/students) and the tables below._")
    else:
        lines += ["| Date | Event | Sign up |", "|---|---|---|"]
        for day, page in rows:
            signup = "Closed; see page" if page.closed else f"[Sign up]({page.signup})"
            lines.append(f"| {day:%a %b} {day.day}, {day.year} | [{radar.markdown_cell(page.title or page.slug)}]({page.url}) | "
                         f"{signup} |")
    return "\n".join(lines)


def replace_block(readme: str, body: str, today: date) -> tuple[str, bool]:
    """Swap the text between the markers. The 'last changed' date moves only when the content does, so a week
    with no changes produces no diff and no pull request."""
    m = re.search(re.escape(START) + r"\n(.*?)" + re.escape(END), readme, re.S)
    if not m:
        raise ValueError(f"README.md has no {START} ... {END} block")
    current = re.sub(r"\n*_Last changed: [^_]*_\s*$", "", m.group(1).rstrip())
    if current.strip() == body.strip():
        return readme, False
    block = f"{START}\n{body}\n\n_Last changed: {today.isoformat()}_\n{END}"
    return readme[:m.start()] + block + readme[m.end():], True


def report(d: dict, events_changed: bool, today: date, baseline: bool) -> str:
    out = [f"# Velocity refresh: {today.isoformat()}", ""]
    if baseline:
        out += ["No previous snapshot existed, so this run only recorded a baseline. Future runs will compare "
                "against it.", ""]
    out.append(f"- Events block in README: {'**updated**' if events_changed else 'unchanged'}")
    for key, label in (("changed", "Pages edited since the last check"), ("added", "New pages"),
                       ("removed", "Pages removed (links to these will break)")):
        out.append(f"- {label}: {len(d[key])}")
    out += [f"- New news posts: {len(d['new_news'])} · new company profiles: {len(d['new_companies'])}",
            f"- velocity.fund pages with changed text: {len(d['hash_changed'])}", ""]
    if not d["any"] and not events_changed:
        out.append("Nothing changed.")
        return "\n".join(out) + "\n"
    for key, title in (("changed", "Edited pages"), ("added", "New pages"), ("removed", "Removed pages")):
        if not d[key]:
            continue
        out += [f"## {title}", "", "| Page | Linked from |", "|---|---|"]
        for path in d[key]:
            refs = references(SITE + path) if path != "/" else []
            where = ", ".join(f"`{r}`" for r in refs[:6]) + (" …" if len(refs) > 6 else "") if refs else \
                "_not linked yet: should it be?_"
            out.append(f"| [{path}]({SITE}{path}) | {where} |")
        out.append("")
    if d["hash_changed"]:
        out += ["## velocity.fund", ""] + [f"- [{u}]({u}): text changed. Check the cheque sizes and process in "
                                            "README.md, docs/velocity-guide.md and skills/fundraise-prep."
                                            for u in d["hash_changed"]] + [""]
    if d["new_news"]:
        out += ["## New news posts", "", "Skim these for new programs, awards or deadlines.", ""]
        out += [f"- {SITE}{p}" for p in d["new_news"][:15]]
        if len(d["new_news"]) > 15:
            out.append(f"- …and {len(d['new_news']) - 15} more")
        out.append("")
    out += ["## Next step", "",
            "Check each page above and update the hand-written tables it's linked from. You can do it by hand, or "
            "run the `kit-refresh` skill in Claude Code from a clone of this repository. Update the \"last checked\" "
            "dates for anything you verified."]
    return "\n".join(out) + "\n"


def take_snapshot() -> tuple[dict, list]:
    pages = parse_sitemap(radar.fetch(f"{SITE}/sitemap.xml"))
    if not pages:
        raise RuntimeError("the sitemap is empty or unreadable, so the site may have changed")
    hashes = {}
    for url in HASHED:
        try:
            hashes[url] = text_hash(radar.fetch(url))
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"warning: could not read {url}: {e}", file=sys.stderr)
    event_pages, failed = radar.load_pages()
    for line in failed:
        print(f"warning: could not read {line}", file=sys.stderr)
    return {"pages": pages, "hashes": hashes}, event_pages


def main() -> None:
    ap = argparse.ArgumentParser(description="Detect Velocity website changes and refresh the README events block.")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    ap.add_argument("--report", metavar="FILE", help="also write the report as Markdown")
    ap.add_argument("--days", type=int, default=90, help="how far ahead the events block looks")
    args = ap.parse_args()
    today = date.today()
    try:
        new, event_pages = take_snapshot()
    except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
        sys.exit(f"ERROR: could not read {SITE}: {e}. Nothing was changed.")
    baseline = not SNAPSHOT.exists()
    old = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if not baseline else new
    changes = diff(old, new)
    readme = README.read_text(encoding="utf-8")
    updated, events_changed = replace_block(readme, events_block(event_pages, today, args.days), today)
    text = report(changes, events_changed, today, baseline)
    if not args.check:
        if events_changed:
            README.write_text(updated, encoding="utf-8")
        if baseline or changes["any"] or changes["new_companies"]:
            SNAPSHOT.parent.mkdir(exist_ok=True)
            SNAPSHOT.write_text(json.dumps(new, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
