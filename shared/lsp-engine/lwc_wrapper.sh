#!/bin/bash
# LWC Language Server wrapper for Claude Code LSP integration
#
# REQUIRES: npm install -g @salesforce/lwc-language-server
#
# Unlike Apex and Agent Script LSPs, the LWC Language Server is available
# as a standalone npm package and does NOT require VS Code.
#
# The VS Code bundled version (dist/lwcServer.js) has VS Code-specific
# dependencies that don't work standalone, so we only support the npm package.

set -e

# Log file for debugging (optional)
LOG_FILE="${LSP_LOG_FILE:-/dev/null}"

# Check for standalone npm package
if ! command -v lwc-language-server &> /dev/null; then
    echo "Error: LWC Language Server not found." >&2
    echo "" >&2
    echo "Install with:" >&2
    echo "  npm install -g @salesforce/lwc-language-server" >&2
    echo "" >&2
    echo "Note: Unlike Apex/Agent Script, LWC LSP does NOT require VS Code." >&2
    exit 1
fi

# Launch the LWC language server with stdio transport
exec lwc-language-server --stdio 2>>"$LOG_FILE"
