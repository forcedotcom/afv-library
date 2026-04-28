---
name: sf-ai-agentforce-persona
description: >
  Deep persona design for Agentforce agents with 50-point scoring.
  TRIGGER when: user designs agent personas, defines agent personality/identity,
  creates persona documents, encodes persona into Agentforce Builder fields or
  Agent Script, translates brand guidelines to agent voice, or asks about
  agent tone/voice/register.
  DO NOT TRIGGER when: building agent metadata (use sf-ai-agentforce), testing
  agents (use sf-ai-agentforce-testing), or Agent Script DSL
  (use sf-ai-agentscript).
license: MIT
allowed-tools: Read Write AskUserQuestion Glob Grep
metadata:
  version: "2.4.0"
  author: "cascadi"
  scoring: "50 points across 5 categories"
  last_validated: "2026-03-31"
  tags: "salesforce, agentforce, persona, identity, register, formality, warmth, personality, tone, brevity, humor, chatting-style, brand-input, sample-dialog"
---

# Agent Persona Design

## How to Use

This skill designs an AI agent persona through a fast input-to-sample-dialog loop. Provide any starting input — a brand guide PDF, a URL, a prior persona document, or a text description — and the skill drafts a complete persona, shows you how the agent sounds in sample dialog, and lets you refine until it's right.

**What it produces:**
- A persona document (`_local/generated/[agent-name]-persona.md`) defining who the agent is, how it sounds, and what it never does
- Scoring available on request (50-point rubric)
- Encoding available as a separate workflow (persona → tool-specific field values)

**What it drives downstream:** The persona document feeds into conversation design and Agentforce encoding. Those are separate steps — this skill defines the *persona*, not dialog flows or field configurations.

**Session resumption:** If you stop mid-workflow, your partial progress is preserved in the conversation and can be resumed.

## When to Use This Skill

- Designing a new Agentforce agent and need to define its personality before building
- Retrofitting persona consistency onto an existing agent whose tone is inconsistent
- Translating brand guidelines or tone documents into a structured persona
- Aligning stakeholders on what an agent should sound like before development begins
- Documenting an agent's voice for handoff between design and implementation teams

**Scope boundary:** This skill defines WHO the agent is. It does not define dialog flows, utterance templates, or interaction branching — those belong in conversation design.

**Delegate elsewhere when:**
- building agent metadata, topics, or actions → [sf-ai-agentforce](../sf-ai-agentforce/SKILL.md)
- testing finished agent behavior → [sf-ai-agentforce-testing](../sf-ai-agentforce-testing/SKILL.md)
- encoding deterministic `.agent` logic or FSM behavior → [sf-ai-agentscript](../sf-ai-agentscript/SKILL.md)

## Framework Reference

Read `references/persona-framework.md` for the full framework. It defines:

- **Identity** — 3-5 personality adjectives that anchor every other decision
- **12 dimensions** across 5 categories:
  - **Register** — Subordinate / Peer / Advisor / Coach
  - **Voice** — Formality, Warmth, Personality Intensity (3 independent dimensions)
  - **Tone** — Emotional Coloring, Empathy Level (+ Tone Boundaries, Tone Flex)
  - **Delivery** — Brevity, Humor
  - **Chatting Style** — Emoji, Formatting, Punctuation, Capitalization
- **Phrase Book & Never-Say List** — what to say and what to never say
- **Tone Flex** — how tone shifts by context
- **Lexicon** — per-topic vocabulary

Dimensions are ordered by dependency — upstream choices constrain downstream ones. Constraint notes in the framework explain how earlier choices pull later ones. Constraints are recommendations, not hard locks — any combination is valid.

---

## Entry Point Detection

Detect the user's intent from their opening message:

- **User provides brand input, text description, or no document** → **Design flow** (below)
- **User provides a completed persona.md document and asks to encode** → **Encode flow** (below)
- **User provides a persona.md + a list of topics or actions** → **Encode flow**
- **User provides a completed persona.md without stating intent** → Show a compact summary of the loaded persona, then offer the hub menu (refine, score, encode). Do not assume encode.
- **Ambiguous** → Ask: "Are you designing a new persona or encoding an existing one for Agentforce?"

---

## Design Flow

