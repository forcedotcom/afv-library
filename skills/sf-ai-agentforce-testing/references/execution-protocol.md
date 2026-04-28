<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Phase A4 Execution Protocol

> **This protocol is NON-NEGOTIABLE.** After I-7 confirmation, you MUST follow EXACTLY these steps based on the partition strategy. DO NOT improvise, skip steps, or run sequentially when the plan says swarm.

## Path A: Sequential Execution (worker_count == 1)

Run a single `multi_turn_test_runner.py` process. No team needed.

```bash
set -a; source ~/.sfagent/{org_alias}/{eca_name}/credentials.env; set +a
python3 {SKILL_PATH}/hooks/scripts/multi_turn_test_runner.py \
  --scenarios {scenario_file} \
  --agent-id {agent_id} \
  --var '$Context.RoutableId={routable_id}' \
  --var '$Context.CaseId={case_id}' \
  --output {working_dir}/results.json \
  --report-file {working_dir}/report.ansi \
  --verbose
```

## Path B: Swarm Execution (worker_count == 2) — MANDATORY CHECKLIST

**YOU MUST EXECUTE EVERY STEP BELOW IN ORDER. DO NOT SKIP ANY STEP.**

☐ **Step 1: Split scenarios into 2 partitions**
  Group the generated category YAML files into 2 balanced buckets by total scenario count.
  Write `{working_dir}/scenarios-part1.yaml` and `{working_dir}/scenarios-part2.yaml`.
  Each partition file must be valid YAML with a `scenarios:` key containing its subset.

☐ **Step 2: Create team**
  ```
  TeamCreate(team_name="sf-test-{agent_name}")
  ```

☐ **Step 3: Create 2 tasks** (one per partition)
  ```
  TaskCreate(subject="Run partition 1", description="Execute scenarios-part1.yaml")
  TaskCreate(subject="Run partition 2", description="Execute scenarios-part2.yaml")
  ```

☐ **Step 4: Spawn 2 workers IN PARALLEL** (single message with 2 Task tool calls)
  Use the **Worker Agent Prompt Template** (see [swarm-execution.md](swarm-execution.md)). CRITICAL: Both Task calls MUST be in the SAME message.
  ```
  Task(subagent_type="general-purpose", team_name="sf-test-{agent_name}", name="worker-1", prompt=WORKER_PROMPT_1)
  Task(subagent_type="general-purpose", team_name="sf-test-{agent_name}", name="worker-2", prompt=WORKER_PROMPT_2)
  ```

☐ **Step 5: Wait for both workers to report** (they SendMessage when done)
  Do NOT proceed until both workers have sent their results via SendMessage.

☐ **Step 6: Aggregate results**
  ```bash
  python3 {SKILL_PATH}/hooks/scripts/rich_test_report.py \
    --results {working_dir}/worker-1-results.json {working_dir}/worker-2-results.json
  ```

☐ **Step 7: Present unified report** to the user

☐ **Step 8: Offer fix loop** if any failures detected

☐ **Step 9: Shutdown workers**
  ```
  SendMessage(type="shutdown_request", recipient="worker-1")
  SendMessage(type="shutdown_request", recipient="worker-2")
  ```

☐ **Step 10: Clean up**
  ```
  TeamDelete
  ```
