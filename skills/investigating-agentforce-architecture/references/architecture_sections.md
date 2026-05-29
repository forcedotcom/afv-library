# architecture.md section reference

Per-section rendering spec for `scripts/render_architecture.py::render`.
Ten core sections + one conditional section. Source of truth: the
`metadata_tree.json` schema produced by `scripts/parse_wave.py` at the
end of phase 9.

**Source of truth: the live tree** — field shapes evolve as parse_wave
learns new agent generations. When this doc disagrees with the
`metadata_tree.json` written by `parse_wave.py` for an actual agent on
your machine (under `~/.claude/data/investigating-agentforce-architecture/<org>/<agent>__<ver>/`),
trust the live tree.

The Mermaid templates live at `assets/mermaid/*.mmd` and are the sole
consumer of the renderer helpers; each `{{PARAM}}` contract is
documented in the template's own header comment.

---

## Per-diagram node caps

Default caps (override via `render(..., max_mermaid_nodes={...})`):

| Diagram kind | Default cap | Over-cap behaviour |
|---|---|---|
| `flowchart` | 200 | summary placeholder + top-5 fan-out + catalog pointer |
| `stateDiagram` | 40 | summary placeholder (no fan-out — states are not nodes) |
| `sequenceDiagram` | 60 | summary placeholder + top-5 fan-out |
| `graph` | 100 | summary placeholder + top-5 fan-out |

Cap is measured in rendered elements (nodes + edges for flowchart/graph,
messages for sequenceDiagram, states + transitions for stateDiagram).
Above cap, the renderer emits a `> [diagram truncated: ...]` blockquote
with the element count, the top-5 nodes by fan-out (when applicable),
and a pointer to the catalog section that enumerates the same data
without compression.

---

## 1. Header + agent overview

**Purpose**: identify the agent and its planner in a single kv table.

**Input fields** (`tree.agent.*`):

- `api_name` — agent developer name
- `version` — `v<N>` label
- `master_label` — human-readable name
- `description` — prose summary
- `agent_type` — `EinsteinAgentKind` / `EinsteinCopilotForSalesforce` / …
- `type` — `ExternalCopilot` / `InternalCopilot` / …
- `agent_template`
- `bot_source`
- `generation` — `classic` / `nga` / `search` / `byop`
- `planner_name`
- `planner_type`
- `bot_id`

Plus `tree._schema_version`.

**Output shape**: `# <H1>` with api_name + version, followed by a 2-col
markdown table.

**Empty/degenerate cases**:

- Missing `api_name` / `version` renders `?` in the H1 (not `None`).
- Any missing field renders `-` in its row — not empty, because GitHub
 table rendering collapses empty cells and the row loses alignment.

---

## 2. Anatomy summary

**Purpose**: one-paragraph executive summary plus health callouts.

**Input fields**:

- `tree._kind_counts` — preferred source for topic / action / flow /
 apex / prompt counts.
- `tree.depth`, `tree.node_count` — size metrics.
- `tree._partial`, `tree._partial_reason` — health flag + prose reason.
- `tree._pending_fetches` — `{"FLOW":[...],"APEX":[...],
 "PROMPT_TEMPLATE":[...],"STANDARD_ACTION":[...]}`. Count determines
 the "pending fetches: N" line in the callout.
- `tree._unresolved` — triggers a second warn callout with the count.
- `tree.agent.planner_name` — missing -> warn callout.

**Output shape**: `## 2. Anatomy summary` + paragraph + zero-to-three
blockquote callouts. Callouts render as `> **Health: PARTIAL.**` /
`> **Health: WARN.**` prefixes with bullet sub-lines.

**Empty/degenerate cases**: if `_kind_counts` is absent, the walker
supplies counts from its own pass over the tree. Zero topics is valid
(SequentialPlannerIntentClassifier).

---

## 3. Invocation sequence

**Purpose**: show the lanes a single user turn traverses, from utterance
to response.

**Input fields**:

- `tree.agent.generation` — drives lane selection.
- `tree.agent.planner_type` — distinguishes ReAct vs Sequential within
 `classic`.
- Walker-derived `topics[]` and `actions[]` — message count estimate.

**Output shape**: `sequenceDiagram` via `load_mermaid("invocation_
sequence", ...)`. Lanes per generation:

| Generation | Lanes |
|---|---|
| `classic` + ReAct | User, Planner, TopicClassifier, ActionExecutor |
| `classic` + SequentialPlannerIntentClassifier | User, Planner, ActionExecutor |
| `nga` (ConcurrentMultiAgent, VoiceAgent) | User, Planner, Orchestrator, SubAgent, ActionExecutor |
| `search` / `byop` | same as `classic` ReAct (planner lane labelled generically) |

**Empty/degenerate cases**: 0 topics still renders — the Planner ->
ActionExecutor round-trip fires without a TopicClassifier hop. Above
the `sequenceDiagram` cap, the section emits the truncation placeholder
and skips the mermaid block entirely.

---

## 4. Action tree

**Purpose**: the full declared action tree as a flowchart with per-topic
subgraphs, plus a deterministic ASCII appendix for diff review.

**Input fields**:

- Walker-derived `topics[]` -> one subgraph per topic.
- Walker-derived `edges[]` -> `parent_api_name --> child_api_name`.
- `node._cycle_back_to` -> dotted back-edge `A -.->|cycle_back_to: X| B`.
- Planner-level actions (top-level `GEN_AI_FUNCTION` with no parent
 topic) -> synthetic `_plannerActions` subgraph.

