"""Context observation and debugging tools."""

import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .shared_context import CompanyContext


class ContextObserver:
    """Tools to observe and debug context evolution."""

    @staticmethod
    def print_context_tree(context: CompanyContext) -> None:
        """
        Print context state as formatted tree.

        Args:
            context: The CompanyContext to print
        """
        print(json.dumps(context.state, indent=2, default=str))

    @staticmethod
    def replay_history(context: CompanyContext) -> None:
        """
        Replay all state changes in chronological order.

        Args:
            context: The CompanyContext to replay
        """
        for i, change in enumerate(context.history):
            timestamp = change["timestamp"]
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            print(f"{i + 1}. [{timestamp}] {change['agent']} -> {change['key']}")

    @staticmethod
    def export_timeline(context: CompanyContext, filename: str) -> None:
        """
        Export context changes as timeline JSON.

        Args:
            context: The CompanyContext to export
            filename: Path to save the timeline
        """
        timeline = [
            {
                "step": i + 1,
                "time": (
                    change["timestamp"].isoformat()
                    if isinstance(change["timestamp"], datetime)
                    else change["timestamp"]
                ),
                "stage": change["stage"],
                "agent": change["agent"],
                "action": f"Updated {change['key']}",
                "value": str(change["new_value"])[:200],
            }
            for i, change in enumerate(context.history)
        ]

        with open(filename, "w") as f:
            json.dump(timeline, f, indent=2)

    @staticmethod
    def get_agent_activity(context: CompanyContext, agent_name: str) -> list[dict]:
        """
        Get all activity for a specific agent.

        Args:
            context: The CompanyContext to search
            agent_name: Name of the agent

        Returns:
            List of history entries for the agent
        """
        return context.get_history(agent=agent_name)

    @staticmethod
    def get_stage_summary(context: CompanyContext, stage: str) -> dict:
        """
        Get summary of a specific stage.

        Args:
            context: The CompanyContext to summarize
            stage: Stage name

        Returns:
            Dictionary with stage summary
        """
        stage_history = context.get_history(stage=stage)
        return {
            "stage": stage,
            "num_changes": len(stage_history),
            "agents_involved": list({h["agent"] for h in stage_history}),
            "keys_modified": list({h["key"] for h in stage_history}),
            "stage_context": context.stage_contexts.get(stage, {}),
        }

    @staticmethod
    def calculate_costs(context: CompanyContext) -> dict:
        """
        Calculate and return cost breakdown.

        Args:
            context: The CompanyContext with cost data

        Returns:
            Dictionary with cost breakdown
        """
        return {
            "total": context.state.get("costs", {}).get("total", 0),
            "by_stage": context.state.get("costs", {}).get("by_stage", {}),
            "token_usage": context.state.get("token_usage", {}),
        }
