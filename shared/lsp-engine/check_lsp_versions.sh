#!/usr/bin/env bash
# ============================================================================
# SF-Skills Environment Version Checker
# ============================================================================
# Checks installed versions of VS Code extensions, runtimes, and Salesforce CLI
# against the latest available versions. Results are cached for 7 days.
#
# Usage:
#   ./check_lsp_versions.sh           # Check versions (uses cache if fresh)
#   ./check_lsp_versions.sh --force   # Force refresh (ignore cache)
#   ./check_lsp_versions.sh --quiet   # Exit code only (0=current, 1=updates)
#   ./check_lsp_versions.sh --json    # Output as JSON
#
# Exit Codes:
#   0 - All versions current
#   1 - Updates available
#   2 - Error occurred
# ============================================================================

set -euo pipefail

# Source VS Code extension directory discovery
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_vscode_common.sh"

# Configuration
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/sf-skills"
CACHE_FILE="$CACHE_DIR/version_check.json"
TIMESTAMP_FILE="$CACHE_DIR/last_check_timestamp"
CACHE_TTL_DAYS=7
VSCODE_EXT_DIR="$(find_vscode_ext_dir 2>/dev/null || echo "$HOME/.vscode/extensions")"

# VS Code extensions to check (parallel arrays for portability)
EXTENSION_IDS=(
    "salesforce.salesforcedx-vscode-apex"
    "salesforce.salesforcedx-vscode-lwc"
    "salesforce.agent-script-language-client"
)
EXTENSION_NAMES=(
    "Apex LSP"
    "LWC LSP"
    "Agent Script LSP"
)

# Runtime recommendations
JAVA_MIN_VERSION=11
JAVA_REC_VERSION=21
NODE_MIN_VERSION=18
NODE_REC_VERSION=22

# Parse arguments
FORCE_REFRESH=false
QUIET_MODE=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)  FORCE_REFRESH=true; shift ;;
        --quiet)  QUIET_MODE=true; shift ;;
        --json)   JSON_OUTPUT=true; shift ;;
        *)        shift ;;
    esac
done

# Ensure cache directory exists
mkdir -p "$CACHE_DIR"

# ============================================================================
# Utility Functions
# ============================================================================

# Check if cache is fresh (less than 7 days old)
cache_is_fresh() {
    if [[ ! -f "$TIMESTAMP_FILE" ]]; then
        return 1
    fi

    local last_check
    last_check=$(cat "$TIMESTAMP_FILE")
    local now
    now=$(date +%s)
    local age_days=$(( (now - last_check) / 86400 ))

    [[ $age_days -lt $CACHE_TTL_DAYS ]]
}

# Get cache age in human-readable format
get_cache_age() {
    if [[ ! -f "$TIMESTAMP_FILE" ]]; then
        echo "never"
        return
    fi

    local last_check
    last_check=$(cat "$TIMESTAMP_FILE")
    local now
    now=$(date +%s)
    local age_secs=$(( now - last_check ))

    if [[ $age_secs -lt 3600 ]]; then
        echo "$(( age_secs / 60 )) minutes ago"
    elif [[ $age_secs -lt 86400 ]]; then
        echo "$(( age_secs / 3600 )) hours ago"
    else
        echo "$(( age_secs / 86400 )) days ago"
    fi
}

# Calculate next check date
get_next_check_date() {
    if [[ ! -f "$TIMESTAMP_FILE" ]]; then
        date "+%b %d, %Y"
        return
    fi

    local last_check
    last_check=$(cat "$TIMESTAMP_FILE")
    local next_check=$(( last_check + (CACHE_TTL_DAYS * 86400) ))

    # Cross-platform date formatting
    if [[ "$(uname)" == "Darwin" ]]; then
        date -r "$next_check" "+%b %d, %Y"
    else
        date -d "@$next_check" "+%b %d, %Y"
    fi
}

# Update timestamp
update_timestamp() {
    date +%s > "$TIMESTAMP_FILE"
}

# ============================================================================
# Version Detection Functions
# ============================================================================

