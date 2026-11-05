#!/usr/bin/env python3
"""Check startup application evidence against the criteria Velocity publishes at velocityincubator.com/apply.

  python check.py discovery conversations.csv   turn a customer-conversation log into evidence you can quote
  python check.py market market.json            bottom-up market sizing: customers, segments, price, conversion
  python check.py lint answers.md               flag buzzwords, top-down claims and padded sentences

This is an unofficial helper. Its thresholds are this kit's rules of thumb, not Velocity's scoring.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Velocity's guidance names "platform" and "solution". The rest are common words with the same problem.
BUZZWORDS = ["platform", "solution", "solutions", "seamless", "seamlessly", "leverage", "leveraging", "cutting-edge",
             "innovative", "revolutionary", "disruptive", "game-changing", "synergy", "hyper-personalized",
             "best-in-class", "world-class", "next-generation", "state-of-the-art", "ecosystem", "holistic",
             "end-to-end", "robust", "empower", "empowering", "unlock", "reimagine", "reinvigorate", "ai-driven",
             "ai-powered"]
TOP_DOWN = [r"\bcagr\b", r"\$?\d+(\.\d+)?\s*(b|bn|billion|t|trillion)\b", r"\bbillion[- ]dollar\b",
            r"\bmarket (is|was) (projected|expected|estimated|valued)\b", r"\baccording to (a|an|the) (recent )?report\b",
            r"\b\d+(\.\d+)?% of the market\b", r"\bif we (capture|get|win) (just )?\d"]
LONG_SENTENCE = 35


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def yes(value: str) -> bool:
    return (value or "").strip().lower() in ("y", "yes", "true", "1")


def parse_date(value: str):
    try:
        return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


# --- discovery -------------------------------------------------------------------------------------------------------
def discovery(path: Path) -> dict:
    if not path.exists():
        die(f"conversation log not found: {path}")
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except UnicodeDecodeError:
        die(f"{path.name} is not UTF-8. In Excel use 'Save As → CSV UTF-8'.")
    needed = {"Date", "Person", "Role", "Minutes", "KnewBefore", "Method"}
    if rows and not needed <= set(rows[0]):
        die(f"{path.name} needs the columns {', '.join(sorted(needed))}. See examples/conversations.example.csv.")
    conversations, surveys, bad = [], [], []
    for i, r in enumerate(rows, 2):
        day = parse_date(r.get("Date", ""))
        try:
            minutes = float(r.get("Minutes") or 0)
        except ValueError:
            minutes = -1
        if not day or minutes < 0 or not (r.get("Person") or "").strip():
            bad.append(f"row {i}: needs a person, a YYYY-MM-DD date and a number of minutes")
            continue
        record = {**r, "_day": day, "_minutes": minutes}
        (surveys if (r.get("Method") or "").strip().lower() == "survey" else conversations).append(record)
    out = {"conversations": len(conversations), "surveys": len(surveys), "problems": bad, "flags": []}
    if not conversations:
        out["flags"].append("No conversations logged yet. Velocity looks for real conversations, with counts and dates.")
        out["statement"] = ""
        return out
    days = sorted(c["_day"] for c in conversations)
    long_calls = [c for c in conversations if c["_minutes"] >= 30]
    strangers = [c for c in conversations if not yes(c.get("KnewBefore", ""))]
    roles = sorted({(c.get("Role") or "").strip() for c in conversations if (c.get("Role") or "").strip()})
    orgs = {(c.get("Organization") or "").strip().lower() for c in conversations if (c.get("Organization") or "").strip()}
    wants = [c for c in conversations if yes(c.get("WouldPay", ""))]
    out.update(first=days[0], last=days[-1], long_calls=len(long_calls), strangers=len(strangers), roles=roles,
               organizations=len(orgs), would_pay=len(wants))
    if len(strangers) < len(conversations) / 2:
        out["flags"].append(f"Only {len(strangers)} of {len(conversations)} were people you didn't already know. "
                            "Velocity says speaking only to people you know isn't enough.")
    if surveys and len(surveys) < 100:
        out["flags"].append(f"{len(surveys)} survey response{'s' if len(surveys) != 1 else ''} logged. Velocity finds surveys less compelling than "
                            "conversations and wants hundreds of responses at minimum, so lead with your calls.")
    if len(conversations) < 20:
        out["flags"].append(f"{len(conversations)} conversations so far. Kit rule of thumb: aim for 20 or more before "
                            "you apply.")
    if not wants:
        out["flags"].append("No one is marked WouldPay. Ask about budget and willingness to pay, since Velocity may ask "
                            "for proof that your customer would buy.")
    who = ", ".join(roles[:3]) if roles else "potential customers"
    span = f"{days[0]:%B %Y} and {days[-1]:%B %Y}" if days[0].strftime("%Y%m") != days[-1].strftime("%Y%m") else \
        f"{days[0]:%B %Y}"
    length = (f", {len(long_calls)} of them 30 minutes or longer" if long_calls else "")
    out["statement"] = (f"Between {span} we held {len(conversations)} conversations with potential customers "
                        f"({who}){length}. {len(strangers)} were with people we didn't know beforehand.")
    if wants:
        out["statement"] += f" {len(wants)} said they would pay for a product that solved this."
    if orgs:
        out["statement"] += f" They came from {len(orgs)} organizations."
    return out


def cmd_discovery(args) -> None:
    r = discovery(Path(args.log))
    print(f"Conversations: {r['conversations']}   Survey responses: {r['surveys']}")
    if r["conversations"]:
        print(f"Date range: {r['first']} to {r['last']}")
        print(f"30+ minutes: {r['long_calls']}   Didn't know them before: {r['strangers']}   "
              f"Would pay: {r['would_pay']}   Organizations: {r['organizations']}")
    if r["statement"]:
        print(f"\nDraft for your application (add how you found them, and what you learned):\n  {r['statement']}")
    for label, items in (("Worth fixing", r["flags"]), ("Rows skipped", r["problems"])):
        if items:
            print(f"\n{label}:")
            for item in items:
                print(f"  - {item}")


# --- market ----------------------------------------------------------------------------------------------------------
def number(value, what: str, name: str) -> float:
    try:
        return float(str(value).replace(",", "").replace("$", "").replace("%", "").strip())
    except (TypeError, ValueError):
        die(f"segment {name!r}: {what} must be a number, got {value!r}")


def market(path: Path) -> dict:
    if not path.exists():
        die(f"market file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"{path.name} is not valid JSON: {e}")
    segments = data.get("segments") if isinstance(data, dict) else None
    if not segments:
        die(f"{path.name} needs a \"segments\" list. See examples/market.example.json.")
    rows, flags = [], []
    for s in segments:
        name = str(s.get("name", "(unnamed)"))
        customers = number(s.get("customers"), "customers", name)
        price = number(s.get("price_per_year"), "price_per_year", name)
        conversion = number(s.get("conversion_percent"), "conversion_percent", name)
        if conversion > 100 or conversion < 0:
            die(f"segment {name!r}: conversion_percent must be between 0 and 100")
        if not s.get("customers_source"):
            flags.append(f"{name}: say where the customer count comes from.")
        if not s.get("price_evidence"):
            flags.append(f"{name}: say why customers would pay this price, ideally from your conversations.")
        if not s.get("conversion_reason"):
            flags.append(f"{name}: say why you can convert this share, and why you'd beat the alternatives.")
        if conversion > 25:
            flags.append(f"{name}: {conversion:g}% conversion is high. Expect to be asked why, and have evidence ready.")
        rows.append(dict(name=name, customers=customers, price=price, conversion=conversion,
                         won=customers * conversion / 100, revenue=customers * conversion / 100 * price,
                         source=s.get("customers_source", "")))
    summary = "; ".join(f"{r['customers']:,.0f} {r['name']} ({r['source'] or 'source needed'}), at ${r['price']:,.0f} a "
                        f"year, aiming to convert {r['conversion']:g}%" for r in rows)
    return {"rows": rows, "flags": flags, "total": sum(r["revenue"] for r in rows), "statement":
            f"We count {summary}."}


def cmd_market(args) -> None:
    r = market(Path(args.file))
    print(f"{'Segment':30}{'Customers':>12}{'Price/yr':>11}{'Convert':>9}{'Customers won':>15}{'Annual revenue':>16}")
    for x in r["rows"]:
        print(f"{x['name'][:29]:30}{x['customers']:>12,.0f}{x['price']:>11,.0f}{x['conversion']:>8g}%"
              f"{x['won']:>15,.0f}{x['revenue']:>16,.0f}")
    print(f"{'Total':77}{r['total']:>16,.0f}")
    print(f"\nDraft for your application:\n  {r['statement']}")
    print("\nVelocity asks for the inputs and says it will do the multiplying, so lead with the sentence above and keep "
          "the revenue total for your own planning.")
    if r["flags"]:
        print("\nWorth fixing:")
        for f in r["flags"]:
            print(f"  - {f}")


# --- lint ------------------------------------------------------------------------------------------------------------
def lint_text(text: str) -> list[tuple[int, str, str]]:
    findings = []
    for number_, line in enumerate(text.splitlines(), 1):
        lowered = line.lower()
        for word in BUZZWORDS:
            if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", lowered):
                findings.append((number_, "buzzword", f"\"{word}\": say what the product actually does"))
        for pattern in TOP_DOWN:
            m = re.search(pattern, lowered)
            if m:
                findings.append((number_, "top-down", f"\"{m.group(0)}\": replace it with customer counts, price and "
                                                      "conversion"))
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            count = len(sentence.split())
            if count > LONG_SENTENCE:
                findings.append((number_, "long", f"{count}-word sentence: \"{' '.join(sentence.split()[:6])}...\""))
    return findings


def cmd_lint(args) -> None:
    path = Path(args.file)
    if not path.exists():
        die(f"file not found: {path}")
    text = path.read_text(encoding="utf-8")
    findings = lint_text(text)
    print(f"{len(text.split())} words, {len(findings)} finding(s)")
    for line, kind, message in findings:
        print(f"  line {line:<4} {kind:9} {message}")
    if findings:
        print("\nTest: could a child or a grandparent picture your product after reading this?")
        sys.exit(1)
    print("Nothing flagged. A linter can't judge clarity, so have someone outside tech read it too.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Check application evidence against Velocity's published criteria.")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("discovery", help="summarize a conversation log")
    p.add_argument("log")
    p.set_defaults(func=cmd_discovery)
    p = sub.add_parser("market", help="bottom-up market sizing")
    p.add_argument("file")
    p.set_defaults(func=cmd_market)
    p = sub.add_parser("lint", help="flag buzzwords and top-down claims")
    p.add_argument("file")
    p.set_defaults(func=cmd_lint)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
