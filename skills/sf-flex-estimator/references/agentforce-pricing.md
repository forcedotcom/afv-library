# Agentforce Flex Credit Pricing Reference

## Overview

Agentforce pricing is based on per-invocation charges for prompts and actions. Unlike Data Cloud, Agentforce does **not** use tiered multipliers - pricing is linear.

**Key Concepts:**
- **Per-Invocation Billing**: Each agent execution incurs prompt + action charges
- **Prompt Tiers**: Four tiers based on model capability (2-16 FC)
- **Action Types**: Three types with different rates (16-30 FC)
- **Token Overages**: Additional charges when exceeding token limits
- **No Volume Discounts**: Linear pricing regardless of volume

---

## Prompt/Topic Pricing

### Prompt Tier Table

| Tier | FC per Call | Cost | Model Examples | Use Case |
|------|-------------|------|----------------|----------|
| **Starter (BYOLLM)** | 2 FC | $0.008 | Bring Your Own LLM | Custom model integration |
| **Basic** | 2 FC | $0.008 | Gemini Flash, GPT-4o mini | Simple classification, routing |
| **Standard** | 4 FC | $0.016 | GPT-4o, Claude Sonnet 4 | General-purpose agents |
| **Advanced** | 16 FC | $0.064 | Future deep research models | Complex reasoning, research |

### How to Choose a Tier

**Use Basic (2 FC) when:**
- Simple intent classification
- Yes/no questions
- Basic routing logic
- FAQ responses
- Low-complexity reasoning

**Use Standard (4 FC) when:**
- Multi-step reasoning required
- Context-aware responses
- Integration with multiple data sources
- Moderate complexity workflows
- **Most production agents** (80% of use cases)

**Use Advanced (16 FC) when:**
- Deep research required
- Complex multi-step planning
- Advanced reasoning tasks
- Specialized domain expertise
- High-stakes decision making

**Cost Comparison:**

| Scenario | Basic (2 FC) | Standard (4 FC) | Advanced (16 FC) |
|----------|--------------|-----------------|------------------|
| 1,000 calls | $8 | $16 | $64 |
| 10,000 calls | $80 | $160 | $640 |
| 100,000 calls | $800 | $1,600 | $6,400 |

**Recommendation:** Start with Standard tier for production agents. Downgrade to Basic only for simple classification topics. Reserve Advanced for specialized deep-research topics.

---

## Action Pricing

### Action Type Table

| Action Type | FC per Invocation | Cost | Use Case |
|-------------|-------------------|------|----------|
| **Standard/Custom Action** | 20 FC | $0.08 | API calls, data operations, integrations |
| **Voice Action** | 30 FC | $0.12 | Voice-enabled agent actions |
| **Sandbox Action** | 16 FC | $0.064 | Testing/development actions |

### Action Details

**Standard/Custom Actions (20 FC):**
- Most common action type
- Includes:
  - Apex action invocations
  - Flow invocations
  - External API calls (via Named Credentials)
  - Data operations (SOQL queries, DML)
  - Custom integrations
- Used in 95% of production agents

**Voice Actions (30 FC):**
- Voice-enabled action execution
- 50% premium over standard actions
- Includes:
  - Speech-to-text processing
  - Voice-optimized responses
  - Telephony integrations
- Use when: Voice channel required, accessibility needs

**Sandbox Actions (16 FC):**
- Development/testing environment
- 20% discount vs standard actions
- Use when: Testing new actions, staging environments
- **Not for production use**

---

## Token Overage Pricing

### Token Limits

**Prompt Token Limit:** 2,000 tokens
- Average prompt: 500-1,000 tokens
- ~1,500 words or ~10KB of text
- Includes: System instructions + user input + context

**Action Token Limit:** 10,000 tokens
- Average action: 2,000-5,000 tokens
- ~7,500 words or ~50KB of text
- Includes: Action input + output + metadata

### Overage Charges

**When overage occurs:**
- Additional prompt charge: 1 × prompt tier rate
- Additional action charge: 1 × action rate

**Example: Standard Prompt Overage**
```
Normal prompt (1,500 tokens): 4 FC
Oversized prompt (2,500 tokens): 4 FC + 4 FC = 8 FC
Cost: $0.016 → $0.032 (2x)
```

**Example: Standard Action Overage**
```
Normal action (5,000 tokens): 20 FC
Oversized action (12,000 tokens): 20 FC + 20 FC = 40 FC
Cost: $0.08 → $0.16 (2x)
```

### Overage Frequency

**Typical overage rates:**
- Prompts: <1% in well-designed agents
- Actions: <1% in normal operations

**High overage risk scenarios:**
- Large document grounding (>5 pages)
- Complex multi-step reasoning
- Extensive context injection
- Large API response processing

**How to estimate:**
- Simple agents: 0% overage
- Moderate complexity: 5% prompt overage, 0% action overage
- Complex agents: 20% prompt overage, 1% action overage