Two phases: **Phase 1 (Essentials)** gets to sample dialog as fast as possible. **Phase 2 (Electives)** lets the user choose what to do next.

```
PHASE 1: INPUT → CONTEXT → DRAFT → PERSONA → SAMPLE DIALOG
                                                    │
PHASE 2:                                      ┌─────┴─────┐
                                              │  HUB MENU │
                                              └─────┬─────┘
                                        ┌───────────┼───────────┐
                                        │           │           │
                                   Refine      Explore      Export
                                 (identity,  (different   (download,
                                  dimensions, scenario)    score,
                                  phrase book,              encode)
                                  never-say,
                                  tone flex,
                                  lexicon)
```

### Phase 1: Essentials

#### Step 1: Input

Accept any starting input. No detection question needed — accept whatever the user provides.

**Accepted inputs:**
- Brand guide or tone-of-voice document (PDF, text)
- Organization URL
- Prior persona document (persona.md from a previous session)
- Free-text description (e.g., "a sales coach who talks like Crocodile Dundee")
- Existing agent system prompt or Agent Script file
- Any combination of the above

**If the user provides nothing** (invokes the skill without additional input):
> "Share something to get started — a brand guide, a URL, or just describe the agent in your own words. I'll draft a persona and show you how it sounds in conversation."

Do NOT ask a detection question. Accept whatever arrives and proceed.

#### Step 2: Minimal Context

Collect only what the input doesn't already answer. **Every question is skippable.** Zero questions is valid — if the input provides enough signal, skip directly to Draft.

**Context signals to extract or ask about (priority order):**

1. **Company** — who they are, what they do, who they serve. If the user provided a brand guide or URL, extract this — don't re-ask.
2. **Audience** — who the agent serves: internal employee, external customer, partner, vendor, investor, or other. Affects register, formality, warmth. If the user says "internal sales coach," audience is already answered.
3. **Modality** — how the agent communicates: chat, email, telephony, multimodal, or other. Affects Chatting Style, Brevity, and whether emoji makes sense. Multiple modalities are valid.
4. **Primary language** — affects formality norms and cultural adaptation.
5. **At least 1 use case or JTBD** — needed to generate meaningful sample dialog.

**Do NOT collect:** interaction model (agent design, not persona), agent type (agent design, not persona), topic list, agent name (comes after identity).

**Extraction before asking:** Parse the user's input for context signals before deciding what to ask. "Design an internal sales coach persona for Buc-ee's" already answers audience (internal), role (sales coach), and implies a brand context. Don't re-ask what's already given.

**May ask 1-2 clarifying questions** to surface tensions in the input (e.g., "Your brand guide emphasizes both 'bold irreverence' and 'trusted expertise' — which should win when they conflict?"). But every question is skippable.

#### One-Shot vs. Wizard

After extracting context, assess the richness of the input:

- **Rich input** (brand guide PDF, detailed description, prior persona, URL with strong brand copy): Offer the user a choice — "I have strong signals — I can draft the full persona now and show you how it sounds, or walk through each dimension category if you prefer." Default to **one-shot**: draft everything silently, present the persona, then show sample dialog.
- **Minimal input** (brief description, just a company name): Default to **wizard**: ask context questions, walk through dimensions by dependency tier.
- **Blank slate** (no input at all): Prompt for input first, then wizard path.

Either path leads to the same output. The user can always override — a one-shot user can refine afterward, and a wizard user can skip ahead.

#### Step 3: Draft

This step is the skill's intelligence — it must execute explicitly as specified below.

##### 3A: Input Parsing

Extract persona signals from the user's input. Brand guides are often much richer than they appear — mine them thoroughly. A good brand guide can populate identity, dimensions, phrase book, never-say list, AND lexicon in a single pass. Aim to use **80%+ of actionable content.**

