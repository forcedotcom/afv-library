#!/usr/bin/env bash
# ============================================================================
# Apex Language Server Wrapper for sf-skills Plugin
# ============================================================================
# This script discovers and invokes the Salesforce Apex Language Server
# (apex-jorje-lsp.jar) using a cache-first discovery model:
#
#   1. Local cache   ~/.claude/lsp-engine/servers/apex/apex-jorje-lsp.jar
#                    (downloaded via lsp-acquire.py — no VS Code needed)
#   2. Env var       APEX_LSP_JAR=/path/to/apex-jorje-lsp.jar
#   3. VS Code       ~/.vscode/extensions/salesforce.salesforcedx-vscode-apex-*
#                    (fallback for users with VS Code installed)
#
# Prerequisites:
#   - Java 11+ installed (Adoptium/OpenJDK recommended)
#   - One of: lsp-acquire.py cache, APEX_LSP_JAR env var, or VS Code extension
#
# Usage:
#   ./apex_wrapper.sh [--stdio]
#
# Environment:
#   APEX_LSP_JAR    - Direct path to apex-jorje-lsp.jar (optional, skips discovery)
#   LSP_LOG_FILE    - Path to log file (optional, default: /dev/null)
#   JAVA_HOME       - Custom Java installation path (optional, auto-detected)
#   APEX_LSP_MEMORY - JVM heap size in MB (optional, default: 2048)
# ============================================================================

set -euo pipefail

# Source VS Code extension directory discovery
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_vscode_common.sh"

# Configuration
LOG_FILE="${LSP_LOG_FILE:-/dev/null}"
JAVA_HOME_OVERRIDE="${JAVA_HOME:-}"
JVM_MEMORY="${APEX_LSP_MEMORY:-2048}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [apex-lsp] $*" >> "$LOG_FILE"
}

