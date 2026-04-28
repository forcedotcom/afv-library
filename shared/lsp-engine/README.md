# LSP Engine for sf-skills

Language Server Protocol integration for Salesforce development skills in Claude Code.

## Overview

This module provides a shared LSP engine that enables real-time validation of Salesforce files during Claude Code authoring sessions. Currently supports:

- **Agent Script** (`.agent` files) - via direct download or VS Code extension
- **Apex** (`.cls`, `.trigger` files) - via direct download or VS Code extension
- **LWC** (`.js`, `.html` files) - via standalone npm package

## Architecture: Cache-First Discovery

Each wrapper script discovers its LSP server using a 3-tier priority chain:

```
Discovery order (per wrapper):
  1. Local cache    ~/.claude/lsp-engine/servers/{apex,agentscript}/
                    Downloaded via lsp-acquire.py — no VS Code needed
  2. Env var        APEX_LSP_JAR / AGENTSCRIPT_LSP_SERVER
                    Direct path override for custom setups
  3. VS Code dirs   ~/.vscode/extensions/ etc.
                    Fallback for users with VS Code installed
  4. Error          Suggests running lsp-acquire.py
```

This means **VS Code is optional** — the installer automatically downloads LSP servers from the VS Code Marketplace during install, or you can run `lsp-acquire.py` manually.

## Prerequisites

### Quick Reference

| Language | VS Code Required? | Standalone? |
|----------|-------------------|-------------|
| **LWC** | ❌ No | ✅ `npm install -g @salesforce/lwc-language-server` |
| **Apex** | ❌ No | ✅ `python3 lsp-acquire.py apex` (or VS Code) |
| **Agent Script** | ❌ No | ✅ `python3 lsp-acquire.py agentscript` (or VS Code) |

### Runtimes

- **Java 11+** — Required for Apex LSP (`brew install openjdk@21`)
- **Node.js 18+** — Required for Agent Script and LWC LSPs (`brew install node`)

### For LWC (.js, .html files) - npm Package

LWC has a standalone npm package (no download tool needed):

```bash
npm install -g @salesforce/lwc-language-server
```

### For Apex & Agent Script - Direct Download (Recommended)

The installer automatically downloads LSP servers. To manually download or update:

```bash
# Download all servers
python3 ~/.claude/lsp-engine/lsp-acquire.py

# Download specific server
python3 ~/.claude/lsp-engine/lsp-acquire.py apex
python3 ~/.claude/lsp-engine/lsp-acquire.py agentscript

# Check what would be downloaded (dry-run)
python3 ~/.claude/lsp-engine/lsp-acquire.py --check

# Show current cache status
python3 ~/.claude/lsp-engine/lsp-acquire.py --status

# Force re-download (e.g., after extension update)
python3 ~/.claude/lsp-engine/lsp-acquire.py --force
```

### For Apex & Agent Script - VS Code (Alternative)

If you already have VS Code with Salesforce extensions installed, the wrappers will find them automatically as a fallback. No additional setup needed.

## Usage

### In Hooks (Recommended)

```python
#!/usr/bin/env python3
import sys
import json
sys.path.insert(0, str(Path.home() / ".claude" / "lsp-engine"))

from lsp_client import get_diagnostics
from diagnostics import format_diagnostics_for_claude

# Read hook input
hook_input = json.load(sys.stdin)
file_path = hook_input.get("tool_input", {}).get("file_path", "")

# Validate .agent files
if file_path.endswith(".agent"):
    result = get_diagnostics(file_path)
    output = format_diagnostics_for_claude(result)
    if output:
        print(output)
```

### Standalone CLI

```bash
# Test LSP validation
python3 lsp_client.py /path/to/file.agent
```

## Module Structure

