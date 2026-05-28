#!/usr/bin/env python3
"""First-run setup: grant allowlist rules + seed gitignore files.

Idempotent. Called by the agent's Phase 3 on first run (sentinel absent). On
every subsequent run the agent skips calling this script entirely.

Three actions:
 1. Merge ~30 canonical rules into ~/.claude/settings.json permissions.allow
    (only adds missing entries; preserves any rules already present). Atomic
    write: staged tmp file in the same directory + os.replace(). On corrupt
    JSON, the original is copied aside to .corrupt.backup and the script
    exits 2 without modifying anything — Claude Code refusing to start on a
    blanked permission list is worse than refusing to grant.
 2. mkdir -p ~/.claude/data/investigating-agentforce-architecture/ + write
    .gitignore (`*`) iff the current content is not already exactly `*`.
    Metadata trees can carry customer-specific labels, descriptions, and
    flow names; preventing accidental git commits is load-bearing.
 3. mkdir -p ~/.claude/cache/investigating-agentforce-architecture/ + same
    .gitignore seeding.

Usage:
    python3 grant_allowlist.py

Inputs:
    none (all paths hardcoded under $HOME/.claude/)

Outputs:
    side effects: settings.json rewritten, two .gitignore files seeded
    stdout: one progress line per action
    exit 0: full success
    exit 1: write failure (disk full, permission denied)
    exit 2: settings.json unparseable (refuses to wipe)
"""
import json
import pathlib
import shutil
import sys

HOME = pathlib.Path.home()
SETTINGS = HOME / ".claude" / "settings.json"
DATA = HOME / ".claude" / "data" / "investigating-agentforce-architecture"
CACHE = HOME / ".claude" / "cache" / "investigating-agentforce-architecture"
SKILL = HOME / ".claude" / "skills" / "investigating-agentforce-architecture"

# Canonical allowlist rules. Every script gets its own scoped entry — no
# python3:* blanket, no python3 -c:* (agent forbids inline -c).
NEEDED = [
    # /tmp work dir — ephemeral per-invocation scratch (see SKILL.md
    # WORK_DIR construction). Matches the runtime path-prefix in SKILL.md.
    "Bash(mkdir -p /tmp/investigating-agentforce-architecture-*:*)",
    "Bash(rm -rf /tmp/investigating-agentforce-architecture-*:*)",
    "Bash(unzip:*)",
    # Salesforce CLI commands
    "Bash(sf project retrieve start:*)",
    "Bash(sf data query:*)",
    "Bash(sf org display:*)",
    # Read/write: /tmp
    "Read(/tmp/investigating-agentforce-architecture-**)",
    "Write(/tmp/investigating-agentforce-architecture-**)",
    # Skill + agent dirs (read-only)
    f"Read({HOME}/.claude/agents/**)",
    f"Read({HOME}/.claude/skills/**)",
    # Standalone data root
    f"Read({DATA}/**)",
    f"Write({DATA}/**)",
    f"Bash(mkdir -p {DATA}/**)",
    # Standalone cache root
    f"Read({CACHE}/**)",
    f"Write({CACHE}/**)",
    f"Bash(mkdir -p {CACHE}/**)",
    f"Bash(rm -rf {CACHE}/**)",
    f"Bash(mv {CACHE}/**:*)",
    # Sentinel (unversioned)
    f"Bash(touch {HOME}/.claude/.investigating-agentforce-architecture.allowlist-done.v2:*)",
    f"Bash(rm -f {HOME}/.claude/.investigating-agentforce-architecture.allowlist-done.v2:*)",
    # Tools scripts (per-file scoped — no glob). Tools live under tools/;
    # pipeline scripts under scripts/.
    # fix: the rename batch left these pointing at
    # tools/<name>.py for files that actually live in scripts/. Pre-
    # existing port artifact, now made user-visible by install.sh
    # (every internal invocation prompted). Realigned.
    f"Bash(python3 {SKILL}/tools/sanitize.py:*)",
    f"Bash(python3 {SKILL}/tools/grant_allowlist.py:*)",
    # fs_guard moved to plugin _shared/ in v1.5.0 (mirrored into every
    # sibling skill's scripts/_shared/ at install/build time so all 4
    # skills can import it standalone). SKILL.md phase-1 invokes it
    # from this new path; the allowlist mirrors that.
    f"Bash(python3 {SKILL}/scripts/_shared/fs_guard.py:*)",
    f"Bash(python3 {SKILL}/tools/emit_env.py:*)",
    f"Bash(python3 {SKILL}/tools/write_emit_ctx.py:*)",
    f"Bash(python3 {SKILL}/tools/emit_result.py:*)",
    # Pipeline scripts (scripts/, not tools/).
    f"Bash(python3 {SKILL}/scripts/main.py:*)",
    f"Bash(python3 {SKILL}/scripts/resolve_bot.py:*)",
    f"Bash(python3 {SKILL}/scripts/cache_check.py:*)",
    f"Bash(python3 {SKILL}/scripts/parse_bundle.py:*)",
    f"Bash(python3 {SKILL}/scripts/parse_wave.py:*)",
    f"Bash(python3 {SKILL}/scripts/finalize.py:*)",
    f"Bash(python3 {SKILL}/scripts/summarize_tree.py:*)",
    f"Bash(python3 {SKILL}/scripts/render_architecture.py:*)",
    f"Bash(python3 {SKILL}/scripts/probe_channels.py:*)",
    f"Bash(python3 {SKILL}/scripts/fetch_soql.py:*)",
    f"Bash(python3 {SKILL}/scripts/rest_client.py:*)",
    f"Bash(python3 {SKILL}/scripts/sf_cli.py:*)",
    f"Bash(python3 {SKILL}/scripts/soql_loader.py:*)",
    f"Bash(python3 {SKILL}/scripts/parallel_retrieve.py:*)",
    f"Bash(python3 {SKILL}/scripts/resolve_invocation_target.py:*)",
    f"Bash(python3 {SKILL}/scripts/retrieve_planner.py:*)",
    f"Bash(python3 {SKILL}/scripts/config.py:*)",
]


def grant_allowlist() -> None:
    if SETTINGS.exists():
        try:
            data = json.loads(SETTINGS.read_text())
        except json.JSONDecodeError as e:
            backup = SETTINGS.with_suffix(".corrupt.backup")
            shutil.copy(SETTINGS, backup)
            print(f"[allowlist] settings.json unparseable ({e}); backed up to {backup}")
            print("[allowlist] fix settings.json and retry; not modifying")
            sys.exit(2)
    else:
        data = {}

    data.setdefault("permissions", {}).setdefault("allow", [])
    allow = data["permissions"]["allow"]
    before = set(allow)
    added = 0
    for rule in NEEDED:
        if rule not in before:
            allow.append(rule)
            added += 1

    tmp = SETTINGS.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(SETTINGS)
    print(f"[allowlist] added {added} rules ({len(NEEDED)} canonical, {len(allow) - added} pre-existing)")


def seed_gitignore(root: pathlib.Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    gitignore = root / ".gitignore"
    current = gitignore.read_text() if gitignore.exists() else ""
    if current.strip() != "*":
        gitignore.write_text("*\n")
        print(f"[allowlist] seeded {gitignore}")


def main() -> int:
    try:
        grant_allowlist()
        seed_gitignore(DATA)
        seed_gitignore(CACHE)
        print("[allowlist] done")
        return 0
    except (OSError, IOError) as e:
        print(f"[allowlist] write failure: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
