---
name: customer-discovery
description: Plan customer discovery interviews, write non-leading questions, and analyze notes into evidence. Use when a founder needs to talk to customers, is preparing an interview script, has notes to synthesize, or needs discovery evidence for an application or grant.
---

Help the founder learn what's true from real conversations. This is the evidence Velocity weighs most heavily, so accurate records matter as much as good questions.

## Plan

Ask who they want to learn from and what decision the learning will inform. Then give:
- 2-3 specific customer profiles, with where to find each. Include channels that reach strangers: conferences, walking into workplaces, professional forums, and cold email (`cold-outreach` skill). Velocity notes that people you already know aren't enough.
- The 3 riskiest assumptions the calls should test.

## Script

Write 8-10 questions following The Mom Test (https://www.momtestbook.com/): ask about their life and past behaviour, not the idea or hypothetical futures.

| Weak | Better |
|---|---|
| Would you use a tool that does X? | How do you handle X today? Walk me through the last time. |
| How much would you pay? | What have you spent trying to fix this? Whose budget would that come from? |
| Is this a big problem? | What happens when this goes wrong? What did it cost last time? |

Always close with: "Who else should I talk to?" and "Can I follow up in two weeks?" For experts, add: "What did I get wrong?"

Don't pitch in the first half of a discovery call. Save it for the end, if at all.

## Synthesize

Given notes or transcripts:
1. Separate **facts** (past behaviour, numbers, quotes) from **opinions** and **compliments**. Discard compliments.
2. Build a table of problems, how many people raised each unprompted, the best verbatim quote, and what they do today.
3. Say what changed: which assumptions were confirmed, weakened or killed.
4. Name the strongest signals of commitment: money offered, intros made, time spent.
5. Recommend who to talk to next, and whether anyone is ready for a pilot or a letter of intent.

Attribute only what the notes support. Mark a thin sample as thin, and never round up counts.

## Keep the log

Add every call to `tools/velocity-check/examples/conversations.example.csv`'s format (saved as `*.local.csv` so real names stay out of git). Then run:

`python tools/velocity-check/check.py discovery conversations.local.csv`

It produces a statement with real counts and flags weak spots, like too many calls with people the founder already knew.
