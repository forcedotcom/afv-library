<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Analysis Examples

Examples for analyzing extracted STDM data with Polars and the CLI.

---

## CLI Analysis Commands

### Summary Statistics

Get high-level overview of extracted data:

```bash
stdm-extract analyze --data-dir ./stdm_data
```

**Output:**
```
📊 SESSION SUMMARY
═══════════════════════════════════════════════════════════

Agent                        Sessions  Completed  Escalated  Completion %
───────────────────────────────────────────────────────────────────────────
Customer_Support_Agent           450        382         45        84.9%
Order_Tracking_Agent             312        298          8        95.5%
FAQ_Agent                        156        152          2        97.4%
───────────────────────────────────────────────────────────────────────────
TOTAL                            918        832         55        90.6%
```

### Topic Analysis

See which topics handle the most turns:

```bash
stdm-extract topics --data-dir ./stdm_data
```

**Output:**
```
📊 TOPIC ROUTING
═══════════════════════════════════════════════════════════

Topic                        Turns  Sessions  Avg Turns/Session
───────────────────────────────────────────────────────────────
Order_Status                  1234       312              4.0
Return_Policy                  856       245              3.5
Account_Help                   654       198              3.3
General_FAQ                    432       156              2.8
```

### Action Analysis

See which actions are invoked most:

```bash
stdm-extract actions --data-dir ./stdm_data
```

**Output:**
```
📊 ACTION INVOCATIONS
═══════════════════════════════════════════════════════════

Action                       Count  Avg/Session
─────────────────────────────────────────────────
Get_Order_Status              1856         2.0
Search_Knowledge_Base         1245         1.4
Create_Case                    567         0.6
Update_Contact                 234         0.3
```

---

## Python Analysis

### Setup

```python
import polars as pl
from pathlib import Path

data_dir = Path("./stdm_data")

# Lazy loading (memory efficient)
sessions = pl.scan_parquet(data_dir / "sessions" / "**/*.parquet")
interactions = pl.scan_parquet(data_dir / "interactions" / "**/*.parquet")
steps = pl.scan_parquet(data_dir / "steps" / "**/*.parquet")
messages = pl.scan_parquet(data_dir / "messages" / "**/*.parquet")
```

### Session Analysis

**Sessions by End Type:**
```python
sessions.group_by("ssot__AiAgentSessionEndType__c").agg(
    pl.count().alias("count")
).sort("count", descending=True).collect()
```

**Daily Session Trend:**
```python
sessions.with_columns(
    pl.col("ssot__StartTimestamp__c").str.slice(0, 10).alias("date")
).group_by("date").agg(
    pl.count().alias("sessions")
).sort("date").collect()
```

**Hourly Distribution:**
```python
sessions.with_columns(
    pl.col("ssot__StartTimestamp__c").str.slice(11, 2).alias("hour")
).group_by("hour").agg(
    pl.count().alias("sessions")
).sort("hour").collect()
```

### Turn Analysis

**Turns Per Session:**
```python
turns_per_session = (
    interactions
    .filter(pl.col("ssot__AiAgentInteractionType__c") == "TURN")
    .group_by("ssot__AiAgentSessionId__c")
    .agg(pl.count().alias("turns"))
)

# Distribution
turns_per_session.group_by("turns").agg(
    pl.count().alias("sessions")
).sort("turns").collect()
```

**Multi-Topic Sessions (Topic Switches):**
```python
topic_counts = (
    interactions
    .filter(pl.col("ssot__AiAgentInteractionType__c") == "TURN")
    .group_by("ssot__AiAgentSessionId__c")
    .agg(pl.col("ssot__TopicApiName__c").n_unique().alias("topics"))
)

# Sessions with 2+ topics
topic_counts.filter(pl.col("topics") > 1).collect()
```

### Step Analysis

**LLM vs Action Ratio:**
```python
steps.group_by("ssot__AiAgentInteractionStepType__c").agg(
    pl.count().alias("count")
).with_columns(
    (pl.col("count") / pl.col("count").sum() * 100).round(1).alias("percent")
).collect()
```

**Most Used Actions:**
```python
steps.filter(
    pl.col("ssot__AiAgentInteractionStepType__c") == "ACTION_STEP"
).group_by("ssot__Name__c").agg(
    pl.count().alias("invocations")
).sort("invocations", descending=True).head(10).collect()
```

**Steps Per Turn:**
```python
steps.group_by("ssot__AiAgentInteractionId__c").agg(
    pl.count().alias("steps")
).group_by("steps").agg(
    pl.count().alias("turns")
).sort("steps").collect()
```

### Message Analysis

**Average Message Length by Type:**
```python
messages.with_columns(
    pl.col("ssot__ContentText__c").str.len_chars().alias("length")
).group_by("ssot__AiAgentInteractionMessageType__c").agg([
    pl.col("length").mean().round(0).alias("avg_length"),
    pl.col("length").max().alias("max_length"),
]).collect()
```

**Common User Phrases:**
```python
user_msgs = messages.filter(
    pl.col("ssot__AiAgentInteractionMessageType__c") == "INPUT"
).select("ssot__ContentText__c").collect()

from collections import Counter
words = Counter()
for row in user_msgs.iter_rows(named=True):
    text = row["ssot__ContentText__c"] or ""
    words.update(text.lower().split())

print(words.most_common(20))
```

---

## Using the Analyzer Class

The skill includes a helper class for common analyses:

```python
from scripts.analyzer import STDMAnalyzer

analyzer = STDMAnalyzer(Path("./stdm_data"))

# Quick summary
summary = analyzer.session_summary()
print(summary)

# Step breakdown
steps_df = analyzer.step_distribution()
print(steps_df)

# Topic patterns
topics_df = analyzer.topic_analysis()
print(topics_df)

# Find failed sessions
failed = analyzer.find_failed_sessions(limit=10)
print(failed)
```

---

## Exporting Results

### To CSV
```python
result = sessions.group_by(...).agg(...).collect()
result.write_csv("output.csv")
```

### To JSON
```python
result.write_json("output.json")
```

### To Parquet (for further analysis)
```python
result.write_parquet("output.parquet")
```

---

## Visualization (with Matplotlib)

```python
import matplotlib.pyplot as plt

# Daily trend
daily = sessions.with_columns(
    pl.col("ssot__StartTimestamp__c").str.slice(0, 10).alias("date")
).group_by("date").agg(
    pl.count().alias("sessions")
).sort("date").collect()

plt.figure(figsize=(12, 4))
plt.bar(daily["date"], daily["sessions"])
plt.xticks(rotation=45)
plt.title("Sessions per Day")
plt.tight_layout()
plt.savefig("daily_trend.png")
```

---

## See Also

- [Polars Cheatsheet](../references/polars-cheatsheet.md) - Quick reference
- [Analysis Cookbook](../references/analysis-cookbook.md) - More recipes
- [Debugging Sessions](debugging-sessions.md) - Session-level debugging
