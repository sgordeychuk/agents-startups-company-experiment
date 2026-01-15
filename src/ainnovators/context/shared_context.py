"""Shared context pool for the AI startup company."""

import json
import logging
from copy import deepcopy
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class CompanyContext:
    """
    Centralized state pool for the AI company.
    All agents read from and write to this shared context.
    """

    def __init__(self) -> None:
        """Initialize the shared context."""
        # Core state containers
        self.state: dict[str, Any] = {
            # Stage tracking
            "current_stage": None,
            "completed_stages": [],
            "stage_outputs": {},
            # Work products
            "idea": None,
            "research": None,
            "prototype": None,
            "marketing_strategies": None,
            "pitch": None,
            # Decisions and reasoning
            "decisions": [],
            "rejections": [],
            "iterations": 0,
            # Agent interactions
            "conversations": [],
            "tool_calls": [],
            # Metadata
            "start_time": datetime.now(),
            "costs": {"total": 0.0, "by_stage": {}},
            "token_usage": {"total": 0, "by_agent": {}},
        }

        # Change history for debugging
        self.history: list[dict[str, Any]] = []

        # Stage-specific contexts (nested)
        self.stage_contexts: dict[str, dict[str, Any]] = {
            "idea_development": {},
            "prototyping": {},
            "pitch": {},
        }

    def update(
        self,
        agent_name: str,
        key: str,
        value: Any,
        stage: str | None = None,
    ) -> None:
        """
        Agent updates shared context, records change in history.

        Args:
            agent_name: Name of the agent making the update
            key: The key to update in state
            value: The new value
            stage: Optional stage name (defaults to current_stage)
        """
        old_value = self.state.get(key)
        self.state[key] = value

        # Record change
        change = {
            "timestamp": datetime.now(),
            "agent": agent_name,
            "stage": stage or self.state.get("current_stage"),
            "key": key,
            "old_value": old_value,
            "new_value": value,
        }
        self.history.append(change)
        logger.info(f"[{agent_name}] Updated {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Read from shared context.

        Args:
            key: The key to read
            default: Default value if key not found

        Returns:
            The value associated with the key
        """
        return self.state.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        """
        Return full state snapshot for debugging.

        Returns:
            Dictionary containing state, stage_contexts, and history length
        """
        return {
            "state": deepcopy(self.state),
            "stage_contexts": deepcopy(self.stage_contexts),
            "history_length": len(self.history),
        }

    def get_history(
        self,
        agent: str | None = None,
        stage: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get filtered change history.

        Args:
            agent: Filter by agent name
            stage: Filter by stage name

        Returns:
            List of history entries matching the filters
        """
        history = self.history
        if agent:
            history = [h for h in history if h["agent"] == agent]
        if stage:
            history = [h for h in history if h["stage"] == stage]
        return history

    def set_stage_context(self, stage: str, key: str, value: Any) -> None:
        """
        Set a value in stage-specific context.

        Args:
            stage: The stage name
            key: The key to set
            value: The value to set
        """
        if stage in self.stage_contexts:
            self.stage_contexts[stage][key] = value

    def get_stage_context(self, stage: str, key: str, default: Any = None) -> Any:
        """
        Get a value from stage-specific context.

        Args:
            stage: The stage name
            key: The key to get
            default: Default value if not found

        Returns:
            The value or default
        """
        return self.stage_contexts.get(stage, {}).get(key, default)

    def export_for_next_stage(self) -> dict[str, Any]:
        """
        Export relevant context for the next stage.
        Summarizes to avoid context window explosion.

        Returns:
            Dictionary with essential context for next stage
        """
        return {
            "idea": self.state.get("idea"),
            "research": self.state.get("research"),
            "prototype": self.state.get("prototype"),
            "marketing_strategies": self.state.get("marketing_strategies"),
            "completed_stages": self.state.get("completed_stages", []),
            "decisions": self.state.get("decisions", []),
        }

    def save_to_file(self, filepath: str) -> None:
        """
        Save context snapshot to JSON file.

        Args:
            filepath: Path to save the snapshot
        """
        snapshot = self.snapshot()
        # Convert datetime objects to ISO format strings
        snapshot["state"]["start_time"] = snapshot["state"]["start_time"].isoformat()

        with open(filepath, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, filepath: str) -> CompanyContext:
        """
        Load context from JSON file.

        Args:
            filepath: Path to load from

        Returns:
            New CompanyContext instance with loaded state
        """
        with open(filepath) as f:
            data = json.load(f)

        context = cls()
        context.state = data.get("state", context.state)
        context.stage_contexts = data.get("stage_contexts", context.stage_contexts)

        # Convert start_time back to datetime
        if isinstance(context.state.get("start_time"), str):
            context.state["start_time"] = datetime.fromisoformat(context.state["start_time"])

        return context
