---
name: loi-drafter
description: Draft, strengthen and track non-binding letters of intent from customers, pilot sites, design partners and grant supporters using the kit's LOI generator. Use when a founder wants an LOI, letter of support, or evidence of customer demand for investors or grant applications.
---

Help the founder get letters of intent that are true, specific and useful. A letter records what a real person said they intend to do, so it can't be stronger than the conversation behind it.

## Rules

- **Only use facts the founder gives you.** If the counterparty hasn't said it, it doesn't go in. Mark gaps and ask. Never invent quantities, prices, dates or quotes.
- **The founder drafts; the counterparty decides.** Encourage them to edit the letter and sign on their own letterhead if they prefer.
- **Non-binding stays non-binding.** Don't add commitments. Words like "shall", "guarantee" or "exclusive" could create obligations and scare off signers. If the founder wants a commitment, they need a contract and a lawyer.
- **This is not legal advice.** Whether a letter binds anyone depends on its wording and the parties' conduct. Suggest a lawyer's review before relying on a template, especially for health, exclusivity or money changing hands.

## Steps

1. Find the tool: `${CLAUDE_PLUGIN_ROOT}/tools/loi-generator/loi.py`, or `tools/loi-generator/loi.py` in a clone. Run `python loi.py types` and pick with the founder:
   - `customer`: intends to buy
   - `pilot`: time-boxed trial with success criteria
   - `design-partner`: shapes the product in exchange for early access
   - `health-pilot`: hospital, clinic or lab, with privacy, ethics and procurement steps
   - `letter-of-support`: backs a grant application
   - `partnership`: channel, supplier or co-development
2. Run `python loi.py fields --type <type>`, and collect the answers from the founder's notes or by asking. Ask what the counterparty actually said about budget and timing.
3. Save a deal file named `<company>.local.json`, with `"Type"` set, following `examples/pilot.example.json`. The `.local` name keeps it out of git.
4. Run `python loi.py score <file>`. Explain the gaps, and which questions to go back and ask. Don't paper over a gap by inventing an answer.
5. Run `python loi.py build <file> --track tracker.local.csv`, then read the output as the signer would.
6. For the ask itself, adapt `tools/loi-generator/loi_request_email.md`.

## What makes a letter strong

A named person with budget influence, the problem in their words, a number (units, price, budget), a date, measurable success criteria, a dated next step, and permission to share with investors and grant reviewers. A paid pilot beats any letter.

## Reporting traction honestly

Run `python loi.py pipeline tracker.local.csv`. Quote only signed or converted letters and always say they're non-binding. Drafted, sent and lapsed letters aren't traction. Don't let a founder describe LOIs as contracts, bookings or revenue.

## Health organizations

Use `health-pilot`. Don't put personal health information in a letter. Flag that privacy review, ethics board review and procurement can take months, so plan ahead. Ontario's health privacy law (PHIPA) applies to many custodians; see https://www.ipc.on.ca/.