| Signal Type | What to Look For | Maps To |
|---|---|---|
| **Voice/tone** | Adjectives, "we are..." statements, voice pillars ("clear, concise, authoritative") | Identity traits, dimensions |
| **Negative** | "Never," "don't," prohibited words/phrasings ("say 'complimentary' not 'free'"), prohibited greetings | Never-Say List, Phrase Book |
| **Vocabulary** | Brand name, product lines → global. Brand "isms," preferred terms → global or per-topic. Domain jargon → per-topic. Preferred vs. prohibited word pairs | Global Lexicon, per-topic Lexicon, Never-Say + Phrase Book pairs |
| **Formatting** | Capitalization rules, punctuation opinions (Oxford comma, em dashes), number/date/price formatting, foreign word formatting | Chatting Style dimensions + custom section |
| **CTAs/interaction** | CTA patterns ("SHOP NOW"), promotional language rules | Phrase Book + Never-Say |
| **Usage rules** | Preposition preferences ("at [brand]" not "from [brand]"), standards that would sound wrong if violated | Never-Say + Phrase Book |
| **Audience** | Who the brand talks to, formal vs. informal examples, relationship language | Design Inputs, Register, Formality |

**If input is a prior persona.md:** Extract dimensions directly.

##### 3B: Dimension Selection

Map extracted signals to the 12 framework dimensions:

1. Pre-populate all 12 dimensions from the input signals
2. Override dimensions where the input provides clear signals (e.g., brand guide says "never use slang" → Formality: Formal)
3. For each dimension, show the full spectrum and indicate which value is recommended and why when there's a strong signal

##### 3C: Confidence Annotations

Mark each dimension as:
- **Strong signal** — clear evidence in input (quote or cite the source)
- **Default** — inferred from context, no direct evidence in input

These annotations are shown during refinement so the designer knows where to focus.

##### 3D: Generation

From the dimension map, generate:
- **Identity traits** — 3-5 adjectives with behavioral definitions
- **Phrase Book** — example phrases tuned to all selected dimensions. Generate **2-4 phrases per category** — one example is not enough to establish a pattern. Categories include:
  - **All agents:** Acknowledgement, Affirmation, Apologies (for agent mistakes only — not system errors), Off-Topic Redirect (steering back from out-of-scope requests), Welcome/Greeting
  - **External-facing agents (customer, vendor, investor):** Escalation/Handoff (passing to a human)
  - **Encouraging/Enthusiastic coloring:** Celebrating Progress
  - **Coach register:** Teaching Moments
  - **Humor ≠ None:** Humor Examples (showing the humor type in context)
  - **Optional (any agent):** Returning Customer Greeting (personalized re-engagement)
  - Do **not** include errors or system error handling in the Phrase Book — error messages are generated as required messages during encoding
- **Never-Say List** — anti-phrases derived from Tone Boundaries, Identity contradictions, and input's negative signals. Generate **at least 5 entries** — cover generic chatbot filler, register violations, and persona-specific anti-phrases
- **Tone Boundaries** — what the agent must never sound like
- **Tone Flex** — baseline + triggers + shift rules
- **Negative Identity** — 2-4 character-level anti-patterns. Generate from negative signals in the input and from Identity traits.
- **Global Lexicon** — brand name, company name, product line names, industry terms used across all topics.
- **Values** *(optional)* — Only if the user explicitly stated beliefs, values, or worldview. Never infer values.

##### 3E: Name

After identity traits are established:
- Suggest up to 3 names that distill the identity
- Allow the user to write their own
- Reassure: "You can change this later."

If a name was provided in input, use it and skip this sub-step.

##### 3F: State Object

Maintain the full dimension map as an explicit **state object** across the conversation. Every regeneration works from this state, not from conversation history. The state object contains:
- All 12 dimension values
- Confidence annotation per dimension (strong signal / default)
- Identity traits
- Negative Identity statements
- Values (if provided by user — never inferred)
- Phrase Book
- Never-Say List
- Tone Boundaries
- Tone Flex rules

Update the state object on every change. When regenerating sample dialog, read from the state object.

##### Interaction Design

These guidelines apply across all surfaces — CLI, TUI, web, IDE. Each environment adapts the patterns to its own idiom.

**Output before questions.** Show generated content (dimensions, phrase book, tone flex) as regular output first. Then ask a concise question with short options. Never embed long content inside question labels or option descriptions — it will be truncated in constrained environments and is harder to read everywhere.

