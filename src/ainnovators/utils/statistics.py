"""Pipeline statistics collection and formatting."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .pricing import calculate_cost


@dataclass
class AgentUsage:
    """Usage statistics for a single agent."""

    agent_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    execution_time_ms: int = 0
    call_count: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used by this agent."""
        return self.prompt_tokens + self.completion_tokens


@dataclass
class StageStatistics:
    """Statistics for a single pipeline stage."""

    stage_name: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    agent_usage: dict[str, AgentUsage] = field(default_factory=dict)

    @property
    def execution_time_ms(self) -> int:
        """Total execution time in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

    @property
    def total_prompt_tokens(self) -> int:
        """Total prompt tokens for this stage."""
        return sum(a.prompt_tokens for a in self.agent_usage.values())

    @property
    def total_completion_tokens(self) -> int:
        """Total completion tokens for this stage."""
        return sum(a.completion_tokens for a in self.agent_usage.values())

    @property
    def total_tokens(self) -> int:
        """Total tokens for this stage."""
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def total_cost(self) -> float:
        """Total cost for this stage."""
        return sum(a.cost for a in self.agent_usage.values())

    @property
    def total_calls(self) -> int:
        """Total API calls for this stage."""
        return sum(a.call_count for a in self.agent_usage.values())


class PipelineStatistics:
    """
    Central statistics collector for the pipeline.

    Tracks execution time, token usage, and costs per agent and per stage.
    """

    def __init__(self, max_budget: float = 10.0) -> None:
        """
        Initialize the statistics collector.

        Args:
            max_budget: Maximum budget for the experiment in USD
        """
        self.max_budget = max_budget
        self.stages: dict[str, StageStatistics] = {}
        self.pipeline_start_time: datetime | None = None
        self.pipeline_end_time: datetime | None = None
        self._current_stage: str | None = None

    def start_pipeline(self) -> None:
        """Mark the start of pipeline execution."""
        self.pipeline_start_time = datetime.now()

    def end_pipeline(self) -> None:
        """Mark the end of pipeline execution."""
        self.pipeline_end_time = datetime.now()

    def start_stage(self, stage_name: str) -> None:
        """
        Mark the start of a stage.

        Args:
            stage_name: Name of the stage
        """
        self._current_stage = stage_name
        if stage_name not in self.stages:
            self.stages[stage_name] = StageStatistics(stage_name=stage_name)
        self.stages[stage_name].start_time = datetime.now()

    def end_stage(self, stage_name: str) -> None:
        """
        Mark the end of a stage.

        Args:
            stage_name: Name of the stage
        """
        if stage_name in self.stages:
            self.stages[stage_name].end_time = datetime.now()
        self._current_stage = None

    def record_agent_call(
        self,
        stage: str,
        agent: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        execution_time_ms: int,
    ) -> None:
        """
        Record an agent API call.

        Args:
            stage: Stage name
            agent: Agent name
            model: Model used
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            execution_time_ms: Execution time in milliseconds
        """
        if stage not in self.stages:
            self.stages[stage] = StageStatistics(stage_name=stage)

        stage_stats = self.stages[stage]

        if agent not in stage_stats.agent_usage:
            stage_stats.agent_usage[agent] = AgentUsage(agent_name=agent)

        usage = stage_stats.agent_usage[agent]
        usage.prompt_tokens += prompt_tokens
        usage.completion_tokens += completion_tokens
        usage.cost += calculate_cost(model, prompt_tokens, completion_tokens)
        usage.execution_time_ms += execution_time_ms
        usage.call_count += 1

    def get_stage_stats(self, stage_name: str) -> StageStatistics | None:
        """Get statistics for a specific stage."""
        return self.stages.get(stage_name)

    @property
    def total_execution_time_ms(self) -> int:
        """Total pipeline execution time in milliseconds."""
        if self.pipeline_start_time and self.pipeline_end_time:
            return int((self.pipeline_end_time - self.pipeline_start_time).total_seconds() * 1000)
        return sum(s.execution_time_ms for s in self.stages.values())

    @property
    def total_prompt_tokens(self) -> int:
        """Total prompt tokens across all stages."""
        return sum(s.total_prompt_tokens for s in self.stages.values())

    @property
    def total_completion_tokens(self) -> int:
        """Total completion tokens across all stages."""
        return sum(s.total_completion_tokens for s in self.stages.values())

    @property
    def total_tokens(self) -> int:
        """Total tokens across all stages."""
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def total_cost(self) -> float:
        """Total cost across all stages."""
        return sum(s.total_cost for s in self.stages.values())

    @property
    def total_calls(self) -> int:
        """Total API calls across all stages."""
        return sum(s.total_calls for s in self.stages.values())

    def get_agent_totals(self) -> dict[str, AgentUsage]:
        """Get aggregated usage per agent across all stages."""
        agent_totals: dict[str, AgentUsage] = {}

        for stage_stats in self.stages.values():
            for agent_name, usage in stage_stats.agent_usage.items():
                if agent_name not in agent_totals:
                    agent_totals[agent_name] = AgentUsage(agent_name=agent_name)

                total = agent_totals[agent_name]
                total.prompt_tokens += usage.prompt_tokens
                total.completion_tokens += usage.completion_tokens
                total.cost += usage.cost
                total.execution_time_ms += usage.execution_time_ms
                total.call_count += usage.call_count

        return agent_totals

    def get_pipeline_summary(self) -> dict[str, Any]:
        """
        Get pipeline summary as a dictionary.

        Returns:
            Dictionary containing all statistics
        """
        return {
            "total_execution_time_ms": self.total_execution_time_ms,
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost": self.total_cost,
            "max_budget": self.max_budget,
            "budget_used_percent": (self.total_cost / self.max_budget * 100)
            if self.max_budget > 0
            else 0,
            "stages": {
                name: {
                    "execution_time_ms": stats.execution_time_ms,
                    "total_calls": stats.total_calls,
                    "total_tokens": stats.total_tokens,
                    "total_cost": stats.total_cost,
                    "agents": {
                        agent: {
                            "call_count": usage.call_count,
                            "execution_time_ms": usage.execution_time_ms,
                            "prompt_tokens": usage.prompt_tokens,
                            "completion_tokens": usage.completion_tokens,
                            "total_tokens": usage.total_tokens,
                            "cost": usage.cost,
                        }
                        for agent, usage in stats.agent_usage.items()
                    },
                }
                for name, stats in self.stages.items()
            },
            "agents": {
                agent: {
                    "call_count": usage.call_count,
                    "execution_time_ms": usage.execution_time_ms,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost": usage.cost,
                }
                for agent, usage in self.get_agent_totals().items()
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """Alias for get_pipeline_summary."""
        return self.get_pipeline_summary()

    @staticmethod
    def _format_time(ms: int) -> str:
        """Format milliseconds as human-readable time."""
        if ms < 1000:
            return f"{ms}ms"
        seconds = ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"

    def format_summary(self) -> str:
        """
        Format statistics as a human-readable summary.

        Returns:
            Formatted string with statistics tables
        """
        lines = [
            "",
            "=" * 80,
            "                     PIPELINE EXECUTION STATISTICS",
            "=" * 80,
            "",
            "OVERALL SUMMARY",
            "-" * 40,
            f"Total Execution Time: {self._format_time(self.total_execution_time_ms)}",
            f"Total API Calls: {self.total_calls}",
            f"Total Tokens: {self.total_tokens:,} (Input: {self.total_prompt_tokens:,} | Output: {self.total_completion_tokens:,})",
            f"Total Cost: ${self.total_cost:.2f} USD",
            "",
        ]

        # Stage breakdown
        if self.stages:
            lines.extend(
                [
                    "STAGE BREAKDOWN",
                    "-" * 40,
                    f"{'Stage':<20} {'Time':>10} {'Calls':>8} {'Tokens':>12} {'Cost':>10}",
                    "-" * 60,
                ]
            )

            for name, stats in self.stages.items():
                lines.append(
                    f"{name:<20} {self._format_time(stats.execution_time_ms):>10} "
                    f"{stats.total_calls:>8} {stats.total_tokens:>12,} "
                    f"${stats.total_cost:>9.2f}"
                )

            lines.append("")

        # Agent breakdown
        agent_totals = self.get_agent_totals()
        if agent_totals:
            lines.extend(
                [
                    "AGENT BREAKDOWN",
                    "-" * 40,
                    f"{'Agent':<20} {'Calls':>8} {'Time':>10} {'Tokens':>12} {'Cost':>10}",
                    "-" * 60,
                ]
            )

            for agent_name, usage in sorted(
                agent_totals.items(), key=lambda x: x[1].cost, reverse=True
            ):
                lines.append(
                    f"{agent_name:<20} {usage.call_count:>8} "
                    f"{self._format_time(usage.execution_time_ms):>10} "
                    f"{usage.total_tokens:>12,} ${usage.cost:>9.2f}"
                )

            lines.append("")

        # Budget status
        budget_percent = (self.total_cost / self.max_budget * 100) if self.max_budget > 0 else 0
        lines.extend(
            [
                f"Budget: ${self.total_cost:.2f} / ${self.max_budget:.2f} ({budget_percent:.1f}% used)",
                "=" * 80,
                "",
            ]
        )

        return "\n".join(lines)
