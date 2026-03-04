# Growth OS - Ajax Mode

## Owner
**Ali (Ajax mode)** — acquisition + conversion + retention + measurement

## Core Responsibilities
- `/offers` — offer clarity and positioning
- `/experiments` — A/B tests and learnings
- `/clients` — growth tracking for each client
- Measurement infrastructure

---

## Measurement-First Hard Rule

**Never launch spend until this is live:**

1. **UTM Tracking** — Every ad → landing page → conversion tracked
   - `utm_source=facebook`
   - `utm_campaign=sprint_01`
   - `utm_adset={adset_name}`
   - `utm_content={creative_variant}`

2. **Event Tracking** — Every user action captured
   - Page views
   - Form submissions
   - CTA clicks
   - Call bookings

3. **Dashboard** — Real-time view of funnel:
   - Ad impressions → Clicks → Landing views → Form submits → Call bookings

---

## One Funnel Definition

```
FB Ad → Landing Page → Lead Form → Call Booked → Closed Client
```

### Stage Tracking
| Stage | Metric | Target |
|-------|--------|--------|
| Ad Impressions | Reach | - |
| Ad Clicks | CTR | >1% |
| Landing Views | Visit rate | >80% of clicks |
| Form Submits | Lead rate | >5% |
| Call Bookings | Show rate | >50% |
| Closed Clients | Close rate | >30% |

---

## Offer Definition

**Core Offer:** "AI Employees Setup Sprint for SMBs"

| Element | Content |
|---------|---------|
| **Headline** | [Client Name] Gets 1-2 AI Employees Working 24/7 |
| **Subhead** | We set up automation that replaces 10+ hours/week of manual work |
| **CTA** | Book Your Free Strategy Call |
| **Qualification Gate** | Budget: $2k+/mo, Team: 5-50 employees, Urgency: losing to competitors / drowning in work |

### Offer Clarity Rules
- One offer at a time
- Clear outcome: "AI employees" = automation that works while you sleep
- Price anchor: $2k setup + $500/mo
- Risk reversal: "If we don't deliver 10 hours saved in 30 days, money back"

---

## Facebook Ad Structure (MVP)

### Campaign
```
Campaign: AI-Employees-Sprint-[Month]
Objective: Lead Generation
Budget: $20/day (hard cap until 10 conversions)
```

### Ad Sets (3)
| Name | Targeting | Angle |
|------|-----------|-------|
| Pain-Audience | Business owners working 60+ hrs, no time for marketing | "Drowning in work?" |
| Outcome-Audience | Already using tools, want more automation | "What if AI worked 24/7?" |
| Proof-Audience | Visited pricing/service pages | "See what others achieved" |

### Creatives (2 each = 6 total)
- **Video (15s)**: Founder screen-share showing AI in action
- **Image**: Before/after workload comparison

### Kill Rules
- CPC > $15 → Pause ad set
- CTR < 0.5% → Pause creative
- CPL > $50 → Review landing page
- No conversions in 48hrs → Pause campaign

---

## Experiment Protocol

### Required for Every Test
```
Hypothesis: If [change], then [metric] will improve by [X]%
Metric: [Primary metric to track]
Sample Target: [N = required sample size]
Stop Rule: [When to end test]
Owner: [Who runs it]
```

### ICE Scoring
| Factor | Score |
|--------|-------|
| **I**mpact | 1-10 |
| **C**onfidence | 1-10 |
| **E**ase | 1-10 |

Score = I × C × E. Prioritize highest scores.

### Experiment Log
Location: `/experiments`

| Date | Hypothesis | Test | Duration | N | Result | Learning |
|------|-----------|------|----------|---|--------|----------|
|      |           |      |          |   |        |          |

---

## Retention + LTV Loop

### After Client Closes
1. **Onboarding sequence** (days 1-7)
   - Welcome email
   - Setup checklist
   - First success call

2. **Weekly check-in** (weeks 2-4)
   - Review metrics
   - Identify expansion opportunities

3. **30-Day Review**
   - Time saved (retention signal)
   - Expansion potential
   - Referral ask

### LTV Tracking
- Track: Setup fee + Monthly retainer + Expansion revenue
- Cohort by: Acquisition source, offer variant
- Report: LTV by cohort monthly

### Feedback Loop
Retention learnings → Feed back into ad targeting:
- "What worked" → Include in ads
- "What objecetions" → Overcome in copy

---

## Ops Integration

### JJ - Daily
- Morning: 5-point ops check
- Daily: Growth summary (Slack/WhatsApp)
- Routing: Blockers → appropriate owner

### Vlad - Tracking Implementation
- Event tracking in product
- API endpoints for dashboard
- UTM parameter validation
- Real-time funnel dashboard

### Coppa - Compliance
- Review ads before scale
- Compliance check on claims
- Data privacy (GDPR, etc.)

### Ali - Cadence
- **Daily**: 5-point ops check (5 min)
- **Weekly**: Deep funnel review (30 min)
- **Bi-weekly**: Experiment review
- **Monthly**: Cohort report + CAC/LTV analysis

---

## Token-Efficient Cadence

| Frequency | What | Duration |
|-----------|------|----------|
| Daily | 5-point ops check | 5 min |
| Weekly | One canonical growth log | 30 min |
| Monthly | Cohort + CAC/LTV report | 1 hr |
| Quarterly | Strategy review | Half day |

**Rule:** Avoid constant thread churn. One canonical growth log per week. Summarize, don't report every detail in real-time.

---

## Directory Structure

```
/offers/
  └── current-offer.md

/experiments/
  ├── experiment-log.md
  └── learnings-archive.md

/clients/
  └── [client-name]/
      ├── metrics.md
      └── notes.md
```

---

## First 30 Days

| Day | Action |
|-----|--------|
| 1-3 | Set up tracking (UTM, events, dashboard) |
| 4-7 | Build landing page |
| 8-10 | Create FB ad creatives |
| 11 | Launch $20/day |
| 12-14 | Monitor, kill losers |
| 15-21 | Optimize winners |
| 22-30 | First experiment, first learnings |

---

*Last updated: 2026-03-03*
