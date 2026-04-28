#!/usr/bin/env bash
# ============================================================================
# VS Code Extension Directory Discovery (Internal Utility)
# ============================================================================
# Sourceable utility that resolves the VS Code extensions directory across
# desktop, remote-SSH, WSL, Insiders, and Cursor IDE installations.
#
# Usage:
#   source "$(dirname "$0")/_vscode_common.sh"
#   ext_base=$(find_vscode_ext_dir) || { echo "not found"; exit 1; }
#
# Override:
#   export VSCODE_EXTENSIONS_DIR=/custom/path   # skips auto-detection
# ============================================================================

# Discover the first existing VS Code extensions directory.
# Prints the path and returns 0 on success, returns 1 if none found.
find_vscode_ext_dir() {
    local candidates=(
        "${VSCODE_EXTENSIONS_DIR:-}"                      # User override
        "$HOME/.vscode/extensions"                        # Desktop
        "$HOME/.vscode-server/extensions"                 # Remote SSH / WSL
        "$HOME/.vscode-insiders/extensions"               # Insiders desktop
        "$HOME/.vscode-server-insiders/extensions"        # Insiders remote
        "$HOME/.cursor/extensions"                        # Cursor IDE
    )

    for dir in "${candidates[@]}"; do
        if [[ -n "$dir" ]] && [[ -d "$dir" ]]; then
            echo "$dir"
            return 0
        fi
    done

    return 1
}
