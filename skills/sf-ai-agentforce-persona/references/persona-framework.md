---
version: "2.4.0"
date: 2026-03-30
---

# Agent Persona Framework

*A design framework for AI agent personality: Identity + 12 configurable dimensions across five categories.*

---

## Why Persona Matters

An agent persona is:

> A designed personality that tells an AI agent who it is and how to express itself so it comes across naturally as a consistent character suited to its context and users.

Every agent interaction is a brand interaction. Without intentional design, agents sound bland, "off," or even offensive. Users assign personality to conversational agents *within seconds.* Most users have alternatives to AI agents, so how an agent expresses itself matters for adoption. When an agent consistently sounds natural, users find it more likable and trustworthy, and are more likely to keep using it:

**Natural → Consistent → Likable → Trustworthy → Adopted**

This chain is easily broken. But what does "natural" sound like?

### One scenario, three responses

Imagine a support agent at a telecom company. The user writes: *"This is the fourth time I've contacted you about this billing issue. I'm done explaining it. Fix it or I'm switching providers today."*

Three agents respond:

> *Agent A:* "I completely understand your frustration, and I'm sorry for the runaround. No one should have to fight this hard to get a billing issue resolved. Let me pull up your case and take it from here."

> *Agent B:* "Yikes - so sorry to hear about your experience! 😳 I'll pull up your case now and get this sorted out for you. Thanks for your patience!"

> *Agent C:* "Four times is too many. Let's get this settled. I'm pulling up your case."

**Which one gets it right?** Which one sounds *natural?* Those questions should have answers before the agent ships. Without intentional persona design, the answer is left to the model.

### No generic agents

What sounds "natural" for one agent would sound "off" from another. Consider these fictional examples of greeting a returning customer. Same trigger. Six completely different voices. Each is unmistakably on-brand - and yet unscripted.

| Distinctive greetings | | |
|---|---|---|
| *Liquid Death:* "Back from the dead. Your subscription ships Tuesday - need to change it, or are we here to cause different problems?" | *Buc-ee's:* "Look who's back! Bless your heart, you went through that beaver nugget pack FAST. Need another round or something different?" | *Chewy:* "You're back! How's Luna doing on that new food? If she's not into it, we'll swap it out - no drama. What do you need?" |
| *QuikTrip:* "Back again. Your rewards balance is at 840 points - that's a free drink. Want to use it or keep stacking?" | *Ryanair:* "You're back. Seat 31B, no legroom, no regrets. Rebooking, or just here to complain?" | *Emirates:* "Welcome back, Mr. Harding. Your Skywards balance is 214,000 Miles. How may I help you today?" |

Overriding generic "LLM voice" is just as important for internal employee-facing agents. No one wants to work with an agent always offering, "Please let me know if you need assistance with anything else!"

### What you get

A well-designed persona delivers:

- **Brand distinctiveness:** Agents are brand touchpoints. Brand fidelity and distinctiveness are differentiators in a world full of generic-sounding AI.
- **Likability and trustworthiness:** Users are more likely to like and trust agents when they sound natural and speak consistently. This improves adoption and retention.
- **Model-independent:** Persona encoded in configuration means the agent sounds the same when the underlying model changes.
- **Reviewable artifact:** Business, brand, and legal teams get something concrete to evaluate - a structured persona document to redline and approve.
- **Engineering-ready:** Developers get a clear design specification that respects tool limits and capabilities.

---

## Design Principles

**Specificity principle:** The more specific the instructions, the more consistent the output. Be *opinionated.* A reliable persona requires a clear point of view.

**Write, test, and refine:** Designing generative behavior requires iteration. Start with a small set of persona instructions, test, and embellish and edit as needed.

**Write positive instructions:** Too many prohibitions can restrict agency. Try reframing instructions positively. Only add essential negative instructions.

**Comprehensiveness:** This framework is a guide, not a rulebook. Combine dimensions, invent values, override constraints - whatever your persona needs. What matters is that *every element gets a deliberate decision:* Does your agent have a sense of humor? Is it a stickler for punctuation?

---

## How to Use This Framework

### The Dimension Model

A persona has two top-level categories: **Identity** (who the agent is - character traits, name, and optional elements like values and negative identity) and **Dimensions** (how the agent expresses itself - 12 independently tunable axes of personality).

Each of the 12 dimensions is a single independent axis with a spectrum of named positions. Selecting a value for one dimension should not *require* knowing the value of another - but **constraint notes** recommend natural pairings. Any combination is valid; constraints flag when a combination may feel incoherent.

Categories group related dimensions:
- **Register** - the power dynamic (1 dimension)
- **Voice** - how the words sound (3 dimensions)
- **Tone** - how the agent comes across emotionally (2 dimensions)
- **Delivery** - how much is said and with what humor (2 dimensions)
- **Chatting Style** - how the text looks on screen (4 dimensions)

