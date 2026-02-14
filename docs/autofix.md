# Autofix Contract

Drace formatter and linter share one rule source: Darkian rule discovery.

- Lint discovery: `check_*` functions
- Formatter discovery: `fixes_*` functions
- Formatter also consumes `fix` payloads emitted by `check_*` findings

Both are loaded automatically through `drace.darkian.get_rules(...)` and
`drace.darkian.get_fixers(...)` using the same `only_rules`/`ignored_rules`
filters.

## Fix payload schema

Each fix is a dict with:

- `op`: operation type
- Operation-specific fields

Supported operations:

1. `replace_line`
- Required fields: `line`, `content`
- Semantics: replace a single 1-based line with a new string

2. `replace_block`
- Required fields: `start`, `end`, `content`
- Semantics: replace inclusive 1-based line range `[start, end]` with a list
  of strings

## Rule authoring guide

Use either pattern:

1. Inline fix in lint finding:
```python
{
    "file": file,
    "line": 10,
    "col": 1,
    "code": "Z999",
    "msg": "something",
    "fix": {"op": "replace_line", "line": 10, "content": "x = 1"},
}
```

2. Dedicated fixer function:
```python
def fixes_z999(context):
    return [{"op": "replace_line", "line": 10, "content": "x = 1"}]
```

## Safety and behavior

- Invalid fix payloads are ignored.
- Fixes are applied from bottom to top to reduce line-shift conflicts.
- Formatter runs multiple passes; if no changes occur, it stops.
- Rules without fixes still lint normally and do not affect formatting.

## Strict CI mode

Use `drace format <path> --strict-fix` to enforce a clean post-format result.

- Drace formats files first.
- Drace re-lints the same target.
- Command exits non-zero if any findings remain.
- `--strict-fix` cannot be combined with `--diff`.
