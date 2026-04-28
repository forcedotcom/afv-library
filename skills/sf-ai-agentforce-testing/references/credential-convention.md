<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Credential Convention (~/.sfagent/)

Persistent ECA credential storage managed by `hooks/scripts/credential_manager.py`.

## Directory Structure

```
~/.sfagent/
├── .gitignore          ("*" — auto-created, prevents accidental commits)
├── {Org-Alias}/        (org alias — case-sensitive, e.g. MyOrg-Sandbox)
│   └── {ECA-Name}/     (ECA app name — use `discover` to find actual name)
│       └── credentials.env
└── Other-Org/
    └── My_ECA/
        └── credentials.env
```

## File Format

```env
# credentials.env — managed by credential_manager.py
# 'export' prefix allows direct `source credentials.env` in shell
export SF_MY_DOMAIN=yourdomain.my.salesforce.com
export SF_CONSUMER_KEY=3MVG9...
export SF_CONSUMER_SECRET=ABC123...
```

## Security Rules

| Rule | Implementation |
|------|---------------|
| Directory permissions | `0700` (owner only) |
| File permissions | `0600` (owner only) |
| Git protection | `.gitignore` with `*` auto-created in `~/.sfagent/` |
| Secret display | NEVER show full secrets — mask as `ABC...XYZ` (first 3 + last 3) |
| Credential passing | Export as env vars for subprocesses, never write to temp files |

## CLI Reference

```bash
# Discover orgs and ECAs
python3 {SKILL_PATH}/hooks/scripts/credential_manager.py discover
python3 {SKILL_PATH}/hooks/scripts/credential_manager.py discover --org-alias YourOrg

# Load credentials (secrets masked in output)
python3 {SKILL_PATH}/hooks/scripts/credential_manager.py load --org-alias {org} --eca-name {eca}

# Save new credentials
python3 {SKILL_PATH}/hooks/scripts/credential_manager.py save \
  --org-alias {org} --eca-name {eca} \
  --domain yourdomain.my.salesforce.com \
  --consumer-key 3MVG9... --consumer-secret ABC123...

# Validate OAuth flow
python3 {SKILL_PATH}/hooks/scripts/credential_manager.py validate --org-alias {org} --eca-name {eca}

# Source credentials for shell use (set -a auto-exports all vars)
set -a; source ~/.sfagent/{org}/{eca}/credentials.env; set +a
```
