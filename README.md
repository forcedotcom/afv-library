# Agentforce Vibes Library

AI prompts and rules library for Agentforce Vibes development, content creation, and workflow automation.

## 📚 About

This repository curates Salesforce-focused prompts and system rules from the wider developer community to accelerate Agentforce Vibes agentic workflows. Collections are organized by development discipline—Apex, LWC, flows, deployments, testing, investigation, spec-driven delivery, and more—so contributors can share reusable prompts, scaffolds, and guardrails that other teams can adapt and extend.

## 🚀 Quick Start

### Using with VS Code Extension

Coming soon!

### Manual Usage

Browse the repository and copy/paste any prompt or rule directly into Agenforce Vibes.

### Connecting Team or Personal Libraries

You can register additional repos with the extension as long as they mirror this structure:

- Root folders named `prompts/` and `rules/`, each containing category subfolders (e.g., `prompts/apex-development/`).
- Each prompt or rule stored in its own Markdown file with YAML frontmatter (`name`, `description`, `tags`, optional setup metadata).
- Category folders may include a `README.md` describing their focus; empty folders are allowed for future content.

When you add a new library:

1. Ensure the folder layout matches the table in `## 🗂️ Structure`.
2. Follow the naming conventions and prompt format outlined below.
3. Register the repository with `Agentforce Vibes: Add Library` in VS Code.
4. Refresh the extension to surface the new content instantly.

## 📝 Prompt Format

Every prompt begins with YAML frontmatter that surfaces key metadata to contributors and tooling:

```markdown
---
name: Concise Prompt Title
description: One-sentence summary of the outcome you want
tags: category, use-case, tooling
requires_deploy: true        # optional – include when pre-work is required
setup_summary: Deploy baseline trigger before refactor  # optional helper text
---
```

- `name`, `description`, and `tags` are required.
- Use lowercase, comma-separated tags drawn from the category and focus area (e.g., `apex, refactor, testing`).
- Add `requires_deploy` (and an optional `setup_summary`) when the prompt depends on seed metadata or data.

After the frontmatter, organize the body with clear sections. A common pattern is:

1. `## Setup` – only when pre-work, sample metadata, or environment configuration is needed.
2. `## Context` – summarize the scenario, constraints, personas, or assets involved.
3. `## Instructions` – detail the tasks in numbered steps, calling out decision points or checkpoints.
4. `## Testing & Reporting` – define verification steps, coverage expectations, or deliverables.
5. `## Follow-ups` – optional space for stretch goals, review questions, or iteration loops.

### Example Prompt

**File:** `prompts/apex-development/trigger-refactoring.md`

