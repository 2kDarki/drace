# Contributing to Drace

Thanks for considering a contribution.

## Getting Started

1. Create a virtual environment and install dependencies.
2. Run tests before and after changes:
```bash
pytest -q
```
3. Keep changes focused and include tests for behavior changes.

## Scope Guidelines

- Rule behavior changes should include or update tests under `tests/`.
- CLI behavior changes should include subprocess-based regression tests.
- Documentation examples should use valid `drace` commands.

## Pull Requests

1. Describe the problem and the solution briefly.
2. Include before/after behavior for user-visible changes.
3. Ensure tests pass locally.
