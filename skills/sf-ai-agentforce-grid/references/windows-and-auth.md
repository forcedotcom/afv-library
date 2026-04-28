# Windows And Auth

## Auth Checklist

Use this sequence before any serious Grid work:

1. `sf org list --json`
2. If that fails with `NoDefaultEnvError`, run `sf org list --json`
3. Pick the correct alias and run `sf config set target-org <alias>`
4. Re-run `sf org list --json`

## Common Windows Problems

### `curl ... | bash` fails

Typical cause:

- `bash.exe` is only the WSL launcher
- no Linux distro is installed

Correct response:

- do the installation natively in PowerShell
- clone/build repos directly
- update Codex/Claude config files directly

### `sf api request rest --body ...` fails with `JSON_PARSER_ERROR`

This is a practical Windows/PowerShell quoting problem.

Do not waste time trying many quote variants.

Preferred fallback:

- use the Grid MCP if available
- otherwise use `scripts/grid_api_request.mjs`

## Direct REST Fallback

The bundled helper script delegates authentication to Salesforce CLI and sends JSON through a safe request spec rather than shell-built command strings. This avoids PowerShell quoting issues without pulling access tokens into Node directly.

Example:

```powershell
node scripts/grid_api_request.mjs GET /workbooks
node scripts/grid_api_request.mjs POST /workbooks "{""name"":""My Grid Workbook""}"
```

Target a specific org alias:

```powershell
node scripts/grid_api_request.mjs GET /llm-models --target-org sdo5
```

## MCP Config Notes

Per-project `.mcp.json` is a good place to wire the Grid MCP for Codex.

Typical shape:

```json
{
  "mcpServers": {
    "grid-connect": {
      "command": "node",
      "args": ["C:\\Users\\<user>\\.agentforce-grid\\agentforce-grid-mcp\\dist\\index.js"]
    }
  }
}
```

If Salesforce CLI has no default org, the MCP may exist but still fail at runtime.

## Verification Commands

Use one of these to prove the org and Grid API are alive:

```powershell
sf org list --json
node scripts/grid_api_request.mjs GET /workbooks
node scripts/grid_api_request.mjs GET /llm-models
node scripts/grid_api_request.mjs GET /agents
```
