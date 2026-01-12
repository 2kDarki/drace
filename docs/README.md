# Drace Documentation

Drace is a pragmatic linter and formatter for Python.  
It focuses on readability, maintainability, and long-term code quality rather than strict stylistic compliance.

Drace does not aim to replace tools like `black` or `flake8`.  
It aims to complement or substitute them when deeper structural feedback is desired.

This documentation explains:
- The philosophy behind Drace
- The Darkian Standards it assumes
- The Z-series rules and what they represent
- How configuration and scoring work
- Known limitations and tradeoffs

## How to read these docs

Recommended order:
1. Philosophy
2. Darkian Standards
3. Z-Series Rules
4. Engine Overview
5. Configuration
6. Scoring

Each Z-rule document explains **what the rule represents and why it exists**, not how it is implemented.
