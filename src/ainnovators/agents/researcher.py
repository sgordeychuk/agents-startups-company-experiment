"""Researcher Agent implementation."""

import json
import logging
from typing import TYPE_CHECKING, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

from ..config import config
from ..utils import get_web_search_tool
from .base_agent import BaseAgent

if TYPE_CHECKING:
    from ..context.shared_context import CompanyContext

logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM_MESSAGE = """You are a market research analyst for an AI-powered startup incubator. Your role is to:
1. Validate startup ideas through comprehensive market research
2. Identify and analyze competitors in target markets
3. Calculate addressable market sizes (TAM/SAM/SOM)
4. Assess risks and challenges
5. Identify market opportunities

You have access to shared company context via read_context() and write_context().

When conducting research:
- Use web_search() and deep_research() tools extensively
- Be data-driven and cite specific sources when available
- Look for concrete numbers, statistics, and market data
- Identify at least 3 competitors for any market
- Calculate realistic market size estimates
- Document both risks and opportunities

When providing recommendations:
- Use "GO", "NO-GO", or "PIVOT" as decision recommendations
- Always provide clear reasoning based on research findings
- Consider market opportunity, competition, and feasibility
- Be honest about limitations and unknowns in the data

Structure research outputs as JSON with these fields:
- market_analysis: Comprehensive market overview
- competitors: List of competitor analyses (name, description, strengths, weaknesses)
- market_size: TAM/SAM/SOM estimates with sources
- risks: List of identified risks and challenges
- opportunities: List of market opportunities
- recommendation: GO/NO-GO/PIVOT decision
- reasoning: Detailed reasoning for recommendation
"""