**Batch independent questions.** When multiple questions have no dependency relationship — meaning neither answer constrains the other — present them together rather than one at a time. This reduces round-trips and keeps the flow moving. Examples:
- Context signals (modality + use case) are independent — ask together
- Voice dimensions (Formality, Warmth, Personality Intensity) are independent — ask together
- Chatting Style dimensions (Emoji, Formatting, Punctuation, Capitalization) are independent — ask together
- Encoding context (tool + topics + actions) are independent — ask together

Do **not** batch across dependency boundaries. Register must be answered before Voice. Voice before Tone. Tone before Delivery. Follow the framework's dependency order for sequential questions.

**Short labels, descriptions underneath.** Question options should be scannable in under 2 seconds. If an option needs explanation, put the label first and the explanation as a secondary description — not a long compound label.

**Multi-select when appropriate.** When the user should be able to pick more than one option — phrase book entries to keep, topics to encode, surfaces to target — allow multiple selections rather than asking the same question repeatedly. If the environment supports multi-select natively, use it. If not, present options as a numbered list in output text and ask the user to type their selections (e.g., "Which ones? Type the numbers: 1, 3, 5"). Either way, the user selects multiple and confirms once.

**Compact output formats.** Use tables and structured lists for dimensions, not prose paragraphs. One line per dimension with value and signal annotation. Phrase book entries grouped by category. Never-say entries as a compact list. Dense, scannable output respects the user's time.

**Progress awareness.** Before presenting the hub menu after an elective, show a one-line status summary of what's been completed and what remains:
> "Clover: ✓ Identity · ✓ Dimensions · ✓ Phrase book (18) · ✓ Never-say (8) · Remaining: tone flex, lexicon, score, encode"

**Summary before transitions.** Before moving into scoring, encoding, or any new phase, show a brief orientation line so the user knows the current state:
> "Scoring Clover — Peer register, Professional, Warm, Encouraging, Concise."
> "Encoding Clover for Agentforce Builder — external customer, chat."

**Confidence callouts.** After presenting a drafted persona, highlight the 1-2 lowest-confidence dimensions so the user knows where to focus refinement:
> "Least certain: Humor (defaulted to Warm — no signal in input) and Emoji (defaulted to Functional). Adjust these first if they matter."

#### Step 4: Present the Persona

Before showing sample dialog, present the drafted persona in a compact, scannable format. This is NOT the full persona document — it's a summary for review. The user needs to see what was generated before seeing it in action.

**Format:**
- **Identity** — traits on one line, dot-separated
- **Dimensions** — compact table: one row per dimension with value and signal marker (★ = strong signal from input, no marker = default/inferred)
- **Phrase Book** — entries grouped by category, showing actual phrases
- **Never-Say** — compact list
- **Tone Boundaries** — compact list
- **Tone Flex** — table with trigger, coloring shift, empathy shift, humor guidance

**Design rationale.** Before the persona summary, introduce it with a brief narrative explaining the key design choices — why these identity traits, why this register, what in the input drove the major decisions. This is a design partner explaining their thinking, not a data dump. Keep it to 2-4 sentences. This rationale is conversational context only — it does not get written to the persona document.

> Example: "I went with Gracious and Composed because luxury hospitality needs poise under pressure. Peer register rather than Subordinate — Coral Cloud's brand is warm and personal, not deferential. Encouraging coloring felt right for a resort that wants guests to feel excited, not just served."

After the persona summary, note the lowest-confidence dimensions (see Confidence callouts in Interaction Design) so the user knows where to focus if they want to refine.

Then proceed directly to sample dialog — no confirmation question needed between persona presentation and sample dialog. The persona provides context for understanding the sample.

#### Step 5: Sample Dialog

Present a few turns of conversation (3-5 exchanges) based on the use case from Step 2.

**Requirements:**
- The dialog demonstrates the persona in action — word choice, tone, brevity, humor, formatting
- Include at least one "interesting" turn: an error, a clarification, or an emotional moment — not just happy path
- None of these agents say "Hello! How can I help you today?" — the sample should make the persona's impact obvious
- For voice/telephony modality, start the dialog with the welcome message including AI disclosure so the user sees it in context

**After presenting the sample dialog,** prompt for feedback. The prompt should encourage free-text adjustments as the primary editing path — "Tell me what to change — 'make it warmer,' 'drop the humor,' 'don't say that' — or pick an option." Structured options should be limited to:
- "Looks good — show me what's next"
- "Try a different scenario"
- (free-text input always available)

