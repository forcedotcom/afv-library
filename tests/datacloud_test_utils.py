from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
ORG_ALIAS = os.getenv("SF_DATACLOUD_ORG_ALIAS")
PARTIAL_ORG_ALIAS = os.getenv("SF_DATACLOUD_PARTIAL_ORG_ALIAS")
ENABLED_ORG_ALIAS = os.getenv("SF_DATACLOUD_ENABLED_ORG_ALIAS")

DATACLOUD_SKILLS = [
    "sf-datacloud",
    "sf-datacloud-connect",
    "sf-datacloud-prepare",
    "sf-datacloud-harmonize",
    "sf-datacloud-segment",
    "sf-datacloud-act",
    "sf-datacloud-retrieve",
]

PHASE_SKILLS = [skill for skill in DATACLOUD_SKILLS if skill != "sf-datacloud"]

EXPECTED_FRONTMATTER_LINES = {
    "sf-datacloud": [
        'name: sf-datacloud',
        'compatibility: "Requires an external community sf data360 CLI plugin and a Data Cloud-enabled org"',
        'author: "Gnanasekaran Thoppae"',
    ],
    "sf-datacloud-connect": [
        'name: sf-datacloud-connect',
        'phase: "Connect"',
    ],
    "sf-datacloud-prepare": [
        'name: sf-datacloud-prepare',
        'phase: "Prepare"',
    ],
    "sf-datacloud-harmonize": [
        'name: sf-datacloud-harmonize',
        'phase: "Harmonize"',
    ],
    "sf-datacloud-segment": [
        'name: sf-datacloud-segment',
        'phase: "Segment"',
    ],
    "sf-datacloud-act": [
        'name: sf-datacloud-act',
        'phase: "Act"',
    ],
    "sf-datacloud-retrieve": [
        'name: sf-datacloud-retrieve',
        'phase: "Retrieve"',
    ],
}

EXPECTED_HEADINGS = {
    "sf-datacloud": [
        "## When This Skill Owns the Task",
        "## Required Context to Gather First",
        "## Core Operating Rules",
        "## Recommended Workflow",
        "## High-Signal Gotchas",
        "## Output Format",
        "## Cross-Skill Integration",
        "## Reference Map",
    ],
    "sf-datacloud-connect": [
        "## When This Skill Owns the Task",
        "## Required Context to Gather First",
        "## Core Operating Rules",
        "## Recommended Workflow",
        "## High-Signal Gotchas",
        "## Output Format",
        "## References",
    ],
    "sf-datacloud-prepare": [
        "## When This Skill Owns the Task",
        "## Required Context to Gather First",
        "## Core Operating Rules",
        "## Recommended Workflow",
        "## High-Signal Gotchas",
        "## Output Format",
        "## References",
    ],
    "sf-datacloud-harmonize": [
        "## When This Skill Owns the Task",
        "## Required Context to Gather First",
        "## Core Operating Rules",
        "## Recommended Workflow",
        "## High-Signal Gotchas",
        "## Output Format",
        "## References",
    ],
    "sf-datacloud-segment": [
        "## When This Skill Owns the Task",
        "## Required Context to Gather First",
        "## Core Operating Rules",
        "## Recommended Workflow",
        "## High-Signal Gotchas",
        "## Output Format",
        "## References",
    ],
    "sf-datacloud-act": [
        "## When This Skill Owns the Task",
        "## Required Context to Gather First",
        "## Core Operating Rules",
        "## Recommended Workflow",
        "## High-Signal Gotchas",
        "## Output Format",
        "## References",
    ],
    "sf-datacloud-retrieve": [
        "## When This Skill Owns the Task",
        "## Required Context to Gather First",
        "## Core Operating Rules",
        "## Recommended Workflow",
        "## High-Signal Gotchas",
        "## Output Format",
        "## References",
    ],
}

EXPECTED_COMMANDS = {
    "sf-datacloud": [
        "sf data360 man",
        "sf data360 doctor",
        "sf data360 data-stream list",
        "sf data360 dmo list",
        "sf data360 identity-resolution list",
        "sf data360 segment list",
        "diagnose-org.mjs",
    ],
    "sf-datacloud-connect": [
        "sf data360 connection connector-list",
        "sf data360 connection list",
        "sf data360 connection get",
        "sf data360 connection objects",
        "sf data360 connection schema-get",
        "sf data360 connection test",
        "sf data360 connection create",
        "sf data360 connection schema-upsert",
        "examples/connections/heroku-postgres.json",
        "examples/connections/redshift.json",
        "examples/connections/sharepoint-unstructured.json",
        "examples/connections/snowflake-connection.json",
        "examples/connections/ingest-api-connection.json",
        "examples/connections/ingest-api-schema.json",
    ],
    "sf-datacloud-prepare": [
        "sf data360 data-stream list",
        "sf data360 dlo list",
        "sf data360 data-stream create-from-object",
        "sf data360 data-stream create",
        "sf data360 data-stream run",
        "sf data360 connection run-existing",
        "sf data360 dlo get",
        "examples/ingestion-api/",
        "Profile",
        "Engagement",
        "Other",
    ],
    "sf-datacloud-harmonize": [
        "sf data360 dmo list --all",
        "sf data360 query describe",
        "sf data360 dmo mapping-list",
        "sf data360 dmo map-to-canonical",
        "sf data360 identity-resolution run",
    ],
    "sf-datacloud-segment": [
        "sf data360 segment list",
        "sf data360 calculated-insight list",
        "sf data360 segment create",
        "sf data360 segment publish",
        "sf data360 segment count",
    ],
    "sf-datacloud-act": [
        "sf data360 activation platforms",
        "sf data360 activation-target list",
        "sf data360 data-action-target list",
        "sf data360 activation create",
        "sf data360 data-action create",
    ],
    "sf-datacloud-retrieve": [
        "sf data360 query sql",
        "sf data360 query sqlv2",
        "sf data360 query async-create",
        "sf data360 query describe",
        "sf data360 search-index list",
        "sf data360 query vector",
        "sf data360 query hybrid",
        "examples/search-indexes/hybrid-structured.json",
        "examples/search-indexes/vector-knowledge.json",
    ],
}