# Get installed extension version and source (cache or vscode)
# Outputs: "version" on stdout; sets EXT_SOURCE_<sanitized_id> to "cache" or "vscode"
get_installed_extension_version() {
    local ext_id="$1"
    local sanitized_id
    sanitized_id=$(echo "$ext_id" | tr '.-' '__')

    # 1. Check local cache (servers/manifest.json)
    local manifest_file="$SCRIPT_DIR/servers/manifest.json"
    if [[ -f "$manifest_file" ]]; then
        # Map extension IDs to server names used in manifest
        local server_name=""
        case "$ext_id" in
            salesforce.salesforcedx-vscode-apex) server_name="apex" ;;
            salesforce.agent-script-language-client) server_name="agentscript" ;;
        esac

        if [[ -n "$server_name" ]]; then
            # Extract version from manifest using grep/sed (no jq dependency)
            # Look for the server block and extract extension_version
            local cached_version
            cached_version=$(grep -A5 "\"$server_name\"" "$manifest_file" 2>/dev/null \
                | grep '"extension_version"' \
                | sed 's/.*"\([0-9][0-9.]*\)".*/\1/' \
                | head -1)

            if [[ -n "$cached_version" ]]; then
                # Verify the actual server files exist
                local verify_ok=false
                case "$server_name" in
                    apex)        [[ -f "$SCRIPT_DIR/servers/apex/apex-jorje-lsp.jar" ]] && verify_ok=true ;;
                    agentscript) [[ -f "$SCRIPT_DIR/servers/agentscript/server.js" ]] && verify_ok=true ;;
                esac

                if $verify_ok; then
                    eval "EXT_SOURCE_${sanitized_id}=cache"
                    echo "$cached_version"
                    return
                fi
            fi
        fi
    fi

    # 2. Check VS Code extension directories
    local ext_dir
    ext_dir=$(find "$VSCODE_EXT_DIR" -maxdepth 1 -type d -name "${ext_id}-*" 2>/dev/null | sort -V | tail -1)

    if [[ -z "$ext_dir" ]]; then
        eval "EXT_SOURCE_${sanitized_id}=none"
        echo ""
        return
    fi

    eval "EXT_SOURCE_${sanitized_id}=vscode"
    # Extract version from directory name (e.g., salesforce.xxx-62.8.0 -> 62.8.0)
    basename "$ext_dir" | sed "s/${ext_id}-//"
}

