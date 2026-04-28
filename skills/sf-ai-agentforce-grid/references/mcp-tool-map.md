# Grid MCP Tool Map

This is a practical grouping of the Grid MCP surface discovered from the MCP server source.

## Workbooks

- `get_workbooks`
- `create_workbook`
- `get_workbook`
- `get_workbook_worksheets`
- `delete_workbook`

Use these for top-level Grid containers.

## Worksheets

- `create_worksheet`
- `get_worksheet`
- `get_worksheet_data`
- `get_worksheet_data_generic`
- `update_worksheet`
- `delete_worksheet`
- `add_rows`
- `delete_rows`
- `import_csv`
- `run_worksheet`
- `get_run_worksheet_job`

Use `get_worksheet_data` as the primary read endpoint.

## Columns

- `add_column`
- `edit_column`
- `delete_column`
- `save_column`
- `reprocess_column`
- `get_column_data`
- `create_column_from_utterance`
- `generate_json_path`

Use `add_column` with full config when precision matters.
Use `create_column_from_utterance` for quick exploration.

## Cells And Execution

- `update_cells`
- `paste_data`
- `trigger_row_execution`
- `validate_formula`
- `generate_ia_input`

These are helpful after worksheet structure exists.

## Org Metadata

- `get_column_types`
- `get_llm_models`
- `get_supported_types`
- `get_evaluation_types`
- `get_formula_functions`
- `get_formula_operators`
- `get_invocable_actions`
- `describe_invocable_action`
- `get_prompt_templates`
- `get_prompt_template`
- `get_list_views`
- `get_list_view_soql`
- `generate_soql`
- `generate_test_columns`

Use these instead of guessing available models, templates, actions, or field grammar.

## Salesforce Data Discovery

- `get_sobjects`
- `get_sobject_fields_display`
- `get_sobject_fields_filter`
- `get_sobject_fields_record_update`
- `get_dataspaces`
- `get_data_model_objects`
- `get_data_model_object_fields`

Use these before building Object and DataModelObject columns.

## Agents

- `get_agents`
- `get_agent_variables`

Use `get_agents` first, then read the agent's active version and variables before configuring `Agent` or `AgentTest` columns.

## Higher-Level Workflow Helpers

- `create_workbook_with_worksheet`
- `poll_worksheet_status`
- `get_worksheet_summary`
- `setup_agent_test`

These are the fastest way to get working results for common workflows.

## Declarative Grid Build

- `apply_grid`

Use this when you want to create or update a worksheet from YAML.
It is good for repeatable recipes and repo-stored specs.

## URL Helper

- `get_url`

Use this to produce a Lightning URL for Grid Studio, records, flows, or setup pages after creating something.
