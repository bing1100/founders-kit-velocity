# LOI generator

Draft non-binding letters of intent (LOIs) from a short list of facts, check how much evidence they'd carry, and track them honestly. It writes **Word (.docx)** for the counterparty to edit, **HTML** to print to PDF, and **Markdown** to keep in git.

Founders use LOIs as evidence of demand for incubators, investors and grant reviewers. A letter only carries weight if it's specific, so this tool asks for the details that make it count and scores the result before you send it.

> **Not legal advice.** These templates are a starting point. Whether a letter binds anyone depends on its wording and on how the parties behave. Have a lawyer review them before you rely on them, especially for health care, exclusivity, or anything involving money.

## Letter types

| Type | Use it when |
|---|---|
| `customer` | A prospect intends to buy once the product meets stated needs |
| `pilot` | A prospect intends to run a time-boxed pilot with success criteria |
| `design-partner` | A prospect will shape the product in exchange for early access |
| `health-pilot` | A hospital, clinic or lab intends to pilot. Adds privacy, ethics and procurement steps, and keeps patient data out of the letter |
| `letter-of-support` | An organization backs your grant or program application |
| `partnership` | A partner intends to resell, integrate, supply or co-develop |

Every letter includes the same closing terms. It says it is **not binding**, lets you show it **in confidence to investors and grant reviewers** but not publicize it, and sets an **expiry date** (90 days unless you choose one) and governing law (Ontario by default).

## Quick start

```bash
cd tools/loi-generator
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # only needed for .docx

python loi.py types                                    # list the letter types
python loi.py fields --type pilot                      # what facts each type needs
python loi.py new --type pilot --out acme.local.json   # answer questions, save a deal file
python loi.py score acme.local.json                    # how strong would it be?
python loi.py build acme.local.json --track tracker.local.csv
```

The files go to `output/`, named like `LOI-Acme-Health-pilot-2026-11-05.docx`. Name your deal files and trackers `*.local.json` and `*.local.csv`: the kit's `.gitignore` keeps them, and the people named in them, out of git.

To try it without your own data:

```bash
python loi.py build examples/pilot.example.json --out /tmp/loi-demo
```

## Batch: one letter per prospect

Make a CSV with one row per counterparty and one column per field. See `examples/prospects.example.csv`.

```bash
python loi.py build --type customer --csv prospects.local.csv --track tracker.local.csv
```

A row with a required field empty is skipped and listed, so no half-filled letter is written.

## Score: is this letter worth sending?

```
$ python loi.py score examples/pilot.example.json
Example Regional Health: Strong, 100/100
```

The score checks for:
- a named signer with a title
- the problem in the counterparty's own words
- numbers: quantity, price, pilot fee or success thresholds
- a target date
- a dated next step
- an expiry date

It also warns about **vague words** like "interested", "might" and "potentially", and about **binding-sounding words** like "shall", "guarantee" and "exclusive". The score measures how specific the letter is. It can't tell you whether the signer means it.

## Pipeline: what you can honestly claim

```
$ python loi.py pipeline examples/tracker.example.csv --today 2026-11-05
Status       Letters   Indicative annual value
Sent               1               CAD $45,000
Signed             1              CAD $120,000
Converted          1               CAD $30,000
Expired            1               CAD $90,000

You can say: 1 signed non-binding LOI worth about CAD $120,000 in indicative annual value; 1 converted to paid agreement worth CAD $30,000.
Needs attention:
  - Example General Hospital: sent 28 days ago with no signature. Follow up.
  - Example University Hospital: lapsed on 2026-10-18, so it is counted as expired. Renew it or mark it Expired.
```

Tracker statuses are `Drafted`, `Sent`, `Signed`, `Converted`, `Declined` and `Expired`. A signed letter past its expiry date counts as expired, so a lapsed letter never inflates the number you quote. Call LOIs non-binding, and never present them as revenue or bookings.

## Asking for the letter

`loi_request_email.md` is a follow-up email for people you've already spoken to. It works with [`automated-outreach`](../automated-outreach/):

```bash
cd ../automated-outreach
python send_outreach.py --dry-run --csv warm.local.csv --template ../loi-generator/loi_request_email.md --var SenderName="Jane Doe"
```

## Tips

- **Ask for a number.** A price range or pilot fee is the strongest signal a letter can carry. A paid pilot beats any letter.
- **Let them edit it.** Send the .docx and invite changes. Some organizations will put it on their own letterhead.
- **Health organizations take time.** Privacy review, ethics review and procurement can take months, so start early.
- **Follow up before it lapses.** A pipeline of expired letters says more about your follow-through than about demand.

## Files

| File | What it is |
|---|---|
| `loi.py` | the tool: types, fields, new, build, score, pipeline |
| `templates/*.md` | one template per letter type; `_general.md` holds the shared closing terms |
| `templates/catalog.json` | the fields, prompts and examples for each type |
| `examples/` | a sample deal file, prospect CSV and tracker, with fictional data |
| `loi_request_email.md` | follow-up email asking for a letter |
| `tests/` | `python -m unittest discover -s tests` |

Templates use `{{Field}}` placeholders and `[[if Field]] ... [[end]]` for optional lines. If you add a field, also add it to `catalog.json`. The tests fail if a template uses a field the catalog doesn't define.
