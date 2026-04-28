"""
Session Tracing Data Model (STDM) extraction orchestrator.

Extracts all 4 DMOs (Session, Interaction, Step, Message) with
relationship preservation and supports incremental extraction.

Features:
- Full extraction with date range filtering
- Agent name filtering
- Session tree extraction (all related records for specific sessions)
- Incremental extraction with watermark tracking
- Parquet output with date partitioning

Usage:
    auth = DataCloudAuth("myorg", "consumer_key")
    client = DataCloudClient(auth)
    extractor = STDMExtractor(client, Path("./data"))

    # Extract last 7 days
    result = extractor.extract_sessions(
        since=datetime.now() - timedelta(days=7)
    )
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .datacloud_client import DataCloudClient
from .models import (
    SCHEMAS,
    DMO_NAMES,
    build_select_clause,
    GENERATION_SCHEMA,
    CONTENT_QUALITY_SCHEMA,
    CONTENT_CATEGORY_SCHEMA,
)


console = Console()


@dataclass
class ExtractionResult:
    """Results from an extraction operation."""

    sessions_count: int = 0
    interactions_count: int = 0
    steps_count: int = 0
    messages_count: int = 0
    output_dir: Optional[Path] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    @property
    def total_records(self) -> int:
        """Total records extracted across all DMOs."""
        return (
            self.sessions_count +
            self.interactions_count +
            self.steps_count +
            self.messages_count
        )

    @property
    def duration_seconds(self) -> float:
        """Extraction duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "sessions_count": self.sessions_count,
            "interactions_count": self.interactions_count,
            "steps_count": self.steps_count,
            "messages_count": self.messages_count,
            "total_records": self.total_records,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
        }


