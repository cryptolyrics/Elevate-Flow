# Mission Control v2 — UX Research Report

**Client:** Elevate Studios  
**Focus:** Revenue, Execution, Clarity  
**Date:** February 2026  
**Timebox:** 60 minutes

---

## Executive Summary

This report covers UX patterns for mission control dashboards and command centers. The recommendation is a **dark-themed, grid-based dashboard** with:
- Fixed left sidebar navigation
- 4 top-level KPI cards
- Main visualization area (pipeline/charts)
- Slide-out panels for actions
- Command palette (Cmd+K) for power users

---

## 5 Real Examples

### 1. Loft Orbital's Cockpit
**URL:** loftorbital.com

- Modern satellite command interface
- Vertical sidebar with icons + labels
- Floating map toolbar
- Card-based scenario views
- Low-contrast badges showing active item counts

**Screenshot:** ![Loft Orbital](https://uiplanet.ru/wp-content/uploads/2023/01/loft-orbital-mission-control-software-ux-design-1.jpg)

---

### 2. Stripe Dashboard
**URL:** dashboard.stripe.com

- Financial command center, minimalist
- Ample whitespace, prominent KPIs
- Top-level metrics: total volume, new customers, charges
- Intuitive drill-down navigation
- Consistent brand colors and typography

**Screenshot:** ![Stripe](https://images.ctfassets.net/fzn2n1nzq965/1H4B7uWJzY2Y2W2Wu2aW2u/7b8c9d7e9f8a6b5c4d3e2f1a0b9c8d7e/stripe-dashboard.png)

---

### 3. Salesforce Sales Pipeline
**URL:** salesforce.com

- Visual pipeline management
- Color and size to highlight trends
- Role-based views
- AI-driven insights and forecasting
- Interactive, drill-down capabilities

---

### 4. Cavallo Mission Control
**URL:** visualalchemy.net/cavallo-mission-control-dashboard-1

- Order processing command center
- Customizable notification badges
- Profitability metrics (revenue, trends)
- Queue tracking (order status through stages)
- Human performance metrics

**Key insight:** Real-world order/operations dashboards need:
- Notifications: Custom alerts for approvals, new customers, critical metrics
- Profitability: Revenue and profitability trends
- Queue: Order status through processing stages
- Human Performance: Staff metrics for staffing decisions

---

### 5. Asana Project Dashboard
**URL:** asana.com

- Task/project execution
- Drag-and-drop customization
- Color-coded categories
- Real-time sync
- Personalized layouts

---

## Layout Recommendation

```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Logo | Search | Quick Actions | User Profile   │
├────────┬────────────────────────────────────────────────┤
│        │ TOP ROW: 4 KPI Cards                          │
│        │ [Revenue] [Pipeline] [Active] [Tasks Due]      │
│  SIDE  ├────────────────────────────────────────────────┤
│  BAR   │ MIDDLE: Main Visualization                    │
│        │ (Pipeline Funnel / Revenue Chart / Map)       │
│  Nav   │                                                │
│  Icons ├────────────────────────────────────────────────┤
│        │ BOTTOM: Activity Feed / Action Items          │
└────────┴────────────────────────────────────────────────┘
```

### Grid System
- CSS Grid, 12-column
- Draggable/resizable widgets
- Desktop-first (command center, not mobile)

### Responsive Breakpoints
| Breakpoint | Width | Behavior |
|------------|-------|----------|
| Desktop | 1200px+ | Full sidebar + grid |
| Tablet | 768-1199px | Collapsed sidebar (icons only) |
| Mobile | <768px | Bottom nav, stacked cards |

---

## Color Palette

| Role | Hex | Usage |
|------|-----|-------|
| Background | `#0F172A` | Main bg (dark slate) |
| Surface | `#1E293B` | Cards, panels |
| Surface elevated | `#334155` | Hover states |
| Primary | `#3B82F6` | Actions, links (electric blue) |
| Success | `#10B981` | Revenue up, deals won |
| Warning | `#F59E0B` | At-risk, pending |
| Danger | `#EF4444` | Blockers, lost |
| Text primary | `#F8FAFC` | Headings, key values |
| Text muted | `#94A3B8` | Labels, secondary |

**Why dark mode default:**
- Command center vibe
- Reduces eye strain for long sessions
- Modern, premium feel
- Data visualization pops against dark bg

---

## Navigation

### Primary: Fixed Left Sidebar
- **Width:** 64px collapsed, 240px expanded
- **Items:**
  - Dashboard (home)
  - Revenue
  - Pipeline
  - Tasks
  - Team
  - Settings

### Secondary: Top Bar
- Breadcrumbs
- Contextual actions
- Global search

### Tertiary: Command Palette
- **Shortcut:** Cmd+K (or Ctrl+K)
- **Function:** Jump anywhere, search, run actions
- **Style:** Modal overlay, fuzzy search

---

## Mobile Considerations

While this is desktop-first, mobile should be **view-only with alerts**:

| Feature | Mobile |
|---------|--------|
| KPI cards | Stacked, scrollable |
| Charts | Simplified, touch-friendly |
| Navigation | Bottom tab bar |
| Actions | Limited to critical (alerts, approvals) |
| Notifications | Push + in-app |

**Recommendation:** Build responsive, but don't optimize heavily for mobile. This is an operations dashboard, not a consumer app.

---

## Key Principles

1. **Pulse First:** Top row always shows "How are we executing today?"
2. **Drill-Don't-Navigate:** Slide-out panels keep context
3. **Customizable:** Users arrange widgets to their priority
4. **Real-Time:** Activity feed and live data (no manual refresh)
5. **Dark Default:** Professional, command center aesthetic

---

## Tech Stack Recommendation

| Layer | Tool |
|-------|------|
| Framework | React (Next.js) or Vue 3 |
| Styling | Tailwind CSS |
| Charts | Recharts or Tremor |
| Icons | Lucide or Heroicons |
| Fonts | Inter (UI), JetBrains Mono (numbers) |
| State | Zustand or TanStack Query |
| Grid | react-grid-layout |

---

## Next Steps

1. [ ] Wireframe key screens (Dashboard, Revenue, Pipeline)
2. [ ] Build component library (KPIs, cards, charts)
3. [ ] User test with 5+ Elevate team members
4. [ ] Iterate on layout based on feedback
5. [ ] Implement command palette

---

*End of Report*
