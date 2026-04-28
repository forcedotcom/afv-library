# Apply Grid Examples

These examples are designed to be copied, adapted, and used with the Grid MCP `apply_grid` tool.

Use them after validating the underlying workflow in a real org.

## Example 1: Opportunity Outreach Workbook

Use this when the user wants a quick outreach draft workflow with real Salesforce data and AI-generated follow-up content.

```yaml
workbook: Top Opportunity Outreach
worksheet: Outreach
model: gpt-5-mini

columns:
  - name: Top Opportunities
    type: object
    object: OpportunityContactRole
    soql: >
      SELECT OpportunityId, ContactId, IsPrimary,
             Opportunity.Name, Opportunity.Amount, Opportunity.StageName,
             Opportunity.Account.Name,
             Contact.Name, Contact.Email
      FROM OpportunityContactRole
      WHERE IsPrimary = true
        AND Opportunity.Amount != NULL
      ORDER BY Opportunity.Amount DESC NULLS LAST
      LIMIT 10

  - name: Opportunity Name
    type: reference
    source: Top Opportunities
    field: Opportunity.Name

  - name: Amount
    type: reference
    source: Top Opportunities
    field: Opportunity.Amount

  - name: Stage
    type: reference
    source: Top Opportunities
    field: Opportunity.StageName

  - name: Account Name
    type: reference
    source: Top Opportunities
    field: Opportunity.Account.Name

  - name: Contact Name
    type: reference
    source: Top Opportunities
    field: Contact.Name

  - name: Contact Email
    type: reference
    source: Top Opportunities
    field: Contact.Email

  - name: Email Subject
    type: ai
    instruction: >
      Write a concise, professional outbound email subject line for {Contact Name}
      at {Account Name} about the {Opportunity Name} opportunity.
      Keep it under 9 words and avoid hype.
    responseFormat: plain_text

  - name: Draft Email
    type: ai
    instruction: >
      Write a professional sales outreach email to {Contact Name} at {Account Name}
      about the opportunity "{Opportunity Name}".
      The opportunity amount is {Amount} and the current stage is {Stage}.
      Address the contact by first name if possible.
      Keep it between 120 and 170 words.
      Mention business value and a clear next step.
      Sound consultative, not pushy.
      Do not invent product claims beyond the context provided.
    responseFormat: plain_text
```

## Example 2: Agent Test Workbook

Use this when the user wants a reproducible agent test harness from YAML.

```yaml
workbook: Agent Test Suite
worksheet: Tests
model: gpt-5-mini

columns:
  - name: Utterances
    type: text

  - name: Expected Response
    type: text

  - name: Agent Output
    type: agent_test
    agent: Sales Agent
    inputUtterance: Utterances
    isDraft: false

  - name: Coherence
    type: eval/coherence
    input: Agent Output

  - name: Response Match
    type: eval/response_match
    input: Agent Output
    reference: Expected Response

data:
  Utterances:
    - "I want pricing for your enterprise package."
    - "Can you summarize the implementation timeline?"
    - "Who should I talk to about a renewal?"
  Expected Response:
    - "Pricing and packaging guidance"
    - "Implementation timeline summary"
    - "Renewal contact guidance"
```

## Example 3: Prompt Template Pipeline

Use this when the org already has a prompt template and the user wants a repeatable worksheet built around it.

```yaml
workbook: Prompt Template Pipeline
worksheet: Prompt Runs
model: gpt-5-mini

columns:
  - name: Source Text
    type: text

  - name: Generated Summary
    type: prompt_template
    template: Account_Summary
    inputs:
      input1: "{Source Text}"

data:
  Source Text:
    - "Acme is preparing for a renewal and needs a concise executive summary."
    - "Globex is evaluating expansion and wants a sales-ready summary."
```

## Usage Notes

- Validate the real workflow interactively first if the org is unfamiliar.
- Prefer `reference` columns for extracted fields before writing large AI prompts.
- Keep YAML specs centered on column names so they remain easy to maintain.
- When org-specific IDs are required, resolve them first and then make the YAML as portable as possible around names and structure.
