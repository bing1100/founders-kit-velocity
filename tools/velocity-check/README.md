# velocity-check

Check your application evidence against the criteria Velocity publishes on its [Apply page](https://www.velocityincubator.com/apply). It has three checks. It needs Python 3.9+ and nothing else.

```bash
cd tools/velocity-check
python check.py discovery conversations.local.csv   # customer conversations → evidence you can quote
python check.py market market.local.json            # bottom-up market sizing
python check.py lint answers.md                     # buzzwords, top-down claims, padded sentences
```

Velocity's own advice comes first. The tool's extra thresholds, such as "20 or more conversations", are this kit's rules of thumb and are labelled as such. **It's unofficial and doesn't predict a decision.**

## discovery

Log every customer conversation as it happens: one row each, columns as in `examples/conversations.example.csv`.

| Column | Meaning |
|---|---|
| `Date` | YYYY-MM-DD |
| `Person`, `Role`, `Organization` | who you spoke to |
| `Method` | `Call`, `In person` or `Survey`. Surveys are counted separately. |
| `Minutes` | length of the conversation |
| `KnewBefore` | `Yes` if you knew them before. Velocity says speaking only to people you know isn't enough. |
| `WouldPay` | `Yes` if they said they'd pay |
| `Source`, `Quote`, `NextStep` | for you; not scored |

The output is a sentence with real counts and dates, the kind Velocity's examples show, plus warnings: mostly people you knew, a small survey, or no one saying they'd pay.

## market

Write each segment with a count, a source, a price, evidence for the price, a conversion rate and a reason. Use `examples/market.example.json` as the format. The tool does the arithmetic, drafts the sentence, and flags missing sources and conversion rates that will draw questions.

## lint

Flags words that hide what the product does ("platform", "solution", "seamless" and others), top-down claims ("$12 billion", "CAGR", "according to a report"), and sentences over 35 words. It exits with code 1 if anything is flagged, so you can use it in a pre-commit hook.

Tests: `python -m unittest discover -s tests`