When the user types a natural language adjustment ("make it warmer," "it shouldn't say 'that's frustrating'"), apply it using the conversational editing mappings (see Refine section), regenerate sample dialog with the change, and re-present. Stay in this loop until the user says "looks good" or asks for the hub. Don't bounce to the hub after every adjustment.

When the user selects "Looks good — move on," transition to Phase 2 by offering the hub menu.

### Phase 2: Electives

After the sample dialog, show a progress line (see Interaction Design) and offer next steps. The user picks what to do. After completing any elective, show the updated progress line and offer the hub menu again (minus completed items). The user decides when they're done.

**Hub menu options** (grouped for scannability):

- "Refine the persona" — opens a sub-menu: identity, dimensions, phrase book, never-say, tone flex, lexicon, or free-text addition
- "Try a different sample dialog scenario"
- "Score the persona"
- "Download the persona document"
- "Encode for Agentforce deployment"
- "I'm done"

#### Refine

When the user selects "Refine the persona," offer a sub-menu:
- "Identity traits"
- "Dimensions" (show current values for reference)
- "Phrase book"
- "Never-say list"
- "Tone flex rules"
- "Lexicon"
- "Something else" (free-text — see Other below)

Two editing modes, both available at any time. The user can mix them freely.

**Conversational Editing** — The user describes changes in natural language. Map common requests to specific dimension changes:

| User says | Dimension change | Also consider |
|---|---|---|
| "warmer" | Warmth: increase one position | Empathy Level: increase one position |
| "cooler" / "less warm" | Warmth: decrease one position | Empathy Level: decrease one position |
| "more formal" | Formality: increase one position | Register: shift toward Advisor |
| "less formal" / "more casual" | Formality: decrease one position | |
| "shorter" / "more concise" | Brevity: decrease one position (toward Terse) | |
| "longer" / "more detail" | Brevity: increase one position (toward Expansive) | |
| "more personality" | Personality Intensity: increase one position | Humor: consider enabling if None |
| "less personality" / "more neutral" | Personality Intensity: decrease one position | |
| "less robotic" | Warmth: increase + Personality Intensity: increase | |
| "more professional" | Formality: Professional, Humor: None or Dry | Personality Intensity: Moderate |
| "friendlier" | Warmth: increase + Emotional Coloring: Encouraging | Empathy Level: increase |
| "more direct" / "blunter" | Emotional Coloring: toward Blunt, Brevity: toward Terse | Empathy Level: toward Minimal |
| "more encouraging" | Emotional Coloring: Encouraging | Empathy Level: Moderate or Attuned |
| "funnier" | Humor: increase one position | Personality Intensity: increase if Reserved |
| "no humor" | Humor: None | |
| "more emoji" | Emoji: increase one position | |
| "less emoji" | Emoji: decrease one position | |

When a request is ambiguous, apply the primary mapping and narrate the change so the user can correct.

**Deterministic Editing** — Invoked by asking to "show all settings," "show the dimension table," or "let me see the details." Display all dimensions with confidence annotations. The user selects specific dimensions to adjust. Present the full spectrum with the current value highlighted. After adjustment, regenerate sample dialog.

**Diff-Based Regeneration** — After a single-dimension change:
1. Show the change explicitly: "Warmth: Warm → Cool"
2. Hold ALL unchanged dimensions constant
3. Regenerate sample dialog varying only the changed dimension
4. Narrate what shifted in the output so the user connects the dimension change to the behavioral difference

#### Other (free-text additions)

When the user wants to add something that doesn't fit a standard framework concept, accept it. Review the input:
- If it maps naturally to an existing framework element (e.g., a tone boundary, a phrase book entry, a lexicon term), propose incorporating it there and ask for approval.
- If it doesn't fit, insert the user-generated text into the persona document as a custom section and ensure it's included in encoding output.

#### Lexicon

Lexicon is optional. Introduce the concept: domain vocabulary scoped per topic. Gather words that matter — especially words specific to certain topics. Disambiguate from phrase book:
- **Phrase Book** = how the agent sounds in common situations (acknowledgements, redirects, celebrations)
- **Lexicon** = what specific words and terms the agent uses in particular domains (technical terms, brand language, industry jargon)

