# AI Rule: TypeScript Standards

Enforces strict TypeScript standards for type-safe React applications.

## Targets
- `**/*.ts`
- `**/*.tsx`

## MANDATORY Configuration
- `strict: true` - Enable all strict type checking
- `noUncheckedIndexedAccess: true` - Prevent unsafe array/object access
- `noUnusedLocals: true` - Report unused variables
- `noUnusedParameters: true` - Report unused parameters

## Function Return Types (REQUIRED)
```typescript
// Always specify return types
function fetchUserData(id: string): Promise<User> {
  return api.get(`/users/${id}`);
}

const calculateTotal = (items: Item[]): number => {
  return items.reduce((sum, item) => sum + item.price, 0);
};
```

## Interface Definitions (REQUIRED)
```typescript
// Data structures
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// React component props
interface ButtonProps {
  variant: 'primary' | 'secondary';
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({ variant, onClick, disabled, children }) => {
  // Implementation
};
```

## Type Safety Rules

### Never Use `any`
```typescript
// FORBIDDEN
const data: any = await fetchData();

// REQUIRED: Proper typing
interface ApiResponse {
  data: User[];
  status: 'success' | 'error';
}
const response: ApiResponse = await fetchData();

// ACCEPTABLE: Unknown when type is truly unknown
const parseJson = (input: string): unknown => JSON.parse(input);
```

### Null Safety
```typescript
// Handle null/undefined explicitly
interface UserProfile {
  user: User | null;
  loading: boolean;
  error: string | null;
}

// Use optional chaining and nullish coalescing
const displayName = user?.name ?? 'Anonymous';
const avatarUrl = user?.profile?.avatar ?? '/default-avatar.png';
```

## React TypeScript Patterns

### Event Handlers
```typescript
const handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
  event.preventDefault();
};

const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
  setInputValue(event.target.value);
};

const handleClick = (event: React.MouseEvent<HTMLButtonElement>): void => {
  console.log('Button clicked');
};
```

### State and Hooks
```typescript
// Type useState properly
const [user, setUser] = useState<User | null>(null);
const [loading, setLoading] = useState<boolean>(false);
const [errors, setErrors] = useState<string[]>([]);

// Type custom hooks
interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useApi<T>(url: string): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  return { data, loading, error, refetch };
}
```

## API Types

### Salesforce Records
```typescript
interface SalesforceRecord {
  Id: string;
  attributes: { type: string; url: string };
}

interface Account extends SalesforceRecord {
  Name: { value: string };
  Industry?: { value: string | null };
}
```

### GraphQL via DataSDK
Use `getDataSDK()` from `@salesforce/sdk-data` for all GraphQL operations. The SDK handles authentication and CSRF token management:

```typescript
import { getDataSDK } from '@salesforce/sdk-data';

const data = await getDataSDK();
const response = await data.graphql?.<GetAccountsQuery>(QUERY, variables);

if (response?.errors?.length) {
  throw new Error(response.errors.map(e => e.message).join('; '));
}

const accounts = response?.data;
```

## Error Handling Types
```typescript
interface ApiError {
  message: string;
  status: number;
  code?: string;
}

class CustomError extends Error {
  constructor(message: string, public readonly status: number, public readonly code?: string) {
    super(message);
    this.name = 'CustomError';
  }
}
```

## Anti-Patterns (FORBIDDEN)

### Type Assertions
```typescript
// FORBIDDEN: Unsafe assertions
const user = data as User;

// REQUIRED: Type guards
function isUser(obj: unknown): obj is User {
  return typeof obj === 'object' && obj !== null && typeof (obj as User).id === 'string';
}

if (isUser(data)) {
  console.log(data.name); // Now safely typed
}
```

### Missing Return Types
```typescript
// FORBIDDEN: No return type
const fetchData = async (id: string) => {
  return await api.get(`/data/${id}`);
};

// REQUIRED: Explicit return type
const fetchData = async (id: string): Promise<ApiResponse> => {
  return await api.get(`/data/${id}`);
};
```

## Quality Checklist
Before completing TypeScript code:
1. All functions have explicit return types
2. All interfaces are properly defined
3. No `any` types used (use `unknown` if necessary)
4. Null/undefined handling is explicit
5. React components are properly typed
6. API calls have proper type definitions
7. `tsc -b` compiles without errors

## Enforcement
- TypeScript errors MUST be fixed before any commit
- NEVER disable TypeScript strict mode
- Code reviews MUST check for proper typing
