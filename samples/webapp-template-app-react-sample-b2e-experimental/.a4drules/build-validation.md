# AI Rule: Build Validation

Build validation for successful deployments with minimal friction.

## Targets
- `force-app/main/default/webapplications/*/**/*`
- `**/*.{js,ts,jsx,tsx}`

## MANDATORY: Build Success

**Before completing any coding session** (from the web app directory `force-app/main/default/webapplications/<appName>/`):
```bash
npm run build  # MUST succeed with no errors
```

## Quick Quality Checks
Run from the web app directory (`force-app/main/default/webapplications/<appName>/`):
```bash
npm run lint   # ESLint; fix issues before completing
npm run build  # Runs tsc -b && vite build; catches TypeScript and build issues
```

## Requirements

**Must Pass:**
- `npm run build` completes successfully
- No TypeScript compilation errors
- No critical ESLint errors

**Can Be Warnings:**
- ESLint warnings
- Minor TypeScript warnings

## Fix Commands (when available in the web app's package.json)
```bash
npm run lint         # Run ESLint (always available)
# If your project adds Prettier/format scripts, use those before completing
```

## Workflow

**During Development:**
1. Write code with AI assistance
2. Save frequently (auto-format on save)
3. Check periodically: `npm run lint` (optional)

**Before Completion:**
1. Run `npm run build` from the web app directory
2. If it fails: fix TypeScript/ESLint errors (run `npm run lint`), then retry build

## Error Priority

**Fix Immediately:**
- TypeScript compilation errors
- Import/export errors
- Syntax errors

**Fix When Convenient:**
- ESLint warnings
- Unused variables

## Hard Requirements
- Build must complete without errors
- No broken imports
- Basic TypeScript type safety

## Key Commands (web app directory)
```bash
npm run dev          # Start development server (vite)
npm run build        # TypeScript + Vite build; check deployment readiness
npm run lint         # Run ESLint
```

## Troubleshooting Import Errors
```bash
npm install          # Check missing dependencies
# Verify file exists, case sensitivity, export/import match
```
