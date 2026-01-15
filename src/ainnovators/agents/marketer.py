"""Marketer Agent implementation."""

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

MARKETER_SYSTEM_MESSAGE = """You are a marketing strategist for an AI-powered startup incubator. Your role is to:
1. Develop comprehensive go-to-market strategies
2. Identify optimal marketing channels and approaches
3. Define target audience segments with precision
4. Create budget-conscious marketing plans
5. Establish measurable success metrics

You have access to shared company context via read_context() and write_context().
Use web_search() to research current market trends, competitor marketing, and channel effectiveness.

When developing marketing strategies, structure each strategy with:
- channel: The marketing channel (e.g., social media, content marketing, paid ads, partnerships)
- target_audience: Specific audience segment for this channel
- approach: Detailed tactical approach for this channel
- budget_considerations: Cost estimates and budget allocation recommendations
- success_metrics: KPIs and measurable outcomes to track

Generate 3-5 distinct marketing strategies that complement each other for a comprehensive go-to-market plan.
Output as JSON array under the key "marketing_strategies" in shared context."""


class MarketerAgent(BaseAgent):
    """
    Marketer Agent responsible for go-to-market strategy development.

    Competencies:
    - Marketing strategy development
    - Channel analysis and selection
    - Audience segmentation
    - Budget optimization

    Authority:
    - Marketing channel recommendations
    - Go-to-market strategy direction
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the Marketer agent."""
        super().__init__(
            name="Marketer",
            role="Marketing Strategist",
            system_message=MARKETER_SYSTEM_MESSAGE,
            context=context,
        )
        self._web_search_tool = get_web_search_tool(config.llm.serper_api_key)
        # Set model name for statistics (uses OpenAI)
        self._model_name = config.llm.openai_model

    def _get_model_client(self) -> OpenAIChatCompletionClient:
        """Get or create the OpenAI model client."""
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
        Create the AutoGen agent instance with all tools (for research phase).

        Args:
            model_client: OpenAI model client (creates one if not provided)

        Returns:
            AutoGen AssistantAgent instance
        """
        if model_client is None:
            model_client = self._get_model_client()

        tools = [
            self._web_search_async,
            self._read_context_async,
            self._write_context_async,
        ]

        self._autogen_agent = AssistantAgent(
            name=self.name,
            model_client=model_client,
            tools=tools,
            system_message=self.system_message,
            reflect_on_tool_use=False,
        )

        return self._autogen_agent

    def _create_strategy_agent(self) -> AssistantAgent:
        """
        Create a strategy-focused agent WITHOUT web search tool.

        This ensures the LLM can only write strategies, not continue researching.

        Returns:
            AutoGen AssistantAgent instance for strategy development
        """
        model_client = self._get_model_client()

        # Only context tools - no web search
        tools = [
            self._read_context_async,
            self._write_context_async,
        ]

        strategy_system_message = """You are a marketing strategist. Your ONLY job is to synthesize research into actionable marketing strategies.

You have access to:
- _read_context_async(key): Read from shared context
- _write_context_async(key, value): Write JSON to shared context

