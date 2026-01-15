"""CEO Agent implementation."""

import json
import logging
from typing import TYPE_CHECKING, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..config import config
from ..utils import get_web_search_tool
from .base_agent import BaseAgent

if TYPE_CHECKING:
    from ..context.shared_context import CompanyContext

logger = logging.getLogger(__name__)

CEO_SYSTEM_MESSAGE = """You are the CEO of an AI-powered startup incubator. Your role is to:
1. Generate innovative startup ideas based on market trends and opportunities
2. Make go/no-go decisions on ideas based on research findings
3. Coordinate resources and priorities across the team
4. Ensure all work aligns with creating viable, investable businesses

You have access to shared company context via read_context() and write_context().
Always explain your reasoning for decisions.

When generating ideas, structure them with:
- problem: Clear problem statement
- solution: Proposed solution approach
- target_market: Target customer segment
- value_proposition: Key value to customers
- novelty: What makes this idea unique

When making decisions, always provide clear reasoning based on:
- Market opportunity and size
- Competitive landscape
- Technical feasibility
- Resource requirements
- Risk assessment"""


class CEOAgent(BaseAgent):
    """
    CEO Agent responsible for strategic vision and decision-making.

    Competencies:
    - Strategic vision
    - Resource allocation
    - Decision-making

    Authority:
    - Go/no-go on ideas
    - Resource allocation between stages
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the CEO agent."""
        super().__init__(
            name="CEO",
            role="Chief Executive Officer",
            system_message=CEO_SYSTEM_MESSAGE,
            context=context,
        )
        # Initialize web search tool
        self._web_search = get_web_search_tool(config.llm.serper_api_key)
        # Set model name for statistics (uses OpenAI)
        self._model_name = config.llm.openai_model

    def _get_model_client(self) -> OpenAIChatCompletionClient:
        """Get the OpenAI model client."""
        return OpenAIChatCompletionClient(
            model=config.llm.openai_model,
            api_key=config.llm.openai_api_key,
            model_info={
                "vision": True,
                "function_calling": True,
                "json_output": True,
                "family": "gpt-5",
            },
        )

    def create_autogen_agent(
        self, model_client: OpenAIChatCompletionClient | None = None
    ) -> AssistantAgent:
        """
        Create the AutoGen agent instance using the new API.

        Args:
            model_client: OpenAI model client (creates one if not provided)

        Returns:
            AutoGen AssistantAgent instance
        """
        if model_client is None:
            model_client = self._get_model_client()

        # Get tools (async functions)
        tools = [
            self._web_search_async,
            self._make_decision_async,
            self._read_context_async,
            self._write_context_async,
        ]

        # Create the agent
        self._autogen_agent = AssistantAgent(
            name=self.name,
            model_client=model_client,
            tools=tools,
            system_message=self.system_message,
            max_tool_iterations=3,  # Reduced from 5
            reflect_on_tool_use=False,  # Disable to reduce API calls
        )

        return self._autogen_agent

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get CEO-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "web_search",
                "description": "Search the web for market trends and opportunities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for market trends, competitors, or opportunities",
                        }
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "make_decision",
                "description": "Record a strategic decision with reasoning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "string",
                            "description": "The decision being made (e.g., 'GO', 'NO-GO', 'PIVOT')",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning for the decision",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence level (0-1)",
                            "minimum": 0,
                            "maximum": 1,
                        },
                    },
                    "required": ["decision", "reasoning"],
                },
            },
        ]

    async def _web_search_async(self, query: str) -> str:
        """
        Perform web search using Serper API (async version for new autogen).

        Args:
            query: Search query to find market trends, competitors, or opportunities

        Returns:
            Formatted search results as string
        """
        logger.info(f"[CEO] Web search requested: {query}")

        try:
            # Get the web search tool instance
            web_search = get_web_search_tool(config.llm.serper_api_key)

            # Perform search and get formatted results
            results = web_search.search_and_format(query, num_results=5)

            logger.info("[CEO] Web search completed successfully")
            return results

        except Exception as e:
            logger.error(f"[CEO] Web search failed: {e}")
            return f"Web search failed: {str(e)}"

    async def _make_decision_async(
        self, decision: str, reasoning: str, confidence: float = 0.8
    ) -> str:
        """
        Record a strategic decision in context (async version for new autogen).

        Args:
            decision: The decision being made (e.g., 'GO', 'NO-GO', 'PIVOT')
            reasoning: Detailed reasoning for the decision
            confidence: Confidence level (0-1)

        Returns:
            Confirmation message
        """
        decision_record = {
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "agent": self.name,
            "stage": self.read_context("current_stage"),
        }

        # Add to decisions list
        decisions = self.read_context("decisions", [])
        decisions.append(decision_record)
        self.write_context("decisions", decisions)

        logger.info(f"[CEO] Decision made: {decision} (confidence: {confidence})")
        return f"Decision recorded: {decision}"

    async def _read_context_async(self, key: str) -> str:
        """
        Read from shared context (async version for new autogen).

        Args:
            key: The key to read from shared context

        Returns:
            JSON string of the value
        """
        value = self.read_context(key)
        return json.dumps(value, default=str)

    async def _write_context_async(self, key: str, value: str) -> str:
        """
        Write to shared context (async version for new autogen).

        Args:
            key: The key to write to shared context
            value: JSON string of the value to write

        Returns:
            Confirmation message
        """
        try:
            # Parse JSON value
            parsed_value = json.loads(value)
            self.write_context(key, parsed_value)
            return f"Successfully updated {key} in shared context"
        except json.JSONDecodeError as e:
            return f"Failed to parse value as JSON: {e}"

    def _extract_json_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Extract a valid JSON object from text, handling multiple JSON objects.

        Args:
            text: Text that may contain JSON objects

        Returns:
            Parsed JSON object or None if no valid JSON found
        """
        # Try to find JSON objects by looking for balanced braces
        depth = 0
        start = -1

        for i, char in enumerate(text):
            if char == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    # Found a complete JSON object
                    try:
                        json_str = text[start : i + 1]
                        obj = json.loads(json_str)

                        # Check if this looks like an idea object
                        # (has expected fields like problem, solution, etc.)
                        if isinstance(obj, dict) and any(
                            key in obj
                            for key in ["problem", "solution", "target_market", "value_proposition"]
                        ):
                            return obj
                    except json.JSONDecodeError:
                        # This wasn't valid JSON, continue searching
                        pass

                    start = -1

        # If no idea-like object found, try to find any valid JSON object
        depth = 0
        start = -1

        for i, char in enumerate(text):
            if char == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        json_str = text[start : i + 1]
                        obj = json.loads(json_str)
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        pass

                    start = -1

        return None

    # Keep sync versions for backwards compatibility
    def _web_search(self, query: str) -> str:
        """Sync wrapper for web search."""
        import asyncio

        return asyncio.run(self._web_search_async(query))

    def _make_decision(self, decision: str, reasoning: str, confidence: float = 0.8) -> str:
        """Sync wrapper for make decision."""
        import asyncio

        return asyncio.run(self._make_decision_async(decision, reasoning, confidence))

    async def generate_ideas_async(self, chairman_input: str) -> dict[str, Any]:
        """
        Generate startup ideas based on chairman input (async version).

        Args:
            chairman_input: Direction from the chairman

        Returns:
            Generated idea structure
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Create prompt for idea generation
        prompt = f"""Based on this direction from the chairman: "{chairman_input}"

Generate a comprehensive startup idea. Structure your response as JSON with these fields:
- problem: Clear problem statement
- solution: Proposed solution approach
- target_market: Target customer segment
- value_proposition: Key value to customers
- novelty: What makes this idea unique
- market_size_estimate: Rough TAM estimate
- competitive_advantage: Key differentiators

Use _write_context_async() to save the idea under the "idea" key once generated."""

        # Generate the idea using the agent
        response = await self._autogen_agent.run(task=prompt)

        # Record usage for statistics
        self._record_usage(response)

        # Extract idea from context (agent should have written it)
        idea = self.read_context("idea")

        if not idea:
            # Fallback: try to parse from response
            logger.warning("[CEO] Idea not found in context, parsing from response")
            try:
                # Try to extract JSON from response messages
                response_text = ""
                if hasattr(response, "messages"):
                    for msg in response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)
                else:
                    response_text = str(response)

                # Try to find and parse valid JSON objects
                idea = self._extract_json_from_text(response_text)
                if idea:
                    self.write_context("idea", idea)
                else:
                    raise ValueError("No valid idea JSON found in response")
            except Exception as e:
                logger.error(f"[CEO] Failed to parse idea: {e}")
                raise

        return idea

    def generate_ideas(self, chairman_input: str) -> dict[str, Any]:
        """
        Generate startup ideas (sync wrapper).

        Args:
            chairman_input: Direction from the chairman

        Returns:
            Generated idea structure
        """
        import asyncio

        return asyncio.run(self.generate_ideas_async(chairman_input))

    async def review_research_async(self, research: dict[str, Any]) -> dict[str, Any]:
        """
        Review research findings and make go/no-go decision (async version).

        Args:
            research: Research data from researcher agent

        Returns:
            Decision with reasoning
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Get the original idea for context
        idea = self.read_context("idea", {})

        prompt = f"""Review this research and make a GO/NO-GO decision.

