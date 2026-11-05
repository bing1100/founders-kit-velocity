---
name: cold-outreach
description: Write personalized cold emails and prepare a batch for the kit's automated-outreach sender, for customer discovery, expert calls or warm-up before a letter of intent. Use when a founder wants to reach people they don't know by email.
---

Help the founder get replies from strangers without being spammy. You prepare and preview. **The founder does all sending.**

## Rules you always follow

- **Never send email yourself.** Only run `send_outreach.py --dry-run`. The founder runs `--test-self` and real batches in their own terminal.
- **Never ask for, read or handle an access token.** It can send mail as the founder. If one is pasted into chat, tell them to treat it as compromised and sign out of Graph Explorer to revoke the session.
- **Never invent personalization.** If you can't verify a detail, ask the founder or leave the row incomplete, which makes the tool skip it.
- **Keep real lists out of git.** Name them `*.local.csv`.

## Write the template

Use the structure in `tools/automated-outreach/email_template.md`:
1. A subject line that shows it's meant for this person.
2. Who you are, in one sentence.
3. The problem as your **understanding**, for them to correct. People reply to fix something specific.
4. One real, verifiable detail about them.
5. A specific ask: 15 minutes at a named time.
6. An opt-out line. Canada's anti-spam law (CASL) has requirements, so keep it, and identify the sender. Point founders to https://crtc.gc.ca/eng/internet/anti.htm for the rules, and suggest legal advice for commercial campaigns.

Keep it under 120 words of body text. Write plainly. Don't sell in the first email.

## Prepare the batch

1. Build the CSV with one row per person and a column per placeholder.
2. Read `tools/automated-outreach/README.md`, then run a preview: `python send_outreach.py --dry-run --limit 3 --csv x.local.csv --var SenderName="..."`.
3. Read the previews as the recipient would. Fix anything generic.
4. Give the founder the next commands to run themselves, in order: `--check`, `--test-self`, then `--limit 10`.

## Limits to pass on

- Send small batches: 10-20 a day, and no more than about 50. Sudden volume can get a mailbox blocked.
- The README's guidance on UW mailboxes applies: use a UW address for university and research purposes, and check whether company outreach should come from a company address.
- One polite follow-up after 5-7 days. Honour every opt-out immediately by marking the row `Do not contact`.

## After replies

Log each call for `customer-discovery`. Use `tools/loi-generator/loi_request_email.md` for people ready to sign a letter of intent.
