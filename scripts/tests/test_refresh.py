"""Offline tests. Run with: python -m unittest discover -s scripts/tests"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import refresh  # noqa: E402
from refresh import radar  # noqa: E402

SITE = refresh.SITE
SITEMAP = f"""<urlset>
<url><loc>{SITE}</loc><lastmod>2026-01-01T00:00:00Z</lastmod></url>
<url><loc>{SITE}/apply</loc><lastmod>2026-02-01T00:00:00Z</lastmod></url>
<url><loc>{SITE}/programs-events/cornerstone</loc><lastmod>2026-03-01T00:00:00Z</lastmod></url>
<url><loc>{SITE}/news/a</loc></url>
<url><loc>{SITE}/company/x</loc><lastmod>2026-01-01T00:00:00Z</lastmod></url>
</urlset>"""
README = f"""# Kit

Intro

{refresh.START}
old text

_Last changed: 2026-01-01_
{refresh.END}

## After
"""


class Sitemap(unittest.TestCase):
    def test_parse(self):
        pages = refresh.parse_sitemap(SITEMAP)
        self.assertEqual(pages["/"], "2026-01-01T00:00:00Z")
        self.assertEqual(pages["/apply"], "2026-02-01T00:00:00Z")
        self.assertEqual(pages["/news/a"], "")
        self.assertEqual(len(pages), 5)


class Diff(unittest.TestCase):
    def setUp(self):
        self.old = {"pages": refresh.parse_sitemap(SITEMAP), "hashes": {"https://velocity.fund/": "aaa"}}

    def test_no_change(self):
        d = refresh.diff(self.old, self.old)
        self.assertFalse(d["any"])

    def test_changes_classified(self):
        new_pages = dict(self.old["pages"])
        new_pages["/apply"] = "2026-06-01T00:00:00Z"            # edited
        new_pages["/programs-events/new-thing"] = "2026-06-01"   # added
        del new_pages["/programs-events/cornerstone"]           # removed
        new_pages["/news/b"] = ""                               # new news
        new_pages["/company/y"] = ""                            # new company: counted, not "any"
        new_pages["/company/x"] = "2027-01-01"                  # edited company: ignored
        d = refresh.diff(self.old, {"pages": new_pages, "hashes": {"https://velocity.fund/": "bbb"}})
        self.assertEqual(d["changed"], ["/apply"])
        self.assertEqual(d["added"], ["/programs-events/new-thing"])
        self.assertEqual(d["removed"], ["/programs-events/cornerstone"])
        self.assertEqual(d["new_news"], ["/news/b"])
        self.assertEqual(d["new_companies"], ["/company/y"])
        self.assertEqual(d["hash_changed"], ["https://velocity.fund/"])
        self.assertTrue(d["any"])

    def test_new_companies_alone_are_not_a_change_to_review(self):
        pages = dict(self.old["pages"], **{"/company/z": ""})
        self.assertFalse(refresh.diff(self.old, {"pages": pages, "hashes": self.old["hashes"]})["any"])

    def test_newly_hashed_url_is_not_a_change(self):
        new = {"pages": self.old["pages"], "hashes": {**self.old["hashes"], "https://velocity.fund/team.html": "c"}}
        self.assertEqual(refresh.diff(self.old, new)["hash_changed"], [])


class Block(unittest.TestCase):
    def test_replace_and_idempotent(self):
        out, changed = refresh.replace_block(README, "new table", date(2026, 11, 5))
        self.assertTrue(changed)
        self.assertIn("new table\n\n_Last changed: 2026-11-05_\n" + refresh.END, out)
        self.assertNotIn("old text", out)
        self.assertTrue(out.endswith("## After\n"))
        again, changed = refresh.replace_block(out, "new table", date(2026, 11, 12))
        self.assertFalse(changed)
        self.assertEqual(again, out)

    def test_missing_markers(self):
        with self.assertRaises(ValueError):
            refresh.replace_block("# no markers", "x", date(2026, 11, 5))

    def test_events_block(self):
        pages = [radar.Page("soon", title="Pitch | Night", dates=[date(2026, 11, 16)],
                            signups=["https://luma.com/x"]),
                 radar.Page("shut", title="Closed one", dates=[date(2026, 11, 20)], closed=True),
                 radar.Page("past", title="Old", dates=[date(2026, 1, 1)])]
        body = refresh.events_block(pages, date(2026, 11, 5), 90)
        self.assertIn("| Mon Nov 16, 2026 | [Pitch \\| Night](https://www.velocityincubator.com/programs-events/soon) "
                      "| [Sign up](https://luma.com/x) |", body)
        self.assertIn("Closed; see page", body)
        self.assertNotIn("Old", body)
        self.assertIn("No dated events", refresh.events_block([], date(2026, 11, 5), 90))


class Report(unittest.TestCase):
    def test_references_point_at_real_lines(self):
        refs = refresh.references(f"{SITE}/apply")
        self.assertTrue(any(r.startswith("README.md:") for r in refs))
        path, line = refs[0].rsplit(":", 1)
        self.assertIn(f"{SITE}/apply", (refresh.ROOT / path).read_text().splitlines()[int(line) - 1])

    def test_reference_match_is_exact(self):
        # /apply must not match /apply-something, and must match a link with an anchor.
        self.assertIsNotNone(refresh.re.search(re_for("/apply"), f"[x]({SITE}/apply#faq)"))
        self.assertIsNone(refresh.re.search(re_for("/apply"), f"[x]({SITE}/apply-now)"))

    def test_report_text(self):
        d = refresh.diff({"pages": {}, "hashes": {}}, {"pages": {"/apply": "x"}, "hashes": {}})
        text = refresh.report(d, True, date(2026, 11, 5), False)
        self.assertIn("Events block in README: **updated**", text)
        self.assertIn("## New pages", text)
        self.assertIn("kit-refresh", text)
        quiet = refresh.report(refresh.diff({"pages": {}}, {"pages": {}}), False, date(2026, 11, 5), False)
        self.assertIn("Nothing changed.", quiet)


def re_for(path):
    return refresh.re.escape(SITE + path) + r"(?=[)\s\"'#?<|]|$)"


if __name__ == "__main__":
    unittest.main()
