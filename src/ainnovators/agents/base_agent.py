"""Base agent class for the AI startup company."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..context.shared_context import CompanyContext


@dataclass
class UsageInfo:
    """Token usage information from an API response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.prompt_tokens + self.completion_tokens


def extract_usage_from_response(response: Any) -> UsageInfo:
    """
    Extract token usage from an AutoGen TaskResult response.

    Iterates through response.messages and sums up the models_usage
    attribute from each message.

    Args:
        response: AutoGen TaskResult object

    Returns:
        UsageInfo with aggregated token counts
    """
    total_prompt = 0
    total_completion = 0

    if hasattr(response, "messages"):
        for msg in response.messages:
            if hasattr(msg, "models_usage") and msg.models_usage is not None:
                usage = msg.models_usage
                if hasattr(usage, "prompt_tokens"):
                    total_prompt += usage.prompt_tokens or 0
                if hasattr(usage, "completion_tokens"):
                    total_completion += usage.completion_tokens or 0

    return UsageInfo(prompt_tokens=total_prompt, completion_tokens=total_completion)


class BaseAgent(ABC):
    """
    Base class for all agents in the AI startup company.
    Provides common functionality for context access and agent configuration.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_message: str,
        context: CompanyContext | None = None,
    ) -> None:
        """
        Initialize the base agent.

        Args:
            name: Agent name identifier
            role: Agent role description
            system_message: System prompt for the agent
            context: Shared company context
        """
        self.name = name
        self.role = role
        self.system_message = system_message
        self._context = context
        self._autogen_agent: Any = None
        self._last_usage: UsageInfo | None = None
        self._model_name: str = "unknown"

    def get_last_usage(self) -> UsageInfo | None:
        """Get the token usage from the last API call."""
        return self._last_usage

    def get_model_name(self) -> str:
        """Get the model name used by this agent."""
        return self._model_name

    def clear_usage(self) -> None:
        """Clear accumulated usage (call at start of method)."""
        self._last_usage = UsageInfo()

    def _record_usage(self, response: Any) -> None:
        """
        Extract and accumulate usage from an AutoGen response.

        Args:
            response: AutoGen TaskResult object
        """
        new_usage = extract_usage_from_response(response)
        if self._last_usage is None:
            self._last_usage = new_usage
        else:
            self._last_usage = UsageInfo(
                prompt_tokens=self._last_usage.prompt_tokens + new_usage.prompt_tokens,
                completion_tokens=self._last_usage.completion_tokens + new_usage.completion_tokens,
            )

    def set_context(self, context: CompanyContext) -> None:
        """
        Set the shared context for the agent.

        Args:
            context: The CompanyContext instance to use
        """
        self._context = context

    def read_context(self, key: str, default: Any = None) -> Any:
        """
        Read a value from shared context.

        Args:
            key: The key to read
            default: Default value if key not found

        Returns:
            The value from context or default
        """
        if self._context is None:
            raise RuntimeError("Context not set for agent")
        return self._context.get(key, default)

    def write_context(self, key: str, value: Any) -> str:
        """
        Write a value to shared context.

        Args:
            key: The key to write
            value: The value to write

        Returns:
            Confirmation message
        """
        if self._context is None:
            raise RuntimeError("Context not set for agent")
        self._context.update(self.name, key, value)
        return f"Updated {key} in shared context"

    @abstractmethod
    def create_autogen_agent(self, model_client: Any | None = None) -> Any:
        """
        Create and return the AutoGen agent instance using new API.

        Args:
            model_client: Model client (e.g., AnthropicChatCompletionClient)

        Returns:
            AutoGen AssistantAgent instance
        """
        pass

    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get the list of tools available to this agent.

        Returns:
            List of tool definitions
        """
        pass

    def get_function_map(self) -> dict[str, Any]:
        """
        Get the function map for context access.

        Returns:
            Dictionary mapping function names to implementations
        """
        return {
            "read_context": self.read_context,
            "write_context": self.write_context,
        }

    def get_context_functions(self) -> list[dict[str, Any]]:
        """
        Get standard context access function definitions.

        Returns:
            List of function definitions for context access
        """
        return [
            {
                "name": "read_context",
                "description": "Read from shared company context",
                "parameters": {
                    "type": "object",
                    "properties": {"key": {"type": "string"}},
                    "required": ["key"],
                },
            },
            {
                "name": "write_context",
                "description": "Write to shared company context",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "value": {"type": "object"},
                    },
                    "required": ["key", "value"],
                },
            },
        ]