# Query VS Code Marketplace for latest version
get_marketplace_version() {
    local ext_id="$1"
    local publisher="${ext_id%%.*}"
    local name="${ext_id#*.}"

    # VS Code Marketplace API (same as VS Code uses internally)
    local response
    response=$(curl -s --max-time 10 \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Accept: application/json;api-version=3.0-preview.1" \
        -d "{\"filters\":[{\"criteria\":[{\"filterType\":7,\"value\":\"$ext_id\"}]}],\"flags\":914}" \
        "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery" 2>/dev/null) || {
        echo ""
        return
    }

    # Extract version using sed (portable, no jq dependency)
    # Look for "version":"X.Y.Z" pattern
    echo "$response" | grep -oE '"version"\s*:\s*"[0-9]+\.[0-9]+\.[0-9]+"' | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/'
}

# Get installed Java version
get_java_version() {
    local java_bin=""

    # Find Java (same logic as apex_wrapper.sh)
    local candidates=(
        "${JAVA_HOME:-}/bin/java"
        "/opt/homebrew/opt/openjdk@21/bin/java"
        "/opt/homebrew/opt/openjdk@17/bin/java"
        "/opt/homebrew/opt/openjdk@11/bin/java"
        "/opt/homebrew/opt/openjdk/bin/java"
        "$HOME/.sdkman/candidates/java/current/bin/java"
        "/usr/bin/java"
        "/usr/local/bin/java"
    )

    for candidate in "${candidates[@]}"; do
        if [[ -n "$candidate" ]] && [[ -x "$candidate" ]]; then
            java_bin="$candidate"
            break
        fi
    done

    if [[ -z "$java_bin" ]]; then
        echo ""
        return
    fi

    # Get version
    local version_output
    version_output=$("$java_bin" -version 2>&1 | head -1)

    # Extract version (handles both 1.8.x and 11.0.x formats)
    local version
    version=$(echo "$version_output" | grep -oE '([0-9]+)(\.[0-9]+)*' | head -1)

    # Convert to major version
    if [[ "$version" == 1.* ]]; then
        echo "$version" | cut -d. -f2
    else
        echo "$version" | cut -d. -f1
    fi
}

# Get installed Node.js version
get_node_version() {
    local node_bin=""

    # Find Node.js (same logic as agentscript_wrapper.sh)
    node_bin=$(which node 2>/dev/null || true)

    if [[ -z "$node_bin" ]]; then
        local candidates=(
            "/opt/homebrew/bin/node"
            "/usr/local/bin/node"
            "$HOME/.nvm/current/bin/node"
            "$HOME/.volta/bin/node"
            "/usr/bin/node"
        )

        for candidate in "${candidates[@]}"; do
            if [[ -n "$candidate" ]] && [[ -x "$candidate" ]]; then
                node_bin="$candidate"
                break
            fi
        done
    fi

    if [[ -z "$node_bin" ]]; then
        echo ""
        return
    fi

    # Get major version (v22.12.0 -> 22)
    "$node_bin" --version 2>/dev/null | grep -oE 'v([0-9]+)' | head -1 | tr -d 'v'
}

# Get installed Salesforce CLI version
get_sf_version() {
    local sf_bin
    sf_bin=$(which sf 2>/dev/null || true)

    if [[ -z "$sf_bin" ]]; then
        echo ""
        return
    fi

    # Get version (outputs something like "@salesforce/cli/2.72.0 darwin-arm64 node-v22.12.0")
    sf --version 2>/dev/null | grep -oE '@salesforce/cli/[0-9]+\.[0-9]+\.[0-9]+' | head -1 | sed 's/@salesforce\/cli\///'
}

# Get latest SF CLI version from npm registry
get_latest_sf_version() {
    local response
    response=$(curl -s --max-time 10 "https://registry.npmjs.org/@salesforce/cli" 2>/dev/null) || {
        echo ""
        return
    }

    # Extract latest stable version (not rc or nightly)
    # Look for "latest":"X.Y.Z" in dist-tags
    echo "$response" | grep -oE '"latest"\s*:\s*"[0-9]+\.[0-9]+\.[0-9]+"' | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/'
}

# ============================================================================
# Version Comparison
# ============================================================================

# Compare semver versions (returns 0 if v1 >= v2, 1 otherwise)
version_gte() {
    local v1="$1"
    local v2="$2"

    # Handle empty versions
    [[ -z "$v1" ]] && return 1
    [[ -z "$v2" ]] && return 0

    # Use sort -V for version comparison
    local higher
    higher=$(printf '%s\n%s\n' "$v1" "$v2" | sort -V | tail -1)
    [[ "$v1" == "$higher" ]]
}

# Determine status based on versions
get_status() {
    local installed="$1"
    local latest="$2"

    if [[ -z "$installed" ]]; then
        echo "NOT_INSTALLED"
    elif [[ -z "$latest" ]]; then
        echo "UNKNOWN"
    elif version_gte "$installed" "$latest"; then
        echo "CURRENT"
    else
        echo "UPDATE"
    fi
}

# ============================================================================
# Output Functions
# ============================================================================

# Print table header
print_header() {
    local title="$1"
    local show_source="${2:-false}"
    echo ""
    echo "$title"
    if $show_source; then
        printf '──────────────────────────────────┬────────────┬──────────┬────────┬────────\n'
        printf '%-34s│ %-10s │ %-8s │ %-6s │ %s\n' "Component" "Installed" "Latest" "Source" "Status"
        printf '──────────────────────────────────┼────────────┼──────────┼────────┼────────\n'
    else
        printf '───────────────────────────────────────┬────────────┬──────────┬────────\n'
        printf '%-39s│ %-10s │ %-8s │ %s\n' "Component" "Installed" "Latest" "Status"
        printf '───────────────────────────────────────┼────────────┼──────────┼────────\n'
    fi
}

# Print table row
print_row() {
    local name="$1"
    local installed="$2"
    local latest="$3"
    local status="$4"
    local source="${5:-}"

    local status_icon
    case "$status" in
        CURRENT)       status_icon="✅" ;;
        UPDATE)        status_icon="⚠️ " ;;
        NOT_INSTALLED) status_icon="❌" ;;
        *)             status_icon="❓" ;;
    esac

    # Truncate name if too long
    local display_installed="${installed:-N/A}"
    local display_latest="${latest:-N/A}"

    if [[ -n "$source" ]]; then
        local display_name="${name:0:32}"
        printf '%-34s│ %-10s │ %-8s │ %-6s │ %s\n' "$display_name" "$display_installed" "$display_latest" "$source" "$status_icon"
    else
        local display_name="${name:0:37}"
        printf '%-39s│ %-10s │ %-8s │ %s\n' "$display_name" "$display_installed" "$display_latest" "$status_icon"
    fi
}