class ResearcherAgent(BaseAgent):
    """
    Researcher Agent responsible for market research and validation.

    Competencies:
    - Market research
    - Competitive analysis
    - Data synthesis

    Authority:
    - Validation recommendations
    - Market sizing
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the Researcher agent."""
        super().__init__(
            name="Researcher",
            role="Market Research Analyst",
            system_message=RESEARCHER_SYSTEM_MESSAGE,
            context=context,
        )
        # Initialize web search tool
        self._web_search_tool = get_web_search_tool(config.llm.serper_api_key)
        # Set model name for statistics
        self._model_name = config.llm.primary_model

    def create_autogen_agent(
        self, model_client: AnthropicChatCompletionClient | None = None
    ) -> AssistantAgent:
        """
        Create the AutoGen agent instance using the new API.

        Args:
            model_client: Anthropic model client (creates one if not provided)

        Returns:
            AutoGen AssistantAgent instance
        """
        # Create model client if not provided
        if model_client is None:
            model_client = AnthropicChatCompletionClient(
                model=config.llm.primary_model,
                api_key=config.llm.anthropic_api_key,
                max_tokens=8192,  # Increase from default 4096
            )

        # Get tools (async functions)
        tools = [
            self._web_search_async,
            self._deep_research_async,
            self._read_context_async,
            self._write_context_async,
        ]

        # Create the agent
        self._autogen_agent = AssistantAgent(
            name=self.name,
            model_client=model_client,
            tools=tools,
            system_message=self.system_message,
            reflect_on_tool_use=False,  # Reduce API calls
        )

        return self._autogen_agent

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get Researcher-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "web_search",
                "description": "Search the web for market data, competitors, and trends",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for market data, competitors, or trends",
                        }
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "deep_research",
                "description": "Conduct comprehensive research on a topic with multiple searches",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Topic to research comprehensively",
                        },
                        "depth": {
                            "type": "string",
                            "description": "Research depth: shallow (2 searches), medium (4 searches), or deep (6 searches)",
                            "enum": ["shallow", "medium", "deep"],
                        },
                    },
                    "required": ["topic"],
                },
            },
        ]

    async def _web_search_async(self, query: str) -> str:
        """
        Perform web search using Serper API (async version for new autogen).

        Args:
            query: Search query to find market data, competitors, or trends

        Returns:
            Formatted search results as string
        """
        logger.info(f"[Researcher] Web search requested: {query}")

        try:
            # Get the web search tool instance
            web_search = get_web_search_tool(config.llm.serper_api_key)

            # Perform search and get formatted results
            results = web_search.search_and_format(query, num_results=5)

            logger.info("[Researcher] Web search completed successfully")
            return results

        except Exception as e:
            logger.error(f"[Researcher] Web search failed: {e}")
            return f"Web search failed: {str(e)}"

    async def _deep_research_async(self, topic: str, depth: str = "medium") -> str:
        """
        Conduct comprehensive research on a topic with multiple searches (async version).

        Args:
            topic: Topic to research comprehensively
            depth: Research depth (shallow/medium/deep) - controls number of searches

        Returns:
            Formatted research findings synthesized from multiple searches
        """
        logger.info(f"[Researcher] Deep research requested: {topic} (depth: {depth})")

        try:
            # Determine number of searches based on depth
            num_searches_map = {"shallow": 2, "medium": 4, "deep": 6}
            num_searches = num_searches_map.get(depth, 4)

            # Get the web search tool instance
            web_search = get_web_search_tool(config.llm.serper_api_key)

            # Conduct multiple searches with different angles
            search_queries = [
                f"{topic} overview",
                f"{topic} market trends 2025 2026",
                f"{topic} competitors companies",
                f"{topic} market size statistics",
                f"{topic} challenges risks",
                f"{topic} opportunities growth",
            ]

            # Limit to num_searches
            search_queries = search_queries[:num_searches]

            # Perform all searches
            all_results = []
            for query in search_queries:
                try:
                    results = web_search.search_and_format(query, num_results=3)
                    all_results.append(f"\n## Search: {query}\n{results}")
                except Exception as e:
                    logger.warning(f"[Researcher] Search failed for '{query}': {e}")
                    all_results.append(f"\n## Search: {query}\nFailed: {str(e)}")

            # Synthesize results
            synthesized = f"# Deep Research: {topic}\n\n" + "\n".join(all_results)
            synthesized += f"\n\n---\nCompleted {len(all_results)} searches at depth: {depth}"

            logger.info(f"[Researcher] Deep research completed with {len(all_results)} searches")
            return synthesized

        except Exception as e:
            logger.error(f"[Researcher] Deep research failed: {e}")
            return f"Deep research failed: {str(e)}"

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

    def _extract_market_size_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Extract market size data (TAM/SAM/SOM) from text.

        Args:
            text: Text that may contain market size JSON

        Returns:
            Market size dict or None if not found
        """
        # Look for JSON objects with TAM/SAM/SOM fields
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

                        # Check if this looks like market size data
                        if isinstance(obj, dict) and any(
                            key in obj for key in ["TAM", "SAM", "SOM", "tam", "sam", "som"]
                        ):
                            return obj
                    except json.JSONDecodeError:
                        pass

                    start = -1

        return None

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

        # First pass: look for research-specific objects
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

                        # Check if this looks like a research object
                        # (has expected fields like market_analysis, competitors, etc.)
                        if isinstance(obj, dict) and any(
                            key in obj
                            for key in ["market_analysis", "competitors", "market_size", "risks"]
                        ):
                            return obj
                    except json.JSONDecodeError:
                        # This wasn't valid JSON, continue searching
                        pass

                    start = -1

        # If no research-like object found, try to find any valid JSON object
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

    def _deep_research(self, topic: str, depth: str = "medium") -> str:
        """Sync wrapper for deep research."""
        import asyncio

        return asyncio.run(self._deep_research_async(topic, depth))

    async def research_idea_async(self, idea: dict[str, Any]) -> dict[str, Any]:
        """
        Research a startup idea comprehensively (async version).

        Args:
            idea: The startup idea to research

        Returns:
            Research findings with market_analysis, competitors, market_size, risks, opportunities, recommendation
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Clear usage for fresh tracking
        self.clear_usage()

        # STEP 1: Conduct comprehensive research
        logger.info("[Researcher] Step 1: Conducting comprehensive research")
        research_prompt = f"""Research this startup idea:

{json.dumps(idea, indent=2)}

Use _deep_research_async() and _web_search_async() to gather information on:
1. The problem space and target market (use deep_research)
2. Competitors - find at least 3-5 specific companies/products
3. Market size data and statistics
4. Industry risks and challenges
5. Market opportunities and trends

Conduct thorough research and summarize your findings with specific data, company names, numbers, and sources."""

        step1_response = await self._autogen_agent.run(task=research_prompt)
        self._record_usage(step1_response)

        # Extract research findings
        research_findings = ""
        if hasattr(step1_response, "messages"):
            for msg in step1_response.messages:
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    if not content.startswith("[Function"):
                        research_findings += content + "\n"
        else:
            research_findings = str(step1_response)

        logger.info(f"[Researcher] Step 1 complete: {len(research_findings)} chars of research")

        # STEP 2: Synthesize findings into structured output
        logger.info("[Researcher] Step 2: Synthesizing research findings")
        synthesis_prompt = f"""Your research is COMPLETE. You have enough data. DO NOT conduct any more searches.

Your research findings:
{research_findings[:3000]}

Your ONLY task now is to:
1. Structure the findings into a comprehensive JSON object
2. Call _write_context_async("research", <json_string>) with the JSON

DO NOT call _web_search_async or _deep_research_async - you already have the data you need.

The JSON object must have these 7 fields:
{{
  "market_analysis": "2-3 paragraph overview based on your research",
  "competitors": [
    {{"name": "...", "description": "...", "strengths": "...", "weaknesses": "..."}}
  ],
  "market_size": {{"TAM": "...", "SAM": "...", "SOM": "...", "sources": "..."}},
  "risks": ["risk1", "risk2", ...],
  "opportunities": ["opportunity1", "opportunity2", ...],
  "recommendation": "GO or NO-GO or PIVOT",
  "reasoning": "2-3 paragraphs explaining your recommendation"
}}

NOW - IMMEDIATELY call _write_context_async("research", <json_string>) with your structured JSON.
Do not ask for permission. Do not do more research. Just CALL THE FUNCTION NOW."""

        step2_response = await self._autogen_agent.run(task=synthesis_prompt)
        self._record_usage(step2_response)

        # Extract research from context
        research = self.read_context("research")

        if not research:
            logger.warning("[Researcher] Research not found in context, parsing from response")
            try:
                response_text = ""
                if hasattr(step2_response, "messages"):
                    for msg in step2_response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)
                else:
                    response_text = str(step2_response)

                research = self._extract_json_from_text(response_text)
                if research:
                    self.write_context("research", research)
                else:
                    raise ValueError("No valid research JSON found in response")
            except Exception as e:
                logger.error(f"[Researcher] Failed to parse research: {e}")
                raise

        return research

    def research_idea(self, idea: dict[str, Any]) -> dict[str, Any]:
        """
        Research a startup idea comprehensively (sync wrapper).

        Args:
            idea: The startup idea to research

        Returns:
            Research findings
        """
        import asyncio

        return asyncio.run(self.research_idea_async(idea))

    async def analyze_competitors_async(self, market: str) -> list[dict[str, Any]]:
        """
        Analyze competitors in a market (async version).

        Args:
            market: The target market to analyze

        Returns:
            List of competitor analyses
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # STEP 1: Find competitors through web searches
        logger.info(f"[Researcher] Step 1: Searching for competitors in {market}")
        search_prompt = f"""Find major competitors in the {market} market.

