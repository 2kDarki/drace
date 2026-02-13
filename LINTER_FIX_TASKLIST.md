# Drace Linter Fix Tasklist (Handoff)

## Context Snapshot
- Date: 2026-02-13
- Current status: self-lint works, but several rule categories still produce high noise.
- Latest validated tests: `746 passed, 24 skipped`.
- Self-lint (post Z202 AST-mutation fix):
  - `drace/**/*.py`: 977 findings
  - First-party only (excluding `drace/linter/pyflakes/**`): 718 findings

## Repro Commands
```bash
cd /data/data/com.termux/files/home/GitHub/drace
python -m drace config reset
python -m drace lint drace
python -m drace score drace
pytest -q
```

## Critical Behavior Bug
- [ ] Fix score mode output behavior to be silent except for score.
- Expected: `drace score <path>` should not print per-file lint findings.
- Current repro: `python -m drace score drace/__main__.py` still prints lint details.
- Primary file: `drace/reporters/linting.py`

## Phase 1: Reduce Rule Noise (Highest Priority)

### Z200 (over-reporting one-liner opportunities)
- [ ] Do not flag blocks already written as one-liners.
- [ ] Skip suggestions when compaction gives no readability gain.
- [ ] Avoid flagging `if __name__ == "__main__": ...`.
- Files:
  - `drace/darkian/z2/z200.py`
- Validation:
  - `drace/__main__.py` should not raise `Z200` on line 3.

### Z223 (implicit mutation false positives)
- [ ] Remove duplicate reports from nested traversal.
- [ ] Do not flag legitimate closure/nonlocal patterns as implicit external mutation.
- [ ] Separate true global mutation from local closure assignment behavior.
- Files:
  - `drace/darkian/z2/z223.py`
  - `drace/cli.py` (for regression examples)

### Z226 (temporal coupling false positives)
- [ ] Restrict detection to meaningful suspicious sequences, not routine reassignment.
- [ ] Avoid firing on common accumulator/update patterns.
- [ ] Require stronger signal than simple reassignment proximity.
- Files:
  - `drace/darkian/z2/z226.py`
  - `drace/linter/engine.py` (currently frequently flagged by this rule)

### Z228 (abstraction leak overreach)
- [ ] Only flag when mutable object is internal state exposure risk.
- [ ] Do not flag standard API-return lists/dicts that are intentional/public contract.
- [ ] Tighten to ownership/encapsulation heuristics.
- Files:
  - `drace/darkian/z2/z228.py`
  - `drace/config.py`, `drace/darkian/__init__.py` (example false positives)

## Phase 2: Improve Signal Quality

### Z222 (coupling pressure)
- [ ] Reduce false positives for orchestration functions by distinguishing dependency injection from incidental name use.
- [ ] Consider weighted threshold or explicit exclusions for known framework utility patterns.
- Files:
  - `drace/darkian/z2/z222.py`

### Z227 (hidden dependency)
- [ ] Re-check stdlib constants/sentinels and module-level symbol handling.
- [ ] Keep current improvements (`NamedExpr`, `with as`) and add tests for remaining edge cases.
- Files:
  - `drace/darkian/z2/z227.py`

### Z101 (import ordering)
- [ ] Confirm stable classification across Termux/Linux environments.
- [ ] Ensure no self-reporting loop due to rule-specific ordering expectations.
- Files:
  - `drace/darkian/z1/z101.py`

## Phase 3: Real Codebase Hygiene (Non-rule defects)
- [ ] Remove star imports where practical (`F405`, `E602`):
  - `drace/reporters/linting.py`
  - `drace/utils.py`
- [ ] Fix spacing/whitespace/style issues (`W29x`, `E225`, `E272`, `E302`, `E303`, `W391`).
- [ ] Fix line-length outliers (`E501`) in first-party modules.
- [ ] Resolve `E741` ambiguous name (`I`) in `drace/constants.py`.

## Existing Structural Fix Already Applied
- [x] Z202 no longer mutates shared AST (major source of synthetic-name artifacts like `_V0`).
- File:
  - `drace/darkian/z2/z202.py`

## Test Work Required
- [ ] Add rule-specific regression tests for each noisy category:
  - `Z200`, `Z223`, `Z226`, `Z228`, `Z222`.
- [ ] Add score-mode behavior test:
  - Assert no per-finding output during `score`.
- Suggested test file additions:
  - `tests/test_score_mode.py`
  - `tests/test_rule_noise_reductions.py`

## Acceptance Criteria for “Linter Complete”
- [ ] `drace score <path>` output is score-only.
- [ ] First-party self-lint findings reduced substantially, specifically:
  - `Z200`, `Z223`, `Z226`, `Z228` no longer dominate.
- [ ] No known systemic false-positive class remains.
- [ ] Full suite passes: `pytest -q`.
- [ ] Rule docs remain consistent with implemented behavior.

## Quick Resume Plan (Next Chat)
1. Fix score-mode silent output in `drace/reporters/linting.py`.
2. Implement noise-reduction pass in `Z200`, `Z223`, `Z226`, `Z228`.
3. Add regression tests for those four rules.
4. Re-run self-lint metrics and compare against current baseline (718 first-party findings).
5. Tackle `Z222/Z227/Z101` signal refinements.
6. Finish style/real-defect cleanup.