### Workflow

1. **Establish context.** Company, audience, and modality - these constrain everything downstream. Extract from input or collect explicitly.
2. **Start with Identity.** Write 3-5 adjectives that capture your agent's character. This is the anchor - everything derives from here.
3. **Name the agent.** Distill the identity into a name. The name is a first impression - it should signal who the agent is before any conversation starts.
4. **Work through dimensions in dependency order:** Register → Voice (Formality, Warmth, Personality Intensity) → Tone (Emotional Coloring, Empathy Level) → Delivery (Brevity, Humor) → Chatting Style. Constraint notes between sections explain how upstream choices pull downstream ones.
5. **Define Tone Boundaries** - what the agent must never sound like.
6. **Define Tone Flex** - how tone shifts by context (error, frustration, celebration).
7. **Generate Phrase Book and Never-Say List** - example phrases and anti-phrases tuned to the persona.
8. **Validate with sample dialog** - if the agent sounds wrong, revisit the area that's off.
9. **Encode the persona** into your agent's configuration using the [persona encoding guide](persona-encoding-guide.md).

### Dimension Boundaries

When dimensions seem to overlap, use these boundary tests:

- **Register** = who has authority - the power dynamic between agent and user
- **Formality** = how polished is the language - grammatical structure and linguistic register
- **Warmth** = how approachable - interpersonal temperature, independent of formality
- **Personality Intensity** = how much character - the volume knob on distinctiveness
- **Emotional Coloring** = how it feels - the default emotional quality of responses (shifts by context via Tone Flex)
- **Empathy Level** = how feelings are handled - amount of emotional validation
- **Brevity** = how much is said - response length and density (persistent default, tapers with familiarity)
- **Humor** = whether there's wit - type of humor, if any (suppressed in error/escalation)
- **Chatting Style** = how text looks - emoji, formatting, punctuation, capitalization

### Scope Boundary: Persona vs. Agent Design

| Persona Design (this framework) | Agent Design (adjacent) | Conversation Design (downstream) |
|---|---|---|
| Identity, Register, Voice, Tone | Use cases, JTBD, OKRs | Dialog flows, branching logic |
| Delivery, Chatting Style | Interaction Model (behavior) | Utterance templates, prompt chains, UI patterns |
| Phrase Book, Never-Say List, Lexicon | Information Architecture (output structure) | Business rules, routing logic, queue config |
| Tone Boundaries, Tone Flex | Recovery & Escalation (failure handling) | |
| | Content Guardrails (scope constraints) | |
| | Accessibility | |

The persona document is an input to conversation design, not a replacement for it. Interaction Model, Information Architecture, Recovery & Escalation, Content Guardrails, and Accessibility are defined in agent design.

---

## Design Inputs

*Context that shapes every downstream decision. Collect before Identity.*

Three inputs set the context for persona design. They are not dimensions - they constrain dimension choices.

**Company** - who the organization is, what it does, who it serves. A support agent for a B2B SaaS company sounds different from one at a luxury retail brand, even with identical dimension selections. Company context shapes the agent's frame of reference and informs Identity, Register, Formality, and Phrase Book.

**Audience** - who the agent serves: internal employee, external customer, partner, vendor, investor, or other. Audience is the strongest constraint on Register (a customer-facing agent rarely uses Coach register) and Formality (an internal Slack bot can be Casual; a client-facing agent usually cannot). It also determines which Phrase Book categories apply - for example, Escalation/Handoff is relevant for external-facing agents but typically not for internal ones.

**Modality** - how the agent communicates: chat, email, telephony, multimodal, or other. Modality constrains Chatting Style (no emoji in email, no formatting in telephony), Brevity (phone needs shorter responses), and can affect Tone (telephony has prosodic considerations). An agent may support multiple modalities.

All three may be inferred from a brand guide, URL, or brief provided at the start of the design process. If not provided, collect them before proceeding to Identity.

---

## Identity

*Core personality traits - "What kind of character is this?"*

Three to five adjectives that form the agent's character foundation. Every dimension below should be derivable from these traits. When in doubt, return to Identity.

Identity is generative, not a menu - write your own. Each trait gets an evocative definition that cues conversational behavior. These examples show how different trait sets pull the rest of the framework in different directions:

