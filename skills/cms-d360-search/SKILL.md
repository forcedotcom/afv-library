---
name: cms-d360-search
description: Data Cloud AI Hybrid Search via search_electronic_media or search_content_in_d360 MCP tool. Performs semantic search across Salesforce CMS and 3rd-party DAMs using natural language queries. Invoked from cms-media-search when the user selects Data Cloud – AI Hybrid Search.
license: Apache-2.0
compatibility: Requires content MCP server with search_electronic_media or search_content_in_d360 tool.
metadata:
  author: afv-library
  version: "2.0"
---

# Data Cloud – AI Hybrid Search

Semantic search across Salesforce CMS and connected 3rd-party DAMs. Invoked by `cms-media-search` when the user selects **Data Cloud – AI Hybrid Search**.

Best for natural language queries, cross-system searches, and semantic similarity (vs exact keyword matching).

## Step 1: Build the Query

Use the user's original request **as-is**. No keyword extraction, taxonomy splitting, or translation needed — the tool handles semantic interpretation.

## Step 2: Call the MCP Tool

Call **one** of these tools (try primary first, fall back to legacy):

| Priority | Tool name |
|----------|-----------|
| Primary | `search_content_in_d360` |
| Fallback | `search_electronic_media` |

Input: `query` = the user's search query string. Refer to the tool's schema for additional parameters.

## Step 3: Present Results and Handle Selection

- Present **every** result as a numbered option with title, URL, and source. Never auto-select.
- Wait for the user to choose by number or name.
- After selection: confirm, apply the URL in code, show what changed, offer next steps.

## Errors

On any error (no results, tool unavailable, tool returns error): inform the user and offer to (1) retry with different terms, (2) try a different source via `cms-media-options`, or (3) provide their own image URL. Do not retry automatically.