#### Done

When the user selects "I'm done," offer to download the persona document if it hasn't been saved yet. Show a final summary of what was produced and where files were written. Clean exit.

---

## Scoring

Score the persona document against a 50-point rubric. Scoring is **on-demand** — triggered when the user asks.

**Before scoring,** show a brief orientation summary (see Interaction Design). Then display the scorecard inline. After displaying, offer to save to `_local/generated/[agent-name]-persona-scorecard.md`. Then return to the hub menu.

*For an unbiased score, have a different person run the scoring rubric on the generated persona.*

| Category | /10 | Criteria |
|---|---|---|
| **Identity Coherence** | /10 | • Traits distinct, non-contradictory, behaviorally defined — observable behaviors, not aspirations • Design Inputs present and coherent: audience → register, modality → chatting style, company → frame of reference |
| **Dimension Consistency** | /10 | • Each dimension coherent with Identity, constraints respected • Tone Boundaries consistent with Emotional Coloring/Empathy; Tone Flex within range • Chatting Style adapted for modality (suppressed for telephony) |
| **Behavioral Specificity** | /10 | • Concrete behavioral examples, testable rules • Never-Say ≥5 (chatbot filler + register violations + persona-specific) • Global Lexicon populated • Brand guide: extraction depth — vocabulary, formatting, usage, CTAs captured? |
| **Phrase Book Quality** | /10 | • 2-4 phrases per applicable category • All-agent: Acknowledgement, Affirmation, Apologies (mistakes only), Off-Topic Redirect, Welcome • Conditional: Escalation/Handoff (external), Celebrating Progress (Encouraging), Teaching Moments (Coach), Humor Examples (Humor ≠ None) • Phrases match register and dimensions • Brand guide content captured |
| **Sample Quality** | /10 | • Persona recognizable without seeing dimension table • Happy path + uncertainty + boundary scenarios • Modality-appropriate (telephony: brevity recalibrated, formatting suppressed) • Brand vocabulary appears naturally |

**Scoring rules:**
- Score each category independently. Provide a number and 1-2 sentences of justification.
- Flag inconsistencies between dimensions. Note productive tensions vs. contradictions.
- If any category scores below 7, provide a specific suggestion for improvement.
- Total: 45-50 production-ready, 35-44 strong foundation, 25-34 needs revision, below 25 restart.

---

## Encode Flow

A standalone entry point for encoding an existing persona document into tool-specific output. Accessible when the user provides a completed persona.md, or after the Design flow.

Read `references/persona-encoding-guide.md` for encoding architecture and `assets/persona-encoding-template.md` for the output structure. Voice selection and tuning are outside the primary encode flow — use `references/persona-encoding-guide-voice.md` as a reference only when modality includes telephony or other voice output.

**Before encoding,** show a brief orientation summary (see Interaction Design) confirming the agent name, authoring tool, audience, and modality.

### Encoding Context

Company, audience, and modality are collected during design (Step 2). Encoding inherits them — don't re-ask. Collect only what's needed for encoding:

1. **Agent authoring tool** — "Are you encoding for Agentforce Builder or Agent Script?"
2. **Topics** *(optional)* — "Do you have specific topics defined? Per-topic encoding tailors brevity, tone flex, and vocabulary to each topic." If provided, generate per-topic persona instructions. If the user declines, offer: "No, generate a few examples." In that case, infer 2-3 plausible topics from the persona context and generate per-topic instructions, clearly labeled: "These are examples inferred from the persona context — replace with your actual topics."
3. **Actions** *(optional)* — "Do you have specific actions defined? Per-action encoding generates in-character loading text users see while waiting." If provided, generate persona-consistent loading text for each. If the user declines, offer: "No, generate a few examples." In that case, infer 2-3 plausible actions from the persona context and generate in-character loading text for each, clearly labeled: "These are examples inferred from the persona context — replace with your actual actions."

The user can do just the global encoding and return later with topics and actions.

### Generation

#### If Agent Script

Output ready-to-paste YAML blocks:

