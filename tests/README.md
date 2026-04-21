# Testing Guide for `afv-library`

This directory contains all tests for the skills in this repo. Tests live here - never inside `skills/` - so the published package stays clean.

> **Note:** The framework configuration files (`package.json`, `vitest.config.ts`, `scripts/run-skill-tests.sh`) are not part of this PR. The commands below will work once the framework PR is merged.

## Quick start

```bash
npm ci
pip3 install pytest         # only if you have Python script-tests

npm run test                # run everything (validator + skill-tests + script-tests)

npm run validate:skills     # structural validator only
npm run test:skills         # skill-tests only (Vitest)
npm run test:scripts        # script-tests only (pytest, bash, bats, TypeScript/JS)
```

## Directory structure

When skill owners add tests, the directory grows like this:

```
tests/
├── README.md                             ← you are here
├── helpers/                              ← shared utilities (part of the framework)
│   ├── index.ts
│   ├── parse-skill.ts
│   ├── extract-code-blocks.ts
│   ├── apex-validator.ts
│   ├── xml-validator.ts
│   └── link-checker.ts
│
├── generating-apex/                      ← one skill, one directory
│   └── skill-tests/
│       └── content.test.ts
│
├── testing-agentforce/                   ← skill with scripts
│   ├── skill-tests/
│   │   └── content.test.ts
│   └── script-tests/
│       └── test_run_specs.sh
│
└── ...
```

### How to organize

The directory name doesn't have to match a skill name - Vitest and the discovery script don't check it. You can organize however makes sense for your team:

- **One directory per skill** (e.g. `tests/generating-apex/`) - good default when one team owns one skill.
- **One directory per team** (e.g. `tests/agentforce/`) - useful when a team owns multiple skills and wants to cover them in fewer test files.

Inside each directory, up to two folders:


| Folder          | Purpose                                                                                 | Language                                                         | Runner                        |
| --------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------- |
| `skill-tests/`  | Validate SKILL.md content - frontmatter values, code block correctness, asset existence | TypeScript only                                                  | Vitest                        |
| `script-tests/` | Test executable scripts in their native language                                        | Same language as your script (Python, Bash, Bats, TypeScript/JS) | pytest, bash, bats, or vitest |


Most skills only need `skill-tests/`. Add `script-tests/` only if your skill ships scripts in `scripts/`.

## Adding tests for your skill

### Step 1: Create the directory

```bash
mkdir -p tests/<your-directory-name>/skill-tests
```

Use the skill name (e.g. `generating-apex`) or a team name (e.g. `agentforce`) - whichever fits your ownership model.

### Step 2: Write a skill-test

Create a `*.test.ts` file inside `skill-tests/`. The `SKILL` constant controls which skill directory gets read - it's independent of the test directory name.

**Single-skill example** (`tests/generating-apex/skill-tests/content.test.ts`):

```typescript
import { describe, it, expect } from "vitest"
import { readSkillFile, skillHasFile, extractCodeBlocks, hasBalancedBraces } from "../../helpers"

const SKILL = "generating-apex"

describe(`${SKILL}: SKILL.md content`, () => {
  const content = readSkillFile(SKILL, "SKILL.md")

  it("description mentions the key activation context", () => {
    expect(content).toMatch(/Apex/)
  })
})

describe(`${SKILL}: code examples`, () => {
  const body = readSkillFile(SKILL, "SKILL.md")
  const blocks = extractCodeBlocks(body, "apex")

  it("has code blocks", () => {
    expect(blocks.length).toBeGreaterThan(0)
  })

  for (const block of blocks) {
    it(`block at line ${block.startLine} has balanced braces`, () => {
      const result = hasBalancedBraces(block.content)
      expect(result.balanced, `open=${result.open} close=${result.close}`).toBe(true)
    })
  }
})

describe(`${SKILL}: required assets exist`, () => {
  const files = ["assets/template.cls", "references/patterns.md"]

  for (const file of files) {
    it(`${file} exists`, () => {
      expect(skillHasFile(SKILL, file)).toBe(true)
    })
  }
})
```

**Multi-skill example** (`tests/agentforce/skill-tests/content.test.ts`) - one file covering multiple skills owned by the same team:

