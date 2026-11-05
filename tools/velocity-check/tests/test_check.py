"""Run with: python -m unittest discover -s tests"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import check  # noqa: E402


class Discovery(unittest.TestCase):
    def setUp(self):
        self.r = check.discovery(ROOT / "examples" / "conversations.example.csv")

    def test_surveys_are_not_conversations(self):
        self.assertEqual((self.r["conversations"], self.r["surveys"]), (4, 1))

    def test_counts(self):
        self.assertEqual((self.r["long_calls"], self.r["strangers"], self.r["would_pay"]), (3, 3, 2))
        self.assertEqual(self.r["organizations"], 4)

    def test_statement_uses_real_numbers(self):
        s = self.r["statement"]
        self.assertIn("August 2026 and September 2026", s)
        self.assertIn("4 conversations", s)
        self.assertIn("3 of them 30 minutes or longer", s)
        self.assertIn("2 said they would pay", s)

    def test_flags(self):
        text = " ".join(self.r["flags"])
        self.assertIn("survey", text)
        self.assertIn("20 or more", text)

    def test_mostly_known_people_flagged_and_bad_rows_reported(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.csv"
            p.write_text("Date,Person,Role,Minutes,KnewBefore,Method\n2026-01-02,A,x,30,Yes,Call\n2026-01-03,B,x,30,Yes,"
                         "Call\nnot-a-date,C,x,30,No,Call\n2026-01-05,D,x,soon,No,Call\n")
            r = check.discovery(p)
        self.assertEqual(r["conversations"], 2)
        self.assertEqual(len(r["problems"]), 2)
        self.assertIn("didn't already know", " ".join(r["flags"]))

    def test_empty_log(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.csv"
            p.write_text("Date,Person,Role,Minutes,KnewBefore,Method\n")
            r = check.discovery(p)
        self.assertEqual(r["conversations"], 0)
        self.assertEqual(r["statement"], "")


class Market(unittest.TestCase):
    def test_math(self):
        r = check.market(ROOT / "examples" / "market.example.json")
        self.assertEqual(r["rows"][0]["revenue"], 150 * 0.10 * 45000)
        self.assertEqual(r["total"], 150 * 0.10 * 45000 + 900 * 0.05 * 24000)
        self.assertIn("150 Ontario hospital labs", r["statement"])
        self.assertEqual(r["flags"], [])

    def test_missing_evidence_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.json"
            p.write_text('{"segments":[{"name":"X","customers":"1,000","price_per_year":"$10","conversion_percent":"40%"}]}')
            r = check.market(p)
        self.assertEqual(r["rows"][0]["won"], 400)
        text = " ".join(r["flags"])
        for needle in ("where the customer count", "why customers would pay", "why you can convert", "40% conversion"):
            self.assertIn(needle, text)


class Lint(unittest.TestCase):
    def test_flags_bad_lines_only(self):
        findings = check.lint_text((ROOT / "examples" / "answers.example.md").read_text())
        lines = {f[0] for f in findings}
        self.assertEqual(lines, {1, 2})
        kinds = {f[1] for f in findings}
        self.assertEqual(kinds, {"buzzword", "top-down"})

    def test_no_false_positive_on_substrings_or_small_numbers(self):
        self.assertEqual(check.lint_text("We charge $40 a month. The platforms team at Shopify replied in 3 days."), [])
        self.assertEqual(check.lint_text("There are 900 labs, and each spends $45,000 a year."), [])

    def test_long_sentence(self):
        self.assertEqual(check.lint_text(" ".join(["word"] * 40) + ".")[0][1], "long")


class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "check.py"), *args], capture_output=True, text=True)

    def test_lint_exit_codes(self):
        self.assertEqual(self.run_cli("lint", str(ROOT / "examples" / "answers.example.md")).returncode, 1)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.md"
            p.write_text("Our robot runs routine blood tests.")
            self.assertEqual(self.run_cli("lint", str(p)).returncode, 0)

    def test_other_commands_run(self):
        for cmd, f in (("discovery", "conversations.example.csv"), ("market", "market.example.json")):
            r = self.run_cli(cmd, str(ROOT / "examples" / f))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Draft for your application", r.stdout)


if __name__ == "__main__":
    unittest.main()