```markdown
---
name: Trigger Refactor Helper
description: Refactor the Opportunity trigger into a handler pattern with tests
tags: apex, refactor, testing
requires_deploy: true
setup_summary: Deploy baseline trigger to target org before running instructions
---

## Setup
1. Deploy the baseline trigger shown below to your default or scratch org.
2. Confirm the trigger compiles successfully before continuing.

```apex
// ... baseline trigger omitted for brevity ...
```

## Instructions
Refactor `OpportunityTrigger` into a handler class (or classes) that handles the same behavior using bulk-safe patterns. Ensure the trigger itself delegates and remains behaviorally identical.

## Testing & Reporting
- Create unit tests covering positive and negative paths for each handler method.
- Include a bulk test that updates 50 `Opportunity` records where only half qualify for the `after update` logic.
- Deploy the refactored code and run the tests, then report coverage and key observations.

## 📂 Categories Guide

These starter categories reflect the current repository layout. Contributors are welcome to propose new ones or reorganize as long as the structure stays consistent for the VS Code extension.

### Prompts

| Category | Purpose | Example Topics |
|----------|---------|----------------|
| **apex-development** | Build and optimize Apex codebases | Trigger frameworks, async patterns, governor limit tuning |
| **lwc-development** | Craft Lightning Web Components | Component architecture, reactive data, UI patterns |
| **metadata-deployments** | Plan and execute releases | Packaging, Git branching, rollback prep |
| **vibe-coding** | Agentforce Vibes coding workflows | Apex/LWC scaffolds, prompt-to-code translation |
| **testing-automation** | Validate platform behavior | Apex tests, Flow scenarios, regression suites |
| **investigation-triage** | Diagnose and resolve issues | Incident response, log analysis, performance forensics |
| **data-operations** | Manage data pipelines | ETL prompts, bulk operations, platform events |
| **spec-driven-dev** | Generate and refine specification-first workflows | Requirement capture, traceability matrices, auto-generated tasks |
| **security-compliance** | Enforce standards and controls | Permission audits, secure coding, compliance narratives |
| **integration-fabric** | Coordinate external services | API design, middleware coordination, error recovery |
| **enablement-docs** | Share knowledge and runbooks | Onboarding guides, release notes, changelog automation |

### Rules

| Category | Focus | Example Assets |
|----------|-------|----------------|
| **apex-development** | Standards for Apex architecture and quality | Trigger guardrails, async execution policies |
| **lwc-development** | Front-end guardrails for Lightning Web Components | Accessibility checklists, component review templates |
| **metadata-deployments** | Release management discipline | Branching policies, deployment readiness reviews |
| **vibe-coding** | Coding quality for Agentforce Vibes assets | Code review criteria, secure pattern guides |
| **testing-automation** | Verification and validation expectations | Test coverage thresholds, regression playbooks |
| **investigation-triage** | Incident and root-cause response | Escalation runbooks, logging requirements |
| **data-operations** | Data stewardship and job governance | Data quality SLAs, bulk job safeguards |
| **spec-driven-dev** | Specification-first delivery standards | Definition-of-done templates, traceability requirements |
| **security-compliance** | Platform security and regulatory posture | Access reviews, compliance attestation steps |
| **integration-fabric** | External connection reliability | Retry policies, credential rotation standards |
| **enablement-docs** | Knowledge management and enablement | Release note templates, onboarding workflows |
| **org-governance** | Enterprise policy alignment | Org strategy playbooks, architecture review guidelines |
| **support-operations** | Production support excellence | Incident response SLAs, shift handover procedures |
| **ai-safety** | Responsible agent behavior | Ethical guidelines, bias detection checklists |

## ✨ Creating New Prompts & Rules

1. **Choose the right category** based on use case (if nothing fits, propose a new category)
2. **Create a descriptive filename** (use kebab-case: `my-prompt.md`)
3. **Add frontmatter** with name, description, and tags
4. **Write clear instructions** with placeholders for user input
5. **Test** before committing
6. **Commit with message**: `Add [name] for [use case]`

### Naming Conventions

- Use lowercase with hyphens: `code-review-helper.md`
- Be descriptive: `salesforce-apex-debug.md` not `debug.md`
- Include context: `blog-post-outline.md` not `outline.md`

## 🔧 Best Practices

### Writing Effective Prompts

- ✅ **Be specific** - Clear instructions yield better results
- ✅ **Use structure** - Numbered lists and sections help
- ✅ **Add context** - Explain what you want and why
- ✅ **Include examples** - Show expected output format
- ✅ **Test thoroughly** - Verify prompts work as intended

### Prompt Engineering

- ✅ **Clarify the objective** – Capture the outcome, stakeholders, and success metrics directly in the frontmatter
- ✅ **Share context** – Provide links, metadata, or sample records so Agentforce can ground its reasoning
- ✅ **Set guardrails** – Define tone, compliance boundaries, what to avoid, and when to ask for confirmation
- ✅ **Guide the workflow** – Break the request into staged checkpoints (ideate → propose → confirm → deliver)
- ✅ **Capture feedback loops** – Invite GPT-5 to flag assumptions, pose questions, and suggest validation steps
- ✅ **Encourage adaptability** – Note how the prompt or rule can flex across org types, industries, and data volumes

#### Structuring Prompts

- **Prime with examples**: Include concise samples that illustrate the desired format or code pattern
- **Model the format**: Provide headings and numbered steps so Agentforce mirrors the final artifact
- **Address ambiguity**: Explicitly call out unknowns and ask Agentforce to gather missing inputs
- **Control verbosity**: Specify length limits, number of alternatives, or time horizons
- **Request diagnostics**: Ask Agentforce to share reasoning, risks, and verification plans when appropriate

#### Template: Multi-Step Prompt

```markdown
---
name: Apex Service Hardening Plan
description: Audit and fortify an Apex service to stay within governor limits while preserving behavior
tags: apex-development, optimization, audit
requires_deploy: false
---

## Context
- Usage profile: [Invocation volume, entry points, data scale]
- Known issues: [Timeouts, limit exceptions, performance complaints]
- Stakeholders: [Product owners, support teams, compliance partners]

## Instructions
1. Summarize existing architecture, dependencies, and limit usage; list assumptions needing confirmation.
2. Propose at least two optimization strategies, including refactor scope, data implications, and rollback considerations.
3. Recommend a preferred strategy once assumptions are resolved, detailing implementation phases and change management steps.

## Testing & Reporting
- Define unit, integration, and bulk test coverage with pass criteria.
- Specify telemetry/observability updates (logging, metrics, alerts) to validate success.
- Produce an execution checklist with owners, timelines, and escalation contacts.
```

### Organizing Rules

- ✅ **One rule per file** - Keep rules focused and modular
- ✅ **Use clear names** - Describe what the rule enforces
- ✅ **Document purpose** - Explain why the rule exists
- ✅ **Keep updated** - Review and refine regularly
- ✅ **Version control** - Track changes over time

## 🤝 Contributing

### How to Contribute

1. Clone the repository
2. Create a feature branch: `git checkout -b add-new-prompt`
3. Add your prompt/rule following the format
4. Test thoroughly
5. Create a pull request with description

**Contribution checklist**
- Confirm the file lives in the correct category folder
- Complete the YAML frontmatter (`name`, `description`, `tags`)
- Include clear instructions and placeholders for user-specific details
- Add a short note on how others can adapt the prompt, especially for varying Salesforce environments
- Verify the content respects licensing and attribution requirements
- Provide any supporting references or context in the pull request description

### Feedback

Found an issue or have a suggestion?
- Open an issue in GitHub
- Suggest improvements via pull request
- Start a discussion in GitHub Discussions or the pull request thread

## 🔄 Maintenance

### Updating Prompts

To update an existing prompt:
1. Edit the `.md` file
2. Update the description if behavior changed
3. Test the updated prompt
4. Commit with clear message: `Update [prompt]: [what changed]`

### Adding New Categories

To add a new category:
1. Create a new folder in `prompts/` or `rules/`
2. Add a `README.md` explaining the category
3. Add initial prompts/rules
