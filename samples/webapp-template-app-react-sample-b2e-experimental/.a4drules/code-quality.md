# AI Rule: Code Quality Standards

Enforces ESLint, Prettier, and coding best practices for consistent, maintainable code.

**Execution rule:** Do not use `node -e` for any file or config edits. Use `replace_in_file` or `write_to_file` only (see **webapp-no-node-e.md**).

## Targets
- `force-app/main/default/webapplications/*/**/*`
- `**/*.{js,ts,jsx,tsx,json,md}`

## MANDATORY Checks

**Before completing code** (run from the web app directory `force-app/main/default/webapplications/<appName>/`):
```bash
npm run lint   # MUST result in: 0 errors (0 warnings preferred)
npm run build  # MUST succeed (includes TypeScript check)
```

If your project adds Prettier, use a consistent config (e.g. `.prettierrc` with `semi`, `singleQuote`, `printWidth`, etc.) and run format checks before completing.

## Lint / Fix

```bash
npm run lint   # Run ESLint (always available in the template web app)
# Use your editor's format-on-save or add npm scripts for Prettier if desired
```

## Import Order (MANDATORY)
```typescript
// 1. React ecosystem
import { useState, useEffect } from 'react';

// 2. External libraries (alphabetical)
import clsx from 'clsx';

// 3. UI components (alphabetical)
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// 4. Internal utilities (alphabetical)
import { useAuth } from '../hooks/useAuth';
import { formatDate } from '../utils/dateUtils';

// 5. Relative imports
import { ComponentA } from './ComponentA';

// 6. Type imports (separate, at end)
import type { User, ApiResponse } from '../types';
```

## Naming Conventions
```typescript
// PascalCase: Components, classes
const UserProfile = () => {};
const ApiClient = class {};

// camelCase: Variables, functions, properties
const userName = 'john';
const fetchUserData = async () => {};

// SCREAMING_SNAKE_CASE: Constants
const API_BASE_URL = 'https://api.example.com';

// kebab-case: Files
// user-profile.tsx, api-client.ts
```

## React Component Structure
```typescript
interface ComponentProps {
  // Props interface first
}

const Component: React.FC<ComponentProps> = ({ prop1, prop2 }) => {
  // 1. Hooks
  // 2. Computed values
  // 3. Event handlers
  // 4. JSX return

  return <div />;
};

export default Component;
```

## JSX Standards
```typescript
// Self-closing tags
<Button onClick={handleClick} />

// Conditional rendering
{isLoading && <Spinner />}
{error ? <ErrorMessage error={error} /> : <Content />}

// Lists with keys
{items.map(item => <Item key={item.id} data={item} />)}
```

## Error Handling
```typescript
// Async functions with try-catch
const fetchData = async (id: string): Promise<Data> => {
  try {
    const response = await api.get(`/data/${id}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch data:', error);
    throw error;
  }
};
```

## Anti-Patterns (FORBIDDEN)
```typescript
// NEVER disable ESLint without justification
// eslint-disable-next-line

// NEVER mutate state directly
state.items.push(newItem); // Wrong
setItems(prev => [...prev, newItem]); // Correct

// NEVER use magic numbers/strings
setTimeout(() => {}, 5000); // Wrong
const DEBOUNCE_DELAY = 5000; // Correct
```

## Quality Workflow

**Before Committing:**
1. `npm run lint` - 0 errors (and 0 warnings when possible)
2. `npm run build` - Build must succeed (TypeScript + Vite)

## Zero Tolerance Policy
- ESLint errors: MUST be 0
- ESLint warnings: MUST be 0 (fix when convenient)
- TypeScript errors: MUST be 0 (enforced by `npm run build`)
