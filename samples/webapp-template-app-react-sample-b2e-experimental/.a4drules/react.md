# AI Customization Rule: React Web App (SFDX)

This rule consolidates React web application guidelines, data access rules, security standards, anti-patterns, and project integration requirements for consistent AI-generated code.

## Targets (File Pattern Matching)

Apply these rules to the React web app files under the SFDX package directory:

- `force-app/main/default/webapplications/*/**/*.js`
- `force-app/main/default/webapplications/*/**/*.jsx`
- `force-app/main/default/webapplications/*/**/*.ts`
- `force-app/main/default/webapplications/*/**/*.tsx`

## Rule Objectives

- Enforce secure, performant, and maintainable patterns for Salesforce data access.
- Standardize UI with shadcn/ui and Tailwind.
- Prevent prohibited patterns that break React or Salesforce constraints.

## UI / layout edits (MANDATORY — read before any UI change)

**When the user asks for UI changes** (new components, pages, navigation, header, footer, sidebar, theme, or “layout”):  
**You MUST open and update `src/appLayout.tsx`** (the theme layout) whenever the change affects how the app shell looks or behaves.  
Do not only edit pages or components and leave `appLayout.tsx` unchanged.  
If in doubt, **edit appLayout.tsx as well**.  
The layout file is: `force-app/main/default/webapplications/<appName>/src/appLayout.tsx` (or the app’s `appLayout.tsx` used by `routes.tsx`).

**Navigation menu and placeholder name/design:** In `appLayout.tsx`, always replace the **default navigation menu** (items and labels) with app-specific links and names, and replace the **placeholder app name** (header, nav brand, footer) and **placeholder design** with the actual app name and intentional styling. Do not leave template nav or "React App"–style branding. See **webapp-nav-and-placeholders.md**.

## Project & Entry Points

- React web app root: `force-app/main/default/webapplications/<appName>/`
- Main entry component: `force-app/main/default/webapplications/<appName>/src/App.tsx`
- **Theme/layout shell**: `force-app/main/default/webapplications/<appName>/src/appLayout.tsx` — wraps all routed content (navigation, header, sidebar, outlet). Routes use `<AppLayout />` as the layout element; page content renders inside it via `<Outlet />`. When making UI edits that affect global layout, navigation, header, footer, sidebar, or theme, **you must consider and edit appLayout.tsx** in addition to page or component files; do not only edit individual pages and omit the layout.
- Running Development Server (from the web app directory):
  - `npm run dev` — starts the Vite dev server
  - You can generally assume the dev server is already running and don't need to start it.
- Build (from the web app directory):
  - `npm run build` — TypeScript check + Vite build
- Deploy and open in Salesforce are done from the **SFDX project root** (e.g. via Salesforce CLI or the IDE), not via the web app's package.json. Keep the app buildable so deploy workflows continue to work.

## Component Library (MANDATORY)

- Use shadcn/ui for UI components (Buttons, Cards, Inputs, Dialogs, etc.).
- Import patterns:

```javascript
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
```

## Styling Standards

- Use Tailwind CSS utility classes.
- Follow consistent spacing, color, and typography conventions.

## React & TypeScript Standards

- Component Architecture: Prefer functional components with hooks.
- File Naming: Use PascalCase for components (e.g., `Button.tsx`) and camelCase for hooks (e.g., `useAuth.ts`).
- Imports: Use absolute paths (e.g., `@/components/...`) if the `tsconfig.json` or `vite.config.ts` supports it.
- State: Default to `useState` for local state; avoid adding global state libraries unless requested.

## Layout and theme (appLayout.tsx) — CRITICAL for UI edits

