# sf-metadata

Salesforce metadata generation and org-querying skill with 120-point scoring. Build custom objects, fields, permission sets, validation rules, and related metadata with production-focused patterns.

## Features

- **Metadata Generation**: Custom objects, fields, layouts, validation rules, permission sets
- **Org Querying**: Describe objects and inspect metadata via `sf` CLI
- **120-Point Scoring**: Validation across structure, naming, security, and best practices
- **Automatic FLS Follow-Up**: Default to Permission Set generation for new custom objects and fields unless the user opts out
- **Cross-Skill Orchestration**: Works with sf-flow, sf-data, and sf-deploy

## Installation

```bash
# Install as part of sf-skills
npx skills add Jaganpro/sf-skills

# Or install just this skill
npx skills add Jaganpro/sf-skills --skill sf-metadata
```

## Quick Start

### 1. Invoke the skill

```
Skill: sf-metadata
Request: "Create a custom object Invoice__c with amount and due date fields"
```

### 2. Common tasks

- Generate object and field metadata
- Query metadata types in a target org
- Generate or update permission sets for newly added fields
- Prepare metadata for deployment via sf-deploy

## Documentation

- [SKILL.md](SKILL.md) - Full workflow and orchestration guidance
- [references/field-and-cli-reference.md](references/field-and-cli-reference.md) - Field types and CLI commands
- [references/permset-auto-generation.md](references/permset-auto-generation.md) - Automatic permission-set / FLS generation rules
- [references/best-practices-scoring.md](references/best-practices-scoring.md) - 120-point scoring breakdown
- [references/orchestration.md](references/orchestration.md) - Cross-skill execution order

## Related Skills

- `sf-flow` - Build automations on top of new metadata
- `sf-data` - Load test data after deployment
- `sf-deploy` - Validate and deploy metadata changes

## License

MIT License. See the repository root [LICENSE](../../LICENSE).
