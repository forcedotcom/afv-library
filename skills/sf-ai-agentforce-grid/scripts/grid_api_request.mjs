#!/usr/bin/env node

import { gridRequestJson, wrapUntrustedGridData } from "./grid_rest_utils.mjs";

function usage() {
  console.error("Usage: node scripts/grid_api_request.mjs <METHOD> <PATH> [JSON_BODY] [--target-org alias]");
  process.exit(1);
}

const args = process.argv.slice(2);
if (args.length < 2) usage();

const method = args[0].toUpperCase();
const path = args[1];

let bodyArg;
let targetOrg;

for (let i = 2; i < args.length; i++) {
  if (args[i] === "--target-org") {
    targetOrg = args[i + 1];
    i += 1;
  } else if (bodyArg === undefined) {
    bodyArg = args[i];
  }
}

let parsedBody;
if (bodyArg !== undefined) {
  try {
    parsedBody = JSON.parse(bodyArg);
  } catch (error) {
    console.error("JSON_BODY must be valid JSON.");
    console.error(String(error));
    process.exit(1);
  }
}

try {
  const payload = gridRequestJson({
    method,
    gridPath: path,
    body: parsedBody,
    targetOrg,
  });
  console.log(JSON.stringify(wrapUntrustedGridData("salesforce-grid-api-response", payload), null, 2));
} catch (error) {
  console.error("Grid API request failed.");
  console.error(String(error.stderr || error.stdout || error.message || error));
  process.exit(1);
}