Use _web_search_async() to conduct 2-3 searches to identify:
- Leading companies and products in this market
- Their key features and offerings
- Market positioning and strengths
- Known weaknesses or gaps

Find at least 3-5 specific competitors. List the company names and what you learned about each."""

        step1_response = await self._autogen_agent.run(task=search_prompt)

        # Extract search findings
        search_findings = ""
        if hasattr(step1_response, "messages"):
            for msg in step1_response.messages:
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    if not content.startswith("[Function"):
                        search_findings += content + "\n"
        else:
            search_findings = str(step1_response)

        logger.info(
            f"[Researcher] Step 1 complete: {len(search_findings)} chars of competitor data"
        )

        # STEP 2: Structure competitor analysis
        logger.info("[Researcher] Step 2: Structuring competitor analysis")
        analysis_prompt = f"""Your research is COMPLETE. You have enough data. DO NOT conduct any more searches.

Your research findings:
{search_findings[:2000]}

Your ONLY task now is to:
1. Structure the findings into a JSON array
2. Call _write_context_async("competitors", <json_string>) with the JSON

DO NOT call _web_search_async or _deep_research_async - you already have the data you need.

The JSON array must have 3+ competitors based on what you found (Zogo, Cleo, Frich, PocketGuard, Acorns, Chime, etc.):

[
  {{
    "name": "Competitor Name",
    "description": "What they do (1-2 sentences)",
    "strengths": "Their key advantages",
    "weaknesses": "Their limitations",
    "market_position": "Market positioning"
  }}
]

