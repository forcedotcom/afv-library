<!-- Parent: sf-ai-agentforce-testing/SKILL.md -->

# Swarm Execution Rules (Native Claude Code Teams)

When `worker_count > 1` in the test plan, use Claude Code's native team orchestration for parallel test execution. When `worker_count == 1`, run sequentially without creating a team.

## Team Lead Rules (Claude Code)

```
RULE: Create team via TeamCreate("sf-test-{agent_name}")
RULE: Create one TaskCreate per partition (category or count split)
RULE: Spawn one Task(subagent_type="general-purpose") per worker
RULE: Each worker gets credentials as env vars in its prompt (NEVER in files)
RULE: Wait for all workers to report via SendMessage
RULE: After all workers complete, run rich_test_report.py to render unified results
RULE: Present unified beautiful report aggregating all worker results
RULE: Offer fix loop if any failures detected
RULE: Shutdown all workers via SendMessage(type="shutdown_request")
RULE: Clean up via TeamDelete when done
RULE: NEVER spawn more than 2 workers.
RULE: When categories > 2, group into 2 balanced buckets.
RULE: Queue remaining work to existing workers after they complete first batch.
```

## Worker Agent Prompt Template

Each worker receives this prompt (team lead fills in the variables):

```
You are a multi-turn test worker for Agentforce agent testing.

YOUR TASK:
1. Claim your task via TaskUpdate(status="in_progress", owner=your_name)

2. Load credentials and run the test:
   set -a; source ~/.sfagent/{org_alias}/{eca_name}/credentials.env; set +a

   python3 {skill_path}/hooks/scripts/multi_turn_test_runner.py \
     --scenarios {scenario_file} \
     --agent-id {agent_id} \
     --var '$Context.RoutableId={routable_id}' \
     --var '$Context.CaseId={case_id}' \
     --output {working_dir}/worker-{N}-results.json \
     --report-file {working_dir}/worker-{N}-report.ansi \
     --worker-id {N} --verbose

3. IMPORTANT — RENDER RICH TUI REPORT IN YOUR PANE:
   After the test runner completes, render the results visually so they appear
   in your conversation pane (the tmux panel the user can see):

   python3 -c "
   import sys, json
   sys.path.insert(0, '{skill_path}/hooks/scripts')
   from multi_turn_test_runner import format_results_rich
   with open('{working_dir}/worker-{N}-results.json') as f:
       results = json.load(f)
   print(format_results_rich(results, worker_id={N}, scenario_file='{scenario_file}'))
   "

   Then copy-paste that output into your conversation as a text message so it
   renders in your Claude Code pane for the user to see.

4. Analyze: which scenarios passed, which failed, and WHY

5. SendMessage to team lead with:
   - Pass/fail summary (counts + percentages)
   - For each failure: scenario name, turn number, what went wrong, suggested fix
   - Total execution time
   - Any patterns noticed (e.g., "all context_preservation tests failed — may be a systemic issue")

6. Mark your task as completed via TaskUpdate

IMPORTANT:
- If a test fails with an auth error (exit code 2), report it immediately — do NOT retry
- If a test fails with scenario failures (exit code 1), analyze and report all failures
- You CAN communicate with other workers if you discover related issues
- The --report-file flag writes a persistent ANSI report file viewable with `cat` or `bat`
```

## Partition Strategies

| Strategy | How It Works | Best For |
|----------|-------------|----------|
| `by_category` | One worker per test pattern (topic_routing, context, etc.) | Most runs — natural isolation |
| `by_count` | Split N scenarios evenly across W workers | Large scenario counts |
| `sequential` | Single process, no team | Quick runs, debugging |

## Team Lead Aggregation

After all workers report, the team lead:

1. **Aggregates** all worker result JSON files via `rich_test_report.py`:
   ```bash
   python3 {SKILL_PATH}/hooks/scripts/rich_test_report.py \
     --results /tmp/sf-test-{session}/worker-*-results.json
   ```
2. **Deduplicates** any shared failure patterns across workers
3. **Presents** the unified Rich report (colored Panels, Tables, Tree) to the user
4. **Calculates** aggregate scoring across the 7 categories
5. **Offers** fix loop: if failures exist, ask user whether to auto-fix via `sf-ai-agentscript`
6. **Shuts down** all workers and deletes the team

---

## CLI Swarm Execution (Agent Teams for CLI Tests)

When multiple CLI test suites need to be deployed and run simultaneously, use agent teams for parallel execution.

**When to use swarm:**
- 3+ test suites to deploy and run
- User selects "Swarm: parallel deploy+run" in Step 4
- Each suite is independent (no shared state)

**Swarm Protocol:**

☐ **Step 1: Create team**
```
TeamCreate(team_name="cli-test-{agent_name}")
```

☐ **Step 2: Create tasks** (one per suite)
```
TaskCreate(subject="Deploy+Run {suite_name}", description="sf agent test create + run for {suite}")
```

☐ **Step 3: Spawn workers** (max 3, batch suites if > 3)
Workers are `fde-qa-engineer` agents. Each worker:
1. Deploys its assigned suite(s) via `sf agent test create --spec`
2. Runs via `sf agent test run --api-name`
3. Polls results via `sf agent test results --job-id`
4. SendMessage to leader with results summary

```
Task(subagent_type="fde-qa-engineer", team_name="cli-test-{agent_name}",
     name="test-worker-1", prompt=CLI_WORKER_PROMPT)
Task(subagent_type="fde-qa-engineer", team_name="cli-test-{agent_name}",
     name="test-worker-2", prompt=CLI_WORKER_PROMPT)
```

☐ **Step 4: Collect + aggregate results**
Leader waits for all workers to report back via SendMessage.

☐ **Step 5: Present unified report**
Aggregate all suite results into the standard results format.

☐ **Step 6: Shutdown + TeamDelete**
Send shutdown_request to all workers, then TeamDelete to clean up.

**Version check:** Teams require Claude Code with TeamCreate support.
If TeamCreate is unavailable, fall back to sequential execution.
