# Drace

Drace is a pragmatic Python linter and formatter focused on readability,
maintainability, and practical code quality signals.

## Highlights

- Lint + format + score workflows in one CLI
- Syntax-tolerant analysis so broken files still receive useful feedback
- Rule-driven autofix with multi-pass formatting
- Strict CI mode via `--strict-fix`
- Configurable defaults through `drace config`

## Installation

```bash
pip install drace
```

## Quick Start

```bash
drace lint src/
drace format src/
drace format src/ --diff
drace format src/ --strict-fix
drace score src/
```

## Configuration

```bash
drace config list
drace config line_len 100
drace config ignored_rules + Z221
drace config reset all
```

Flexible separators are supported:

```bash
drace config line_len = 100
drace config color :: on
```

## Documentation

- `docs/README.md`
- `docs/engine.md`
- `docs/autofix.md`
- `docs/config.md`
- `docs/rules/README.md`

## Philosophy

Drace emphasizes structure over cosmetic compliance. It flags maintainability
pressure early so teams can keep code easy to understand and safe to change.

## Limitations

- Python-focused tooling
- Deeper analysis may be slower than style-only linters
- Opinionated defaults may differ from strict PEP8-only setups

## License

MIT. See `LICENSE`.

## Contributing

See `CONTRIBUTING.md`.
