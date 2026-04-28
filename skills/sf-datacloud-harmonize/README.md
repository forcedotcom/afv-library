# sf-datacloud-harmonize

Schema harmonization and unification workflows for Salesforce Data Cloud.

## Use this skill for

- DMOs
- field mappings
- relationships
- identity resolution
- unified profiles
- data graphs
- universal ID lookup

## Example requests

```text
"Map this DLO to ssot__Individual__dlm"
"Help me create an identity resolution ruleset"
"Why are unified profiles not appearing?"
"Show me the DMO fields before I create mappings"
```

## Common commands

```bash
sf data360 dmo list --all -o myorg 2>/dev/null
sf data360 query describe -o myorg --table ssot__Individual__dlm 2>/dev/null
sf data360 dmo mapping-list -o myorg --source Contact_Home__dll --target ssot__Individual__dlm 2>/dev/null
sf data360 identity-resolution list -o myorg 2>/dev/null
```

## References

- [SKILL.md](SKILL.md)
- [../sf-datacloud/assets/definitions/dmo.template.json](../sf-datacloud/assets/definitions/dmo.template.json)
- [../sf-datacloud/assets/definitions/mapping.template.json](../sf-datacloud/assets/definitions/mapping.template.json)
- [../sf-datacloud/assets/definitions/relationship.template.json](../sf-datacloud/assets/definitions/relationship.template.json)
- [../sf-datacloud/assets/definitions/data-graph.template.json](../sf-datacloud/assets/definitions/data-graph.template.json)
- [CREDITS.md](CREDITS.md)

## License

MIT License - See [LICENSE](LICENSE).
