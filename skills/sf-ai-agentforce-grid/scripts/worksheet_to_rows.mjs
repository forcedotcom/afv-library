#!/usr/bin/env node

import {
  gridRequestJson,
  sanitizeForAgent,
  wrapUntrustedGridData,
} from "./grid_rest_utils.mjs";

function usage() {
  console.error("Usage: node scripts/worksheet_to_rows.mjs <worksheetId> [--columns col1,col2] [--target-org alias]");
  process.exit(1);
}

const args = process.argv.slice(2);
if (args.length < 1) usage();

const worksheetId = args[0];
let columnsFilter;
let targetOrg;

for (let i = 1; i < args.length; i++) {
  if (args[i] === "--columns") {
    columnsFilter = args[i + 1]?.split(",").map((s) => s.trim()).filter(Boolean);
    i += 1;
  } else if (args[i] === "--target-org") {
    targetOrg = args[i + 1];
    i += 1;
  }
}

let payload;
try {
  payload = gridRequestJson({
    method: "GET",
    gridPath: `/worksheets/${encodeURIComponent(worksheetId)}/data`,
    targetOrg,
  });
} catch (error) {
  console.error("Failed to read worksheet data.");
  console.error(String(error.stderr || error.stdout || error.message || error));
  process.exit(1);
}

const columnNameById = Object.fromEntries((payload.columns ?? []).map((c) => [c.id, c.name]));
const rowMap = new Map();

for (const [columnId, cells] of Object.entries(payload.columnData ?? {})) {
  const columnName = columnNameById[columnId] ?? columnId;
  for (const cell of cells) {
    const rowId = cell.worksheetRowId;
    if (!rowMap.has(rowId)) rowMap.set(rowId, { worksheetRowId: rowId });
    rowMap.get(rowId)[columnName] = sanitizeForAgent(cell.displayContent);
  }
}

let rows = Array.from(rowMap.values());
if (columnsFilter?.length) {
  rows = rows.map((row) => {
    const filtered = { worksheetRowId: row.worksheetRowId };
    for (const columnName of columnsFilter) filtered[columnName] = row[columnName];
    return filtered;
  });
}

console.log(JSON.stringify(wrapUntrustedGridData("salesforce-grid-worksheet-data", {
  worksheetId,
  worksheetName: sanitizeForAgent(payload.name),
  workbookId: sanitizeForAgent(payload.workbookId),
  rowCount: rows.length,
  rows,
}), null, 2));
