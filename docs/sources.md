# Sources and discrepancies

How this kit's Velocity content was gathered, and the places where Velocity's own pages disagree. **Last checked: 2026-11-05.**

## What we read

- Every page in [velocityincubator.com/sitemap.xml](https://www.velocityincubator.com/sitemap.xml) under `/apply`, `/how-we-help`, `/about`, `/students`, `/contact-us`, `/non-dilutive-awards-and-grants-velocity`, `/discounts`, `/sponsors`, `/give`, `/momentum-2025`, `/code-of-conduct` and `/velocity-expert-community`, plus all ~45 `/programs-events/` pages. The sitemap also lists 600+ company pages and 400+ news posts, which aren't summarized here.
- [velocity.fund](https://velocity.fund/): home, How We Help and Team.
- University of Waterloo: [Entrepreneurship programs](https://uwaterloo.ca/entrepreneurship/programs), [funding finder](https://uwaterloo.ca/entrepreneurship/program-finder/funding), [IP policy](https://uwaterloo.ca/entrepreneurship/our-ip-policy), [WatCo](https://uwaterloo.ca/research/waterloo-commercialization-office-watco) and [Innovation Arena](https://uwaterloo.ca/innovation-arena/).
- A web search for other Velocity sites. Results:
  - `concept.uwaterloo.ca` now redirects to velocityincubator.com.
  - `velocityincubator.com/spaces` now redirects to `/how-we-help`.
  - `velocity.uwaterloo.ca` and `velocityfund.ca` no longer resolve.
  - `uwaterloo.ca/velocity` returns 404.
  - The old "External funding opportunities" page on velocityincubator.com now redirects to `/how-we-help`.
  - Third-party profiles (for example on altss.com) give older Velocity Fund cheque sizes and were not used.

Content is paraphrased and linked rather than copied. The text, logo and trademarks belong to their owners.

## Discrepancies on Velocity's own pages

| Topic | What differs | What this kit does |
|---|---|---|
| Headline stats | The home page and footer say 500+ startups, 1,200+ founders and $40B. Parts of the About page say 400+, 1,151 and $35B. The Innovation Arena page says 400+ and US$26B. | Uses the home page figures |
| Velocity Fund core cheque | $100K-$1M on the fund's home page; $150K-$1M on its How We Help page | Shows both |
| Cornerstone length | "10-day sprint" in its header and on the Sponsors page; "two-week sprint" in its body | Calls it a 10-day sprint |
| Co-op Problem Award | Grants page: $1,500 top award, $750 second, and up to 10 × $500. Co-op Simulation page: up to ten $500 tuition scholarships. | Shows the Grants page amounts and links both |
| Velocity science room | ESC 232 on the Spaces page; EC 231 on the Contact page | Shows both |
| Incubator floor space | About 45,000 sq ft of office (How we help) inside a 90,000 sq ft building (Innovation Arena) | Gives both, with context |
| Contact email on the Grants page | `velocity@uwaterloo.com`, which is likely a typo. The Spaces page uses `velocity@uwaterloo.ca`, and the Contact page uses `info@velocityincubator.com`. | Uses info@velocityincubator.com |
| Dates on Up Start, Summer Accelerator and Lab2Market | Some pages still show 2025 or early-2026 dates | Marked as past cycles; check the page |
| Velocity Fund Apply button | A `mailto:` link with no address | Uses hello@velocity.fund, shown on the same site |

## Keeping this current

- **Automatically:** the weekly [Velocity refresh](../.github/workflows/velocity-refresh.yml) workflow compares the sitemap with [`data/velocity-pages.json`](../data/velocity-pages.json), refreshes the README's auto-updated events list, and opens a pull request listing every changed page. See the README's [Keeping This Kit Current](../README.md#-keeping-this-kit-current) section.
- **With Claude:** run `/kit-refresh` in Claude Code from a clone of the repository to check the flagged pages and update the hand-written tables.
- **By hand:**
  - `python scripts/refresh.py --check` shows what changed;
  - `python tools/velocity-radar/radar.py --all` lists every event page;
  - `python scripts/check_links.py` checks every link.

Update the "Last checked" dates only for sections you verified.
