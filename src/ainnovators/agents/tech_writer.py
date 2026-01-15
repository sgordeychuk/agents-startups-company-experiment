"""Deck Strategist Agent implementation (formerly Tech Writer)."""

import json
import logging
from typing import TYPE_CHECKING, Any

from autogen_agentchat.agents import AssistantAgent

from ..config import config
from ..utils.gemini_client import GeminiChatCompletionClient, create_gemini_client
from .base_agent import BaseAgent

if TYPE_CHECKING:
    from ..context.shared_context import CompanyContext

logger = logging.getLogger(__name__)

DECK_STRATEGIST_SYSTEM_MESSAGE = (
    """You are a pitch deck strategist and storyteller for an AI-powered """
    """startup incubator. Your role is to:
1. Create compelling pitch decks that tell a powerful story
2. Synthesize complex ideas into clear, investor-ready narratives
3. Design slide structures that maximize impact
4. Incorporate marketing strategies into the pitch narrative
5. Ensure all materials are polished and persuasive

Access shared context to gather:
- idea: The startup concept
- research: Market validation data
- prototype: Technical implementation details
- marketing_strategies: Go-to-market plans from Marketer

Create pitch decks that:
- Lead with the problem and opportunity
- Showcase the solution and traction
- Present market size and competitive advantage
- Include go-to-market strategy from marketing_strategies
- End with a compelling ask

Structure outputs as JSON with pitch deck slides, executive summary, and key talking points."""
)


