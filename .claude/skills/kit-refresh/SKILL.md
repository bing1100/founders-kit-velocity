---
name: kit-refresh
description: Maintainer skill for founders-kit-velocity. Checks Velocity's website for changes and updates the README, docs and skills to match, then opens a pull request. Use when asked to refresh, update or re-verify the kit, or to act on a "Velocity refresh" pull request.
---

You keep this kit accurate. Founders act on its dates, amounts and eligibility rules, so **every change must come from a page you read in this session**. If you can't verify something, leave it as it is and say so in the pull request. Don't guess. Never push to `main` and never merge: your output is a pull request for a person to review.

## 1. Start from the latest state

1. Run `git fetch origin` and `gh pr list --head automated/velocity-refresh --state open`.
   - If the automated pull request is open, check out its branch and build on it. Its description is the change report.
   - Otherwise, branch from `origin/main` as `refresh/YYYY-MM-DD` and run `python scripts/refresh.py --report /tmp/velocity-report.md`. That updates the events block and `data/velocity-pages.json` and writes the report.
2. Run `python tools/velocity-radar/radar.py --days 120` for upcoming events with signup links.

## 2. Check every flagged page

For each page in the report's **Edited**, **New** and **Removed** tables, read the live page. Use WebFetch, or `curl -sL <url> | pandoc -f html -t plain`. Then go to each `file:line` the report lists, and to any related rows it doesn't list.

| Page type | Where it appears |
|---|---|
| `/programs-events/*` | README **Happening Now**, **Pitch Competitions & Challenges**, **Workshops**, **Programs** |
| `/non-dilutive-awards-and-grants-velocity` | README **Funding & Awards**; skill `funding-finder` |
| `/apply`, `/how-we-help`, `/students` | README **The Incubator**; `docs/velocity-guide.md`; skill `velocity-application` |
| `/velocity-expert-community`, `/discounts`, `/contact-us`, `/about` | README **Quick Links**, **Coaching**, **Discounts**; guide **Contacts** |
| velocity.fund pages | README **Velocity Fund & Investors**; guide **Velocity Fund**; skill `fundraise-prep` |
| New news posts | Skim titles for new programs, awards, prizes or deadlines |

## 3. Update with care

- **Happening Now:** remove anything that has ended. Add events and deadlines in the next ~6 weeks that matter to founders. Link the signup form only while registration is open. Otherwise link the event page.
- **Recurring tables:** update "Last ran", prizes and eligibility. Don't remove a recurring program just because it's between cycles.
- **New pages:** add them to the right table if they're useful to founders. Not every page belongs.
- **Removed pages:** replace or remove the links. Run `python scripts/check_links.py` to find any others.
- **Contradictions:** where Velocity's pages disagree, show both values or the more conservative one, and add a row to `docs/sources.md`.
- **Content:** paraphrase and link. Don't copy long passages of Velocity's text.
- **Dates:** update "last checked" dates only for sections you verified: the README notice above Events, the badge and footer, and the guide's and `docs/sources.md`'s headers. Update the badge only after a full pass.
- **Style:** keep the existing table formats and plain style.
- **Out of scope:** don't touch the auto-updated block between the `velocity-radar` markers. The script owns it.

## 4. Verify

All must pass before you open a pull request:

```bash
for d in tools/loi-generator tools/velocity-check tools/velocity-radar; do (cd $d && python -m unittest discover -s tests); done
python -m unittest discover -s scripts/tests
python scripts/check_links.py
```

Fix any link reported as BROKEN that you introduced or that a page change caused. Links marked "blocked" are sites refusing automated checks; open a few by hand.

## 5. Open the pull request

Commit with a clear message, push the branch, and run `gh pr create`, or update the open automated pull request. The description must have:
- **Changed:** one line per edit, with the source URL. For example: "Cornerstone: Winter 2027 dates, Jan 12 to Feb 5 (source)".
- **Couldn't verify:** anything left unchanged because a page was unclear or unreachable.
- **Needs a decision:** for example, a new program that might deserve its own row.

Reply to the user with the pull request link and a short summary. Remind them to spot-check dates and amounts against the sources before merging.
