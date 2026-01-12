# Philosophy

Drace is inspired by the ideas popularized in *The Pragmatic Programmer*, distilled into actionable signals rather than abstract advice.

The core question Drace tries to answer is:

> Will this code remain understandable and safe to change over time?

Drace assumes that:
- Code is read far more often than it is written
- Structure communicates intent more clearly than comments
- Visual layout affects comprehension speed
- Small design pressures compound into large maintenance costs

## Pragmatism over purity

Drace prioritizes:
- Readability over minimalism
- Explicitness over cleverness
- Structural clarity over stylistic conformity

Rules are designed to **nudge**, not enforce ideology.  
Most warnings indicate *pressure*, not errors.

## The Z-series

Z-series rules are grouped signals that reflect different dimensions of code quality:

- **Z100–Z199**: Structural layout and visual consistency
- **Z200–Z219**: Control flow density and readability
- **Z220–Z239**: Design pressure, coupling, and cohesion
- **Z900+**: Meta and tool-level diagnostics

Each rule exists because the absence of structure eventually becomes a cost.