# Find Java binary
find_java() {
    # Check JAVA_HOME first
    if [[ -n "$JAVA_HOME_OVERRIDE" ]] && [[ -x "$JAVA_HOME_OVERRIDE/bin/java" ]]; then
        echo "$JAVA_HOME_OVERRIDE/bin/java"
        return 0
    fi

    # Try common locations (cross-platform)
    # Note: Prioritize Homebrew OpenJDK over /usr/local/bin/java which may be a stub
    local candidates=(
        "/opt/homebrew/opt/openjdk@21/bin/java"
        "/opt/homebrew/opt/openjdk@17/bin/java"
        "/opt/homebrew/opt/openjdk@11/bin/java"
        "/opt/homebrew/opt/openjdk/bin/java"
        "$HOME/.sdkman/candidates/java/current/bin/java"
        "/Library/Java/JavaVirtualMachines/adoptium-21.jdk/Contents/Home/bin/java"
        "/Library/Java/JavaVirtualMachines/adoptium-17.jdk/Contents/Home/bin/java"
        "/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home/bin/java"
        "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home/bin/java"
        "/usr/bin/java"
        "/usr/local/bin/java"
    )

    for candidate in "${candidates[@]}"; do
        if [[ -n "$candidate" ]] && [[ -x "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

# Validate Java version (requires 11+)
validate_java_version() {
    local java_bin="$1"
    local version_output
    version_output=$("$java_bin" -version 2>&1 | head -1)

    # Extract version number (handles both "1.8.0_xxx" and "11.0.x" formats)
    local version
    version=$(echo "$version_output" | grep -oE '([0-9]+)(\.[0-9]+)*' | head -1)

    # Get major version
    local major_version
    if [[ "$version" == 1.* ]]; then
        # Old format: 1.8.0 -> 8
        major_version=$(echo "$version" | cut -d. -f2)
    else
        # New format: 11.0.x -> 11
        major_version=$(echo "$version" | cut -d. -f1)
    fi

    if [[ -z "$major_version" ]]; then
        log "WARNING: Could not determine Java version"
        return 0  # Continue anyway
    fi

    if [[ "$major_version" -lt 11 ]]; then
        log "ERROR: Java 11+ required (found version $version)"
        echo "Error: Java 11+ required (found $version_output)" >&2
        return 1
    fi

    log "Java version: $version (major: $major_version)"
    return 0
}

# Discover Apex LSP JAR: cache → env var → VS Code extension
find_apex_extension() {
    # 1. Check local cache (downloaded via lsp-acquire.py)
    local cached_jar="$SCRIPT_DIR/servers/apex/apex-jorje-lsp.jar"
    if [[ -f "$cached_jar" ]]; then
        log "Using cached Apex LSP: $cached_jar"
        echo "$cached_jar"
        return 0
    fi

    # 2. Check env var override
    if [[ -n "${APEX_LSP_JAR:-}" ]] && [[ -f "$APEX_LSP_JAR" ]]; then
        log "Using APEX_LSP_JAR: $APEX_LSP_JAR"
        echo "$APEX_LSP_JAR"
        return 0
    fi

    # 3. Fall back to VS Code extension directories
    local ext_base
    if ! ext_base=$(find_vscode_ext_dir); then
        log "No cached server, no APEX_LSP_JAR, and no VS Code extensions directory found."
        return 1
    fi

    # Find the main Apex extension (exclude -debugger, -testing, etc.)
    # Pattern: salesforce.salesforcedx-vscode-apex-VERSION (version starts with digit)
    local latest
    latest=$(find "$ext_base" -maxdepth 1 -type d -name "salesforce.salesforcedx-vscode-apex-[0-9]*" 2>/dev/null | sort -V | tail -1)

    if [[ -n "$latest" ]]; then
        # Check dist directory first (newer versions)
        local jar_path="$latest/dist/apex-jorje-lsp.jar"
        if [[ -f "$jar_path" ]]; then
            echo "$jar_path"
            return 0
        fi

        # Try out directory (older versions)
        jar_path="$latest/out/apex-jorje-lsp.jar"
        if [[ -f "$jar_path" ]]; then
            echo "$jar_path"
            return 0
        fi
    fi

    log "Apex extension not found in: $ext_base (set VSCODE_EXTENSIONS_DIR to override)"
    return 1
}

# Main execution
main() {
    log "=== Apex LSP Wrapper Starting ==="

    # Find Java
    local java_bin
    if ! java_bin=$(find_java); then
        echo "Error: Java not found. Please install Java 11+ (Adoptium recommended)." >&2
        echo "  Download: https://adoptium.net/temurin/releases/" >&2
        log "ERROR: Java not found"
        exit 1
    fi
    log "Using Java: $java_bin"

    # Validate Java version
    if ! validate_java_version "$java_bin"; then
        exit 1
    fi

    # Discover LSP server (cache → env var → VS Code)
    local jar_path
    if ! jar_path=$(find_apex_extension); then
        echo "Error: Apex Language Server not found." >&2
        echo "" >&2
        echo "Option 1 — Download directly (no VS Code needed):" >&2
        echo "  python3 ~/.claude/lsp-engine/lsp-acquire.py apex" >&2
        echo "" >&2
        echo "Option 2 — Point to an existing JAR:" >&2
        echo "  export APEX_LSP_JAR=/path/to/apex-jorje-lsp.jar" >&2
        echo "" >&2
        echo "Option 3 — Install VS Code Salesforce Extensions:" >&2
        echo "  code --install-extension salesforce.salesforcedx-vscode-apex" >&2
        exit 1
    fi
    log "JAR path: $jar_path"

    # Execute the Apex LSP server with stdio transport
    # JVM flags based on Salesforce recommendations:
    #   -Ddebug.internal.errors=true  : Report internal errors
    #   -Ddebug.semantic.errors=false : Disable semantic errors (faster)
    #   -Dlwc.typegeneration.disabled=true : Disable LWC type generation
    log "Starting Apex LSP server with ${JVM_MEMORY}MB heap..."
    exec "$java_bin" \
        -cp "$jar_path" \
        -Ddebug.internal.errors=true \
        -Ddebug.semantic.errors=false \
        -Ddebug.completion.statistics=false \
        -Dlwc.typegeneration.disabled=true \
        -Xmx${JVM_MEMORY}M \
        apex.jorje.lsp.ApexLanguageServerLauncher \
        "$@"
}

main "$@"
