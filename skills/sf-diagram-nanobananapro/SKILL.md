---
name: sf-diagram-nanobananapro
description: >
  AI-powered image generation for Salesforce visuals via Nano Banana Pro.
  TRIGGER when: user asks for PNG/SVG output, UI mockups, wireframes, visual ERDs,
  or says "generate image" / "create mockup".
  DO NOT TRIGGER when: text-based Mermaid diagrams (use sf-diagram-mermaid),
  or non-visual documentation tasks.
license: MIT
metadata:
  version: "1.5.0"
  author: "Jag Valaiyapathy"
  scoring: "80 points across 5 categories"
---

# sf-diagram-nanobananapro: Salesforce Visual AI Skill

Use this skill when the user needs **rendered visuals**, not text diagrams: ERDs, UI mockups, architecture illustrations, slide-ready images, or image edits using Nano Banana Pro.

## Hard Gate: Prerequisites First

Always run the prerequisites check before using the skill:

```bash
~/.claude/skills/sf-diagram-nanobananapro/scripts/check-prerequisites.sh
```

If prerequisites fail, stop and route the user to setup guidance in:
- [references/gemini-cli-setup.md](references/gemini-cli-setup.md)

---

## When This Skill Owns the Task

Use `sf-diagram-nanobananapro` when the user wants:
- PNG / SVG-style image output
- rendered ERDs or architecture diagrams
- LWC or Experience Cloud mockups / wireframes
- visual polish beyond Mermaid
- edits to a previously generated image

Delegate elsewhere when the user wants:
- Mermaid or text-only diagrams → [sf-diagram-mermaid](../sf-diagram-mermaid/SKILL.md)
- metadata discovery for ERDs → [sf-metadata](../sf-metadata/SKILL.md)
- LWC implementation after the mockup → [sf-lwc](../sf-lwc/SKILL.md)
- Apex review / implementation → [sf-apex](../sf-apex/SKILL.md)

---

## Required Context to Gather First

Ask for or infer:
- image type: ERD, UI mockup, architecture illustration, or image edit
- subject scope and key entities / systems
- target quality: draft vs presentation vs production asset
- preferred style and aspect ratio
- whether the user wants quick mode or an interview-driven prompt build

---

## Interview-First Workflow

Unless the user explicitly asks for **quick/simple/just generate**, ask clarifying questions first.

### Minimum question set
| Request type | Ask about |
|---|---|
| ERD / schema | objects, visual style, purpose, extras |
| UI mockup | component type, object/context, device/layout, style |
| architecture image | systems, boundaries, protocols, emphasis |
| image edit | what to keep, what to change, output quality |

Question bank: [references/interview-questions.md](references/interview-questions.md)

### Quick mode defaults
If the user says “quick”, “simple”, or “just generate”, default to:
- professional style
- 1K draft output
- legend included when helpful
- one image first, then iterate

---

## Recommended Workflow

### 1. Gather inputs
Decide which of these are needed:
- object list / metadata
- purpose: draft vs presentation vs documentation
- desired aesthetic
- aspect ratio / resolution
- whether this is a fresh render or edit of an existing image

### 2. Build a concrete prompt
Good prompts specify:
- subject and scope
- composition / layout
- color treatment
- labels / legends / relationship lines
- output quality goal

### 3. Generate a fast draft first
```bash
gemini --yolo "/generate 'Professional Salesforce ERD with Account, Contact, Opportunity; clean legend; white background; Salesforce-style colors'"
```

### 4. Iterate before final
Use natural-language edits:
```bash
gemini --yolo "/edit 'Move Account to center, thicken relationship lines, add legend in bottom right'"
```

### 5. Use the Python script for controlled final output
Use the script when you need higher resolution or explicit edit inputs:
```bash
uv run scripts/generate_image.py \
  -p "Final production-quality Salesforce ERD with legend and field highlights" \
  -f "crm-erd-final.png" \
  -r 4K
```

Full iteration guide: [references/iteration-workflow.md](references/iteration-workflow.md)

---

## Default Style Guidance

For ERDs, default to the **architect.salesforce.com** aesthetic unless the user asks otherwise:
- dark border + light fill cards
- cloud-specific accent colors
- clean labels and relationship lines
- presentation-ready whitespace and hierarchy

Style guide: [references/architect-aesthetic-guide.md](references/architect-aesthetic-guide.md)

---

## Common Patterns

| Pattern | Default approach |
|---|---|
| visual ERD | get metadata if available, then render a draft first |
| LWC mockup | use component template + user context + one draft iteration |
| architecture illustration | emphasize systems and flows, reduce field-level detail |
| image refinement | use `/edit` for small changes before regenerating |
| final production asset | switch to script-driven 2K/4K generation |

Examples: [references/examples-index.md](references/examples-index.md)

---

## Output / Review Guidance

After generating, do one of these:
- open the file in Preview for visual inspection
- attach/read the image in the coding session for multimodal review
- ask the user whether to iterate on layout, labeling, or color before finalizing

Keep the first pass cheap; only spend on high-res output after the composition is right.

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|---|---|---|
| Mermaid first draft or text diagram | [sf-diagram-mermaid](../sf-diagram-mermaid/SKILL.md) | faster structural diagramming |
| object / field discovery for ERD | [sf-metadata](../sf-metadata/SKILL.md) | accurate schema grounding |
| turn mockup into real component | [sf-lwc](../sf-lwc/SKILL.md) | implementation after design |
| review Apex / trigger code in parallel | [sf-apex](../sf-apex/SKILL.md) | code-quality follow-up |

---

## Reference Map

### Start here
- [references/gemini-cli-setup.md](references/gemini-cli-setup.md)
- [references/interview-questions.md](references/interview-questions.md)
- [references/iteration-workflow.md](references/iteration-workflow.md)

### Visual style / examples
- [references/architect-aesthetic-guide.md](references/architect-aesthetic-guide.md)
- [references/examples-index.md](references/examples-index.md)
- [assets/erd/](assets/erd/)
- [assets/lwc/](assets/lwc/)
- [assets/architecture/](assets/architecture/)
- [assets/review/](assets/review/)

---

## Score Guide

| Score | Meaning |
|---|---|
| 70+ | strong image prompt / workflow choice |
| 55–69 | usable draft with iteration needed |
| 40–54 | partial alignment to request |
| < 40 | poor fit; re-interview and rebuild prompt |
