#!/usr/bin/env bash
#
# sf-skills Release Helper Script
# ================================
#
# Creates a new release of sf-skills by:
# 1. Validating version format (v*.*.*)
# 2. Updating version in skills-registry.json
# 3. Creating annotated git tag
# 4. Pushing tag to origin (triggers GitHub Actions release workflow)
#
# Usage:
#     ./scripts/create-release.sh v1.2.0
#
# Requirements:
#     - jq (for JSON manipulation)
#     - git
#     - Clean working directory (no uncommitted changes)
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Files to update
REGISTRY_JSON="$REPO_ROOT/shared/hooks/skills-registry.json"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_banner() {
    echo ""
    echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║              sf-skills Release Helper                         ║${NC}"
    echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "  ${GREEN}✅${NC} $1"
}

print_info() {
    echo -e "  ${BLUE}ℹ️ ${NC} $1"
}

print_warning() {
    echo -e "  ${YELLOW}⚠️ ${NC} $1"
}

print_error() {
    echo -e "  ${RED}❌${NC} $1"
}

print_step() {
    echo ""
    echo -e "${BOLD}Step $1: $2${NC}"
    echo "──────────────────────────────────────────────────────"
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

check_dependencies() {
    local missing=()

    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi

    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing required dependencies: ${missing[*]}"
        echo "  Install with: brew install ${missing[*]}"
        exit 1
    fi
}

validate_version_format() {
    local version="$1"

    # Must match v followed by semver (v1.0.0, v1.2.3, etc.)
    if [[ ! "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format: $version"
        echo "  Expected format: v1.2.3 (semantic versioning with 'v' prefix)"
        exit 1
    fi
}

check_clean_working_directory() {
    if ! git diff --quiet || ! git diff --staged --quiet; then
        print_error "Working directory has uncommitted changes"
        echo "  Please commit or stash changes before creating a release"
        git status --short
        exit 1
    fi
}

check_tag_not_exists() {
    local version="$1"

    if git tag -l "$version" | grep -q "$version"; then
        print_error "Tag $version already exists"
        echo "  Use a different version or delete the existing tag first"
        exit 1
    fi
}

get_current_version() {
    if [ -f "$REGISTRY_JSON" ]; then
        jq -r '.version // "0.0.0"' "$REGISTRY_JSON"
    else
        echo "0.0.0"
    fi
}

# ============================================================================
# UPDATE FUNCTIONS
# ============================================================================

update_registry_json() {
    local version="$1"
    local version_no_v="${version#v}"  # Remove 'v' prefix

    if [ ! -f "$REGISTRY_JSON" ]; then
        print_warning "skills-registry.json not found, skipping"
        return 0
    fi

    local temp_file
    temp_file=$(mktemp)

    jq --arg v "$version_no_v" '.version = $v' "$REGISTRY_JSON" > "$temp_file"
    mv "$temp_file" "$REGISTRY_JSON"
    print_success "Updated skills-registry.json to v$version_no_v"
}

create_git_tag() {
    local version="$1"
    local current_version="$2"

    # Get commit count since last tag for the message
    local commit_count
    if git describe --tags --abbrev=0 &>/dev/null; then
        local last_tag
        last_tag=$(git describe --tags --abbrev=0)
        commit_count=$(git rev-list "$last_tag"..HEAD --count)
    else
        commit_count=$(git rev-list HEAD --count)
    fi

    # Create annotated tag with message
    local tag_message="Release $version

Changes since v$current_version:
- $commit_count commits

Created by: scripts/create-release.sh
Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

    git tag -a "$version" -m "$tag_message"
    print_success "Created annotated tag: $version"
}

push_tag() {
    local version="$1"

    print_info "Pushing tag to origin..."
    git push origin "$version"
    print_success "Pushed tag $version to origin"
}

commit_version_updates() {
    local version="$1"

    # Stage version file changes
    git add "$REGISTRY_JSON" 2>/dev/null || true

    # Check if there are changes to commit
    if git diff --staged --quiet; then
        print_info "No version file changes to commit"
        return 0
    fi

    git commit -m "chore: bump version to $version

Updated:
- shared/hooks/skills-registry.json

[automated by scripts/create-release.sh]"

    print_success "Committed version updates"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    print_banner

    # Check arguments
    if [ $# -lt 1 ]; then
        echo "Usage: $0 <version>"
        echo ""
        echo "Examples:"
        echo "  $0 v1.0.0"
        echo "  $0 v1.2.3"
        echo ""
        exit 1
    fi

    local new_version="$1"

    # Step 1: Check dependencies
    print_step 1 "Checking dependencies"
    check_dependencies
    print_success "All dependencies available"

    # Step 2: Validate version format
    print_step 2 "Validating version"
    validate_version_format "$new_version"
    print_success "Version format valid: $new_version"

    # Get current version for comparison
    local current_version
    current_version=$(get_current_version)
    print_info "Current version: v$current_version"

    # Step 3: Check working directory
    print_step 3 "Checking git status"
    cd "$REPO_ROOT"
    check_clean_working_directory
    print_success "Working directory is clean"

    # Step 4: Check tag doesn't exist
    check_tag_not_exists "$new_version"
    print_success "Tag $new_version does not exist yet"

    # Step 5: Update version files
    print_step 4 "Updating version files"
    update_registry_json "$new_version"

    # Step 6: Commit version changes
    print_step 5 "Committing changes"
    commit_version_updates "$new_version"

    # Step 7: Create tag
    print_step 6 "Creating git tag"
    create_git_tag "$new_version" "$current_version"

    # Step 8: Push tag (triggers GitHub Actions)
    print_step 7 "Pushing to remote"
    push_tag "$new_version"

    # Summary
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ RELEASE CREATED SUCCESSFULLY!${NC}"
    echo ""
    echo "  Version: $new_version"
    echo "  Previous: v$current_version"
    echo ""
    echo "  GitHub Actions will now:"
    echo "    1. Generate changelog from commits"
    echo "    2. Create GitHub Release with notes"
    echo ""
    echo "  View release at:"
    echo "    https://github.com/Jaganpro/sf-skills/releases/tag/$new_version"
    echo ""
}

main "$@"
