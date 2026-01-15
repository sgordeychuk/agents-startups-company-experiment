"""Stage execution logging utilities for debugging and tracking."""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StageExecutionLogger:
    """
    Logger for tracking stage execution with detailed agent interactions.

    Captures all agent calls, timing, iterations, and events during
    stage execution for debugging and analysis.
    """

    def __init__(self, stage_name: str, output_dir: Path | None = None) -> None:
        """
        Initialize the stage execution logger.

        Args:
            stage_name: Name of the stage being executed
            output_dir: Directory to save logs (default: ./test_results)
        """
        self.stage_name = stage_name
        self.output_dir = output_dir or Path("./test_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Execution tracking
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.current_iteration = 0
        self.current_agent_start: datetime | None = None

        # Log data
        self.log_data: dict[str, Any] = {
            "stage_name": stage_name,
            "timestamp_start": None,
            "timestamp_end": None,
            "execution_time_ms": 0,
            "success": False,
            "input": {},
            "iterations": [],
            "final_output": None,
            "events": [],
            "error": None,
        }

        # Current iteration data
        self.current_iteration_data: dict[str, Any] = {"iteration": 0, "agents": []}

    def start(self, input_data: dict[str, Any] | None = None) -> None:
        """
        Start logging stage execution.

        Args:
            input_data: Input data for the stage
        """
        self.start_time = datetime.now()
        self.log_data["timestamp_start"] = self.start_time.isoformat()
        if input_data:
            self.log_data["input"] = input_data
        logger.info(f"[{self.stage_name}] Stage execution started")

    def start_iteration(self, iteration: int) -> None:
        """
        Start a new iteration.

        Args:
            iteration: Iteration number
        """
        # Save previous iteration if exists
        if self.current_iteration_data["agents"]:
            self.log_data["iterations"].append(self.current_iteration_data)

        # Start new iteration
        self.current_iteration = iteration
        self.current_iteration_data = {"iteration": iteration, "agents": []}
        logger.info(f"[{self.stage_name}] Starting iteration {iteration}")

    def log_agent_start(self, agent_name: str, method: str, input_data: Any = None) -> None:
        """
        Log the start of an agent method call.

        Args:
            agent_name: Name of the agent
            method: Method being called
            input_data: Input to the method (optional)
        """
        self.current_agent_start = datetime.now()
        logger.info(f"[{self.stage_name}] {agent_name}.{method}() started")

    def log_agent_complete(
        self,
        agent_name: str,
        method: str,
        output: Any,
        input_data: Any = None,
    ) -> None:
        """
        Log the completion of an agent method call.

        Args:
            agent_name: Name of the agent
            method: Method that was called
            output: Output from the method
            input_data: Input to the method (optional)
        """
        end_time = datetime.now()
        start_time = self.current_agent_start or end_time
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        agent_log = {
            "agent_name": agent_name,
            "method": method,
            "timestamp_start": start_time.isoformat(),
            "timestamp_end": end_time.isoformat(),
            "execution_time_ms": execution_time_ms,
            "output": output,
        }

        if input_data is not None:
            agent_log["input"] = input_data

        self.current_iteration_data["agents"].append(agent_log)
        logger.info(
            f"[{self.stage_name}] {agent_name}.{method}() completed in {execution_time_ms}ms"
        )

    def log_event(self, event_type: str, data: Any) -> None:
        """
        Log a stage event.

        Args:
            event_type: Type of event (e.g., "convergence", "error", "warning")
            data: Event data
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        self.log_data["events"].append(event)
        logger.info(f"[{self.stage_name}] Event: {event_type}")

    def complete(
        self,
        success: bool,
        final_output: Any = None,
        error: Any = None,
    ) -> None:
        """
        Complete the stage execution and save logs.

        Args:
            success: Whether the stage completed successfully
            final_output: Final output from the stage
            error: Error information if failed
        """
        self.end_time = datetime.now()
        self.log_data["timestamp_end"] = self.end_time.isoformat()

        if self.start_time:
            execution_time = (self.end_time - self.start_time).total_seconds() * 1000
            self.log_data["execution_time_ms"] = int(execution_time)

        # Save final iteration
        if self.current_iteration_data["agents"]:
            self.log_data["iterations"].append(self.current_iteration_data)

        self.log_data["success"] = success
        self.log_data["final_output"] = final_output

        if error:
            if isinstance(error, Exception):
                self.log_data["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                    "traceback": traceback.format_exc(),
                }
            else:
                self.log_data["error"] = error

        # Save logs to files
        self._save_logs()

        status = "succeeded" if success else "failed"
        logger.info(f"[{self.stage_name}] Stage execution {status}")

    def _save_logs(self) -> None:
        """Save logs to JSON, text, and HTML files."""
        # Save JSON log with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"{self.stage_name}_stage_{timestamp}.json"
        json_filepath = self.output_dir / json_filename

        with open(json_filepath, "w") as f:
            json.dump(self.log_data, f, indent=2, default=str)

        logger.info(f"Stage execution log saved to: {json_filepath}")

        # Save human-readable summary
        summary_filename = f"{self.stage_name}_stage_latest.txt"
        summary_filepath = self.output_dir / summary_filename
        self._save_summary(summary_filepath)

    def _save_summary(self, filepath: Path) -> None:
        """
        Save human-readable summary of stage execution.

        Args:
            filepath: Path to save summary
        """
        lines = [
            "=" * 80,
            f"Stage Execution Summary: {self.stage_name}",
            "=" * 80,
            f"Start Time: {self.log_data.get('timestamp_start')}",
            f"End Time: {self.log_data.get('timestamp_end')}",
            f"Execution Time: {self.log_data.get('execution_time_ms', 0)}ms",
            f"Success: {'✓ PASSED' if self.log_data.get('success') else '✗ FAILED'}",
            "",
        ]

        # Add input
        if self.log_data.get("input"):
            lines.append("Input:")
            lines.append("-" * 80)
            lines.append(json.dumps(self.log_data["input"], indent=2, default=str))
            lines.append("")

        # Add iterations
        iterations = self.log_data.get("iterations", [])
        if iterations:
            lines.append(f"Iterations: {len(iterations)}")
            lines.append("-" * 80)
            for iter_data in iterations:
                lines.append(f"\nIteration {iter_data['iteration']}:")
                for agent in iter_data.get("agents", []):
                    agent_name = agent.get("agent_name")
                    method = agent.get("method")
                    exec_time = agent.get("execution_time_ms")
                    lines.append(f"  - {agent_name}.{method}(): {exec_time}ms")
            lines.append("")

        # Add events
        events = self.log_data.get("events", [])
        if events:
            lines.append(f"Events: {len(events)}")
            lines.append("-" * 80)
            for event in events:
                event_type = event.get("type")
                event_data = event.get("data", {})
                lines.append(f"  - {event_type}: {json.dumps(event_data, default=str)}")
            lines.append("")

        # Add final output
        if self.log_data.get("final_output"):
            lines.append("Final Output:")
            lines.append("-" * 80)
            lines.append(json.dumps(self.log_data["final_output"], indent=2, default=str))
            lines.append("")

        # Add error if any
        if self.log_data.get("error"):
            lines.append("Error:")
            lines.append("-" * 80)
            error = self.log_data["error"]
            lines.append(f"Type: {error.get('type', 'Unknown')}")
            lines.append(f"Message: {error.get('message', 'No message')}")
            if error.get("traceback"):
                lines.append("\nTraceback:")
                lines.append(error["traceback"])
            lines.append("")

        # Write summary
        with open(filepath, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Stage execution summary saved to: {filepath}")
