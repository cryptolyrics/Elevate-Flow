# Skill: Experiment Engine

## Description
Hypothesis framework, test design, statistical significance, and learning repository.

## What This Covers
- Writing strong hypotheses
- Designing valid experiments
- Determining statistical significance
- Building a learning repository

## When to Use
Whenever running any A/B test or experiment.

## Key Frameworks

### Hypothesis Framework
```
Problem: [What user pain point or business issue?]

Observation: [What data or user insight suggests this?]

Hypothesis: If [specific change], then [primary metric] will improve by [X%] because [clear reasoning].

Prediction: [What will happen if hypothesis is true?]
Risk: [What could go wrong?]
```

### ICE Scoring
Prioritize experiments by:
- **I**mpact: How much revenue/metric could this move?
- **C**onfidence: How sure are you this will work?
- **E**ase: How easy is this to test?

Score each 1-10. Multiply. Sort by total.

### Statistical Significance
```
Significance level: p < 0.05 (95% confidence)
Power: 80% (detecting real effect 80% of the time)

Sample size formula:
n = 16 × σ² / δ²
where σ = standard deviation, δ = minimum detectable effect
```

### Experiment Log
| Date | Hypothesis | Test | Duration | N | Result | p-value | Decision |
|------|-----------|------|----------|---|--------|---------|----------|
|      |           |      |          |   |        |         |          |

### Learning Repository
For each experiment:
- What did we learn?
- What would we do differently?
- What should we test next?
- What should we never do again?
