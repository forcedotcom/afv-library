# MUST FOLLOW

0. **Always invoke the `local-expert` MCP** when dealing with web applications: call **`get_expert_knowledge`** with topic **`webapplications-design-system`** (for UI/design), and with **`webapplications`** when generating or structuring the app. Do not skip the design-system expert for any web app UI work.
1. **No `node -e`.** This project forbids `node -e` for any operation (file edits, config, shell automation). Use `replace_in_file` or `write_to_file` only. See **webapp-no-node-e.md**.

# React Development & Stability Rules

## Terminal & Execution Strategy
- **NEVER use `node -e`** for file manipulation, string replacement, or reading files. Forbidden. Use `replace_in_file` or `write_to_file` only. 
- ALWAYS use `replace_in_file` or `write_to_file` for code changes.
- IF you must parse JSON (like package.json), use `jq` if available. Otherwise, read the file and process it internally.
- ALWAYS use `npm` or `yarn` commands directly rather than writing custom Node scripts to trigger them.

## React & TypeScript Standards
- Component Architecture: Prefer functional components with hooks.
- File Naming: Use PascalCase for components (e.g., `Button.tsx`) and camelCase for hooks (e.g., `useAuth.ts`).
- Imports: Use absolute paths (e.g., `@/components/...`) if the `tsconfig.json` or `vite.config.ts` supports it.
- State: Default to `useState` for local state; avoid adding global state libraries unless requested.

## Reliability Protocol
- Before running any build or test command, check for the existence of `node_modules`. If missing, prompt to run `npm install`.
- When searching for code, use `search_files` with regex rather than trying to `grep` or `awk` through the terminal.
- If a command fails twice, STOP and report the exact error to the user rather than attempting a third "creative" bash one-liner.

# General app generation guidance

Your goal is to create a functioning app on Salesforce platform. Do not mock UIs, but use tools at your disposal, such as custom objects, graphql API, Apex controllers in order to achieve your goal.

**Home page must be populated:** The home page (root route) must never be left as the default template. Always populate it with real content—e.g. landing content, banners, tiles, hero, navigation to main features—tailored to the app or use case. Make it visually pleasing and purposeful. Do not leave placeholder or "Welcome to..." default content.

**Replace default boilerplate:** Always replace default scaffold content (e.g. "React App", "Vite + React", default page titles, placeholder headings in index.html or App.tsx) with **project- or app-specific** names and copy. Do not leave generic "React App" or template placeholders in the UI or document title.

**Navigation menu and placeholder name/design (critical — often missed):** **Build the navigation into the app layout** (`appLayout.tsx`) so every page shares the same nav. Always edit the **navigation menu** in that layout file: replace default nav items and labels with app-specific links and names; do not leave template "Home"/"About" or placeholder links. Always replace the **placeholder app name** in header, nav brand, footer, and `<title>` with the actual app name, and update **placeholder design** (header/footer/shell) so it's not the template default. See **webapp-nav-and-placeholders.md**.

**Frontend aesthetics (avoid AI slop):** Make creative, distinctive frontends that surprise and delight. Use distinctive typography (avoid Inter, Roboto, Arial, Space Grotesk as defaults), cohesive color with sharp accents (use CSS variables; avoid purple-on-white clichés), high-impact motion (e.g. staggered reveals), and atmosphere/depth in backgrounds. Do not converge on generic, cookie-cutter layouts. Follow **webapplications-design-system** expert knowledge for full guidance.

# SFDX React Web Application Creation

When the user asks to **create a React app** (or a web app, webpplication, etc) in this SFDX project:

1. **Generate the app** using the Salesforce CLI:
   \`\`\`bash
   sf webapp generate -n MyWebApp -t reactbasic
   \`\`\`
   Use the app name the user requested instead of \`MyWebApp\` if they specify one.

Do not use \`create-react-app\`, Vite, or other generic React scaffolds for this scenario; use \`sf webapp generate\` so the app is SFDX-aware.

2. **For B2B/B2C or authenticated/guest apps:** Also create site container metadata and create and configure Digital Experience Sites to host the React web application.

When modifying webapp in an SFDX project, use the experts MCP to obtain the latest guidance and design before starting implementation. Never assume or create tools that are not explicitly available

3. Repeat iterations until the there are no pending actions left.


# Software development cycle (modified for continuous execution)

- Execute tasks continuously until all planned items are complete in the current iteration, without pausing after intermediate checkpoints.
- Maintain a running checklist and proceed through it sequentially.
- Quality gates (lint/build) remain required, but failures should be remediated inline and the workflow should continue through all feature tasks in this iteration unless the user directs otherwise.

## Attempt Completion Enforcement (Local Project Rule)

- Do NOT invoke attempt_completion until ALL checklist items for the current iteration are complete and quality gates pass.
- Intermediate status updates must use task_progress on tool calls (never attempt_completion) until completion criteria are met.
- The only exceptions that allow early attempt_completion are:
  - A blocking error that cannot be resolved after reasonable remediation and requires user input
  - The user explicitly instructs to pause or complete early

## Stop Conditions

Only stop when:
- All checklist items are completed and quality gates pass, or
- A blocking error cannot be resolved after reasonable remediation, or
- The user explicitly asks to pause.
