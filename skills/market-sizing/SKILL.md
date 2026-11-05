---
name: market-sizing
description: Build a bottom-up market size from customer counts, segments, price and conversion, instead of top-down market reports. Use when a founder needs market size for an application, pitch deck or grant, or has a TAM number they can't defend.
---

Replace the "X billion dollar market" slide with numbers the founder can defend. Velocity's application guidance says market-report figures aren't compelling: show how many customers exist, how you segment them, what you'd charge, and why you can convert them.

## Method

1. **Define who buys, narrowly.** "Ontario hospital labs running over 500 tests a day" rather than "healthcare".
2. **Count them from a checkable source:** government registries, association directories, licensing bodies, company databases. Search for real sources and link them. If you can't verify a figure, label it an assumption. Never present an estimate as a fact.
3. **Set a price from evidence:** what customers said, what they pay for the alternative, or the cost of the problem.
4. **Set conversion with a reason:** why these customers and not the alternative, and through what channel.
5. **Order the segments.** Which is first, what do you learn there, and what does it unlock?

## Tool

Save the inputs in the format of `tools/velocity-check/examples/market.example.json`, named `market.local.json`, then run:

`python tools/velocity-check/check.py market market.local.json`

It does the arithmetic, drafts the sentence for an application, and flags missing sources and unusually high conversion.

## Output

- A segment table: customers, source, price, conversion, reasoning.
- A short paragraph in plain language. For Velocity, lead with the inputs; they say they'll do the multiplying.
- The weakest assumption, and the cheapest way to test it. Usually that's more customer calls.
- If the honest number is small, say so. A small first segment with a credible path beats an inflated total.

Top-down numbers can appear as context, but never as the whole story.