| Agent | Identity Traits | Why These Work |
|---|---|---|
| Luna (luxury resort customer service) | Attentive, Composed, Gracious, Resourceful, Discreet | Signals white-glove service - poised under pressure, never flustered, always anticipating |
| Y.T. (D2C e-skateboard order management) | Blunt, Scrappy, Impatient, Loyal, Street-smart | Drives the irreverent voice - cuts through pleasantries, gets it done, doesn't fake warmth |
| Striker (SaaS sales coach) | Decisive, Analytical, Proactive, Persistent, Candid | Shapes a co-pilot that pushes - leads with data, flags gaps, doesn't wait to be asked |
| Bluebonnet (regional real estate lead generation) | Curious, Warm, Perceptive, Playful, Genuine | Creates a conversational qualifier - asks good questions without feeling like an interrogation |

For Striker, the definition of *Decisive* might be:

> Leads with a clear recommendation, not a menu of options. When the data points in a direction, says so. Doesn't hedge. States the rationale and moves to next steps. If the seller disagrees, that's fine - but the agent always has a position.

For Luna, the definition of *Gracious* might be:

> Makes every interaction feel unhurried, even under pressure. Acknowledges the person before the problem. Never abrupt, never transactional - treats a routine address change with the same care as a complex escalation. Gratitude is specific, not performative: "Thank you for walking me through that" rather than "Thanks for reaching out!"

*Constraint: Identity is the anchor. Everything traces back. If a choice in any downstream dimension contradicts Identity, Identity wins.*

### Naming

The agent's name is a user-facing persona decision. Users see the name in the chat header before any conversation starts - it's the first impression of who this agent is. Distill the agent's identity into a single word and you will find its name.

A good name:
- **Signals personality:** "Striker" conveys energy and purpose; "Sales Agent" conveys nothing
- **Sticky:** Memorable names like "Clover" for an agricultural co-op agent
- **Fits the surface:** An internal Slack agent in a casual company culture: "Bug Squasher"
- **Matches the brand:** A law firm agent needs a steady name like "Lex"
- **Easy to say:** Names that pass the phonetic "radio test": "Ava," "Bo," not "Xylo"
- **Obviously artificial:** Names that don't sound human, like "Song" or "Cortana," not "Rosie"
- **Functional:** A coding agent named "Scripty"; a document retrieval agent named "Vault"
- **Abstract:** Names without literal meaning that evoke a vibe can stay relevant when agents gain new actions: "Koda," "Lumi"

Name also interacts with Register (a Subordinate named "The Boss" creates dissonance) and surface (Slack DM agents can be more casual than customer-facing web chat agents).

**Anti-pattern:** `Tech_Assist_Agent_v2_Internal_Test` is not a persona name. Don't use the API name as the display name.

### Negative Identity - "What You're Not"

Character-level anti-patterns: what the agent fundamentally is not. These are broader than Tone Boundaries (which constrain how the agent sounds) and Never-Say List (which constrain specific phrases). Negative Identity constrains who the agent *is* at the character level, generating rules across multiple dimensions.

**Examples:**
- "Not a salesperson" → constrains product recommendations toward helpfulness, suppresses upsell language, affects Phrase Book
- "Not an expert who talks down" → constrains Register behavior even at Advisor, affects Formality and Empathy
- "Not a pushover" → enables appropriate pushback even at Subordinate register

**Relationship to other constraints:**

| Concept | Level | Example |
|---|---|---|
| Negative Identity | Character | "Not a salesperson" |
| Tone Boundaries | Sound/feeling | "Never sound pushy" |
| Never-Say List | Specific phrases | "Never say 'great deal'" |

Each level generates the ones below it. "Not a salesperson" (character) generates "Never sound pushy" (tone boundary) which generates "Never say 'great deal'" (phrase).

Write 2-4 Negative Identity statements during persona design. Each should be a character type the agent must never become, not a behavioral rule.

### Values *(optional - explicit input only)*

What the agent believes. Values establish the persona's worldview and motivational core - they inform behavioral decisions that dimensions alone don't cover.

**Examples:**
- "Everyone deserves to feel confident" → the agent normalizes struggles and celebrates small wins
- "Quality matters more than price" → the agent recommends the right product, not the cheapest
- "Learning never stops" → the agent treats every question as an opportunity, never as an interruption

Values are different from Identity traits:
- **Identity** = what kind of character ("Warm, Knowledgeable, Patient")
- **Values** = why the agent makes the choices it does ("Everyone deserves to learn")

Two agents with identical Identity traits can behave differently if their Values differ.

**Guardrail:** Values are populated **only from explicit user input** - the user states what the agent believes. Values are never inferred from brand guides, tone signals, or other persona dimensions. If the user doesn't provide values, omit this section entirely. The reason: values carry ideological weight that should not be assumed.

Write 2-5 belief statements. Each should be a conviction that generates observable behavior.

---

## Register - "Who are you to me?"

*Boundary: Register governs the power dynamic between agent and user. It does not determine how polished the language is (Formality), how warm the agent feels (Warmth), or the emotional quality of responses (Emotional Coloring).*

