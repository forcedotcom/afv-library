<!-- Parent: sf-metadata/SKILL.md -->
# Salesforce CLI Commands Reference

## Overview

This guide covers sf CLI v2 commands for metadata operations, org queries, and deployment tasks.

---

## Authentication

### Authorize an Org
```bash
# Web login (interactive)
sf org login web --alias myorg

# JWT flow (CI/CD)
sf org login jwt \
  --client-id <client_id> \
  --jwt-key-file server.key \
  --username user@example.com \
  --alias myorg

# SFDX Auth URL (from file)
sf org login sfdx-url --sfdx-url-file authFile.txt --alias myorg
```

### List Connected Orgs
```bash
sf org list

# With details
sf org list --verbose
```

### Display Org Info
```bash
sf org display --target-org myorg

# JSON output
sf org display --target-org myorg --json
```

---

## Object & Field Queries

### Describe an Object
```bash
# Standard or custom object
sf sobject describe --sobject Account --target-org myorg

# JSON output (for parsing)
sf sobject describe --sobject Account --target-org myorg --json

# Tooling API object
sf sobject describe --sobject ApexClass --target-org myorg --use-tooling-api
```

### List Objects
```bash
# All objects
sf sobject list --target-org myorg --sobject all

# Custom objects only
sf sobject list --target-org myorg --sobject custom

# Standard objects only
sf sobject list --target-org myorg --sobject standard
```

### Parse Object Fields (with jq)
```bash
# List all field names
sf sobject describe --sobject Account --target-org myorg --json | \
  jq -r '.result.fields[].name'

# List custom fields only
sf sobject describe --sobject Account --target-org myorg --json | \
  jq -r '.result.fields[] | select(.custom == true) | .name'

# Get field details
sf sobject describe --sobject Account --target-org myorg --json | \
  jq '.result.fields[] | {name, type, length, label}'
```

---

## Metadata Operations

### List Metadata Types
```bash
# All available metadata types
sf org list metadata-types --target-org myorg

# JSON output
sf org list metadata-types --target-org myorg --json
```

### List Metadata of a Type
```bash
# Custom Objects
sf org list metadata --metadata-type CustomObject --target-org myorg

# Custom Fields (specify folder/object)
sf org list metadata --metadata-type CustomField --folder Account --target-org myorg

# Profiles
sf org list metadata --metadata-type Profile --target-org myorg

# Permission Sets
sf org list metadata --metadata-type PermissionSet --target-org myorg

# Flows
sf org list metadata --metadata-type Flow --target-org myorg

# Apex Classes
sf org list metadata --metadata-type ApexClass --target-org myorg
```

---

## Retrieve Metadata

### Retrieve by Metadata Type
```bash
# Single type
sf project retrieve start --metadata CustomObject:Account --target-org myorg

# Multiple items
sf project retrieve start \
  --metadata CustomObject:Account \
  --metadata CustomObject:Contact \
  --target-org myorg

# Wildcard (all of type)
sf project retrieve start --metadata "CustomObject:*" --target-org myorg
```

### Retrieve from Manifest (package.xml)
```bash
sf project retrieve start --manifest manifest/package.xml --target-org myorg
```

### Retrieve to Specific Directory
```bash
sf project retrieve start \
  --metadata CustomObject:Account \
  --target-org myorg \
  --output-dir ./retrieved
```

---

## Deploy Metadata

### Deploy Source Directory
```bash
# Deploy all source
sf project deploy start --source-dir force-app --target-org myorg

# Dry run (validation only)
sf project deploy start --source-dir force-app --target-org myorg --dry-run

# With specific test level
sf project deploy start \
  --source-dir force-app \
  --target-org myorg \
  --test-level RunLocalTests
```

### Deploy Specific Metadata
```bash
sf project deploy start \
  --metadata CustomObject:Invoice__c \
  --target-org myorg
```

### Deploy from Manifest
```bash
sf project deploy start --manifest manifest/package.xml --target-org myorg
```

### Check Deploy Status
```bash
# Poll for status
sf project deploy report --job-id <jobId>

# Resume watching
sf project deploy resume --job-id <jobId>
```

