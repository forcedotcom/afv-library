---
description: A4D rule — always update navigation menu and placeholder name/design; never leave default
alwaysApply: true
---

# Navigation Menu & Placeholder Name/Design (MANDATORY)

Agents consistently miss these. **You must not leave them default.**

**Navigation belongs in the app layout:** Build the navigation **into** the app layout (e.g. `appLayout.tsx`). The layout component must include the nav—header nav, sidebar, or both—so every page is wrapped by the same shell and nav. Do not omit navigation from the layout or put it only on individual pages.

## 1. Navigation menu

- **Always edit the navigation menu** in the layout file (typically `src/appLayout.tsx`). Replace default/placeholder nav items and labels with **app-specific** links and names.
- Do **not** leave template items (e.g. "Home", "About", generic links or placeholder labels). Use real routes and labels that match the app (e.g. "Dashboard", "Products", "Orders" for an e‑commerce app).
- The navigation is part of the app shell; it lives in **appLayout.tsx** (or the file that `routes.tsx` uses as the layout). Open that file and update every nav link and label.

**Check before finishing:** Did I change the nav items and labels in the layout file to match this app? If not, the task is incomplete.

## 2. Placeholder name and design

- **Replace the placeholder app name** everywhere it appears: header, nav brand/logo area, footer, document `<title>`, and any "Welcome to…" or generic title text. Use the **actual app name** (e.g. the name used in `sf webapp generate -n <AppName>` or the user's requested name).
- **Replace placeholder design** in the shell: default header/footer styling, generic logo area, and any template branding must be updated to match the app's aesthetic (or at least use the real app name and intentional styling).

**Check before finishing:** Is the app name and shell design still the template default anywhere? If yes, update it.

## Where to edit

- **Layout/nav/branding:** `force-app/main/default/webapplications/<appName>/src/appLayout.tsx` — the app layout must contain the navigation (build it in here).
- **Document title:** `force-app/main/default/webapplications/<appName>/index.html`
- **Root page content:** The component rendered at the root route (often `Home` or similar in `routes.tsx`)

Completing a web app task includes updating **navigation menu**, **app name in header/nav/footer/title**, and **placeholder design** in the shell—not only the main page content.