NOW - IMMEDIATELY call _write_context_async("competitors", <json_string>) with your structured JSON array.
Do not ask for permission. Do not do more research. Just CALL THE FUNCTION NOW."""

        step2_response = await self._autogen_agent.run(task=analysis_prompt)

        # Extract competitors from context
        logger.info("[Researcher] Reading competitors from context...")
        competitors = self.read_context("competitors", [])
        logger.info(
            f"[Researcher] Competitors from context: {len(competitors) if isinstance(competitors, list) else 'not a list'}"
        )

        # Debug: check all context keys
        if hasattr(self._context, "state"):
            logger.info(f"[Researcher] Context keys: {list(self._context.state.keys())}")

        if not competitors:
            logger.warning("[Researcher] Competitors not found in context, parsing from response")
            try:
                response_text = ""
                if hasattr(step2_response, "messages"):
                    for msg in step2_response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)
                else:
                    response_text = str(step2_response)

                # Try to parse as JSON array
                import re

                matches = re.findall(r"\[[\s\S]*?\]", response_text)
                for match in matches:
                    try:
                        competitors = json.loads(match)
                        if isinstance(competitors, list) and competitors:
                            self.write_context("competitors", competitors)
                            break
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                logger.error(f"[Researcher] Failed to parse competitors: {e}")

        return competitors

    def analyze_competitors(self, market: str) -> list[dict[str, Any]]:
        """
        Analyze competitors in a market (sync wrapper).

        Args:
            market: The target market to analyze

        Returns:
            List of competitor analyses
        """
        import asyncio

        return asyncio.run(self.analyze_competitors_async(market))

    async def calculate_market_size_async(self, market: str) -> dict[str, Any]:
        """
        Calculate TAM/SAM/SOM for a market (async version).

        Args:
            market: The market to size

        Returns:
            Market sizing data with TAM/SAM/SOM estimates
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # STEP 1: Gather market data through web searches
        logger.info(f"[Researcher] Step 1: Gathering market data for: {market}")
        search_prompt = f"""Research the {market} market size.

Use _web_search_async() to conduct 3-5 searches to find:
1. Global or regional market size data and forecasts
2. Growth rates (CAGR) and projections
3. Market statistics and trends
4. Segment-specific data if available

Gather as much numerical data as possible. After your searches, write a summary of the key findings including all numbers, growth rates, and sources you found."""

        step1_response = await self._autogen_agent.run(task=search_prompt)

        # Extract search findings from response
        search_findings = ""
        if hasattr(step1_response, "messages"):
            for msg in step1_response.messages:
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    if not content.startswith("[Function"):
                        search_findings += content + "\n"
        else:
            search_findings = str(step1_response)

        logger.info(f"[Researcher] Step 1 complete: {len(search_findings)} chars of market data")

        # STEP 2: Calculate TAM/SAM/SOM based on gathered data
        logger.info("[Researcher] Step 2: Calculating TAM/SAM/SOM")
        calc_prompt = f"""Your research is COMPLETE. You have enough data. DO NOT conduct any more searches.

Your research findings:
{search_findings[:2000]}

Your ONLY task now is to:
1. Calculate TAM/SAM/SOM from the market data you found
2. Call _write_context_async("market_size", <json_string>) with the JSON

DO NOT call _web_search_async or _deep_research_async - you already have the data you need.

Calculate:
1. TAM (Total Addressable Market): The largest relevant market size you found
2. SAM (Serviceable Addressable Market): 10-30% of TAM for target segment
3. SOM (Serviceable Obtainable Market): 1-5% of SAM achievable in 3-5 years

JSON structure:
{{
  "TAM": "<dollar amount with source>",
  "SAM": "<calculated dollar amount with reasoning>",
  "SOM": "<calculated dollar amount with reasoning>",
  "sources": "<comma-separated list of sources>",
  "growth_rate": "<CAGR from research>",
  "notes": "<explain your calculations and assumptions>"
}}

NOW - IMMEDIATELY call _write_context_async("market_size", <json_string>) with your calculated market size.
Do not ask for permission. Do not do more research. Just CALL THE FUNCTION NOW."""

        step2_response = await self._autogen_agent.run(task=calc_prompt)

        # Extract market size from context
        market_size = self.read_context("market_size")

        if not market_size:
            # Fallback parsing
            logger.warning("[Researcher] Market size not found in context, parsing from response")
            try:
                response_text = ""
                if hasattr(step2_response, "messages"):
                    for msg in step2_response.messages:
                        if hasattr(msg, "content"):
                            content = str(msg.content)
                            if not content.startswith("[Function"):
                                response_text += content + "\n"
                else:
                    response_text = str(step2_response)

                logger.info(f"[Researcher] Market size response text length: {len(response_text)}")

                # Look for market size data specifically (TAM, SAM, SOM)
                market_size = self._extract_market_size_from_text(response_text)
                if market_size:
                    self.write_context("market_size", market_size)
                else:
                    logger.warning("[Researcher] Could not extract market size from response")
            except Exception as e:
                logger.error(f"[Researcher] Failed to parse market size: {e}")

        return market_size or {}

    def calculate_market_size(self, market: str) -> dict[str, Any]:
        """
        Calculate TAM/SAM/SOM for a market (sync wrapper).

        Args:
            market: The market to size

        Returns:
            Market sizing data
        """
        import asyncio

        return asyncio.run(self.calculate_market_size_async(market))

    async def assess_risks_async(self, idea: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Assess risks for a startup idea (async version).

        Args:
            idea: The startup idea to assess

        Returns:
            List of identified risks with severity and mitigation strategies
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # STEP 1: Research risks in the market/industry
        logger.info("[Researcher] Step 1: Researching risks for the idea")
        research_prompt = f"""Research risks for this startup idea:

{json.dumps(idea, indent=2)}

Use _web_search_async() to research 2-3 queries about:
- Common challenges in this market/industry
- Competitive threats and market dynamics
- Technical and operational hurdles
- Regulatory and compliance issues
- Financial viability concerns

Summarize the key risk areas you found with specific examples and data."""

        step1_response = await self._autogen_agent.run(task=research_prompt)

        # Extract research findings
        research_findings = ""
        if hasattr(step1_response, "messages"):
            for msg in step1_response.messages:
                if hasattr(msg, "content"):
                    content = str(msg.content)
                    if not content.startswith("[Function"):
                        research_findings += content + "\n"
        else:
            research_findings = str(step1_response)

        logger.info(
            f"[Researcher] Step 1 complete: {len(research_findings)} chars of risk research"
        )

        # STEP 2: Structure risk assessment
        logger.info("[Researcher] Step 2: Structuring risk assessment")
        assessment_prompt = f"""Your research is COMPLETE. You have enough data. DO NOT conduct any more searches.

Your research findings:
{research_findings[:2000]}

Your ONLY task now is to:
1. Structure the findings into a JSON array of risks
2. Call _write_context_async("risks", <json_string>) with the JSON

DO NOT call _web_search_async or _deep_research_async - you already have the data you need.

The JSON array must have 5+ risks based on your research:

[
  {{
    "category": "Market/Technical/Financial/Operational/Regulatory",
    "description": "Specific risk description (1-2 sentences)",
    "severity": "High/Medium/Low",
    "likelihood": "High/Medium/Low",
    "mitigation": "Mitigation strategies"
  }}
]

NOW - IMMEDIATELY call _write_context_async("risks", <json_string>) with your structured JSON array.
Do not ask for permission. Do not do more research. Just CALL THE FUNCTION NOW."""

        step2_response = await self._autogen_agent.run(task=assessment_prompt)

        # Extract risks from context
        risks = self.read_context("risks", [])

        if not risks:
            logger.warning("[Researcher] Risks not found in context, parsing from response")
            try:
                response_text = ""
                if hasattr(step2_response, "messages"):
                    for msg in step2_response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)
                else:
                    response_text = str(step2_response)

                # Try to parse as JSON array
                import re

                matches = re.findall(r"\[[\s\S]*?\]", response_text)
                for match in matches:
                    try:
                        risks = json.loads(match)
                        if isinstance(risks, list) and risks:
                            self.write_context("risks", risks)
                            break
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                logger.error(f"[Researcher] Failed to parse risks: {e}")

        return risks

    def assess_risks(self, idea: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Assess risks for a startup idea (sync wrapper).

        Args:
            idea: The startup idea to assess

        Returns:
            List of identified risks
        """
        import asyncio

        return asyncio.run(self.assess_risks_async(idea))
