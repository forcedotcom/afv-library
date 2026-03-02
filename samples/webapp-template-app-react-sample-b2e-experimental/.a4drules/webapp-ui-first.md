---
description: A4D rule — build UI first, then business logic for web apps
alwaysApply: true
---

# A4D Rule: UI First, Then Business Logic (Proceed Immediately After UI)

When building or modifying a web application (or any feature within it):

1. **Build the UI first**
   - Implement layout, structure, and components (pages, forms, lists, navigation).
   - Apply styling, theming, and design-system usage so the interface is visually complete and navigable.
   - Use placeholder or mock data only where needed to render the UI; do not wire real APIs yet.

2. **Proceed to API and business logic immediately after UI completion (same iteration)**
   - As soon as the UI for a feature is visually complete and routable, begin wiring the data layer for that same feature in the same iteration.
   - Add data fetching (GraphQL preferred per LDS rules, then UI API; avoid Apex REST for React), state management, and event handlers.
   - Connect forms and actions to real APIs and backend behavior.
   - Add validation, loading, and user-friendly error states.
   - Keep the build green; fix TypeScript and ESLint issues as you wire logic.

3. **Quality gates before marking the feature complete**
   - Run `npm run lint` and ensure 0 errors (warnings acceptable if minor).
   - Run `npm run build` and ensure it passes.
   - Replace any remaining mock data relevant to the feature with real data paths or clearly marked TODOs if blocked.

**Rationale:** A visible, stable UI gives a clear target, and immediately wiring the API and business logic in the same iteration ensures end‑to‑end functionality and avoids stale mock UIs. This also aligns with design-system guidance (invoke **webapplications-design-system**) and LDS data access rules.

Notes:
- Within LDS, prefer GraphQL for complex reads and mutations; fall back to standard UI API adapters when appropriate.
- For React apps, do not implement or call Apex REST. If server-side logic is truly required and cannot be achieved via GraphQL/UI API, surface a limitation explicitly.
- If a feature's UI spans multiple pages, wire business logic page-by-page as each page's UI stabilizes, rather than deferring all logic to the end.
