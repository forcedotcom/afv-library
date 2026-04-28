# sf-diagram-nanobananapro

AI-powered visual content generation for Salesforce development. Generate ERD diagrams, LWC mockups, and architecture visuals using Gemini 3 Pro Image (Nano Banana Pro).

## Features

- **Visual ERD Generation**: Create actual rendered ERD diagrams (not just Mermaid code)
- **LWC/UI Mockups**: Generate wireframes and component mockups following SLDS
- **Gemini Code Review**: Parallel code review while Claude continues working
- **Documentation Research**: Parallel Salesforce documentation research via Gemini

## Installation

```bash
# Install as part of sf-skills
npx skills add Jaganpro/sf-skills

# Or install just this skill
npx skills add Jaganpro/sf-skills --skill sf-diagram-nanobananapro
```

## Prerequisites

**IMPORTANT**: Run the prerequisites check before using this skill:

```bash
~/.claude/skills/sf-diagram-nanobananapro/scripts/check-prerequisites.sh
```

| Requirement | Description | How to Get |
|-------------|-------------|------------|
| **Ghostty Terminal** | Required for Kitty graphics protocol | https://ghostty.org |
| **GEMINI_API_KEY** | Personal API key for Nano Banana Pro | https://aistudio.google.com/apikey |
| **Gemini CLI** | Command-line interface for Gemini | `npm install -g @google/gemini-cli` |
| **Nano Banana Extension** | Image generation extension | `gemini extensions install nanobanana` |
| **timg** | Terminal image viewer with Kitty support | `brew install timg` |

## Quick Start

### 1. Set up your API key

Add to `~/.zshrc`:
```bash
export GEMINI_API_KEY="your-personal-api-key"
export NANOBANANA_MODEL=gemini-3-pro-image-preview
```

### 2. Invoke the skill

```
Skill: sf-diagram-nanobananapro
Request: "Generate an ERD diagram showing Account, Contact, and Opportunity relationships"
```

### 3. View the result

Images are displayed inline using Kitty graphics protocol (Ghostty) or via Claude's multimodal vision using the Read tool.

## Use Cases

| Use Case | Example Request |
|----------|-----------------|
| ERD Diagrams | "Generate a visual ERD for Account, Contact, Opportunity" |
| LWC Mockups | "Create a mockup for an Account list datatable component" |
| Code Review | "Get Gemini's review of this Apex trigger" |
| Doc Research | "Research the Flow best practices in Salesforce docs" |

## Cross-Skill Integration

| Related Skill | When to Use |
|---------------|-------------|
| sf-diagram-mermaid | Convert Mermaid to visual rendering |
| sf-metadata | Query object/field data before generating ERDs |
| sf-lwc | Generate mockups for LWC components |
| sf-apex | Review Apex code via Gemini sub-agent |

## Documentation

- [Gemini CLI Setup](references/gemini-cli-setup.md)

## Security Notes

**NEVER commit your GEMINI_API_KEY to version control**

- Store API key in `~/.zshrc` only (not in project files)
- The key is personal and tied to your Google account billing

## Requirements

- Ghostty terminal (for Kitty graphics)
- Gemini CLI with Nano Banana extension
- GEMINI_API_KEY environment variable
- timg (for terminal image display)

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2025 Jag Valaiyapathy
