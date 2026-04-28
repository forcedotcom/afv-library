---
version: "1.0.0"
date: 2026-03-25
---

# Voice Encoding Guide

How to encode a persona for Agentforce Voice. This guide covers voice selection, fine-tuning, pronunciation, and voice-specific instruction adjustments.

> **Reference only:** Voice selection and tuning sit outside the primary persona design and encode flow. Use this guide only when modality includes telephony, click-to-talk, or other voice output.

**Prerequisite:** A completed persona document and familiarity with the [Persona Encoding Guide](persona-encoding-guide.md). Voice encoding extends the standard encoding — it does not replace it. Global instructions, topic calibration, and static messages still apply. This guide covers what's different for voice.

---

## When This Guide Applies

When the agent's modality includes telephony, click-to-talk, or any voice/audio output. If the agent is text-only (chat, email), this guide does not apply.

Voice encoding happens in **Agentforce Builder → Connections → Voice Settings**, not in the main agent configuration. It is a separate configuration surface with its own settings.

---

## Voice Selection

Voice selection is the aural first impression — the equivalent of the agent's name in text. The agent's voice is selected from a library of pre-built voices in Agentforce Builder.

Each voice is a bundle of fixed characteristics:

| Property | Description | Example |
|---|---|---|
| **Name** | Display name | "Kai" |
| **Gender** | Male / Female | Female |
| **Age** | Young adult / Middle-aged / Older | Middle-aged |
| **Primary Language** | Language the voice is optimized for | English (US) |
| **Accent** | Regional accent | Southern American |
| **Style** | Free-text style label | "Warm" |
| **Description** | Character description | "A gentle Southern voice with a warm but measured tone." |

These properties are read-only — they describe the selected voice but are not independently configurable. You choose a voice as a package.

### Matching persona to voice

Select voices by matching persona dimensions to voice properties:

| Persona Signal | Voice Property | Match Logic |
|---|---|---|
| Primary language | Language | Start with voices verified for the agent's language. Others are available but not optimized. |
| Gender (from persona context) | Gender | Infer from persona name, pronouns, description. Only ask if ambiguous. |
| Identity adjectives | Description | Keyword overlap — warm, professional, friendly, calm, energetic |
| Register | Style, Description | Peer → casual, natural. Advisor → professional, authoritative. |
| Formality | Style, Description | Formal → polished, clear. Casual → relaxed, natural. |
| Warmth | Description | Warm → warm, friendly, gentle. Cool → neutral, grounded, measured. |
| Personality Intensity | Description, Stability default | Bold → energetic, expressive. Reserved → calm, steady. |
| Audience context | Age | Match voice age to audience expectations. |
| Regional context | Accent | Match to brand or audience region. |

Recommend **at least 3 voices by name** with reasoning and per-voice starting points for Speed, Stability, and Similarity. The default voice library is available in most orgs — use this guide's matching criteria to select from it. Also share the **voice selection criteria** (language, gender, qualities) so the designer can evaluate other voices available in their org.

Always verify selections in the target org — the library may vary by edition or release.

---

## Voice Fine-Tuning

Three sliders in **Connections → Voice Settings → Advanced → Voice Tuning**. These are starting points for experimentation — adjust based on how the voice sounds in preview, not just the numbers.

| Parameter | Range | Labels | What It Controls |
|---|---|---|---|
| **Speed** | 0.7–1.2 | Slower ↔ Faster | Speaking rate |
| **Stability** | 0–1 | Variable ↔ Monotone | Emotional range vs. consistency |
| **Similarity** | 0–1 | Low ↔ High | Adherence to base voice model |

### Persona interaction — starting points

These are starting points, not prescriptions. Voice tuning is subjective — experiment with different values and listen to the results.

**Stability** is the primary persona lever. It controls emotional expressiveness — the aural equivalent of Emotional Coloring and Personality Intensity.

| Persona Profile | Stability Starting Point | Rationale |
|---|---|---|
| Bold + Enthusiastic/Encouraging | Lower (0.55–0.70) | More expressive, varied delivery |
| Moderate + Neutral | Default range (0.75–0.85) | Balanced consistency and natural variation |
| Reserved + Clinical/Neutral | Higher (0.85–0.95) | More consistent, measured delivery |

**Speed** interacts with Brevity. A Terse persona that speaks slowly creates a mismatch. A Moderate persona that speaks too fast sounds rushed.

| Persona Profile | Speed Starting Point | Rationale |
|---|---|---|
| Terse + Direct | Slightly faster (1.0–1.1) | Matches concise delivery |
| Moderate + Professional | Default range (0.90–1.0) | Natural conversational pace |
| Expansive + Warm | Slightly slower (0.80–0.93) | Unhurried, approachable |

**Similarity** is a consistency control. Keep it at or above 0.75 unless there's a specific reason to deviate. Lower values introduce more variation from the base voice.

### Tuning order

1. Select the voice first
2. Adjust Stability to match Emotional Coloring + Personality Intensity
3. Adjust Speed to match Brevity
4. Leave Similarity at default unless the voice sounds off

---

## Pronunciation Dictionary *(optional)*

Configured in **Advanced** voice settings. Defines phonetic rendering for specific words — brand names, product names, technical terms, acronyms.