- **appLayout.tsx** is the application shell: it wraps every page and typically contains the main navigation (e.g. `NavigationMenu`), header, sidebar, and `<Outlet />` for child routes. It defines the global look and structure of the app.
- **MANDATORY:** When asked to change the UI in ways that affect the **overall layout**, **navigation**, **header**, **footer**, **sidebar**, or **theme** (e.g. add a top bar, change nav items, add a sidebar, apply a theme wrapper), you **MUST** edit `appLayout.tsx` (or the app’s layout file) as part of the same change. Do not only edit individual pages or components and leave the layout unchanged.
- **Before finishing any UI edit:** Ask yourself: “Does this touch layout, nav, header, footer, sidebar, or theme?” If yes, **you must have modified appLayout.tsx** (or the layout file used by routes). If you did not, add that edit before considering the task done.
- If the project uses feature inheritance (e.g. `__inherit__appLayout`), the editable layout may live in the app or feature at `src/appLayout.tsx`; ensure you modify the correct file that is actually used by `routes.tsx`.

## Module & Platform Restrictions

- React apps must NOT import or rely on Salesforce platform modules; do not use:
  - `@salesforce/*`
  - `lightning/*`
  - `@wire` (LWC-only)
- Use standard web APIs and npm packages only.

## LWC MCP Server Integration (Data Access Guidance)

The LWC MCP server (via Agentforce Vibes extension) provides framework-agnostic data access guidance for UI API and GraphQL patterns.

### Primary Tool: `orchestrate_lds_data_requirements`

The `orchestrate_lds_data_requirements` tool analyzes data requirements and routes to appropriate guidance tools (UI API or GraphQL). **Note:** Tool names may change, but the purpose remains orchestrating LDS data requirements.