# ============================================================================
# Main Check Logic
# ============================================================================

run_checks() {
    local updates_available=false
    local results=()

    # Check VS Code extensions
    for i in "${!EXTENSION_IDS[@]}"; do
        local ext_id="${EXTENSION_IDS[$i]}"
        local display_name="${EXTENSION_NAMES[$i]}"
        local installed
        installed=$(get_installed_extension_version "$ext_id")
        local latest
        latest=$(get_marketplace_version "$ext_id")
        local status
        status=$(get_status "$installed" "$latest")

        # Retrieve the source that was set by get_installed_extension_version
        local sanitized_id
        sanitized_id=$(echo "$ext_id" | tr '.-' '__')
        local source_var="EXT_SOURCE_${sanitized_id}"
        local source="${!source_var:-none}"

        results+=("ext|$ext_id|$display_name|$installed|$latest|$status|$source")

        [[ "$status" == "UPDATE" || "$status" == "NOT_INSTALLED" ]] && updates_available=true
    done

    # Check runtimes
    local java_version
    java_version=$(get_java_version)
    local java_status="CURRENT"
    if [[ -z "$java_version" ]]; then
        java_status="NOT_INSTALLED"
        updates_available=true
    elif [[ "$java_version" -lt "$JAVA_MIN_VERSION" ]]; then
        java_status="UPDATE"
        updates_available=true
    fi
    results+=("runtime|java|Java|${java_version:-}|$JAVA_REC_VERSION LTS|$java_status")

    local node_version
    node_version=$(get_node_version)
    local node_status="CURRENT"
    if [[ -z "$node_version" ]]; then
        node_status="NOT_INSTALLED"
        updates_available=true
    elif [[ "$node_version" -lt "$NODE_MIN_VERSION" ]]; then
        node_status="UPDATE"
        updates_available=true
    fi
    results+=("runtime|node|Node.js|${node_version:-}|$NODE_REC_VERSION LTS|$node_status")

    # Check Salesforce CLI
    local sf_installed
    sf_installed=$(get_sf_version)
    local sf_latest
    sf_latest=$(get_latest_sf_version)
    local sf_status
    sf_status=$(get_status "$sf_installed" "$sf_latest")

    [[ "$sf_status" == "UPDATE" || "$sf_status" == "NOT_INSTALLED" ]] && updates_available=true
    results+=("cli|sf|sf (@salesforce/cli)|$sf_installed|$sf_latest|$sf_status")

    # Save results to cache
    local json_results='{"timestamp":'$(date +%s)',"results":['
    local first=true
    for result in "${results[@]}"; do
        IFS='|' read -r type id name installed latest status source <<< "$result"
        $first || json_results+=','
        first=false
        json_results+="{\"type\":\"$type\",\"id\":\"$id\",\"name\":\"$name\",\"installed\":\"$installed\",\"latest\":\"$latest\",\"status\":\"$status\",\"source\":\"${source:-}\"}"
    done
    json_results+='],"updates_available":'
    $updates_available && json_results+='true' || json_results+='false'
    json_results+='}'

    echo "$json_results" > "$CACHE_FILE"
    update_timestamp

    # Output results
    if $JSON_OUTPUT; then
        echo "$json_results"
    elif ! $QUIET_MODE; then
        display_results "${results[@]}"
    fi

    $updates_available && return 1 || return 0
}