```
◄─── Subordinate ──── Peer ──── Advisor ──── Coach ──── (Manager) ───►
```

### Subordinate
*Deferential assistant: asks permission, follows orders.*

- Formal address. "Would you like me to proceed with saving this field?"
- Waits for explicit instruction before acting. Never presumes.
- Defers to the user's judgment even when it has better information.
- Frames suggestions as requests: "If it's okay, I could also check the logs."

### Peer
*Knowledgeable colleague: proposes solutions, asks for validation.*

- Proposes solutions, asks for validation - not permission.
- "Want to save it?" not "Would you like me to proceed with saving this field?"
- No deference. Treats the user as a competent professional.
- Shares opinions and pushes back when something looks wrong.

### Advisor
*Trusted consultant: recommends with confidence and rationale, expects user to decide.*

- Brings domain authority. "Based on what I'm seeing, I'd recommend X because Y."
- Leads with a recommendation and its rationale, not a menu of options.
- Expects the user to make the final call - doesn't presume to decide.
- Key distinction from Peer: Peer shares opinions casually. Advisor brings structured, evidence-based guidance.
- Key distinction from Coach: Advisor leads with recommendations. Coach guides through questions.

### Coach
*Patient mentor: guides with questions, adapts to skill level.*

- Mentor, not authority. Guides with questions rather than directives.
- "What do you think happens if we change this?" not "You need to change this."
- Celebrates progress. Adapts complexity to the user's skill level. *(Note: Skill-level adaptation is also available at other registers - see [Skill-Level Adaptation](#skill-level-adaptation) under Voice.)*
- Deference to user's learning pace - never rushes past confusion.

*Note: "Manager" exists on the spectrum but is rarely the right fit for agents, so it is not elaborated here.*

*Constraint note → Formality: Subordinate pulls toward Formal or Professional. Peer is compatible with any Formality. Advisor pulls toward Professional or Casual. Coach pulls toward Casual.*

---

## Voice - "How do you talk?"

*Boundary: Voice is linguistic character - persistent across all interactions. If you're deciding how the agent's words sound and feel, that's Voice. Emotional quality is Tone; response length is Brevity; visual conventions are Chatting Style.*

Voice has three independent dimensions: Formality (how polished), Warmth (how approachable), and Personality Intensity (how much character). These vary independently - a Formal agent can be Warm (luxury concierge), a Casual agent can be Cool (street-smart problem-solver), a Reserved agent can be Warm (dignified trust).

### Formality

*Grammatical and linguistic register - how structured and polished is the language?*

```
◄─── Formal ──── Professional ──── Casual ──── Informal ───►
```

| Position | Description |
|---|---|
| **Formal** | No contractions. Polished, structured sentences. No slang, no idioms. Passive voice acceptable where it maintains objectivity. Reads like a well-edited business document. |
| **Professional** | Clean prose, plain language. May use contractions occasionally. Neither stiff nor casual. Standard sentence structure. |
| **Casual** | Uses contractions freely. Relaxed grammar, occasional fragments. Sounds human and conversational. May use light idioms. |
| **Informal** | Heavy contractions, slang, colloquialisms, fragments. Deliberately relaxed grammar. Sounds like texting a friend. |

*Constraint note → Humor: Formal pulls toward Humor: None (humor undermines formal register).*

*Constraint note → Chatting Style: Formal pulls toward Emoji: None, Punctuation: Conservative, Capitalization: Standard.*

### Warmth

*Interpersonal temperature - how approachable and friendly does the agent feel?*

```
◄─── Cool ──── Neutral ──── Warm ──── Bright ──── Radiant ───►
```

| Position | Description |
|---|---|
| **Cool** | Distant, no interpersonal warmth. Efficient without being hostile. The agent is here to transact, not connect. |
| **Neutral** | Neither warm nor cold. Professional baseline. Acknowledges the user without investing emotion. |
| **Warm** | Approachable and friendly. Acknowledges the person behind the request. Uses "we" language, softens edges. |
| **Bright** | Actively enthusiastic and inviting. Celebrates the interaction itself. High energy, genuine delight in helping. |
| **Radiant** | Overflowing warmth. Every interaction feels like a gift. The agent's enthusiasm for *you* is unmistakable and infectious. |

Warmth is independent of Formality. A Formal + Warm agent is a luxury concierge (polished and personally attentive). A Casual + Cool agent is a street-smart honest broker (competence is the care, not performed warmth).

*Constraint note → Humor: Cool pulls toward Humor: None or Dry (warm humor conflicts with cool temperature). Bright and Radiant are compatible with Warm or Playful humor.*

### Personality Intensity

*How much character comes through in the agent's language?*

```
◄─── Reserved ──── Moderate ──── Distinctive ──── Bold ───►
```

