<!-- Parent: sf-ai-agentforce-observability/SKILL.md -->
# Troubleshooting Guide

Common issues and solutions for Agentforce session tracing extraction.

## Authentication Issues

### 401 Unauthorized

**Symptom:**
```
RuntimeError: Token exchange failed: invalid_grant
```

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Expired JWT | Check certificate expiration with `openssl x509 -enddate -noout -in cert.crt` |
| Wrong consumer key | Verify consumer key matches External Client App |
| Certificate mismatch | Re-upload certificate to Salesforce |
| User not authorized | Assign user to Connected App / Permission Set |

**Debug Steps:**
```bash
# Test JWT generation
python3 -c "
from scripts.auth import DataCloudAuth
auth = DataCloudAuth('myorg', 'CONSUMER_KEY')
print(auth.get_token()[:50])
"

# Verify org connection
sf org display --target-org myorg --json
```

### 403 Forbidden

**Symptom:**
```
RuntimeError: Access denied: Ensure ECA has cdp_query_api scope
```

**Solutions:**

1. **Add Required Scopes** to External Client App:
   - `cdp_query_api`
   - `cdp_profile_api`

2. **Assign Data 360 Permissions** to user:
   - Setup → Permission Sets → Data 360 permissions

3. **Enable Data 360** in org:
   - Setup → Data 360 → Enable

---

## Data Issues

### No Session Data Found

**Symptom:**
```
Extracted 0 sessions
```

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Session tracing not enabled | Setup → Agentforce → Enable Session Tracing |
| Wrong date range | Data typically lags 5-15 minutes |
| Wrong agent name | Check exact API name with `sf org list metadata --metadata-type Bot --target-org <alias>` |
| Sandbox without data | Session tracing may not be enabled in sandbox |

**Debug:**
```python
# Check if DMO exists and has data
from scripts.datacloud_client import Data360Client

client = Data360Client(auth)
count = client.count("ssot__AIAgentSession__dlm")
print(f"Total sessions in Data 360: {count}")
```

### Query Timeout

**Symptom:**
```
RuntimeError: Request timed out after 3 retries
```

**Solutions:**

1. **Add date filters** to reduce data volume:
   ```python
   extractor.extract_sessions(
       since=datetime.now() - timedelta(days=1),  # Shorter range
   )
   ```

2. **Use incremental extraction**:
   ```bash
   python3 scripts/cli.py extract-incremental --org prod
   ```

3. **Increase timeout**:
   ```python
   client = DataCloudClient(auth, timeout=300.0)  # 5 minutes
   ```

### Memory Error

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. **Use lazy evaluation**:
   ```python
   # Good
   sessions = pl.scan_parquet(path)
   result = sessions.filter(...).collect()

   # Bad
   sessions = pl.read_parquet(path)  # Loads everything
   ```

2. **Stream to Parquet** instead of loading:
   ```python
   client.query_to_parquet(sql, output_path)  # Streams, doesn't load all
   ```

3. **Process in batches**:
   ```python
   for i in range(0, total_sessions, 1000):
       batch_ids = session_ids[i:i+1000]
       # Process batch
   ```

---

## Extraction Issues

### Missing Child Records

**Symptom:**
```
Sessions: 1000
Interactions: 0
Steps: 0
```

**Cause:** Session IDs not matching in child queries.

**Solution:**
```python
# Verify session IDs are valid
sessions_df = pl.read_parquet(data_dir / "sessions" / "data.parquet")
print(sessions_df.head())  # Check ssot__Id__c values

# Check if interactions exist for these sessions
interaction_query = f"""
SELECT COUNT(*) FROM ssot__AIAgentInteraction__dlm
WHERE ssot__AiAgentSessionId__c IN ('{session_ids[0]}')
"""
```

### Parquet Write Failure

**Symptom:**
```
ArrowInvalid: Could not convert X with type Y
```

**Solutions:**

1. **Check for nested/complex types**:
   ```python
   # Complex types are serialized to JSON strings
   if isinstance(value, (dict, list)):
       value = json.dumps(value)
   ```

2. **Use explicit schema**:
   ```python
   from scripts.models import SCHEMAS
   client.query_to_parquet(sql, path, schema=SCHEMAS["sessions"])
   ```

---

## Analysis Issues

### Polars Import Error

**Symptom:**
```
ImportError: No module named 'polars'
```

**Solution:**
```bash
pip install polars pyarrow
```

### Empty DataFrame

**Symptom:**
```python
analyzer.session_summary()  # Returns empty DataFrame
```

**Debug:**
```python
# Check if files exist
from pathlib import Path
data_dir = Path("./stdm_data")
print(list(data_dir.glob("**/*.parquet")))

# Check if files have data
import pyarrow.parquet as pq
pf = pq.ParquetFile(data_dir / "sessions" / "data.parquet")
print(f"Rows: {pf.metadata.num_rows}")
```

### Column Not Found

**Symptom:**
```
SchemaError: column 'ssot__Id__c' not found
```

**Cause:** Parquet file has different column names.

**Debug:**
```python
# Check actual column names
import pyarrow.parquet as pq
pf = pq.ParquetFile("path/to/file.parquet")
print(pf.schema_arrow)
```

---

## CLI Issues

