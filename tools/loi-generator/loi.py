#!/usr/bin/env python3
"""Draft, score and track letters of intent (LOIs) from a deal file or a CSV of prospects.

  python loi.py types                               list the letter types
  python loi.py fields --type pilot                 show the facts each type needs
  python loi.py new --type pilot --out x.local.json answer questions; save a deal file
  python loi.py build x.local.json                  write the letter (md, html; docx with python-docx)
  python loi.py build --type pilot --csv y.local.csv batch: one letter per CSV row
  python loi.py score x.local.json                  how much evidence would this letter carry?
  python loi.py pipeline tracker.local.csv          totals you can quote honestly, plus what needs chasing

The templates are starting points, not legal advice. See README.md.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z]+)\s*\}\}")
CONDITION = re.compile(r"\[\[if ([A-Za-z]+)\]\](.*?)\[\[end\]\]", re.S)

# Free-text fields are checked for language that weakens the letter or could read as a commitment.
VAGUE = ["interested", "might", "maybe", "possibly", "potentially", "exploring", "could be", "some time", "sometime",
         "tbd", "to be determined", "unknown"]
BINDING = ["shall", "guarantee", "guaranteed", "agrees to pay", "will pay", "will purchase", "commit to buy",
           "committed to buy", "must purchase", "binding", "exclusive", "exclusively"]
TRACKER_COLUMNS = ["Company", "Contact", "Type", "Status", "AnnualValue", "Currency", "Created", "Sent", "Signed",
                   "Expires", "NextStep"]
STATUSES = ["drafted", "sent", "signed", "converted", "declined", "expired"]
STALE_DAYS = 14


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def catalog() -> dict:
    return json.loads((TEMPLATES / "catalog.json").read_text(encoding="utf-8"))


def fields_for(kind: str) -> dict:
    cat = catalog()
    if kind not in cat["types"]:
        die(f"unknown letter type {kind!r}. Choose from: {', '.join(cat['types'])}")
    return {**cat["common"], **cat["types"][kind]["fields"]}


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


# --- filling a letter ------------------------------------------------------------------------------------------------
def apply_defaults(kind: str, deal: dict, today: date) -> dict:
    """Return a copy with defaults filled. Dates in a deal must be YYYY-MM-DD so expiry arithmetic can't go wrong."""
    out = {k: (str(v).strip() if v is not None else "") for k, v in deal.items()}
    for name, meta in fields_for(kind).items():
        default = meta.get("default")
        if out.get(name) or not default:
            continue
        if default == "today":
            out[name] = today.isoformat()
        elif default != "plus90":
            out[name] = default
    letter_date = parse_date(out.get("Date", ""))
    if out.get("Date") and not letter_date:
        die(f"Date must be YYYY-MM-DD, got {out['Date']!r}")
    if not out.get("ExpiryDate") and letter_date:
        out["ExpiryDate"] = (letter_date + timedelta(days=90)).isoformat()
    return out


def missing_fields(kind: str, deal: dict) -> list[str]:
    return [n for n, m in fields_for(kind).items()
            if not m.get("optional") and not m.get("scoring_only") and not deal.get(n)]


def render(kind: str, deal: dict) -> str:
    """Return the filled letter as restricted Markdown. Values are inserted once and never re-scanned."""
    text = (TEMPLATES / f"{kind}.md").read_text(encoding="utf-8")
    text = text.replace("[[include general]]", (TEMPLATES / "_general.md").read_text(encoding="utf-8"))
    text = CONDITION.sub(lambda m: m.group(2) if deal.get(m.group(1)) else "", text)
    return PLACEHOLDER.sub(lambda m: deal.get(m.group(1), m.group(0)), text)


def blocks(markdown: str) -> list[tuple[str, str]]:
    """Split the restricted Markdown into (kind, text): h1, h2, p, li, signatures."""
    out = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "[[signatures]]":
            out.append(("signatures", ""))
        elif line.startswith("# "):
            out.append(("h1", line[2:]))
        elif line.startswith("## "):
            out.append(("h2", line[3:]))
        elif line.startswith("- "):
            out.append(("li", line[2:]))
        else:
            out.append(("p", line))
    return out


def signature_parties(deal: dict) -> list[tuple[str, str, str, str]]:
    return [(deal["CounterpartyName"], deal["SignerName"], deal["SignerTitle"], deal["SignerEmail"]),
            (deal["StartupName"], deal["StartupSignerName"], deal["StartupSignerTitle"], deal["StartupEmail"])]


