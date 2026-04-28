#!/usr/bin/env bash
# ============================================================================
# Agent Script LSP Wrapper for sf-skills Plugin
# ============================================================================
# This script discovers and invokes the Salesforce Agent Script Language Server
# using a cache-first discovery model:
#
#   1. Local cache   ~/.claude/lsp-engine/servers/agentscript/server.js
#                    (downloaded via lsp-acquire.py — no VS Code needed)
#   2. Env var       AGENTSCRIPT_LSP_SERVER=/path/to/server.js
#   3. VS Code       ~/.vscode/extensions/salesforce.agent-script-language-client-*
#                    (fallback for users with VS Code installed)
#
# Prerequisites:
#   - Node.js 18+ installed
#   - One of: lsp-acquire.py cache, AGENTSCRIPT_LSP_SERVER env var, or VS Code extension
#
# Usage:
#   ./agentscript_wrapper.sh [--stdio]
#
# Environment:
#   AGENTSCRIPT_LSP_SERVER - Direct path to server.js (optional, skips discovery)
#   LSP_LOG_FILE           - Path to log file (optional, default: /dev/null)
#   NODE_PATH              - Custom Node.js binary path (optional, auto-detected)
# ============================================================================

set -euo pipefail

# Source VS Code extension directory discovery
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_vscode_common.sh"

# Configuration
LOG_FILE="${LSP_LOG_FILE:-/dev/null}"
NODE_BIN="${NODE_PATH:-}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [lsp-engine] $*" >> "$LOG_FILE"
}

# Find Node.js binary
find_node() {
    if [[ -n "$NODE_BIN" ]] && [[ -x "$NODE_BIN" ]]; then
        echo "$NODE_BIN"
        return 0
    fi

    # Try common locations (cross-platform)
    local candidates=(
        "$(which node 2>/dev/null || true)"
        "/usr/local/bin/node"
        "/opt/homebrew/bin/node"
        "$HOME/.nvm/current/bin/node"
        "$HOME/.volta/bin/node"
        "/usr/bin/node"
    )

    for candidate in "${candidates[@]}"; do
        if [[ -n "$candidate" ]] && [[ -x "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

# Discover AgentScript LSP server: cache → env var → VS Code extension
find_vscode_extension() {
    # 1. Check local cache (downloaded via lsp-acquire.py)
    local cached_server="$SCRIPT_DIR/servers/agentscript/server.js"
    if [[ -f "$cached_server" ]]; then
        log "Using cached AgentScript LSP: $cached_server"
        echo "$cached_server"
        return 0
    fi

    # 2. Check env var override
    if [[ -n "${AGENTSCRIPT_LSP_SERVER:-}" ]] && [[ -f "$AGENTSCRIPT_LSP_SERVER" ]]; then
        log "Using AGENTSCRIPT_LSP_SERVER: $AGENTSCRIPT_LSP_SERVER"
        echo "$AGENTSCRIPT_LSP_SERVER"
        return 0
    fi

    # 3. Fall back to VS Code extension directories
    local ext_base
    local pattern="salesforce.agent-script-language-client-*"

    if ! ext_base=$(find_vscode_ext_dir); then
        log "No cached server, no AGENTSCRIPT_LSP_SERVER, and no VS Code extensions directory found."
        return 1
    fi

    # Find the newest version (sort by version number)
    local latest
    latest=$(find "$ext_base" -maxdepth 1 -type d -name "$pattern" 2>/dev/null | sort -V | tail -1)

    if [[ -n "$latest" ]] && [[ -f "$latest/server/server.js" ]]; then
        echo "$latest/server/server.js"
        return 0
    fi

    log "Agent Script extension not found in: $ext_base (set VSCODE_EXTENSIONS_DIR to override)"
    return 1
}

# Validate Node.js version (requires 18+)
validate_node_version() {
    local node_bin="$1"
    local version_output
    version_output=$("$node_bin" --version 2>/dev/null)

    # Extract major version (v22.21.0 -> 22)
    local major_version
    major_version=$(echo "$version_output" | grep -oE 'v([0-9]+)' | head -1 | tr -d 'v')

    if [[ -z "$major_version" ]]; then
        log "WARNING: Could not determine Node.js version"
        return 0  # Continue anyway
    fi

    if [[ "$major_version" -lt 18 ]]; then
        log "ERROR: Node.js 18+ required (found v$major_version)"
        echo "Error: Node.js 18+ required (found $version_output)" >&2
        return 1
    fi

    log "Node.js version: $version_output"
    return 0
}

# Main execution
main() {
    log "=== Agent Script LSP Wrapper Starting ==="

    # Find Node.js
    local node_bin
    if ! node_bin=$(find_node); then
        echo "Error: Node.js not found. Please install Node.js 18+." >&2
        log "ERROR: Node.js not found"
        exit 1
    fi
    log "Using Node.js: $node_bin"

    # Validate Node.js version
    if ! validate_node_version "$node_bin"; then
        exit 1
    fi

    # Discover LSP server (cache → env var → VS Code)
    local server_path
    if ! server_path=$(find_vscode_extension); then
        echo "Error: Agent Script LSP server not found." >&2
        echo "" >&2
        echo "Option 1 — Download directly (no VS Code needed):" >&2
        echo "  python3 ~/.claude/lsp-engine/lsp-acquire.py agentscript" >&2
        echo "" >&2
        echo "Option 2 — Point to an existing server:" >&2
        echo "  export AGENTSCRIPT_LSP_SERVER=/path/to/server.js" >&2
        echo "" >&2
        echo "Option 3 — Install VS Code Agent Script extension:" >&2
        echo "  code --install-extension salesforce.agent-script-language-client" >&2
        exit 1
    fi
    log "Server path: $server_path"

    # Execute the LSP server with stdio transport
    log "Starting LSP server..."
    exec "$node_bin" "$server_path" --stdio "$@"
}

main "$@"