```
lsp-engine/
├── __init__.py              # Package exports
├── _vscode_common.sh        # VS Code extension dir discovery (sourced by wrappers)
├── agentscript_wrapper.sh   # Shell wrapper for Agent Script LSP
├── apex_wrapper.sh          # Shell wrapper for Apex LSP
├── lwc_wrapper.sh           # Shell wrapper for LWC LSP
├── lsp-acquire.py           # Direct download tool (VS Code Marketplace → local cache)
├── check_lsp_versions.sh    # Environment version checker
├── lsp_client.py            # Python LSP client (multi-language)
├── diagnostics.py           # Diagnostic formatting
├── servers/                 # Downloaded LSP server cache (auto-created)
│   ├── manifest.json        # Version tracking (schema_version, SHA256, timestamps)
│   ├── apex/                # Cached Apex LSP (apex-jorje-lsp.jar)
│   └── agentscript/         # Cached AgentScript LSP (server.js + node_modules)
└── README.md                # This file
```

## `servers/manifest.json` Format

The manifest tracks which LSP servers have been downloaded and their versions:

```json
{
  "schema_version": 1,
  "servers": {
    "apex": {
      "extension_id": "salesforce.salesforcedx-vscode-apex",
      "extension_version": "62.10.0",
      "vsix_sha256": "a1b2c3d4...",
      "acquired_at": "2026-03-02T14:30:00Z"
    },
    "agentscript": {
      "extension_id": "salesforce.agent-script-language-client",
      "extension_version": "1.3.0",
      "vsix_sha256": "e5f6g7h8...",
      "acquired_at": "2026-03-02T14:31:00Z"
    }
  }
}
```

The `servers/` directory is preserved across `install.py --update` runs to avoid
re-downloading large binaries (~50MB+).

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APEX_LSP_JAR` | Direct path to apex-jorje-lsp.jar (skips discovery) | — |
| `AGENTSCRIPT_LSP_SERVER` | Direct path to server.js (skips discovery) | — |
| `VSCODE_EXTENSIONS_DIR` | Override VS Code extensions directory | Auto-detected (see below) |
| `LSP_LOG_FILE` | Path to log file | `/dev/null` |
| `NODE_PATH` | Custom Node.js path (Agent Script) | Auto-detected |
| `JAVA_HOME` | Custom Java path (Apex) | Auto-detected |
| `APEX_LSP_MEMORY` | JVM heap size in MB (Apex) | 2048 |

### VS Code Extension Directory Discovery (Fallback)

When no cached server or env var is set, the shell wrappers search for VS Code extensions:

1. `$VSCODE_EXTENSIONS_DIR` (user override)
2. `~/.vscode/extensions/` (VS Code desktop)
3. `~/.vscode-server/extensions/` (VS Code remote SSH / WSL)
4. `~/.vscode-insiders/extensions/` (VS Code Insiders desktop)
5. `~/.vscode-server-insiders/extensions/` (VS Code Insiders remote)
6. `~/.cursor/extensions/` (Cursor IDE)

## Environment Health Check

The LSP engine includes a version checker that monitors your development environment and alerts you when updates are available.

### What It Checks

| Component | Source | Minimum | Recommended |
|-----------|--------|---------|-------------|
| **LSP Servers** | | | |
| └─ Apex LSP | Cache or VS Code | - | Latest |
| └─ LWC LSP | VS Code Marketplace | - | Latest |
| └─ Agent Script LSP | Cache or VS Code | - | Latest |
| **Runtimes** | | | |
| └─ Java | Local install | 11 | 21 LTS |
| └─ Node.js | Local install | 18 | 22 LTS |
| **Salesforce CLI** | npm registry | - | Latest stable |

The version checker shows a **Source** column for LSP servers indicating whether they're loaded from `cache` (lsp-acquire.py) or `vscode` (VS Code extension directory).

### Automatic Checks (Weekly)

The environment check runs automatically via a SessionStart hook when you use sf-skills. It:

1. **Caches results** for 7 days to avoid excessive API calls
2. **Runs silently** if everything is current
3. **Shows warnings** only when updates are available or cache is stale

Cache location: `~/.cache/sf-skills/version_check.json`

### Manual Usage

```bash
# Run with cached results (if fresh)
./check_lsp_versions.sh

# Force refresh (ignore cache)
./check_lsp_versions.sh --force

# Quiet mode (exit code only: 0=current, 1=updates available)
./check_lsp_versions.sh --quiet

# JSON output (for scripting)
./check_lsp_versions.sh --json
```

### Sample Output

```
🔍 SF-SKILLS ENVIRONMENT CHECK (cached 2 days ago)
════════════════════════════════════════════════════════════════

