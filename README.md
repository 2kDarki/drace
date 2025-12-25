# Drace – The Pragmatic Linter & Formatter

**Drace** is a resilient, opinionated, and user-centric linter + formatter for Python. It doesn't just enforce convention — it encourages **better code thinking**, inspired by **The Pragmatic Programmer** and real-world software philosophies.

---

## Features

- **Resilient Parsing:** Drace won't crash on fatal syntax errors — it continues linting and shows where things broke
- **Custom Linting Rules:** Includes pragmatic and aesthetic rules like:
  - `Z200`: Suggests one-liners where appropriate
  - `Z202`: Suggests refactoring for DRY-ness
  - `Z221`: Warns about bloated functions
  - `Z222`: Flags high external dependency usage
- **AST-based & Rule-based Checks:** Deep analysis where needed, quick rules where not
- **Formatter Included:** Drace has a formatter with opinionated but readable output
- **User-Friendly Config System:**
  - Supports CLI and interactive (USSD-like) editing
  - Temporary overrides and persistent defaults
- **Readable Output:**
  - Colored, well-padded output for clarity
  - Aligns messages visually for fast scanning

---

## Installation

```bash
pip install drace
```

## Usage

### Linting & Formatting

```bash
drace lint path/to/file.py       # Lint a file
drace format path/to/file.py     # Format a file
drace                            # Defaults to linting current directory
```

### Scoring Code Quality

```bash
drace score path/to/dir
```

> Calculates a "Darkian Standard" score based on lines vs issues.

### Configuration

```bash
drace config                    # Launch interactive (USSD-style) config
drace config line_len 100       # Set line length limit
drace config list               # View current config
drace config reset              # Reset all defaults
drace config reset line_len     # Reset a key
```

Drace allows multiple separator styles: `=`, `:`, `::`, etc:
```bash
drace config line_len = 100
```
---

## Philosophy

Drace is **pragmatic-first**. It values **readability**, **clarity**, and **real-world coding sensibilities** over strict adherence to PEP8. It helps you write code that's both clean and thoughtful.

Unlike tools like `flake8` or `black`, Drace:
- Handles broken files gracefully
- Suggests deeper improvements (e.g., cohesion, function size)
- Doesn't treat aesthetics and logic as separate

---

## Limitations

- **Slower than others:** Due to deep AST analysis and graceful error handling, Drace may take its time (about 2 seconds longer) on large, nested files
- **Currently Python-only**: But support for other languages might arrive as I learn them (Go will probably be supported soon)
- **Opinionated:** May conflict with pure PEP8 setups

---

## License

Drace is free to use, modify, and distribute. See [LICENSE](LICENSE)

---

## [Contributing](contributing.md)

Have suggestions or want to add new rules?  
Pull requests and ideas welcome — Drace is built to grow.
