"""Idea Development Stage implementation."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..agents.base_agent import BaseAgent
    from ..config import ModeConfig
    from ..context.shared_context import CompanyContext
    from ..utils.statistics import PipelineStatistics

from ..utils.stage_logger import StageExecutionLogger

logger = logging.getLogger(__name__)


@dataclass
class StageGate:
    """Quality gate criteria for stage completion."""

    name: str
    description: str
    threshold: float = 0.7
    required_fields: list[str] | None = None
    validator: str | None = None

    def evaluate(self, data: dict[str, Any]) -> tuple[bool, str]:
        """
        Evaluate if the gate criteria is met.

        Args:
            data: Data to evaluate

        Returns:
            Tuple of (passed, reason)
        """
        if self.validator == "legal_insights":
            return self._evaluate_legal_insights(data)
        elif self.validator == "idea_structure":
            return self._evaluate_idea_structure(data)
        elif self.validator == "research_complete":
            return self._evaluate_research_complete(data)
        elif self.required_fields:
            return self._evaluate_required_fields(data)
        else:
            return True, "No validation rules defined"

    def _evaluate_required_fields(self, data: dict[str, Any]) -> tuple[bool, str]:
        """Check that required fields are present and non-empty."""
        if not self.required_fields:
            return True, "No required fields"

        missing = []
        empty = []
        for field in self.required_fields:
            if field not in data:
                missing.append(field)
            elif not data[field]:
                empty.append(field)

        if missing:
            return False, f"Missing fields: {missing}"
        if empty:
            return False, f"Empty fields: {empty}"
        return True, "All required fields present"

    def _evaluate_legal_insights(self, data: dict[str, Any]) -> tuple[bool, str]:
        """Validate legal insights has correct structure (not idea data)."""
        legal = data.get("legal_insights", {})
        if not legal:
            return False, "legal_insights is empty or missing"

        # Check for idea fields that should NOT be in legal insights
        idea_fields = {
            "problem",
            "solution",
            "target_market",
            "value_proposition",
            "novelty",
            "market_size_estimate",
            "competitive_advantage",
        }
        idea_field_count = sum(1 for f in idea_fields if f in legal)
        if idea_field_count >= 3:
            return (
                False,
                f"legal_insights contains {idea_field_count} idea fields - wrong data type",
            )

        # Check for required legal fields
        required_legal = {"overall_risk_level", "blocking_issues", "recommendations", "key_risks"}
        missing = required_legal - set(legal.keys())
        if missing:
            return False, f"legal_insights missing required fields: {missing}"

        # Check key_risks has content
        key_risks = legal.get("key_risks", [])
        if not isinstance(key_risks, list) or len(key_risks) < 2:
            return (
                False,
                f"legal_insights key_risks has {len(key_risks) if isinstance(key_risks, list) else 0} items, need at least 2",
            )

        # Check for validation failure marker
        if legal.get("validation_failed"):
            return False, f"legal_insights validation failed: {legal.get('error', 'unknown error')}"

        return True, f"legal_insights valid with {len(legal)} analysis sections"

    def _evaluate_idea_structure(self, data: dict[str, Any]) -> tuple[bool, str]:
        """Validate idea has proper structure."""
        idea = data.get("idea", {})
        if not idea:
            return False, "idea is empty or missing"

        required = {"problem", "solution", "target_market", "value_proposition", "novelty"}
        missing = required - set(idea.keys())
        if missing:
            return False, f"idea missing required fields: {missing}"

        # Check fields are not empty
        empty = [f for f in required if not idea.get(f)]
        if empty:
            return False, f"idea has empty required fields: {empty}"

        return True, "idea structure valid"

    def _evaluate_research_complete(self, data: dict[str, Any]) -> tuple[bool, str]:
        """Validate research/validation is complete."""
        validation = data.get("final_validation", {})
        if not validation:
            return False, "final_validation is missing"

        required = {"recommendation", "risks", "opportunities"}
        missing = required - set(validation.keys())
        if missing:
            return False, f"validation missing fields: {missing}"

        rec = validation.get("recommendation", "").upper()
        if rec not in {"GO", "NO-GO", "PIVOT"}:
            return False, f"Invalid recommendation: {rec}"

        return True, f"Research complete with recommendation: {rec}"


class BaseStage(ABC):
    """Base class for all pipeline stages."""

    def __init__(
        self,
        name: str,
        context: CompanyContext,
        agents: dict[str, BaseAgent],
    ) -> None:
        """
        Initialize the stage.

        Args:
            name: Stage name
            context: Shared company context
            agents: Dictionary of available agents
        """
        self.name = name
        self.context = context
        self.agents = agents
        self.gates: list[StageGate] = []
        self._statistics: PipelineStatistics | None = None

    def set_statistics(self, statistics: PipelineStatistics) -> None:
        """
        Set the statistics collector for this stage.

        Args:
            statistics: PipelineStatistics instance
        """
        self._statistics = statistics

    def _record_agent_usage(
        self,
        agent_name: str,
        execution_time_ms: int,
    ) -> None:
        """
        Record agent usage in statistics.

        Args:
            agent_name: Name of the agent (e.g., "CEO", "Researcher", "LegalAdvisor")
            execution_time_ms: Execution time in milliseconds
        """
        if not self._statistics:
            return

        # Map display names to agent dictionary keys
        name_to_key = {
            "ceo": "ceo",
            "researcher": "researcher",
            "legaladvisor": "legal_advisor",
            "developer": "developer",
            "designer": "designer",
            "qa": "qa",
            "marketer": "marketer",
            "deckstrategist": "deck_strategist",
        }

        agent_key = name_to_key.get(agent_name.lower().replace("_", ""), agent_name.lower())
        agent = self.agents.get(agent_key)
        if not agent:
            return

        usage = agent.get_last_usage()
        if usage:
            self._statistics.record_agent_call(
                stage=self.name,
                agent=agent_name,
                model=agent.get_model_name(),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                execution_time_ms=execution_time_ms,
            )

    @abstractmethod
    def run(self) -> bool:
        """
        Execute the stage.

        Returns:
            True if stage completed successfully
        """
        pass

    def check_gates(self, data: dict[str, Any]) -> tuple[bool, list[tuple[str, bool, str]]]:
        """
        Check all quality gates.

        Args:
            data: Data to evaluate

        Returns:
            Tuple of (all_passed, list of (gate_name, passed, reason))
        """
        results = []
        all_passed = True

        for gate in self.gates:
            passed, reason = gate.evaluate(data)
            results.append((gate.name, passed, reason))
            if not passed:
                all_passed = False
                logger.warning(f"[{self.name}] Gate '{gate.name}' failed: {reason}")
            else:
                logger.info(f"[{self.name}] Gate '{gate.name}' passed: {reason}")

        return all_passed, results


class IdeaDevelopmentStage(BaseStage):
    """
    Stage 1: Idea Development

    Participants: CEO (lead), Researcher (validation)

    This stage combines idea generation and validation in an iterative loop:
    - CEO generates initial ideas based on chairman input
    - Researcher validates with market research, competitor analysis, risk assessment
    - CEO refines based on feedback until convergence

    Quality Gates:
    - Novelty score: Is it unique vs existing solutions?
    - Problem-solution fit: Clear problem + solution
    - Market size: Addressable market identified
    """

    def __init__(
        self,
        context: CompanyContext,
        agents: dict[str, BaseAgent],
        mode_config: ModeConfig | None = None,
    ) -> None:
        """Initialize the Idea Development stage."""
        super().__init__("idea_development", context, agents)

        from ..config import ModeConfig

        self.mode_config = mode_config or ModeConfig.standard()

        # Define quality gates (same for both modes)
        self.gates = [
            StageGate(
                name="idea_structure",
                description="Idea has all required fields (problem, solution, target_market, etc.)",
                validator="idea_structure",
            ),
            StageGate(
                name="research_complete",
                description="Market research completed with clear recommendation",
                validator="research_complete",
            ),
            StageGate(
                name="legal_readiness",
                description="Legal insights generated with proper structure (not idea data)",
                validator="legal_insights",
            ),
        ]

    def run(self) -> bool:
        """
        Execute the idea development stage.

        Flow:
        1. CEO generates initial ideas based on chairman input
        2. Researcher provides initial validation
        3. CEO and Researcher iterate to refine idea
        4. Final idea written to context

        Returns:
            True if idea passes quality gates
        """
        # Get chairman input
        chairman_input = self.context.get("chairman_input")
        if not chairman_input:
            logger.error("No chairman_input in context")
            return False

        # Initialize stage execution logger
        stage_logger = StageExecutionLogger(
            stage_name="idea_development", output_dir=Path("./test_results")
        )
        stage_logger.start(input_data={"chairman_input": chairman_input})

        try:
            # Generate initial idea (CEO)
            logger.info("[IdeaDev] Starting idea generation")
            stage_logger.start_iteration(0)
            stage_logger.log_agent_start("CEO", "generate_ideas")
            idea = self._generate_ideas(chairman_input)
            stage_logger.log_agent_complete("CEO", "generate_ideas", idea)
            # Record usage for statistics
            exec_time = stage_logger.current_iteration_data["agents"][-1]["execution_time_ms"]
            self._record_agent_usage("CEO", exec_time)
            logger.info("[IdeaDev] Initial idea generated")

            # Iterative refinement loop
            max_iterations = 3
            current_iteration = 0
            final_idea = idea
            validation = None

            legal_insights = None
            while current_iteration < max_iterations:
                # Researcher validates
                stage_logger.log_agent_start("Researcher", "research_idea")
                validation = self._validate_idea(final_idea)
                stage_logger.log_agent_complete("Researcher", "research_idea", validation)
                # Record usage for statistics
                exec_time = stage_logger.current_iteration_data["agents"][-1]["execution_time_ms"]
                self._record_agent_usage("Researcher", exec_time)
                logger.info(
                    f"[IdeaDev] Validation complete: {validation.get('recommendation', 'UNKNOWN')}"
                )

                # Legal Advisor analyzes legal risks
                stage_logger.log_agent_start("LegalAdvisor", "analyze_legal_risks")
                legal_insights = self._analyze_legal_risks(final_idea, validation)
                stage_logger.log_agent_complete(
                    "LegalAdvisor", "analyze_legal_risks", legal_insights
                )
                # Record usage for statistics
                exec_time = stage_logger.current_iteration_data["agents"][-1]["execution_time_ms"]
                self._record_agent_usage("LegalAdvisor", exec_time)
                logger.info(
                    f"[IdeaDev] Legal analysis complete: {legal_insights.get('overall_risk_level', 'UNKNOWN')}"
                )

                # Check convergence (includes legal assessment)
                if self._check_convergence(validation, legal_insights):
                    logger.info(f"[IdeaDev] Convergence achieved at iteration {current_iteration}")
                    stage_logger.log_event(
                        "convergence",
                        {
                            "iteration": current_iteration,
                            "recommendation": validation.get("recommendation"),
                            "legal_risk_level": legal_insights.get("overall_risk_level"),
                        },
                    )
                    break

                # CEO refines based on feedback (includes legal insights)
                current_iteration += 1
                if current_iteration < max_iterations:
                    logger.info(f"[IdeaDev] Starting refinement iteration {current_iteration}")
                    stage_logger.start_iteration(current_iteration)
                    stage_logger.log_agent_start("CEO", "refine_idea")
                    try:
                        final_idea = self._refine_idea(final_idea, validation, legal_insights)
                        stage_logger.log_agent_complete("CEO", "refine_idea", final_idea)
                        # Record usage for statistics
                        exec_time = stage_logger.current_iteration_data["agents"][-1][
                            "execution_time_ms"
                        ]
                        self._record_agent_usage("CEO", exec_time)
                        logger.info("[IdeaDev] Idea refined")
                    except Exception as e:
                        logger.warning(f"[IdeaDev] Refinement failed: {e}, using last good idea")
                        stage_logger.log_event(
                            "refinement_failed",
                            {
                                "iteration": current_iteration,
                                "error": str(e),
                            },
                        )
                        break

            # Store final results in context
            self.context.update("IdeaDevelopmentStage", "idea", final_idea, "idea_development")
            self.context.update(
                "IdeaDevelopmentStage", "iterations", current_iteration, "idea_development"
            )
            if legal_insights:
                self.context.update(
                    "IdeaDevelopmentStage", "legal_insights", legal_insights, "idea_development"
                )

            # Store in stage_outputs
            stage_output_data = {
                "idea": final_idea,
                "final_validation": validation,
                "legal_insights": legal_insights,
                "iterations": current_iteration,
                "converged": current_iteration < max_iterations,
            }

            # Run quality gates to validate output
            gates_passed, gate_results = self.check_gates(stage_output_data)

            # Store gate results
            stage_output_data["quality_gates"] = {
                "passed": gates_passed,
                "results": [
                    {"gate": name, "passed": passed, "reason": reason}
                    for name, passed, reason in gate_results
                ],
            }

            stage_outputs = self.context.get("stage_outputs", {})
            stage_outputs["idea_development"] = stage_output_data
            self.context.update("IdeaDevelopmentStage", "stage_outputs", stage_outputs)

            # Store iteration history in stage context for debugging
            self.context.set_stage_context("idea_development", "final_idea", final_idea)
            self.context.set_stage_context("idea_development", "final_validation", validation)
            self.context.set_stage_context("idea_development", "legal_insights", legal_insights)
            self.context.set_stage_context("idea_development", "iteration_count", current_iteration)

            # Log gate results
            if not gates_passed:
                failed_gates = [name for name, passed, _ in gate_results if not passed]
                logger.warning(f"[IdeaDev] Quality gates failed: {failed_gates}")
                stage_logger.log_event(
                    "quality_gates_failed",
                    {
                        "failed_gates": failed_gates,
                        "results": [
                            {"gate": name, "passed": passed, "reason": reason}
                            for name, passed, reason in gate_results
                        ],
                    },
                )
            else:
                logger.info("[IdeaDev] All quality gates passed")
                stage_logger.log_event(
                    "quality_gates_passed",
                    {
                        "results": [
                            {"gate": name, "passed": passed, "reason": reason}
                            for name, passed, reason in gate_results
                        ],
                    },
                )

            # Save execution log
            stage_logger.complete(
                success=gates_passed,
                final_output={
                    "idea": final_idea,
                    "iterations": current_iteration,
                    "converged": current_iteration < max_iterations,
                    "quality_gates_passed": gates_passed,
                },
            )

            if not gates_passed:
                logger.error("[IdeaDev] Stage failed quality gates")
                return False

            logger.info("[IdeaDev] Stage completed successfully")
            return True

        except Exception as e:
            logger.error(f"[IdeaDev] Stage failed: {e}")
            stage_logger.complete(success=False, error=e)

            # Still store partial results if available
            if "idea" in locals():
                self.context.update("IdeaDevelopmentStage", "idea", idea, "idea_development")

            return False

    def _generate_ideas(self, input_prompt: str) -> dict[str, Any]:
        """
        Generate initial ideas using CEO agent.

        This is iteration 0 - pure creative generation.

        Args:
            input_prompt: Chairman's input

        Returns:
            Structured idea dict

        Raises:
            RuntimeError: If CEO unavailable or generation fails
        """
        ceo = self.agents.get("ceo")
        if not ceo:
            raise RuntimeError("CEO agent not available")

        logger.info("[IdeaDev] CEO generating initial idea")
        idea = ceo.generate_ideas(input_prompt)

        # Validate idea structure
        required_fields = ["problem", "solution", "target_market", "value_proposition", "novelty"]
        missing = [f for f in required_fields if f not in idea]
        if missing:
            logger.warning(f"[IdeaDev] Idea missing fields: {missing}")
            # Continue with partial idea rather than failing

        # Store in context (CEO should do this, but ensure it's there)
        self.context.update("CEO", "idea", idea, "idea_development")

        return idea

    def _validate_idea(self, idea: dict[str, Any]) -> dict[str, Any]:
        """
        Validate an idea using Researcher agent.

        Researcher performs comprehensive market research and returns:
        - market_analysis
        - competitors
        - market_size
        - risks
        - opportunities
        - recommendation (GO/NO-GO/PIVOT)
        - reasoning

        Args:
            idea: The idea to validate

        Returns:
            Validation results dict

        Raises:
            RuntimeError: If Researcher unavailable or validation fails
        """
        researcher = self.agents.get("researcher")
        if not researcher:
            raise RuntimeError("Researcher agent not available")

        logger.info("[IdeaDev] Researcher validating idea")
        validation = researcher.research_idea(idea)

        # Store in context
        self.context.update("Researcher", "research", validation, "idea_development")

        return validation

    def _analyze_legal_risks(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze legal risks using Legal Advisor agent.

        Args:
            idea: The idea to analyze
            research: Market research findings from Researcher

        Returns:
            Legal insights dict with risk assessment and recommendations
        """
        legal_advisor = self.agents.get("legal_advisor")
        if not legal_advisor:
            logger.warning("[IdeaDev] Legal Advisor agent not available, skipping legal analysis")
            return {
                "overall_risk_level": "UNKNOWN",
                "blocking_issues": [],
                "recommendations": [],
            }

        logger.info("[IdeaDev] Legal Advisor analyzing legal risks")
        legal_insights = legal_advisor.analyze_legal_risks(idea, research)

        # Store in context
        self.context.update("LegalAdvisor", "legal_insights", legal_insights, "idea_development")

        return legal_insights

    def _refine_idea(
        self,
        idea: dict[str, Any],
        feedback: dict[str, Any],
        legal_insights: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Refine idea based on researcher feedback and legal analysis.

        CEO reviews the validation feedback and legal insights to refine the idea:
        - Identified market risks
        - Market gaps
        - Competitive weaknesses
        - Opportunities
        - Legal blocking issues
        - Compliance requirements

        Args:
            idea: The original idea
            feedback: Validation feedback from researcher
            legal_insights: Legal analysis from Legal Advisor

        Returns:
            Refined idea dict

        Raises:
            RuntimeError: If CEO unavailable or refinement fails
        """
        ceo = self.agents.get("ceo")
        if not ceo:
            raise RuntimeError("CEO agent not available")

        # Create refinement prompt for CEO (includes legal insights)
        refinement_prompt = self._create_refinement_prompt(idea, feedback, legal_insights)

        logger.info("[IdeaDev] CEO refining idea based on feedback")

        # Store feedback in context first
        self.context.update("IdeaDevelopmentStage", "refinement_feedback", feedback)

        # Call CEO to generate refined version
        refined_idea = ceo.generate_ideas(refinement_prompt)

        # Update context with refined idea
        self.context.update("CEO", "idea", refined_idea, "idea_development")

        return refined_idea

    def _create_refinement_prompt(
        self,
        idea: dict[str, Any],
        feedback: dict[str, Any],
        legal_insights: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a prompt for CEO to refine the idea.

        Args:
            idea: Original idea
            feedback: Researcher's validation feedback
            legal_insights: Legal Advisor's legal analysis

        Returns:
            Refinement prompt string
        """
        risks = feedback.get("risks", [])
        opportunities = feedback.get("opportunities", [])
        recommendation = feedback.get("recommendation", "UNKNOWN")
        reasoning = feedback.get("reasoning", "")

        # Build legal section if available
        legal_section = ""
        if legal_insights:
            blocking = legal_insights.get("blocking_issues", [])
            legal_recs = legal_insights.get("recommendations", [])[:5]
            overall_risk = legal_insights.get("overall_risk_level", "UNKNOWN")

            legal_section = f"""
Legal Risk Assessment:
- Overall Legal Risk: {overall_risk}

Blocking Legal Issues:
{self._format_legal_issues(blocking)}

Priority Legal Recommendations:
{self._format_legal_recommendations(legal_recs)}
"""

        prompt = f"""Refine this startup idea based on market research feedback and legal analysis.

Original Idea:
{json.dumps(idea, indent=2)}

Market Research Results:
- Recommendation: {recommendation}
- Reasoning: {reasoning}

Key Risks to Address:
{self._format_list(risks)}

Opportunities to Leverage:
{self._format_list(opportunities)}
{legal_section}
Please refine the idea to:
1. Mitigate the identified market risks
2. Capitalize on the opportunities
3. Strengthen competitive positioning
4. Improve market fit
5. Address blocking legal issues
6. Incorporate compliance requirements into the business model

Generate an improved version with the same structure (problem, solution, target_market, value_proposition, novelty, market_size_estimate, competitive_advantage).
"""
        return prompt

    def _check_convergence(
        self,
        validation: dict[str, Any],
        legal_insights: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if the idea has converged (is good enough to proceed).

        Convergence happens when:
        1. No critical legal blocking issues exist
        2. AND (Researcher recommends "GO" OR "PIVOT" with manageable risks)

        Args:
            validation: Validation dict from researcher
            legal_insights: Legal analysis from Legal Advisor

        Returns:
            True if converged
        """
        # Check for critical legal blocking issues first
        if legal_insights:
            blocking = legal_insights.get("blocking_issues", [])
            critical_legal = [
                issue
                for issue in blocking
                if isinstance(issue, dict) and issue.get("severity", "").upper() == "CRITICAL"
            ]
            if critical_legal:
                logger.info(
                    f"[IdeaDev] Found {len(critical_legal)} critical legal issues, continuing iteration"
                )
                return False

        recommendation = validation.get("recommendation", "").upper()

        # Direct GO recommendation
        if recommendation == "GO":
            return True

        # PIVOT with manageable risks
        if recommendation == "PIVOT":
            risks = validation.get("risks", [])
            # Check if all risks are low or medium severity
            high_severity_risks = [
                r for r in risks if isinstance(r, dict) and r.get("severity", "").upper() == "HIGH"
            ]
            if len(high_severity_risks) == 0:
                return True

        # NO-GO or insufficient data -> continue iterating
        return False

    def _format_list(self, items: list) -> str:
        """
        Format a list for prompt.

        Args:
            items: List of items to format

        Returns:
            Formatted string
        """
        if not items:
            return "None identified"

        if isinstance(items[0], dict):
            # Format dict items (e.g., risks with severity)
            return "\n".join(
                f"- {item.get('description', item.get('name', str(item)))}" for item in items
            )
        else:
            # Format string items
            return "\n".join(f"- {item}" for item in items)

    def _format_legal_issues(self, issues: list) -> str:
        """
        Format blocking legal issues for prompt.

        Args:
            issues: List of legal issue dicts

        Returns:
            Formatted string
        """
        if not issues:
            return "None identified"

        return "\n".join(
            f"- [{issue.get('severity', 'HIGH')}] {issue.get('issue', str(issue))}"
            for issue in issues
        )

    def _format_legal_recommendations(self, recommendations: list) -> str:
        """
        Format legal recommendations for prompt.

        Args:
            recommendations: List of recommendation dicts

        Returns:
            Formatted string
        """
        if not recommendations:
            return "None"

        return "\n".join(
            f"- [P{rec.get('priority', '?')}] {rec.get('action', str(rec))}"
            for rec in recommendations
        )
