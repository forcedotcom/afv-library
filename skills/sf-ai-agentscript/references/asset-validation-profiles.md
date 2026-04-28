# Asset Validation Profiles

The `assets/` directory intentionally mixes **three kinds of `.agent` files**:

1. **Standalone examples/templates** — complete files that should validate as full agents.
2. **Org fixtures** — structurally valid files that may block only because the currently resolved org is missing referenced users/Flows/classes.
3. **Partial snippets/patterns** — reusable building blocks that intentionally omit top-level blocks or rely on surrounding context.

Because of that mix, a single "every `.agent` file must have 0 blocking findings" rule creates false failures.

## Profile Manifest

Source of truth:

- `assets/validation-profiles.json`

Validation harness:

- `scripts/validate-asset-profiles.py`

## How the Harness Works

The harness runs the main validator (`hooks/scripts/agentscript-syntax-validator.py`) against every `assets/**/*.agent` file, then checks the results against the profile manifest.

### Profile types

#### 1. `standalone_examples`
These are expected to be complete agents/templates.

Policy:
- **No blocking findings allowed**
- Only explicitly allowlisted warning IDs may appear
- Typical intentional warning classes here are template/demo reminders (`ASV-CFG-007`) and teaching-pattern advisories such as planner-hint warnings (`ASV-RUN-007`)

#### 2. `org_fixtures`
These are complete files, but the current local org may not contain all referenced metadata.

Policy:
- Only explicitly allowlisted org-dependent blocking IDs may appear
- Only explicitly allowlisted warning IDs may appear
- Current example: `ASV-ORG-007` for missing outbound route Flows in the resolved org

#### 3. `partial_snippets`
These are partial fragments or pattern files that are not intended to be published directly.

Policy:
- Only explicitly allowlisted completeness/snippet-related blocking IDs may appear
- Only explicitly allowlisted warning IDs may appear
- Any new unexpected blocker **or warning** still fails the harness

## Run It

```bash
python3 skills/sf-ai-agentscript/scripts/validate-asset-profiles.py
```

Expected success shape:

```text
Asset validation profile summary
-------------------------------
- standalone_examples: ...
- org_fixtures: ...
- partial_snippets: ...

✅ All asset files matched their configured validation profile expectations.
```

## Why This Is Better Than Ignoring Failures

This profile-based approach keeps the validator strict **without** pretending every asset file is the same kind of artifact.

It gives us:
- strict validation for complete examples
- explicit documentation of intentional partials
- controlled tolerance for org-dependent fixtures
- failure on newly introduced unexpected blockers
- failure on newly introduced unexpected warnings that are not part of the file/profile's documented teaching intent

## Maintenance Rules

When you add a new file under `assets/`:

1. Decide whether it is a **standalone example**, **org fixture**, or **partial snippet**.
2. Add it to `assets/validation-profiles.json`.
3. If you allow blocking IDs or warning IDs for it, document *why* in the PR or commit.
4. Re-run:
   ```bash
   python3 skills/sf-ai-agentscript/scripts/validate-asset-profiles.py
   ```

If the harness fails, either:
- fix the asset, or
- update the profile manifest intentionally.

Do **not** silently broaden allowlists without explaining why.