### Command Not Found

**Symptom:**
```
bash: stdm-extract: command not found
```

**Solution:**
```bash
# Run directly
python3 scripts/cli.py extract --help

# Or install as package (if setup.py exists)
pip install -e .
```

### Environment Variable Not Set

**Symptom:**
```
ValueError: Consumer key not found. Set SF_CONSUMER_KEY
```

**Solutions:**

1. **Set environment variable**:
   ```bash
   export SF_CONSUMER_KEY="3MVG9..."
   ```

2. **Pass via command line**:
   ```bash
   python3 scripts/cli.py extract --org prod --consumer-key "3MVG9..."
   ```

3. **Create `.env` file** (if using python-dotenv):
   ```
   SF_CONSUMER_KEY=3MVG9...
   ```

---

## Data 360 Specific Issues

### DMO Not Found

**Symptom:**
```
Error: Object ssot__AIAgentSession__dlm not found
```

**Causes:**

1. **Session tracing not enabled** - Enable in Agentforce settings
2. **Wrong API version** - Use v66.0 or higher
3. **Permission issue** - User needs Data 360 access

### Query Syntax Error

**Symptom:**
```
Error: Unexpected token at position X
```

**Common fixes:**

| Issue | Fix |
|-------|-----|
| Single quotes in values | Escape: `'O''Brien'` |
| Reserved words | Use backticks: `` `Order` `` |
| Date format | Use ISO: `'2026-01-28T00:00:00.000Z'` |

---

## Lessons Learned (Live Deployment - Jan 2026)

Critical discoveries from live testing against a sandbox org.

### API Version: v66.0 Recommended

**Problem:** Documentation referenced v60.0, but Data 360 Query SQL API requires v64.0+. We recommend v66.0 (Spring '26).

**Fix:**
```python
# Wrong (v60.0)
url = f"{instance_url}/services/data/v60.0/ssot/querybuilder/execute"

# Correct (v66.0)
url = f"{instance_url}/services/data/v66.0/ssot/query-sql"
```

### Field Naming: AiAgent (lowercase 'i')

**Problem:** Documentation shows `AIAgent` but actual schema uses `AiAgent`.

**Wrong:**
```sql
SELECT ssot__AIAgentSessionId__c FROM ssot__AIAgentInteraction__dlm
```

**Correct:**
```sql
SELECT ssot__AiAgentSessionId__c FROM ssot__AIAgentInteraction__dlm
```

**Affected fields:** All FK references in Interaction, Step, and Moment DMOs.

### AIAgentMoment Links to Sessions, Not Interactions

**Problem:** Documentation implied Moments link to Interactions via `AIAgentInteractionId__c`.

**Reality:** AIAgentMoment links directly to Sessions via `ssot__AiAgentSessionId__c`.

**Correct Schema:**
```
AIAgentSession → AIAgentInteraction → AIAgentInteractionStep
       ↓
AIAgentMoment (links to session, not interaction)
```

### Response Format: Array of Arrays

**Problem:** Expected array of objects, but v64.0+ returns array of arrays.

**v65.0 Response:**
```json
{
  "metadata": [{"name": "ssot__Id__c"}, {"name": "ssot__Name__c"}],
  "data": [
    ["019abc...", "Session 1"],
    ["019def...", "Session 2"]
  ]
}
```

**Fix:** Convert using metadata column names:
```python
column_names = [col["name"] for col in metadata]
records = [dict(zip(column_names, row)) for row in data]
```

### External Client App Setup URL

**Problem:** Documentation had wrong Setup URL.

**Wrong:** `/lightning/setup/ExternalClientAppManager/home`
**Correct:** `/lightning/setup/ManageExternalClientApplication/home`

### Incremental Extraction Overwrites Data

**Problem:** `extract-incremental` was overwriting Parquet files instead of appending.

**Symptoms:**
- Running incremental after full extract → lost all historical data
- Session count dropped from 447 to 17

**Fix:** Added `append` + `dedupe_key` parameters to `query_to_parquet()`:
```python
# Now correctly reads existing, appends new, dedupes by ID
result = client.query_to_parquet(
    sql, output_path,
    append=True,
    dedupe_key="ssot__Id__c"
)
```

### Session End Types All NOT_SET

**Observation:** 100% of sessions had `ssot__AiAgentSessionEndType__c = 'NOT_SET'`.

**Possible causes:**
- Sessions not explicitly closed
- Agent Builder sessions don't track end types
- Potential data quality issue in source org

**Recommendation:** Investigate session closure patterns in agent configuration.

---

## Getting Help

### Debug Mode

```bash
# Enable verbose logging
python3 scripts/cli.py extract --org prod --verbose 2>&1 | tee debug.log
```

### Check Data 360 Status

```bash
# List available DMOs
python3 -c "
from scripts.auth import Data360Auth
from scripts.datacloud_client import Data360Client

auth = Data360Auth('prod', 'KEY')
client = Data360Client(auth)
dmos = client.list_dmos()
for dmo in dmos:
    print(dmo.get('name'))
"
```

### Report Issues

If you encounter issues not covered here:

1. Enable verbose mode and capture logs
2. Note the error message and stack trace
3. Check Data 360 health status
4. Contact Salesforce support for API issues