CLI_HELP_COMMANDS = [
    ["sf", "data360", "man"],
    ["sf", "data360", "doctor", "--help"],
    ["sf", "data360", "connection", "connector-list", "--help"],
    ["sf", "data360", "connection", "list", "--help"],
    ["sf", "data360", "connection", "get", "--help"],
    ["sf", "data360", "connection", "objects", "--help"],
    ["sf", "data360", "connection", "fields", "--help"],
    ["sf", "data360", "connection", "schema-get", "--help"],
    ["sf", "data360", "connection", "schema-upsert", "--help"],
    ["sf", "data360", "connection", "test", "--help"],
    ["sf", "data360", "connection", "run-existing", "--help"],
    ["sf", "data360", "connection", "create", "--help"],
    ["sf", "data360", "data-stream", "list", "--help"],
    ["sf", "data360", "data-stream", "get", "--help"],
    ["sf", "data360", "data-stream", "create-from-object", "--help"],
    ["sf", "data360", "data-stream", "create", "--help"],
    ["sf", "data360", "data-stream", "run", "--help"],
    ["sf", "data360", "dlo", "list", "--help"],
    ["sf", "data360", "dlo", "get", "--help"],
    ["sf", "data360", "dmo", "list", "--help"],
    ["sf", "data360", "dmo", "get", "--help"],
    ["sf", "data360", "dmo", "mapping-list", "--help"],
    ["sf", "data360", "dmo", "map-to-canonical", "--help"],
    ["sf", "data360", "identity-resolution", "list", "--help"],
    ["sf", "data360", "identity-resolution", "create", "--help"],
    ["sf", "data360", "identity-resolution", "run", "--help"],
    ["sf", "data360", "segment", "list", "--help"],
    ["sf", "data360", "segment", "create", "--help"],
    ["sf", "data360", "segment", "publish", "--help"],
    ["sf", "data360", "segment", "count", "--help"],
    ["sf", "data360", "calculated-insight", "list", "--help"],
    ["sf", "data360", "calculated-insight", "create", "--help"],
    ["sf", "data360", "calculated-insight", "run", "--help"],
    ["sf", "data360", "activation", "platforms", "--help"],
    ["sf", "data360", "activation", "create", "--help"],
    ["sf", "data360", "activation", "list", "--help"],
    ["sf", "data360", "activation", "data", "--help"],
    ["sf", "data360", "activation-target", "list", "--help"],
    ["sf", "data360", "activation-target", "create", "--help"],
    ["sf", "data360", "data-action", "create", "--help"],
    ["sf", "data360", "data-action-target", "list", "--help"],
    ["sf", "data360", "data-action-target", "create", "--help"],
    ["sf", "data360", "query", "describe", "--help"],
    ["sf", "data360", "query", "sql", "--help"],
    ["sf", "data360", "query", "sqlv2", "--help"],
    ["sf", "data360", "query", "async-create", "--help"],
    ["sf", "data360", "query", "vector", "--help"],
    ["sf", "data360", "query", "hybrid", "--help"],
    ["sf", "data360", "search-index", "list", "--help"],
]

PROMPT_FIXTURES = {
    "sf-datacloud": "Set up a Data Cloud pipeline from CRM ingestion to unified profiles and troubleshoot it across phases.",
    "sf-datacloud-connect": "Browse connection objects, create a Snowflake Data Cloud connection from JSON, and upload an Ingestion API schema.",
    "sf-datacloud-prepare": "Create a Data Cloud data stream, rerun the stream for unstructured ingestion, and inspect the DLO.",
    "sf-datacloud-harmonize": "Map to canonical, create identity resolution, and inspect unified profiles.",
    "sf-datacloud-segment": "Publish a segment, count segment members, and run a calculated insight.",
    "sf-datacloud-act": "List activation targets and create a data action for downstream delivery.",
    "sf-datacloud-retrieve": "Run a hybrid search with a prefilter, describe a Data Cloud table, and inspect a search index.",
}

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text()


def skill_text(skill: str) -> str:
    return read_text(f"skills/{skill}/SKILL.md")


def split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    assert match, "Expected YAML frontmatter wrapped in --- markers"
    return match.group(1), match.group(2)


def load_registry() -> dict:
    return json.loads(read_text("shared/hooks/skills-registry.json"))


def run(cmd: Iterable[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(cmd),
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def sf_data360_available() -> bool:
    return run(["sf", "data360", "man"]).returncode == 0


def output_text(result: subprocess.CompletedProcess[str]) -> str:
    return strip_ansi((result.stdout or "") + (result.stderr or ""))


def output_json(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)


def entry_matches_prompt(entry: dict, prompt: str) -> bool:
    prompt_lower = prompt.lower()
    if any(keyword.lower() in prompt_lower for keyword in entry.get("keywords", [])):
        return True
    return any(
        re.search(pattern, prompt_lower, re.IGNORECASE)
        for pattern in entry.get("intentPatterns", [])
    )
