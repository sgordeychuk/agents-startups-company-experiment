"""Legal Advisor Agent implementation."""

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

LEGAL_ADVISOR_SYSTEM_MESSAGE = """You are a Legal Advisor for a startup incubator. Analyze legal risks for startup ideas.

Key responsibilities:
- Identify blocking legal issues that could prevent operation
- Assess IP, regulatory, privacy, and liability risks
- Provide actionable recommendations with priorities

Use web_search() and legal_research() for research. Use severity levels: CRITICAL/HIGH/MEDIUM/LOW.

Output JSON with these required fields:
- overall_risk_level: CRITICAL/HIGH/MEDIUM/LOW
- blocking_issues: [{issue, severity, resolution_path}]
- key_risks: [{category, risk_level, summary}]
- recommendations: [{priority, action, category, blocking}]
"""


class LegalAdvisorAgent(BaseAgent):
    """
    Legal Advisor Agent responsible for legal due diligence.

    Competencies:
    - Intellectual property analysis
    - Regulatory compliance assessment
    - Privacy law expertise
    - Liability risk evaluation
    - Licensing requirements identification

    Authority:
    - Legal risk assessment
    - Compliance recommendations
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the Legal Advisor agent."""
        super().__init__(
            name="LegalAdvisor",
            role="Legal Advisor",
            system_message=LEGAL_ADVISOR_SYSTEM_MESSAGE,
            context=context,
        )
        self._web_search_tool = get_web_search_tool(config.llm.serper_api_key)
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

        tools = [
            self._web_search_async,
            self._legal_research_async,
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

    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get Legal Advisor-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "web_search",
                "description": "Search the web for legal information, regulations, and compliance requirements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for legal research",
                        }
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "legal_research",
                "description": "Conduct comprehensive legal research on a specific domain with multiple searches",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Legal topic to research (e.g., 'fintech regulations', 'healthcare data privacy')",
                        },
                        "jurisdiction": {
                            "type": "string",
                            "description": "Target jurisdiction (US, EU, global)",
                            "enum": ["US", "EU", "global"],
                        },
                    },
                    "required": ["topic"],
                },
            },
        ]

    async def _web_search_async(self, query: str) -> str:
        """
        Perform web search for legal information (async version).

        Args:
            query: Search query for legal research

        Returns:
            Formatted search results as string
        """
        logger.info(f"[LegalAdvisor] Web search requested: {query}")

        try:
            web_search = get_web_search_tool(config.llm.serper_api_key)
            results = web_search.search_and_format(query, num_results=5)
            logger.info("[LegalAdvisor] Web search completed successfully")
            return results

        except Exception as e:
            logger.error(f"[LegalAdvisor] Web search failed: {e}")
            return f"Web search failed: {str(e)}"

    async def _legal_research_async(self, topic: str, jurisdiction: str = "US") -> str:
        """
        Conduct comprehensive legal research on a topic with multiple searches.

        Args:
            topic: Legal topic to research
            jurisdiction: Target jurisdiction (US, EU, global)

        Returns:
            Formatted research findings synthesized from multiple searches
        """
        logger.info(
            f"[LegalAdvisor] Legal research requested: {topic} (jurisdiction: {jurisdiction})"
        )

        try:
            web_search = get_web_search_tool(config.llm.serper_api_key)

            search_queries = [
                f"{topic} legal regulations compliance {jurisdiction} 2025 2026",
                f"{topic} startup legal risks liability",
                f"{topic} data privacy GDPR CCPA requirements",
                f"{topic} intellectual property patents licensing",
            ]

            all_results = []
            for query in search_queries:
                try:
                    results = web_search.search_and_format(query, num_results=3)
                    all_results.append(f"\n## Search: {query}\n{results}")
                except Exception as e:
                    logger.warning(f"[LegalAdvisor] Search failed for '{query}': {e}")
                    all_results.append(f"\n## Search: {query}\nFailed: {str(e)}")

            synthesized = f"# Legal Research: {topic} ({jurisdiction})\n\n" + "\n".join(all_results)
            synthesized += f"\n\n---\nCompleted {len(all_results)} legal searches"

            logger.info(f"[LegalAdvisor] Legal research completed with {len(all_results)} searches")
            return synthesized

        except Exception as e:
            logger.error(f"[LegalAdvisor] Legal research failed: {e}")
            return f"Legal research failed: {str(e)}"

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
        try:
            parsed_value = json.loads(value)
            self.write_context(key, parsed_value)
            return f"Successfully updated {key} in shared context"
        except json.JSONDecodeError as e:
            return f"Failed to parse value as JSON: {e}"

    # Required fields for valid legal insights
    LEGAL_REQUIRED_FIELDS = {
        "overall_risk_level",
        "blocking_issues",
        "recommendations",
        "key_risks",
    }
    # Fields that indicate this is an idea, not legal insights
    IDEA_FIELDS = {
        "problem",
        "solution",
        "target_market",
        "value_proposition",
        "novelty",
        "market_size_estimate",
        "competitive_advantage",
    }

    def _is_valid_legal_insights(self, obj: dict[str, Any]) -> bool:
        """
        Validate that an object is legal insights, not idea data.

        Args:
            obj: Dictionary to validate

        Returns:
            True if the object is valid legal insights
        """
        if not isinstance(obj, dict):
            return False

        # Reject if it looks like an idea (has idea-specific fields)
        idea_field_count = sum(1 for f in self.IDEA_FIELDS if f in obj)
        if idea_field_count >= 3:
            logger.warning(f"[LegalAdvisor] Rejecting object with {idea_field_count} idea fields")
            return False

        # Must have required legal fields
        has_required = all(f in obj for f in self.LEGAL_REQUIRED_FIELDS)
        if not has_required:
            missing = self.LEGAL_REQUIRED_FIELDS - set(obj.keys())
            logger.warning(f"[LegalAdvisor] Missing required legal fields: {missing}")
            return False

        # key_risks must have at least 2 items
        key_risks = obj.get("key_risks", [])
        if not isinstance(key_risks, list) or len(key_risks) < 2:
            logger.warning(
                f"[LegalAdvisor] key_risks has {len(key_risks) if isinstance(key_risks, list) else 0} items, need at least 2"
            )
            return False

        return True

    def _extract_json_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Extract a valid legal insights JSON object from text.

        Only returns JSON that passes legal insights validation.
        Will NOT return idea data even if it's valid JSON.

        Args:
            text: Text that may contain JSON objects

        Returns:
            Parsed legal insights JSON or None if no valid legal JSON found
        """
        depth = 0
        start = -1
        candidates = []

        # Find all JSON objects in the text
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
                            candidates.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = -1

        # Return the first valid legal insights object
        for obj in candidates:
            if self._is_valid_legal_insights(obj):
                return obj

        logger.warning(
            f"[LegalAdvisor] No valid legal insights found in {len(candidates)} JSON candidates"
        )
        return None

    def _web_search(self, query: str) -> str:
        """Sync wrapper for web search."""
        import asyncio

        return asyncio.run(self._web_search_async(query))

    def _legal_research(self, topic: str, jurisdiction: str = "US") -> str:
        """Sync wrapper for legal research."""
        import asyncio

        return asyncio.run(self._legal_research_async(topic, jurisdiction))

    async def analyze_legal_risks_async(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze legal risks for a startup idea (async version).

        Args:
            idea: The startup idea to analyze
            research: Market research findings from Researcher

        Returns:
            Legal insights with risk assessment, blocking issues, and recommendations
        """
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Clear usage for fresh tracking
        self.clear_usage()

        risks_from_research = research.get("risks", [])
        target_market = idea.get("target_market", "general")
        solution = idea.get("solution", "")
        problem = idea.get("problem", "")

        logger.info("[LegalAdvisor] Step 1: Conducting legal research")
        research_prompt = f"""Analyze the legal risks for this startup idea:

IDEA:
{json.dumps(idea, indent=2)}

MARKET RESEARCH RISKS IDENTIFIED:
{json.dumps(risks_from_research, indent=2)}

Use legal_research() and web_search() to research:
1. Intellectual property considerations - existing patents, trademark availability
2. Regulatory requirements for this industry/market
3. Data privacy and protection obligations
4. Liability and insurance requirements
5. Licensing and permits needed
6. Industry-specific legal constraints

Focus on jurisdiction: US (primary), EU (secondary).

Conduct thorough legal research and summarize your findings with specific laws, regulations, and requirements."""

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

        logger.info(
            f"[LegalAdvisor] Step 1 complete: {len(research_findings)} chars of legal research"
        )

        logger.info("[LegalAdvisor] Step 2: Synthesizing legal insights")
        synthesis_prompt = f"""Research is COMPLETE. DO NOT search again.

Your findings:
{research_findings[:3500]}

Create legal insights JSON and call _write_context_async("legal_insights", <json>).

Required JSON structure:
{{
  "overall_risk_level": "CRITICAL/HIGH/MEDIUM/LOW",
  "blocking_issues": [{{"issue": "description", "severity": "CRITICAL/HIGH", "resolution_path": "how to fix"}}],
  "key_risks": [{{"category": "IP/Regulatory/Privacy/Liability/Licensing", "risk_level": "HIGH/MEDIUM/LOW", "summary": "brief description"}}],
  "recommendations": [{{"priority": 1-5, "action": "specific action", "category": "IP/Regulatory/Privacy/Liability/Licensing", "blocking": true/false}}]
}}

Include at least 3 key_risks covering different categories.
Call _write_context_async NOW."""

        step2_response = await self._autogen_agent.run(task=synthesis_prompt)
        self._record_usage(step2_response)

        legal_insights = self.read_context("legal_insights")

        # Validate that what's in context is actually legal insights, not idea data
        if legal_insights and not self._is_valid_legal_insights(legal_insights):
            logger.warning(
                "[LegalAdvisor] Context contains invalid legal_insights (possibly idea data), "
                "will try to parse from response"
            )
            legal_insights = None

        if not legal_insights:
            logger.warning(
                "[LegalAdvisor] Legal insights not found in context, parsing from response"
            )
            try:
                response_text = ""
                if hasattr(step2_response, "messages"):
                    for msg in step2_response.messages:
                        if hasattr(msg, "content"):
                            response_text += str(msg.content)
                else:
                    response_text = str(step2_response)

                legal_insights = self._extract_json_from_text(response_text)
                if legal_insights:
                    self.write_context("legal_insights", legal_insights)
                else:
                    raise ValueError("No valid legal insights JSON found in response")
            except Exception as e:
                logger.error(f"[LegalAdvisor] Failed to parse legal insights: {e}")
                legal_insights = {
                    "overall_risk_level": "UNKNOWN",
                    "blocking_issues": [],
                    "recommendations": [],
                    "error": str(e),
                    "validation_failed": True,
                }

        return legal_insights

    def analyze_legal_risks(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze legal risks for a startup idea (sync wrapper).

        Args:
            idea: The startup idea to analyze
            research: Market research findings from Researcher

        Returns:
            Legal insights with risk assessment, blocking issues, and recommendations
        """
        import asyncio

        return asyncio.run(self.analyze_legal_risks_async(idea, research))