### Test Levels
| Level | Description |
|-------|-------------|
| `NoTestRun` | No tests (sandbox only) |
| `RunSpecifiedTests` | Run specific tests |
| `RunLocalTests` | Run org tests (non-managed) |
| `RunAllTestsInOrg` | Run all tests |

---

## Generate Metadata

### Generate Custom Object
```bash
sf schema generate sobject --label "My Object"
```

### Generate Custom Field
```bash
sf schema generate field --label "My Field" --object Account
```

### Generate Package.xml
```bash
# From source directory
sf project generate manifest --source-dir force-app --name package.xml

# From org metadata
sf project generate manifest \
  --from-org myorg \
  --metadata-type CustomObject \
  --name package.xml
```

---

## Data Operations

### Query Records (SOQL)
```bash
# Simple query
sf data query --query "SELECT Id, Name FROM Account LIMIT 10" --target-org myorg

# Export to CSV
sf data query \
  --query "SELECT Id, Name FROM Account" \
  --target-org myorg \
  --result-format csv > accounts.csv

# Bulk export (large data, > 2,000 records)
sf data export bulk \
  --query "SELECT Id, Name FROM Account" \
  --target-org myorg \
  --output-file accounts.csv
```

### Import/Export Records
```bash
# Export to JSON
sf data export tree \
  --query "SELECT Id, Name, Industry FROM Account WHERE Industry != null" \
  --target-org myorg \
  --output-dir ./data

# Import from JSON
sf data import tree --files data/Account.json --target-org myorg
```

---

## Apex Operations

### Execute Anonymous Apex
```bash
# From command line
sf apex run --target-org myorg --file scripts/anonymous.apex

# Interactive
sf apex run --target-org myorg
```

### Run Tests
```bash
# All local tests
sf apex run test --target-org myorg --test-level RunLocalTests

# Specific test class
sf apex run test --target-org myorg --tests MyTestClass

# Specific test method
sf apex run test --target-org myorg --tests MyTestClass.testMethod

# With code coverage
sf apex run test --target-org myorg --code-coverage --test-level RunLocalTests
```

---

## Useful Patterns

### Check Object Exists
```bash
sf sobject describe --sobject MyObject__c --target-org myorg --json | \
  jq -r '.status'
# Returns 0 if exists, 1 if not
```

### Get Field API Names
```bash
sf sobject describe --sobject Account --target-org myorg --json | \
  jq -r '.result.fields[].name' | sort
```

### Get Custom Field Count
```bash
sf sobject describe --sobject Account --target-org myorg --json | \
  jq '[.result.fields[] | select(.custom == true)] | length'
```

### List All Custom Objects
```bash
sf org list metadata --metadata-type CustomObject --target-org myorg --json | \
  jq -r '.result[].fullName' | grep '__c$'
```

### Validate Deployment
```bash
sf project deploy start \
  --source-dir force-app \
  --target-org myorg \
  --dry-run \
  --test-level RunLocalTests \
  --json | jq '.result.status'
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SF_TARGET_ORG` | Default target org |
| `SF_ACCESS_TOKEN` | Auth token |
| `SF_INSTANCE_URL` | Instance URL |
| `SF_API_VERSION` | API version |

---

## Common Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--target-org` | `-o` | Target org alias |
| `--json` | | JSON output |
| `--wait` | `-w` | Wait time (minutes) |
| `--verbose` | | Verbose output |
| `--help` | `-h` | Show help |

---

## Quick Reference

### Daily Operations
```bash
# Check org
sf org display -o myorg

# Deploy changes
sf project deploy start -d force-app -o myorg

# Run tests
sf apex run test -o myorg -l RunLocalTests -c

# Query data
sf data query -q "SELECT Id FROM Account LIMIT 1" -o myorg
```

### Metadata Discovery
```bash
# What's in the org?
sf org list metadata-types -o myorg

# What objects exist?
sf sobject list -o myorg --sobject all

# Describe an object
sf sobject describe -s Account -o myorg
```

### CI/CD Pipeline
```bash
# Authenticate
sf org login jwt ...

# Validate
sf project deploy start -d force-app -o myorg --dry-run -l RunLocalTests

# Deploy
sf project deploy start -d force-app -o myorg -l RunLocalTests

# Run additional tests
sf apex run test -o myorg -l RunLocalTests -c -r human
```
