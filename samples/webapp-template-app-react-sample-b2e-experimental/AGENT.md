# Agent guide: SFDX project with React web app

This project is a **Salesforce DX (SFDX) project** containing a **React web application**. The structure is generated; the app lives under `force-app/main/default/webapplications/<appName>/`. Use this file when working in this directory.

## Project layout

- **Project root**: this directory — SFDX project root. Contains `sfdx-project.json`, `force-app/`, and (optionally) LWC/Aura.
- **React web app**: `force-app/main/default/webapplications/<appName>/`  
  - Replace `<appName>` with the actual app folder name (e.g. `base-react-app`, or the name chosen when the app was generated).
  - Entry: `src/App.tsx`  
  - Routes: `src/routes.tsx`  
  - API/GraphQL: `src/api/` (e.g. `graphql.ts`, `graphql-operations-types.ts`, `utils/`)

Path convention: **webapplications** (lowercase).

## Two package.json contexts

### 1. Project root (this directory)

Used for SFDX metadata (LWC, Aura, etc.). Scripts here are for the base SFDX template:

| Command | Purpose |
|---------|---------|
| `npm run lint` | ESLint for `aura/` and `lwc/` |
| `npm run test` | LWC Jest (passWithNoTests) |
| `npm run prettier` | Format supported metadata files |
| `npm run prettier:verify` | Check Prettier |

Root **does not** run the React app. The root `npm run build` is a no-op for the base SFDX project.

### 2. React web app (where you do most work)

**Always `cd` into the web app directory for dev/build/lint/test:**

```bash
cd force-app/main/default/webapplications/<appName>
```

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | TypeScript (`tsc -b`) + Vite build |
| `npm run lint` | ESLint for the React app |
| `npm run test` | Vitest |
| `npm run preview` | Preview production build |
| `npm run graphql:codegen` | Generate GraphQL types |
| `npm run graphql:schema` | Fetch GraphQL schema |

**Before finishing changes:** run `npm run build` and `npm run lint` from the web app directory; both must succeed.

## Agent rules (.a4drules)

This project includes **.a4drules/** at the project root. Follow them when generating or editing code.

When rules refer to “web app directory” or `force-app/main/default/webapplications/<appName>/`, use the **actual app folder name** for this project.

## Deploying

From **this project root**:

```bash
# Build the React app first (replace <appName> with the app folder name)
cd force-app/main/default/webapplications/<appName> && npm i && npm run build && cd -

# Deploy web app only
sf project deploy start --source-dir force-app/main/default/webapplications --target-org <alias>

# Deploy all metadata
sf project deploy start --source-dir force-app --target-org <alias>
```

## Conventions (quick reference)

- **UI**: shadcn/ui + Tailwind. Import from `@/components/ui/...`.
- **Entry**: Keep `App.tsx` and routes in `src/`; add features as new routes or sections, don’t replace the app shell but you may modify it to match the requested design.