| Field | Description |
|---|---|
| **Word** | The term to define pronunciation for |
| **Pronunciation** | Phonetic representation |
| **Format** | IPA (phonetic symbols) or CMU/ARPAbet (ASCII-friendly) |

The Pronunciation Dictionary is the voice counterpart to the Lexicon in text encoding. When the persona's global or per-topic Lexicon defines domain vocabulary, the Pronunciation Dictionary ensures those terms are spoken correctly.

**When to use:** Brand names with non-obvious pronunciation, product names, acronyms that should be spelled out vs. spoken as words, foreign-origin terms, industry jargon. Skip this if all terms have standard English pronunciations.

**IPA vs. CMU:** Use IPA for precision. Use CMU (ARPAbet) if the team is more comfortable with ASCII notation. Either format works.

---

## Key-Term Prompting

Configured in **Advanced** voice settings. Biases the speech-to-text engine toward correct transcription of important terms.

This is the *input* counterpart to the Pronunciation Dictionary. The Pronunciation Dictionary ensures the agent *speaks* terms correctly. Key-Term Prompting ensures the agent *hears* terms correctly.

Populate from the same global Lexicon source: brand name, product names, domain jargon, acronyms. No phonetics needed — plain text.

---

## Voice-Specific Instruction Adjustments

When encoding persona instructions for a voice agent, adjust from the text defaults:

**Brevity recalibration.** Voice benefits from shorter responses — there's no scrollback, no re-reading. Shift Brevity one position shorter than the text default. A Moderate text persona becomes Concise for voice.

**Formatting suppression.** Chatting Style dimensions that control visual presentation don't apply to voice:
- Emoji → suppress entirely
- Formatting (bullets, bold, headers) → convert to natural speech patterns. Bullets become ordinals ("First... Second... Third..."). Bold becomes vocal emphasis (handled by the TTS engine).
- Links → "I'll send you a link" or "You can find that at..."

**Pausing.** Structured data (addresses, phone numbers, confirmation codes) benefits from natural pausing. The platform handles some of this automatically (spoken delivery optimization), but instructions can reinforce it: "Read back phone numbers in groups of three."

---

## Voice Welcome Message

The voice welcome message must be:
- **Shorter than text** — spoken greetings feel long. Aim for one sentence.
- **AI disclosure included** — in voice channels, there is no UI label or avatar to signal the agent is AI. The welcome message is the only place for disclosure. This is a regulatory and trust requirement.
- **In the persona's voice** — the disclosure should match the agent's Formality, Warmth, and Register. A confident introduction, not a legal disclaimer.

Examples by persona style:

| Persona Profile | Voice Welcome |
|---|---|
| Casual + Warm + Peer | "Hey, this is Kai — I'm an AI agent with Coral Cloud. What can I help with?" |
| Professional + Neutral + Advisor | "Thank you for calling. You're speaking with a virtual assistant. How can I help you today?" |
| Formal + Cool + Subordinate | "Good afternoon. This is an automated service agent. Please describe how I may assist you." |

The text welcome message and voice welcome message may differ. Text can be longer and include formatting. Voice must be ear-optimized and include AI disclosure.

---

## Multi-Channel Persona Consistency

When the same persona operates across text and voice, most of the persona stays the same. What adapts:

| Persona Element | Text | Voice |
|---|---|---|
| Identity | Same | Same |
| Register | Same | Same |
| Formality | Same | Same |
| Warmth | Same | Same |
| Emotional Coloring | Same | Same — Stability reinforces it |
| Empathy Level | Same | Same |
| Brevity | As designed | One position shorter |
| Humor | Same type | Same — but timing differs in speech |
| Emoji | As designed | Suppressed |
| Formatting | As designed | Suppressed — ordinals replace bullets |
| Punctuation | As designed | N/A — TTS handles prosody |
| Capitalization | As designed | N/A |
| Phrase Book | Same phrases | Same — phrasing works in both |
| Never-Say List | Same | Same |
| Tone Flex | Same triggers and shifts | Same |
| Lexicon | Same terms | Same — plus Pronunciation Dictionary for voice |
| Welcome Message | May differ | Shorter, includes AI disclosure |

---

## Platform Voice Behaviors (not persona-configurable)

These are built into the voice pipeline. Persona instructions should account for the conversational rhythm they create, but they are not directly configurable:

- **Semantic endpointing** — detects utterance completion by meaning, not silence duration
- **Filler audio** — audio indicators during processing latency
- **Entity confirmation** — automatic readback of names, emails, phone numbers
- **Interruption detection** — distinguishes genuine interruptions from acknowledgements
- **Content safety guardrails** — prevents offensive language, protects private information
- **Spoken delivery optimization** — automatic pausing for addresses, numbers, structured data

---

## Voice Pipeline Architecture (reference)

```
Caller speaks → STT (Deepgram) → text transcript
    → Reasoning Engine → text response
        → TTS (ElevenLabs) → spoken audio → caller hears
```

- **STT** — speech to text. Key-Term Prompting improves accuracy here.
- **TTS** — text to speech. Voice Selection + Speed + Stability + Similarity + Pronunciation Dictionary control this stage.
- Persona instructions affect the reasoning engine (what to say). Voice settings affect the TTS engine (how it sounds). These are independent encoding surfaces that must be designed together.
