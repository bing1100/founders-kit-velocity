#!/usr/bin/env python3
"""Check every external link in the kit's Markdown files.

  python scripts/check_links.py            check all *.md files
  python scripts/check_links.py README.md  check one file

Exit code 1 if any link is broken (404, 410 or unreachable). Sites that refuse automated checks (401, 403, 429, 999)
are listed as "blocked" so a person can open them; they don't fail the run.
"""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"https?://[^\s)\"'<>`|]+")
SKIP = ("localhost", "example.org", "example.com", "example.net", ".example")
BLOCKED = {401, 403, 429, 999}
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) founders-kit-velocity-link-check", "Accept": "*/*"}


def links(files: list[Path]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for f in files:
        for url in LINK.findall(f.read_text(encoding="utf-8")):
            url = url.rstrip(".,;:")
            if any(s in url for s in SKIP) or "{{" in url:
                continue
            found.setdefault(url, []).append(str(f.relative_to(ROOT)))
    return found


def status(url: str) -> tuple[str, int | str]:
    for method in ("HEAD", "GET"):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS, method=method), timeout=20) as r:
                return url, r.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (400, 403, 404, 405, 429, 500, 501):
                continue
            return url, e.code
        except Exception as e:  # timeouts, DNS failures, TLS errors
            if method == "GET":
                return url, type(e).__name__
    return url, "unknown"


def main() -> None:
    files = [Path(a).resolve() for a in sys.argv[1:]] or sorted(
        p for p in ROOT.rglob("*.md") if ".git" not in p.parts and ".venv" not in p.parts)
    found = links(files)
    with ThreadPoolExecutor(12) as pool:
        results = sorted(pool.map(status, found))
    broken = [(u, c) for u, c in results if not (isinstance(c, int) and (c < 400 or c in BLOCKED))]
    blocked = [(u, c) for u, c in results if isinstance(c, int) and c in BLOCKED]
    for label, items in (("BROKEN", broken), ("blocked (check by hand)", blocked)):
        for url, code in items:
            print(f"{label:24} {code!s:20} {url}  ({', '.join(sorted(set(found[url])))})")
    print(f"\n{len(results)} links: {len(results) - len(broken) - len(blocked)} ok, {len(blocked)} blocked, "
          f"{len(broken)} broken")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
