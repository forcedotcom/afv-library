# A4D Rules Index

Rules in this folder guide the agent for this SFDX project. **Knowledge** (expert content) lives in the **local-expert MCP** repo (e.g. `local-expert-mcp`); rules here reference when to call which expert.

## Always-apply rules (MUST follow)

| File | Purpose |
|------|--------|
| **webapp.md** | Main web app rules: invoke local-expert MCP (`webapplications-design-system` + `webapplications`), no `node -e`, React/SFDX workflow; **replace default boilerplate**; **populate home page**; **frontend aesthetics**—avoid AI slop, follow design-system expert. |
| **webapp-no-node-e.md** | No `node -e` for any file/config/shell work; use `replace_in_file` or `write_to_file` only. |
| **a4d-webapp-generate.md** | Before `sf webapp generate`: call `get_expert_knowledge` with `webapplications-design-system` and `webapplications`; then run CLI. |
| **webapp-ui-first.md** | Build UI (layout, components, styling) first; then implement business logic (APIs, state, handlers). |
| **webapp-nav-and-placeholders.md** | **Build navigation into the app layout** (`appLayout.tsx`). Always update nav menu (app-specific items/labels) and placeholder name/design (header/nav/footer/title). Often missed—mandatory. |

## Context-specific rules (by file pattern or topic)

| File | Purpose |
|------|--------|
| **react.md** | React web app structure, shadcn/Tailwind, data access, security; edit `appLayout.tsx` when changing layout. |
| **ui-layout.md** | When changing UI/nav/header/footer/sidebar/theme, always update `appLayout.tsx`. |
| **code-quality.md** | ESLint, Prettier, import order, naming, lint/build before completion; no `node -e`. |
| **build-validation.md** | `npm run build` must succeed from web app dir before completing. |
| **typescript.md** | TypeScript strictness, return types, interfaces. |
| **images.md** | Images: Unsplash default, CSP, alt text, error handling. |
| **react_image_processing.md** | Image handling (Unsplash, CSP, accessibility) for React components. |
| **graphql/** | GraphQL tools and knowledge (schemas, LDS guides). |

## Knowledge repository (experts)

Expert knowledge is served by the **local-expert MCP** (e.g. at `local-expert-mcp`). The agent must call **`get_expert_knowledge`** with the appropriate topic:

- **webapplications-design-system** — Always use for web app UI/design work (design system, typography, color, motion).
- **webapplications** — Use for app generation and structure; then call sub-topics as needed (e.g. `webapplications-best-practice`, `webapplications-feature-*`).

See the MCP repo's **rule-expert-mcp.md** for full topic list and when to call which expert.
