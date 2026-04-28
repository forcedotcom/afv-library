# Upstream Distillation Map for sf-datacloud

This file exists to make downstream maintenance easy without sacrificing sf-skills consistency.

## Source repositories

### Skill concepts and phase model
- Repo: `gthoppae/sf-data360-skills`
- URL: https://github.com/gthoppae/sf-data360-skills
- Last reviewed commit for this integration: `0b446c4d245cef385c504d4677233e367fb87f36`

### CLI runtime and command surface
- Repo: `gthoppae/sf-cli-plugin-data360`
- URL: https://github.com/gthoppae/sf-cli-plugin-data360
- Last reviewed commit for this integration: `c3507ff593da82b3de51000ccbddcf979090e900`

## v0.0.7 review highlights

### Skills repo (`sf-data360-skills`)
- adds curated connector examples for SharePoint Unstructured, Snowflake, and Ingestion API
- adds Ingestion API schema-upload guidance for `connection schema-upsert`
- adds prepare-phase guidance for stream refresh behavior vs connection-level reruns
- adds ingestion example assets for sending records through the Ingestion API
- adds unstructured DLO guidance for UI-vs-CLI setup trade-offs

### Plugin repo (`sf-cli-plugin-data360`)
- improves `connection schema-get` output
- improves `connection test` name resolution for non-default connector types
- tightens `search-index config` argument handling
- adds `--raw` response output support on shared CRUD surfaces
- adds connector examples and bug-fix coverage in tests

## What sf-skills intentionally keeps

- the 7-part phase decomposition
- the community `sf data360` command surface as the runtime
- high-signal gotchas such as connector type requirements, `--all` pagination, API-version quirks, SQL-vs-SOQL distinctions, and connector-specific auth shapes
- deterministic JSON definition file patterns
- new upstream additions that are broadly useful, such as SharePoint Unstructured, Snowflake, Ingestion API, and unstructured-refresh guidance

## What sf-skills intentionally changes

- renames the family from `sf-data360-*` to `sf-datacloud-*`
- rewrites prompts into sf-skills house style
- keeps the plugin external instead of vendoring or forking it
- adds deterministic helper scripts and generic templates suited to sf-skills users
- avoids workshop-specific org names, payloads, and repo-coupled installation assumptions
- selectively distills public-safe example payloads and gotchas instead of copying workshop flows blindly
- does not automatically vendor UI-automation helpers unless they are validated and worth the maintenance cost

## Maintenance contract

When upstream changes, do **not** copy blindly.

Instead:
1. review new upstream commits
2. identify changed command behaviors, install patterns, or gotchas
3. update sf-skills prompts and templates in a distilled form
4. keep naming, attribution, and cross-skill boundaries consistent with sf-skills
5. update this file with the new reviewed commit SHAs

## High-priority upstream areas to re-check

- installation / linking workflow for the community plugin
- command counts and topic coverage
- API-version guidance
- known issues and bug-fix notes
- live-tested command set
- any new commands affecting Connect / Prepare / Harmonize / Segment / Act / Retrieve boundaries
- connector-specific payload examples worth distilling into generic repo-safe examples
- search-index / hybrid-search guidance and any command-surface changes around hybrid scoring or prefilter behavior
- Ingestion API schema-upload flow, send-data examples, and problem-record guidance
- unstructured-source setup differences between connection-level reruns, stream refreshes, and initial UI seeding
- UI-only gaps where upstream introduces browser automation; validate before importing

## Cross-skill boundary reminders

Keep Data Cloud product work in `sf-datacloud-*`, but do not blur into:
- `sf-ai-agentforce-observability` for STDM/session tracing/parquet workflows
- `sf-soql` for CRM SOQL-only tasks
- `sf-data` for CRM record seeding/cleanup
- `sf-metadata` for CRM schema creation

## Local helper files in this family

- `references/plugin-setup.md`
- `scripts/bootstrap-plugin.sh`
- `scripts/verify-plugin.sh`
- `assets/definitions/`

These are sf-skills-owned conveniences and should evolve independently from upstream when that improves user experience.
