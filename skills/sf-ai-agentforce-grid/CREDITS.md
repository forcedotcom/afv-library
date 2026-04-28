# Credits

## sf-ai-agentforce-grid Skill

Contributed to [`sf-skills`](https://github.com/Jaganpro/sf-skills) by [Dylan Andersen](https://github.com/dylandersen).

## Upstream Inspiration

### [Jag Valaiyapathy](https://github.com/Jaganpro)

Created the `sf-skills` project and the `sf-ai-agentforce` skill structure that this Grid skill uses as its template.

### [Chintan Shah](https://github.com/chintanavs)

Created the original Agentforce Grid MCP-and-skill project [`agentforce-grid-ai-skills`](https://github.com/chintanavs/agentforce-grid-ai-skills), whose Grid-specific patterns, API guidance, and implementation direction were used and distilled into this skill.

## This Grid Skill

This variant adapts that structure for Agentforce Grid / AI Workbench workflows, with emphasis on:

- Grid MCP-first workflow design
- Windows-safe setup and authenticated REST fallbacks
- worksheet composition patterns for `Object`, `Reference`, `AI`, `Agent`, `AgentTest`, and `PromptTemplate` columns
- reproducible `apply_grid` YAML examples
- practical findings from live Grid API testing

## References & Inspiration

### Upstream Project

- [`sf-skills`](https://github.com/Jaganpro/sf-skills)
- [`sf-ai-agentforce`](https://github.com/Jaganpro/sf-skills/tree/main/skills/sf-ai-agentforce)
- [`agentforce-grid-ai-skills`](https://github.com/chintanavs/agentforce-grid-ai-skills)

### Salesforce / Grid Documentation

- [Agentforce DX Developer Guide](https://developer.salesforce.com/docs/einstein/genai/guide/agent-dx-nga-author-agent.html)
- [Agentforce Metadata Types](https://developer.salesforce.com/docs/einstein/genai/references/agents-metadata-tooling/agents-metadata.html)
- [Agent Script Guide](https://developer.salesforce.com/docs/einstein/genai/guide/agent-script.html)

## License

MIT License - See [LICENSE](LICENSE)
