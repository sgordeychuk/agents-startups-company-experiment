"""Agent testing utilities for debugging and validation."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import config
from ..context import CompanyContext

logger = logging.getLogger(__name__)


class AgentTester:
    """
    Utility for testing individual agents in isolation.

    Captures all agent outputs, context changes, tool calls,
    and logs for debugging purposes.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        """
        Initialize the agent tester.

        Args:
            output_dir: Directory to save test results (default: ./test_results)
        """
        self.output_dir = output_dir or Path("./test_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_results: dict[str, Any] = {}

    def test_agent(
        self,
        agent: Any,
        test_name: str,
        test_function: str,
        test_input: dict[str, Any],
        context: CompanyContext | None = None,
    ) -> dict[str, Any]:
        """
        Test an agent by running a specific function with test input.

        Args:
            agent: The agent instance to test
            test_name: Name for this test (used in output filename)
            test_function: Name of the agent method to call
            test_input: Dictionary of arguments to pass to the function
            context: Optional context to use (creates fresh one if not provided)

        Returns:
            Test results dictionary with outputs, logs, and context changes
        """
        logger.info(f"Starting agent test: {test_name}")

        # Create or use provided context
        if context is None:
            context = CompanyContext()
            agent.set_context(context)

        # Record initial state
        initial_context = context.snapshot()

        # Prepare result container
        result = {
            "test_name": test_name,
            "agent_name": agent.name,
            "agent_role": agent.role,
            "test_function": test_function,
            "test_input": test_input,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "output": None,
            "error": None,
            "context_changes": [],
            "initial_context": initial_context,
            "final_context": None,
            "execution_time_ms": 0,
        }

        # Execute the test
        start_time = datetime.now()
        try:
            # Get the function from the agent
            if not hasattr(agent, test_function):
                raise AttributeError(f"Agent {agent.name} has no method '{test_function}'")

            func = getattr(agent, test_function)

            # Call the function with test input
            logger.info(f"Calling {agent.name}.{test_function}() with input: {test_input}")
            output = func(**test_input)

            result["output"] = output
            result["success"] = True
            logger.info(f"Test {test_name} completed successfully")

        except Exception as e:
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": self._format_exception(e),
            }
            logger.error(f"Test {test_name} failed: {e}")

        finally:
            end_time = datetime.now()
            result["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

            # Record final state
            result["final_context"] = context.snapshot()

            # Calculate context changes
            result["context_changes"] = self._get_context_diff(
                initial_context, result["final_context"]
            )

            # Save results
            self._save_results(test_name, result)

        return result

    def test_agent_conversation(
        self,
        agent: Any,
        test_name: str,
        messages: list[dict[str, str]],
        context: CompanyContext | None = None,
    ) -> dict[str, Any]:
        """
        Test an agent with a conversation (multiple messages).

        Args:
            agent: The agent instance to test
            test_name: Name for this test
            messages: List of messages to send (format: [{"role": "user", "content": "..."}])
            context: Optional context to use

        Returns:
            Test results with all responses
        """
        logger.info(f"Starting conversation test: {test_name}")

        # Create or use provided context
        if context is None:
            context = CompanyContext()
            agent.set_context(context)

        # Ensure agent has AutoGen agent created
        if not agent._autogen_agent:
            llm_config = {
                "model": config.llm.primary_model,
                "api_key": config.llm.anthropic_api_key,
                "api_type": "anthropic",
            }
            agent.create_autogen_agent(llm_config)

        # Record initial state
        initial_context = context.snapshot()

        result = {
            "test_name": test_name,
            "agent_name": agent.name,
            "agent_role": agent.role,
            "test_type": "conversation",
            "messages": messages,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "responses": [],
            "error": None,
            "initial_context": initial_context,
            "final_context": None,
            "execution_time_ms": 0,
        }

        start_time = datetime.now()
        try:
            # Send each message and collect responses
            for msg in messages:
                logger.info(f"Sending message: {msg['content'][:100]}...")
                response = agent._autogen_agent.generate_reply(messages=[msg])
                result["responses"].append(
                    {
                        "input": msg,
                        "output": response,
                    }
                )

            result["success"] = True
            logger.info(f"Conversation test {test_name} completed successfully")

        except Exception as e:
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": self._format_exception(e),
            }
            logger.error(f"Conversation test {test_name} failed: {e}")

        finally:
            end_time = datetime.now()
            result["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

            # Record final state
            result["final_context"] = context.snapshot()
            result["context_changes"] = self._get_context_diff(
                initial_context, result["final_context"]
            )

            # Save results
            self._save_results(test_name, result)

        return result

    def test_agent_tools(
        self,
        agent: Any,
        test_name: str,
        context: CompanyContext | None = None,
    ) -> dict[str, Any]:
        """
        Test all tools available to an agent.

        Args:
            agent: The agent instance to test
            test_name: Name for this test
            context: Optional context to use

        Returns:
            Test results with tool definitions and function map
        """
        logger.info(f"Testing agent tools: {test_name}")

        if context:
            agent.set_context(context)

        result = {
            "test_name": test_name,
            "agent_name": agent.name,
            "agent_role": agent.role,
            "test_type": "tools",
            "timestamp": datetime.now().isoformat(),
            "tools": [],
            "function_map": [],
            "success": True,
        }

        try:
            # Get tool definitions
            tools = agent.get_tools()
            result["tools"] = tools
            result["tool_count"] = len(tools)

            # Get function map
            function_map = agent.get_function_map()
            result["function_map"] = list(function_map.keys())
            result["function_count"] = len(function_map)

            logger.info(f"Agent has {len(tools)} tools and {len(function_map)} functions")

        except Exception as e:
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
            }
            result["success"] = False

        # Save results
        self._save_results(test_name, result)
        return result

    def _get_context_diff(
        self,
        initial: dict[str, Any],
        final: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Calculate differences between initial and final context.

        Args:
            initial: Initial context snapshot
            final: Final context snapshot

        Returns:
            List of changes
        """
        changes = []

        # Compare state changes
        initial_state = initial.get("state", {})
        final_state = final.get("state", {})

        for key in set(list(initial_state.keys()) + list(final_state.keys())):
            initial_value = initial_state.get(key)
            final_value = final_state.get(key)

            if initial_value != final_value:
                changes.append(
                    {
                        "type": "state",
                        "key": key,
                        "before": initial_value,
                        "after": final_value,
                    }
                )

        return changes

    def _format_exception(self, exc: Exception) -> str:
        """Format exception with traceback."""
        import traceback

        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    def _save_results(self, test_name: str, result: dict[str, Any]) -> None:
        """
        Save test results to file.

        Args:
            test_name: Name of the test
            result: Test results dictionary
        """
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Save as JSON
        with open(filepath, "w") as f:
            json.dump(result, f, indent=2, default=str)

        logger.info(f"Test results saved to: {filepath}")

        # Also save a summary
        summary_file = self.output_dir / f"{test_name}_latest.txt"
        self._save_summary(summary_file, result)

    def _save_summary(self, filepath: Path, result: dict[str, Any]) -> None:
        """
        Save human-readable summary of test results.

        Args:
            filepath: Path to save summary
            result: Test results dictionary
        """
        lines = [
            "=" * 80,
            f"Agent Test Summary: {result['test_name']}",
            "=" * 80,
            f"Agent: {result.get('agent_name')} ({result.get('agent_role')})",
            f"Timestamp: {result.get('timestamp')}",
            f"Success: {'✓ PASSED' if result.get('success') else '✗ FAILED'}",
            f"Execution Time: {result.get('execution_time_ms', 0)}ms",
            "",
        ]

        # Add test-specific info
        if result.get("test_function"):
            lines.append(f"Function Tested: {result['test_function']}")
            lines.append(f"Test Input: {json.dumps(result.get('test_input'), indent=2)}")

        if result.get("test_type") == "conversation":
            lines.append(f"Messages: {len(result.get('messages', []))}")
            lines.append(f"Responses: {len(result.get('responses', []))}")

        if result.get("test_type") == "tools":
            lines.append(f"Tools: {result.get('tool_count', 0)}")
            lines.append(f"Functions: {result.get('function_count', 0)}")

        lines.append("")

        # Add output
        if result.get("output"):
            lines.append("Output:")
            lines.append("-" * 80)
            lines.append(json.dumps(result["output"], indent=2, default=str))
            lines.append("")

        # Add responses for conversation tests
        if result.get("responses"):
            lines.append("Conversation:")
            lines.append("-" * 80)
            for i, resp in enumerate(result["responses"], 1):
                lines.append(f"\n[Message {i}]")
                lines.append(f"Input: {resp['input']['content'][:200]}...")
                lines.append(f"Output: {str(resp['output'])[:500]}...")
            lines.append("")

        # Add error if any
        if result.get("error"):
            lines.append("Error:")
            lines.append("-" * 80)
            lines.append(f"Type: {result['error']['type']}")
            lines.append(f"Message: {result['error']['message']}")
            lines.append("")

        # Add context changes
        if result.get("context_changes"):
            lines.append("Context Changes:")
            lines.append("-" * 80)
            for change in result["context_changes"]:
                lines.append(f"- {change['key']}: {change['before']} → {change['after']}")
            lines.append("")

        # Write summary
        with open(filepath, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Test summary saved to: {filepath}")


def quick_test_agent(
    agent: Any,
    method_name: str,
    test_input: dict[str, Any],
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Quick helper to test an agent method.

    Args:
        agent: Agent instance
        method_name: Method to call
        test_input: Input arguments
        output_dir: Optional output directory

    Returns:
        Test results
    """
    tester = AgentTester(output_dir=output_dir)
    test_name = f"{agent.name}_{method_name}"
    return tester.test_agent(
        agent=agent,
        test_name=test_name,
        test_function=method_name,
        test_input=test_input,
    )
