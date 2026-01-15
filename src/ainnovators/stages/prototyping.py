"""Prototyping Stage implementation with QA validation and iteration loop."""

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..agents.base_agent import BaseAgent
    from ..config import ModeConfig
    from ..context.shared_context import CompanyContext

from .idea_development import BaseStage, StageGate

logger = logging.getLogger(__name__)


class PrototypingStage(BaseStage):
    """
    Stage 3: Prototyping

    Participants: Developer (lead), Designer, QA

    Flow:
    1. Developer designs architecture
    2. Designer creates UI/UX design specifications
    3. Developer creates prototype code
    4. Start Docker containers
    5. Developer-QA iteration loop (up to 3 times)
    6. Final quality gate evaluation

    Quality Gates:
    - Code quality: Linting passes, no critical issues
    - Feature completeness: Core value prop implemented
    - QA validation: No blocking bugs
    """

    def __init__(
        self,
        context: CompanyContext,
        agents: dict[str, BaseAgent],
        mode_config: ModeConfig | None = None,
    ) -> None:
        """Initialize the Prototyping stage."""
        super().__init__("prototyping", context, agents)

        from ..config import ExecutionMode, ModeConfig

        self.mode_config = mode_config or ModeConfig.standard()

        if self.mode_config.mode == ExecutionMode.EXTENDED:
            self.gates = [
                StageGate(
                    name="code_quality",
                    description="Linting passes, no critical issues",
                    threshold=0.85,
                ),
                StageGate(
                    name="feature_completeness",
                    description="Core value proposition implemented",
                    threshold=0.8,
                ),
                StageGate(
                    name="qa_validation",
                    description="No blocking bugs",
                    threshold=0.9,
                ),
            ]
        else:
            self.gates = [
                StageGate(
                    name="architecture_complete",
                    description="Architecture design completed",
                    threshold=0.7,
                ),
                StageGate(
                    name="design_system_complete",
                    description="Design system created",
                    threshold=0.7,
                ),
            ]

    def run(self) -> bool:
        """
        Execute the prototyping stage.

        Standard mode (research-focused):
        1. Developer designs architecture
        1.5. Developer generates implementation summary
        2. Designer creates design system only (colors, typography, spacing)
        2.5. Designer generates final design images (auto-derived screens)

        Extended mode (full prototype):
        1-2.5: Same as standard
        3. Developer creates prototype code (frontend + backend)
        4. Start Docker containers
        5. Developer-QA iteration loop (up to 3 times)
        6. Stop Docker containers

        Returns:
            True if stage completes successfully
        """
        mode_name = self.mode_config.mode.value.upper()
        logger.info(f"[Prototyping Stage] Starting prototyping stage ({mode_name} mode)")

        idea = self.context.get("idea")
        research = self.context.get("research")

        if not idea:
            logger.error("[Prototyping Stage] No idea found in context")
            return False

        if not research:
            logger.warning(
                "[Prototyping Stage] No research found - proceeding without research context"
            )

        try:
            # STEP 1: Architecture design (Developer)
            logger.info("[Prototyping Stage] Step 1: Designing architecture")
            start_time = time.time()
            architecture = self._design_architecture(idea, research)
            exec_time = int((time.time() - start_time) * 1000)
            self._record_agent_usage("Developer", exec_time)
            logger.info(f"[Prototyping Stage] Architecture created: {len(str(architecture))} chars")

            # STEP 1.5: Generate implementation summary (Developer)
            logger.info("[Prototyping Stage] Step 1.5: Generating implementation summary")
            start_time = time.time()
            implementation_summary = self._generate_implementation_summary(idea, architecture)
            exec_time = int((time.time() - start_time) * 1000)
            self._record_agent_usage("Developer", exec_time)
            logger.info(
                f"[Prototyping Stage] Implementation summary: {len(implementation_summary)} chars"
            )

            # STEP 2: Design system only (Designer) - no wireframes
            logger.info("[Prototyping Stage] Step 2: Creating design system only")
            start_time = time.time()
            design_system = self._create_design_system_only(idea, research, architecture)
            exec_time = int((time.time() - start_time) * 1000)
            self._record_agent_usage("Designer", exec_time)
            logger.info(
                f"[Prototyping Stage] Design system created: {len(str(design_system))} chars"
            )

            # STEP 2.5: Generate final design images (Designer)
            logger.info("[Prototyping Stage] Step 2.5: Creating final design images")
            start_time = time.time()
            final_designs = self._create_final_designs(idea, design_system, architecture)
            exec_time = int((time.time() - start_time) * 1000)
            self._record_agent_usage("Designer", exec_time)
            logger.info(f"[Prototyping Stage] Final designs created: {len(final_designs)} images")

            # Initialize stage output data
            stage_output_data: dict[str, Any] = {
                "architecture": architecture,
                "implementation_summary": implementation_summary,
                "design_system": design_system,
                "final_designs": final_designs,
            }

            prototype = None

            # EXTENDED MODE: Full prototype generation
            if self.mode_config.enable_code_generation:
                logger.info("[Prototyping Stage] EXTENDED MODE: Generating full prototype")

                # STEP 3: Create prototype (Developer)
                logger.info("[Prototyping Stage] Step 3: Creating prototype code")
                start_time = time.time()
                prototype = self._create_prototype(architecture, design_system)
                exec_time = int((time.time() - start_time) * 1000)
                self._record_agent_usage("Developer", exec_time)
                logger.info(
                    f"[Prototyping Stage] Prototype created: {prototype.get('files_generated', 0)} files"
                )
                logger.info(
                    f"[Prototyping Stage] Prototype directory: {prototype.get('directory')}"
                )
                stage_output_data["prototype"] = prototype

                # STEP 4: Start Docker containers (if enabled) with retry loop
                docker_started = False
                if self.mode_config.enable_docker:
                    logger.info("[Prototyping Stage] Step 4: Starting Docker containers")
                    docker_started = self._start_docker_with_retries(prototype, max_attempts=3)
                    if not docker_started:
                        logger.error(
                            "[Prototyping Stage] Failed to start Docker containers after all retries"
                        )
                        logger.warning("[Prototyping Stage] Continuing without QA validation")

                # STEP 5: Developer-QA iteration loop (if enabled)
                if self.mode_config.enable_qa_iteration and docker_started:
                    logger.info("[Prototyping Stage] Step 5: Developer-QA iteration loop")
                    qa_passed = self._run_qa_iteration_loop(
                        prototype, design_system, max_iterations=3
                    )

                    stage_output_data["qa_results"] = self.context.get("qa_results")
                    stage_output_data["qa_bugs"] = self.context.get("qa_bugs")

                    # STEP 6: Final quality gate evaluation
                    if qa_passed:
                        logger.info("[Prototyping Stage] All quality gates passed")
                    else:
                        logger.warning(
                            "[Prototyping Stage] Quality gates not fully passed after max iterations"
                        )

                # Stop Docker containers
                if docker_started and prototype:
                    logger.info("[Prototyping Stage] Stopping Docker containers")
                    self._stop_docker(prototype)
            else:
                logger.info("[Prototyping Stage] STANDARD MODE: Skipping prototype code generation")

            # Store in stage_outputs for frontend display
            stage_outputs = self.context.get("stage_outputs", {})
            stage_outputs["prototyping"] = stage_output_data
            self.context.update("PrototypingStage", "stage_outputs", stage_outputs)

            logger.info(f"[Prototyping Stage] Prototyping stage complete ({mode_name} mode)")
            return True

        except Exception as e:
            logger.error(f"[Prototyping Stage] Failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _design_architecture(
        self, idea: dict[str, Any], research: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Design system architecture using Developer agent.

        Args:
            idea: The startup idea
            research: Optional research findings

        Returns:
            Architecture design
        """
        developer = self.agents.get("developer")
        if not developer:
            raise ValueError("Developer agent not available")

        architecture = developer.design_architecture(idea, research)

        self.context.update(self.name, "architecture", architecture)

        return architecture

    def _create_prototype(
        self,
        architecture: dict[str, Any],
        design: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create the prototype using Developer agent.

        Args:
            architecture: System architecture
            design: Design specifications

        Returns:
            Prototype data including directory path and file count
        """
        developer = self.agents.get("developer")
        if not developer:
            raise ValueError("Developer agent not available")

        experiment_dir = self.context.get("experiment_dir")
        if not experiment_dir:
            from ..config import config

            experiment_dir = str(config.storage.experiments_dir / "prototype_run")

        prototype = developer.create_prototype(architecture, design, experiment_dir)

        self.context.update(self.name, "prototype", prototype)

        return prototype

    def _create_design(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        architecture: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create UI/UX design using Designer agent.

        Args:
            idea: The startup idea
            research: Research findings
            architecture: Optional system architecture

        Returns:
            Design artifacts
        """
        designer = self.agents.get("designer")
        if not designer:
            raise ValueError("Designer agent not available")

        design = designer.create_design(idea, research, architecture)

        self.context.update(self.name, "design", design)

        return design

    def _generate_implementation_summary(
        self, idea: dict[str, Any], architecture: dict[str, Any]
    ) -> str:
        """
        Generate implementation summary using Developer agent.

        Args:
            idea: The startup idea
            architecture: The designed architecture

        Returns:
            Text summary of implementation approach
        """
        developer = self.agents.get("developer")
        if not developer:
            raise ValueError("Developer agent not available")

        summary = developer.generate_implementation_summary(idea, architecture)
        self.context.update(self.name, "implementation_summary", summary)
        return summary

    def _create_design_system_only(
        self,
        idea: dict[str, Any],
        research: dict[str, Any],
        architecture: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create design system only (colors, typography, spacing) - no wireframes.

        Args:
            idea: The startup idea
            research: Research findings
            architecture: Optional system architecture

        Returns:
            Design system (colors, typography, spacing only)
        """
        designer = self.agents.get("designer")
        if not designer:
            raise ValueError("Designer agent not available")

        design_system = designer.create_design_system_only(idea, research, architecture)
        self.context.update(self.name, "design_system", design_system)
        return design_system

    def _create_final_designs(
        self,
        idea: dict[str, Any],
        design_system: dict[str, Any],
        architecture: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Create final design images using Designer agent.

        Auto-derives screens from the idea and generates consistent design images
        using the design system colors. In extended mode, generates more screens
        and mobile variants.

        Args:
            idea: The startup idea
            design_system: Design system with colors, typography, spacing
            architecture: Optional technical architecture

        Returns:
            List of generated design metadata
        """
        designer = self.agents.get("designer")
        if not designer:
            logger.warning("[Prototyping Stage] Designer agent not available for final designs")
            return []

        experiment_dir = self.context.get("experiment_dir")
        final_designs = designer.create_final_designs_light(
            idea, design_system, architecture, experiment_dir, self.mode_config
        )

        self.context.update(self.name, "final_designs", final_designs)

        return final_designs

    def _start_docker(self, prototype: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Start Docker containers for the prototype.

        Args:
            prototype: Prototype metadata with directory path

        Returns:
            Tuple of (success, error_details). error_details contains phase, stderr, etc.
        """
        from ..utils.docker_manager import DockerManager

        prototype_dir = prototype.get("directory")
        if not prototype_dir:
            logger.error("[Prototyping Stage] No prototype directory found")
            return False, {"phase": "init", "error": "No prototype directory found"}

        docker = DockerManager(prototype_dir)

        logger.info("[Prototyping Stage] Building Docker images...")
        if not docker.build():
            error = docker.get_last_error()
            error["phase"] = "build"
            logger.error("[Prototyping Stage] Docker build failed")
            return False, error

        logger.info("[Prototyping Stage] Starting Docker containers...")
        if not docker.start():
            error = docker.get_last_error()
            error["phase"] = "start"
            logger.error("[Prototyping Stage] Docker start failed")
            return False, error

        logger.info("[Prototyping Stage] Waiting for services to be ready...")
        time.sleep(15)

        status = docker.status()
        if not status.get("running", False):
            logger.error("[Prototyping Stage] Docker containers not running")
            return False, {
                "phase": "healthcheck",
                "error": "Containers not running after startup",
                "status": status,
            }

        logger.info("[Prototyping Stage] Docker containers started successfully")
        logger.info("[Prototyping Stage] Frontend: http://localhost:3000")
        logger.info("[Prototyping Stage] Backend: http://localhost:8000")

        return True, {}

    def _start_docker_with_retries(
        self,
        prototype: dict[str, Any],
        max_attempts: int = 3,
    ) -> bool:
        """
        Start Docker with retry loop. Developer agent fixes issues on failure.

        Args:
            prototype: Prototype metadata with directory path
            max_attempts: Maximum number of attempts (default 3)

        Returns:
            True if Docker started successfully
        """
        developer = self.agents.get("developer")

        for attempt in range(1, max_attempts + 1):
            logger.info(f"[Prototyping Stage] Docker start attempt {attempt}/{max_attempts}")

            success, error_details = self._start_docker(prototype)

            if success:
                return True

            error_phase = error_details.get("phase", "unknown")
            logger.error(f"[Prototyping Stage] Docker failed at {error_phase} phase")

            if attempt >= max_attempts:
                logger.error(f"[Prototyping Stage] Docker failed after {max_attempts} attempts")
                break

            if developer:
                logger.info("[Prototyping Stage] Developer fixing Docker issues...")
                start_time = time.time()
                fix_result = developer.fix_docker_issues(prototype, error_details)
                exec_time = int((time.time() - start_time) * 1000)
                self._record_agent_usage("Developer", exec_time)

                if fix_result.get("success"):
                    files_fixed = len(fix_result.get("files_modified", []))
                    logger.info(f"[Prototyping Stage] Fixed {files_fixed} files")
                    diagnosis = fix_result.get("diagnosis", "N/A")
                    logger.info(f"[Prototyping Stage] Diagnosis: {diagnosis}")
                else:
                    logger.warning("[Prototyping Stage] Docker fix attempt failed")
            else:
                logger.warning("[Prototyping Stage] No developer agent available for Docker fixes")

        return False

    def _stop_docker(self, prototype: dict[str, Any]) -> bool:
        """
        Stop Docker containers.

        Args:
            prototype: Prototype metadata with directory path

        Returns:
            True if containers stopped successfully
        """
        from ..utils.docker_manager import DockerManager

        prototype_dir = prototype.get("directory")
        if not prototype_dir:
            return False

        docker = DockerManager(prototype_dir)
        return docker.stop()

    def _rebuild_docker(self, prototype: dict[str, Any]) -> bool:
        """
        Rebuild and restart Docker containers after fixes.

        Args:
            prototype: Prototype metadata with directory path

        Returns:
            True if rebuild successful
        """
        from ..utils.docker_manager import DockerManager

        prototype_dir = prototype.get("directory")
        if not prototype_dir:
            return False

        docker = DockerManager(prototype_dir)

        logger.info("[Prototyping Stage] Stopping containers for rebuild...")
        docker.stop()

        logger.info("[Prototyping Stage] Rebuilding Docker images...")
        if not docker.build():
            logger.error("[Prototyping Stage] Docker rebuild failed")
            return False

        logger.info("[Prototyping Stage] Restarting containers...")
        if not docker.start():
            logger.error("[Prototyping Stage] Docker restart failed")
            return False

        logger.info("[Prototyping Stage] Waiting for services to restart...")
        time.sleep(10)

        return docker.status().get("running", False)

    def _run_qa_iteration_loop(
        self,
        prototype: dict[str, Any],
        design: dict[str, Any],
        max_iterations: int = 3,
    ) -> bool:
        """
        Run Developer-QA iteration loop.

        Pattern follows idea_development.py CEO-Researcher loop.

        Args:
            prototype: Prototype metadata
            design: Design specification
            max_iterations: Maximum number of QA iterations

        Returns:
            True if quality gates pass
        """
        qa = self.agents.get("qa")
        developer = self.agents.get("developer")

        if not qa:
            logger.warning("[Prototyping Stage] QA agent not available - skipping QA validation")
            return True

        if not developer:
            logger.warning("[Prototyping Stage] Developer agent not available - skipping bug fixes")
            return True

        current_iteration = 0
        all_bugs: list[dict[str, Any]] = []

        while current_iteration < max_iterations:
            logger.info(
                f"[Prototyping Stage] QA iteration {current_iteration + 1}/{max_iterations}"
            )

            start_time = time.time()
            qa_results = qa.test_prototype(
                prototype_url="http://localhost:3000",
                api_url="http://localhost:8000",
                design=design,
            )
            exec_time = int((time.time() - start_time) * 1000)
            self._record_agent_usage("QA", exec_time)

            bugs = qa_results.get("bugs", [])
            all_bugs = bugs
            self.context.update("QA", "qa_bugs", all_bugs, "prototyping")
            self.context.update("QA", "qa_results", qa_results, "prototyping")

            logger.info(f"[Prototyping Stage] QA found {len(bugs)} bugs")
            logger.info(f"[Prototyping Stage] QA summary: {qa_results.get('summary', 'N/A')}")

            if self._check_qa_quality_gates(qa_results):
                logger.info(f"[Prototyping Stage] QA passed at iteration {current_iteration + 1}")
                return True

            current_iteration += 1
            if current_iteration >= max_iterations:
                logger.warning("[Prototyping Stage] Max QA iterations reached")
                break

            critical_high_bugs = [b for b in bugs if b.get("severity") in ("critical", "high")]
            if critical_high_bugs:
                logger.info(
                    f"[Prototyping Stage] Developer fixing {len(critical_high_bugs)} critical-high bugs"
                )
                start_time = time.time()
                fix_result = developer.fix_bugs(
                    prototype=prototype,
                    bugs=critical_high_bugs[:5],
                )
                exec_time = int((time.time() - start_time) * 1000)
                self._record_agent_usage("Developer", exec_time)

                if fix_result.get("success"):
                    logger.info(
                        f"[Prototyping Stage] Fixed {len(fix_result.get('files_modified', []))} files"
                    )

                    if not self._rebuild_docker(prototype):
                        logger.error("[Prototyping Stage] Failed to rebuild after fixes")
                        break
                else:
                    logger.warning(
                        "[Prototyping Stage] Bug fixes failed - continuing to next iteration"
                    )
            else:
                logger.info("[Prototyping Stage] No critical-high bugs to fix")
                break

        return False

    def _check_qa_quality_gates(self, qa_results: dict[str, Any]) -> bool:
        """
        Check QA quality gates.

        Gates:
        1. Prototype is running (can load pages)
        2. Has proper styling (no major layout issues)
        3. No critical or high severity bugs

        Args:
            qa_results: QA test results

        Returns:
            True if all gates pass
        """
        bugs = qa_results.get("bugs", [])

        if not qa_results.get("prototype_running", False):
            logger.warning("[QA Gate] Prototype not running - gate failed")
            return False

        if not qa_results.get("has_styling", False):
            logger.warning("[QA Gate] Missing proper styling - gate failed")
            return False

        critical_high_count = sum(1 for b in bugs if b.get("severity") in ("critical", "high"))
        if critical_high_count > 0:
            logger.warning(
                f"[QA Gate] {critical_high_count} critical-high bugs remaining - gate failed"
            )
            return False

        logger.info("[QA Gate] All quality gates passed")
        return True

    def _validate_prototype(
        self,
        prototype: dict[str, Any],
        design: dict[str, Any],
    ) -> dict[str, Any]:
        """
        QA validation of prototype (legacy interface).

        Args:
            prototype: The prototype
            design: The design

        Returns:
            QA validation results
        """
        qa = self.agents.get("qa")
        if not qa:
            raise ValueError("QA agent not available")

        return qa.test_prototype(design=design)

    def _iterate_on_feedback(
        self,
        prototype: dict[str, Any],
        qa_feedback: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Iterate on prototype based on QA feedback (legacy interface).

        Args:
            prototype: Current prototype
            qa_feedback: QA findings

        Returns:
            Updated prototype
        """
        developer = self.agents.get("developer")
        if not developer:
            raise ValueError("Developer agent not available")

        bugs = qa_feedback.get("bugs", [])
        return developer.fix_bugs(prototype, bugs)
