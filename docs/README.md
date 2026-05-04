# Drace Documentation

Drace is a pragmatic Python linter and formatter that combines:

- style checks
- semantic checks
- rule-driven diagnostics
- rule-driven autofix

The goal is to keep code understandable under real-world change pressure.

## Documentation map

1. `docs/philosophy.md`
2. `docs/standards.md`
3. `docs/rules/README.md`
4. `docs/engine.md`
5. `docs/autofix.md`
6. `docs/config.md`
7. `docs/scoring.md`

## Quick usage reference

```bash
drace lint src/
drace format src/
drace format src/ --diff
drace format src/ --strict-fix
drace score src/
drace config list
```

## Design intent

Drace does not treat "clean code" as purely stylistic. It reports structural pressures such as coupling, repeated control flow, and oversized units so teams can improve maintainability before those pressures become defects.
