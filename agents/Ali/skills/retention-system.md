# Skill: Retention System

## Description
Cohort analysis, churn prediction, engagement scoring, and lifecycle email sequences.

## What This Covers
- Cohort analysis by acquisition date, source, plan, feature usage
- Churn prediction from behavioral signals
- Engagement scoring methodology
- Lifecycle email design

## When to Use
When analyzing retention or building churn prevention systems.

## Key Frameworks

### Cohort Analysis
Group users by:
- Acquisition month
- Acquisition source (paid/organic/referral)
- Plan tier (free/pro/enterprise)
- Key feature adoption (used X feature in first 7 days)

Calculate:
- Retention rate: Users still active at day 30/60/90
- Churn rate: 1 - retention
- Revenue churn: ARR lost from churned customers

### Churn Prediction Signals
Watch for:
- Login frequency decreasing
- Feature usage dropping
- NPS score declining
- Support tickets increasing
- Time in product decreasing

### Engagement Scoring
Score 0-100 based on:
- Login frequency (0-25 pts)
- Feature breadth (0-25 pts)
- Depth of usage (0-25 pts)
- Response to emails (0-25 pts)

### Lifecycle Emails
- Welcome sequence (days 0-7)
- Activation series (days 7-30)
- Engagement series (days 30-60)
- Win-back sequence (day 60+ inactive)
