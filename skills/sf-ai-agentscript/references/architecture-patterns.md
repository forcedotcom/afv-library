<!-- Parent: sf-ai-agentscript/SKILL.md -->

# Architecture Patterns

Use these patterns when deciding how much should be deterministic, how much should be LLM-directed, and how to split work across topics.

---

## Control Heuristic

- Start with the minimum deterministic control needed.
- Script only where “mostly right” is unacceptable.
- Keep high-variance conversation LLM-directed when possible.
- If the workflow has no real reasoning need, use Flow or Apex.

---

## Pattern 0: Deterministic Sandwich

Apply hard control at the edges and leave the middle flexible.

```text
gate / triage / auth  →  flexible worker topic(s)  →  deterministic closeout
```

**Use when:**
- auth or verification must happen first
- compliance text or closeout steps must always run
- the middle still benefits from flexible reasoning

**Anti-pattern:** scripting the whole conversation when only the edges need guarantees. If the middle is also fixed, use Flow or Apex.

---

## Pattern 1: Hub and Spoke

Central router (hub) to specialized topics (spokes). Use for multi-purpose agents.

```
       ┌─────────────┐
       │  router     │
       │   (hub)     │
       └──────┬──────┘
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│refunds │ │ orders │ │support │
└────────┘ └────────┘ └────────┘
```

**Use when:** the first turn is mostly classification and each downstream topic owns a distinct capability.

**Routing note:** keep spoke descriptions semantically non-overlapping. If one utterance plausibly fits two spokes, merge, split, or rename them.

---

## Pattern 2: Verification Gate

Security gate before protected topics. Mandatory for sensitive data.

```
┌─────────┐     ┌──────────┐     ┌───────────┐
│  entry  │ ──▶ │ VERIFY   │ ──▶ │ protected │
└─────────┘     │  (GATE)  │     │  topics   │
                └────┬─────┘     └───────────┘
                     │ 3 fails
                     ▼
                ┌──────────┐
                │ lockout  │
                └──────────┘
```

**Use when:** account access, protected updates, regulated data, or irreversible actions require a hard precondition.

---

## Pattern 3: Post-Action Loop

Topic re-resolves after action completes — put completion checks at the **top**.

```yaml
topic refund:
  reasoning:
    instructions: ->
      # POST-ACTION CHECK (at TOP - triggers on next loop)
      if @variables.refund_status == "Approved":
        run @actions.create_crm_case
        transition to @topic.success

      # PRE-LLM DATA LOADING
      run @actions.check_churn_risk
      set @variables.risk = @outputs.score

      # DYNAMIC INSTRUCTIONS FOR LLM
      if @variables.risk >= 80:
        | Offer full refund to retain customer.
      else:
        | Offer $10 credit instead.
```

**Use when:** an action updates state and the next deterministic branch depends on that updated state.

---

## Pattern 4: Staged Multi-Turn Workflow

When a workflow naturally spans **multiple user turns**, model each phase as its own topic instead of keeping a single topic with `step = 1 / 2 / 3` flags.

```yaml
variables:
  lookup_id: mutable string = ""
  lookup_result: mutable string = ""

topic collect_lookup_id:
  description: "Collect the identifier needed for the lookup"
  reasoning:
    instructions: ->
      if @variables.lookup_id == "":
        | Ask the user for the identifier, then call {!@actions.save_lookup_id}.
      else:
        transition to @topic.run_lookup
    actions:
      save_lookup_id: @utils.setVariables
        description: "Save the identifier for the next stage"
        with lookup_id = ...

topic run_lookup:
  description: "Run the lookup after the identifier is known"
  reasoning:
    instructions: ->
      if @variables.lookup_result != "":
        transition to @topic.present_lookup_result

      run @actions.lookup_record
        with lookup_id = @variables.lookup_id
        set @variables.lookup_result = @outputs.result

topic present_lookup_result:
  description: "Present the lookup result"
  reasoning:
    instructions: |
      Share {!@variables.lookup_result} with the user.
```

**Why this pattern is safer:**
- user input capture stays LLM-directed
- deterministic work only runs after required state exists
- each turn boundary is explicit
- transitions are easier to debug than step counters

**Anti-pattern to avoid:** one large topic that increments a `step` variable and accidentally triggers step 2 in the same turn that finished step 1.

---

## Pattern 5: Multi-Intent Orchestration

If a user can ask about **more than one independent intent in the same utterance**, decide the architecture based on the desired response style.

| Scenario | Recommended pattern |
|---|---|
| User may ask about several independent tasks in one message | Expose specialist topics/capabilities as delegated tools and let the orchestrator route between them |
| One business process spans multiple turns in sequence | Use staged topics with explicit transitions |
| Only the final stage should produce the user-facing answer | Use intermediate work topics, then transition to a final presentation topic |

**Lightweight router example:**

```yaml
start_agent router:
  description: "Route to the right specialist"
  reasoning:
    instructions: |
      Determine which specialist capability is needed.
    actions:
      handle_shipping: @topic.shipping_status
        description: "Handle shipping status questions"
      handle_returns: @topic.returns
        description: "Handle return questions"
      handle_billing: @topic.billing
        description: "Handle billing questions"
```

**Guidance:**
- For genuine multi-intent handling, prefer specialist tools/topics over building a queue string in one monolithic topic.
- For single-intent chained workflows, prefer `after_reasoning` or explicit topic transitions.
- If the orchestrator should not answer directly, let worker topics do the work and transition to one final response topic.

---

## Quick Decision Guide

| Need | Prefer |
|---|---|
| Hard gating before sensitive actions | Verification Gate |
| Critical gate + flexible middle + must-run closeout | Deterministic Sandwich |
| Deterministic branch after action result | Post-Action Loop |
| Multi-turn data collection then deterministic execution | Staged Multi-Turn Workflow |
| Multiple specialist capabilities | Hub and Spoke |
| Several possible intents in one utterance | Multi-Intent Orchestration |
| Fully fixed workflow with no real reasoning need | Flow or Apex instead of full Agent Script |
