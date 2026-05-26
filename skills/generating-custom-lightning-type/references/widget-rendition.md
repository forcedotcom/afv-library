# Widget Rendition Reference

How to author a UEM widget tree that renders a Custom Lightning Type's grounding schema as a `tile/mosaic` widget across surfaces.

## When to read this file

Read this file when the parent skill routes to widget rendition (user requested a "widget", "mosaic", or "fragment"). Do not use these patterns for custom-LWC renderers.

## Scope

- **In scope**: building the UEM tree under `renderer.componentOverrides["$"].children`, including composition, attribute binding, layout, and writing the final `renderer.json`.
- **Out of scope**: runtime meta directives (`forEach`, `forItem`, `if`) — read `references/widget-meta-directives.md`.

---

## Composition

A widget is a UEM(Unified Experience Model) tree of blocks. Every block follows this shape:

```ts
interface Block {
  definition: string  // {namespace}/{blockName}
  attributes?: Record<string, any>
  meta?: {
    forEach?: string   // see widget-meta-directives.md
    forItem?: string   // see widget-meta-directives.md
    if?: string        // see widget-meta-directives.md
  }
  children?: Block[]
}
```

---

## Available metadata actions

### discoverUiComponents

**Purpose**: Discover the palette of blocks available for composition.

**Required parameters**: `actionName: "discoverUiComponents"`, `metadataType: "FRAGMENT"`, `parameters.pageType: "FRAGMENT"`. Optional: `searchQuery` to filter by name/description.

**Returns**: list of `{ definition, description, label, attributes? }`.

### getUiComponentSchemas

**Purpose**: Fetch JSON schemas (property types, required vs optional, validation) for selected blocks.

**Required parameters**: `actionName: "getUiComponentSchemas"`, `metadataType: "FRAGMENT"`, `parameters.pageType: "FRAGMENT"`, `parameters.componentDefinitions: ["namespace/definition", …]`. Optional: `includeKnowledge` (default `true`).

**Returns**: `componentSchemas[]` (success entries carry the JSON schema, failure entries carry an error message — partial failures are supported).

---

## Attribute binding

- Bind a block property to schema data with `{!$attrs.<attrName>}`. `<attrName>` MUST match the property name in the grounding schema. Example: `"text": "{!$attrs.title}"`.
- When the block is inside a `forEach`, reference the loop variable instead — e.g. `"text": "{!$item.name}"`. See `references/widget-meta-directives.md`.

---

## Layout best practices

These conventions cover widget *structure* — how blocks are grouped and stacked. For visual style choices, see *Styling best practices* below.

The first child inside `tile/mosaic.children` should be a single `tile/column`. All widget content goes inside that column for predictable vertical structure across surfaces.

| Primitive | Purpose | When to use |
|-----------|---------|-------------|
| `tile/column` | Vertical stack of children | The root wrapper, and any group of blocks that should stack |
| `tile/row` | Horizontal stack of children | Two or more blocks that belong on the same line |
| `tile/card` | Visually-boxed group | A bounded section that should read as one unit |
| `tile/divider` | Visual rule between sections | Separating major content groups (header / body / footer) |
| `tile/spacer` | Whitespace without a visible line | When extra space is needed but a divider would be too heavy; set `flex: true` to fill remaining space in a row |

Use the five primitives above for structure; all other (content) blocks come from `discoverUiComponents`.

- **Sectioning**: Place a `tile/divider` *or* a fresh `tile/card`-bounded section between major content groups (header → body, body → footer). Pick the divider for lightweight rules between sections of the same widget; pick a card when the section is its own logical unit. Do not use either inside a single section.
- **Nesting**: Prefer flat layouts. Only nest a `tile/column` inside a `tile/row` (or vice versa) when the visual orientation actually changes for that subgroup.

---

## Styling best practices

Widgets express *intent*, not pixels. Each surface (Slack, ChatGPT, ACC, Mobile, etc.) provides a default native look and feel, and brand/theme overrides apply automatically. Principles the widget author owns:

- **Style semantically.** Use `variant`, `size`, and other enum-typed attributes (e.g. `primary`, `destructive`, `success`, `warning`) to express intent. Do not pin literal colors, fonts, or pixel values — that fights the surface's rendering and breaks brand/theme application.
- **One primary action per visible group.** At most one `tile/button` with `variant: primary` per visible action group. Use `secondary`, `outline`, or `ghost` for additional actions. Reserve `destructive` for genuinely destructive operations (delete, cancel a paid order, etc.).
- **One `h1` per widget.** The `h1` is the widget title. Use `h2`/`h3` for sub-section headings (skipping levels is fine if the hierarchy is shallow), `body` for prose, and `caption` for helper text.
- **Use semantic state variants on state-bearing blocks.** For `tile/alert`, `tile/badge`, `tile/callout`, and `tile/chip`, set `variant` to the semantic state (`success`, `warning`, `error`, `info`, etc.). Do not express state by overriding `text.color` on a generic block — the dedicated blocks render the correct iconography and accessibility cues for free.
- **Accept schema defaults for `gap`, `padding`, and `size`** unless there's a specific reason to override. When you do override, always pass the enum-defined token (the schema rejects pixel values and freeform strings).
- **Don't pin `width`, `height`, or `maxWidth`** unless a content constraint genuinely requires it — the surface owns layout sizing. For long text, use `truncate: true` rather than capping `maxWidth`.
- **Use the Lucide icon set.** Every `icon` attribute resolves to a name in the Lucide icon set. Pass the Lucide name (e.g. `"check"`, `"alert-circle"`); other icon libraries are not supported.

