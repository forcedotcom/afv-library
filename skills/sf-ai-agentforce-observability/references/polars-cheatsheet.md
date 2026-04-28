<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Polars Cheatsheet

Quick reference for analyzing STDM data with Polars.

## Loading Data

```python
import polars as pl
from pathlib import Path

data_dir = Path("./stdm_data")

# Lazy loading (recommended for large datasets)
sessions = pl.scan_parquet(data_dir / "sessions" / "**/*.parquet")
interactions = pl.scan_parquet(data_dir / "interactions" / "**/*.parquet")
steps = pl.scan_parquet(data_dir / "steps" / "**/*.parquet")
messages = pl.scan_parquet(data_dir / "messages" / "**/*.parquet")

# Eager loading (loads everything into memory)
sessions_df = pl.read_parquet(data_dir / "sessions" / "**/*.parquet")
```

---

## Basic Operations

### Count Records
```python
sessions.select(pl.count()).collect()
# Or
len(sessions.collect())
```

### View Schema
```python
sessions.collect_schema()
```

### Preview Data
```python
sessions.head(5).collect()
sessions.fetch(5)  # Faster, doesn't scan full file
```

### Select Columns
```python
sessions.select([
    "ssot__Id__c",
    "ssot__AiAgentApiName__c",
    "ssot__AiAgentSessionEndType__c"
]).collect()
```

---

## Filtering

### Single Condition
```python
sessions.filter(pl.col("ssot__AiAgentApiName__c") == "My_Agent")
```

### Multiple Conditions (AND)
```python
sessions.filter(
    (pl.col("ssot__AiAgentApiName__c") == "My_Agent") &
    (pl.col("ssot__AiAgentSessionEndType__c") == "Completed")
)
```

### Multiple Conditions (OR)
```python
sessions.filter(
    pl.col("ssot__AiAgentSessionEndType__c").is_in(["Escalated", "Failed"])
)
```

### Null Checks
```python
sessions.filter(pl.col("ssot__EndTimestamp__c").is_not_null())
sessions.filter(pl.col("ssot__EndTimestamp__c").is_null())
```

### String Contains
```python
messages.filter(pl.col("ssot__ContentText__c").str.contains("order"))
```

---

## Aggregation

### Group By with Count
```python
sessions.group_by("ssot__AiAgentApiName__c").agg(
    pl.count().alias("session_count")
).sort("session_count", descending=True).collect()
```

### Multiple Aggregations
```python
sessions.group_by("ssot__AiAgentApiName__c").agg([
    pl.count().alias("total"),
    pl.col("ssot__AiAgentSessionEndType__c")
      .filter(pl.col("ssot__AiAgentSessionEndType__c") == "Completed")
      .count().alias("completed")
]).collect()
```

### Unique Count
```python
interactions.group_by("ssot__AiAgentSessionId__c").agg(
    pl.col("ssot__TopicApiName__c").n_unique().alias("topic_count")
).collect()
```

---

## Joins

### Inner Join
```python
sessions.join(
    interactions,
    left_on="ssot__Id__c",
    right_on="ssot__AiAgentSessionId__c",
    how="inner"
)
```

### Left Join
```python
sessions.join(
    interactions,
    left_on="ssot__Id__c",
    right_on="ssot__AiAgentSessionId__c",
    how="left"
)
```

---

## Date/Time Operations

### Parse Timestamp
```python
sessions.with_columns(
    pl.col("ssot__StartTimestamp__c").str.to_datetime().alias("start_dt")
)
```

### Extract Date Parts
```python
sessions.with_columns([
    pl.col("ssot__StartTimestamp__c").str.slice(0, 10).alias("date"),
    pl.col("ssot__StartTimestamp__c").str.slice(11, 2).alias("hour"),
])
```

### Date Filtering
```python
sessions.filter(
    pl.col("ssot__StartTimestamp__c") >= "2026-01-01T00:00:00.000Z"
)
```

---

## Computed Columns

### Add Column
```python
sessions.with_columns(
    (pl.col("completed") / pl.col("total") * 100).round(1).alias("completion_rate")
)
```

### String Length
```python
messages.with_columns(
    pl.col("ssot__ContentText__c").str.len_chars().alias("msg_length")
)
```

### Conditional Column
```python
sessions.with_columns(
    pl.when(pl.col("ssot__AiAgentSessionEndType__c") == "Completed")
      .then(pl.lit("Success"))
      .otherwise(pl.lit("Failure"))
      .alias("outcome")
)
```

---

## Sorting

### Single Column
```python
sessions.sort("ssot__StartTimestamp__c", descending=True)
```

### Multiple Columns
```python
sessions.sort(["ssot__AiAgentApiName__c", "ssot__StartTimestamp__c"])
```

---

## Output

### Collect (Execute)
```python
result = sessions.filter(...).collect()  # Returns DataFrame
```

### Write Parquet
```python
result.write_parquet("output.parquet")
```

### Write CSV
```python
result.write_csv("output.csv")
```

### To Python Dict
```python
result.to_dicts()  # List of dicts
result.row(0, named=True)  # Single row as dict
```

---

## Performance Tips

### 1. Use Lazy Evaluation
```python
# Good: Lazy, optimized query plan
result = (
    pl.scan_parquet(path)
    .filter(...)
    .group_by(...)
    .agg(...)
    .collect()
)

# Avoid: Eager, loads everything
df = pl.read_parquet(path)
result = df.filter(...)
```

### 2. Select Early
```python
# Good: Only load needed columns
sessions.select(["ssot__Id__c", "ssot__AiAgentApiName__c"]).filter(...)

# Avoid: Load all, filter later
sessions.filter(...).select(...)
```

### 3. Filter Before Join
```python
# Good: Filter before joining
filtered_sessions = sessions.filter(pl.col("ssot__AiAgentApiName__c") == "My_Agent")
filtered_sessions.join(interactions, ...)

# Avoid: Join everything, then filter
sessions.join(interactions, ...).filter(...)
```

### 4. Use Streaming for Large Results
```python
# For very large datasets
sessions.collect(streaming=True)
```

---

## Common Patterns

### Session Statistics
```python
sessions.group_by("ssot__AiAgentApiName__c").agg([
    pl.count().alias("sessions"),
    pl.col("ssot__AiAgentSessionEndType__c")
      .filter(pl.col("ssot__AiAgentSessionEndType__c") == "Completed")
      .count().alias("completed"),
    pl.col("ssot__AiAgentSessionEndType__c")
      .filter(pl.col("ssot__AiAgentSessionEndType__c") == "Escalated")
      .count().alias("escalated"),
]).collect()
```

### Daily Trend
```python
sessions.with_columns(
    pl.col("ssot__StartTimestamp__c").str.slice(0, 10).alias("date")
).group_by("date").agg(
    pl.count().alias("sessions")
).sort("date").collect()
```

### Top N Actions
```python
steps.filter(
    pl.col("ssot__AiAgentInteractionStepType__c") == "ACTION_STEP"
).group_by("ssot__Name__c").agg(
    pl.count().alias("invocations")
).sort("invocations", descending=True).head(10).collect()
```

---

## See Also

- [Analysis Cookbook](../references/analysis-cookbook.md) - Full recipes
- [Polars Documentation](https://docs.pola.rs/)