Original Idea:
{json.dumps(idea, indent=2)}

Research Findings:
{json.dumps(research, indent=2)}

Evaluate based on:
1. Market opportunity and size
2. Competitive landscape
3. Risk assessment
4. Alignment with our capabilities

Use _make_decision_async() to record your decision with reasoning. Decision should be "GO", "NO-GO", or "PIVOT"."""

        # Generate review
        response = await self._autogen_agent.run(task=prompt)

        # Record usage for statistics
        self._record_usage(response)

        # Extract the decision from context
        decisions = self.read_context("decisions", [])
        latest_decision = decisions[-1] if decisions else None

        if not latest_decision:
            logger.warning("[CEO] No decision found in context")
            # Create a default decision
            latest_decision = {
                "decision": "UNKNOWN",
                "reasoning": "No decision was recorded",
                "confidence": 0.0,
            }

        return latest_decision

    def review_research(self, research: dict[str, Any]) -> dict[str, Any]:
        """
        Review research findings (sync wrapper).

        Args:
            research: Research data from researcher agent

        Returns:
            Decision with reasoning
        """
        import asyncio

        return asyncio.run(self.review_research_async(research))

    async def final_review_async(self, pitch: dict[str, Any]) -> dict[str, Any]:
        """
        Perform final review of pitch deck (async version).

        Args:
            pitch: Pitch deck data

        Returns:
            Final approval decision
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Get full context
        idea = self.read_context("idea", {})
        research = self.read_context("research", {})
        prototype = self.read_context("prototype", {})

        prompt = f"""Perform a final review of the complete startup package.

Idea:
{json.dumps(idea, indent=2)}

Research:
{json.dumps(research, indent=2)}

Prototype:
{json.dumps(prototype, indent=2)}

Pitch Deck:
{json.dumps(pitch, indent=2)}

Evaluate:
1. Completeness of documentation
2. Alignment across all deliverables
3. Investment readiness
4. Team execution quality

Use _make_decision_async() to record final APPROVE or REJECT decision with detailed reasoning."""

        # Generate review
        response = await self._autogen_agent.run(task=prompt)

        # Record usage for statistics
        self._record_usage(response)

        # Extract the decision
        decisions = self.read_context("decisions", [])
        latest_decision = decisions[-1] if decisions else None

        if not latest_decision:
            logger.warning("[CEO] No final decision found in context")
            latest_decision = {
                "decision": "PENDING",
                "reasoning": "Review incomplete",
                "confidence": 0.0,
            }

        return latest_decision

    def final_review(self, pitch: dict[str, Any]) -> dict[str, Any]:
        """
        Perform final review of pitch deck (sync wrapper).

        Args:
            pitch: Pitch deck data

        Returns:
            Final approval decision
        """
        import asyncio

        return asyncio.run(self.final_review_async(pitch))
