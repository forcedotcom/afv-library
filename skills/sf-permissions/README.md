# sf-permissions

Salesforce Permission Set analysis, visualization, and auditing tool.

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ensure you're authenticated via sf CLI
sf org login web --set-default

# 4. Run commands
python scripts/cli.py hierarchy                              # View org hierarchy
python scripts/cli.py detect object Account --access delete  # Who can delete Accounts?
python scripts/cli.py user john@example.com                  # Analyze user permissions
```

## Features

- **Permission Hierarchy Viewer**: Visualize PSG → PS relationships
- **Permission Detector**: "Who has access to X?" for objects, fields, Apex, custom permissions
- **User Analyzer**: See all permissions assigned to a specific user
- **CSV/JSON Export**: Export Permission Set configurations
- **Dual Output**: ASCII trees (terminal) + Mermaid diagrams (documentation)

## CLI Commands

```bash
# View org permission hierarchy
python scripts/cli.py hierarchy
python scripts/cli.py hierarchy --format mermaid > hierarchy.md

# Detect who has specific permissions
python scripts/cli.py detect object Account --access delete
python scripts/cli.py detect field Account.AnnualRevenue --access edit
python scripts/cli.py detect apex MyApexController
python scripts/cli.py detect custom Can_Approve_Expenses
python scripts/cli.py detect system ModifyAllData

# Analyze user permissions
python scripts/cli.py user john@company.com
python scripts/cli.py user 005xx000001234AAA --format mermaid

# Export Permission Set
python scripts/cli.py export Sales_Manager -o /tmp/sm.csv
python scripts/cli.py export Sales_Manager -o /tmp/sm.json

# View Permission Set details
python scripts/cli.py ps Sales_Manager
python scripts/cli.py psg Sales_Cloud_User
python scripts/cli.py users Sales_Manager  # List users with this PS
```

## Documentation

- [SKILL.md](SKILL.md) - Full skill definition and SOQL reference
- [references/permission-model.md](references/permission-model.md) - How Salesforce permissions work
- [references/soql-reference.md](references/soql-reference.md) - Permission-related SOQL queries
- [references/usage-examples.md](references/usage-examples.md) - CLI and Python API examples

## Credits

Inspired by [PSLab](https://github.com/OumArbani/PSLab) by Oumaima Arbani.

## License

MIT License - see [LICENSE](LICENSE)
