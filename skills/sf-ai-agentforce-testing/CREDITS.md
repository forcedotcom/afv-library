# Credits & Acknowledgments

This skill was built upon the collective wisdom of the Salesforce Agentforce developer community and official Salesforce documentation. We gratefully acknowledge the following resources and contributors.

---

## Official Salesforce Resources

### Agentforce Testing Documentation
- **Agent Testing API & CLI**: [developer.salesforce.com/docs](https://developer.salesforce.com/docs/einstein/genai/guide/testing-api-cli.html)
- **Run Agent Tests**: [Agent DX Test Run Guide](https://developer.salesforce.com/docs/einstein/genai/guide/agent-dx-test-run.html)
- **SF Agent Commands**: [CLI Reference](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_agent_commands_unified.htm)
- **Agentforce Testing Center**: [Help Documentation](https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm)

### Trailhead Modules
- **Agentforce Testing**: Testing strategies for AI agents
- **Einstein Copilot Testing**: Validation and quality assurance

---

## Community Contributors

### Salesforce Agentforce Community
Key patterns and practices from:
- Agentforce Developer Community forums
- Salesforce Stack Exchange discussions
- Partner implementations and case studies

### SF CLI Team
The `sf agent test` command set provides the foundation for automated agent testing:
- Test spec generation
- Async test execution
- Result formatting (JSON, JUnit, TAP)
- Interactive preview modes

---

## Related Skills

This skill builds upon patterns established in:

| Skill | Pattern Applied |
|-------|-----------------|
| sf-testing | Agentic test-fix loop pattern |
| sf-ai-agentscript | Agent Script authoring integration (recommended) |
| sf-ai-agentforce | Agentforce platform setup |
| sf-connected-apps | External Client App setup for Agent Runtime API testing |
| sf-debug | Error analysis patterns |

---

## Key Patterns Integrated

| Pattern | Source | Integration |
|---------|--------|-------------|
| Test Spec YAML | SF Agent CLI | assets/basic-test-spec.yaml |
| Agentic Fix Loop | sf-testing skill | references/agentic-fix-loops.md |
| Coverage Analysis | SF Testing Center | references/coverage-analysis.md |
| Cross-Skill Orchestration | sf-skills architecture | hooks/scripts/ |

---

## Philosophy

This skill integrates Salesforce's official Agentforce testing capabilities with agentic development patterns. The goal is to enable autonomous agent development loops where tests automatically identify issues, fixes are generated, and quality is validated - reducing manual intervention in the agent development lifecycle.

---

*If we've missed anyone whose work influenced this skill, please let us know so we can add proper attribution.*
