---
description: A4D rule — call expert MCP (webapplications + webapplications-design-system) before sf webapp generate
alwaysApply: true
---

# A4D Rule: Before `sf webapp generate`

Before running **`sf webapp generate`**, you **must**:

1. **Call the expert MCP** (`get_expert_knowledge`) with topic **`webapplications-design-system`** — always invoke this expert for UI/design direction.
2. **Call the expert MCP** with topic **`webapplications`** to get generation and structure guidance.
3. Follow the instructions from the MCP responses.
4. Only after that, run `sf webapp generate` (e.g. `sf webapp generate -n <AppName> -t <template>`).

**Webapp name (`-n` / `<AppName>`):** Must be **alphanumerical only**—no spaces, hyphens, underscores, or other special characters. Use only letters (A–Z, a–z) and digits (0–9). If the desired name has spaces or special characters, use a single alphanumeric word (e.g. `CoffeeBoutique` instead of `Coffee Boutique` or `coffee-boutique`).

Do not run `sf webapp generate` without having invoked the expert MCP with **`webapplications-design-system`** and **`webapplications`** first.

When modifying an existing web app (UI, layout, or new features), **always** call `get_expert_knowledge` with topic **`webapplications-design-system`** before making UI or design changes.

**After generating (or when touching a new app):** Replace all default boilerplate content (e.g. "React App", "Vite + React", default document title in `index.html`, placeholder text in the shell) with the actual app name or user-facing copy. Do not leave generic template text in the UI or `<title>`.

**Home page content:** Populate the home page (root route) with real, app-specific content (e.g. landing section, banners, tiles, hero, links to features). Never leave the home page as the default template or placeholder.

**Navigation menu and placeholder name/design:** After generating or when delivering a web app, **you must** (1) **Edit the navigation menu** in `appLayout.tsx`: replace every default nav item and label with app-specific routes and names; do not leave template "Home"/"About" or placeholder links. (2) **Replace the placeholder app name** in the header, nav brand, footer, and `index.html` `<title>` with the actual app name. (3) **Update placeholder design** in the shell (header/footer/branding) so it is not the template default. See **webapp-nav-and-placeholders.md**. Agents often skip this—do not.

Prioritize webapplications generation first, and then generate the metadata.