**System block:**
1. **`config.agent_name`** — The persona name.
2. **`system.instructions`** — Full persona content as a YAML literal block scalar (`|`): Identity, dimension behavioral rules, phrase book, chatting style rules, tone rules, tone boundaries, never-say list. No character limits.
3. **`system.messages.welcome`** — Generate a static in-persona welcome message. For multimodal agents with a telephony channel, generate two: a text welcome and a shorter telephony welcome (ear-optimized, includes AI disclosure). Default to static; note the option for dynamic as supplemental.
4. **`system.messages.error`** — Generate one (1) static in-persona system error message. No dynamic option available for this field.

**Per-topic overrides** (if topics provided):
5. **`reasoning.instructions` per topic** — Persona calibration: brevity, lexicon, tone flex, phrase book entries, humor guidance, persona reminder.
6. **Topic-level `system:` override** — Only when a topic's tone flex warrants a full system-level override. Rare.

**Per-action loading text** (if actions provided):
7. **`progress_indicator_message`** per action — In-character loading text with `include_in_progress_indicator: True`.

**Deterministic response examples:**
8. Example `| text` pipes for common if/else branches written in the persona's voice.

**Telephony adjustments** (if modality includes telephony):
9. **Instruction adjustments** — note brevity recalibration (one position shorter for telephony), formatting suppression (no emoji, bullets → ordinals), and any pausing guidance for structured data.

#### If Agentforce Builder

**Agent Configuration Fields:**
1. **Name** (80 chars) — Show character count.
2. **Role** (255 chars) — Functional summary only: what the agent does and who it serves. "You are..." Do **not** encode persona style here. Show character count.
3. **Company** (255 chars) — Populate from company context collected in Step 2. Show character count.
4. **Welcome Message** (800 chars, aim for ≤ 255) — Generate a static in-persona welcome message reflecting Identity + Register + Voice + Tone + Brevity. For multimodal agents with a telephony channel, generate two: a text welcome and a shorter telephony welcome (ear-optimized, includes AI disclosure). Show character count.
5. **Error Message** — Generate one (1) static in-persona system error message reflecting Formality + Warmth + Emotional Coloring + Brevity.

**Agentforce Builder Settings:**
6. **Tone dropdown** — Recommend based on Register + Formality. Note it's a coarse approximation.
7. **Conversation Recommendations on Welcome Screen** — On when use cases are defined; Off when open-ended.
8. **Conversation Recommendations in Agent Responses** — On for proactive agents; Off for socratic agents.

**Global Persona Block:**
9. **Global instructions** — Full persona content for a dedicated global instructions topic. Synthesize from all persona sections.

**Per-topic persona instructions** (if topics provided):
10. Tailored instructions per topic with brevity calibration, phrase book entries, lexicon terms, tone flex triggers, humor guidance.

**Loading Text:**
11. **Per-action loading text** — If specific actions were provided, generate persona-consistent loading text for each. If the user chose "generate a few examples," infer 2-3 plausible actions and generate in-character loading text for each, clearly labeled as examples.

**Telephony adjustments** (if modality includes telephony): Same items as Agent Script telephony adjustments above.

#### Output

Present encoding values inline for review. Character-limited fields (Name, Role, Company, Welcome, Error) display inline with character counts. Unbounded fields (Global Instructions, per-topic instructions) are too long to display inline — show a summary with character count and write the full content to file.

Write the encoding output using the `Write` tool. Default path: `_local/generated/[agent-name]-persona-encoding.md`. Then return to the hub menu.

---

## Output

The skill produces up to four Markdown files:

1. **Persona document** (`_local/generated/[agent-name]-persona.md`) — follows the `assets/persona-template.md` structure. The design artifact defining who the agent is, how it sounds, and what it never does.
2. **Sample dialog** (`_local/generated/[agent-name]-sample-dialog.md`) — follows the `assets/sample-dialog-template.md` structure. Validation artifact demonstrating the persona in conversation.
3. **Scorecard** (`_local/generated/[agent-name]-persona-scorecard.md`) — 50-point rubric evaluation. Generated on request.
4. **Encoding output** (`_local/generated/[agent-name]-persona-encoding.md`) — follows the `assets/persona-encoding-template.md` structure. Tool-specific: Agentforce Builder field values and settings, or Agent Script YAML blocks. Generated on request via the Encode flow.
