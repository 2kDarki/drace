# Linting Engine Overview

Drace runs a layered lint pipeline per file:

1. `pycodestyle` checks (patched vendor copy)
2. `pyflakes` checks (mapped to Drace-style codes/messages)
3. Darkian rule checks (`check_*` in `drace/darkian/**`)

Results are merged and sorted by `(line, col)` before reporting.

## Syntax resilience

Drace uses tolerant parsing helpers so syntax errors do not stop all analysis.
This is why a file can still receive useful design/readability findings even
when it contains invalid Python in one region.

## Rule discovery contract

Darkian discovery is dynamic and shared by lint + format:

- `check_*` callables become lint checks
- `fixes_*` callables become formatter fixers
- `check_*` findings may also include inline `fix` payloads

Filtering:

- `only_rules` limits discovery to selected rule codes
- `ignored_rules` excludes selected rule codes

## Vendor exclusion behavior

Embedded vendor code under Drace's own vendored linter paths is skipped by
Drace's own diagnostics so internal copies do not pollute project output.
