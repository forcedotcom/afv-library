# AI Decision Element Guide

## Overview

The AI Decision element ("Define with AI") lets AI evaluate flow data at runtime to determine which outcome path to follow. Instead of manually defining conditions (e.g., "Status equals Closed"), you write natural-language instructions and AI decides which outcome fires.

Introduced in API version 62.0 (Spring '25). Requires Einstein AI credits.

---

## XML Structure

An AI Decision is a standard `<decisions>` element with `<attributes>` blocks of type `LlmPrompt`. There is no separate element type — the `<attributes>` block is the only difference from a manual decision.

### Decision-level instructions

```xml
<decisions>
    <name>Route_Case_Based_on_Sentiment</name>
    <label>Route Case Based on Sentiment</label>
    <attributes>
        <type>LlmPrompt</type>
        <value>Detect the sentiment on the case based on subject
        &quot;{!Get_Case.Subject}&quot; and description
        &quot;{!Get_Case.Description}&quot; as Negative, Positive,
        Neutral, or Undetermined.</value>
    </attributes>
    <defaultConnector>
        <targetReference>Handle_Default</targetReference>
    </defaultConnector>
    <defaultConnectorLabel>Not Negative</defaultConnectorLabel>
    <rules>
        ...
    </rules>
</decisions>
```

### Outcome-level instructions

Each `<rules>` block (outcome) also gets an `<attributes>` block describing when AI should choose that path:

```xml
<rules>
    <name>Negative</name>
    <attributes>
        <type>LlmPrompt</type>
        <value>The customer&apos;s sentiment is Negative. The case
        subject or description contains language indicating frustration,
        anger, dissatisfaction, complaint, or urgency.</value>
    </attributes>
    <conditionLogic>and</conditionLogic>
    <connector>
        <targetReference>Assign_to_Senior_Support</targetReference>
    </connector>
    <label>Negative</label>
</rules>
```

### Key structural notes

| Aspect | Detail |
|---|---|
| Element type | Standard `<decisions>` — no new XML element |
| AI marker | `<attributes><type>LlmPrompt</type><value>...</value></attributes>` |
| Decision instructions | `<attributes>` as a direct child of `<decisions>` |
| Outcome instructions | `<attributes>` as a direct child of each `<rules>` |
| Conditions | No `<conditions>` block needed; `<conditionLogic>and</conditionLogic>` is present but vestigial |
| Default outcome | No `<attributes>` block needed — it catches everything not matched |
| Merge fields | Use `{!Element.Field}` references in prompt text so AI has data context |
| XML escaping | `&quot;` for quotes, `&apos;` for apostrophes inside `<value>` |

---

## When to Use AI Decision vs Manual Decision

| Use AI Decision when | Use manual Decision when |
|---|---|
| Conditions are subjective (sentiment, intent, tone) | Conditions are objective (status = "Closed") |
| You need NLP-style evaluation of free-text fields | You're comparing picklist or numeric values |
| The routing logic would require many complex rules | A few simple conditions cover all cases |
| You want flexible, less predetermined outcomes | Deterministic behavior is required |

---

## Writing Effective Instructions

### Decision Instructions (element level)
- Describe the **overall decision** the AI is making
- Include **merge field references** (`{!Get_Case.Subject}`) so AI has data
- List all possible categories the AI should classify into
- Be specific about what data to evaluate

**Good:**
> Detect the sentiment on the case based on subject "{!Get_Case.Subject}" and description "{!Get_Case.Description}" as Negative, Positive, Neutral, or Undetermined.

**Bad:**
> Figure out the sentiment.

### Outcome Instructions (rule level)
- Describe **when this specific outcome applies**
- Include concrete indicators or signals AI should look for
- Be mutually exclusive with other outcomes where possible

**Good:**
> The customer's sentiment is Negative. The subject or description contains language indicating frustration, anger, dissatisfaction, complaint, or urgency.

**Bad:**
> Negative sentiment.

---

## Governance and Cost

- Each AI Decision evaluation **consumes Einstein credits**. Monitor usage in Setup > Digital Wallet.
- Avoid placing AI Decision elements inside loops — each iteration costs credits.
- AI Decision adds latency (LLM call) — not suitable for high-volume record-triggered flows.
- Best suited for **autolaunched flows, screen flows, or low-volume triggers**.
- Debug your automation to verify AI is routing to the correct outcome before activation.

---

## Template

See [`assets/ai-decision-template.xml`](../assets/ai-decision-template.xml) for a copy-paste starting point.
