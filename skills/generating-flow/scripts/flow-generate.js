#!/usr/bin/env node

// flow-generate.js — Call Salesforce Flow generation invocable actions via REST API.
//
// Approach B: Generic per-action caller. The agent orchestrates the 3-step pipeline
// by invoking this script once per step, passing outputs between calls.
//
// Usage:
//   node flow-generate.js --org <alias> --action <actionName> --input <json>
//
// Pipeline:
//   Step 1: --action fetchGroundedObjectMetadata  --input '{"userPrompt":"...", "inflightMetadata":[...]}'
//   Step 2: --action flowElementSelection         --input '{"userPrompt":"...", "groundingMetadata":"...", "operationId":""}'
//   Step 3: --action flowElementGeneration         --input '{"operationId":"...", "requestSource":"A4V"}'
//           (repeat Step 3 until output contains isComplete: true)
//
// Prerequisites:
//   - sf CLI authenticated to target org
//   - Node.js 18+ (for native fetch)

const { execFileSync } = require("child_process");
const { parseArgs } = require("util");

// ── Allowed actions ─────────────────────────────────────────────────────────

const ALLOWED_ACTIONS = new Set([
  "fetchGroundedObjectMetadata",
  "flowElementSelection",
  "flowElementGeneration",
]);

// ── Argument parsing ────────────────────────────────────────────────────────

let args;
try {
  ({ values: args } = parseArgs({
    options: {
      org:          { type: "string" },
      action:       { type: "string" },
      input:        { type: "string" },
      help:         { type: "boolean", default: false },
    },
    strict: true,
  }));
} catch (err) {
  console.error(`ERROR: ${err.message}`);
  console.error("Run with --help for usage.");
  process.exit(1);
}

if (args.help) {
  console.error(
    `Usage: node flow-generate.js --org <alias> --action <name> --input <json>

Options:
  --org         Salesforce org alias (required)
  --action      Invocable action name (required)
  --input       JSON string with action input parameters

Allowed actions:
  fetchGroundedObjectMetadata   Step 1: fetch org schema metadata
  flowElementSelection          Step 2: select flow elements
  flowElementGeneration         Step 3: generate flow metadata (loop until isComplete)`
  );
  process.exit(0);
}

if (!args.org) {
  console.error("ERROR: --org is required.\nRun with --help for usage.");
  process.exit(1);
}

if (!args.action) {
  console.error("ERROR: --action is required.\nRun with --help for usage.");
  process.exit(1);
}

if (!ALLOWED_ACTIONS.has(args.action)) {
  console.error(
    `ERROR: Unknown action "${args.action}".\n` +
      `  Allowed: ${[...ALLOWED_ACTIONS].join(", ")}`
  );
  process.exit(1);
}

if (!args.input) {
  console.error("ERROR: --input is required.\nRun with --help for usage.");
  process.exit(1);
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function log(...msg) {
  console.error(...msg);
}

function die(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(1);
}

// ── Parse input ─────────────────────────────────────────────────────────────

let inputParams;
try {
  inputParams = JSON.parse(args.input);
} catch (err) {
  die(`Failed to parse input JSON: ${err.message}`);
}

// ── Authenticate ────────────────────────────────────────────────────────────

log(`Authenticating to org '${args.org}'...`);

let orgInfo;
try {
  const raw = execFileSync("sf", ["org", "display", "--json", "-o", args.org], {
    encoding: "utf8",
    stdio: ["pipe", "pipe", "pipe"],
  });
  orgInfo = JSON.parse(raw);
} catch {
  die(
    `Failed to display org '${args.org}'. Is it authenticated?\n  Run: sf org login web --alias "${args.org}"`
  );
}

const token = orgInfo.result?.accessToken;
const instanceUrl = orgInfo.result?.instanceUrl;
const apiVersion = orgInfo.result?.apiVersion;

if (!token || !instanceUrl) {
  die(`Could not extract accessToken or instanceUrl for org '${args.org}'.`);
}

if (!apiVersion) {
  die(`Could not determine API version for org '${args.org}'.`);
}

const apiBase = `${instanceUrl}/services/data/v${apiVersion}`;
log(`  Instance:    ${instanceUrl}`);
log(`  API version: ${apiVersion}`);
log(`  API base:    ${apiBase}`);
log();

// ── Execute action ──────────────────────────────────────────────────────────

async function executeAction(actionName, params) {
  const endpoint = `${apiBase}/actions/standard/${actionName}`;
  const payload = { inputs: [params] };

  log(`POST ${endpoint}`);
  log(`  payload keys: ${Object.keys(params).join(", ")}`);
  log();

  const resp = await fetch(endpoint, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  const text = await resp.text();

  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }

  if (!resp.ok) {
    log(`ERROR: HTTP ${resp.status}`);
    log(typeof body === "string" ? body : JSON.stringify(body, null, 2));
    process.exit(1);
  }

  return body;
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  log(`Action: ${args.action}`);
  log();

  const result = await executeAction(args.action, inputParams);

  // Extract the first (and typically only) output entry
  const output = result?.[0] ?? result;

  // Check for action-level errors
  const errors = output?.errors ?? [];
  if (errors.length > 0) {
    log("Action returned errors:");
    log(JSON.stringify(errors, null, 2));
    process.exit(1);
  }

  const outputValues = output?.outputValues ?? output;

  log("Action completed successfully.");
  log();

  // Print the output as JSON to stdout for the agent to consume
  console.log(JSON.stringify(outputValues, null, 2));
}

main().catch((err) => {
  console.error(`FATAL: ${err.message}`);
  process.exit(1);
});
