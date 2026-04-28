<!-- Parent: sf-ai-agentscript/SKILL.md -->

# Sources & Acknowledgments

| Source | Contribution |
|--------|--------------|
| [trailheadapps/agent-script-recipes](https://github.com/trailheadapps/agent-script-recipes) | High-value secondary source for examples and emerging patterns. Mar 2026 audit against upstream commit `9c90176` confirmed: `developer_name` is now canonical, `description:` is the public config field used across the recipe corpus, `@actions.` prefix guidance is explicit, and `run @actions.X` vs reasoning-level utility resolution is documented. Caveats: repo still contains stale/inconsistent examples (`connections:` plural wrapper, mixed lifecycle-hook guidance, strong Employee-Agent bias, weak Service-Agent coverage). Treat as a corroborating source, not sole truth. See [upstream-recipes-audit.md](upstream-recipes-audit.md). |
| [Official GA Documentation](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-script.html) | GA alignment audit (v2.4.0): `filter_from_agent` as GA standard output property, `@system_variables.user_input`, `prompt://` shorthand, `developer_name` output property, `go_to_` naming convention, `is None` vs `== ""` distinction, topic-level `system:` overrides, variable `label` property, `timestamp`/`currency` type restrictions |
| Salesforce Official Documentation | Core syntax, API references, deployment guides |
| TDD Validation (this skill) | 13 validation agents confirming current-release syntax compatibility |
| Tribal knowledge interviews | Canvas View bugs, VS Code limitations, credit consumption patterns |
| [agentforce.guide](https://agentforce.guide/) | Unofficial but useful examples (note: some patterns don't compile in current release) |
| @kunello ([PR #20](https://github.com/Jaganpro/sf-skills/pull/20)) | Prompt template `"Input:fieldName"` binding syntax, context-aware description overrides, `{!@actions.X}` instruction reference patterns, callback behavior notes, error pattern catalog |
| [aquivalabs/my-org-butler](https://github.com/aquivalabs/my-org-butler) | Official sources registry pattern, known-issues tracking structure, verification protocol, Builder UI → Agent Script migration guide, self-improvement protocol |

> **⚠️ Note on Feature Validation**: Some patterns from external sources (e.g., `always_expect_input:`) do NOT compile in Winter '26. Action metadata properties (`label:`, `require_user_confirmation:`, etc.) are valid on **action definitions with targets** but NOT on `@utils.transition`. The `before_reasoning:`/`after_reasoning:` lifecycle hooks ARE valid but require **direct content** (no `instructions:` wrapper). This skill documents only patterns that pass TDD validation.

> **Source-of-truth order for this skill**: official Salesforce docs → local validate/preview/publish evidence → upstream/community examples. When these disagree, prefer observed org behavior over recipe prose.