def to_markdown(markdown: str, deal: dict) -> str:
    sig = "\n\n".join(f"**{org}**\n\nSignature: ______________________________\n\nName: {name}\n\nTitle: {title}\n\n"
                      f"Email: {email}\n\nDate: ______________" for org, name, title, email in signature_parties(deal))
    # Keep "From:" and "To:" on separate lines when the file is viewed as rendered Markdown.
    body = re.sub(r"^(\*\*From:\*\* .*)$", r"\1  ", markdown, flags=re.M)
    return body.replace("[[signatures]]", sig).rstrip() + "\n"


def inline_html(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(text))


def to_html(markdown: str, deal: dict) -> str:
    parts, in_list = [], False
    for kind, text in blocks(markdown):
        if kind == "li" and not in_list:
            parts.append("<ul>")
            in_list = True
        elif kind != "li" and in_list:
            parts.append("</ul>")
            in_list = False
        if kind == "h1":
            parts.append(f"<h1>{inline_html(text)}</h1>")
        elif kind == "h2":
            parts.append(f"<h2>{inline_html(text)}</h2>")
        elif kind == "li":
            parts.append(f"<li>{inline_html(text)}</li>")
        elif kind == "p":
            parts.append(f"<p>{inline_html(text)}</p>")
        else:
            cells = "".join(
                f'<div class="sig"><strong>{html.escape(o)}</strong><div class="line"></div><div>Signature</div>'
                f"<p>Name: {html.escape(n)}<br>Title: {html.escape(t)}<br>Email: {html.escape(e)}<br>"
                f"Date: ______________</p></div>"
                for o, n, t, e in signature_parties(deal))
            parts.append(f'<div class="sigs">{cells}</div>')
    if in_list:
        parts.append("</ul>")
    title = html.escape(f"Letter of intent: {deal['CounterpartyName']} and {deal['StartupName']}")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>
  @page {{ size: letter; margin: 2.2cm; }}
  body {{ font: 11pt/1.45 Georgia, "Times New Roman", serif; color: #111; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 18pt; margin: 0 0 1rem; }}
  h2 {{ font-size: 12pt; margin: 1.3rem 0 .35rem; }}
  p {{ margin: .45rem 0; }} ul {{ margin: .35rem 0; padding-left: 1.3rem; }} li {{ margin: .2rem 0; }}
  .sigs {{ display: flex; gap: 2.5rem; margin-top: 2.2rem; break-inside: avoid; }}
  .sig {{ flex: 1; }} .line {{ border-bottom: 1px solid #111; height: 3rem; }} .sig > div:nth-child(3) {{ font-size: 9pt; color: #555; }}
  @media print {{ body {{ margin: 0; padding: 0; max-width: none; }} }}
</style></head><body>
{chr(10).join(parts)}
</body></html>
"""


def add_runs(paragraph, text: str) -> None:
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if part:
            paragraph.add_run(part).bold = bool(i % 2)


def write_docx(markdown: str, deal: dict, path: Path) -> bool:
    try:
        from docx import Document
        from docx.shared import Pt
    except ImportError:
        return False
    doc = Document()
    doc.styles["Normal"].font.name = "Georgia"
    doc.styles["Normal"].font.size = Pt(11)
    for kind, text in blocks(markdown):
        if kind == "h1":
            doc.add_heading(text, level=1)
        elif kind == "h2":
            doc.add_heading(text, level=2)
        elif kind == "li":
            add_runs(doc.add_paragraph(style="List Bullet"), text)
        elif kind == "p":
            add_runs(doc.add_paragraph(), text)
        else:
            table = doc.add_table(rows=1, cols=2)
            for cell, (org, name, title, email) in zip(table.rows[0].cells, signature_parties(deal)):
                cell.paragraphs[0].add_run(org).bold = True
                for line in ("", "______________________________", "Signature", f"Name: {name}", f"Title: {title}",
                             f"Email: {email}", "Date: ______________"):
                    cell.add_paragraph(line)
    doc.save(str(path))
    return True


# --- scoring ---------------------------------------------------------------------------------------------------------
def score_deal(kind: str, deal: dict) -> tuple[int, list[str], list[str]]:
    """Score how specific the letter is. Returns (score, gaps, warnings). Specificity, not proof of demand."""
    checks = [
        ("Named signer with a title", bool(deal.get("SignerName") and deal.get("SignerTitle")), 15,
         "Name a real person and title. A letter from \"the team\" carries little weight."),
        ("Specific problem", len(deal.get("Problem", "").split()) >= 8, 15,
         "Describe the problem in the counterparty's own terms, in at least one full sentence."),
        ("Target date", bool(deal.get("TargetDate")) or kind == "letter-of-support", 10,
         "Add a target date or quarter."),
        ("Dated next step", bool(re.search(r"\d", deal.get("NextStep", ""))), 15,
         "Put a date on the next step so the letter leads to something."),
        ("Expiry date", bool(deal.get("ExpiryDate")), 5, "Add an expiry date."),
    ]
    if kind == "customer":
        checks += [("Quantity", bool(deal.get("Quantity")), 10, "State how much they expect to buy."),
                   ("Price or budget", bool(re.search(r"\d", deal.get("PriceIndication", ""))), 20,
                    "Get a number or range. A price is the strongest signal in the letter."),
                   ("Purchase conditions", bool(deal.get("PurchaseConditions")), 10, "State what must be true first.")]
    elif kind in ("pilot", "health-pilot"):
        checks += [("Measurable success criteria", bool(re.search(r"\d", deal.get("SuccessCriteria", ""))), 15,
                    "Put a number in the success criteria so both sides know what winning means."),
                   ("Paid pilot", bool(re.search(r"\d", deal.get("PilotFee", ""))), 15,
                    "Ask for a pilot fee, even a small one. Paying is the clearest evidence of need."),
                   ("Path to purchase", bool(deal.get("ConversionIntent")), 10, "State what happens if the pilot works.")]
        if kind == "health-pilot":
            checks.append(("Clinical lead", bool(deal.get("ClinicalChampion")), 5, "Name a clinical lead."))
    elif kind == "design-partner":
        checks += [("Concrete contribution", bool(re.search(r"\d", deal.get("PartnerCommitment", ""))), 15,
                    "Say how often and how long they will meet."),
                   ("Expected price", bool(re.search(r"\d", deal.get("PriceIndication", ""))), 25,
                    "Discuss the price after the partnership. Without one this is feedback, not demand.")]
    elif kind == "letter-of-support":
        checks += [("Named program", bool(deal.get("ProgramName")), 10, "Name the program you are applying to."),
                   ("Defined role", bool(deal.get("SupportRole")), 15, "Say exactly how they would take part."),
                   ("Stated contribution", bool(deal.get("InKindContribution")), 15,
                    "State an in-kind or cash contribution, valued in dollars if you can.")]
    elif kind == "partnership":
        checks += [("Defined roles", bool(deal.get("PartnerRole") and deal.get("StartupRole")), 20,
                    "State what each side would do."),
                   ("Commercial terms", bool(re.search(r"\d", deal.get("CommercialTerms", ""))), 20,
                    "Put a number on the commercial terms.")]
    earned = sum(points for _, ok, points, _ in checks if ok)
    total = sum(points for _, _, points, _ in checks)
    gaps = [f"{label}: {advice}" for label, ok, _, advice in checks if not ok]
    warnings = []
    meta = fields_for(kind)
    for name, value in deal.items():
        if name not in meta or meta[name].get("default") or meta[name].get("scoring_only"):
            continue
        lowered = str(value).lower()
        for word in VAGUE:
            if re.search(rf"\b{re.escape(word)}\b", lowered):
                warnings.append(f"{name}: \"{word}\" is vague. Replace it with what they actually said they would do.")
        for word in BINDING:
            if re.search(rf"\b{re.escape(word)}\b", lowered):
                warnings.append(f"{name}: \"{word}\" can read as a binding promise. Keep it as an intention, or use a "
                                "contract instead.")
    return round(100 * earned / total), gaps, warnings


def grade(score: int) -> str:
    return "Strong" if score >= 80 else "Credible" if score >= 55 else "Weak"


# --- tracker ---------------------------------------------------------------------------------------------------------
def add_to_tracker(path: Path, kind: str, deal: dict, today: date) -> None:
    rows = []
    if path.exists():
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    if any(r.get("Company", "").strip().lower() == deal["CounterpartyName"].lower() and r.get("Type") == kind
           for r in rows):
        print(f"  tracker: {deal['CounterpartyName']} ({kind}) is already listed, left as it is")
        return
    rows.append({"Company": deal["CounterpartyName"], "Contact": deal["SignerName"], "Type": kind, "Status": "Drafted",
                 "AnnualValue": deal.get("AnnualValue", ""), "Currency": deal.get("Currency", ""),
                 "Created": today.isoformat(), "Expires": deal.get("ExpiryDate", ""),
                 "NextStep": deal.get("NextStep", "")})
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKER_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def money(value: float, currency: str = "") -> str:
    return f"{currency + ' ' if currency else ''}${value:,.0f}"


def pipeline(path: Path, today: date) -> dict:
    if not path.exists():
        die(f"tracker not found: {path}")
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    counts = {s: 0 for s in STATUSES}
    values = {s: 0.0 for s in STATUSES}
    currencies, chase = set(), []
    for r in rows:
        status = (r.get("Status") or "").strip().lower()
        company = (r.get("Company") or "?").strip()
        if status not in counts:
            chase.append(f"{company}: unknown status {r.get('Status')!r} (use {', '.join(STATUSES)})")
            continue
        expires, sent = parse_date(r.get("Expires", "")), parse_date(r.get("Sent", ""))
        lapsed = status in ("drafted", "sent", "signed") and expires is not None and expires < today
        bucket = "expired" if lapsed else status  # a lapsed letter must never inflate the number founders quote
        counts[bucket] += 1
        try:
            amount = float(re.sub(r"[,$\s]", "", r.get("AnnualValue") or "0") or 0)
        except ValueError:
            chase.append(f"{company}: AnnualValue {r.get('AnnualValue')!r} is not a number, so it is not counted")
            amount = 0.0
        values[bucket] += amount
        if amount and (r.get("Currency") or "").strip():
            currencies.add(r["Currency"].strip())
        if lapsed:
            chase.append(f"{company}: lapsed on {expires}, so it is counted as expired. Renew it or mark it Expired.")
        elif status == "sent" and sent and (today - sent).days > STALE_DAYS:
            chase.append(f"{company}: sent {(today - sent).days} days ago with no signature. Follow up.")
    currency = currencies.pop() if len(currencies) == 1 else ""
    if len(currencies) > 0:
        chase.append("More than one currency in the tracker: the totals below add them together as if they were one.")
    live = counts["signed"]
    summary = (f"{live} signed non-binding LOI{'s' if live != 1 else ''} worth about "
               f"{money(values['signed'], currency)} in indicative annual value")
    if counts["converted"]:
        summary += (f"; {counts['converted']} converted to paid agreement{'s' if counts['converted'] != 1 else ''} worth "
                    f"{money(values['converted'], currency)}")
    return {"counts": counts, "values": values, "currency": currency, "chase": chase, "summary": summary + "."}


# --- commands --------------------------------------------------------------------------------------------------------
def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")[:60] or "letter"


def load_deal(path: Path) -> tuple[str, dict]:
    if not path.exists():
        die(f"deal file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"{path.name} is not valid JSON: {e}")
    if not isinstance(data, dict) or "Type" not in data:
        die(f"{path.name} needs a \"Type\" key, such as \"pilot\". See examples/.")
    kind = str(data.pop("Type"))
    fields_for(kind)
    return kind, data


def build_one(kind: str, deal: dict, out_dir: Path, formats: list[str], today: date, tracker: Path | None) -> bool:
    deal = apply_defaults(kind, deal, today)
    missing = missing_fields(kind, deal)
    who = deal.get("CounterpartyName") or "(no counterparty)"
    if missing:
        print(f"SKIPPED {who}: no value for {', '.join(missing)}")
        return False
    markdown = render(kind, deal)
    leftover = PLACEHOLDER.findall(markdown)
    if leftover:
        print(f"SKIPPED {who}: no value for {', '.join(sorted(set(leftover)))}")
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"LOI-{slug(deal['CounterpartyName'])}-{kind}-{deal['Date']}"
    written = []
    if "md" in formats:
        (out_dir / f"{stem}.md").write_text(to_markdown(markdown, deal), encoding="utf-8")
        written.append(f"{stem}.md")
    if "html" in formats:
        (out_dir / f"{stem}.html").write_text(to_html(markdown, deal), encoding="utf-8")
        written.append(f"{stem}.html")
    if "docx" in formats:
        if write_docx(markdown, deal, out_dir / f"{stem}.docx"):
            written.append(f"{stem}.docx")
        else:
            print("  note: skipped .docx because python-docx isn't installed (pip install -r requirements.txt)")
    score, gaps, warnings = score_deal(kind, deal)
    print(f"{who}: {', '.join(written)}  [{grade(score)}, {score}/100]")
    for w in warnings:
        print(f"  WARNING {w}")
    if tracker:
        add_to_tracker(tracker, kind, deal, today)
    return True


def cmd_types(_args) -> None:
    for name, meta in catalog()["types"].items():
        print(f"{name:18} {meta['title']}\n{'':18} {meta['use']}")


def cmd_fields(args) -> None:
    for name, meta in fields_for(args.type).items():
        tag = "optional" if meta.get("optional") else "pipeline only" if meta.get("scoring_only") else \
            "has default" if meta.get("default") else "required"
        print(f"{name:20} [{tag}] {meta['prompt']}")
        if meta.get("example"):
            print(f"{'':20} e.g. {meta['example']}")


def cmd_new(args) -> None:
    out = Path(args.out)
    if out.exists() and not args.force:
        die(f"{out} already exists. Choose another name, or pass --force to overwrite it.")
    deal: dict = {"Type": args.type}
    print("Answer in plain language. Press Enter to accept a default or skip an optional question.\n")
    for name, meta in fields_for(args.type).items():
        default = meta.get("default", "")
        hint = "" if default in ("", "today", "plus90") else f" [{default}]"
        example = f" (e.g. {meta['example']})" if meta.get("example") else ""
        answer = input(f"{meta['prompt']}{example}{hint}: ").strip()
        if answer:
            deal[name] = answer
    out.write_text(json.dumps(deal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved {out}. Next: python loi.py score {out}  then  python loi.py build {out}")


def cmd_build(args) -> None:
    today = date.today()
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    unknown = sorted(set(formats) - {"md", "html", "docx"})
    if unknown or not formats:
        die(f"--format takes md, html and docx (got {args.format!r})")
    tracker = Path(args.track) if args.track else None
    out_dir = Path(args.out)
    if args.csv:
        if not args.type:
            die("--csv needs --type")
        path = Path(args.csv)
        if not path.exists():
            die(f"CSV not found: {path}")
        fields_for(args.type)
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
        except UnicodeDecodeError:
            die(f"{path.name} is not UTF-8. In Excel use 'Save As → CSV UTF-8'.")
        built = sum(build_one(args.type, {k: v for k, v in r.items() if k}, out_dir, formats, today, tracker)
                    for r in rows)
        print(f"\n{built} of {len(rows)} letters written to {out_dir}/")
        if built < len(rows):
            sys.exit(1)
        return
    if not args.deal:
        die("give a deal file, or --type and --csv")
    kind, deal = load_deal(Path(args.deal))
    if not build_one(kind, deal, out_dir, formats, today, tracker):
        sys.exit(1)


def cmd_score(args) -> None:
    kind, deal = load_deal(Path(args.deal))
    deal = apply_defaults(kind, deal, date.today())
    score, gaps, warnings = score_deal(kind, deal)
    print(f"{deal.get('CounterpartyName', '(no counterparty)')}: {grade(score)}, {score}/100")
    print("This measures how specific the letter is. It can't tell you whether the signer means it.")
    for label, items in (("To strengthen it", gaps), ("Check the wording", warnings)):
        if items:
            print(f"\n{label}:")
            for item in items:
                print(f"  - {item}")


def cmd_pipeline(args) -> None:
    today = parse_date(args.today) if args.today else date.today()
    if not today:
        die("--today must be YYYY-MM-DD")
    result = pipeline(Path(args.tracker), today)
    print(f"{'Status':12}{'Letters':>8}{'Indicative annual value':>26}")
    for status in STATUSES:
        print(f"{status.capitalize():12}{result['counts'][status]:>8}"
              f"{money(result['values'][status], result['currency']):>26}")
    print(f"\nYou can say: {result['summary']}")
    print("Quote signed and converted letters only, and call them non-binding. Drafted and sent letters aren't traction.")
    if result["chase"]:
        print("\nNeeds attention:")
        for line in result["chase"]:
            print(f"  - {line}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Draft, score and track letters of intent. See README.md.")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("types", help="list the letter types").set_defaults(func=cmd_types)
    p = sub.add_parser("fields", help="show the facts a letter type needs")
    p.add_argument("--type", required=True)
    p.set_defaults(func=cmd_fields)
    p = sub.add_parser("new", help="answer questions and save a deal file")
    p.add_argument("--type", required=True)
    p.add_argument("--out", required=True, help="deal file to write; name it *.local.json to keep it out of git")
    p.add_argument("--force", action="store_true", help="overwrite an existing deal file")
    p.set_defaults(func=cmd_new)
    p = sub.add_parser("build", help="write letters from a deal file or a CSV")
    p.add_argument("deal", nargs="?", help="deal file (JSON)")
    p.add_argument("--type", help="letter type, with --csv")
    p.add_argument("--csv", help="one letter per row; columns are the field names")
    p.add_argument("--format", default="md,html,docx", help="comma-separated: md, html, docx")
    p.add_argument("--out", default="output", help="output folder")
    p.add_argument("--track", metavar="CSV", help="also add each letter to this tracker")
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("score", help="check how specific a letter would be")
    p.add_argument("deal")
    p.set_defaults(func=cmd_score)
    p = sub.add_parser("pipeline", help="summarize a tracker")
    p.add_argument("tracker")
    p.add_argument("--today", help="YYYY-MM-DD; defaults to today")
    p.set_defaults(func=cmd_pipeline)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
