<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Key Insights & Troubleshooting

| Problem | Symptom | Solution |
|---------|---------|----------|
| **`sf agent test create` fails** | "Required fields are missing: [MasterLabel]" | Add `name:` field to top of YAML spec (see Phase B1) |
| Tests fail silently | No results returned | Agent not published - run `sf agent publish authoring-bundle` |
| Topic not matched | Wrong topic selected | Add keywords to topic description |
| Action not invoked | Action never called | Improve action description |
| Live preview 401 | Authentication error | Re-authenticate: `sf org login web` |
| API 401 | Token expired or wrong credentials | Re-authenticate ECA |
| API 404 on session create | Wrong Agent ID | Re-query BotDefinition for correct Id |
| Empty API response | Agent not activated | Activate and publish agent |
| Context lost between turns | Agent re-asks for known info | Add context retention instructions to topic |
| Topic doesn't switch | Agent stays on old topic | Add transition phrases to target topic |
| **⚠️ `--use-most-recent` broken on `test results`** | **"Nonexistent flag" error (confirmed v2.123.1)** | **Use `--job-id` explicitly, or use `test resume --use-most-recent` (works)** |
| **Topic name mismatch** | **Expected `GeneralCRM`, got `MigrationDefaultTopic`** | **Verify actual topic names from first test run** |
| **Action superset matching** | **Expected `[A]`, actual `[A,B]` but PASS** | **CLI uses SUPERSET logic** |
