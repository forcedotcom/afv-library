# UI layout: always update appLayout.tsx (MANDATORY)

**Build navigation into the app layout:** The app layout (e.g. `appLayout.tsx`) must **include** the navigation—header nav, sidebar, or both—so that every routed page is wrapped by the same shell and nav. Do not omit nav from the layout or rely on per-page nav only.

## Targets (File Pattern Matching)

Apply this rule when editing React UI or layout:

- `force-app/main/default/webapplications/*/src/appLayout.tsx`
- `force-app/main/default/webapplications/*/src/**/*.tsx`
- `force-app/main/default/webapplications/*/src/**/*.jsx`

## Rule (CRITICAL)

**When making any UI change** that affects navigation, header, footer, sidebar, theme, or overall layout:

1. **You MUST also edit `src/appLayout.tsx`** (the theme layout used by `routes.tsx`).
2. Do not only edit pages or components and leave `appLayout.tsx` unchanged.
3. Before finishing: confirm you opened and modified `appLayout.tsx` if the change touches layout/nav/theme. If you did not, the task is incomplete — update the layout file.

**Navigation menu and placeholder name/design (often missed):** When editing the layout, **always** update (1) the **navigation menu**—replace default nav items and labels with app-specific links and names; do not leave template "Home"/"About" or placeholder links; (2) the **app name** in header/nav brand/footer and in `index.html` `<title>`—use the actual app name, not the template placeholder; (3) any **placeholder design** in the shell so it matches the app. See **webapp-nav-and-placeholders.md**.

Path: `force-app/main/default/webapplications/<appName>/src/appLayout.tsx` (or the app's layout file that `routes.tsx` imports). (or the app’s layout file that `routes.tsx` imports).
