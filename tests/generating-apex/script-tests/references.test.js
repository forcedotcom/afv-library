import { describe, it, expect } from "vitest"
import { readSkillFile } from "../../helpers"
import fs from "fs"
import path from "path"

const SKILL = "generating-apex"
const REFS_DIR = path.join(__dirname, "..", "..", "..", "skills", SKILL, "references")

describe(`${SKILL}: reference files are valid`, () => {
  it("references directory exists and has .cls files", () => {
    const files = fs.readdirSync(REFS_DIR).filter((f) => f.endsWith(".cls"))
    expect(files.length).toBeGreaterThan(0)
  })

  it("all reference files are non-empty", () => {
    const files = fs.readdirSync(REFS_DIR).filter((f) => f.endsWith(".cls"))
    for (const file of files) {
      const content = readSkillFile(SKILL, `references/${file}`)
      expect(content.trim().length, `${file} should not be empty`).toBeGreaterThan(0)
    }
  })

  // TODO: Add more tests - validate class names match filenames, check for ApexDoc, etc.
})
