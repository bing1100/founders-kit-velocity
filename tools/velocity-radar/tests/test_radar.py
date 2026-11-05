"""Offline tests. Run with: python -m unittest discover -s tests"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import radar  # noqa: E402

PAGE = """<html><head><title>Founder Night &amp; Pitches | Velocity</title>
<meta content="Pitch to founders" name="description"></head><body>
<script>var d = "January 1, 2020";</script>
<a href="https://form.fillout.com/t/5ZQrB5NE7Pus">Book a coach</a>
<a href="https://luma.com/abc123">Register now</a>
<a href="https://www.linkedin.com/company/uwvelocity">in</a>
<p>December 3, 2026</p><p>Sidebar: Nov 16, 2026</p><p>Not a date: February 31, 2026</p>
</body></html>"""


class Parsing(unittest.TestCase):
    def setUp(self):
        self.page = radar.parse_page("founder-night", PAGE)

    def test_title_and_summary(self):
        self.assertEqual(self.page.title, "Founder Night & Pitches")
        self.assertEqual(self.page.summary, "Pitch to founders")

    def test_only_full_dates_from_visible_text(self):
        self.assertEqual(self.page.dates, [date(2026, 12, 3)])

    def test_signup_skips_shared_coaching_form(self):
        self.assertEqual(self.page.signups, ["https://luma.com/abc123"])
        self.assertEqual(self.page.signup, "https://luma.com/abc123")

    def test_page_without_signup_falls_back_to_itself(self):
        page = radar.parse_page("x", "<title>X</title>")
        self.assertEqual(page.signup, f"{radar.BASE}/programs-events/x")

    def test_closed_detected(self):
        self.assertTrue(radar.parse_page("x", "<p>Registrations closed</p>").closed)
        self.assertFalse(self.page.closed)

    def test_sitemap(self):
        xml = (f"<loc>{radar.BASE}/programs-events/b</loc><loc>{radar.BASE}/news/n</loc>"
               f"<loc>{radar.BASE}/programs-events/a</loc><loc>{radar.BASE}/programs-events/a</loc>")
        self.assertEqual(radar.slugs_from_sitemap(xml), ["a", "b"])


class Selecting(unittest.TestCase):
    def setUp(self):
        self.pages = [radar.Page("past", dates=[date(2026, 1, 1)]), radar.Page("soon", dates=[date(2026, 11, 16)]),
                      radar.Page("far", dates=[date(2027, 6, 1)]), radar.Page("none")]

    def test_upcoming_window_includes_today(self):
        rows = radar.upcoming(self.pages, date(2026, 11, 16), 60)
        self.assertEqual([p.slug for _, p in rows], ["soon"])

    def test_all_sorted_with_undated_last(self):
        self.assertEqual([p.slug for _, p in radar.all_rows(self.pages)], ["far", "soon", "past", "none"])

    def test_markdown_cell_cannot_break_table(self):
        self.assertEqual(radar.markdown_cell("a|b [c]"), "a\\|b (c)")


if __name__ == "__main__":
    unittest.main()
