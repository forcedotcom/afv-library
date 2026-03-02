#Goal

- You are configuring image usage for React applications generated through Vibe Coding. 
- Your goal is to ensure Unsplash is used as the default image source unless the developer provides their own images.

# AI Customization Rule: React Image Processing

Image handling standards for React web apps (SFDX): CSP compliance, accessibility, and proper image sources.

## Targets (File Pattern Matching)

- `force-app/main/default/webapplications/*/**/*.tsx`
- `force-app/main/default/webapplications/*/**/*.ts`
- `force-app/main/default/webapplications/*/**/*.jsx`
- `force-app/main/default/webapplications/*/**/*.js`
- `force-app/main/default/webapplications/*/**/*.html`

## Core Rules

### Default Image Source: Unsplash

Use Unsplash by default (pre-configured in CSP):

```
https://images.unsplash.com/photo-{PHOTO_ID}?w={WIDTH}&h={HEIGHT}&fit=crop&q=80
```

Sample Photo IDs: `1557683316-973673baf926` (tech), `1506905925346-21bda4d32df4` (nature)

### Alternative Sources

If user requests another source (Pexels, custom):

- Use requested source
- Inform user: "Add CSP Trusted Site in Setup → Security → CSP Trusted Sites"

### Accessibility (MANDATORY)

- Always include descriptive `alt` text
- Use `alt=""` for decorative images only

### Avoid (CSP Violations)

- Avoid until requested `placeholder.com`, `picsum.photos`, `via.placeholder.com`  
- Pre-configured: `images.unsplash.com`, `source.unsplash.com`, `images.pexels.com`