📦 LSP SERVERS
──────────────────────────────────┬────────────┬──────────┬────────┬────────
Component                         │ Installed  │ Latest   │ Source │ Status
──────────────────────────────────┼────────────┼──────────┼────────┼────────
salesforce.salesforcedx-vscode-ape│ 62.10.0    │ 62.10.0  │ cache  │ ✅
salesforce.agent-script-language-c│ 1.2.0      │ 1.2.0    │ vscode │ ✅

⚙️  RUNTIMES
───────────────────────────────────────┬────────────┬──────────┬────────
Component                              │ Installed  │ Latest   │ Status
───────────────────────────────────────┼────────────┼──────────┼────────
Java                                   │ 21         │ 21 LTS   │ ✅
Node.js                                │ 22         │ 22 LTS   │ ✅

🛠️  SALESFORCE CLI
───────────────────────────────────────┬────────────┬──────────┬────────
Component                              │ Installed  │ Latest   │ Status
───────────────────────────────────────┼────────────┼──────────┼────────
sf (@salesforce/cli)                   │ 2.75.0     │ 2.75.0   │ ✅

════════════════════════════════════════════════════════════════
🔄 Next check: Mar 09, 2026 (or run with --force)
```

### Disabling Automatic Checks

To disable the weekly check, remove the `SessionStart` hook from your skill's `hooks.json`:

```json
{
  "hooks": {
    "SessionStart": []  // Empty array disables
  }
}
```

## Troubleshooting

### Agent Script Issues

#### "LSP server not found"

Try these in order:

1. **Download directly** (recommended): `python3 ~/.claude/lsp-engine/lsp-acquire.py agentscript`
2. **Point to existing server**: `export AGENTSCRIPT_LSP_SERVER=/path/to/server.js`
3. **Install VS Code extension**: `code --install-extension salesforce.agent-script-language-client`

#### "Node.js not found"

Install Node.js 18+:
- macOS: `brew install node`
- Or download from https://nodejs.org

#### "Node.js version too old"

Upgrade to Node.js 18+:
- macOS: `brew upgrade node`

### Apex Issues

#### "Apex Language Server not found"

Try these in order:

1. **Download directly** (recommended): `python3 ~/.claude/lsp-engine/lsp-acquire.py apex`
2. **Point to existing JAR**: `export APEX_LSP_JAR=/path/to/apex-jorje-lsp.jar`
3. **Install VS Code extension**: `code --install-extension salesforce.salesforcedx-vscode-apex`

#### "Java not found"

Install Java 11+:
- macOS: `brew install openjdk@11`
- Or download from https://adoptium.net/temurin/releases/

#### "Java version too old"

Upgrade to Java 11+:
- macOS: `brew install openjdk@21`
- Set JAVA_HOME: `export JAVA_HOME=/opt/homebrew/opt/openjdk@21`

### LWC Issues

#### "LWC Language Server not found"

The standalone npm package is not installed:
```bash
npm install -g @salesforce/lwc-language-server
```

Verify installation:
```bash
which lwc-language-server
# Should return: /opt/homebrew/bin/lwc-language-server (or similar)
```

**Note:** Unlike Apex and Agent Script, LWC does NOT require VS Code or lsp-acquire.py. The npm package works standalone.

#### "Node.js not found" or "Node.js version too old"

Same as Agent Script - install/upgrade Node.js 18+.

## How It Works

```
1. Hook triggers after Write/Edit on supported file
         │
         ▼
2. lsp_client.py detects language from extension
   (.agent → agentscript, .cls → apex, .js/.html → lwc)
         │
         ▼
3. Spawns appropriate LSP server via wrapper script
   - agentscript_wrapper.sh for .agent
   - apex_wrapper.sh for .cls/.trigger
   - lwc_wrapper.sh for .js/.html (LWC)
         │
         ▼
   Wrapper discovers server: cache → env var → VS Code → error
         │
         ▼
4. Sends textDocument/didOpen with file content
         │
         ▼
5. Parses textDocument/publishDiagnostics response
         │
         ▼
6. Formats errors for Claude → Auto-fix loop
```

## License

MIT - See LICENSE file in repository root.
