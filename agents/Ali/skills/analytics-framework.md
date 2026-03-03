# Skill: Analytics Framework

## Description
Metric definition, dashboard design, attribution modeling, and measurement infrastructure.

## What This Covers
- Defining metrics that drive revenue
- Dashboard design focused on actionable insights
- Attribution modeling
- Building measurement before running experiments

## When to Use
When setting up analytics or evaluating whether you can measure something.

## Key Frameworks

### Metric Hierarchy
```
Revenue
├── ARPU (Average Revenue Per User)
├── MRR (Monthly Recurring Revenue)
├── Churn Rate
└── LTV (Lifetime Value)
    └── LTV = ARPU × Gross Margin / Churn Rate

Acquisition
├── CAC (Customer Acquisition Cost)
├── CAC Payback Period
└── Organic vs Paid ratio

Activation
├── Time to Value (how fast user gets first win)
├── Activation Rate (% who reach Aha! moment)
└── Onboarding Completion Rate

Engagement
├── DAU/MAU Ratio
├── Feature Adoption Rate
└── NPS Score
```

### Attribution Models
- First-touch: Credit to first interaction
- Last-touch: Credit to final interaction before conversion
- Linear: Equal credit across all touchpoints
- Time-decay: More credit to recent touchpoints
- W-shaped: 35% first, 35% last, 30%中间

### Measurement Before Experiment
Before running ANY experiment:
1. Define primary metric
2. Define secondary metrics
3. Set up tracking
4. Establish baseline
5. Calculate required sample size
6. Set success criteria

If you can't measure it, don't run it.
