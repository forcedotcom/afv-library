# Grid Recipes

## Recipe 1: Object -> Reference -> AI

This is the most reliable composition pattern for business worksheets.

1. Import records with one `Object` column.
2. Extract exact fields with `Reference` columns.
3. Add AI or Agent columns that run `EACH_ROW`.
4. Read back results from `get_worksheet_data`.

Use this when:

- prompts need clean field inputs
- nested object structures are awkward
- you want readable intermediate columns for debugging

## Recipe 2: Top Opportunities Outreach

Goal:

- pull a ranked set of opportunities
- get a real contact email
- generate subject lines and drafts

Recommended source:

- `OpportunityContactRole`

Reason:

- many orgs do not populate a single primary contact lookup directly on `Opportunity`
- `OpportunityContactRole WHERE IsPrimary = true` is often more reliable for outreach scenarios

Example SOQL:

```sql
SELECT OpportunityId, ContactId, IsPrimary,
       Opportunity.Name, Opportunity.Amount, Opportunity.StageName,
       Opportunity.Account.Name,
       Contact.Name, Contact.Email
FROM OpportunityContactRole
WHERE IsPrimary = true
  AND Opportunity.Amount != NULL
ORDER BY Opportunity.Amount DESC NULLS LAST
LIMIT 10
```

Recommended follow-up reference columns:

- `Opportunity.Name`
- `Opportunity.Amount`
- `Opportunity.StageName`
- `Opportunity.Account.Name`
- `Contact.Name`
- `Contact.Email`

Recommended AI outputs:

- `Email Subject`
- `Draft Email`
- optional `CTA Recommendation`
- optional `Risk / Objection Guess`

## Recipe 3: Agent Test Suite

Good shape:

1. Text column for utterances
2. Optional text column for expected outputs
3. `AgentTest` column
4. One or more evaluation columns

Useful evaluation types:

- `COHERENCE`
- `COMPLETENESS`
- `INSTRUCTION_FOLLOWING`
- `RESPONSE_MATCH`
- `TOPIC_ASSERTION`

## Recipe 4: Prompt Template Pipeline

Good shape:

1. Input source column
2. Reference columns for prompt inputs
3. Prompt template column
4. Optional evaluation column

Use this when the org already has prompt templates the user wants to operationalize in Grid.

## Recipe 5: Invocable Action / Flow Testing

Good shape:

1. Source text/object columns
2. Invocable action column
3. Reference columns that extract outputs

Use metadata discovery first:

- get invocable actions
- describe the action
- generate IA input if needed

## Prompt Design Tips For Grid AI Columns

- Keep prompts grounded in worksheet columns.
- Use extracted reference columns instead of deep nested references where possible.
- Tell the model exactly what output shape you want.
- Keep draft-email prompts explicit about length, tone, and prohibited invention.
- Treat first-pass subject lines as prototypes.

## Reading Results Correctly

In `v66.0`, worksheet payloads are rowless by default:

- use `columnData`
- group cells by `worksheetRowId`
- map each `worksheetColumnId` back to its column name

Use the bundled script when you want a row table:

```powershell
node scripts/worksheet_to_rows.mjs <worksheet-id>
```
