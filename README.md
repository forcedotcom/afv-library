# Agentforce Vibes Library

Salesforce's official repository of agent skills for app building. It spans Agentforce agents, Lightning apps, Flow, Apex, SOQL, LWC, UI bundles, objects and fields, permission sets, and more—and we're just getting started.

Optimized for Agentforce Vibes. Compatible with all AI tools that support skills.

## 📚 About

This repository curates Salesforce app building skills from Salesforce and the entire community.

## 🗂️ Structure

```
afv-library/
├── skills/               # Directory-based executable workflows
│   ├── generating-apex/
│   ├── generating-custom-object/
│   ├── generating-flow/
│   └── ...
├── samples/              # Synced sample apps (e.g. from npm)
│   └── ui-bundle-template-app-react-sample-b2e/
│   └── ...
├── scripts/
│   └── ...
└── README.md
```

## 🚀 Usage

| **Tool** | **Do This** |
|----------|-------------|
| **Agentforce Vibes** | Skills are auto-installed and auto-updated |
| **Claude Code, Codex, Gemini CLI, OpenCode, etc** | `npx skills add forcedotcom/afv-library` |


## 📦 Samples

The `samples/` folder contains synced sample apps. For example, `samples/ui-bundle-template-app-react-sample-b2e/` is kept in sync with the npm package `@salesforce/ui-bundle-template-app-react-sample-b2e` (nightly and on manual trigger via GitHub Actions). To run the same sync locally from the repo root:

```bash
npm install
npm run sync-react-b2e-sample
```

The GitHub Action runs these same commands and opens a PR only when the npm package version has changed. See [samples/README.md](samples/README.md) for details.


## 🛠️ Agent Skills

Agent Skills are modular capabilities that bundle executable workflows, scripts, and reference materials into self-contained directories. This repository follows the open [Agent Skills specification](https://agentskills.io/) and is usable by all AI tools that support skills: Claude Code, Codex, Gemini CLI, OpenCode, etc.

### Directory Structure

Each skill is a folder containing:
- `SKILL.md` (required) - instructions + YAML frontmatter
- `scripts/` (optional) - executable Python/Bash/JS
- `references/` (optional) - additional documentation
- `assets/` (optional) - templates, schemas, lookup data


## 🤝 Contributing

See [Contributing](./CONTRIBUTING.md) for complete details.


## 💬 Feedback

Found an issue or have a suggestion?
- Open an issue in GitHub
- Suggest improvements via pull request
- Start a discussion in GitHub Discussions or the pull request thread

