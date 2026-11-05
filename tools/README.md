# Founder tools

Small, scriptable tools for the work that decides early-stage outcomes: talking to customers, proving demand and keeping track. Each has its own README. All are Python 3.9+ and keep your data on your machine.

| Tool | What it does | Needs |
|---|---|---|
| [automated-outreach](automated-outreach/) | Sends personalized cold emails from your own Microsoft 365 mailbox (such as a UW account), a few at a time, from a CSV. Preview, test-to-self and resume after interruption. | `requests` |
| [loi-generator](loi-generator/) | Drafts letters of intent (customer, pilot, design partner, health pilot, letter of support, partnership) as .docx, HTML and Markdown. Scores how specific they are, and tracks your pipeline honestly. | standard library; `python-docx` for .docx |
| [velocity-check](velocity-check/) | Checks application evidence against Velocity's published criteria: customer-conversation log, bottom-up market sizing, buzzword lint. | standard library |
| [velocity-radar](velocity-radar/) | Lists Velocity events and signup links live from the website. | standard library |

How they connect:

```
cold-outreach ──► discovery calls ──► velocity-check discovery ──► application / grant
                         │
                         └──► warm prospects ──► loi-generator ──► loi.py pipeline ──► deck and updates
```

The [Claude skills](../skills/) drive these tools. For example, `/velocity:loi-drafter` collects the facts and runs `loi.py` for you.

## Brainstorm: tools worth building next

Ranked by value to an early Velocity founder against the effort to build. Contributions welcome. Open an issue first, and keep tools small, local-first and honest about their limits.

| # | Tool | Why it matters | Effort |
|---|---|---|---|
| 1 | **Deadline calendar (.ics)** | Turn `velocity-radar` output and grant deadlines into a calendar feed, so the Cornerstone, Up Start and Summer Accelerator windows aren't missed. | Small |
| 2 | **Runway and dilution calculator** | Burn, runway, and a stack of SAFEs converting at a priced round, with an option pool. Founders often misjudge dilution until the round closes. | Small |
| 3 | **Customer quote bank** | Searchable quotes from discovery notes, tagged by problem and segment, to reuse in LOIs, pitches and grant applications without misquoting anyone. | Small |
| 4 | **Investor CRM and update sender** | A pipeline CSV like the LOI tracker, plus monthly updates sent through `automated-outreach`. | Medium |
| 5 | **Data room builder** | Creates a standard folder skeleton and checks for missing items: cap table, IP assignments, signed LOIs, grant obligations. | Small |
| 6 | **Pilot scorecard** | Tracks a pilot's success criteria against its baseline each week, and drafts the results summary for the decision meeting. | Medium |
| 7 | **Warm-intro mapper** | Matches a LinkedIn connections export to a target list, to find who can introduce you. | Medium |
| 8 | **Pitch timer** | Records a rehearsal and reports time per section and words per minute, and runs `velocity-check lint` on the transcript. Built for the two-minute, no-slides format. | Medium |
| 9 | **SR&ED and IRAP time log** | Turns commits and calendar entries into a draft log of experimental work for tax-credit and grant claims, for an accountant to review. | Medium |
| 10 | **Compliance starter** | A CASL consent and opt-out log for outreach, plus privacy checklists (PIPEDA, and PHIPA for health) to bring to a lawyer. | Medium |
| 11 | **Founder agreement worksheet** | Turns the `founder-alignment` conversation into a term summary for a lawyer: vesting, roles, IP assignment, departure. | Small |
