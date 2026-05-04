# Darkian Scoring

The Darkian score is a heuristic metric representing code health.

For each analyzed file, Drace computes:

`score = 100 * (1 - findings / lines)`

The final score shown in CLI output is the average of per-file scores, clamped at `>= 0`.

## What the score is good for

- Tracking quality trend over time
- Comparing one revision against another
- Quickly spotting large regressions

## What the score is not

- A substitute for review
- A complete quality definition
- A rule to optimize blindly
