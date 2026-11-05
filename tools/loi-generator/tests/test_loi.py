"""Run with: python -m unittest discover -s tests"""
import csv
import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import loi  # noqa: E402

TODAY = date(2026, 11, 5)
EXAMPLE = json.loads((ROOT / "examples" / "pilot.example.json").read_text())


def full_deal(kind):
    deal = {name: meta.get("example", "x") for name, meta in loi.fields_for(kind).items() if not meta.get("default")}
    return loi.apply_defaults(kind, deal, TODAY)


class Templates(unittest.TestCase):
    def test_every_type_has_template_and_all_placeholders_are_declared(self):
        for kind in loi.catalog()["types"]:
            text = (loi.TEMPLATES / f"{kind}.md").read_text() + (loi.TEMPLATES / "_general.md").read_text()
            used = set(loi.PLACEHOLDER.findall(text)) | set(re.findall(r"\[\[if ([A-Za-z]+)\]\]", text))
            self.assertLessEqual(used, set(loi.fields_for(kind)), kind)

    def test_required_fields_are_used_in_the_letter(self):
        # A field that is asked for but never printed would waste the founder's time. Signer details are printed by
        # the signature block, and Currency also feeds the pipeline tracker.
        internal = {"StartupEmail", "SignerEmail", "SignerName", "SignerTitle", "StartupSignerName",
                    "StartupSignerTitle", "Currency"}
        for kind in loi.catalog()["types"]:
            text = (loi.TEMPLATES / f"{kind}.md").read_text() + (loi.TEMPLATES / "_general.md").read_text()
            used = set(loi.PLACEHOLDER.findall(text))
            for name, meta in loi.fields_for(kind).items():
                if meta.get("scoring_only") or name in internal:
                    continue
                self.assertIn(name, used, f"{kind}: {name}")

    def test_every_letter_renders_with_non_binding_clause_and_no_leftovers(self):
        for kind in loi.catalog()["types"]:
            deal = full_deal(kind)
            text = loi.render(kind, deal)
            self.assertEqual(loi.missing_fields(kind, deal), [], kind)
            self.assertNotIn("{{", text, kind)
            self.assertNotIn("[[if", text, kind)
            self.assertNotIn("[[end", text, kind)
            self.assertIn("**Not binding.**", text, kind)
            self.assertIn("[[signatures]]", text, kind)

    def test_optional_section_disappears_when_blank(self):
        deal = dict(full_deal("pilot"), PilotFee="", ConversionIntent="")
        text = loi.render("pilot", deal)
        self.assertNotIn("Pilot fee", text)
        self.assertNotIn("If the pilot succeeds", text)
        self.assertIn("Pilot fee", loi.render("pilot", full_deal("pilot")))


class Filling(unittest.TestCase):
    def test_defaults_and_expiry(self):
        deal = loi.apply_defaults("pilot", {"Date": "2026-01-01"}, TODAY)
        self.assertEqual(deal["ExpiryDate"], "2026-04-01")
        self.assertEqual(deal["Currency"], "CAD")
        self.assertIn("Ontario", deal["GoverningLaw"])
        self.assertEqual(loi.apply_defaults("pilot", {}, TODAY)["Date"], "2026-11-05")

    def test_explicit_expiry_kept(self):
        self.assertEqual(loi.apply_defaults("pilot", {"Date": "2026-01-01", "ExpiryDate": "2026-02-01"}, TODAY)
                         ["ExpiryDate"], "2026-02-01")

    def test_values_are_not_rescanned(self):
        deal = dict(full_deal("pilot"), Problem="{{StartupName}} [[if PilotFee]]x[[end]]")
        self.assertIn("{{StartupName}} [[if PilotFee]]x[[end]]", loi.render("pilot", deal))

    def test_signature_block_prints_every_signer_detail(self):
        deal = full_deal("pilot")
        page = loi.to_html(loi.render("pilot", deal), deal)
        for name in ("SignerName", "SignerTitle", "SignerEmail", "StartupSignerName", "StartupSignerTitle",
                     "StartupEmail"):
            self.assertIn(deal[name].replace("&", "&amp;"), page, name)

    def test_html_escapes_values(self):
        deal = dict(full_deal("pilot"), Problem="<script>alert(1)</script> & more", CounterpartyName="A&B <Co>")
        page = loi.to_html(loi.render("pilot", deal), deal)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("A&amp;B &lt;Co&gt;", page)

    def test_slug_cannot_escape_the_folder(self):
        self.assertNotIn("/", loi.slug("../../etc/passwd"))
        self.assertNotIn(".", loi.slug("../../etc/passwd"))
        self.assertEqual(loi.slug("///"), "letter")


