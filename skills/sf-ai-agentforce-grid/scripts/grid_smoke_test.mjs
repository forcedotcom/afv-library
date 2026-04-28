#!/usr/bin/env node

import {
  gridRequestWithStatus,
  wrapUntrustedGridData,
} from "./grid_rest_utils.mjs";

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--target-org") {
      out.targetOrg = argv[i + 1];
      i += 1;
    }
  }
  return out;
}

const { targetOrg } = parseArgs(process.argv.slice(2));

function req(method, path, body) {
  return gridRequestWithStatus({
    method,
    gridPath: path,
    body,
    targetOrg,
  });
}

const summary = {
  auth: {
    targetOrg: targetOrg ?? "default-configured-org",
    authDelegatedTo: "salesforce-cli",
  },
};

try {
  summary.workbooks = req("GET", "/workbooks");
  summary.models = req("GET", "/llm-models");
  summary.agents = req("GET", "/agents");

  const workbookName = `Grid Smoke Test ${new Date().toISOString().replace(/[:.]/g, "-")}`;
  const workbook = req("POST", "/workbooks", { name: workbookName });
  summary.createWorkbook = workbook;

  if (workbook.ok && workbook.payload?.id) {
    const workbookId = workbook.payload.id;
    summary.defaultWorksheets = req("GET", `/workbooks/${workbookId}/worksheets`);
    summary.deleteWorkbook = req("DELETE", `/workbooks/${workbookId}`);
  }
} catch (error) {
  console.error("Grid smoke test failed.");
  console.error(String(error.stderr || error.stdout || error.message || error));
  process.exit(1);
}

console.log(JSON.stringify(wrapUntrustedGridData("salesforce-grid-smoke-test", summary), null, 2));
