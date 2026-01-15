"""Pipeline orchestration for the AI startup company."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .agents import (
    BaseAgent,
    CEOAgent,
    DeckStrategistAgent,
    DesignerAgent,
    DeveloperAgent,
    LegalAdvisorAgent,
    MarketerAgent,
    QAAgent,
    ResearcherAgent,
)
from .config import Config, ModeConfig, config
from .context import CompanyContext
from .stages import (
    IdeaDevelopmentStage,
    PitchStage,
    PrototypingStage,
)
from .utils import ExperimentLogger, PipelineStatistics

logger = logging.getLogger(__name__)


class StartupPipeline:
    """
    Orchestrates the startup idea pipeline.

    Stages:
    1. Idea Development - CEO, Researcher (generation + validation in iterative loop)
    2. Prototyping - Developer, Designer, QA
    3. Pitch - Marketer, Deck Strategist, CEO (sequential workflow)
    """

    def __init__(
        self,
        app_config: Config | None = None,
        experiment_dir: Path | None = None,
        mode_config: ModeConfig | None = None,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            app_config: Application configuration (uses global config if not provided)
            experiment_dir: Directory for experiment outputs (creates timestamped if None)
            mode_config: Execution mode configuration (standard vs extended)
        """
        self.config = app_config or config
        self.mode_config = mode_config or ModeConfig.standard()
        self.context = CompanyContext()
        self.agents: dict[str, BaseAgent] = {}
        self.stages: list[tuple[str, Any]] = []

        # Store mode config in context for stages and agents to access
        self.context.update("system", "execution_mode", self.mode_config.mode.value)
        self.context.update(
            "system",
            "mode_config",
            {
                "mode": self.mode_config.mode.value,
                "enable_code_generation": self.mode_config.enable_code_generation,
                "enable_qa_iteration": self.mode_config.enable_qa_iteration,
                "enable_docker": self.mode_config.enable_docker,
                "design_screen_count": self.mode_config.design_screen_count,
                "enable_mobile_variants": self.mode_config.enable_mobile_variants,
                "enhanced_design_prompts": self.mode_config.enhanced_design_prompts,
                "enhanced_slides_content": self.mode_config.enhanced_slides_content,
                "include_all_design_images": self.mode_config.include_all_design_images,
            },
        )

        # Initialize statistics collector
        self.statistics = PipelineStatistics(max_budget=self.config.cost.max_budget_per_experiment)

        # Set up experiment directory
        self.experiment_dir = experiment_dir or self._create_experiment_dir("experiment")
        self._setup_experiment_dir()

        self._initialize_agents()
        self._initialize_stages()

    def _create_experiment_dir(self, name: str) -> Path:
        """Create a timestamped experiment directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"{name}_{timestamp}"
        return self.config.storage.experiments_dir / experiment_name

    def _setup_experiment_dir(self) -> None:
        """Set up experiment directory structure and store in context."""
        # Create directories
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        (self.experiment_dir / "wireframes").mkdir(exist_ok=True)
        (self.experiment_dir / "designs").mkdir(exist_ok=True)
        (self.experiment_dir / "logs").mkdir(exist_ok=True)

        # Initialize experiment logger (captures all output to logs folder)
        self.experiment_logger = ExperimentLogger(self.experiment_dir)

        # Store in context for agents to access
        self.context.update("system", "experiment_dir", str(self.experiment_dir))
        self.context.update("system", "experiment_name", self.experiment_dir.name)

        logger.info(f"Experiment directory: {self.experiment_dir}")

    def _initialize_agents(self) -> None:
        """Initialize all agents with shared context."""
        self.agents = {
            "ceo": CEOAgent(context=self.context),
            "researcher": ResearcherAgent(context=self.context),
            "legal_advisor": LegalAdvisorAgent(context=self.context),
            "developer": DeveloperAgent(context=self.context),
            "designer": DesignerAgent(context=self.context),
            "qa": QAAgent(context=self.context),
            "marketer": MarketerAgent(context=self.context),
            "deck_strategist": DeckStrategistAgent(context=self.context),
        }

    def _initialize_stages(self) -> None:
        """Initialize all pipeline stages with mode config."""
        self.stages = [
            ("idea_development", IdeaDevelopmentStage(self.context, self.agents, self.mode_config)),
            ("prototyping", PrototypingStage(self.context, self.agents, self.mode_config)),
            ("pitch", PitchStage(self.context, self.agents, self.mode_config)),
        ]

    def run(self, chairman_input: str) -> dict[str, Any]:
        """
        Run the full pipeline.

        Args:
            chairman_input: Direction from the chairman

        Returns:
            Final context snapshot
        """
        # Start experiment logging (captures all output to logs folder)
        self.experiment_logger.start()

        try:
            logger.info(f"Starting pipeline with input: {chairman_input[:100]}...")
            logger.info(f"Experiment directory: {self.experiment_dir}")

            # Start pipeline statistics
            self.statistics.start_pipeline()

            # Store chairman input
            self.context.update("system", "chairman_input", chairman_input)

            # Run each stage
            for stage_name, stage in self.stages:
                logger.info(f"Starting stage: {stage_name}")
                self.context.update("system", "current_stage", stage_name)

                # Start stage timing
                self.statistics.start_stage(stage_name)

                # Pass statistics to stage for recording agent usage
                stage.set_statistics(self.statistics)

                try:
                    success = stage.run()
                except NotImplementedError as e:
                    logger.warning(f"Stage {stage_name} not implemented: {e}")
                    success = False
                except Exception as e:
                    logger.error(f"Stage {stage_name} failed with exception: {e}")
                    success = False

                # End stage timing
                self.statistics.end_stage(stage_name)

                # Record completion or failure
                if success:
                    completed = self.context.get("completed_stages", [])
                    completed.append(stage_name)
                    self.context.update("system", "completed_stages", completed)
                    logger.info(f"Completed stage: {stage_name}")
                else:
                    failed = self.context.get("failed_stages", [])
                    failed.append(stage_name)
                    self.context.update("system", "failed_stages", failed)
                    logger.warning(f"Stage {stage_name} failed, continuing to next stage")

                # Save context snapshot after each stage
                self._save_stage_context(stage_name)

            # End pipeline statistics
            self.statistics.end_pipeline()

            # Save statistics to context and file
            self._save_statistics()

            # Save final context
            self._save_final_context()

            return self.context.snapshot()

        finally:
            # Stop experiment logging
            self.experiment_logger.stop()
            logger.info(f"Experiment logs saved to: {self.experiment_logger.log_path}")

    def _save_stage_context(self, stage_name: str) -> None:
        """Save context snapshot after a stage completes."""
        context_file = self.experiment_dir / f"context_{stage_name}.json"
        self.context.save_to_file(str(context_file))
        logger.info(f"Saved stage context: {context_file}")

    def _save_final_context(self) -> None:
        """Save final context snapshot."""
        context_file = self.experiment_dir / "context_final.json"
        self.context.save_to_file(str(context_file))
        logger.info(f"Saved final context: {context_file}")

    def _save_statistics(self) -> None:
        """Save pipeline statistics to file and context."""
        import json

        # Save statistics to JSON file
        stats_file = self.experiment_dir / "statistics.json"
        with open(stats_file, "w") as f:
            json.dump(self.statistics.to_dict(), f, indent=2, default=str)
        logger.info(f"Saved statistics: {stats_file}")

        # Also store in context for export
        self.context.update(
            "system",
            "costs",
            {
                "total": self.statistics.total_cost,
                "by_stage": {
                    name: stats.total_cost for name, stats in self.statistics.stages.items()
                },
            },
        )
        self.context.update(
            "system",
            "token_usage",
            {
                "total": self.statistics.total_tokens,
                "by_agent": {
                    name: usage.total_tokens
                    for name, usage in self.statistics.get_agent_totals().items()
                },
            },
        )

    def print_statistics(self) -> None:
        """Print pipeline statistics summary to console."""
        print(self.statistics.format_summary())

    def run_from_stage(self, stage_name: str, context_file: str) -> dict[str, Any]:
        """
        Resume pipeline from a specific stage.

        Args:
            stage_name: Stage to start from
            context_file: Path to context snapshot file

        Returns:
            Final context snapshot
        """
        # Start experiment logging
        self.experiment_logger.start()

        try:
            # Load previous context into existing object (preserve references for stages/agents)
            loaded_context = CompanyContext.load_from_file(context_file)
            self.context.state = loaded_context.state
            self.context.stage_contexts = loaded_context.stage_contexts
            self.context.history = loaded_context.history

            # Find starting stage
            stage_found = False
            for name, stage in self.stages:
                if name == stage_name:
                    stage_found = True

                if stage_found:
                    logger.info(f"Running stage: {name}")
                    self.context.update("system", "current_stage", name)

                    try:
                        success = stage.run()
                    except NotImplementedError as e:
                        logger.warning(f"Stage {name} not implemented: {e}")
                        success = False
                    except Exception as e:
                        logger.error(f"Stage {name} failed with exception: {e}")
                        success = False

                    # Record completion or failure
                    if success:
                        completed = self.context.get("completed_stages", [])
                        if name not in completed:
                            completed.append(name)
                            self.context.update("system", "completed_stages", completed)
                        logger.info(f"Completed stage: {name}")
                    else:
                        failed = self.context.get("failed_stages", [])
                        if name not in failed:
                            failed.append(name)
                            self.context.update("system", "failed_stages", failed)
                        logger.warning(f"Stage {name} failed, continuing to next stage")

            return self.context.snapshot()

        finally:
            # Stop experiment logging
            self.experiment_logger.stop()
            logger.info(f"Experiment logs saved to: {self.experiment_logger.log_path}")

    def get_stage(self, stage_name: str) -> Any | None:
        """
        Get a specific stage by name.

        Args:
            stage_name: Name of the stage

        Returns:
            Stage instance or None
        """
        for name, stage in self.stages:
            if name == stage_name:
                return stage
        return None

    def save_checkpoint(self, filepath: str) -> None:
        """
        Save current context as checkpoint.

        Args:
            filepath: Path to save checkpoint
        """
        self.context.save_to_file(filepath)
        logger.info(f"Saved checkpoint to {filepath}")

    def get_status(self) -> dict[str, Any]:
        """
        Get current pipeline status.

        Returns:
            Status dictionary
        """
        return {
            "current_stage": self.context.get("current_stage"),
            "completed_stages": self.context.get("completed_stages", []),
            "failed_stages": self.context.get("failed_stages", []),
            "iterations": self.context.get("iterations", 0),
            "costs": self.context.get("costs", {}),
        }


class StartupCompany:
    """
    High-level interface for the AI startup company.

    This is the main entry point for running experiments.
    """

    def __init__(
        self,
        name: str = "experiment",
        app_config: Config | None = None,
        experiment_dir: Path | None = None,
        mode_config: ModeConfig | None = None,
    ) -> None:
        """
        Initialize the startup company.

        Args:
            name: Experiment name (will be prefixed to timestamp)
            app_config: Application configuration
            experiment_dir: Explicit experiment directory (overrides name + timestamp)
            mode_config: Execution mode configuration (standard vs extended)
        """
        self.config = app_config or config
        self.mode_config = mode_config or ModeConfig.standard()

        # Create experiment directory with timestamp if not provided
        if experiment_dir:
            self.experiment_dir = experiment_dir
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.experiment_dir = self.config.storage.experiments_dir / f"{name}_{timestamp}"

        self.name = self.experiment_dir.name
        self.pipeline = StartupPipeline(
            app_config=self.config,
            experiment_dir=self.experiment_dir,
            mode_config=self.mode_config,
        )

    def run_experiment(
        self,
        chairman_input: str,
    ) -> dict[str, Any]:
        """
        Run a full experiment.

        Args:
            chairman_input: Direction from the chairman

        Returns:
            Experiment results
        """
        logger.info(f"Starting experiment: {self.name}")
        logger.info(f"Experiment directory: {self.experiment_dir}")
        result = self.pipeline.run(chairman_input)
        logger.info(f"Completed experiment: {self.name}")
        logger.info(f"Results saved to: {self.experiment_dir}")

        return result

    def get_results(self) -> dict[str, Any]:
        """
        Get current experiment results.

        Returns:
            Results dictionary
        """
        return {
            "name": self.name,
            "status": self.pipeline.get_status(),
            "context": self.pipeline.context.snapshot(),
        }