display_results() {
    local results=("$@")
    local cache_age
    cache_age=$(get_cache_age)

    echo ""
    echo "🔍 SF-SKILLS ENVIRONMENT CHECK (cached $cache_age)"
    echo "════════════════════════════════════════════════════════════════"

    # LSP Servers (VS Code Extensions or Direct Download)
    print_header "📦 LSP SERVERS" true
    for result in "${results[@]}"; do
        IFS='|' read -r type id name installed latest status source <<< "$result"
        [[ "$type" == "ext" ]] && print_row "$id" "$installed" "$latest" "$status" "${source:-}"
    done

    # Runtimes
    print_header "⚙️  RUNTIMES"
    for result in "${results[@]}"; do
        IFS='|' read -r type id name installed latest status <<< "$result"
        [[ "$type" == "runtime" ]] && print_row "$name" "$installed" "$latest" "$status"
    done

    # Salesforce CLI
    print_header "🛠️  SALESFORCE CLI"
    for result in "${results[@]}"; do
        IFS='|' read -r type id name installed latest status <<< "$result"
        [[ "$type" == "cli" ]] && print_row "$name" "$installed" "$latest" "$status"
    done

    echo ""
    echo "════════════════════════════════════════════════════════════════"

    # Show update commands if needed
    local has_updates=false
    for result in "${results[@]}"; do
        IFS='|' read -r type id name installed latest status source <<< "$result"
        if [[ "$status" == "UPDATE" || "$status" == "NOT_INSTALLED" ]]; then
            has_updates=true
            break
        fi
    done

    if $has_updates; then
        echo "💡 UPDATE COMMANDS:"
        for result in "${results[@]}"; do
            IFS='|' read -r type id name installed latest status source <<< "$result"
            if [[ "$status" == "UPDATE" || "$status" == "NOT_INSTALLED" ]]; then
                case "$type" in
                    ext)
                        if [[ "${source:-}" == "cache" ]]; then
                            echo "   python3 ~/.claude/lsp-engine/lsp-acquire.py --force"
                        elif [[ "$status" == "NOT_INSTALLED" ]]; then
                            echo "   python3 ~/.claude/lsp-engine/lsp-acquire.py  (recommended)"
                            echo "   code --install-extension $id  (alternative)"
                        else
                            echo "   code --install-extension $id"
                        fi
                        ;;
                    runtime)
                        case "$id" in
                            java) echo "   brew install openjdk@$JAVA_REC_VERSION" ;;
                            node) echo "   brew install node" ;;
                        esac
                        ;;
                    cli)     echo "   brew upgrade sf" ;;
                esac
            fi
        done
        echo ""
    fi

    local next_check
    next_check=$(get_next_check_date)
    echo "🔄 Next check: $next_check (or run with --force)"
    echo ""
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    # Check if we can use cached results
    if ! $FORCE_REFRESH && cache_is_fresh && [[ -f "$CACHE_FILE" ]]; then
        if $JSON_OUTPUT; then
            cat "$CACHE_FILE"
        elif ! $QUIET_MODE; then
            # Re-display cached results
            local cached_json
            cached_json=$(cat "$CACHE_FILE")

            # Parse cached JSON and display
            # (Simple approach: just re-run for display purposes)
            # In practice, we'd parse the JSON, but bash isn't great at that
            run_checks
            return $?
        else
            # Quiet mode - check updates_available from cache
            grep -q '"updates_available":true' "$CACHE_FILE" && return 1 || return 0
        fi
    else
        run_checks
        return $?
    fi
}

main "$@"
