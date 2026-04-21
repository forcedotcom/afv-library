import { describe, it, expect } from "vitest"
import { readSkillFile, skillHasFile } from "../../helpers"
import fs from "fs"
import path from "path"

const SKILL = "generating-apex"
const ASSETS_DIR = path.join(__dirname, "..", "..", "..", "skills", SKILL, "assets")

describe(`${SKILL}: template files are valid`, () => {
  it("all .cls files are non-empty", () => {
    const files = fs.readdirSync(ASSETS_DIR).filter((f) => f.endsWith(".cls"))
    expect(files.length).toBeGreaterThan(0)
    for (const file of files) {
      const content = readSkillFile(SKILL, `assets/${file}`)
      expect(content.trim().length, `${file} should not be empty`).toBeGreaterThan(0)
    }
  })

  it("every template has a placeholder token", () => {
    const files = fs.readdirSync(ASSETS_DIR).filter((f) => f.endsWith(".cls"))
    for (const file of files) {
      const content = readSkillFile(SKILL, `assets/${file}`)
      expect(content, `${file} should have a {placeholder}`).toMatch(/\{[A-Z]/)
    }
  })

  // TODO: Add more tests - validate specific templates, check for required methods, etc.
})
