---
description: A4D rule — no node -e; use replace_in_file / write_to_file only
alwaysApply: true
---

# A4D Enforcement: No node -e

This project forbids using "node -e" for any operation (file manipulation, string replacement, reading/writing configs, shell automation).

Policy:
- Never use "node -e" one-liners.
- Use replace_in_file or write_to_file for code/config edits.
- Use jq/sed/awk cautiously when needed; prefer replace_in_file for deterministic edits.
- For JSON edits: prefer write_to_file after reading, or replace_in_file with precise diffs.
- For ESLint/TS config changes: edit files directly via write_to_file or replace_in_file.

Rationale:
- Ensures reproducibility and auditability.
- Avoids shell escaping bugs and cross-platform inconsistencies.
- Aligns with project reliability protocol.

Violation handling:
- If any prior step used "node -e", revert and redo using write_to_file or replace_in_file.

**Cross-reference:** This rule is also summarized in **webapp.md** (MUST FOLLOW #1). Both apply.
