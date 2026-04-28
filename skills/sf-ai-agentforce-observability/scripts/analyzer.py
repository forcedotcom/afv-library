"""
Polars-based analysis helpers for STDM data.

Uses Polars lazy evaluation for memory-efficient analysis of
large datasets (100M+ rows).

Features:
- Session summary statistics
- Step distribution analysis
- Topic routing analysis
- Message timeline reconstruction
- All operations use lazy evaluation where possible

Usage:
    analyzer = STDMAnalyzer(Path("./stdm_data"))

    # Get session summary
    summary = analyzer.session_summary()
    print(summary)

    # Debug specific session
    timeline = analyzer.message_timeline("session_id")
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import polars as pl
from rich.console import Console
from rich.table import Table


console = Console()


@dataclass
class STDMAnalyzer:
    """
    Polars-based analysis helpers for session tracing data.

    Uses lazy evaluation for memory efficiency, enabling analysis
    of datasets with millions of records.

    Attributes:
        data_dir: Directory containing extracted Parquet files

    Example:
        >>> analyzer = STDMAnalyzer(Path("./stdm_data"))
        >>> summary = analyzer.session_summary()
        >>> print(summary)
    """

    data_dir: Path

    def __post_init__(self):
        """Validate data directory exists."""
        self.data_dir = Path(self.data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

    def _get_parquet_path(self, entity: str) -> Path:
        """Get Parquet file path for entity."""
        # Try direct file first
        direct_path = self.data_dir / entity / "data.parquet"
        if direct_path.exists():
            return direct_path

        # Try partitioned directory
        partition_path = self.data_dir / entity
        if partition_path.exists() and partition_path.is_dir():
            # Check for parquet files
            parquet_files = list(partition_path.glob("**/*.parquet"))
            if parquet_files:
                return partition_path

        raise FileNotFoundError(f"No data found for {entity} in {self.data_dir}")

    def load_sessions(self) -> pl.LazyFrame:
        """
        Load sessions as lazy frame.

        Returns:
            Polars LazyFrame for sessions
        """
        path = self._get_parquet_path("sessions")
        return pl.scan_parquet(path)

    def load_interactions(self) -> pl.LazyFrame:
        """
        Load interactions as lazy frame.

        Returns:
            Polars LazyFrame for interactions
        """
        path = self._get_parquet_path("interactions")
        return pl.scan_parquet(path)

    def load_steps(self) -> pl.LazyFrame:
        """
        Load steps as lazy frame.

        Returns:
            Polars LazyFrame for steps
        """
        path = self._get_parquet_path("steps")
        return pl.scan_parquet(path)

    def load_messages(self) -> pl.LazyFrame:
        """
        Load messages as lazy frame.

        Returns:
            Polars LazyFrame for messages
        """
        path = self._get_parquet_path("messages")
        return pl.scan_parquet(path)

    def session_summary(self) -> pl.DataFrame:
        """
        Generate session summary statistics.

        Returns DataFrame with:
        - Total sessions by agent
        - Average turns per session
        - Average duration
        - End type distribution

        Returns:
            Polars DataFrame with summary statistics
        """
        sessions = self.load_sessions()
        interactions = self.load_interactions()

        # Calculate turns per session
        turns_per_session = (
            interactions
            .filter(pl.col("ssot__AiAgentInteractionType__c") == "TURN")
            .group_by("ssot__AiAgentSessionId__c")
            .agg(pl.count().alias("turn_count"))
        )

        # Join with sessions and aggregate by channel type (since agent name is in Moments)
        # Note: Agent API name is in AIAgentMoment, not AIAgentSession
        summary = (
            sessions
            .join(
                turns_per_session,
                left_on="ssot__Id__c",
                right_on="ssot__AiAgentSessionId__c",
                how="left"
            )
            .group_by("ssot__AiAgentChannelType__c")
            .agg([
                pl.count().alias("session_count"),
                pl.col("turn_count").mean().alias("avg_turns"),
                pl.col("ssot__AiAgentSessionEndType__c").filter(
                    pl.col("ssot__AiAgentSessionEndType__c") == "Completed"
                ).count().alias("completed_count"),
                pl.col("ssot__AiAgentSessionEndType__c").filter(
                    pl.col("ssot__AiAgentSessionEndType__c") == "Escalated"
                ).count().alias("escalated_count"),
                pl.col("ssot__AiAgentSessionEndType__c").filter(
                    pl.col("ssot__AiAgentSessionEndType__c") == "Abandoned"
                ).count().alias("abandoned_count"),
            ])
            .with_columns([
                (pl.col("completed_count") / pl.col("session_count") * 100).round(1).alias("completion_rate"),
            ])
            .sort("session_count", descending=True)
        )

        return summary.collect()

    def step_distribution(self, agent_name: Optional[str] = None) -> pl.DataFrame:
        """
        Analyze step type distribution.

        Returns:
        - LLM_STEP vs ACTION_STEP ratio
        - Most common action names
        - Average steps per turn

        Args:
            agent_name: Optional agent API name to filter

        Returns:
            Polars DataFrame with step distribution
        """
        steps = self.load_steps()
        interactions = self.load_interactions()

        if agent_name:
            # Agent name is in AIAgentMoment, not AIAgentSession
            # To filter by agent, we'd need to load moments and join
            # For now, log a warning and skip the filter
            console.print(f"[yellow]Warning: Agent filter '{agent_name}' ignored - agent name is in AIAgentMoment[/yellow]")

        # Step type distribution
        step_types = (
            steps
            .group_by("ssot__AiAgentInteractionStepType__c")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )

        return step_types.collect()

    def action_distribution(self, agent_name: Optional[str] = None) -> pl.DataFrame:
        """
        Analyze action name distribution for ACTION_STEP types.

        Args:
            agent_name: Optional agent API name to filter

        Returns:
            Polars DataFrame with action counts
        """
        steps = self.load_steps()

        # Filter to action steps only
        action_steps = steps.filter(
            pl.col("ssot__AiAgentInteractionStepType__c") == "ACTION_STEP"
        )

        if agent_name:
            # Agent name is in AIAgentMoment, not AIAgentSession
            console.print(f"[yellow]Warning: Agent filter '{agent_name}' ignored - agent name is in AIAgentMoment[/yellow]")

        # Group by action name
        actions = (
            action_steps
            .group_by("ssot__Name__c")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )

        return actions.collect()

    def topic_analysis(self) -> pl.DataFrame:
        """
        Analyze topic routing patterns.

        Returns:
        - Topic frequency
        - Sessions per topic
        - Average turns per topic

        Returns:
            Polars DataFrame with topic analysis
        """
        interactions = self.load_interactions()

        # Filter to TURN interactions (not SESSION_END)
        turns = interactions.filter(
            pl.col("ssot__AiAgentInteractionType__c") == "TURN"
        )

        # Topic frequency
        topics = (
            turns
            .group_by("ssot__TopicApiName__c")
            .agg([
                pl.count().alias("turn_count"),
                pl.col("ssot__AiAgentSessionId__c").n_unique().alias("session_count"),
            ])
            .with_columns([
                (pl.col("turn_count") / pl.col("session_count")).round(2).alias("avg_turns_per_session"),
            ])
            .sort("turn_count", descending=True)
        )

        return topics.collect()

    def message_timeline(self, session_id: str) -> pl.DataFrame:
        """
        Reconstruct message timeline for a specific session.

        Useful for debugging agent behavior by seeing the full
        conversation flow.

        Note: This method uses UNION (concat) instead of JOINs to avoid
        cartesian product explosion. A naive JOIN approach would produce
        4st² records (where t=turns, s=steps). This UNION approach produces
        only (moments + steps) records.

        Args:
            session_id: Session ID to analyze

        Returns:
            Polars DataFrame with chronological messages
        """
        sessions = self.load_sessions()
        interactions = self.load_interactions()
        messages = self.load_messages()
        steps = self.load_steps()

        # Get session info
        session_info = (
            sessions
            .filter(pl.col("ssot__Id__c") == session_id)
            .collect()
        )

        if session_info.is_empty():
            raise ValueError(f"Session not found: {session_id}")

        # Get interactions for this session
        session_interactions = (
            interactions
            .filter(pl.col("ssot__AiAgentSessionId__c") == session_id)
            .select("ssot__Id__c")
        )

        # Get moments (AIAgentMoment links to sessions, not interactions)
        # Schema: AiAgentSessionId, RequestSummaryText, ResponseSummaryText, StartTimestamp
        session_moments = (
            messages
            .filter(pl.col("ssot__AiAgentSessionId__c") == session_id)
            .select([
                pl.col("ssot__StartTimestamp__c").alias("timestamp"),
                pl.lit("MOMENT").alias("event_type"),
                pl.col("ssot__RequestSummaryText__c").alias("request"),
                pl.col("ssot__ResponseSummaryText__c").alias("response"),
                pl.col("ssot__AiAgentApiName__c").alias("agent"),
            ])
        )

        # Get steps for this session's interactions
        session_steps = (
            steps
            .join(
                session_interactions,
                left_on="ssot__AiAgentInteractionId__c",
                right_on="ssot__Id__c",
                how="inner"
            )
            .select([
                pl.col("ssot__StartTimestamp__c").alias("timestamp"),
                pl.col("ssot__AiAgentInteractionStepType__c").alias("event_type"),
                pl.col("ssot__Name__c").alias("request"),
                pl.col("ssot__OutputValueText__c").alias("response"),
                pl.lit(None).cast(pl.Utf8).alias("agent"),
            ])
        )

        # Combine and sort by timestamp
        timeline = (
            pl.concat([session_moments, session_steps])
            .sort("timestamp")
        )

        return timeline.collect()

    def session_timeline_optimized(self, session_id: str) -> pl.DataFrame:
        """
        Reconstruct session timeline with turn structure preserved.

        This optimized method avoids the cartesian product problem that
        occurs when naively joining Session → Interaction → Message → Step.

        The naive JOIN approach produces 4st² records (where t=turns, s=steps).
        Example: 2 turns × 5 steps = 80 records instead of 15.

        This method uses UNION ALL (via concat) to combine:
        1. Messages (input/output per turn)
        2. Steps (reasoning chain per output)

        Result: (2+s)t+1 records instead of 4st² records.

        Args:
            session_id: Session ID to analyze

        Returns:
            Polars DataFrame with structured timeline including:
            - turn_number: Which turn this event belongs to
            - event_type: MOMENT, LLM_STEP, ACTION_STEP
            - timestamp: When the event occurred
            - content: The request/response/action content
        """
        interactions = self.load_interactions()
        messages = self.load_messages()
        steps = self.load_steps()

        # Get turns for this session (ordered by timestamp)
        session_turns = (
            interactions
            .filter(
                (pl.col("ssot__AiAgentSessionId__c") == session_id) &
                (pl.col("ssot__AiAgentInteractionType__c") == "TURN")
            )
            .sort("ssot__StartTimestamp__c")
            .with_row_index("turn_number")
            .select([
                "ssot__Id__c",
                (pl.col("turn_number") + 1).alias("turn_number"),  # 1-indexed
            ])
            .collect()
        )

        if session_turns.is_empty():
            return pl.DataFrame({
                "turn_number": [],
                "event_order": [],
                "event_type": [],
                "timestamp": [],
                "content": [],
                "detail": [],
            })

        turn_ids = session_turns["ssot__Id__c"].to_list()
        turn_map = dict(zip(
            session_turns["ssot__Id__c"].to_list(),
            session_turns["turn_number"].to_list()
        ))

        # Get moments (user request + agent response summaries)
        # These are per-session, but we associate with turns by timestamp
        moments_df = (
            messages
            .filter(pl.col("ssot__AiAgentSessionId__c") == session_id)
            .select([
                pl.col("ssot__StartTimestamp__c").alias("timestamp"),
                pl.col("ssot__RequestSummaryText__c").alias("request"),
                pl.col("ssot__ResponseSummaryText__c").alias("response"),
                pl.col("ssot__AiAgentApiName__c").alias("agent"),
            ])
            .collect()
        )

        # Get steps for this session's turns
        steps_df = (
            steps
            .filter(pl.col("ssot__AiAgentInteractionId__c").is_in(turn_ids))
            .select([
                pl.col("ssot__AiAgentInteractionId__c").alias("interaction_id"),
                pl.col("ssot__StartTimestamp__c").alias("timestamp"),
                pl.col("ssot__AiAgentInteractionStepType__c").alias("step_type"),
                pl.col("ssot__Name__c").alias("name"),
                pl.col("ssot__OutputValueText__c").alias("output"),
            ])
            .collect()
        )

        # Build unified timeline
        timeline_rows = []
        event_order = 0

        # Process moments (request/response pairs)
        for row in moments_df.iter_rows(named=True):
            event_order += 1
            # Request
            if row["request"]:
                timeline_rows.append({
                    "turn_number": 0,  # Moments span turns
                    "event_order": event_order,
                    "event_type": "REQUEST",
                    "timestamp": row["timestamp"],
                    "content": row["request"],
                    "detail": row.get("agent", ""),
                })
            event_order += 1
            # Response
            if row["response"]:
                timeline_rows.append({
                    "turn_number": 0,
                    "event_order": event_order,
                    "event_type": "RESPONSE",
                    "timestamp": row["timestamp"],
                    "content": row["response"],
                    "detail": row.get("agent", ""),
                })

        # Process steps (reasoning chain)
        for row in steps_df.iter_rows(named=True):
            event_order += 1
            turn_num = turn_map.get(row["interaction_id"], 0)
            timeline_rows.append({
                "turn_number": turn_num,
                "event_order": event_order,
                "event_type": row["step_type"] or "STEP",
                "timestamp": row["timestamp"],
                "content": row["name"] or "",
                "detail": (row["output"] or "")[:200],  # Truncate for display
            })

        if not timeline_rows:
            return pl.DataFrame({
                "turn_number": [],
                "event_order": [],
                "event_type": [],
                "timestamp": [],
                "content": [],
                "detail": [],
            })

        # Create DataFrame and sort by timestamp
        result = pl.DataFrame(timeline_rows).sort("timestamp")

        return result

    def end_type_distribution(self) -> pl.DataFrame:
        """
        Analyze session end type distribution.

        Returns:
            Polars DataFrame with end type counts and percentages
        """
        sessions = self.load_sessions()

        distribution = (
            sessions
            .group_by("ssot__AiAgentSessionEndType__c")
            .agg(pl.count().alias("count"))
            .with_columns([
                (pl.col("count") / pl.col("count").sum() * 100).round(1).alias("percentage"),
            ])
            .sort("count", descending=True)
        )

        return distribution.collect()

    def sessions_by_date(self) -> pl.DataFrame:
        """
        Get session counts by date.

        Returns:
            Polars DataFrame with daily session counts
        """
        sessions = self.load_sessions()

        daily = (
            sessions
            .with_columns([
                pl.col("ssot__StartTimestamp__c").str.slice(0, 10).alias("date"),
            ])
            .group_by("date")
            .agg(pl.count().alias("session_count"))
            .sort("date")
        )

        return daily.collect()

    def find_failed_sessions(self) -> pl.DataFrame:
        """
        Find sessions that ended with failures or escalations.

        Returns:
            Polars DataFrame with failed/escalated sessions
        """
        sessions = self.load_sessions()

        failed = (
            sessions
            .filter(
                pl.col("ssot__AiAgentSessionEndType__c").is_in(["Escalated", "Abandoned", "Failed"])
            )
            .sort("ssot__StartTimestamp__c", descending=True)
        )

        return failed.collect()

    def print_summary(self):
        """Print comprehensive summary to console."""
        console.print("\n[bold cyan]📊 SESSION TRACING SUMMARY[/bold cyan]")
        console.print("═" * 60)

        # Session summary (grouped by channel since agent name is in Moments)
        try:
            summary = self.session_summary()
            console.print("\n[bold]Sessions by Channel[/bold]")

            table = Table()
            table.add_column("Channel", style="cyan")
            table.add_column("Sessions", justify="right")
            table.add_column("Avg Turns", justify="right")
            table.add_column("Completion %", justify="right")

            for row in summary.iter_rows(named=True):
                table.add_row(
                    str(row.get("ssot__AiAgentChannelType__c", "Unknown")),
                    str(row.get("session_count", 0)),
                    f"{row.get('avg_turns', 0) or 0:.1f}",
                    f"{row.get('completion_rate', 0) or 0:.1f}%",
                )

            console.print(table)
        except Exception as e:
            console.print(f"[yellow]Could not load session summary: {e}[/yellow]")

        # End type distribution
        try:
            end_types = self.end_type_distribution()
            console.print("\n[bold]End Type Distribution[/bold]")

            for row in end_types.iter_rows(named=True):
                end_type = row.get("ssot__AiAgentSessionEndType__c", "Unknown")
                count = row.get("count", 0)
                pct = row.get("percentage", 0)

                icon = "✅" if end_type == "Completed" else "🔄" if end_type == "Escalated" else "❌"
                console.print(f"  {icon} {end_type}: {count} ({pct}%)")
        except Exception as e:
            console.print(f"[yellow]Could not load end type distribution: {e}[/yellow]")

        # Topic analysis
        try:
            topics = self.topic_analysis()
            console.print("\n[bold]Top Topics[/bold]")

            for i, row in enumerate(topics.head(5).iter_rows(named=True)):
                topic = row.get("ssot__TopicApiName__c", "Unknown")
                count = row.get("turn_count", 0)
                console.print(f"  {i+1}. {topic}: {count} turns")
        except Exception as e:
            console.print(f"[yellow]Could not load topic analysis: {e}[/yellow]")

    def find_hallucinations(self, limit: int = 100) -> pl.DataFrame:
        """
        Find responses flagged as potentially ungrounded (hallucinations).

        Searches AIAgentInteractionStep for ReactValidationPrompt steps
        where the output contains 'UNGROUNDED', indicating the agent's
        response was not supported by grounded context.

        Args:
            limit: Maximum number of results to return

        Returns:
            Polars DataFrame with columns:
            - session_id: The session where hallucination occurred
            - interaction_id: The specific turn
            - step_id: The validation step ID
            - step_name: Step name (should be ReactValidationPrompt)
            - output_text: The validation output showing UNGROUNDED
            - timestamp: When the step occurred
        """
        steps = self.load_steps()
        interactions = self.load_interactions()

        # Find ReactValidationPrompt steps with UNGROUNDED in output
        hallucinations = (
            steps
            .filter(
                (pl.col("ssot__Name__c").str.contains("ReactValidationPrompt", literal=True)) &
                (pl.col("ssot__OutputValueText__c").str.contains("UNGROUNDED", literal=True))
            )
            .join(
                interactions.select(["ssot__Id__c", "ssot__AiAgentSessionId__c"]),
                left_on="ssot__AiAgentInteractionId__c",
                right_on="ssot__Id__c",
                how="left"
            )
            .select([
                pl.col("ssot__AiAgentSessionId__c").alias("session_id"),
                pl.col("ssot__AiAgentInteractionId__c").alias("interaction_id"),
                pl.col("ssot__Id__c").alias("step_id"),
                pl.col("ssot__Name__c").alias("step_name"),
                pl.col("ssot__OutputValueText__c").alias("output_text"),
                pl.col("ssot__StartTimestamp__c").alias("timestamp"),
            ])
            .sort("timestamp", descending=True)
            .head(limit)
        )

        return hallucinations.collect()

    def hallucination_summary(self) -> pl.DataFrame:
        """
        Get summary statistics for hallucination occurrences.

        Returns:
            Polars DataFrame with:
            - total_hallucinations: Count of UNGROUNDED responses
            - affected_sessions: Number of unique sessions with hallucinations
            - percentage_of_sessions: % of all sessions with hallucinations
        """
        steps = self.load_steps()
        sessions = self.load_sessions()
        interactions = self.load_interactions()

        # Count hallucinations
        hallucination_steps = steps.filter(
            (pl.col("ssot__Name__c").str.contains("ReactValidationPrompt", literal=True)) &
            (pl.col("ssot__OutputValueText__c").str.contains("UNGROUNDED", literal=True))
        )

        # Join to get session IDs
        hallucination_sessions = (
            hallucination_steps
            .join(
                interactions.select(["ssot__Id__c", "ssot__AiAgentSessionId__c"]),
                left_on="ssot__AiAgentInteractionId__c",
                right_on="ssot__Id__c",
                how="left"
            )
            .select("ssot__AiAgentSessionId__c")
            .unique()
        )

        total_hallucinations = hallucination_steps.select(pl.count()).collect().item()
        affected_sessions = hallucination_sessions.select(pl.count()).collect().item()
        total_sessions = sessions.select(pl.count()).collect().item()

        percentage = (affected_sessions / total_sessions * 100) if total_sessions > 0 else 0

        return pl.DataFrame({
            "total_hallucinations": [total_hallucinations],
            "affected_sessions": [affected_sessions],
            "total_sessions": [total_sessions],
            "percentage_of_sessions": [round(percentage, 2)],
        })

    def print_session_debug(self, session_id: str):
        """Print detailed debug view for a session."""
        console.print(f"\n[bold cyan]🔍 SESSION DEBUG: {session_id}[/bold cyan]")
        console.print("═" * 60)

        try:
            # Get session info
            sessions = self.load_sessions()
            session = (
                sessions
                .filter(pl.col("ssot__Id__c") == session_id)
                .collect()
            )

            if session.is_empty():
                console.print(f"[red]Session not found: {session_id}[/red]")
                return

            row = session.row(0, named=True)
            console.print(f"\nChannel: [cyan]{row.get('ssot__AiAgentChannelType__c', 'Unknown')}[/cyan]")
            console.print(f"Started: {row.get('ssot__StartTimestamp__c', 'N/A')}")
            console.print(f"Ended: {row.get('ssot__EndTimestamp__c', 'N/A')}")
            console.print(f"End Type: {row.get('ssot__AiAgentSessionEndType__c', 'N/A')}")

            # Get timeline
            timeline = self.message_timeline(session_id)

            console.print("\n[bold]Timeline[/bold]")
            console.print("─" * 60)

            for event in timeline.iter_rows(named=True):
                timestamp = event.get("timestamp", "")
                event_type = event.get("event_type", "")
                request = event.get("request", "")
                response = event.get("response", "")

                time_str = timestamp[:19] if timestamp else "        "

                if event_type == "MOMENT":
                    # Show request and response from moment
                    if request:
                        content = request[:77] + "..." if len(request or "") > 80 else request
                        console.print(f"{time_str} │ [green][REQUEST][/green] {content}")
                    if response:
                        content = response[:77] + "..." if len(response or "") > 80 else response
                        console.print(f"           │ [blue][RESPONSE][/blue] {content}")
                else:
                    # Show step (LLM_STEP or ACTION_STEP)
                    icon = "⚡" if event_type == "ACTION_STEP" else "🤖"
                    content = request[:77] + "..." if len(request or "") > 80 else request or ""
                    console.print(f"{time_str} │ [yellow][{event_type}][/yellow] {content}")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    # =========================================================================
    # Quality Analysis Methods
    # =========================================================================

    def load_generations(self) -> pl.LazyFrame:
        """
        Load generations as lazy frame.

        Returns:
            Polars LazyFrame for GenAIGeneration records
        """
        path = self._get_parquet_path("generations")
        return pl.scan_parquet(path)

    def load_content_quality(self) -> pl.LazyFrame:
        """
        Load content quality as lazy frame.

        Returns:
            Polars LazyFrame for GenAIContentQuality records
        """
        path = self._get_parquet_path("content_quality")
        return pl.scan_parquet(path)

    def load_content_categories(self) -> pl.LazyFrame:
        """
        Load content categories as lazy frame.

        Returns:
            Polars LazyFrame for GenAIContentCategory records
        """
        path = self._get_parquet_path("content_categories")
        return pl.scan_parquet(path)

    def find_toxic_responses(self, limit: int = 100) -> pl.DataFrame:
        """
        Find responses flagged for toxicity.

        Searches GenAIContentQuality for records where:
        - isToxicityDetected = 'true'

        Also checks GenAIContentCategory for toxicity detectors with high confidence.

        Joins back to Steps and Interactions to get session context.

        Args:
            limit: Maximum number of results to return

        Returns:
            Polars DataFrame with toxic response details
        """
        try:
            quality = self.load_content_quality()
            categories = self.load_content_categories()
            steps = self.load_steps()
            interactions = self.load_interactions()
        except FileNotFoundError:
            return pl.DataFrame({
                "generation_id": [],
                "session_id": [],
                "interaction_id": [],
                "is_toxic": [],
                "confidence": [],
                "timestamp": [],
            })

        # Find toxic content quality records
        toxic_records = (
            quality
            .filter(pl.col("isToxicityDetected__c") == "true")
            .select([
                pl.col("parent__c").alias("generation_id"),
                pl.col("isToxicityDetected__c").alias("is_toxic"),
                pl.lit(None).cast(pl.Float64).alias("confidence"),
                pl.col("timestamp__c").alias("quality_timestamp"),
            ])
        )

        # Also check categories for toxicity with high confidence
        # Note: value__c comes as string from API, cast to float for comparison
        toxic_categories = (
            categories
            .with_columns(pl.col("value__c").cast(pl.Float64, strict=False).alias("value_float"))
            .filter(
                (pl.col("detectorType__c") == "Toxicity") &
                (pl.col("value_float") >= 0.5)
            )
            .select([
                pl.col("parent__c").alias("generation_id"),
                pl.lit("true").alias("is_toxic"),
                pl.col("value_float").alias("confidence"),
                pl.col("timestamp__c").alias("quality_timestamp"),
            ])
        )

        # Combine both sources
        all_toxic = pl.concat([toxic_records, toxic_categories]).unique()

        # Join to steps to get interaction context
        result = (
            all_toxic
            .join(
                steps.select([
                    pl.col("ssot__GenerationId__c"),
                    pl.col("ssot__AiAgentInteractionId__c"),
                    pl.col("ssot__StartTimestamp__c").alias("step_timestamp"),
                ]),
                left_on="generation_id",
                right_on="ssot__GenerationId__c",
                how="left"
            )
            .join(
                interactions.select([
                    pl.col("ssot__Id__c"),
                    pl.col("ssot__AiAgentSessionId__c").alias("session_id"),
                ]),
                left_on="ssot__AiAgentInteractionId__c",
                right_on="ssot__Id__c",
                how="left"
            )
            .select([
                "generation_id",
                "session_id",
                pl.col("ssot__AiAgentInteractionId__c").alias("interaction_id"),
                "is_toxic",
                "confidence",
                pl.coalesce(["quality_timestamp", "step_timestamp"]).alias("timestamp"),
            ])
            .sort("timestamp", descending=True)
            .head(limit)
        )

        return result.collect()

    def find_low_instruction_adherence(self, limit: int = 100) -> pl.DataFrame:
        """
        Find responses with low instruction adherence.

        Searches GenAIContentCategory for records where:
        - detectorType = 'InstructionAdherence'
        - category = 'Low'

        Args:
            limit: Maximum number of results to return

        Returns:
            Polars DataFrame with low adherence details
        """
        try:
            categories = self.load_content_categories()
            steps = self.load_steps()
            interactions = self.load_interactions()
        except FileNotFoundError:
            return pl.DataFrame({
                "generation_id": [],
                "session_id": [],
                "interaction_id": [],
                "category": [],
                "confidence": [],
                "timestamp": [],
            })

        # Note: value__c comes as string from API, cast to float
        low_adherence = (
            categories
            .with_columns(pl.col("value__c").cast(pl.Float64, strict=False).alias("value_float"))
            .filter(
                (pl.col("detectorType__c") == "InstructionAdherence") &
                (pl.col("category__c") == "Low")
            )
            .select([
                pl.col("parent__c").alias("generation_id"),
                pl.col("category__c").alias("category"),
                pl.col("value_float").alias("confidence"),
                pl.col("timestamp__c").alias("cat_timestamp"),
            ])
        )

        # Join to get context
        result = (
            low_adherence
            .join(
                steps.select([
                    pl.col("ssot__GenerationId__c"),
                    pl.col("ssot__AiAgentInteractionId__c"),
                    pl.col("ssot__StartTimestamp__c").alias("step_timestamp"),
                ]),
                left_on="generation_id",
                right_on="ssot__GenerationId__c",
                how="left"
            )
            .join(
                interactions.select([
                    pl.col("ssot__Id__c"),
                    pl.col("ssot__AiAgentSessionId__c").alias("session_id"),
                ]),
                left_on="ssot__AiAgentInteractionId__c",
                right_on="ssot__Id__c",
                how="left"
            )
            .select([
                "generation_id",
                "session_id",
                pl.col("ssot__AiAgentInteractionId__c").alias("interaction_id"),
                "category",
                "confidence",
                pl.coalesce(["cat_timestamp", "step_timestamp"]).alias("timestamp"),
            ])
            .sort("timestamp", descending=True)
            .head(limit)
        )

        return result.collect()

    def find_unresolved_tasks(self, limit: int = 100) -> pl.DataFrame:
        """
        Find sessions where tasks weren't fully resolved.

        Searches GenAIContentCategory for records where:
        - detectorType = 'TaskResolution'
        - category != 'FULLY_RESOLVED'

        Args:
            limit: Maximum number of results to return

        Returns:
            Polars DataFrame with unresolved task details
        """
        try:
            categories = self.load_content_categories()
            steps = self.load_steps()
            interactions = self.load_interactions()
        except FileNotFoundError:
            return pl.DataFrame({
                "generation_id": [],
                "session_id": [],
                "interaction_id": [],
                "resolution_status": [],
                "confidence": [],
                "timestamp": [],
            })

        # Note: value__c comes as string from API, cast to float
        unresolved = (
            categories
            .with_columns(pl.col("value__c").cast(pl.Float64, strict=False).alias("value_float"))
            .filter(
                (pl.col("detectorType__c") == "TaskResolution") &
                (pl.col("category__c") != "FULLY_RESOLVED")
            )
            .select([
                pl.col("parent__c").alias("generation_id"),
                pl.col("category__c").alias("resolution_status"),
                pl.col("value_float").alias("confidence"),
                pl.col("timestamp__c").alias("cat_timestamp"),
            ])
        )

        # Join to get context
        result = (
            unresolved
            .join(
                steps.select([
                    pl.col("ssot__GenerationId__c"),
                    pl.col("ssot__AiAgentInteractionId__c"),
                    pl.col("ssot__StartTimestamp__c").alias("step_timestamp"),
                ]),
                left_on="generation_id",
                right_on="ssot__GenerationId__c",
                how="left"
            )
            .join(
                interactions.select([
                    pl.col("ssot__Id__c"),
                    pl.col("ssot__AiAgentSessionId__c").alias("session_id"),
                ]),
                left_on="ssot__AiAgentInteractionId__c",
                right_on="ssot__Id__c",
                how="left"
            )
            .select([
                "generation_id",
                "session_id",
                pl.col("ssot__AiAgentInteractionId__c").alias("interaction_id"),
                "resolution_status",
                "confidence",
                pl.coalesce(["cat_timestamp", "step_timestamp"]).alias("timestamp"),
            ])
            .sort("timestamp", descending=True)
            .head(limit)
        )

        return result.collect()

    def quality_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive quality report.

        Returns a dictionary with quality metrics:
        - hallucinations: Count and percentage
        - toxicity: Count from quality DMOs
        - instruction_adherence: Low adherence count
        - task_resolution: Unresolved task count

        Returns:
            Dictionary with quality metrics
        """
        report = {
            "hallucinations": {},
            "toxicity": {},
            "instruction_adherence": {},
            "task_resolution": {},
        }

        # Hallucinations (always available from steps)
        try:
            hall_summary = self.hallucination_summary()
            row = hall_summary.row(0, named=True)
            report["hallucinations"] = {
                "count": row["total_hallucinations"],
                "affected_sessions": row["affected_sessions"],
                "percentage": row["percentage_of_sessions"],
            }
        except Exception:
            report["hallucinations"] = {"error": "Could not analyze hallucinations"}

        # Quality DMO metrics (require extract-quality)
        try:
            toxic = self.find_toxic_responses(limit=10000)
            report["toxicity"] = {
                "count": len(toxic),
                "affected_sessions": toxic["session_id"].n_unique() if not toxic.is_empty() else 0,
            }
        except Exception:
            report["toxicity"] = {"count": 0, "note": "Run extract-quality to get toxicity data"}

        try:
            low_adh = self.find_low_instruction_adherence(limit=10000)
            report["instruction_adherence"] = {
                "low_count": len(low_adh),
                "affected_sessions": low_adh["session_id"].n_unique() if not low_adh.is_empty() else 0,
            }
        except Exception:
            report["instruction_adherence"] = {"count": 0, "note": "Run extract-quality to get adherence data"}

        try:
            unresolved = self.find_unresolved_tasks(limit=10000)
            report["task_resolution"] = {
                "unresolved_count": len(unresolved),
                "affected_sessions": unresolved["session_id"].n_unique() if not unresolved.is_empty() else 0,
            }
        except Exception:
            report["task_resolution"] = {"count": 0, "note": "Run extract-quality to get resolution data"}

        return report

    def generate_moment_url(
        self,
        moment_id: str,
        session_id: str,
        agent_name: str,
        title: str,
        time_filter: int = 7,
    ) -> str:
        """
        Generate partial URL to Moment Detail page in Salesforce.

        Note: This generates a relative URL. Prepend with your org's
        instance URL to get the full URL.

        Args:
            moment_id: The moment record ID
            session_id: The session record ID
            agent_name: Agent API name
            title: Request summary text (will be URL encoded)
            time_filter: Time filter value (default: 7 days)

        Returns:
            Relative URL path to the moment detail page
        """
        from urllib.parse import quote

        encoded_title = quote(title or "", safe="")

        return (
            f"/lightning/cmp/runtime_analytics_evf_aie__record?"
            f"c__id={moment_id}&"
            f"c__type=2&"
            f"c__sessionId={session_id}&"
            f"c__timeFilter={time_filter}&"
            f"c__agentApiName={agent_name}&"
            f"c__title={encoded_title}"
        )

    def get_moment_urls(self, session_id: str) -> pl.DataFrame:
        """
        Generate moment detail URLs for a specific session.

        Args:
            session_id: Session ID to get moment URLs for

        Returns:
            Polars DataFrame with moment IDs and their URLs
        """
        messages = self.load_messages()

        moments = (
            messages
            .filter(pl.col("ssot__AiAgentSessionId__c") == session_id)
            .select([
                pl.col("ssot__Id__c").alias("moment_id"),
                pl.col("ssot__AiAgentSessionId__c").alias("session_id"),
                pl.col("ssot__AiAgentApiName__c").alias("agent_name"),
                pl.col("ssot__RequestSummaryText__c").alias("request_summary"),
                pl.col("ssot__StartTimestamp__c").alias("timestamp"),
            ])
            .collect()
        )

        # Generate URLs for each moment
        urls = []
        for row in moments.iter_rows(named=True):
            url = self.generate_moment_url(
                moment_id=row["moment_id"],
                session_id=row["session_id"],
                agent_name=row.get("agent_name") or "",
                title=row.get("request_summary") or "",
            )
            urls.append(url)

        return moments.with_columns(pl.Series("url", urls))

    def print_quality_report(self):
        """Print quality report to console."""
        console.print("\n[bold cyan]📊 QUALITY REPORT[/bold cyan]")
        console.print("═" * 60)

        report = self.quality_report()

        # Hallucinations
        hall = report.get("hallucinations", {})
        if "error" not in hall:
            console.print("\n[bold]🔮 Hallucinations (UNGROUNDED responses)[/bold]")
            console.print(f"  Total: [yellow]{hall.get('count', 0)}[/yellow]")
            console.print(f"  Affected sessions: {hall.get('affected_sessions', 0)}")
            console.print(f"  Session percentage: {hall.get('percentage', 0)}%")
        else:
            console.print(f"\n[yellow]{hall['error']}[/yellow]")

        # Toxicity
        tox = report.get("toxicity", {})
        console.print("\n[bold]☠️ Toxicity[/bold]")
        if "note" in tox:
            console.print(f"  [dim]{tox['note']}[/dim]")
        else:
            console.print(f"  Total: [red]{tox.get('count', 0)}[/red]")
            console.print(f"  Affected sessions: {tox.get('affected_sessions', 0)}")

        # Instruction Adherence
        adh = report.get("instruction_adherence", {})
        console.print("\n[bold]📋 Instruction Adherence[/bold]")
        if "note" in adh:
            console.print(f"  [dim]{adh['note']}[/dim]")
        else:
            console.print(f"  Low adherence: [yellow]{adh.get('low_count', 0)}[/yellow]")
            console.print(f"  Affected sessions: {adh.get('affected_sessions', 0)}")

        # Task Resolution
        res = report.get("task_resolution", {})
        console.print("\n[bold]✅ Task Resolution[/bold]")
        if "note" in res:
            console.print(f"  [dim]{res['note']}[/dim]")
        else:
            console.print(f"  Unresolved: [yellow]{res.get('unresolved_count', 0)}[/yellow]")
            console.print(f"  Affected sessions: {res.get('affected_sessions', 0)}")