@dataclass
class QualityExtractionResult:
    """Results from a quality DMO extraction operation."""

    generations_count: int = 0
    content_quality_count: int = 0
    content_categories_count: int = 0
    output_dir: Optional[Path] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    @property
    def total_records(self) -> int:
        """Total records extracted across quality DMOs."""
        return (
            self.generations_count +
            self.content_quality_count +
            self.content_categories_count
        )

    @property
    def duration_seconds(self) -> float:
        """Extraction duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "generations_count": self.generations_count,
            "content_quality_count": self.content_quality_count,
            "content_categories_count": self.content_categories_count,
            "total_records": self.total_records,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
        }


@dataclass
class STDMExtractor:
    """
    Extract Agentforce session tracing data from Data Cloud.

    Handles the hierarchical DMO structure:
    - AIAgentSession → AIAgentInteraction → (AIAgentInteractionStep, AIAgentMoment)

    Supports both full extraction (by date range) and targeted extraction
    (by session IDs).

    Attributes:
        client: Configured DataCloudClient instance
        output_dir: Base directory for output files

    Example:
        >>> extractor = STDMExtractor(client, Path("./data"))
        >>> result = extractor.extract_sessions(since=datetime(2026, 1, 1))
        >>> print(f"Extracted {result.total_records} records")
    """

    client: DataCloudClient
    output_dir: Path

    def __post_init__(self):
        """Ensure output directory exists."""
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime for Data Cloud SQL."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def _build_session_query(
        self,
        since: datetime,
        until: Optional[datetime] = None,
        agent_names: Optional[List[str]] = None,
    ) -> str:
        """
        Build session extraction query.

        Args:
            since: Start datetime
            until: End datetime (defaults to now)
            agent_names: Optional list of agent API names to filter

        Returns:
            Data Cloud SQL query string
        """
        until = until or datetime.utcnow()

        fields = build_select_clause("sessions")
        dmo = DMO_NAMES["sessions"]

        query = f"""
            SELECT {fields}
            FROM {dmo}
            WHERE ssot__StartTimestamp__c >= '{self._format_timestamp(since)}'
              AND ssot__StartTimestamp__c < '{self._format_timestamp(until)}'
        """.strip()

        # NOTE: Agent name filtering is not directly supported on Session table.
        # Session table does not have ssot__AIAgentApiName__c - that field is on Moment table.
        # To filter by agent, query Moments first to get session IDs, then use extract_session_tree.
        if agent_names:
            console.print(
                "[yellow]Warning: Agent name filtering not supported on Session table. "
                "Use extract_session_tree with session IDs instead.[/yellow]"
            )

        query += "\n  ORDER BY ssot__StartTimestamp__c"

        return query

    def _build_child_query(
        self,
        entity_type: str,
        parent_ids: List[str],
        parent_field: str,
    ) -> str:
        """
        Build query for child records based on parent IDs.

        Args:
            entity_type: 'interactions', 'steps', or 'messages'
            parent_ids: List of parent record IDs
            parent_field: Field name containing parent FK

        Returns:
            Data Cloud SQL query string
        """
        fields = build_select_clause(entity_type)
        dmo = DMO_NAMES[entity_type]

        ids_list = ", ".join(f"'{id}'" for id in parent_ids)
        query = f"""
            SELECT {fields}
            FROM {dmo}
            WHERE {parent_field} IN ({ids_list})
        """.strip()

        return query

    def extract_sessions(
        self,
        since: datetime,
        until: Optional[datetime] = None,
        agent_names: Optional[List[str]] = None,
        include_children: bool = True,
        show_progress: bool = True,
        append: bool = False,
    ) -> ExtractionResult:
        """
        Extract session data with optional child records.

        Args:
            since: Start datetime for extraction
            until: End datetime (defaults to now)
            agent_names: Optional list of agent API names to filter
            include_children: Whether to extract interactions, steps, messages
            show_progress: Show progress indicators
            append: If True, merge with existing data instead of overwriting

        Returns:
            ExtractionResult with counts and metadata
        """
        result = ExtractionResult(
            output_dir=self.output_dir,
            start_time=datetime.now()
        )

        try:
            # 1. Extract sessions
            session_query = self._build_session_query(since, until, agent_names)
            session_path = self.output_dir / "sessions"

            if show_progress:
                console.print("[cyan]Extracting sessions...[/cyan]")

            result.sessions_count = self.client.query_to_parquet(
                session_query,
                session_path / "data.parquet",
                schema=SCHEMAS["sessions"],
                show_progress=show_progress,
                append=append
            )

            if show_progress:
                console.print(f"  [green]✓[/green] {result.sessions_count} sessions")

            if not include_children or result.sessions_count == 0:
                result.end_time = datetime.now()
                self._save_metadata(result, since, until, agent_names)
                return result

            # 2. Get session IDs for child queries
            session_ids = self._get_session_ids(session_path / "data.parquet")

            # 3. Extract interactions
            if show_progress:
                console.print("[cyan]Extracting interactions...[/cyan]")

            interaction_query = self._build_child_query(
                "interactions",
                session_ids,
                "ssot__AiAgentSessionId__c"
            )
            interaction_path = self.output_dir / "interactions"

            result.interactions_count = self.client.query_to_parquet(
                interaction_query,
                interaction_path / "data.parquet",
                schema=SCHEMAS["interactions"],
                show_progress=show_progress,
                append=append
            )

            if show_progress:
                console.print(f"  [green]✓[/green] {result.interactions_count} interactions")

            if result.interactions_count == 0:
                result.end_time = datetime.now()
                self._save_metadata(result, since, until, agent_names)
                return result

            # 4. Get interaction IDs for step queries
            interaction_ids = self._get_interaction_ids(interaction_path / "data.parquet")

            # 5. Extract steps and messages in PARALLEL
            # Steps depend on interaction_ids, Messages depend on session_ids
            # Since we have both, we can run them concurrently for better performance
            if show_progress:
                console.print("[cyan]Extracting steps + messages (parallel)...[/cyan]")

            step_query = self._build_child_query(
                "steps",
                interaction_ids,
                "ssot__AiAgentInteractionId__c"
            )
            step_path = self.output_dir / "steps"

            message_query = self._build_child_query(
                "messages",
                session_ids,  # Messages link to sessions, not interactions
                "ssot__AiAgentSessionId__c"  # Note: lowercase 'i' in AiAgent
            )
            message_path = self.output_dir / "messages"

            # Run both extractions in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both extraction tasks
                futures = {
                    executor.submit(
                        self.client.query_to_parquet,
                        step_query,
                        step_path / "data.parquet",
                        SCHEMAS["steps"],  # schema
                        None,  # partition_cols
                        False,  # show_progress (disable per-task progress in parallel)
                        append,
                    ): "steps",
                    executor.submit(
                        self.client.query_to_parquet,
                        message_query,
                        message_path / "data.parquet",
                        SCHEMAS["messages"],  # schema
                        None,  # partition_cols
                        False,  # show_progress (disable per-task progress in parallel)
                        append,
                    ): "messages",
                }

                # Collect results as they complete
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        count = future.result()
                        if name == "steps":
                            result.steps_count = count
                            if show_progress:
                                console.print(f"  [green]✓[/green] {count} steps")
                        else:
                            result.messages_count = count
                            if show_progress:
                                console.print(f"  [green]✓[/green] {count} messages")
                    except Exception as e:
                        result.errors.append(f"{name}: {str(e)}")
                        if show_progress:
                            console.print(f"  [red]✗[/red] {name}: {e}")

        except Exception as e:
            result.errors.append(str(e))
            if show_progress:
                console.print(f"[red]Error: {e}[/red]")

        result.end_time = datetime.now()
        self._save_metadata(result, since, until, agent_names)
        return result

    def extract_session_tree(
        self,
        session_ids: List[str],
        show_progress: bool = True,
    ) -> ExtractionResult:
        """
        Extract complete session trees for specific session IDs.

        Useful for debugging specific sessions with all related records.

        Args:
            session_ids: List of session IDs to extract
            show_progress: Show progress indicators

        Returns:
            ExtractionResult with counts and metadata
        """
        result = ExtractionResult(
            output_dir=self.output_dir,
            start_time=datetime.now()
        )

        try:
            # 1. Extract sessions by ID
            if show_progress:
                console.print("[cyan]Extracting sessions...[/cyan]")

            session_query = self._build_child_query(
                "sessions",
                session_ids,
                "ssot__Id__c"
            )
            session_path = self.output_dir / "sessions"

            result.sessions_count = self.client.query_to_parquet(
                session_query,
                session_path / "data.parquet",
                schema=SCHEMAS["sessions"],
                show_progress=show_progress
            )

            if show_progress:
                console.print(f"  [green]✓[/green] {result.sessions_count} sessions")

            # 2. Extract interactions
            if show_progress:
                console.print("[cyan]Extracting interactions...[/cyan]")

            interaction_query = self._build_child_query(
                "interactions",
                session_ids,
                "ssot__AiAgentSessionId__c"
            )
            interaction_path = self.output_dir / "interactions"

            result.interactions_count = self.client.query_to_parquet(
                interaction_query,
                interaction_path / "data.parquet",
                schema=SCHEMAS["interactions"],
                show_progress=show_progress
            )

            if show_progress:
                console.print(f"  [green]✓[/green] {result.interactions_count} interactions")

            if result.interactions_count > 0:
                interaction_ids = self._get_interaction_ids(interaction_path / "data.parquet")

                # 3. Extract steps and messages in PARALLEL
                if show_progress:
                    console.print("[cyan]Extracting steps + messages (parallel)...[/cyan]")

                step_query = self._build_child_query(
                    "steps",
                    interaction_ids,
                    "ssot__AiAgentInteractionId__c"
                )
                step_path = self.output_dir / "steps"

                message_query = self._build_child_query(
                    "messages",
                    session_ids,  # Messages link to sessions, not interactions
                    "ssot__AiAgentSessionId__c"  # Note: lowercase 'i' in AiAgent
                )
                message_path = self.output_dir / "messages"

                # Run both extractions in parallel using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {
                        executor.submit(
                            self.client.query_to_parquet,
                            step_query,
                            step_path / "data.parquet",
                            SCHEMAS["steps"],
                            None,  # partition_cols
                            False,  # show_progress
                        ): "steps",
                        executor.submit(
                            self.client.query_to_parquet,
                            message_query,
                            message_path / "data.parquet",
                            SCHEMAS["messages"],
                            None,  # partition_cols
                            False,  # show_progress
                        ): "messages",
                    }

                    for future in as_completed(futures):
                        name = futures[future]
                        try:
                            count = future.result()
                            if name == "steps":
                                result.steps_count = count
                                if show_progress:
                                    console.print(f"  [green]✓[/green] {count} steps")
                            else:
                                result.messages_count = count
                                if show_progress:
                                    console.print(f"  [green]✓[/green] {count} messages")
                        except Exception as e:
                            result.errors.append(f"{name}: {str(e)}")
                            if show_progress:
                                console.print(f"  [red]✗[/red] {name}: {e}")

        except Exception as e:
            result.errors.append(str(e))
            if show_progress:
                console.print(f"[red]Error: {e}[/red]")

        result.end_time = datetime.now()
        self._save_metadata(result, None, None, None, session_ids)
        return result

    def extract_incremental(
        self,
        agent_names: Optional[List[str]] = None,
        show_progress: bool = True,
    ) -> ExtractionResult:
        """
        Perform incremental extraction from last watermark.

        Reads the watermark file to determine the last extraction time
        and extracts only new data.

        Args:
            agent_names: Optional list of agent API names to filter
            show_progress: Show progress indicators

        Returns:
            ExtractionResult with counts and metadata
        """
        watermark_file = self.output_dir / "metadata" / "watermark.json"

        # Determine start time from watermark
        if watermark_file.exists():
            with open(watermark_file) as f:
                watermark = json.load(f)
                since = datetime.fromisoformat(watermark["last_extraction"])
        else:
            # Default to 24 hours ago if no watermark
            since = datetime.utcnow() - timedelta(hours=24)
            if show_progress:
                console.print(
                    f"[yellow]No watermark found, extracting from {since.isoformat()}[/yellow]"
                )

        # Run extraction with append=True to merge with existing data
        result = self.extract_sessions(
            since=since,
            agent_names=agent_names,
            show_progress=show_progress,
            append=True
        )

        # Update watermark if successful
        if not result.errors:
            self._update_watermark()

        return result

    def extract_quality(
        self,
        show_progress: bool = True,
    ) -> "QualityExtractionResult":
        """
        Extract quality DMOs based on existing step data.

        Reads generation IDs from extracted steps and fetches the
        corresponding GenAIGeneration, GenAIContentQuality, and
        GenAIContentCategory records.

        Prerequisites:
            Steps must be extracted first (via extract or extract-tree)

        Returns:
            QualityExtractionResult with counts and metadata
        """
        result = QualityExtractionResult(
            output_dir=self.output_dir,
            start_time=datetime.now()
        )

        try:
            # Get generation IDs from existing steps
            step_path = self.output_dir / "steps" / "data.parquet"
            if not step_path.exists():
                raise FileNotFoundError(
                    "Steps not found. Run extract first, then extract-quality."
                )

            generation_ids = self._get_generation_ids(step_path)

            if not generation_ids:
                if show_progress:
                    console.print("[yellow]No generation IDs found in steps.[/yellow]")
                result.end_time = datetime.now()
                return result

            if show_progress:
                console.print(f"[cyan]Found {len(generation_ids)} unique generation IDs[/cyan]")

            # 1. Extract generations
            if show_progress:
                console.print("[cyan]Extracting generations...[/cyan]")

            generation_query = self._build_quality_query(
                "generations",
                generation_ids,
                "generationId__c"
            )
            generation_path = self.output_dir / "generations"

            result.generations_count = self.client.query_to_parquet(
                generation_query,
                generation_path / "data.parquet",
                schema=SCHEMAS["generations"],
                show_progress=show_progress
            )

            if show_progress:
                console.print(f"  [green]✓[/green] {result.generations_count} generations")

            if result.generations_count == 0:
                result.end_time = datetime.now()
                return result

            # 2. Extract content quality (parent = generation)
            if show_progress:
                console.print("[cyan]Extracting content quality...[/cyan]")

            quality_query = self._build_quality_query(
                "content_quality",
                generation_ids,
                "parent__c"
            )
            quality_path = self.output_dir / "content_quality"

            result.content_quality_count = self.client.query_to_parquet(
                quality_query,
                quality_path / "data.parquet",
                schema=SCHEMAS["content_quality"],
                show_progress=show_progress
            )

            if show_progress:
                console.print(f"  [green]✓[/green] {result.content_quality_count} quality records")

            # Get quality IDs for category lookup
            quality_ids = []
            if result.content_quality_count > 0:
                quality_ids = self._get_quality_ids(quality_path / "data.parquet")

            # 3. Extract content categories (parent = generation OR quality)
            if show_progress:
                console.print("[cyan]Extracting content categories...[/cyan]")

            # Categories can link to either generations or quality records
            all_parent_ids = list(set(generation_ids + quality_ids))
            category_query = self._build_quality_query(
                "content_categories",
                all_parent_ids,
                "parent__c"
            )
            category_path = self.output_dir / "content_categories"

            result.content_categories_count = self.client.query_to_parquet(
                category_query,
                category_path / "data.parquet",
                schema=SCHEMAS["content_categories"],
                show_progress=show_progress
            )

            if show_progress:
                console.print(f"  [green]✓[/green] {result.content_categories_count} category records")

        except Exception as e:
            result.errors.append(str(e))
            if show_progress:
                console.print(f"[red]Error: {e}[/red]")

        result.end_time = datetime.now()
        self._save_quality_metadata(result)
        return result

    def _build_quality_query(
        self,
        entity_type: str,
        parent_ids: List[str],
        parent_field: str,
    ) -> str:
        """Build query for quality DMO records."""
        fields = build_select_clause(entity_type)
        dmo = DMO_NAMES[entity_type]

        # Filter out None values
        valid_ids = [id for id in parent_ids if id is not None]
        if not valid_ids:
            return f"SELECT {fields} FROM {dmo} WHERE 1=0"

        ids_list = ", ".join(f"'{id}'" for id in valid_ids)
        query = f"""
            SELECT {fields}
            FROM {dmo}
            WHERE {parent_field} IN ({ids_list})
        """.strip()

        return query

    def _get_generation_ids(self, parquet_path: Path) -> List[str]:
        """Extract unique generation IDs from steps Parquet file."""
        import pyarrow.parquet as pq

        if not parquet_path.exists():
            return []

        table = pq.read_table(parquet_path, columns=["ssot__GenerationId__c"])
        # Filter out None values and get unique
        ids = [id for id in table.column("ssot__GenerationId__c").to_pylist() if id]
        return list(set(ids))

    def _get_quality_ids(self, parquet_path: Path) -> List[str]:
        """Extract quality record IDs from Parquet file."""
        import pyarrow.parquet as pq

        if not parquet_path.exists():
            return []

        table = pq.read_table(parquet_path, columns=["id__c"])
        return table.column("id__c").to_pylist()

    def _save_quality_metadata(self, result: "QualityExtractionResult"):
        """Save quality extraction metadata to file."""
        metadata_dir = self.output_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "extraction_time": datetime.now().isoformat(),
            "type": "quality",
            "results": result.to_dict(),
        }

        with open(metadata_dir / "quality_extraction.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def print_quality_summary(self, result: "QualityExtractionResult"):
        """Print quality extraction summary to console."""
        table = Table(title="Quality Extraction Summary")
        table.add_column("Entity", style="cyan")
        table.add_column("Count", justify="right", style="green")

        table.add_row("Generations", str(result.generations_count))
        table.add_row("Content Quality", str(result.content_quality_count))
        table.add_row("Content Categories", str(result.content_categories_count))
        table.add_row("─" * 20, "─" * 10)
        table.add_row("Total", str(result.total_records), style="bold")

        console.print(table)

        if result.duration_seconds > 0:
            rate = result.total_records / result.duration_seconds
            console.print(
                f"\nCompleted in {result.duration_seconds:.1f}s "
                f"({rate:.0f} records/sec)"
            )

        if result.errors:
            console.print("\n[red]Errors:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")

    def _get_session_ids(self, parquet_path: Path) -> List[str]:
        """Extract session IDs from Parquet file."""
        import pyarrow.parquet as pq

        if not parquet_path.exists():
            return []

        table = pq.read_table(parquet_path, columns=["ssot__Id__c"])
        return table.column("ssot__Id__c").to_pylist()

    def _get_interaction_ids(self, parquet_path: Path) -> List[str]:
        """Extract interaction IDs from Parquet file."""
        import pyarrow.parquet as pq

        if not parquet_path.exists():
            return []

        table = pq.read_table(parquet_path, columns=["ssot__Id__c"])
        return table.column("ssot__Id__c").to_pylist()

    def _save_metadata(
        self,
        result: ExtractionResult,
        since: Optional[datetime],
        until: Optional[datetime],
        agent_names: Optional[List[str]],
        session_ids: Optional[List[str]] = None,
    ):
        """Save extraction metadata to file."""
        metadata_dir = self.output_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "extraction_time": datetime.now().isoformat(),
            "parameters": {
                "since": since.isoformat() if since else None,
                "until": until.isoformat() if until else None,
                "agent_names": agent_names,
                "session_ids": session_ids,
            },
            "results": result.to_dict(),
        }

        with open(metadata_dir / "extraction.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def _update_watermark(self):
        """Update watermark file with current time."""
        metadata_dir = self.output_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)

        watermark = {
            "last_extraction": datetime.utcnow().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        with open(metadata_dir / "watermark.json", "w") as f:
            json.dump(watermark, f, indent=2)

    def print_summary(self, result: ExtractionResult):
        """Print extraction summary to console."""
        table = Table(title="Extraction Summary")
        table.add_column("Entity", style="cyan")
        table.add_column("Count", justify="right", style="green")

        table.add_row("Sessions", str(result.sessions_count))
        table.add_row("Interactions", str(result.interactions_count))
        table.add_row("Steps", str(result.steps_count))
        table.add_row("Messages", str(result.messages_count))
        table.add_row("─" * 15, "─" * 10)
        table.add_row("Total", str(result.total_records), style="bold")

        console.print(table)

        if result.duration_seconds > 0:
            rate = result.total_records / result.duration_seconds
            console.print(
                f"\nCompleted in {result.duration_seconds:.1f}s "
                f"({rate:.0f} records/sec)"
            )

        if result.errors:
            console.print("\n[red]Errors:[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