**Output shape**: ` ```mermaid ` block with `flowchart TB` + subgraphs
+ edges, followed by a `<details>` with ASCII-tree appendix. When
above cap, the mermaid block is replaced with the truncation
placeholder; the ASCII appendix still renders.

**Empty/degenerate cases**:

- No topics, no planner actions -> `%% no topics` + `%% no edges`
 mermaid comments; diagram still parses.
- Cycle annotations render in both the mermaid (dotted edge) and the
 ASCII appendix (`[cycle]` marker on the node line).

---

## 5. Topic anatomy

**Purpose**: per-topic detail dump. One H3 per topic with a bullet list
of actions.

**Input fields**:

- Walker-derived `topics[]` with `api_name`, `label`, `actions`.
- `topic.raw.master_label` (preferred) or api_name for the label.

**Output shape**: `## 5. Topic anatomy` + one `### \`<api_name>\``
block per topic + kv list (`- Label:`, `- Action count:`, `- Actions:`
with sub-bullets).

**Empty/degenerate cases**: 0 topics -> `_No topics defined (planner
exposes actions directly)._` italic fallback. This is the expected
case for `SequentialPlannerIntentClassifier`.

---

## 6. Action catalog

**Purpose**: flat markdown table of every declared action.

**Input fields**:

- Walker-derived `actions[]` with `api_name`, `topic`, `raw.unwraps_to`.

**Output shape**: 3-col table (`Action | Topic | Unwraps to`). Unwraps
column renders as `KIND \`api_name\`` when `unwraps_to` is present, `-`
otherwise. Planner-level actions show `(plannerAction)` in the topic
column.

**Empty/degenerate cases**: no actions -> `_No actions declared._`
italic fallback.

---

## 7. Planner state machine

**Purpose**: illustrate the planner's control-flow shape.

**Input fields**:

- `tree.agent.generation` — primary branch.
- `tree.agent.planner_type` — sub-branch within `classic`.

**Output shape**: `stateDiagram-v2` via `load_mermaid("planner_state",
...)`. Per-generation templates:

| Generation | States | Transitions |
|---|---|---|
| `classic` + ReAct | Thought / Action / Observation / Respond | Thought -> Action -> Observation -> Thought, Observation -> Respond |
| `classic` + Sequential | Classify / Execute / Respond | linear |
| `nga` | Planning / Orchestration (par/and) / Respond | Planning -> Orchestration -> Respond |
| `search` / `byop` | (skipped — prose placeholder) | (skipped) |

**Empty/degenerate cases**: `search` / `byop` generations render a
one-line italic placeholder noting that the planner is Apex-backed and
pointing at section 9. No mermaid block is emitted.

---

## 8. Data flow / context propagation

**Purpose**: show which slot values propagate from user utterance
through the planner into each action.

**Input fields**:

- Walker-derived `topics[]` and `actions[]`.
- `action.raw.planner_attr.variable_name` + `planner_attr.data_type` —
 labels the edge `A -->|var: Type| B`. When absent, the edge is bare.

**Output shape**: `flowchart LR` via `load_mermaid("data_flow", ...)`.
Skeleton: `User` -> `Planner` -> each `Topic` -> each `Action` under
that topic.

**Empty/degenerate cases**: no planner_attr metadata -> every edge is
bare. 0 topics -> only `User --> Planner` renders (no action-level
edges). Above cap -> truncation placeholder.

---

## 9. Flow / Apex / Prompt catalogs

**Purpose**: per-artifact detail section for every backing flow, apex
class, and prompt template referenced by any action.

**Input fields**:

- Walker-derived `flows{}`, `apex{}`, `prompts{}`, keyed on api_name.
- `node.signature` (or `_signature` fallback) — signature block.

**Output shape**: `### Flows` / `### Apex classes` / `### Prompt
templates` H3 buckets, each containing `#### \`<api_name>\`` + a fenced
signature block or `_Signature not captured._` fallback. Prompt
templates render as a flat bullet list (signature capture is
per-template prose, not a flow/apex shape).

**Empty/degenerate cases**: no backing artifacts in the tree ->
`_No backing artifacts in tree._` italic fallback.

---

## 10. Unresolved refs + artifact pointers

**Purpose**: surface every `_unresolved[]` entry and point at the
sidecar files the reader can open.

**Input fields**:

- `tree._unresolved[]` — list of `{kind, api_name, reason}` records.

**Output shape**: Either a 3-col `Kind | Api name | Reason` table or
an `_No unresolved references._` italic fallback. Followed by an
`### Artifact pointers` sub-heading with a bullet list of relative
paths (tree JSON, manifest, summary).

**Empty/degenerate cases**: always renders — the artifact-pointer list
is unconditional.

---

## Conditional: Dependency graph

**Purpose**: rendered only when `tree._unresolved[]` is non-empty OR
the tree contains cycle annotations. Shows cross-artifact dependencies
plus the unresolved nodes as dashed-outline markers.

**Input fields**:

- Walker-derived `edges[]`.
- `tree._unresolved[]` — each becomes a `:::unresolved` styled node.
- Walker-derived `cycles[]` — each becomes a dotted back-edge.

**Output shape**: `graph LR` via `load_mermaid("dependency_graph",
...)`. Includes a `classDef unresolved` class marker at the bottom of
the template so unresolved nodes render with `stroke-dasharray`.

**Empty/degenerate cases**: not rendered at all when both conditions
are false. Above the `graph` cap -> truncation placeholder replaces
the mermaid block.
