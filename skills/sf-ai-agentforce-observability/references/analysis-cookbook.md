<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Analysis Cookbook

Common analysis patterns using Polars for session tracing data.

## Getting Started

```python
from pathlib import Path
import polars as pl

# Load data as lazy frames (memory efficient)
data_dir = Path("./stdm_data")

sessions = pl.scan_parquet(data_dir / "sessions" / "**/*.parquet")
interactions = pl.scan_parquet(data_dir / "interactions" / "**/*.parquet")
steps = pl.scan_parquet(data_dir / "steps" / "**/*.parquet")
messages = pl.scan_parquet(data_dir / "messages" / "**/*.parquet")
```

---

## Session Analysis

### Basic Statistics

```python
# Session count by agent
sessions.group_by("ssot__AiAgentApiName__c").agg(
    pl.count().alias("session_count")
).sort("session_count", descending=True).collect()
```

### Completion Rate by Agent

```python
sessions.group_by("ssot__AiAgentApiName__c").agg([
    pl.count().alias("total"),
    pl.col("ssot__AiAgentSessionEndType__c")
      .filter(pl.col("ssot__AiAgentSessionEndType__c") == "Completed")
      .count().alias("completed")
]).with_columns([
    (pl.col("completed") / pl.col("total") * 100).round(1).alias("completion_rate")
]).collect()
```

### Session Duration Analysis

```python
# Note: Requires timestamp parsing
sessions.with_columns([
    pl.col("ssot__StartTimestamp__c").str.to_datetime().alias("start"),
    pl.col("ssot__EndTimestamp__c").str.to_datetime().alias("end"),
]).with_columns([
    (pl.col("end") - pl.col("start")).alias("duration")
]).group_by("ssot__AiAgentApiName__c").agg([
    pl.col("duration").mean().alias("avg_duration"),
    pl.col("duration").max().alias("max_duration"),
]).collect()
```

---

## Interaction Analysis

### Turns per Session

```python
turns_per_session = (
    interactions
    .filter(pl.col("ssot__AiAgentInteractionType__c") == "TURN")
    .group_by("ssot__AiAgentSessionId__c")
    .agg(pl.count().alias("turn_count"))
)

# Distribution
turns_per_session.group_by("turn_count").agg(
    pl.count().alias("sessions")
).sort("turn_count").collect()
```

### Topic Routing

```python
# Most common topics
interactions.filter(
    pl.col("ssot__AiAgentInteractionType__c") == "TURN"
).group_by("ssot__TopicApiName__c").agg(
    pl.count().alias("turn_count"),
    pl.col("ssot__AiAgentSessionId__c").n_unique().alias("session_count")
).sort("turn_count", descending=True).collect()
```

### Topic Switches (Multi-Topic Sessions)

```python
# Sessions that used multiple topics
topic_counts = (
    interactions
    .filter(pl.col("ssot__AiAgentInteractionType__c") == "TURN")
    .group_by("ssot__AiAgentSessionId__c")
    .agg(pl.col("ssot__TopicApiName__c").n_unique().alias("topic_count"))
)

# Sessions with 2+ topics
topic_counts.filter(pl.col("topic_count") > 1).collect()
```

---

## Step Analysis

### LLM vs Action Ratio

```python
steps.group_by("ssot__AiAgentInteractionStepType__c").agg(
    pl.count().alias("count")
).with_columns([
    (pl.col("count") / pl.col("count").sum() * 100).round(1).alias("percentage")
]).collect()
```

### Most Used Actions

```python
steps.filter(
    pl.col("ssot__AiAgentInteractionStepType__c") == "ACTION_STEP"
).group_by("ssot__Name__c").agg(
    pl.count().alias("invocations")
).sort("invocations", descending=True).head(20).collect()
```

### Steps per Turn Distribution

```python
steps_per_turn = (
    steps
    .group_by("ssot__AiAgentInteractionId__c")
    .agg(pl.count().alias("step_count"))
)

steps_per_turn.group_by("step_count").agg(
    pl.count().alias("turns")
).sort("step_count").collect()
```

### Action Input/Output Analysis

```python
# Parse JSON in action inputs (example for specific action)
action_steps = steps.filter(
    (pl.col("ssot__AiAgentInteractionStepType__c") == "ACTION_STEP") &
    (pl.col("ssot__Name__c") == "Get_Order_Status")
).collect()

# Parse inputs
import json
for row in action_steps.iter_rows(named=True):
    input_data = json.loads(row["ssot__InputValueText__c"] or "{}")
    output_data = json.loads(row["ssot__OutputValueText__c"] or "{}")
    print(f"Input: {input_data}, Output: {output_data}")
```

