# AI Rule: GraphQL Data Access

Instructs agents to use the established GraphQL utilities for Salesforce data access.

## Targets
- `force-app/main/default/webapplications/<appName>/**/*.ts`
- `force-app/main/default/webapplications/<appName>/**/*.tsx`

## TypeScript Types & Code Generation

### Generated Types File
Types are auto-generated at: `force-app/main/default/webapplications/<appName>/src/api/graphql-operations-types.ts`

### Generation Command
Run from the web app directory (replace `<appName>` with your app folder name, e.g. `base-react-app`):
```bash
cd force-app/main/default/webapplications/<appName> && npm run graphql:codegen
```

The codegen configuration is located at `scripts/graphql/codegen.js` (or the package's codegen config) and generates types from:
- Schema: `schema.graphql` (root level of the web app or as configured)
- Documents: `force-app/main/default/webapplications/<appName>/src/**/*.{graphql,ts,tsx}`

### Type Naming Convention
For a GraphQL operation named `GetHighRevenueAccounts`:
- **Query/Mutation Response Type**: `GetHighRevenueAccountsQuery` or `GetHighRevenueAccountsMutation`
- **Input Variables Type**: `GetHighRevenueAccountsQueryVariables` or `GetHighRevenueAccountsMutationVariables`

## Core Types & Function Signatures

### getDataSDK Function
Available from `@salesforce/sdk-data`:

```typescript
import { getDataSDK } from '@salesforce/sdk-data';

const data = await getDataSDK();
const response = await data.graphql?.<ResponseType, VariablesType>(query, variables);
```

`getDataSDK()` returns a lazily-initialized `DataSDK` singleton. The `graphql` method uses optional chaining (`?.`) because not all surfaces support GraphQL.

### GraphQLResponse Shape
`data.graphql?.()` returns `GraphQLResponse<T>`. Callers destructure `{ data, errors }` and handle errors themselves:

```typescript
interface GraphQLResponse<T> {
  data: T;
  errors?: Array<{
    message: string;
    locations?: Array<{ line: number; column: number }>;
    path?: string[];
  }>;
}
```

### Handling Mixed Responses (Partial Success)

GraphQL can return **both `data` and `errors`** in the same response (partial success). For example, some fields may resolve while others fail due to field-level security. Choose a strategy per use case:

```typescript
// Strategy A: Strict — treat any errors as failure (default for most queries)
if (response?.errors?.length) {
  throw new Error(response.errors.map(e => e.message).join('; '));
}
const result = response?.data;

// Strategy B: Tolerant — log errors but use partial data
if (response?.errors?.length) {
  console.warn('GraphQL partial errors:', response.errors);
}
const result = response?.data;

// Strategy C: Discriminated — fail only when no data came back
if (response?.errors?.length && !response?.data) {
  throw new Error(response.errors.map(e => e.message).join('; '));
}
if (response?.errors?.length) {
  console.warn('Partial success with errors:', response.errors);
}
const result = response?.data;
```

**When to use each:**
- **Strategy A** — Default. Use for queries where incomplete data would be misleading (e.g., financial summaries, approval workflows).
- **Strategy B** — Use when partial data is still useful and the UI can degrade gracefully (e.g., dashboard tiles, optional fields).
- **Strategy C** — Use for mutations where the operation may succeed but some return fields are inaccessible.

For mutation-specific partial responses, see `docs/generate-mutation-query.md` which covers `PARTIAL` and `FAILED` status handling workflows.

### gql Template Tag
Also available from `@salesforce/sdk-data` for inline query definitions:

```typescript
import { gql } from '@salesforce/sdk-data';

const MY_QUERY = gql`
  query MyQuery {
    uiapi {
      ...
    }
  }
`;
```

The `gql` tag is a template literal that allows defining GraphQL queries inline while maintaining syntax highlighting in most editors.

### NodeOfConnection Utility Type
Extract the node type from a connection (edges/node pattern):

```typescript
import { type NodeOfConnection } from '@salesforce/sdk-data';

// Extract Account node type from the query response
type AccountNode = NodeOfConnection<
  GetHighRevenueAccountsQuery['uiapi']['query']['Account']
>;
```

### UIAPI Response Shape
All Salesforce GraphQL queries follow this structure:

```typescript
interface UIAPIQueryResponse {
  uiapi: {
    query: {
      [ObjectName]: {
        edges?: Array<{
          node?: {
            Id: string;
            [FieldName]?: { value?: FieldType | null } | null;
            // Reference fields include the related record
            [ReferenceField]?: {
              value?: string | null;  // The ID
              [RelatedField]?: { value?: RelatedType | null } | null;
            } | null;
          } | null;
        } | null> | null;
      } | null;
    };
  };
}
```

## Required Workflow

There are **two acceptable patterns** for defining GraphQL queries:

### Pattern 1: External .graphql File (Recommended for complex queries)

#### Step 1: Create .graphql File
Store queries in `.graphql` files for codegen to process:

```graphql
# force-app/main/default/webapplications/<appName>/src/api/utils/query/myQuery.graphql
query GetMyData($myVariable: String) {
  uiapi {
    query {
      MyObject(first: 10, where: { Field: { eq: $myVariable } }) {
        edges {
          node {
            Id
            Name { value }
          }
        }
      }
    }
  }
}
```

#### Step 2: Run Code Generation
```bash
cd force-app/main/default/webapplications/<appName> && npm run graphql:codegen
```

This generates types in `graphql-operations-types.ts`:
- `GetMyDataQuery` - response type
- `GetMyDataQueryVariables` - variables type

#### Step 3: Import and Use
```typescript
import { getDataSDK, type NodeOfConnection } from '@salesforce/sdk-data';
import MY_QUERY from './query/myQuery.graphql?raw';
import type {
  GetMyDataQuery,
  GetMyDataQueryVariables,
} from '../graphql-operations-types';

type MyNode = NodeOfConnection<GetMyDataQuery['uiapi']['query']['MyObject']>;

export async function getMyData(
  variables: GetMyDataQueryVariables
): Promise<MyNode[]> {
  const data = await getDataSDK();
  const response = await data.graphql?.<GetMyDataQuery, GetMyDataQueryVariables>(MY_QUERY, variables);

  if (response?.errors?.length) {
    const errorMessages = response.errors.map(e => e.message).join('; ');
    throw new Error(`GraphQL Error: ${errorMessages}`);
  }

  return response?.data?.uiapi?.query?.MyObject?.edges?.map(edge => edge?.node) || [];
}
```

**Key imports for Pattern 1:**
- `getDataSDK` - Get the DataSDK singleton
- `NodeOfConnection` - Extract node types from connection responses
- Query from `.graphql` file with `?raw` suffix
- Generated types from `graphql-operations-types.ts`

**Pattern 1 Benefits:**
- Full codegen support with automatic type generation
- Syntax highlighting and validation in `.graphql` files
- Easier to share queries across multiple files/components
- Better for complex queries with fragments and multiple variables
- IDE support for GraphQL (autocomplete, validation)
- Queries can be tested independently
- Clear separation of concerns between query definition and usage

**Pattern 1 Limitations:**
- Requires separate file management
- Extra step to run codegen after query changes
- More boilerplate (file import with `?raw`, separate file to maintain)
- Slight overhead for very simple queries
- Need to navigate between files during development
- Doesn't support dynamic queries (e.g., the set of fields changes based on runtime conditions and cannot be predetermined)

### Pattern 2: Inline Query with gql Tag (Recommended for simple queries)

For simpler queries without variables or when colocation is preferred:

```typescript
import { getDataSDK, gql } from '@salesforce/sdk-data';
import { type CurrentUserQuery } from '../graphql-operations-types';

const CURRENT_USER_QUERY = gql`
  query CurrentUser {
    uiapi {
      currentUser {
        Id
        Name {
          value
        }
      }
    }
  }
`;

interface User {
    id: string;
    name: string;
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const data = await getDataSDK();
    const response = await data.graphql?.<CurrentUserQuery>(CURRENT_USER_QUERY);

    if (response?.errors?.length) {
      throw new Error(response.errors.map(e => e.message).join('; '));
    }

    const userData = response?.data?.uiapi.currentUser;

    if (!userData) {
      throw new Error('No user data found');
    }

    return {
      id: userData.Id,
      name: userData.Name?.value || 'User',
    };
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
}
```

**Key imports for Pattern 2:**
- `getDataSDK` - Get the DataSDK singleton
- `gql` - Template tag for inline query definition
- Generated types from `graphql-operations-types.ts`

**Pattern 2 Benefits:**
- Query is colocated with usage code
- Supports dynamic queries (e.g., the set of fields changes based on runtime conditions and cannot be predetermined)
- No separate file to maintain
- Still gets type-checked against generated types
- Simpler for straightforward queries

**Pattern 2 Limitations:**
- Inline queries without `gql` template tag are not processed by codegen
- Must manually ensure query name matches generated types
- Less suitable for complex queries with fragments

## Reference Examples

### Pattern 1 Example: accounts.ts
See `force-app/main/default/webapplications/<appName>/src/api/utils/accounts.ts` for Pattern 1:
1. Importing query from `.graphql` file with `?raw` suffix
2. Importing generated types from `graphql-operations-types.ts`
3. Using `NodeOfConnection` to extract node types
4. Proper typing with `data.graphql?.<ResponseType>(query, variables)`
5. Safe data extraction from the nested response

### Pattern 2 Example: user.ts
See `force-app/main/default/webapplications/<appName>/src/api/utils/user.ts` for Pattern 2:
1. Using `gql` template tag for inline query definition
2. Importing generated types from `graphql-operations-types.ts`
3. Simple query without variables
4. Error handling with try/catch
5. Direct access to `uiapi.currentUser` (non-connection response)

## Conditional Field Selection with Directives

For dynamic fieldsets with known fields that should be conditionally included, use GraphQL directives instead of building queries dynamically. This preserves type generation while allowing runtime control.

### Directives
- **`@include(if: $condition)`** - include field/fragment when `$condition` is `true`
- **`@skip(if: $condition)`** - skip field/fragment when `$condition` is `true`

### Example with Fragments
```graphql
# <appName>/src/api/utils/query/getAccountDetails.graphql
query GetAccountDetails(
  $id: ID!
  $includeFinancials: Boolean!
  $includeContacts: Boolean!
) {
  uiapi {
    query {
      Account(where: { Id: { eq: $id } }) {
        edges {
          node {
            Id
            Name { value }
            ...FinancialFields @include(if: $includeFinancials)
            ...ContactFields @include(if: $includeContacts)
          }
        }
      }
    }
  }
}

fragment FinancialFields on Account {
  AnnualRevenue { value }
  NumberOfEmployees { value }
}

fragment ContactFields on Account {
  Phone { value }
  Website { value }
}
```

### Usage
```typescript
import { getDataSDK } from '@salesforce/sdk-data';
import QUERY from './query/getAccountDetails.graphql?raw';
import type {
  GetAccountDetailsQuery,
  GetAccountDetailsQueryVariables,
} from '../graphql-operations-types';

const data = await getDataSDK();
const response = await data.graphql?.<GetAccountDetailsQuery, GetAccountDetailsQueryVariables>(QUERY, {
  id: accountId,
  includeFinancials: userWantsFinancials,
  includeContacts: userWantsContacts,
});
```

### Benefits
- Query stays in `.graphql` file (codegen works)
- Generated types include all possible fields as optional
- Runtime control over which fields are fetched
- Better performance when fields aren't needed
- Type safety is preserved

## Anti-Patterns (Not Recommended)

### Direct API Calls
```typescript
// NOT RECOMMENDED: Direct axios/fetch calls for GraphQL
const response = await axios.post('/graphql', { query });

// PREFERRED: Use the DataSDK
const data = await getDataSDK();
const response = await data.graphql?.<ResponseType>(query, variables);
```

### Missing Type Definitions
```typescript
// NOT RECOMMENDED: Untyped GraphQL calls
const data = await getDataSDK();
await data.graphql?.(query);

// PREFERRED: Provide response type
const data = await getDataSDK();
const response = await data.graphql?.<GetMyDataQuery>(query);
```

### Plain String Queries (Without gql Tag)
```typescript
// NOT RECOMMENDED: Plain string queries without gql tag
const query = `query { ... }`;
const data = await getDataSDK();
await data.graphql?.(query);

// PREFERRED: Use gql tag for inline queries
const QUERY = gql`query { ... }`;
const data = await getDataSDK();
const response = await data.graphql?.<ResponseType>(QUERY);

// OR: Use .graphql file for complex queries
import QUERY from './query/myQuery.graphql?raw';
const data = await getDataSDK();
const response = await data.graphql?.<ResponseType>(QUERY);
```

**Why avoid plain strings:**
- No syntax highlighting or validation
- Harder to maintain and refactor
- More error-prone

## Benefits of the DataSDK GraphQL API
- Uses the DataSDK with proper authentication and CSRF token handling
- Consistent typing with `GraphQLResponse<T>` interface
- Optional chaining (`?.`) safely handles surfaces where GraphQL is unavailable
- Callers get full `GraphQLResponse<T>` for flexible error handling

## Quality Checklist
Before completing GraphQL data access code:

### For Pattern 1 (.graphql files):
1. [ ] Create `.graphql` file for the query/mutation
2. [ ] Run `npm run graphql:codegen` to generate types
3. [ ] Import query with `?raw` suffix
4. [ ] Import generated types from `graphql-operations-types.ts`
5. [ ] Use `data.graphql?.<ResponseType>()` with proper generic
6. [ ] Use `NodeOfConnection` for cleaner node types when needed
7. [ ] Handle optional chaining for nested response data
8. [ ] Follow the pattern in `accounts.ts`

### For Pattern 2 (inline with gql):
1. [ ] Define query using `gql` template tag
2. [ ] Ensure query name matches generated types in `graphql-operations-types.ts`
3. [ ] Import generated types for the query
4. [ ] Use `data.graphql?.<ResponseType>()` with proper generic
5. [ ] Handle `response.errors` and destructure `response.data`
6. [ ] Handle optional chaining for nested response data
7. [ ] Follow the pattern in `user.ts`

### General:
- [ ] Choose Pattern 1 for complex queries with variables, fragments, or when shared
- [ ] Choose Pattern 2 for simple, colocated queries without complex requirements
