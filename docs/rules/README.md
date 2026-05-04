# Z-Series Rules

Each Z-series rule documents a specific design or readability pressure.

Every rule description answers:
1. What the rule targets
2. Why that issue matters
3. What kind of thinking it encourages
4. What the rule explicitly does not claim

Implementation details are intentionally excluded.

Rules are meant to be understood, not memorized.

## Range overview

- `Z100-Z199`: Layout and visual structure
- `Z200-Z219`: Control-flow density and readability pressure
- `Z220-Z239`: Design concerns such as coupling, API shape, and cohesion
- `Z999`: Placeholder for uncoded rules

Use rule docs to decide whether to:

1. apply formatting-only fixes
2. refactor design surfaces
3. tune rule scope with `only_rules` / `ignored_rules`