```typescript
import { describe, it, expect } from "vitest"
import { readSkillFile, extractCodeBlocks, hasBalancedBraces } from "../../helpers"

const SKILLS = [
  "developing-agentforce",
  "testing-agentforce",
  "observing-agentforce",
]

for (const skill of SKILLS) {
  describe(`${skill}: SKILL.md content`, () => {
    const content = readSkillFile(skill, "SKILL.md")

    it("description mentions Agentforce", () => {
      expect(content).toMatch(/Agentforce/)
    })
  })

  describe(`${skill}: code examples have balanced braces`, () => {
    const body = readSkillFile(skill, "SKILL.md")
    const blocks = extractCodeBlocks(body, "yaml")

    for (const block of blocks) {
      it(`block at line ${block.startLine}`, () => {
        const result = hasBalancedBraces(block.content)
        expect(result.balanced).toBe(true)
      })
    }
  })
}
```

Vitest discovers any `*.test.ts` file under `tests/*/skill-tests/` automatically - no registration needed.

### Step 3: (Optional) Add script-tests

Only needed if your skill has scripts in `skills/<your-skill>/scripts/`.

```bash
mkdir -p tests/<your-skill-name>/script-tests
```

Add a test file matching the **required** naming convention for your language. Files that don't match these patterns will not be discovered and will silently not run:


| Language      | File naming pattern        | Runner |
| ------------- | -------------------------- | ------ |
| Python        | `test_*.py` or `*_test.py` | pytest |
| Bash          | `test_*.sh` or `*_test.sh` | bash   |
| Bats          | `*.bats`                   | bats   |
| TypeScript/JS | `*.test.ts` or `*.test.js` | vitest |


### Step 4: Verify

```bash
npm run test:skills         # should pick up your new skill-test
npm run test:scripts        # should pick up your new script-test
```

## Shared helpers

The `tests/helpers/` directory provides reusable utilities so skill owners don't have to rewrite common operations. Import them in any skill-test:

```typescript
import {
  readSkillFile,
  skillHasFile,
  parseSkill,
  extractCodeBlocks,
  hasBalancedBraces,
  hasClassOrInterfaceDeclaration,
  containsAnnotation,
  isWellFormedXml,
  findBrokenLinks,
} from "../../helpers"
```

Browse `tests/helpers/index.ts` to see all available exports. The helpers cover skill file access, code block extraction, Apex structural checks, XML validation, and link checking.

Need a helper that doesn't exist yet? Add it to `tests/helpers/` and export it from `index.ts`.

## How discovery works

**Skill-tests**: Vitest finds all `*.test.{ts,js}` files (configured in `vitest.config.ts`). The `npm run test:skills` command filters to only files with `skill-tests` in the path. No registration needed - drop the file and it runs.

**Script-tests**: The discovery script (`scripts/run-skill-tests.sh`) walks every `tests/*/script-tests/` directory, matches test files by extension, and dispatches to the native runner. If a required runner isn't installed (e.g. pytest), it prints `SKIPPED` instead of failing.

The discovery script matches files to runners as follows:


| Language      | Finds files matching     | Runs them with |
| ------------- | ------------------------ | -------------- |
| Python        | `test_*.py`, `*_test.py` | pytest         |
| Bash          | `test_*.sh`, `*_test.sh` | bash           |
| Bats          | `*.bats`                 | bats           |
| TypeScript/JS | `*.test.ts`, `*.test.js` | vitest         |


**Naming matters.** If your test file doesn't match the expected pattern, it will silently not run:


| Runs               | Does NOT run                                  |
| ------------------ | --------------------------------------------- |
| `test_analyzer.py` | `analyzer_tests.py`                           |
| `analyzer_test.py` | `test-analyzer.py` (hyphens, not underscores) |
| `test_search.sh`   | `search_tests.sh`                             |
| `content.test.ts`  | `content.spec.ts`                             |


## Prerequisites

- **Node.js** (v22, see `.nvmrc`) + `npm ci`
- **Python 3.9+** and `pip install pytest` - only needed if you have Python script-tests
- **Bats** (`brew install bats-core`) - only needed if you have Bats script-tests
- No additional tools needed for bash script-tests

## Need a different language?

The discovery script currently supports Python, Bash, Bats, and TypeScript/JavaScript. If your script-tests require a different language or runner, support will need to be added to `scripts/run-skill-tests.sh`.

For questions or help, reach out on **#afv-skills-onboarding-support** in Slack.

## Examples

Working examples are included in this repo under `tests/`:

- `tests/generating-apex/` - Vitest skill-test + TypeScript and JavaScript script-tests
- `tests/trigger-refactor-pipeline/` - Vitest skill-test + Python (pytest) script-test
- `tests/using-ui-bundle-salesforce-data/` - Vitest skill-test + bash and bats script-tests

