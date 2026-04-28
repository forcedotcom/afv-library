# Credits

## sf-ai-agentscript Skill

Created by [Jag Valaiyapathy](https://github.com/Jaganpro)

## Knowledge Sources

### Agent Script Documentation Workshop (January 2026)

This skill was developed from comprehensive documentation screenshots covering 8 modules (96 total screenshots):

| Module | Topic | Coverage |
|--------|-------|----------|
| 1 | Why Agent Script? | The Problem, Three Innovations, Reasoning Engine, Deterministic Toolkit |
| 2 | FSM Architecture | Legacy Issues, FSM Fundamentals, 5 Node Patterns, Deterministic vs Subjective |
| 3 | Agent Script Syntax | Block Structure, Variables, Topics, Pre-Deployment Checklist |
| 4 | Instruction Resolution | Three Phases, Pre-LLM, LLM Processing, Post-Action Loop |
| 5 | Grounding & Multi-Agent | Retriever Actions, 6 Action Protocols, SOMA Patterns |
| 6 | Forensic Debugging | Interaction Details, Trace Waterfall, Variable State, Script Linting |
| 7 | Batch Testing | Testing Center, Quality Evaluations, LLM-as-Judge, Deployment Lifecycle |
| 8 | CLI & Deployment | Authoring Bundle, CLI Commands, Pro-Code Workflow, Metadata Shuttling |

### Official Salesforce Documentation

- [Agent Script Documentation](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-script.html)
- [Agentforce Builder Guide](https://help.salesforce.com/s/articleView?id=sf.copilot_builder_overview.htm)
- [Agentforce DX Guide](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx.html)
- [Salesforce CLI Agent Commands](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_agent_commands_unified.htm)

### Community Contributions

| Source | Contribution |
|--------|-------------|
| [aquivalabs/my-org-butler](https://github.com/aquivalabs/my-org-butler) | Official sources registry pattern, known-issues tracking structure, verification protocol, Builder UI → Agent Script migration guide, self-improvement protocol |
| @kunello ([PR #20](https://github.com/Jaganpro/sf-skills/pull/20)) | Prompt template `"Input:fieldName"` binding syntax, context-aware description overrides, `{!@actions.X}` instruction reference patterns, callback behavior notes, error pattern catalog |
| [August Krys](https://github.com/not2technical) | Prompt metadata modernization follow-up, including consistency updates around `GenAiPromptTemplate`, published/active template readiness, and current prompt-template examples |
| Hua Xu (Salesforce APAC FDE team) | "Open Gate" pattern: 3-variable state machine for auth-gated topic routing with LLM bypass and EXIT_PROTOCOL |
| [trailheadapps/agent-script-recipes `.airules/AGENT_SCRIPT.md`](https://github.com/trailheadapps/agent-script-recipes) | Error prevention patterns: `@inputs` in `set` anti-pattern, bare action name detection, `run` vs utility action resolution. Contributors: [@pozil](https://github.com/pozil), [@msrivastav13](https://github.com/msrivastav13), [@muenzpraeger](https://github.com/muenzpraeger), [@albarivas](https://github.com/albarivas), [@charlesw-salesforce](https://github.com/charlesw-salesforce) |

### Related Skills

This skill integrates with other sf-skills:

- **sf-ai-agentforce** - Standard Agentforce platform skill (Agent Builder, PromptTemplate, Models API)
- **sf-ai-agentforce-testing** - Agent testing with CLI
- **sf-flow** - Flow development for `flow://` action targets
- **sf-deploy** - Deployment validation and execution

## Key Concepts Attribution

| Concept | Source |
|---------|--------|
| FSM Architecture | Salesforce Agent Script Workshop |
| Instruction Resolution (3-phase model) | Salesforce Agent Script Workshop |
| Deterministic Building Blocks | Salesforce Agent Script Workshop |
| SOMA (Same Org Multi-Agent) | Salesforce Agent Script Workshop |
| 100-Point Scoring System | sf-skills Pattern (adapted from sf-ai-agentforce) |
| Open Gate Pattern (State Gate) | Hua Xu (Salesforce APAC FDE team) |

## Tools & Technologies

- **Claude Code** - AI-assisted development (adapted from "Vibes AI" in original docs)
- **Salesforce CLI v2** - `sf agent` commands for agent management
- **Agent Script DSL** - Salesforce's declarative agent definition language

## License

MIT License - See [LICENSE](LICENSE)

---

*Last updated: February 2026*