**Important for React Applications:** If the MCP tool recommends Apex REST, React applications should ignore this recommendation. Apex REST is not available in React applications. Follow the [Apex REST Strategy](#data-access-priority-order) section above to evaluate whether GraphQL can handle the requirement, or inform the user that the feature is not currently supported in React.

### Tool Availability Check (MANDATORY)

Before implementing data access, **MUST** verify `orchestrate_lds_data_requirements` is available. If unavailable:

1. Notify user: "LWC MCP data access tools not enabled. Add 'lwc-experts' to --toolsets in a4d_mcp_settings.json"
2. Offer to update the file if you have write access
3. Otherwise, provide manual instructions

**Configuration:** Add `"lwc-experts"` to `--toolsets` in `a4d_mcp_settings.json` (typically at `{VSCode/Cursor globalStorage}/salesforce.salesforcedx-einstein-gpt/settings/a4d_mcp_settings.json`). Example: `"metadata,lwc-experts"` in the args array.

### LWC MCP Server Tool Usage Restrictions (CRITICAL)

**This rule applies when building React applications. Do NOT create LWC components or use LWC-specific development tools.**

**Allowed MCP Tools (Data Access Only):**

- `orchestrate_lds_data_requirements` - Primary tool for data access guidance
- Any data access guidance tools referenced by `orchestrate_lds_data_requirements` (e.g., UI API or GraphQL guidance tools)

**Note:** If the MCP tool recommends Apex REST guidance tools, React applications should ignore these recommendations as Apex REST is not available in React.

**Prohibited MCP Tools (LWC Component Development):**

- `guide_lwc_development` - LWC component development guidance
- `orchestrate_lwc_component_creation` - LWC component creation orchestration
- `create_lwc_component_from_prd` - LWC component creation from PRD
- Any other LWC component creation, development, or framework-specific tools

**Enforcement:**

- **NEVER** call LWC component creation or development tools from the LWC MCP server
- **ONLY** use data access related tools that provide framework-agnostic guidance
- If you encounter a request to create LWC components, remind the user that you are building a React app and redirect them to use React patterns instead

## Data Access Rules (CRITICAL)

- MANDATORY: Use the DataSDK (`getDataSDK()` from `@salesforce/sdk-data`) for all API calls from React. The SDK handles authentication and CSRF token management. Do NOT use `axios` or raw `fetch` for Salesforce API calls.

### Data Access Workflow (MANDATORY)

**Before implementing any data access functionality:**

1. **Proactively check** for LWC MCP server tool availability (see [LWC MCP Server Integration](#lwc-mcp-server-integration-data-access-guidance) section above)
2. **Use the LWC MCP server's `orchestrate_lds_data_requirements` tool** to get guidance on the appropriate data access pattern
3. The MCP tool will analyze your requirements and guide you to the appropriate Salesforce data access pattern (GraphQL or UI API)
4. **Follow the MCP tool's recommendations** when implementing data access code, prioritizing GraphQL for all operations
5. **If the tool recommends Apex REST**, ignore this recommendation and follow the [Apex REST Strategy](#data-access-priority-order) to evaluate if GraphQL can handle the requirement

**Note:** The code examples below serve as reference patterns, but your implementation should be informed by the MCP tool's guidance, which provides the most up-to-date best practices and framework-agnostic patterns.

### Data Access Priority Order

The LWC MCP server's `orchestrate_lds_data_requirements` tool follows this priority order when recommending data access patterns:

1. **GraphQL** (queries & mutations) - Preferred for all data operations including reads, writes, complex queries, relationships, and multi-entity operations
2. **Salesforce UI API** - For standard CRUD operations when GraphQL is not suitable

**Apex REST Strategy (CRITICAL):**

- **Apex REST is NOT available in React applications.** If the MCP tool recommends Apex REST, or if you believe Apex is needed:
  1. **Reflect** on why Apex seems necessary
  2. **Evaluate** whether GraphQL queries or mutations can accomplish the task
  3. **If GraphQL cannot handle the requirement**, inform the user that the feature is not currently supported in React applications
  4. **Do NOT** implement Apex REST endpoints or attempt to call them from React

**Note:** For AI/generative features, see the [Einstein LLM Gateway](#einstein-llm-gateway-aigenerative-features) section below.

### Reference Code Examples

The following code examples serve as reference patterns for React applications. **Always consult the LWC MCP server's `orchestrate_lds_data_requirements` tool first** to ensure you're using the most appropriate pattern and latest best practices for your specific use case.

GraphQL query example:

```typescript
import { getDataSDK, gql } from '@salesforce/sdk-data';

const GET_ACCOUNT = gql`
  query GetAccount($id: ID!) {
    uiapi {
      query {
        Account(where: { Id: { eq: $id } }) {
          edges {
            node {
              Id
              Name {
                value
              }
            }
          }
        }
      }
    }
  }
`;

const data = await getDataSDK();
const response = await data.graphql?.<GetAccountQuery>(GET_ACCOUNT, { id: '001...' });

if (response?.errors?.length) {
  throw new Error(response.errors.map(e => e.message).join('; '));
}

const account = response?.data;
```

GraphQL mutation example:

```typescript
import { getDataSDK, gql } from '@salesforce/sdk-data';

const UPDATE_ACCOUNT = gql`
  mutation UpdateAccount($id: ID!, $name: String!) {
    uiapi {
      AccountUpdate(input: {
        Id: $id
        Account: {
          Name: { value: $name }
        }
      }) {
        Record {
          Id
          Name {
            value
          }
        }
      }
    }
  }
`;

const data = await getDataSDK();
const result = await data.graphql?.<UpdateAccountMutation>(UPDATE_ACCOUNT, {
  id: '001...',
  name: 'New Name',
});

if (result?.errors?.length) {
  throw new Error(result.errors.map(e => e.message).join('; '));
}
```

UI API example (using the SDK's fetch):

```typescript
import { getDataSDK } from '@salesforce/sdk-data';

async function fetchRecord(recordId: string) {
  const data = await getDataSDK();
  const response = await data.fetch!(`/services/data/v62.0/ui-api/records/${recordId}`);

  if (!response.ok) {
    throw new Error(`UI API failed: ${response.status}`);
  }

  return response.json();
}
```

## Einstein LLM Gateway (AI/Generative Features)

Einstein LLM Gateway provides AI and generative capabilities for your React application. Use this service when you want to add features such as:

- Text generation
- Prompt-based AI responses
- LLM-powered content creation
- AI-assisted workflows

### Einstein LLM Gateway Pattern

```typescript
import { getDataSDK } from '@salesforce/sdk-data';

async function callEinsteinGenerations({ prompt, model = 'gpt-4', signal }: {
  prompt: string;
  model?: string;
  signal?: AbortSignal;
}): Promise<string> {
  const url = '/services/data/v62.0/einstein/llm/prompt/generations';
  const sdk = await getDataSDK();
  const resp = await sdk.fetch!(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      additionalConfig: {
        applicationName: 'PromptTemplateGenerationsInvocable',
        model,
      },
      promptTextorId: prompt,
    }),
    signal,
  });

  if (!resp.ok) {
    throw new Error(`Einstein LLM request failed (${resp.status})`);
  }

  const data = await resp.json();
  return data?.generations?.[0]?.text || '';
}
```

## Error Handling Pattern

- Always implement robust try/catch for async operations.
- Provide useful but safe error messages (no sensitive data leakage).

```javascript
async function safeFetch(recordId) {
  try {
    const data = await fetchRecord(recordId);
    return data;
  } catch (err) {
    console.error('Salesforce UI API Error:', err);
    throw err;
  }
}
```

## Anti-Patterns (Do NOT do these)

- **Do NOT make UI/layout/theme/nav changes without updating appLayout.tsx** — If you add or change navigation, header, footer, sidebar, or overall layout, you must also edit the layout shell (`src/appLayout.tsx`). Leaving appLayout.tsx untouched while editing only pages or components is an error.
- **Apex REST is not available in React applications** - Do NOT attempt to use or call Apex REST endpoints from React code
- Unnecessary Apex controllers for simple UI API/GraphQL operations
- Missing error handling for async operations
- Hardcoded Salesforce URLs, IDs, or sensitive data
- Ignoring field-level security and permission checks
- Direct DOM manipulation in React components
- Using LWC-specific patterns (`@wire`, LDS) or `@salesforce/*` modules in React

## Security Standards (CRITICAL)

- Validate user permissions before data operations.
- Respect record sharing rules and field-level security.
- Never hardcode credentials or secrets in client code.
- Sanitize all user inputs.
- Use HTTPS for all API calls.

### Authentication Error Handling (MANDATORY)

- The Data SDK handles 401/403 errors.
- When a 401 (Unauthorized) or 403 (Forbidden) response is received, trigger a page refresh with `window.location.reload()` to redirect to login.

### Notes

- avoid swallowing errors.

Input sanitization example:

```javascript
function sanitizeInput(input) {
  if (typeof input !== 'string') return '';
  return input
    .trim()
    .replace(/<script[^>]*>.*?<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .slice(0, 255);
}
```

## Performance Standards

- Implement client-side caching (e.g., RTK Query or React Query) for API data.
- Use `React.memo`, `useMemo`, and `useCallback` where appropriate.
- Implement proper loading and error states.

## TypeScript Standards

- Prefer TypeScript for React components and utilities.
- Define clear and explicit interfaces for props and API data.

## Testing Requirements

- Use Jest + React Testing Library for UI tests.
- Test loading, success, and error states for data-fetching components.

## Application Generation Rules

- When requested to generate a new application:
  - Replace existing template content; do not append to the starter.
  - Preserve the entry point and routes under `force-app/main/default/webapplications/<appName>/src/`.
  - Keep existing build and deploy commands working.
  - Follow the Data Access and Security standards above.

## Debugging Guidance

- Use React DevTools for component inspection.
- Monitor the browser Network tab for REST/GraphQL calls and auth headers.
- Implement Error Boundaries for unhandled exceptions.

## Quality Checklist (for generated code)

- Entry point maintained (`App.tsx` or `App.js` present and wired in routes/pages).
- **Layout maintained (MANDATORY for UI work):** For any change that affects global layout, nav, header, footer, sidebar, or theme, you **must** have edited `appLayout.tsx`. If you did not open or modify appLayout.tsx, the change is incomplete — go back and update the layout file.
- Uses shadcn/ui and Tailwind for UI.
- Follows Data Access rules with proper auth and error handling.
- Enforces Security standards and input sanitization.
- Includes loading and error states.
- Performance optimizations present where reasonable.
- Tests cover core UI and data interactions.
