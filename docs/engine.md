# Linting Engine Overview

Drace processes files in layered stages:

1. Syntax-tolerant parsing
2. Style and structural checks
3. Semantic analysis
4. Darkian rule evaluation

Failures at one stage do not halt subsequent analysis.

This allows Drace to provide feedback even on incomplete or broken files.