---

## Workflow

1. **Parse the schema** — extract property names, types, required vs optional, and nested structure from the CLT's grounding schema. This is the **widget spec**.
2. **Discover blocks** — call `discoverUiComponents`. Use property types from the widget spec to inform `searchQuery` (e.g. text → `"text"`, number → `"number"`).
3. **Select blocks** — choose one block per widget-spec property, plus structural primitives from *Layout best practices*.
4. **Get block schemas** — call `getUiComponentSchemas` for the selected blocks and review their property metadata.
5. **Read every matching example** — before authoring, identify which patterns the widget spec needs and read **all** matching renderer examples in `examples/widgets/`. A complex widget combines multiple patterns; read all that apply.

   | Pattern in the widget spec | Example to read |
   |---|---|
   | Single object (no root iteration) | `examples/widgets/single-object-profile.renderer.json` |
   | Collection (root-level array iterated with `forEach`), including a nested `forEach` over an array on each item | `examples/widgets/list-of-products.renderer.json` |
   | Conditional rendering (`if` bound to a boolean), including `if` + `forEach` on the same `meta` | `examples/widgets/conditional-rendering.renderer.json` |

   Use these as structural starting points, not literal templates. Compose the patterns the widget actually needs.
6. **Build the UEM tree** —
   - Map each widget-spec property to a block property; preserve widget-spec order.
   - **Decide root iteration**: if the schema is a single object, render its properties directly under the root `tile/column`. If the schema is a collection (top-level array), wrap the repeating block in `forEach` / `forItem`. For placement rules and example shapes, read `references/widget-meta-directives.md`.
   - Bind values with placeholder syntax (see *Attribute binding* above).
   - For any block that should render conditionally, add `"if"` on its `meta` — read `references/widget-meta-directives.md`.
7. **Write to the CLT bundle** — output to `lightningTypes/<TypeName>/lightningDesktopGenAi/renderer.json` (or the surface-specific subfolder: `experienceBuilder/`, `lightningMobileGenAi/`, `enhancedWebChat/`). The renderer's root override is:

```json
{
  "renderer": {
    "componentOverrides": {
      "$": {
        "type": "mosaic",
        "definition": "tile/mosaic",
        "children": [ /* the UEM tree built in step 5 — root is tile/column */ ]
      }
    }
  }
}
```

---

## Rules / constraints

| Constraint | Rationale |
|-----------|-----------|
| Block definitions follow `{namespace}/{blockName}` and must match the form returned by `discoverUiComponents` | The runtime resolves blocks by exact definition string |
| Never pass `tile/mosaic` to `getUiComponentSchemas` | It is a fixed wrapper, not a queryable component |
| Always supply `parameters` (with required keys) when calling `execute_metadata_action` | Missing parameters cause a hard failure, not a partial result |
| The first child of `tile/mosaic.children` is a single `tile/column` | Predictable widget structure across surfaces |

---

## Gotchas

| Issue | Resolution |
|-------|-----------|
| `getUiComponentSchemas` returns a partial-failure entry for a block | Pick a different block from `discoverUiComponents` results; do not silently continue without a schema |
| Output written to the wrong surface subfolder | Default to `lightningDesktopGenAi/`; switch only when the user names the surface |

---

## Reference File Index

| File | When to read |
|------|--------------|
| `references/widget-meta-directives.md` | For the `forEach` / `forItem` (iteration) and `if` (conditional rendering) directives — including patterns not shown in examples (nested `forEach`, container-vs-child placement) |
| `examples/widgets/single-object-profile.renderer.json` | For the single-object pattern (root binding via `{!$attrs.X}`, no iteration) |
| `examples/widgets/list-of-products.renderer.json` | For the collection pattern (root-level `lightning__listType` iterated with `forEach`); also covers a nested `forEach` over an array per item |
| `examples/widgets/conditional-rendering.renderer.json` | For the conditional pattern (`if` on a `meta` object, including `if` + `forEach` on the same block) |

A complex widget often combines several of these patterns (e.g. collection + nested `forEach` + conditional). Read every applicable row.