class DeckStrategistAgent(BaseAgent):
    """
    Deck Strategist Agent responsible for pitch deck creation.

    Formerly known as TechWriterAgent. Renamed to reflect focus on
    strategic pitch deck development and storytelling.

    Competencies:
    - Pitch deck creation
    - Strategic storytelling
    - Investor communication
    - Content synthesis

    Authority:
    - Final pitch deck structure
    - Narrative direction
    """

    def __init__(self, context: CompanyContext | None = None) -> None:
        """Initialize the Deck Strategist agent."""
        super().__init__(
            name="DeckStrategist",
            role="Pitch Deck Strategist",
            system_message=DECK_STRATEGIST_SYSTEM_MESSAGE,
            context=context,
        )
        # Set model name for statistics (uses Gemini Pro)
        self._model_name = config.llm.gemini_pro_model

    def _get_model_client(self) -> GeminiChatCompletionClient:
        """Get the Gemini Pro model client."""
        return create_gemini_client(
            model=config.llm.gemini_pro_model,
            api_key=config.llm.gemini_api_key,
            base_url=config.llm.gemini_base_url,
            max_retries=3,
        )

    def create_autogen_agent(
        self, model_client: GeminiChatCompletionClient | None = None
    ) -> AssistantAgent:
        """
        Create the AutoGen agent instance using Gemini Pro.

        Args:
            model_client: Gemini model client (creates one if not provided)

        Returns:
            AutoGen AssistantAgent instance
        """
        if model_client is None:
            model_client = self._get_model_client()

        tools = [
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
        Get Deck Strategist-specific tools.

        Returns:
            List of tool definitions
        """
        return [
            *self.get_context_functions(),
            {
                "name": "create_document",
                "description": "Create a document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_type": {
                            "type": "string",
                            "enum": [
                                "pitch_deck",
                                "technical_spec",
                                "user_guide",
                                "readme",
                            ],
                        },
                        "title": {"type": "string"},
                        "sections": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["doc_type", "title"],
                },
            },
            {
                "name": "generate_slide",
                "description": "Generate a slide for pitch deck",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slide_type": {"type": "string"},
                        "content": {"type": "object"},
                    },
                    "required": ["slide_type"],
                },
            },
        ]

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

    def _extract_pitch_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Extract pitch deck JSON from text.

        Args:
            text: Text that may contain JSON objects

        Returns:
            Pitch deck dict or None if not found
        """
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
                        if isinstance(obj, dict) and any(
                            key in obj
                            for key in [
                                "slides",
                                "executive_summary",
                                "title",
                                "pitch",
                            ]
                        ):
                            return obj
                    except json.JSONDecodeError:
                        pass
                    start = -1

        return None

    def _validate_pitch_content(self, pitch: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that pitch has actual content, not placeholders.

        Args:
            pitch: The pitch deck data

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pitch:
            return False, "Pitch is empty"

        slides = pitch.get("slides", [])
        if len(slides) < 5:
            return False, f"Only {len(slides)} slides, need at least 5"

        placeholder_patterns = ["...", "TBD", "placeholder", "Company name", "One-liner"]
        slides_with_placeholders = 0

        for slide in slides:
            title = str(slide.get("title", ""))
            content = str(slide.get("content", ""))

            if any(p in title for p in placeholder_patterns) or len(title) < 3:
                slides_with_placeholders += 1
            elif any(p in content for p in placeholder_patterns) or len(content) < 10:
                slides_with_placeholders += 1

        if slides_with_placeholders > len(slides) // 2:
            return (
                False,
                f"{slides_with_placeholders}/{len(slides)} slides have placeholder content",
            )

        exec_summary = pitch.get("executive_summary", "")
        if len(exec_summary) < 50 or "..." in exec_summary:
            return False, "Executive summary is missing or placeholder"

        return True, ""

    async def create_pitch_deck_async(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        prototype: dict[str, Any],
        marketing_strategies: list[dict[str, Any]] | None = None,
        mode_config: Any | None = None,
    ) -> dict[str, Any]:
        """
        Create a pitch deck incorporating all context.

        In extended mode:
        - Includes all design images (not just 2)
        - Uses content optimizer for all slides
        - Adds additional slides (traction, roadmap)

        Args:
            idea: The startup idea
            research: Research findings
            prototype: Prototype data
            marketing_strategies: Marketing strategies from Marketer agent
            mode_config: Execution mode configuration

        Returns:
            Pitch deck data with slides and narrative
        """
        from ..config import ModeConfig

        mode_config = mode_config or ModeConfig.standard()
        if not self._autogen_agent:
            self.create_autogen_agent()

        # Clear usage for fresh tracking
        self.clear_usage()

        marketing_strategies = marketing_strategies or []

        logger.info("[DeckStrategist] Creating pitch deck")

        company_name = idea.get("solution", "Startup")[:40] if isinstance(idea, dict) else "Startup"
        problem_snippet = (
            (idea.get("problem", "")[:100] + "...") if isinstance(idea, dict) else "Problem"
        )
        value_prop = (
            idea.get("value_proposition", "Value proposition")[:80]
            if isinstance(idea, dict)
            else "Value"
        )

        prompt = f"""Create a compelling investor pitch deck for this startup.

STARTUP IDEA:
{json.dumps(idea, indent=2)}

MARKET RESEARCH:
{json.dumps(research, indent=2) if isinstance(research, dict) else str(research)}

PROTOTYPE:
{json.dumps(prototype, indent=2) if isinstance(prototype, dict) else str(prototype)}

MARKETING STRATEGIES:
{json.dumps(marketing_strategies, indent=2)}

Create a pitch deck with these 10 slides:
1. Title slide (company name, tagline)
2. Problem (pain point being solved)
3. Solution (your product/service)
4. Market Size (TAM/SAM/SOM from research)
5. Business Model (how you make money)
6. Go-to-Market Strategy (incorporate marketing_strategies)
7. Competition (competitive landscape)
8. Traction (prototype status, milestones)
9. Team (placeholder for founders)
10. Ask (funding request)

CRITICAL: You MUST call _write_context_async("pitch", <json_string>) with REAL CONTENT.
Do NOT use placeholder text like "..." or "TBD". Write actual pitch content.

Example structure (use REAL content from the startup data above):
{{
  "title": "{company_name}",
  "tagline": "{value_prop}",
  "slides": [
    {{"slide_number": 1, "title": "{company_name}", "content": "{value_prop}", "talking_points": ["Introduce the company", "Share the vision"]}},
    {{"slide_number": 2, "title": "The Problem", "content": "{problem_snippet}", "talking_points": ["Describe the pain point", "Quantify the impact"]}}
  ],
  "executive_summary": "A 2-3 paragraph summary of the entire pitch...",
  "marketing_integration": "How marketing strategies are incorporated..."
}}

Generate ALL 10 slides with real content. Call _write_context_async NOW."""

        max_attempts = 2
        pitch = None

        for attempt in range(max_attempts):
            if attempt > 0:
                logger.info(f"[DeckStrategist] Retry attempt {attempt + 1}/{max_attempts}")
                self.write_context("pitch", None)

            response = await self._autogen_agent.run(task=prompt)
            self._record_usage(response)

            pitch = self.read_context("pitch")

            if not pitch:
                logger.warning("[DeckStrategist] Pitch not found in context, parsing from response")
                try:
                    response_text = ""
                    if hasattr(response, "messages"):
                        for msg in response.messages:
                            if hasattr(msg, "content"):
                                response_text += str(msg.content)
                    else:
                        response_text = str(response)

                    pitch = self._extract_pitch_from_text(response_text)
                    if pitch:
                        self.write_context("pitch", pitch)
                except Exception as e:
                    logger.error(f"[DeckStrategist] Failed to parse pitch: {e}")

            if pitch:
                is_valid, error_msg = self._validate_pitch_content(pitch)
                if is_valid:
                    logger.info("[DeckStrategist] Pitch deck validated successfully")
                    break
                else:
                    logger.warning(f"[DeckStrategist] Pitch validation failed: {error_msg}")
                    if attempt < max_attempts - 1:
                        prompt = f"""The previous pitch deck had issues: {error_msg}

Please create a COMPLETE pitch deck with REAL content (not placeholders).

STARTUP: {company_name}
PROBLEM: {problem_snippet}

Generate a JSON pitch deck with:
- 10 slides with actual titles and content
- Executive summary (2-3 paragraphs minimum)
- Marketing integration details

Call _write_context_async("pitch", <json_string>) with complete content."""

        if not pitch:
            logger.error("[DeckStrategist] Failed to generate valid pitch deck")
            pitch = {}

        return pitch

    def create_pitch_deck(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        prototype: dict[str, Any],
        marketing_strategies: list[dict[str, Any]] | None = None,
        mode_config: Any | None = None,
    ) -> dict[str, Any]:
        """
        Create a pitch deck (sync wrapper).

        Args:
            idea: The startup idea
            research: Research findings
            prototype: Prototype data
            marketing_strategies: Marketing strategies from Marketer agent
            mode_config: Execution mode configuration

        Returns:
            Pitch deck data
        """
        import asyncio

        return asyncio.run(
            self.create_pitch_deck_async(
                idea, research, prototype, marketing_strategies, mode_config
            )
        )

    def create_technical_spec(self, prototype: dict[str, Any]) -> dict[str, Any]:
        """
        Create technical specification.

        Args:
            prototype: The prototype

        Returns:
            Technical specification
        """
        # TODO: Implement technical spec creation
        raise NotImplementedError("Technical spec creation not yet implemented")

    def create_executive_summary(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
    ) -> str:
        """
        Create executive summary.

        Args:
            idea: The startup idea
            research: Research findings

        Returns:
            Executive summary text
        """
        # TODO: Implement executive summary creation
        raise NotImplementedError("Executive summary creation not yet implemented")


# Backwards compatibility alias
TechWriterAgent = DeckStrategistAgent