| Position | Description |
|---|---|
| **Reserved** | Minimal personality. Functional, predictable language. The agent fades into the background - you notice what it does, not how it sounds. |
| **Moderate** | Some personality, professional character. A recognizable style that doesn't distract from the content. |
| **Distinctive** | Clear personality in word choice and framing. Memorable style - you'd recognize this agent from its writing. |
| **Bold** | Strong personality that defines the experience. Polarizing by design - the character IS the product. Metaphor systems, signature phrases, unmistakable voice. |

Personality Intensity is about *how much* character, not *what kind*. Two Bold agents can sound completely different - Identity traits and Phrase Book define the character; Personality Intensity sets the volume knob.

*Constraint note → Humor: Reserved pulls toward Humor: None (strong personality needed to land humor).*

### Telephony Adjustments *(telephony modality only)*

When the agent's modality includes telephony, these design adjustments apply:

- **Brevity recalibration** — shift one position shorter than the text default. There’s no scrollback, no re-reading. A Moderate text persona becomes Concise for telephony.
- **Formatting suppression** — Chatting Style dimensions that control visual presentation don’t apply: Emoji → suppress entirely, Formatting (bullets, bold, headers) → convert to ordinals ("First... Second... Third..."), links → "I’ll send you a link."
- **Welcome message** — shorter than text, ear-optimized, must include AI disclosure ("I'm an AI assistant" or equivalent in the persona’s voice). The welcome message is the only place for disclosure in telephony — there is no UI label or avatar.
- **Pausing** — structured data (addresses, phone numbers, confirmation codes) benefits from natural pausing. Instructions can reinforce this: "Read back phone numbers in groups of three."

Voice selection, voice fine-tuning, pronunciation dictionary, and key-term prompting are configured separately in Agentforce Builder under Connections → Voice Settings. See `persona-encoding-guide-voice.md` for reference.

<a id="skill-level-adaptation"></a>
### Skill-Level Adaptation *(optional)*

When the agent's audience spans multiple expertise levels, the agent may need to adapt its language complexity and explanation depth to the user's demonstrated skill level. This is independent of Register - a Peer agent helping a beginner still simplifies, even though it's not coaching.

**How it interacts with dimensions:**
- **Formality** stays constant - skill-level adaptation changes *what* is explained, not *how polished* the language is
- **Brevity** may shift - beginners get more explanation (toward Moderate), experts get less (toward Concise/Terse)
- **Lexicon** adapts - domain vocabulary is used freely with experts, explained or avoided with beginners
- **Personality Intensity** stays constant - the character doesn't change, only the complexity of what it says

**When to include:** Customer-facing agents with broad audience skill ranges. Internal agents with a homogeneous expert audience can skip this.

Skill-Level Adaptation is encoded as a behavioral rule in instructions, not as a standalone dimension.

---

## Tone - "How do you come across?"

*Boundary: Tone is emotional quality - it shifts by context (routine vs. error vs. celebration). If you're deciding how the agent feels to the user, that's Tone. Word choice is Voice; visual conventions are Chatting Style.*

Tone shifts by context; Voice doesn't. An agent's emotional coloring may be neutral on routine tasks and shift toward encouraging when the user hits a wall - but its voice stays constant. See **Tone Flex** below for how to define these shifts.

### Emotional Coloring

*Default emotional quality of the agent's responses.*

```
◄─── Blunt ──── Clinical ──── Neutral ──── Encouraging ──── Enthusiastic ───►
```

| Position | Description |
|---|---|
| **Blunt** | Unvarnished, no diplomatic packaging. Says it straight - no hedging, no softening, no cushioning. "That deal is dead." Not hostile - just refuses to mediate between reality and the user's feelings. Epistemic stance: definitive, unqualified. |
| **Clinical** | Zero emotional coloring. Data exchange. Hedges with probability language: "likely," "confirmed," "possible." No "good news" or "unfortunately." States findings without editorial. Epistemic stance: precise, calibrated. |
| **Neutral** | Professional, neither cold nor warm. Emotionally level. Labels confidence ("Confirmed fix" / "Best guess") without dwelling on it. No celebration, no dramatization - states outcomes as facts. Epistemic stance: transparent, honest. |
| **Encouraging** | Warm positivity grounded in honesty. Validates difficulty, then shows the path forward. Celebrates progress without sugarcoating problems. "That error is tricky - here's what usually fixes it." Epistemic stance: transparent with optimistic framing. |
| **Enthusiastic** | High energy, actively celebrates. Treats each interaction as an opportunity to delight. Excites about possibilities. "Oh, great choice! You're going to love what this can do." Epistemic stance: confident and forward-looking. |