class Scoring(unittest.TestCase):
    def test_example_is_strong(self):
        deal = {k: v for k, v in EXAMPLE.items() if k != "Type"}
        score, gaps, warnings = loi.score_deal("pilot", loi.apply_defaults("pilot", deal, TODAY))
        self.assertEqual((score, gaps, warnings), (100, [], []))

    def test_thin_letter_is_weak(self):
        deal = loi.apply_defaults("pilot", {"SignerName": "S", "SignerTitle": "T", "Problem": "slow"}, TODAY)
        score, gaps, _ = loi.score_deal("pilot", deal)
        self.assertEqual(loi.grade(score), "Weak")
        self.assertTrue(any("Paid pilot" in g for g in gaps))

    def test_every_type_can_reach_100(self):
        for kind in loi.catalog()["types"]:
            score, gaps, _ = loi.score_deal(kind, full_deal(kind))
            self.assertEqual(score, 100, (kind, gaps))

    def test_binding_and_vague_words_flagged(self):
        deal = dict(full_deal("pilot"), PilotScope="we shall deploy", Problem="we might be interested in something new")
        _, _, warnings = loi.score_deal("pilot", deal)
        text = " ".join(warnings)
        self.assertIn('"shall"', text)
        self.assertIn('"might"', text)
        self.assertIn('"interested"', text)

    def test_default_clause_text_not_flagged(self):
        _, _, warnings = loi.score_deal("pilot", full_deal("pilot"))
        self.assertEqual(warnings, [])


class Pipeline(unittest.TestCase):
    def test_counts_only_signed_and_flags_problems(self):
        r = loi.pipeline(ROOT / "examples" / "tracker.example.csv", TODAY)
        # Example University Hospital signed, but its letter has lapsed: it must not count as live traction.
        self.assertEqual(r["counts"]["signed"], 1)
        self.assertEqual(r["values"]["signed"], 120000)
        self.assertEqual(r["counts"]["expired"], 1)
        self.assertEqual(r["counts"]["converted"], 1)
        self.assertIn("1 signed non-binding LOI worth", r["summary"])
        self.assertIn("CAD $120,000", r["summary"])
        self.assertIn("1 converted to paid agreement worth", r["summary"])
        joined = " ".join(r["chase"])
        self.assertIn("Example University Hospital: lapsed", joined)
        self.assertIn("Example General Hospital: sent 28 days ago", joined)

    def test_bad_values_are_reported_not_counted(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.csv"
            path.write_text("Company,Status,AnnualValue\nA,Signed,lots\nB,Maybe,5\nC,Signed,\"1,000\"\n")
            r = loi.pipeline(path, TODAY)
        self.assertEqual(r["values"]["signed"], 1000)
        self.assertTrue(any("A: AnnualValue" in c for c in r["chase"]))
        self.assertTrue(any("B: unknown status" in c for c in r["chase"]))


class CommandLine(unittest.TestCase):
    def run_cli(self, *args, **kw):
        return subprocess.run([sys.executable, str(ROOT / "loi.py"), *args], capture_output=True, text=True, **kw)

    def test_build_from_deal_file(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("build", str(ROOT / "examples" / "pilot.example.json"), "--out", d, "--format", "md,html",
                             "--track", f"{d}/t.csv")
            self.assertEqual(r.returncode, 0, r.stderr)
            names = sorted(p.name for p in Path(d).iterdir())
            self.assertIn("LOI-Example-Regional-Health-pilot-2026-11-05.md", names)
            self.assertIn("LOI-Example-Regional-Health-pilot-2026-11-05.html", names)
            with open(f"{d}/t.csv") as f:
                row = next(csv.DictReader(f))
            self.assertEqual((row["Status"], row["AnnualValue"]), ("Drafted", "120000"))
            # Building twice doesn't duplicate the tracker row.
            self.run_cli("build", str(ROOT / "examples" / "pilot.example.json"), "--out", d, "--format", "md",
                         "--track", f"{d}/t.csv")
            with open(f"{d}/t.csv") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 1)

    def test_batch_csv(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("build", "--type", "customer", "--csv", str(ROOT / "examples" / "prospects.example.csv"),
                             "--out", d, "--format", "md")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(len(list(Path(d).iterdir())), 2)

    def test_missing_field_writes_nothing_and_fails(self):
        with tempfile.TemporaryDirectory() as d:
            deal = {k: v for k, v in EXAMPLE.items() if k != "SuccessCriteria"}
            path = Path(d) / "deal.json"
            path.write_text(json.dumps(deal))
            out = Path(d) / "out"
            r = self.run_cli("build", str(path), "--out", str(out))
            self.assertEqual(r.returncode, 1)
            self.assertIn("SuccessCriteria", r.stdout)
            self.assertFalse(out.exists())

    def test_new_is_interactive_and_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "deal.json"
            count = len(loi.fields_for("letter-of-support"))
            r = self.run_cli("new", "--type", "letter-of-support", "--out", str(out), input="answer\n" * count)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(out.read_text())["Type"], "letter-of-support")
            r = self.run_cli("new", "--type", "pilot", "--out", str(out), input="")
            self.assertEqual(r.returncode, 1)
            self.assertIn("already exists", r.stderr)

    def test_unknown_type_is_a_clear_error(self):
        r = self.run_cli("fields", "--type", "nope")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Choose from", r.stderr)


if __name__ == "__main__":
    unittest.main()
