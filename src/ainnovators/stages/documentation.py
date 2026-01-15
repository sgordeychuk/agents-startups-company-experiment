"""Pitch Stage implementation (formerly Documentation Stage)."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..agents.base_agent import BaseAgent
    from ..config import ModeConfig
    from ..context.shared_context import CompanyContext

from ..utils.stage_logger import StageExecutionLogger
from .idea_development import BaseStage, StageGate

logger = logging.getLogger(__name__)


class PitchStage(BaseStage):
    """
    Stage 4: Pitch (formerly Documentation)

    Sequential Workflow:
    1. Marketer develops marketing strategies
    2. Deck Strategist creates pitch deck incorporating strategies
    3. CEO performs final review

    Quality Gates:
    - Marketing completeness: 3-5 strategies with all required fields
    - Deck structure: All required slides present
    - Clarity: Understandable to non-technical audience
    - Completeness: Covers problem, solution, market, go-to-market
    """

    def __init__(
        self,
        context: CompanyContext,
        agents: dict[str, BaseAgent],
        mode_config: ModeConfig | None = None,
    ) -> None:
        """Initialize the Pitch stage."""
        super().__init__("pitch", context, agents)

        from ..config import ExecutionMode, ModeConfig

        self.mode_config = mode_config or ModeConfig.standard()

        # Adjust gates based on mode
        if self.mode_config.mode == ExecutionMode.EXTENDED:
            self.gates = [
                StageGate(
                    name="marketing_completeness",
                    description="3-5 marketing strategies with all required fields",
                    threshold=0.95,
                ),
                StageGate(
                    name="deck_structure",
                    description="All required slides present with enhanced content",
                    threshold=0.95,
                ),
                StageGate(
                    name="clarity",
                    description="Understandable to non-technical audience",
                    threshold=0.85,
                ),
                StageGate(
                    name="completeness",
                    description="Covers problem, solution, market, go-to-market",
                    threshold=0.9,
                ),
            ]
        else:
            self.gates = [
                StageGate(
                    name="marketing_completeness",
                    description="3-5 marketing strategies with all required fields",
                    threshold=0.9,
                ),
                StageGate(
                    name="deck_structure",
                    description="All required slides present",
                    threshold=0.9,
                ),
                StageGate(
                    name="clarity",
                    description="Understandable to non-technical audience",
                    threshold=0.7,
                ),
                StageGate(
                    name="completeness",
                    description="Covers problem, solution, market, go-to-market",
                    threshold=0.8,
                ),
            ]

    def run(self) -> bool:
        """
        Execute the pitch stage.

        Sequential Flow:
        1. Marketer develops go-to-market strategies
        2. Deck Strategist creates pitch deck with marketing integration
        3. CEO performs final review and approval

        Returns:
            True if pitch approved by CEO
        """
        idea = self.context.get("idea")
        research = self.context.get("research")
        prototype = self.context.get("prototype")

        if not idea or not research:
            logger.error("[Pitch] Missing required context: idea and research are required")
            return False

        if not prototype:
            prototype = self._build_prototype_fallback()
            self.context.update("PitchStage", "prototype", prototype, "pitch")
            if prototype.get("status") == "no_prototyping_data":
                logger.info("[Pitch] Running without prototyping data")
            else:
                logger.info("[Pitch] Using architecture/design data from prototyping")

        stage_logger = StageExecutionLogger(
            stage_name="pitch",
            output_dir=Path("./test_results"),
        )
        stage_logger.start(
            input_data={
                "idea": idea,
                "has_research": bool(research),
                "has_prototype": bool(prototype),
            }
        )

        try:
            # STEP 1: Marketer develops marketing strategies
            logger.info("[Pitch] Step 1: Marketing strategy development")
            stage_logger.log_agent_start("Marketer", "develop_marketing_strategies")

            marketing_strategies = self._develop_marketing_strategies()

            stage_logger.log_agent_complete(
                "Marketer",
                "develop_marketing_strategies",
                {"strategy_count": len(marketing_strategies)},
            )
            # Record usage for statistics
            exec_time = stage_logger.current_iteration_data["agents"][-1]["execution_time_ms"]
            self._record_agent_usage("Marketer", exec_time)
            logger.info(f"[Pitch] Marketing complete: {len(marketing_strategies)} strategies")

            # STEP 2: Deck Strategist creates pitch deck
            logger.info("[Pitch] Step 2: Pitch deck creation")
            stage_logger.log_agent_start("DeckStrategist", "create_pitch_deck")

            pitch_deck = self._create_pitch_deck(marketing_strategies)

            stage_logger.log_agent_complete("DeckStrategist", "create_pitch_deck", pitch_deck)
            # Record usage for statistics
            exec_time = stage_logger.current_iteration_data["agents"][-1]["execution_time_ms"]
            self._record_agent_usage("DeckStrategist", exec_time)
            logger.info("[Pitch] Pitch deck created")

            # Validate pitch deck quality before CEO review
            is_valid, validation_msg = self._validate_pitch_deck(pitch_deck)
            if not is_valid:
                logger.error(f"[Pitch] Pitch deck validation failed: {validation_msg}")
                stage_logger.complete(
                    success=False,
                    final_output={
                        "approved": False,
                        "validation_error": validation_msg,
                    },
                )
                return False

            # STEP 3: CEO final review
            logger.info("[Pitch] Step 3: CEO final review")
            stage_logger.log_agent_start("CEO", "final_review")

            ceo_decision = self._ceo_final_review(pitch_deck)

            stage_logger.log_agent_complete("CEO", "final_review", ceo_decision)
            # Record usage for statistics
            exec_time = stage_logger.current_iteration_data["agents"][-1]["execution_time_ms"]
            self._record_agent_usage("CEO", exec_time)
            logger.info(f"[Pitch] CEO decision: {ceo_decision.get('decision', 'UNKNOWN')}")

            # Store results in context
            self.context.update("PitchStage", "pitch", pitch_deck, "pitch")

            stage_outputs = self.context.get("stage_outputs", {})
            stage_outputs["pitch"] = {
                "marketing_strategies": marketing_strategies,
                "pitch_deck": pitch_deck,
                "ceo_decision": ceo_decision,
            }
            self.context.update("PitchStage", "stage_outputs", stage_outputs)

            decision_str = ceo_decision.get("decision", "").upper()
            approved = "APPROVE" in decision_str or decision_str == "GO"

            stage_logger.complete(
                success=approved,
                final_output={
                    "approved": approved,
                    "strategies": len(marketing_strategies),
                },
            )

            logger.info(f"[Pitch] Stage completed: {'approved' if approved else 'not approved'}")
            return approved

        except Exception as e:
            logger.error(f"[Pitch] Stage failed: {e}")
            stage_logger.complete(success=False, error=e)
            return False

    def _develop_marketing_strategies(self) -> list[dict[str, Any]]:
        """
        Have Marketer develop marketing strategies.

        Returns:
            List of marketing strategy dictionaries
        """
        marketer = self.agents.get("marketer")
        if not marketer:
            raise RuntimeError("Marketer agent not available")

        logger.info("[Pitch] Marketer developing strategies")
        strategies = marketer.develop_marketing_strategies()

        self.context.update("Marketer", "marketing_strategies", strategies, "pitch")
        return strategies

    def _create_pitch_deck(self, marketing_strategies: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Have Deck Strategist create pitch deck.

        Args:
            marketing_strategies: Marketing strategies from Marketer

        Returns:
            Pitch deck data
        """
        deck_strategist = self.agents.get("deck_strategist")
        if not deck_strategist:
            raise RuntimeError("Deck Strategist agent not available")

        aggregated_context = self._gather_context()
        logger.info("[Pitch] Deck Strategist creating pitch deck")

        pitch_deck = deck_strategist.create_pitch_deck(
            idea=aggregated_context["idea"],
            research=aggregated_context["research"],
            prototype=aggregated_context["prototype"],
            marketing_strategies=marketing_strategies,
            mode_config=self.mode_config,
        )

        return pitch_deck

    def _ceo_final_review(self, pitch: dict[str, Any]) -> dict[str, Any]:
        """
        CEO final review of pitch deck.

        Args:
            pitch: The pitch deck

        Returns:
            Final approval decision
        """
        ceo = self.agents.get("ceo")
        if not ceo:
            raise RuntimeError("CEO agent not available")

        logger.info("[Pitch] CEO performing final review")
        return ceo.final_review(pitch)

    def _gather_context(self) -> dict[str, Any]:
        """
        Gather all relevant context for pitch deck creation.

        Returns:
            Aggregated context including marketing strategies, designs, and architecture
        """
        prototype = self.context.get("prototype")
        if not prototype:
            prototype = self._build_prototype_fallback()

        return {
            "idea": self.context.get("idea"),
            "research": self.context.get("research"),
            "prototype": prototype,
            "marketing_strategies": self.context.get("marketing_strategies", []),
            "final_designs": self.context.get("final_designs", []),
            "architecture": self.context.get("architecture"),
            "decisions": self.context.get("decisions", []),
            "completed_stages": self.context.get("completed_stages", []),
        }

    def _validate_pitch_deck(self, pitch_deck: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate pitch deck meets quality gates.

        Args:
            pitch_deck: The pitch deck to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pitch_deck:
            return False, "Pitch deck is empty"

        slides = pitch_deck.get("slides", [])
        if len(slides) < 5:
            return False, f"Only {len(slides)} slides, need at least 5"

        placeholder_patterns = ["...", "TBD", "placeholder"]
        slides_with_issues = 0

        for slide in slides:
            title = str(slide.get("title", ""))
            content = str(slide.get("content", ""))

            if any(p in title for p in placeholder_patterns) or len(title) < 3:
                slides_with_issues += 1
            elif any(p in content for p in placeholder_patterns) or len(content) < 10:
                slides_with_issues += 1

        if slides_with_issues > len(slides) // 2:
            return (
                False,
                f"{slides_with_issues}/{len(slides)} slides have placeholder or missing content",
            )

        exec_summary = pitch_deck.get("executive_summary", "")
        if len(exec_summary) < 50 or "..." in exec_summary:
            return False, "Executive summary is missing or has placeholder content"

        logger.info(f"[Pitch] Pitch deck validated: {len(slides)} slides")
        return True, ""

    def _export_deliverables(self) -> dict[str, str]:
        """
        Export all deliverables to files.

        Returns:
            Dictionary of deliverable paths
        """
        # TODO: Implement deliverable export
        raise NotImplementedError("Deliverable export not yet implemented")

    def _build_prototype_fallback(self) -> dict[str, Any]:
        """
        Build fallback prototype data from available prototyping outputs.

        If no prototyping data exists, returns a minimal placeholder.

        Returns:
            Dict with available architecture/design data or minimal placeholder
        """
        stage_outputs = self.context.get("stage_outputs", {})
        prototyping_outputs = stage_outputs.get("prototyping", {})

        architecture = self.context.get("architecture") or prototyping_outputs.get("architecture")
        implementation_summary = self.context.get(
            "implementation_summary"
        ) or prototyping_outputs.get("implementation_summary")
        design_system = self.context.get("design_system") or prototyping_outputs.get(
            "design_system"
        )

        if not architecture and not implementation_summary and not design_system:
            return {
                "status": "no_prototyping_data",
                "note": "Pitch created from idea and research only - no prototype available",
            }

        return {
            "architecture": architecture,
            "implementation_summary": implementation_summary,
            "design_system": design_system,
            "status": "architecture_only",
            "note": "Full prototype not generated - using architecture and design system",
        }