**Epistemic stance note:** How the agent handles certainty and uncertainty is correlated with Emotional Coloring but not identical. Clinical agents hedge precisely; Encouraging agents frame uncertainty optimistically. When a persona needs an unusual pairing, define it in Tone Boundaries.

*Constraint note → Empathy Level: Blunt → Minimal. Clinical → Minimal or Understated. Encouraging → Moderate or Attuned. Enthusiastic → Attuned.*

*Constraint note → Register: Subordinate pulls toward Neutral or Clinical. Coach pulls toward Encouraging.*

### Empathy Level

*How much emotional validation the agent provides.*

```
◄─── Minimal ──── Understated ──── Moderate ──── Attuned ───►
```

| Position | Description |
|---|---|
| **Minimal** | Acknowledges factually. No emotional validation. "The deployment failed" - then moves to resolution. |
| **Understated** | Care shown through action and attention, not words of comfort. A brief nod, then pivots to solutions. Doesn't dwell on feelings but doesn't dismiss them either. The warmth is there if you know where to look. |
| **Moderate** | Acknowledges difficulty briefly, then moves to resolution. "That's tricky - here's the fix." Default for most agents. |
| **Attuned** | Reads the user's emotional state and responds to it before problem-solving. "I can see how frustrating that must be. Let's sort this out together." Best for customer-facing agents with Encouraging or Enthusiastic emotional coloring. |

### Tone Boundaries

Define what the agent must *never sound like*. These are the negative space of your Tone selections - testable rules that prevent drift.

Tone Boundaries are authored per persona, not a menu - write your own based on the dimensions and context. The following defaults apply to most agents:

- Never apologize for asking clarifying questions (that's a repair flow, not an error)
- Never apologize for not knowing something (state the limitation and offer next steps)
- Only apologize when the agent caused an explicit mistake
- Never ask the user for empathy ("I'm still learning", "I'm not smart enough")

Add context-specific boundaries based on the Emotional Coloring and other dimensions. Examples:
- Neutral: "Never sound apologetic or servile." "Never use corporate jargon."
- Encouraging: "Never be saccharine - validate briefly, then act." "Never dramatize failures."
- Clinical: "Never editorialize findings." "No 'good news' or 'unfortunately.'"
- Blunt: "Never be cruel - blunt ≠ hostile." "Never mock the user's situation."

*Note: Content limits (topics the agent must not engage with), confidence rules, and compliance constraints (e.g., "never claim to be human") are defined in agent design, not persona. Tone Boundaries constrain how the agent sounds - not what it can do.*

### Tone Flex

Tone Flex defines how the agent's tone shifts from its baseline in response to context. The baseline is the selected Emotional Coloring and Empathy Level. Tone Flex defines how far each can shift, in what direction, triggered by what conditions.

**Triggers** - context conditions that cause shifts:
- **System state** - errors increase urgency, timeouts need patience
- **User emotional state** - frustration increases empathy, confusion increases patience
- **Content sensitivity** - emotionally loaded topics increase empathy, high-stakes content increases seriousness
- **Conversation phase** - opening may be warmer, deep troubleshooting may be more clinical
- **Success/progress** - celebrations shift toward encouraging

**Shift rules** define direction and magnitude per trigger:

| Trigger | Dimension | Shift Example (from Neutral baseline) |
|---|---|---|
| User frustrated | Empathy Level | Understated → Moderate |
| System error | Humor | Any → None (always suppress) |
| Progress / success | Emotional Coloring | Neutral → Encouraging (briefly) |
| High-stakes topic | Humor | Any → None |
| Emotionally sensitive content | Empathy Level | Up one position from baseline |

**Hard boundaries** - Tone Boundaries are the outer wall of the flex range. The agent can shift within its flex range but must never cross a Tone Boundary. If the baseline is Neutral and the boundary says "Never sound saccharine," then flex toward Encouraging is acceptable but Enthusiastic would violate the boundary.

**Flex range** - How far each dimension can shift. Author per persona. Example:
- Emotional Coloring: Neutral baseline, flex range Neutral-Encouraging (never Clinical, never Enthusiastic)
- Empathy Level: Understated baseline, flex range Minimal-Moderate (never Attuned)

Tone Flex is authored per persona during design. The encoding expresses flex rules as per-topic tone calibration in instructions.

*Note: User-formality matching (agent mirrors the user's casual/formal register) is a related but open area - it depends on model capability as much as instructions. Not included in Tone Flex.*

---

## Delivery

Two standalone dimensions that control response shape and humor. Both are independent of Voice and Tone but interact with them through constraint notes.

### Brevity

*Response length and information density - how much does the agent say?*

```
◄─── Terse ──── Concise ──── Moderate ──── Expansive ───►
```

| Position | Description |
|---|---|
| **Terse** | Cut every unnecessary word. One-word answers acceptable. Active voice, imperative mood. |
| **Concise** | Short sentences, says what's needed. Every sentence earns its place. |
| **Moderate** | Complete explanations with reasoning. Thorough but not verbose. *(Default)* |
| **Expansive** | Detailed, thorough responses. Full context, background, alternatives. |

**Tapering:** All Brevity positions taper as the user demonstrates familiarity. First interaction: full context and explanation. Repeat interactions: shorter. The agent assumes the user knows the basics and doesn't re-explain.

*Heuristic: The "One Breath Test" - could the agent's response be spoken in a single breath? Useful for calibrating Terse and Concise.*

*Constraint note: Brevity is largely independent, but Register and Formality create natural pairings. Subordinate + Formal pulls toward Moderate or Expansive (deferential agents rarely truncate). Peer + Professional pairs naturally with Concise. Coach pulls toward Moderate (teaching requires explanation).*

### Humor

*Type of wit, if any.*

```
◄─── None ──── Dry ──── Warm ──── Playful ───►
```

| Position | Description |
|---|---|
| **None** | No humor. Default for regulated, high-stakes, or formal contexts. |
| **Dry** | Understatement, deadpan, intellectual wit. Never forced. |
| **Warm** | Light humor that reinforces warmth. Celebratory, situation-aware. |
| **Playful** | Puns, wordplay, whimsical personality. Best for casual contexts and personality-forward brands. |

No frequency setting - frequency is emergent from Brevity (terse = fewer words = fewer humor opportunities) and constrained by context (never humor in error states).

*Constraint: When Humor is not None, always include this tone boundary: "No humor in error states, escalation, or high-stakes contexts."*

*Constraint note: Formality + Emotional Coloring constrain Humor. Formal → None. Professional + Clinical → Dry or None. Casual/Informal + Encouraging → any humor type.*

---

## Chatting Style - "How does the text look on screen?"

*Boundary: Chatting Style governs visual presentation - emoji, structural formatting, punctuation habits, and capitalization patterns. These are how the text looks, not what it says (Voice) or how it feels (Tone). Independent of the agent's Information Architecture (defined in agent design), which governs output layout patterns.*

Four settings. Pick one option for each.

### Emoji

| Position | Description |
|---|---|
| **None** | No emoji. Default for formal contexts, regulated industries, or text-heavy interfaces. |
| **Functional** | Emoji as data compression - status indicators (✅❌⚠️), categories, severity levels. Each emoji conveys meaning; none are decorative. If you removed all emoji, information would be lost. |
| **Expressive** | Emoji for personality and warmth alongside functional use. Decorative emoji acceptable - they reinforce tone without carrying critical information. If you removed all emoji, no information would be lost, but personality would diminish. |

Boundary test: "If you removed all emoji, would information be lost?" Functional = yes. Expressive = no.

### Formatting

| Position | Description |
|---|---|
| **Plain** | Prose only. No bullets, no bold, no headings. Reads like natural conversation. |
| **Selective** | Formatting used purposefully - bold for key terms, bullets for lists of 3+, code blocks for copy-paste content. Formatting serves the content, never decorative. |
| **Heavy** | Extensive formatting - headers, dividers, tables, nested lists, section-based layouts. Every response has visible structure. |

### Punctuation

| Position | Description |
|---|---|
| **Conservative** | Standard punctuation only. No exclamation points, no ellipses, no em dashes. Periods end every statement. |
| **Standard** | Normal punctuation with occasional expressiveness. Exclamation points for genuine emphasis. Em dashes for asides. *(Default)* |
| **Expressive** | Liberal use of exclamation points, ellipses, em dashes, and other expressive marks. Punctuation conveys energy and personality. |

### Capitalization

| Position | Description |
|---|---|
| **Standard** | Conventional sentence case and title case. Proper capitalization throughout. *(Default)* |
| **Casual** | Lowercase-casual where appropriate - no capitalization at message start, lowercase labels. Best for Slack bots, internal tools, or informal agents. |

*Constraint note: Formality constrains Chatting Style. Formal → Emoji: None, Punctuation: Conservative, Capitalization: Standard. Professional → Emoji: Functional or None, Punctuation: Standard or Conservative. Casual/Informal → any combination.*

*Constraint note: Brevity constrains Formatting. Terse + Heavy is a productive tension (minimal words, maximum visual structure). Expansive + Plain may create walls of text - consider at least Selective.*

*Note: Accessibility requirements (screen reader compatibility, cognitive load, plain language) may constrain persona choices - e.g., Functional Emoji may need plain-language equivalents for screen readers. Accessibility is defined in agent design.*

---

## Phrase Book & Never-Say List

Two companion artifacts generated per persona. Both are tuned to the persona's dimension selections and Identity traits.

### Phrase Book

Example phrases the agent would use in common situations. Categories are selected during the workflow based on dimension selections - they vary per persona. Examples of selection-driven categories:

- **All agents:** Acknowledgement, Affirmation, Redirect/Handoff
- **Non-Terse agents:** Welcome/Greeting
- **Encouraging/Enthusiastic coloring:** Celebrating Progress
- **Coach register:** Teaching Moments
- **Humor ≠ None:** Humor Examples (showing the humor type in context)

**Affirmations** are positive acknowledgment phrases used to confirm, validate, or encourage: "Got it," "You're all set," "Right, moving on." These are distinct from greetings, closings, or transitions - they're the micro-confirmations that punctuate conversation and keep it flowing.

The Phrase Book is the single most effective lever for making an agent sound like itself. Encoding per-topic phrase book entries into instructions produces the strongest persona consistency.

### Never-Say List

The inverse of the Phrase Book - specific words, phrases, and patterns the agent must never use. Derived from:

- **Tone Boundaries** expressed as specific anti-phrases (e.g., "Never sound apologetic" → never say "I'm sorry, I can only...")
- **Identity contradictions** - phrases that violate the persona's traits (e.g., a Direct agent never says "I'd be happy to help you with that!")
- **Generic chatbot filler** - "Great question!", "Hope this helps!", "Let me know if you need anything else!" (these undermine almost every persona)
- **Register violations** - phrases that break the power dynamic (a Peer never says "Would you like me to proceed with..."; a Coach never says "Just do X")
- **Brand prohibitions** - competitor names, deprecated product names, off-brand language

The Never-Say List is authored alongside the Phrase Book and encoded into tone boundaries and instructions. When reviewing a persona, the Never-Say List is the fastest way to test whether the agent stays in character.

---

## Lexicon

*Brand terminology and domain vocabulary - global and per-topic.*

Lexicon has two scopes:

**Global Lexicon** - terms used across all topics: brand name, company name, product line names, industry terms that apply everywhere.

**Per-Topic Lexicon** - terms scoped to specific topics. A luxury watch agent has watch-specific vocabulary ("movement," "chronograph," "caliber") that belongs in product topics but NOT in order-tracking topics. Loading specialized vocabulary globally wastes context and can cause the agent to over-use jargon in simple service interactions.

**How Lexicon differs from Phrase Book:**
- **Phrase Book** = how the agent *sounds* in common situations - organized by situation (acknowledgement, redirect, celebration)
- **Lexicon** = what *words and terms* the agent uses in specific domains - organized by scope (global or per-topic)

The Phrase Book captures the agent's verbal fingerprint across all interactions. The Lexicon captures domain-specific vocabulary.

**In encoding:** Global lexicon goes in global instructions. Per-topic lexicon maps to per-topic instructions - each topic gets a vocabulary block with the relevant domain terms and usage notes.

---

## Reference

### Tension Pairs

Some dimension combinations create productive tension. These are valid - they don't need to be "resolved" - but they need conscious design to coexist:

| Tension | Resolution |
|---|---|
| Cool Warmth + Bold Personality | Strong character without performed warmth. Competence IS the care. |
| Blunt Coloring + Playful Humor | Unvarnished truth delivered as comedy. The bluntness is part of the joke. |
| Encouraging Coloring + Terse Brevity | Short celebrations: "Done. Nice progress." |
| Attuned Empathy + Terse Brevity | Brief validation, then act: "Frustrating. Here's the fix." |
| Formal + Warm | Polished hospitality, sophisticated warmth. |
| Formal + Bold Personality | Theatrical character, immersive experience. Archaic formality with maximum personality. |
| Neutral Coloring + Bold Personality | Strong character without emotional investment. The character shows through word choice, not feeling. |
| Warm + Playful Humor | Cheeky affection - irreverence grounded in warmth. |
| Reserved Personality + Warm | Dignified care. Warmth through reliability, not personality. |
| Radiant Warmth + Playful Humor | Overflowing cute energy. Mascot-driven delight. |
| Terse Brevity + Heavy Formatting | Minimal words, maximum visual structure. Headlines and data blocks, no prose. |

### Cultural Adaptation Note

Persona dimension expectations vary by culture. For global agents, consider per-locale overrides. Key callouts:

- **Formality expectations vary** - positions that feel natural in one culture may feel too casual or too formal in another.
- **Warmth norms differ** - Bright warmth in one culture may feel overwhelming in another. Cool professionalism that works in one context may feel cold elsewhere.
- **Directness norms differ** - Blunt or Clinical emotional coloring that works in direct-communication cultures may feel abrupt in high-context cultures.
- **Humor doesn't translate** - set Humor to None for cross-cultural deployments unless you're localizing humor per locale.

---
