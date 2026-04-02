---
name: image-generation
description: Orchestrates how to handle image creation requests. Decides whether to delegate to the media-management MCP tool or fall back to a placeholder when the MCP is unavailable. Use when the user asks to add, include, or place an image or media asset in their project.
---

# Media Management

This skill defines the decision flow for handling image creation requests. It does not generate images itself — it determines what to do based on what is available.

## Decision Flow

1. Look at your available tools. If `create_image` is present, proceed to **Using the MCP Tool**.
2. If `create_image` is not available, proceed to **Fallback: Placeholder**.

## Using the MCP Tool

Delegate image generation to the `create_image` tool from the `media-management` MCP server. (`media-management` here refers to the MCP server name, not this skill.)

Apply these defaults unless the user specifies otherwise:

| Parameter | Default | Options |
|---|---|---|
| `model` | `Standard` | `Standard`, `Premium` |
| `size` | `auto` | `auto`, `1024x1024`, `1536x1024`, `1024x1536` (pick closest to requested size) |
| `quality` | `medium` | `low`, `medium`, `high` |
| `outputCompression` | `75` | `0–100` (webp/jpeg only) |
| `outputFormat` | `webp` | `webp`, `jpeg`, `png` |
| `background` | `auto` | `auto`, `transparent`, `opaque` |

**Format rule:** If `outputFormat` is `png`, set `outputCompression` to `100`.

### After the tool responds

Download and preview the result:

```bash
# Retrieve credentials
TARGET_ORG=$(sf config get target-org --json | jq -r '.result[0].value')

# Download
mkdir -p "generatedimages"
curl -f -H "Authorization: Bearer $ACCESS_TOKEN" "$URL" -o "generatedimages/<responseId>.<outputFormat>"

# Preview
code generatedimages/<responseId>.<outputFormat>
```

Use CSS (`width`, `height`, `object-fit`) to control display size. Never resize using external tools.

## Fallback: Placeholder

When `create_image` is not available, use a static placeholder instead of attempting image generation.

1. Check if `generatedimages/placeholder.svg` already exists.
2. If it exists, use it — do not download again.
3. If it does not exist, download it:

```bash
mkdir -p generatedimages
curl -f -o generatedimages/placeholder.svg "https://res.cloudinary.com/dveb6nwve/image/upload/v1775081606/placeholderFinal_l03h2n.svg"
```

## Placeholder Policy

- Only one placeholder exists: `generatedimages/placeholder.svg`.
- Do not generate alternative placeholders using Python, ImageMagick, or any other tool.
- Do not create resized or reformatted versions of the placeholder.
- If the user asks for a placeholder of a different size or format, inform them that only `placeholder.svg` is available and direct them to use CSS to scale it at the point of use.