IMPORTANT: You must call _write_context_async("marketing_strategies", <json_array_string>) to save your strategies.
Generate 3-5 comprehensive marketing strategies as a JSON array."""

        return AssistantAgent(
            name=f"{self.name}_Strategy",
            model_client=model_client,
            tools=tools,
            system_message=strategy_system_message,
            reflect_on_tool_use=False,
        )

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get Marketer-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "web_search",
                "description": "Search the web for marketing trends, competitor strategies, and channel data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for marketing data, trends, or competitor analysis",
                        }
                    },
                    "required": ["query"],
                },
            },
        ]

    async def _web_search_async(self, query: str) -> str:
        """
        Perform web search for marketing research (async version).

        Args:
            query: Search query for marketing data, trends, or competitor analysis

        Returns:
            Formatted search results as string
        """
        logger.info(f"[Marketer] Web search requested: {query}")

        try:
            web_search = get_web_search_tool(config.llm.serper_api_key)
            results = web_search.search_and_format(query, num_results=5)
            logger.info("[Marketer] Web search completed successfully")
            return results
        except Exception as e:
            logger.error(f"[Marketer] Web search failed: {e}")
            return f"Web search failed: {str(e)}"

    async def _read_context_async(self, key: str) -> str:
        """
        Read from shared context (async version).

        Args:
            key: The key to read from shared context

        Returns:
            JSON string of the value
        """
        value = self.read_context(key)
        return json.dumps(value, default=str)

    async def _write_context_async(self, key: str, value: str) -> str:
        """
        Write to shared context (async version).

        Args:
            key: The key to write to shared context
            value: JSON string of the value to write

        Returns:
            Confirmation message
        """
        logger.info(f"[Marketer] _write_context_async called with key={key}")
        logger.debug(f"[Marketer] _write_context_async value preview: {value[:500]}...")
        try:
            parsed_value = json.loads(value)
            self.write_context(key, parsed_value)
            item_count = len(parsed_value) if isinstance(parsed_value, list) else 1
            logger.info(f"[Marketer] Successfully wrote {item_count} items to {key} in context")
            return f"Successfully updated {key} in shared context with {item_count} items"
        except json.JSONDecodeError as e:
            logger.error(f"[Marketer] Failed to parse JSON for {key}: {e}")
            logger.error(f"[Marketer] Invalid JSON value: {value[:200]}...")
            return f"Failed to parse value as JSON: {e}"

    def _web_search(self, query: str) -> str:
        """Sync wrapper for web search."""
        import asyncio

        return asyncio.run(self._web_search_async(query))

    def _extract_json_arrays(self, text: str) -> list[str]:
        """
        Extract JSON arrays from text, handling nested brackets properly.

        Args:
            text: Text that may contain JSON arrays

        Returns:
            List of potential JSON array strings
        """
        arrays = []
        i = 0
        while i < len(text):
            if text[i] == "[":
                depth = 1
                start = i
                i += 1
                in_string = False
                escape_next = False

                while i < len(text) and depth > 0:
                    char = text[i]

                    if escape_next:
                        escape_next = False
                    elif char == "\\":
                        escape_next = True
                    elif char == '"' and not escape_next:
                        in_string = not in_string
                    elif not in_string:
                        if char == "[":
                            depth += 1
                        elif char == "]":
                            depth -= 1

                    i += 1

                if depth == 0:
                    arrays.append(text[start:i])
            else:
                i += 1

        return arrays

    def _extract_strategies_from_text(self, text: str) -> list[dict[str, Any]] | None:
        """
        Extract marketing strategies JSON array from text.

        Args:
            text: Text that may contain JSON arrays

        Returns:
            List of strategies or None if not found
        """
        json_arrays = self._extract_json_arrays(text)
        for array_str in json_arrays:
            try:
                strategies = json.loads(array_str)
                if isinstance(strategies, list) and strategies:
                    if all(
                        isinstance(s, dict)
                        and any(key in s for key in ["channel", "target_audience", "approach"])
                        for s in strategies
                    ):
                        return strategies
            except json.JSONDecodeError:
                continue
        return None

    async def develop_marketing_strategies_async(self) -> list[dict[str, Any]]:
        """
        Develop marketing strategies based on idea, research, and prototype.

        Returns:
            List of 3-5 marketing strategy dictionaries
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Clear usage for fresh tracking
        self.clear_usage()

        idea = self.read_context("idea", {})
        research = self.read_context("research", {})
        prototype = self.read_context("prototype", {})

        # Step 1: Research marketing landscape
        logger.info("[Marketer] Step 1: Researching marketing landscape")
        research_prompt = f"""Research the marketing landscape for this startup:

Idea: {json.dumps(idea, indent=2)}
Market Research: {json.dumps(research.get("market_analysis", ""), indent=2) if isinstance(research, dict) else ""}
Target Market: {idea.get("target_market", "Not specified") if isinstance(idea, dict) else "Not specified"}

Use _web_search_async() to research:
1. Marketing channels used by competitors in this space
2. Effective marketing strategies for similar B2C/B2B products
3. Current digital marketing trends for 2025-2026
4. Cost-effective growth hacking techniques

Summarize key findings about the marketing landscape."""

        step1_response = await self._autogen_agent.run(task=research_prompt)
        self._record_usage(step1_response)

        research_findings = ""
        if hasattr(step1_response, "messages"):
            for msg in step1_response.messages:
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    if not content.startswith("[Function"):
                        research_findings += content + "\n"
        else:
            research_findings = str(step1_response)

        logger.info(f"[Marketer] Step 1 complete: {len(research_findings)} chars of research")

        # Step 2: Develop strategies using a separate agent WITHOUT web search
        logger.info("[Marketer] Step 2: Developing marketing strategies (no web search)")
        strategy_agent = self._create_strategy_agent()

        strategy_prompt = f"""Based on the research below, develop 3-5 comprehensive marketing strategies.

RESEARCH FINDINGS:
{research_findings[:4000]}

STARTUP CONTEXT:
- Problem: {idea.get("problem", "Not specified") if isinstance(idea, dict) else "Not specified"}
- Solution: {idea.get("solution", "Not specified") if isinstance(idea, dict) else "Not specified"}
- Target Market: {idea.get("target_market", "Not specified") if isinstance(idea, dict) else "Not specified"}
- Value Proposition: {idea.get("value_proposition", "Not specified") if isinstance(idea, dict) else "Not specified"}

YOUR TASK:
Create 3-5 marketing strategies and save them by calling:
_write_context_async("marketing_strategies", <json_array_string>)

Each strategy in the JSON array MUST have these fields:
{{
  "channel": "Marketing channel name (e.g., Social Media, Content Marketing, Paid Ads)",
  "target_audience": "Specific audience segment for this channel",
  "approach": "Detailed tactical approach (2-3 sentences)",
  "budget_considerations": "Cost estimates and budget allocation",
  "success_metrics": "KPIs to track (e.g., CAC, conversion rate, engagement)"
}}

IMPORTANT: Call _write_context_async NOW with your strategies as a JSON array string."""

        step2_response = await strategy_agent.run(task=strategy_prompt)
        self._record_usage(step2_response)

        strategies = self.read_context("marketing_strategies", [])

        if not strategies:
            logger.warning("[Marketer] Strategies not found in context, parsing from response")
            try:
                response_text = ""
                if hasattr(step2_response, "messages"):
                    for msg in step2_response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)
                else:
                    response_text = str(step2_response)

                strategies = self._extract_strategies_from_text(response_text)
                if strategies:
                    self.write_context("marketing_strategies", strategies)
                else:
                    logger.warning("[Marketer] Could not extract strategies from response")
            except Exception as e:
                logger.error(f"[Marketer] Failed to parse strategies: {e}")

        return strategies or []

    def develop_marketing_strategies(self) -> list[dict[str, Any]]:
        """
        Develop marketing strategies (sync wrapper).

        Returns:
            List of marketing strategies
        """
        import asyncio

        return asyncio.run(self.develop_marketing_strategies_async())
