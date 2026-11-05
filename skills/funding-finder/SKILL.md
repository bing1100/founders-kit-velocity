---
name: funding-finder
description: Match a founder to non-dilutive grants, awards, competitions and programs at Velocity, the University of Waterloo and in Canada, checking eligibility and deadlines on the live pages. Use when a founder asks what funding they qualify for, or is looking for grants or free money.
---

Find funding this founder can realistically win, and be honest about what doesn't fit. Deadlines and rules change, so **never state a deadline or amount as current without checking the program's live page in this session.** If you can't check, say so.

## Ask first

Skip what you already know:
- Connection to UW: current student, recent grad and date, researcher or PhD, staff or faculty, none
- Other Ontario institution? Velocity founder?
- Stage, incorporated or not, and funds or revenue received so far
- Sector: deep tech, health, climate, agri-food, software, hardware, social impact
- Full-time on the startup? Work term or co-op coming up?
- Domestic or international status, because some programs restrict this

## Sources, in order

1. The README's **Funding & Awards** table, and `https://www.velocityincubator.com/non-dilutive-awards-and-grants-velocity`.
2. The events and challenges in the README. Competitions are often the fastest money. Run `python tools/velocity-radar/radar.py --days 120` for current dates.
3. UW's finder: `https://uwaterloo.ca/entrepreneurship/program-finder/funding`.
4. Canadian programs in the README: NRC IRAP, SR&ED, Lab2Market, IPON and others. Search for current terms.

## Check prerequisites

Many awards chain together, so spot the dependency. Cornerstone is required for the Abundance and Jain awards, and strongly affects Up Start. The Momentum Grants prioritize full-time recent grads and Summer Accelerator alumni.

## Output

| Program | Amount | Fit (High/Medium/Low) and why | Prerequisite | Next deadline (date checked) | Effort | Link |

Then give:
- The top 3 in the order to pursue them, considering prerequisites and timing.
- What you excluded, with the reason.
- What to do this week.

Non-dilutive means no equity is given up, but it can carry conditions: reporting, matching funds, IP disclosure. Note any you find. Never advise misrepresenting status to qualify. Point founders to an accountant for tax-credit claims.
