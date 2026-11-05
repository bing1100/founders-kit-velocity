# Claude skills for Velocity founders

Fourteen [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) for the work early founders do every week. Several call this kit's [tools](../tools/), and all follow the same rules:
- **Never invent evidence.** Customers, quotes, numbers and dates come from you. Gaps are marked `[NEEDS: ...]`, not filled in.
- **The live page wins.** Velocity rules and deadlines are checked on the current page, not recalled.
- **You send.** Skills draft and preview, and never send email or sign anything.
- **Not legal, tax or investment advice.** Skills say when to bring in a lawyer, accountant or patent professional.

## Install

**As a plugin.** In Claude Code:

```
/plugin marketplace add bing1100/founders-kit-velocity
/plugin install velocity@founders-kit-velocity
```

Skills are then available as `/velocity:<skill>`, and Claude also picks them up automatically when your request matches.

**From a clone.** Open Claude Code in the repository folder. `.claude/skills` links to this folder, so the skills load as project skills, and the tools are right there.

**Just the skills, everywhere:**

```bash
cp -r skills/* ~/.claude/skills/
```

Skills that run tools look for them next to the plugin, or in a clone of this repository.

## The skills

| Skill | Use it to | Uses |
|---|---|---|
| `velocity-application` | Review or draft a Velocity application against its published criteria; prepare for the interview | velocity-check |
| `validate-idea` | Stress-test an idea and design cheap tests before you build | |
| `customer-discovery` | Write non-leading interview questions; turn notes into evidence | velocity-check |
| `cold-outreach` | Write cold emails and preview a batch; you send | automated-outreach |
| `loi-drafter` | Draft, score and track letters of intent | loi-generator |
| `market-sizing` | Size a market bottom-up: customers, segments, price, conversion | velocity-check |
| `pilot-design` | Design a paid pilot with success criteria and a decision date | loi-generator |
| `funding-finder` | Match yourself to grants, awards and competitions, checked live | velocity-radar |
| `ip-readiness` | UW's IP policy (Policy 73), disclosure risk before pitches, who to ask | |
| `two-minute-pitch` | Write a spoken pitch for the Velocity Pitch Competition or a mixer | |
| `fundraise-prep` | Decide whether to raise; build the narrative, deck outline, investor list and data room | |
| `investor-update` | Write a short monthly update for investors or coaches | |
| `founder-alignment` | Align cofounders on roles, equity and commitment; write the founder story | |
| `weekly-sprint` | Turn goals or Velocity milestones into a weekly plan, then review it | |

A typical path: `validate-idea` → `customer-discovery` + `cold-outreach` → `market-sizing` → `velocity-application` → `weekly-sprint` for milestones → `pilot-design` + `loi-drafter` → `funding-finder` → `two-minute-pitch` → `fundraise-prep`.

## Other founder skill packs

We looked at these packs for ideas. The skills here are written from scratch for Velocity and Waterloo, and none of their text is copied.

| Pack | What it covers | Ideas borrowed |
|---|---|---|
| [emotixco/claude-skills-founder](https://github.com/emotixco/claude-skills-founder) (MIT) | 13 skills: validation, personas, competitors, pricing, GTM, pitch deck, fundraising, metrics | The build / pivot / kill verdict and cheap experiments in `validate-idea`; a structured fundraise checklist |
| [slavingia/skills](https://github.com/slavingia/skills) | *The Minimalist Entrepreneur*: community, validation, MVP, first customers, pricing, processes | Selling one customer at a time; a bias toward profitable, sustainable growth |
| [ognjengt/founder-skills](https://github.com/ognjengt/founder-skills) (MIT) | Marketing and product: copywriting, outreach, PRDs, SOPs, launch plans | Outreach structure; repeatable operating procedures |
| [anthropics/skills](https://github.com/anthropics/skills) | Anthropic's examples, including document skills for .docx, .pptx and .pdf | Useful alongside these for decks and documents |

They pair well with these skills, for example for pricing, competitor matrices and launch copy.
