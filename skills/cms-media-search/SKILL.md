---
name: cms-media-search
description: REQUIRED first step for ALL image and media requests. Activate IMMEDIATELY when the user asks to find, search, get, fetch, retrieve, browse, look up, use, add, insert, or need any image, photo, picture, media, visual, graphic, icon, illustration, hero image, banner, thumbnail, logo, background image, cover image, feature image, stock photo, or visual asset. This skill discovers which search sources (Salesforce CMS, Data Cloud, Unsplash) are available by checking MCP tool presence, presents only available options to the user, and delegates to the correct search skill. NEVER call search_media_cms_channels, search_content_in_d360, search_electronic_media, or any image search tool directly — always route through this skill first.
license: Apache-2.0
metadata:
  author: afv-library
  version: "3.0"
---

# CMS Media Search — Source Selection

**MANDATORY ENTRY POINT for every media and image search.** Do not assume a source. Do not call any search tool directly. Discover what is available, present only those options, and delegate to the matching search skill.

## When to Use This Skill

Activate **immediately** — before any other response — whenever the user's request involves any visual content:

- Images, photos, pictures, media, visuals, graphics
- Icons, illustrations, banners, thumbnails, logos
- Hero images, background images, feature images, cover images
- Any asset described as visual (e.g. "something for the carousel", "a picture for the header")

Example triggers:

- "Find a modern luxury apartment exterior and use it in the hero section"
- "I need a hero image for the landing page"
- "Search for family lifestyle photos for the carousel"
- "Get me a logo for the about page"
- "Look up some banner graphics"
- "Can you find product images?"
- "Add an image to the header component"
- "I need some stock photos for the homepage"

---

## Step 1: Discover Available Sources via MCP Tool Presence

**Before presenting any options**, determine which search tools are available by checking the MCP tools accessible in your current environment. Do NOT skip this step. Do NOT assume any tool is available.

Check for these specific MCP tools:

| MCP Tool to look for | If present | Source option to show |
|---|---|---|
| `search_media_cms_channels` | ✅ Available | **CMS Image Search (Salesforce CMS)** |
| `search_content_in_d360` OR `search_electronic_media` | ✅ Available | **Data Cloud – AI Hybrid Search (Salesforce CMS + 3rd-party DAMs)** |
| Any tool from an Unsplash MCP server | ✅ Available | **Unsplash** |
| _(always)_ | — | **Other** (user provides URL or asset path) |

### How to check

1. List the MCP servers and tools available in your environment (e.g. browse MCP tool descriptors, or check configured MCP servers).
2. Match tool names against the table above.
3. A source is available **only** if its corresponding MCP tool is confirmed accessible.

### Rules

- **NEVER present a source unless its MCP tool is confirmed available.**
- If **no search tools are found** → present only **Other** and tell the user no automated media sources are currently configured.

## Step 2: Present Source Options

Build the options list dynamically. Include **only** sources whose MCP tool is available, plus **Other**. Number them sequentially. **Wait for the user to choose before doing anything else.**

**All sources available:**

> I can help you find that. Where would you like to search?
> 1. **Data Cloud – AI Hybrid Search (Salesforce CMS + 3rd-party DAMs)** — Semantic search through D360
> 2. **CMS Image Search (Salesforce CMS)** — Search images by keywords and taxonomies
> 3. **Unsplash** — Stock images from Unsplash
> 4. **Other** (please specify)

**Only CMS + D360 available:**

> I can help you find that image. Where would you like to search?
> 1. **Data Cloud – AI Hybrid Search (Salesforce CMS + 3rd-party DAMs)**
> 2. **CMS Image Search (Salesforce CMS)**
> 3. **Other** (please specify)

**No sources available:**

> No automated media sources are currently configured. You can provide a direct URL or asset library path.
> 1. **Other** (please specify)

## Step 3: Delegate Based on User Selection

Only after the user selects an option, follow the matching action by **source name** (not number — numbers change based on availability):

| User selects | Action |
|---|---|
| **CMS Image Search** | Read and follow `../cms-keyword-search/SKILL.md` |
| **Data Cloud – AI Hybrid Search** | Read and follow `../cms-d360-search/SKILL.md` |
| **Unsplash** | Invoke the Unsplash MCP tool directly (see below) |
| **Other** | Ask the user for the source URL or asset library details |

### Unsplash: Direct MCP Tool Invocation

When the user selects **Unsplash**, do not load a separate skill. Call the Unsplash MCP tool directly:

1. **Build the query** from the user's request (e.g. "modern apartment exterior", "family lifestyle"). Use simple, descriptive keywords.
2. **Invoke the Unsplash MCP tool** exposed by the Unsplash MCP server. Pass the search intent as the query parameter; use the tool's schema for exact parameter names and optional fields (e.g. `per_page`, `orientation`).
3. **Present results** with preview thumbnails, photographer credit where available, and a note that Unsplash images are free to use under the [Unsplash License](https://unsplash.com/license). Let the user choose which image to use before placing it.

## Step 4: Handle Errors

If any MCP tool call fails (server error, token expired, connection refused):

- **Do not silently fail.** Tell the user the search tool is currently unavailable and suggest checking MCP server status.
- Offer to retry, or fall back to **Other** (provide a direct URL or asset library path).
- Do **not** present empty results as if the search succeeded.

## Step 5: Present Results

After the delegated skill returns results:

- Display returned assets with preview thumbnails when available.
- Include asset title, source system, and relevance score or tags.
- Let the user confirm which asset to use before inserting it into the page or component.
- Do **not** automatically use the first result — user selection is required.

---

## Prohibitions

- ❌ Do NOT skip source discovery — never assume a source is available
- ❌ Do NOT present source options without confirming MCP tool availability first
- ❌ Do NOT call `search_media_cms_channels`, `search_content_in_d360`, `search_electronic_media`, or any search tool directly — always go through this skill's source selection flow first
- ❌ Do NOT auto-select a source — always let the user choose
- ❌ Do NOT bypass this skill by loading `cms-keyword-search` or `cms-d360-search` directly for an initial image request
