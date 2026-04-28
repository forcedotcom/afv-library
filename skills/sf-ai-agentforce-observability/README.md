# sf-ai-agentforce-observability

![Status: GA](https://img.shields.io/badge/Status-GA-brightgreen)
![Tests: 260+ Passed](https://img.shields.io/badge/Tests-260%2B%20Passed-success)
![DMOs: 24 Verified](https://img.shields.io/badge/DMOs-24%20Verified-blue)
![Validation: Live API Tested](https://img.shields.io/badge/Validation-Live%20API%20Tested-blue)

Extract and analyze Agentforce session tracing data from Salesforce Data Cloud.

## Status: General Availability (GA)

This skill has been validated against live Salesforce orgs and is production-ready.

| Metric | Value |
|--------|-------|
| **Test Coverage** | 260+ tests across 6 tiers |
| **DMO Discovery** | 24 DMOs verified, 3 not found (RAG Quality) |
| **Live API Validation** | All SQL patterns tested against Data Cloud |
| **Schema Accuracy** | Verified column names match actual API |
| **Last Validated** | January 30, 2026 |

## Features

- **High-Volume Extraction**: Handle 1-10M records/day via Data Cloud Query API
- **Parquet Storage**: Efficient columnar storage (10x smaller than JSON)
- **Polars Analysis**: Lazy evaluation for memory-efficient analysis of 100M+ rows
- **Session Debugging**: Reconstruct session timelines for troubleshooting
- **Incremental Sync**: Watermark-based extraction for continuous monitoring
- **GenAI Quality Analysis**: Extract Trust Layer metrics (toxicity, adherence, resolution)

## Quick Start

### 1. Prerequisites

```bash
# Install Python dependencies
pip install polars pyarrow pyjwt cryptography httpx rich click pydantic

# Verify Data Cloud access
sf org display --target-org myorg
```

### 2. Configure Authentication

Session tracing extraction requires JWT Bearer auth to the Data Cloud Query API.

```bash
# Generate certificate
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
  -keyout ~/.sf/jwt/myorg.key \
  -out ~/.sf/jwt/myorg.crt \
  -subj "/CN=DataCloudAuth"

# Create External Client App (via sf-connected-apps skill)
# Required scopes: cdp_query_api, cdp_profile_api
```

See [references/auth-setup.md](references/auth-setup.md) for detailed instructions.

### 3. Extract Session Data

```bash
# Extract last 7 days
python3 scripts/cli.py extract --org myorg --days 7 --output ./data

# Extract specific date range
python3 scripts/cli.py extract --org myorg --since 2026-01-01 --until 2026-01-15

# Extract complete session tree for debugging
python3 scripts/cli.py extract-tree --org myorg --session-id "a0x..."
```

### 4. Analyze Data

```bash
# Session summary
python3 scripts/cli.py analyze --data-dir ./data

# Debug specific session
python3 scripts/cli.py debug-session --data-dir ./data --session-id "a0x..."

# Topic analysis
python3 scripts/cli.py topics --data-dir ./data

# Extract GenAI quality metrics
python3 scripts/cli.py extract-quality --data-dir ./data
```

### 5. Use with Python

```python
from scripts.analyzer import STDMAnalyzer
from pathlib import Path

analyzer = STDMAnalyzer(Path("./data"))

# Session summary
print(analyzer.session_summary())

# Step distribution
print(analyzer.step_distribution())

# Message timeline for debugging
print(analyzer.message_timeline("a0x..."))
```

## Data Model

**24 DMOs verified** via T6 live API testing (January 2026):

### Session Tracing DMOs (5)
```
AIAgentSession (18 fields)
├── AIAgentSessionParticipant (12 fields) - Roles: USER, AGENT
├── AIAgentInteraction (20 fields) - Types: TURN, SESSION_END
│   ├── AIAgentInteractionStep (23 fields) - Types: LLM_STEP, ACTION_STEP, TOPIC_STEP
│   └── AIAgentInteractionMessage (21 fields) - Types: Input, Output
└── AIAgentMoment (13 fields) - Contains Agent API name
```

### GenAI Audit & Feedback DMOs (13) ✅ T6 Verified
```
GenAIGatewayRequest (30 fields) - LLM call details, token usage
├── GenAIGatewayResponse (8 fields)
├── GenAIGeneration (11 fields) - LLM output text
│   ├── GenAIContentQuality (10 fields) - Trust Layer assessment
│   │   └── GenAIContentCategory (10 fields) - Detector results
│   └── GenAIFeedback (16 fields) - User thumbs up/down
│       └── GenAIFeedbackDetail (10 fields) - Feedback comments
└── GenAIGatewayRequestTag, GenAIGtwyRequestMetadata, GenAIGtwyObjRecord...
```

### Key Enum Values (Live API Verified)
| Entity | Field | Values |
|--------|-------|--------|
| Session | ChannelType | `E & O`, `Builder`, `SCRT2 - EmbeddedMessaging`, `Voice`, `NGC` |
| Participant | AgentType | `EinsteinServiceAgent`, `AgentforceEmployeeAgent`, `AgentforceServiceAgent` |
| Participant | Role | `USER`, `AGENT` |
| Step | StepType | `LLM_STEP`, `ACTION_STEP`, `TOPIC_STEP`, `SESSION_END` |
| ContentCategory | DetectorType | `TOXICITY`, `PII`, `PROMPT_DEFENSE`, `InstructionAdherence` |

### DMOs NOT Found (3)
- `GenAIRetrieverResponse__dlm` ❌
- `GenAIRetrieverRequest__dlm` ❌
- `GenAIRetrieverQualityMetric__dlm` ❌

**Important**: Data Cloud uses `AiAgent` (lowercase 'i') in field names, not `AIAgent`.

See [references/data-model-reference.md](references/data-model-reference.md) for full schema.

## Output Format

Data is stored in Parquet format:

```
stdm_data/
├── sessions/data.parquet
├── interactions/data.parquet
├── steps/data.parquet
├── messages/data.parquet
├── generations/data.parquet        # GenAI quality
├── content_quality/data.parquet    # Trust Layer
├── content_categories/data.parquet # Toxicity/Adherence
└── metadata/
    ├── extraction.json
    └── watermark.json
```

## Real-Time Trace Analysis

For real-time agent trace capture and analysis (v1.1 PlanSuccessResponse with 13 step types), use **sf-ai-agentforce-testing** Phase F via `sf agent preview start/send/end`. This replaces the previous browser-based capture approach with a simpler CLI workflow.

## CLI Reference

| Command | Description |
|---------|-------------|
| `extract` | Extract session data for time range |
| `extract-tree` | Extract full tree for specific session |
| `extract-incremental` | Continue from last extraction |
| `extract-quality` | Extract GenAI Trust Layer metrics |
| `analyze` | Generate summary statistics |
| `debug-session` | Show session timeline |
| `topics` | Topic routing analysis |
| `count` | Count records per DMO |
| `trace-test` | Capture Builder execution traces |

See [references/cli-reference.md](references/cli-reference.md) for all options.

## Validation

This skill includes comprehensive validation testing:

| Tier | Category | Tests | Description |
|------|----------|-------|-------------|
| T1 | Auth & Connectivity | 5 | JWT auth, API access, DMO existence |
| T2 | Extraction Commands | 35 | CLI extract, tree, incremental |
| T3 | Analysis Commands | 46 | Analyze, debug-session, topics |
| T4 | Schema/Documentation | 96 | Field validation, query patterns |
| T5 | Negative Cases | 12 | Error handling, invalid args |
| T6 | **Live SQL Execution** | 39 | All SQL patterns against live API |
| T6 | **DMO Discovery** | 27 | Probe all 27 DMOs for existence |
| T6 | **Field Discovery** | 47 | Discover all fields per DMO |

**Total: 260+ tests | 100% pass rate** (34 discovery tests skip as expected for non-existent DMOs)

Run validation:
```bash
cd validation
source .venv/bin/activate
pytest scenarios/ -v --org YourOrgAlias
```

## Integration with Other Skills

| Skill | Use Case |
|-------|----------|
| `sf-connected-apps` | Set up JWT Bearer auth |
| `sf-ai-agentscript` | Fix agents based on trace analysis |
| `sf-ai-agentforce-testing` | Create tests from observed patterns |
| `sf-debug` | Deep-dive into action failures |

## Requirements

- Python 3.10+
- Salesforce org with Data Cloud and Agentforce enabled
- Session Tracing enabled in Agentforce settings
- JWT Bearer auth configured (via External Client App)
- Salesforce Standard Data Model v1.124+

## Resources

- [Data Model Reference](references/data-model-reference.md) - Full STDM schema
- [Query Patterns](references/query-patterns.md) - SQL examples for Data Cloud
- [Analysis Cookbook](references/analysis-cookbook.md) - Polars analysis patterns
- [Polars Cheatsheet](references/polars-cheatsheet.md) - Quick reference

## License

MIT License - See [LICENSE](LICENSE) file.

## Author

Jag Valaiyapathy

---

*Last updated: January 2026 | Validated against live org*