### Avoiding Overages

**Prompt optimization:**
- Keep system instructions concise (<500 tokens)
- Limit context injection (<1,000 tokens)
- Use retrieval for large documents (don't embed full text)
- Paginate long responses

**Action optimization:**
- Limit API response sizes
- Use field filtering in SOQL (SELECT only needed fields)
- Paginate large result sets
- Compress action outputs

---

## Per-Invocation Cost Calculation

### Formula

```
per_invocation_fc = Σ(prompt_fc) + Σ(action_fc) + overage_fc
per_invocation_cost = per_invocation_fc × $0.004
```

### Example 1: Simple Customer Service Agent

**Structure:**
- 3 prompts (Basic tier): Classification, Response Generation, Escalation Check
- 2 actions (Standard): Fetch Case Data, Update Case
- No token overages

**Calculation:**
```
Prompts: 3 × 2 FC = 6 FC
Actions: 2 × 20 FC = 40 FC
Total: 46 FC per invocation = $0.184

Monthly costs:
- 1K invocations: 46K FC = $184
- 10K invocations: 460K FC = $1,840
- 100K invocations: 4.6M FC = $18,400
```

### Example 2: Complex Sales Agent

**Structure:**
- 5 prompts (Standard tier): Intent, Lead Qualification, Recommendation, Objection Handling, Summary
- 10 actions (Standard): CRM lookups, opportunity updates, email sends
- 20% prompt overage (complex reasoning)

**Calculation:**
```
Prompts: 5 × 4 FC = 20 FC
Actions: 10 × 20 FC = 200 FC
Overages: 20% × 1 prompt × 4 FC = 0.8 FC (per invocation average)
Total: 220.8 FC per invocation ≈ 221 FC = $0.884

Monthly costs:
- 1K invocations: 221K FC = $884
- 10K invocations: 2.21M FC = $8,840
- 100K invocations: 22.1M FC = $88,400
```

### Example 3: Voice-Enabled Agent

**Structure:**
- 4 prompts (Standard tier): Voice transcription processing, Intent, Response, Confirmation
- 6 actions (Voice): Phone system integration, CRM updates, scheduling
- No overages

**Calculation:**
```
Prompts: 4 × 4 FC = 16 FC
Actions: 6 × 30 FC = 180 FC
Total: 196 FC per invocation = $0.784

Monthly costs:
- 1K invocations: 196K FC = $784
- 10K invocations: 1.96M FC = $7,840
- 100K invocations: 19.6M FC = $78,400
```

---

## Optimization Strategies

### 1. Prompt Tier Optimization

**Before: All Standard Prompts**
```
Agent: 5 prompts (Standard)
Per-invocation: 5 × 4 FC = 20 FC
Cost per 100K: $8,000
```

**After: Mixed Tier Strategy**
```
Agent:
- 2 prompts (Basic): Classification, routing
- 3 prompts (Standard): Main reasoning
Per-invocation: (2 × 2) + (3 × 4) = 16 FC
Cost per 100K: $6,400
Savings: $1,600 (20%)
```

### 2. Action Consolidation

**Before: Many Small Actions**
```
Agent: 10 actions (each a separate API call)
Per-invocation: 10 × 20 FC = 200 FC
Cost per 100K: $80,000
```

**After: Batch Operations**
```
Agent: 4 actions (batch API calls, combined operations)
Per-invocation: 4 × 20 FC = 80 FC
Cost per 100K: $32,000
Savings: $48,000 (60%)
```

**Consolidation techniques:**
- Batch API calls where possible
- Combine related data fetches
- Use composite APIs (e.g., Salesforce Composite API)
- Cache frequently accessed data

### 3. Token Overage Prevention

**Before: 20% Prompt Overages**
```
Base: 5 × 4 FC = 20 FC
Overages: 20% × 5 × 4 FC = 4 FC
Total: 24 FC per invocation
Cost per 100K: $9,600
```

**After: Optimized Context**
```
Base: 5 × 4 FC = 20 FC
Overages: 0% (optimized)
Total: 20 FC per invocation
Cost per 100K: $8,000
Savings: $1,600 (16.7%)
```

### 4. Agent Structure Review

**High-cost patterns to avoid:**
- ❌ Using Advanced tier prompts unnecessarily
- ❌ Calling actions that return unused data
- ❌ Redundant prompts (duplicate reasoning steps)
- ❌ Overly complex system instructions
- ❌ Not batching related operations

**Cost-efficient patterns:**
- ✅ Use Basic tier for classification/routing
- ✅ Batch related API calls
- ✅ Keep system instructions concise
- ✅ Use retrieval instead of full-text embedding
- ✅ Cache frequently accessed data

---

## Agent Structure Templates

### Minimal Agent (Low Cost)

```
Prompts:
- 1 Basic: Intent classification (2 FC)
- 1 Standard: Response generation (4 FC)

Actions:
- 1 Standard: Data fetch (20 FC)

Total: 26 FC per invocation = $0.104
```

**Use case:** Simple FAQ bot, basic routing

### Standard Agent (Balanced)

```
Prompts:
- 1 Basic: Classification (2 FC)
- 3 Standard: Reasoning, response, validation (12 FC)

Actions:
- 5 Standard: Data operations, integrations (100 FC)

Total: 114 FC per invocation = $0.456
```

**Use case:** Customer service, sales agent, most production use cases

### Complex Agent (High Cost)

```
Prompts:
- 2 Basic: Classification, routing (4 FC)
- 5 Standard: Main reasoning (20 FC)
- 1 Advanced: Deep research (16 FC)

Actions:
- 10 Standard: Extensive integrations (200 FC)

Total: 240 FC per invocation = $0.96
```

**Use case:** Complex reasoning, multi-system integration, research agents

---

## Real-World Cost Examples

### Example 1: E-commerce Customer Service (10K invocations/month)

**Agent Structure:**
- 3 Standard prompts: Intent, Product Lookup, Response
- 4 Standard actions: Order lookup, inventory check, update CRM, send email

**Costs:**
```
Prompts: 3 × 4 = 12 FC
Actions: 4 × 20 = 80 FC
Total: 92 FC × 10,000 = 920K FC
Monthly: $3,680
Annual: $44,160
```

### Example 2: Financial Services Advisor (100K invocations/month)

**Agent Structure:**
- 5 Standard prompts: Classification, risk assessment, recommendation, compliance check, summary
- 8 Standard actions: Account lookups, transaction queries, portfolio analysis, reporting
- 10% prompt overage (complex calculations)

**Costs:**
```
Prompts: 5 × 4 = 20 FC
Actions: 8 × 20 = 160 FC
Overages: 0.5 × 4 = 2 FC (average per invocation)
Total: 182 FC × 100,000 = 18.2M FC
Monthly: $72,800
Annual: $873,600
```

### Example 3: Healthcare Appointment Scheduler (Voice, 5K invocations/month)

**Agent Structure:**
- 4 Standard prompts: Transcription processing, intent, scheduling, confirmation
- 6 Voice actions: Phone system, calendar lookups, booking, SMS notifications

**Costs:**
```
Prompts: 4 × 4 = 16 FC
Actions: 6 × 30 = 180 FC
Total: 196 FC × 5,000 = 980K FC
Monthly: $3,920
Annual: $47,040
```

---

## Calculation Checklist

When estimating Agentforce costs:

1. ✅ **Count prompts/topics** by tier (Basic/Standard/Advanced)
2. ✅ **Count actions** by type (Standard/Voice/Sandbox)
3. ✅ **Estimate token overages** (0-20% of prompts, 0-1% of actions)
4. ✅ **Calculate per-invocation FC** (sum of all components)
5. ✅ **Apply to usage scenarios** (1K, 10K, 100K, 500K invocations)
6. ✅ **Document agent structure** (for future re-estimation)
7. ✅ **Identify optimization opportunities** (tier changes, action consolidation)

---

## Common Mistakes

### ❌ Mistake 1: Applying Tiered Multipliers to Agentforce
```python
# WRONG: Agentforce does not use tiered multipliers
af_fc = per_invocation_fc × invocations × 0.8  # No discount!

# CORRECT: Linear pricing
af_fc = per_invocation_fc × invocations
```

### ❌ Mistake 2: Not Counting All Prompts
```python
# WRONG: Only counting "main" prompts
prompts = 2  # Missing classification, validation, etc.

# CORRECT: Count every prompt/topic in agent definition
prompts = 5  # All topics that execute per invocation
```

### ❌ Mistake 3: Overage on Total Instead of Per-Component
```python
# WRONG: Applying overage to total
total_fc = prompt_fc + action_fc
overage_fc = total_fc × 0.20

# CORRECT: Overage on prompts only (usually)
prompt_overage_fc = prompt_fc × 0.20
action_overage_fc = action_fc × 0.01  # Rare
```

---

## Python Calculation Tools

### Using flex_calculator.py

```bash
# Calculate per-invocation cost
python3 flex_calculator.py --mode structure --agent-def agent.json

# Generate full scenarios
python3 flex_calculator.py --mode scenarios \
  --agent-def agent.json \
  --output scenarios.json
```

### Agent Definition JSON Format

```json
{
  "prompts": {
    "basic": 2,
    "standard": 3,
    "advanced": 0
  },
  "actions": {
    "standard": 5,
    "voice": 0,
    "sandbox": 0
  },
  "token_overages": {
    "prompts": 0,
    "actions": 0
  }
}
```

---

## Version History

- **v1.0.0** (2026-03-10): Initial Agentforce pricing reference with per-invocation calculation