---

## Message Analysis

### Message Length Distribution

```python
messages.with_columns([
    pl.col("ssot__ContentText__c").str.len_chars().alias("length")
]).group_by("ssot__AiAgentInteractionMessageType__c").agg([
    pl.col("length").mean().alias("avg_length"),
    pl.col("length").max().alias("max_length"),
]).collect()
```

### Common User Phrases

```python
# Word frequency in user messages (simple)
user_messages = messages.filter(
    pl.col("ssot__AiAgentInteractionMessageType__c") == "INPUT"
).select("ssot__ContentText__c").collect()

# Count words
from collections import Counter
words = Counter()
for row in user_messages.iter_rows(named=True):
    content = row["ssot__ContentText__c"] or ""
    words.update(content.lower().split())

print(words.most_common(20))
```

---

## Time-Based Analysis

### Sessions by Date

```python
sessions.with_columns([
    pl.col("ssot__StartTimestamp__c").str.slice(0, 10).alias("date")
]).group_by("date").agg(
    pl.count().alias("sessions")
).sort("date").collect()
```

### Sessions by Hour

```python
sessions.with_columns([
    pl.col("ssot__StartTimestamp__c").str.slice(11, 2).alias("hour")
]).group_by("hour").agg(
    pl.count().alias("sessions")
).sort("hour").collect()
```

### Day of Week Analysis

```python
# Requires datetime conversion
sessions.with_columns([
    pl.col("ssot__StartTimestamp__c")
      .str.to_datetime()
      .dt.weekday()
      .alias("weekday")
]).group_by("weekday").agg(
    pl.count().alias("sessions")
).sort("weekday").collect()
```

---

## Debugging Patterns

### Find Failed Sessions

```python
failed = sessions.filter(
    pl.col("ssot__AiAgentSessionEndType__c").is_in(["Escalated", "Abandoned", "Failed"])
).sort("ssot__StartTimestamp__c", descending=True).collect()

for row in failed.head(5).iter_rows(named=True):
    print(f"Session: {row['ssot__Id__c']}")
    print(f"  Agent: {row['ssot__AiAgentApiName__c']}")
    print(f"  End: {row['ssot__AiAgentSessionEndType__c']}")
    print()
```

### Session Timeline Reconstruction

```python
def get_timeline(session_id: str) -> pl.DataFrame:
    """Reconstruct message timeline for a session."""
    # Get interaction IDs
    interaction_df = interactions.filter(
        pl.col("ssot__AiAgentSessionId__c") == session_id
    ).collect()

    interaction_ids = interaction_df["ssot__Id__c"].to_list()

    # Get messages
    msg_df = messages.filter(
        pl.col("ssot__AiAgentInteractionId__c").is_in(interaction_ids)
    ).sort("ssot__MessageSentTimestamp__c").collect()

    return msg_df

# Usage
timeline = get_timeline("a0x1234567890ABC")
for row in timeline.iter_rows(named=True):
    msg_type = row["ssot__AiAgentInteractionMessageType__c"]
    content = row["ssot__ContentText__c"]
    icon = "→" if msg_type == "INPUT" else "←"
    print(f"{icon} {content[:100]}...")
```

---

## Performance Tips

### Use Lazy Evaluation

```python
# Good: Lazy evaluation, deferred execution
result = (
    sessions
    .filter(pl.col("ssot__AiAgentApiName__c") == "My_Agent")
    .group_by("ssot__AiAgentSessionEndType__c")
    .agg(pl.count())
    .collect()  # Execute here
)

# Avoid: Eager loading of everything
df = pl.read_parquet(data_dir / "sessions" / "**/*.parquet")  # Loads all data
result = df.filter(...)  # Then filter
```

### Select Only Needed Columns

```python
# Good: Select specific columns
sessions.select([
    "ssot__Id__c",
    "ssot__AiAgentApiName__c",
    "ssot__AiAgentSessionEndType__c"
]).collect()

# Avoid: Select all columns
sessions.collect()  # Includes all columns
```

### Use Streaming for Large Results

```python
# For very large datasets
for batch in sessions.collect(streaming=True):
    # Process batch
    pass
```
