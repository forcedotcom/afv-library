#!/usr/bin/env bash
set -euo pipefail

# Cleanup local/generated workspace artifacts for sf-skills.
# By default runs in dry-run mode.
# Use --apply to actually delete the matched paths.

MODE="dry-run"
if [[ "${1:-}" == "--apply" ]]; then
  MODE="apply"
fi

TARGETS=(
  ".DS_Store"
  ".pytest_cache"
  ".venv"
  "sf_skills.egg-info"
  "null"
  "scripts/__pycache__"
  "shared/__pycache__"
  "shared/code_analyzer/__pycache__"
  "shared/hooks/scripts/__pycache__"
  "shared/lsp-engine/__pycache__"
  "tools/__pycache__"
  "skills/sf-ai-agentforce-observability/.venv"
  "skills/sf-ai-agentforce-observability/.trace-venv"
  "skills/sf-ai-agentforce-observability/trace-results"
  "skills/sf-ai-agentforce-observability/validation"
  "skills/sf-ai-agentforce-testing/validation"
  "skills/sf-ai-agentscript/validation"
  "skills/sf-permissions/.venv"
)

PYCACHE_DIRS=()
while IFS= read -r path; do
  PYCACHE_DIRS+=("$path")
done < <(find . -type d -name __pycache__ \
  -not -path './.git/*' \
  -not -path '*/.venv/*' \
  -not -path '*/.trace-venv/*' | sort)
printf 'sf-skills local cleanup (%s)\n' "$MODE"
printf '================================\n'

UNIQUE_TARGETS=()
while IFS= read -r path; do
  UNIQUE_TARGETS+=("$path")
done < <(printf '%s\n' "${TARGETS[@]}" "${PYCACHE_DIRS[@]}" | sort -u)

for path in "${UNIQUE_TARGETS[@]}"; do
  [[ -e "$path" ]] || continue
  if [[ "$MODE" == "dry-run" ]]; then
    printf 'would remove: %s\n' "$path"
  else
    rm -rf "$path"
    printf 'removed: %s\n' "$path"
  fi
done

if [[ "$MODE" == "dry-run" ]]; then
  printf '\nRun with --apply to remove the paths above.\n'
fi
